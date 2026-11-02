"""Check counter viability and instrumentation perturbation in a private process."""

import argparse
import datetime
import faulthandler
import hashlib
import inspect
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import traceback
from pathlib import Path

VERSION = "20261102-probe1"
EXPECTED_TICKS_PER_US = 1000  # CANN GetSystemCycle documentation for Ascend 950.


def check_generated_source(code, mode, repeats):
    clocks = [m.start() for m in re.finditer(r"tileops_probe_clock\(", code)]
    fences = [m.start() for m in re.finditer(r"tileops_probe_fence\(", code)]
    if mode == 0:
        assert not clocks and not fences, "Plain source unexpectedly contains observer calls"
        return
    assert len(fences) == 3, "Expected fence definition and two calls"
    assert len(clocks) == (3 if mode == 2 else 1), "Unexpected number of clock definitions/calls"
    if mode == 2:
        assert fences[1] < clocks[1] < fences[2] < clocks[2], "Counter/fence source order changed"
        if repeats:
            assert "asc_vf_call" in code[clocks[1] : fences[2]], "No VF launch in counter region"


def analyze(cases):
    summary = {}
    for name, item in cases.items():
        if not item["event_samples_us"] or min(item["event_samples_us"]) <= 0:
            raise ValueError(f"Nonpositive or missing NPU event samples: {name}")
        row = {
            "event_sample_count": len(item["event_samples_us"]),
            "counter_sample_count": len(item["counter_samples"]),
            "event_median_us": statistics.median(item["event_samples_us"]),
        }
        if item["counter_samples"]:
            row["counter_median"] = statistics.median(item["counter_samples"])
            row["counter_interval_us_at_documented_rate"] = (
                row["counter_median"] / EXPECTED_TICKS_PER_US
            )
        summary[name] = row
    for repeats in [1, 16, 64]:
        plain = summary[f"r{repeats}-plain"]["event_median_us"]
        fenced = summary[f"r{repeats}-fenced"]["event_median_us"]
        timed = summary[f"r{repeats}-timed"]["event_median_us"]
        summary[f"r{repeats}-changes"] = {
            "fenced_vs_plain_event_percent": (fenced / plain - 1) * 100,
            "timed_vs_fenced_event_percent": (timed / fenced - 1) * 100,
            "timed_vs_plain_event_percent": (timed / plain - 1) * 100,
            "timed_event_delta_vs_empty_us": timed - summary["r0-timed"]["event_median_us"],
            "counter_delta_vs_empty_us_at_documented_rate": (
                summary[f"r{repeats}-timed"]["counter_median"]
                - summary["r0-timed"]["counter_median"]
            )
            / EXPECTED_TICKS_PER_US,
        }
    event_delta = summary["r64-timed"]["event_median_us"] - summary["r16-timed"]["event_median_us"]
    tick_delta = summary["r64-timed"]["counter_median"] - summary["r16-timed"]["counter_median"]
    observed_rate = tick_delta / event_delta if event_delta > 0 else None
    ticks = [summary[f"r{r}-timed"]["counter_median"] for r in [0, 1, 16, 64]]
    checks = {
        "all_counter_intervals_positive": all(
            value > 0 for item in cases.values() for value in item["counter_samples"]
        ),
        "counter_medians_increase_with_work": all(
            a < b for a, b in zip(ticks[:-1], ticks[1:], strict=True)
        ),
        "observed_ticks_per_event_us_from_64_minus_16": observed_rate,
        "counter_intervals_fit_inside_events_at_documented_rate": all(
            ticks / EXPECTED_TICKS_PER_US <= event
            for item in cases.values()
            if item["counter_samples"]
            for ticks, event in zip(item["counter_samples"], item["event_samples_us"], strict=True)
        ),
        "rate_within_10_percent_of_documentation": (
            observed_rate is not None and abs(observed_rate / EXPECTED_TICKS_PER_US - 1) <= 0.1
        ),
    }
    return summary, checks


def execute(report, root, device):
    import resource

    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    faulthandler.enable()
    faulthandler.dump_traceback_later(120, repeat=True)
    here = Path(__file__).resolve().parent
    report["stage"] = "manifest"
    report["probe_files_sha256"] = {}
    for line in (here / "MANIFEST.sha256").read_text().splitlines():
        expected, name = line.split("  ", 1)
        path = (here / name).resolve()
        assert path.is_relative_to(here)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, f"Probe file changed: {name}"
        report["probe_files_sha256"][name] = actual
    report["stage"] = "environment"
    cann_home = os.environ.get("ASCEND_HOME_PATH")
    assert cann_home and Path(cann_home).is_dir(), (
        "Load the existing CANN toolkit environment first"
    )
    cann = Path(cann_home).resolve()
    assert shutil.which("bisheng"), "bisheng is missing from PATH"
    report["compiler_version"] = subprocess.check_output(
        ["bisheng", "--version"], text=True, timeout=30
    ).splitlines()[:4]
    for path in [
        cann / "x86_64-linux/ascend_toolkit_install.info",
        cann / "ascend_toolkit_install.info",
    ]:
        if path.is_file():
            report["cann_installation_info"] = path.read_text()
            break
    smi = os.environ.get("TOPK_NPU_SMI") or shutil.which("npu-smi")
    assert smi, "npu-smi is missing"
    health = subprocess.check_output(
        [smi, "info", "-t", "health", "-i", str(device)], text=True, timeout=30
    )
    (root / "health.txt").write_text(health)
    assert any(
        "Health Status" in line and line.split(":")[-1].strip() == "OK"
        for line in health.splitlines()
    )
    import tilelang
    import tilelang.ascend.language as T
    import torch
    import torch_npu
    from kernels import timer_probe

    report["runtime"] = {
        "python": sys.executable,
        "torch": torch.__version__,
        "torch_npu": torch_npu.__version__,
        "tilelang": tilelang.__version__,
        "tilelang_path": tilelang.__file__,
        "cann_home": str(cann),
        "Kernel_signature": str(inspect.signature(T.Kernel)),
        "has_call_extern": hasattr(T, "call_extern"),
    }
    assert torch.npu.is_available()
    torch.npu.set_device(0)
    chip = torch.npu.get_device_name(0)
    report["device"] = chip
    assert "950" in chip, "This counter conversion is intended for Ascend 950 only"
    x_cpu = torch.arange(4096, dtype=torch.float32)
    x = x_cpu.npu()
    programs, buffers = {}, {}
    cases = report["cases"] = {}
    configurations = [(r, mode) for r in [1, 16, 64] for mode in [0, 1, 2]] + [(0, 2)]
    for repeats, mode in configurations:
        name = f"r{repeats}-" + ["plain", "fenced", "timed"][mode]
        report["stage"] = "compile:" + name
        print("PROBE_COMPILE", name, flush=True)
        program = timer_probe(4096, repeats, mode)
        code = program.get_kernel_source()
        (root / (name + ".cpp")).write_text(code)
        check_generated_source(code, mode, repeats)
        y = torch.empty_like(x)
        clocks = torch.full((2,), -1, device="npu", dtype=torch.int64)
        for _ in range(5):
            program(x, y, clocks)
        torch.npu.synchronize()
        assert torch.equal(y.cpu(), x_cpu + repeats), name
        programs[name] = program
        buffers[name] = (y, clocks)
        cases[name] = {
            "repeats": repeats,
            "mode": mode,
            "generated_source_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "execution_backend": str(program.execution_backend),
            "event_samples_us": [],
            "counter_samples": [],
        }
    report["stage"] = "sampling"
    begin, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
    names = list(programs)
    for iteration in range(50):
        for name in names if iteration % 2 == 0 else names[::-1]:
            report["stage"] = "sample:" + name
            if iteration == 0:
                print("PROBE_SAMPLE", name, flush=True)
            y, clocks = buffers[name]
            clocks.fill_(-1)
            begin.record()
            programs[name](x, y, clocks)
            end.record()
            end.synchronize()
            cases[name]["event_samples_us"].append(begin.elapsed_time(end) * 1000)
            values = clocks.cpu().tolist()  # Same transfer outside every variant's event span.
            if cases[name]["mode"] == 2:
                assert values[0] > 0 and values[1] > values[0], (name, values)
                cases[name]["counter_samples"].append(values[1] - values[0])
    report["stage"] = "output_validation"
    assert torch.equal(x.cpu(), x_cpu), "Input was modified"
    for name, (y, _clocks) in buffers.items():
        assert torch.equal(y.cpu(), x_cpu + cases[name]["repeats"]), name
    report["outputs_equal_reference"] = True
    report["summary"], report["checks"] = analyze(cases)
    report["status"] = "completed"
    report["stage"] = "review_required"
    faulthandler.cancel_dump_traceback_later()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=int(os.environ.get("TOPK_DEVICE", "0")))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    private = Path("/home/y00937463").resolve()
    root = (
        args.output
        or private / "runs" / datetime.datetime.now().strftime("timer-probe-%Y%m%d-%H%M%S")
    ).resolve()
    assert root.is_relative_to(private) and root != private, (
        "Use a fresh directory in the private home"
    )
    assert args.device >= 0
    root.mkdir(parents=True, exist_ok=False)
    for key, relative in {
        "TMPDIR": "tmp",
        "XDG_CACHE_HOME": "cache",
        "TILELANG_CACHE_DIR": "cache/tilelang",
        "ASCEND_CACHE_PATH": "cache/cann",
        "ASCEND_WORK_PATH": "cache/work",
        "ASCEND_PROCESS_LOG_PATH": "logs",
        "TORCH_EXTENSIONS_DIR": "cache/torch",
        "TORCHINDUCTOR_CACHE_DIR": "cache/inductor",
    }.items():
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ.update(
        ASCEND_RT_VISIBLE_DEVICES=str(args.device),
        TASK_QUEUE_ENABLE="0",
        PYTHONDONTWRITEBYTECODE="1",
    )
    sys.dont_write_bytecode = True
    report = {
        "version": VERSION,
        "status": "incomplete",
        "stage": "starting",
        "physical_device": args.device,
        "documented_ticks_per_us": EXPECTED_TICKS_PER_US,
        "stage_profiling_accepted": False,
        "timing_scope": "Events include launch, input load and output store; counter interval measures dependent UB VF work plus observer costs. Compare workload deltas, not absolute equality.",
    }
    try:
        execute(report, root, args.device)
    except Exception as exc:
        report.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        (root / "probe-report.json").write_text(json.dumps(report, indent=2) + "\n")
        brief = {key: value for key, value in report.items() if key != "cases"}
        text = json.dumps(brief, indent=2) + "\n"
        (root / "probe-summary.txt").write_text(text)
        print(text, flush=True)
        print("PROBE_OUTPUT", root, flush=True)


if __name__ == "__main__":
    main()
