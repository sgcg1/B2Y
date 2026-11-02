"""Uninstrumented A2 Decode screening; no production routing changes."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import traceback

BASE = "987da9f9d314f8744bef05a628e60a14b88e63db320374f36a3b6411ce5eb2e3"
SOURCE = "src/tileops/_kernels/attention/topk_select_ascend.py"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def execute(report, repo, root):
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    import torch
    import torch_npu
    import tilelang

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args])

    assert not git("status", "--porcelain", "--untracked-files=no").strip()
    report["commit"] = git("rev-parse", "HEAD").decode().strip()
    baseline = git("show", "7247ad4f355c62a8679dcdc8fdf182c0b219db5e:" + SOURCE)
    report["stage"] = "provenance:baseline"
    report["baseline_sha256"] = digest(baseline)
    assert digest(baseline) == BASE, ("Frozen baseline mismatch", digest(baseline), BASE)
    candidate = (repo / SOURCE).read_bytes()
    expected = json.loads((Path(__file__).parent / "identity.json").read_text())
    assert digest(candidate) == expected["candidate_sha256"], "Unexpected candidate"
    assert digest(Path(__file__).read_bytes()) == expected["run_sha256"], "Tool changed"
    report["identity"] = expected
    report["tool_sha256"] = digest(Path(__file__).read_bytes())
    report["runtime"] = {"python": sys.executable, "torch": torch.__version__,
                         "torch_npu": torch_npu.__version__, "tilelang": tilelang.__version__,
                         "tilelang_path": tilelang.__file__, "cann": os.environ.get("ASCEND_HOME_PATH")}
    report["compiler"] = subprocess.check_output(["bisheng", "--version"], text=True, timeout=30)
    report["health_begin"] = subprocess.check_output(["npu-smi", "info"], text=True)
    torch.npu.set_device(0)
    assert "950" in torch.npu.get_device_name(0)
    programs = {}
    report["generated"] = {}
    for name, raw in [("baseline", baseline), ("control", candidate), ("a2", candidate)]:
        report["stage"] = "compile:" + name
        path = root / (name + ".py")
        path.write_bytes(raw)
        spec = importlib.util.spec_from_file_location("topk_a2_" + name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        kwargs = {} if name == "baseline" else {"HIST_BANKS": 4 if name == "a2" else 1}
        print("COMPILE_BEGIN", name, flush=True)
        saved_stderr = os.dup(2)
        stderr_path = root / (name + "-compile.stderr.log")
        try:
            with stderr_path.open("w") as compile_log:
                sys.stderr.flush()
                os.dup2(compile_log.fileno(), 2)
                program = module.topk_select_ascend(1, 16384, 2048, 1, 1, COARSE=True, H=128,
                                                   PARALLEL_SCAN=True, **kwargs)
        finally:
            sys.stderr.flush()
            os.dup2(saved_stderr, 2)
            os.close(saved_stderr)
            report.setdefault("compile_stderr", {})[name] = stderr_path.read_text()
            print(report["compile_stderr"][name], file=sys.stderr, flush=True)
        print("COMPILE_END", name, flush=True)
        code = program.get_kernel_source()
        (root / (name + ".cpp")).write_text(code)
        report["generated"][name] = digest(code.encode())
        programs[name] = program
        assert "ThreadSync" not in report["compile_stderr"][name], "Unresolved synchronization diagnostic; refuse timing"
    assert report["generated"]["baseline"] == report["generated"]["control"], (
        "Default-off generated source changed; review before timing")
    out = {name: torch.empty((1, 2048), dtype=torch.int32, device="npu") for name in programs}
    starts = torch.zeros(1, dtype=torch.int32, device="npu")
    ends = torch.full_like(starts, 16384)
    report["cases"] = []
    # Generate on NPU as in the recorded Decode experiment; record actual bytes.
    for seed in [20261030, 20261102]:
        torch.manual_seed(seed)
        torch.npu.manual_seed_all(seed)
        x = torch.randn((1, 16384, 1), dtype=torch.float32, device="npu")
        cpu = x.cpu()
        reference = cpu.flatten().argsort(descending=True, stable=True)[:2048].sort().values
        case = {"seed": seed, "input_sha256": digest(cpu.numpy().tobytes()),
                "samples_us": {name: [] for name in programs}}
        report["cases"].append(case)
        for name, program in programs.items():
            report["stage"] = "validate:" + name
            for _ in range(5):
                program(x, starts, ends, out[name])
            torch.npu.synchronize()
            assert torch.equal(out[name].cpu().long().flatten().sort().values, reference), name
        begin, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
        for _ in range(5):
            begin.record(); end.record(); end.synchronize()
        for iteration in range(50):
            names = list(programs)
            from itertools import permutations
            for name in list(permutations(names))[iteration % 6]:
                report["stage"] = f"sample:{seed}:{iteration}:{name}"
                begin.record()
                programs[name](x, starts, ends, out[name])
                end.record()
                end.synchronize()
                case["samples_us"][name].append(begin.elapsed_time(end) * 1000)
        for name in programs:
            assert torch.equal(out[name].cpu().long().flatten().sort().values, reference), name
        case["median_us"] = {name: statistics.median(v) for name, v in case["samples_us"].items()}
        case["baseline_over_a2"] = case["median_us"]["baseline"] / case["median_us"]["a2"]
        # Untimed adversarial checks. This screening does not replace the full contract suite.
        for label in ["equal", "special", "overflow"]:
            values = torch.ones(16384, dtype=torch.float32)
            if label == "special":
                values[:16] = torch.tensor([float("nan"), float("inf"), -float("inf"),
                                           0., -0., 65504., 65520., -65520.] * 2)
            elif label == "overflow":
                values = torch.arange(16384, dtype=torch.float32) * 1e-8 + 1
            oracle_values = values.clone()
            oracle_values[oracle_values.isnan()] = float("inf")
            # NaN ranks above +inf, so use Python's tuple order for the independent oracle.
            import math
            order = sorted(range(16384), key=lambda i: (math.isnan(float(values[i])),
                           float(oracle_values[i]), -i), reverse=True)[:2048]
            x.copy_(values.reshape_as(x))
            expected_set = torch.tensor(sorted(order), dtype=torch.int64)
            for name, program in programs.items():
                program(x, starts, ends, out[name])
                torch.npu.synchronize()
                assert torch.equal(out[name].cpu().long().flatten().sort().values, expected_set), (name, label)
        for start, stop in [(13, 12000), (11, 111), (50, 50), (60, 40)]:
            starts.fill_(start)
            ends.fill_(stop)
            count = max(0, stop - start)
            order = sorted(range(start, stop), key=lambda i: (float(values[i]), -i), reverse=True)[:2048]
            expected_window = torch.tensor(sorted(order + [16384] * (2048 - min(count, 2048))), dtype=torch.int64)
            for name, program in programs.items():
                program(x, starts, ends, out[name])
                torch.npu.synchronize()
                assert torch.equal(out[name].cpu().long().flatten().sort().values, expected_window), (name, start, stop)
        starts.zero_()
        ends.fill_(16384)
        case["adversarial_passed"] = True
    report["health_end"] = subprocess.check_output(["npu-smi", "info"], text=True)
    report.update(status="completed", stage="review_required", accepted=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default=0, type=int)
    args = parser.parse_args()
    root = args.output.resolve()
    assert root.is_relative_to(Path("/home/y00937463")) and root != Path("/home/y00937463")
    assert args.device >= 0
    root.mkdir(parents=True, exist_ok=False)
    for key, relative in {"TMPDIR": "tmp", "XDG_CACHE_HOME": "cache", "TILELANG_CACHE_DIR": "cache/tilelang",
                          "ASCEND_CACHE_PATH": "cache/cann", "ASCEND_WORK_PATH": "cache/work",
                          "ASCEND_PROCESS_LOG_PATH": "logs", "TORCH_EXTENSIONS_DIR": "cache/torch"}.items():
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ.update(ASCEND_RT_VISIBLE_DEVICES=str(args.device), TASK_QUEUE_ENABLE="0",
                      PYTHONDONTWRITEBYTECODE="1")
    sys.dont_write_bytecode = True
    report = {"shape": [1, 16384, 1], "k": 2048, "workers": 1, "threads": 128,
              "coarse": True, "version": "20261102-a2-r3", "status": "incomplete", "physical_device": args.device,
              "timing_scope": "Uninstrumented single kernel call NPU events; not pure kernel time",
              "accepted": False}
    try:
        execute(report, args.repo.resolve(), root)
    except Exception:
        report.update(status="failed", traceback=traceback.format_exc())
        raise
    finally:
        sources = {p.name: p.read_text() for p in root.glob("*.cpp")}
        (root / "a2-return.txt").write_text(json.dumps({"report": report, "sources": sources}, indent=2) + "\n")
        print("A2_OUTPUT", root, flush=True)


if __name__ == "__main__":
    main()
