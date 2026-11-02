"""Experimental full Decode pipeline screening; production route remains unchanged."""
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


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def execute(report, repo, root):
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    import torch
    import torch_npu
    import tilelang
    from itertools import permutations
    from tilelang.ascend.callback import register_ascend_postproc_callback

    report["stage"] = "provenance"
    report["configuration"] = {"N": 16384, "K": 2048, "P": [4], "threads": 128,
                               "kernels_per_pipeline": 4, "boundary_capacity": 2048}
    identity = json.loads((Path(__file__).parent / "identity.json").read_text())
    for path, expected in identity["sources"].items():
        assert digest((repo / path).read_bytes()) == expected, path
    assert digest(Path(__file__).read_bytes()) == identity["run_sha256"]
    assert not subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"]).strip()
    report["commit"] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    raw = subprocess.check_output(["git", "-C", str(repo), "show", identity["baseline_commit"] + ":src/tileops/_kernels/attention/topk_select_ascend.py"])
    assert digest(raw) == identity["baseline_sha256"]
    (root / "baseline.py").write_bytes(raw)
    r1_raw = subprocess.check_output(["git", "-C", str(repo), "show", identity["r1_commit"] + ":src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py"])
    assert digest(r1_raw) == identity["r1_pipeline_sha256"]
    (root / "r1-pipeline.py").write_bytes(r1_raw)
    report["identity"] = identity
    report["runtime"] = {"python": sys.executable, "torch": torch.__version__, "torch_npu": torch_npu.__version__,
                         "tilelang": tilelang.__version__, "tilelang_path": tilelang.__file__,
                         "cann_home": os.environ.get("ASCEND_HOME_PATH")}
    report["compiler"] = subprocess.check_output(["bisheng", "--version"], text=True, timeout=30)
    report["health_begin"] = subprocess.check_output(["npu-smi", "info"], text=True)
    torch.npu.set_device(0)
    assert "950" in torch.npu.get_device_name(0)
    report["generated"] = {}

    def capture(code, target):
        name = report["stage"].split(":")[-1]
        text = str(code)
        (root / (name + "-precompile.cpp")).write_text(text)
        return text

    register_ascend_postproc_callback(capture, override=True)
    baseline_module = load(root / "baseline.py", "full_decode_baseline")
    hist_module = load(repo / "src/tileops/_kernels/attention/topk_select_decode_probe_ascend.py", "full_decode_hist")
    module = load(repo / "src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py", "full_decode_pipeline_r2")
    r1_module = load(root / "r1-pipeline.py", "frozen_decode_pipeline_r1")
    builders = [("baseline", lambda: baseline_module.topk_select_ascend(1, 16384, 2048, 1, 1, COARSE=True, H=128, PARALLEL_SCAN=True)),
                ("finish-r1", r1_module.decode_finish),
                ("finish-control", lambda: module.decode_finish(STABLE_TIE=False)),
                ("finish-new", lambda: module.decode_finish(STABLE_TIE=True))]
    for p in [4]:
        builders.extend([(f"hist-p{p}", lambda p=p: hist_module.decode_histogram(16384, p)),
                         (f"prepare-p{p}", lambda p=p: module.decode_prepare(p, 2048)),
                         (f"compact-p{p}", lambda p=p: module.decode_compact(p))])
    programs = {}
    for name, build in builders:
        report["stage"] = "compile:" + name
        print("COMPILE_BEGIN", name, flush=True)
        stderr_path = root / (name + ".stderr.log")
        saved = os.dup(2)
        try:
            with stderr_path.open("w") as log:
                sys.stderr.flush()
                os.dup2(log.fileno(), 2)
                program = build()
        finally:
            sys.stderr.flush()
            os.dup2(saved, 2)
            os.close(saved)
            report.setdefault("compile_stderr", {})[name] = stderr_path.read_text()
            print(report["compile_stderr"][name], file=sys.stderr, flush=True)
        code = program.get_kernel_source()
        (root / (name + ".cpp")).write_text(code)
        report["generated"][name] = digest(code.encode())
        assert "ThreadSync" not in report["compile_stderr"][name], "Unresolved sync diagnostic"
        programs[name] = program
        print("COMPILE_END", name, flush=True)
    assert report["generated"]["finish-r1"] == report["generated"]["finish-control"], "Disabled finish changed"
    for name, expected in identity["unchanged_generated"].items():
        assert report["generated"][name] == expected, (name, "Shared stage changed")
    x = torch.empty(16384, dtype=torch.float32, device="npu")
    starts = torch.zeros(1, dtype=torch.int32, device="npu")
    ends = torch.full_like(starts, 16384)
    out = {name: torch.empty(2048, dtype=torch.int32, device="npu") for name in ["baseline", "r1", "r2"]}
    work = {name: {"partial": torch.empty((4, 256), dtype=torch.int32, device="npu"),
                "higher": torch.empty(256, dtype=torch.int32, device="npu"),
                "meta": torch.empty(4, dtype=torch.int32, device="npu"),
                "offsets": torch.empty((4, 2), dtype=torch.int32, device="npu"),
                "scores": torch.empty(2048, dtype=torch.float32, device="npu"),
                "indices": torch.empty(2048, dtype=torch.int32, device="npu"),
                "final": torch.empty(2, dtype=torch.int32, device="npu")}
            for name in ["r1", "r2"]}

    def invoke(name):
        if name == "baseline":
            programs[name](x.view(1, 16384, 1), starts, ends, out[name].view(1, 2048))
        else:
            p = 4
            w = work[name]
            programs[f"hist-p{p}"](x, starts, ends, w["partial"])
            programs[f"prepare-p{p}"](w["partial"], w["higher"], w["meta"], out[name], w["offsets"])
            programs[f"compact-p{p}"](x, starts, ends, w["meta"], w["offsets"], w["scores"], w["indices"], out[name])
            programs["finish-r1" if name == "r1" else "finish-new"](x, starts, ends, w["meta"], w["scores"], w["indices"], out[name], w["final"])

    report["validation"] = []

    def validate(cpu, start, stop, label):
        report["stage"] = "validate:" + label
        x.copy_(cpu)
        starts.fill_(start)
        ends.fill_(stop)
        bits = cpu.view(torch.int32).long() & 0xffffffff
        mag = bits & 0x7fffffff
        ordered = torch.where((bits & 0x80000000) != 0, (~bits) & 0xffffffff, bits | 0x80000000)
        keys = torch.where(mag > 0x7f800000, 0xffffffff, torch.where(mag == 0, 0x80000000, ordered))
        valid = max(0, stop - start)
        selected = keys[start:stop].argsort(descending=True, stable=True)[:2048] + start if valid else torch.empty(0, dtype=torch.int64)
        reference = torch.cat((selected, torch.full((2048 - min(valid, 2048),), 16384, dtype=torch.int64))).sort().values
        item = {"label": label, "window": [start, stop], "input_sha256": digest(cpu.numpy().tobytes()), "metadata": {}}
        report["validation"].append(item)
        for name in out:
            out[name].fill_(-1)
            invoke(name)
            torch.npu.synchronize()
            assert torch.equal(out[name].cpu().long().sort().values, reference), (name, label, "Wrong selected set")
            if name != "baseline":
                assert work[name]["final"].cpu().tolist() == [0, min(valid, 2048)], (name, label, "Unfinished quota")
                item["metadata"][name] = work[name]["meta"].cpu().tolist()
                assert item["metadata"][name][3] == valid
        item["passed"] = True

    special = torch.ones(16384, dtype=torch.float32)
    special[:16] = torch.tensor([float("nan"), float("inf"), -float("inf"), 0., -0., 65504., 65520., -65520.] * 2)
    for start, stop in [(0, 16384), (13, 12000), (11, 111), (50, 50), (60, 40)]:
        validate(special, start, stop, f"special-{start}-{stop}")
    validate(torch.ones(16384, dtype=torch.float32), 0, 16384, "all-equal-overflow")
    small = torch.zeros(16384, dtype=torch.float32)
    small[:2047] = 1000.
    small[2047:2147] = 100.
    validate(small, 0, 16384, "small-boundary-tie")
    validate(torch.arange(16384, dtype=torch.float32) * 1e-8 + 1, 0, 16384, "fp32-close-overflow")
    report["cases"] = []
    names = list(out)
    orders = list(permutations(names))
    for label, seed in [("random-20261030", 20261030), ("random-20261102", 20261102),
                        ("all-equal-overflow", None), ("small-boundary-tie", None)]:
        if seed is not None:
            torch.manual_seed(seed)
            torch.npu.manual_seed_all(seed)
            cpu = torch.randn((1, 16384, 1), dtype=torch.float32, device="npu").reshape(-1).cpu()
        else:
            cpu = torch.ones(16384, dtype=torch.float32) if label == "all-equal-overflow" else small
        validate(cpu, 0, 16384, label)
        case = {"label": label, "seed": seed, "input_sha256": digest(cpu.numpy().tobytes()), "event_samples_us": {n: [] for n in names}}
        report["cases"].append(case)
        for name in names:
            for _ in range(5):
                invoke(name)
        torch.npu.synchronize()
        begin, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
        for _ in range(5):
            begin.record(); end.record(); end.synchronize()
        for iteration in range(50):
            for name in orders[iteration % 6]:
                report["stage"] = f"sample:{label}:{iteration}:{name}"
                begin.record()
                invoke(name)
                end.record()
                end.synchronize()
                case["event_samples_us"][name].append(begin.elapsed_time(end) * 1000)
        case["median_us"] = {n: statistics.median(v) for n, v in case["event_samples_us"].items()}
        validate(cpu, 0, 16384, "post-sample-" + label)
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
    report = {"version": "20261102-decode-full-r2", "status": "incomplete",
              "physical_device": args.device, "accepted": False,
              "scope": "Uninstrumented complete four-kernel selection vs frozen one-kernel baseline events; not profiler kernel time"}
    try:
        execute(report, args.repo.resolve(), root)
    except Exception:
        report.update(status="failed", traceback=traceback.format_exc())
        raise
    finally:
        sources = {p.name: p.read_text() for p in root.glob("*.cpp")}
        (root / "full-return.txt").write_text(json.dumps({"report": report, "sources": sources}, indent=2) + "\n")
        print("FULL_OUTPUT", root, flush=True)


if __name__ == "__main__":
    main()
