"""Decode first-round partition/merge cost pilot, not a selection candidate."""
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


def execute(report, repo, root):
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    import torch
    import torch_npu
    import tilelang
    from tilelang.ascend.callback import register_ascend_postproc_callback

    report["stage"] = "provenance"
    report["configuration"] = {"N": 16384, "K": 2048, "P": [1, 2, 4], "threads": 128}
    here = Path(__file__).resolve().parent
    identity = json.loads((here / "identity.json").read_text())
    source = "src/tileops/_kernels/attention/topk_select_decode_probe_ascend.py"
    raw = (repo / source).read_bytes()
    assert digest(raw) == identity["source_sha256"]
    assert digest(Path(__file__).read_bytes()) == identity["run_sha256"]
    assert not subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"]).strip()
    report["commit"] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
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
    spec = importlib.util.spec_from_file_location("decode_cost_pilot", repo / source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    programs = {}
    for p in [1, 2, 4]:
        for kind, build in [("hist", lambda: module.decode_histogram(16384, p)),
                            ("merge", lambda: module.decode_merge(p, 2048))]:
            name = f"{kind}-p{p}"
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
    partial = {p: torch.empty((p, 256), dtype=torch.int32, device="npu") for p in [1, 2, 4]}
    higher = {p: torch.empty(256, dtype=torch.int32, device="npu") for p in [1, 2, 4]}
    meta = {p: torch.empty(4, dtype=torch.int32, device="npu") for p in [1, 2, 4]}
    starts = torch.zeros(1, dtype=torch.int32, device="npu")
    ends = torch.full_like(starts, 16384)
    x = torch.empty(16384, dtype=torch.float32, device="npu")

    def invoke(name):
        p = int(name[-1])
        programs[f"hist-p{p}"](x, starts, ends, partial[p])
        if name.startswith("pipeline"):
            programs[f"merge-p{p}"](partial[p], higher[p], meta[p])

    def validate(cpu, start, end):
        x.copy_(cpu)
        starts.fill_(start)
        ends.fill_(end)
        # Independent CPU FP16 encoding, including canonical NaNs and signed zero.
        bits = cpu.to(torch.float16).view(torch.int16).to(torch.int32) & 65535
        mag = bits & 32767
        ordered = torch.where((bits & 32768) != 0, (~bits) & 65535, bits | 32768)
        canonical = torch.where(mag > 31744, 65535, torch.where(mag == 0, 32768, ordered))
        digits = (canonical >> 8) & 255
        indices = torch.arange(16384)
        for p in [1, 2, 4]:
            expected_rows = []
            for worker in range(p):
                valid = (indices >= start) & (indices < end) & (indices >= worker * (16384 // p)) & (indices < (worker + 1) * (16384 // p))
                expected_rows.append(torch.bincount(digits[valid].long(), minlength=256))
            expected = torch.stack(expected_rows)
            counts = expected.sum(0).tolist()
            before = [sum(counts[b + 1:]) for b in range(256)]
            threshold = next((b for b in range(256) if before[b] <= 2048 < before[b] + counts[b]), -1)
            expected_meta = [threshold, before[threshold] if threshold >= 0 else sum(counts),
                             counts[threshold] if threshold >= 0 else 0, sum(counts)]
            invoke(f"pipeline-p{p}")
            torch.npu.synchronize()
            assert torch.equal(partial[p].cpu().long(), expected), (p, "histogram", start, end)
            assert higher[p].cpu().tolist() == before, (p, "prefix")
            assert meta[p].cpu().tolist() == expected_meta, (p, "metadata")

    report["stage"] = "adversarial-validation"
    special = torch.ones(16384, dtype=torch.float32)
    special[:16] = torch.tensor([float("nan"), float("inf"), -float("inf"), 0., -0., 65504., 65520., -65520.] * 2)
    for start, end in [(0, 16384), (13, 12000), (11, 111), (50, 50), (60, 40)]:
        validate(special, start, end)
    validate(torch.ones(16384, dtype=torch.float32), 0, 16384)
    report["adversarial_passed"] = True
    report["cases"] = []
    for seed in [20261030, 20261102]:
        torch.manual_seed(seed)
        torch.npu.manual_seed_all(seed)
        random_x = torch.randn((1, 16384, 1), dtype=torch.float32, device="npu").reshape(-1)
        cpu = random_x.cpu()
        validate(cpu, 0, 16384)
        names = [f"{kind}-p{p}" for p in [1, 2, 4] for kind in ["hist", "pipeline"]]
        case = {"seed": seed, "input_sha256": digest(cpu.numpy().tobytes()),
                "event_samples_us": {name: [] for name in names}}
        report["cases"].append(case)
        for name in names:
            for _ in range(5):
                invoke(name)
        torch.npu.synchronize()
        begin, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
        for _ in range(5):
            begin.record(); end.record(); end.synchronize()
        for iteration in range(50):
            shift = iteration % len(names)
            order = names[shift:] + names[:shift]
            if (iteration // len(names)) % 2:
                order = order[::-1]
            for name in order:
                report["stage"] = f"sample:{seed}:{iteration}:{name}"
                begin.record()
                invoke(name)
                end.record()
                end.synchronize()
                case["event_samples_us"][name].append(begin.elapsed_time(end) * 1000)
        case["median_us"] = {name: statistics.median(values) for name, values in case["event_samples_us"].items()}
        validate(cpu, 0, 16384)
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
    report = {"version": "20261102-decode-pilot-r1", "status": "incomplete",
              "physical_device": args.device, "accepted": False,
              "scope": "histogram only or histogram+merge two-kernel events; NOT full TopK"}
    try:
        execute(report, args.repo.resolve(), root)
    except Exception:
        report.update(status="failed", traceback=traceback.format_exc())
        raise
    finally:
        sources = {p.name: p.read_text() for p in root.glob("*.cpp")}
        (root / "pilot-return.txt").write_text(json.dumps({"report": report, "sources": sources}, indent=2) + "\n")
        print("PILOT_OUTPUT", root, flush=True)


if __name__ == "__main__":
    main()
