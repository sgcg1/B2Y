"""Measure a fixed Decode diagnostic in a private process; production stays intact."""

import argparse
import faulthandler
import hashlib
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import traceback
from pathlib import Path

from instrument import SLOTS, SOURCE_SHA256, clone_source, transform


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.topk_select_ascend


def summarize(cases):
    result = {}
    for name, case in cases.items():
        events = case["event_samples_us"]
        result[name] = {
            "event_sample_count": len(events),
            "event_median_us": statistics.median(events),
            "event_min_us": min(events),
            "event_max_us": max(events),
        }
    baseline = result["production"]["event_median_us"]
    for name in ("traced", "fenced", "timed"):
        result[name]["event_change_vs_production_percent"] = (
            result[name]["event_median_us"] / baseline - 1
        ) * 100
    timed = cases["timed"]
    rows = timed["stage_samples_ticks"]
    result["timed"]["intervals"] = [
        {**slot, "slot": i, "median_us": statistics.median(row[i] for row in rows) / 1000}
        for i, slot in enumerate(SLOTS)
    ]
    result["timed"]["sum_of_intervals_median_us"] = (
        statistics.median(sum(row) for row in rows) / 1000
    )
    result["timed"]["envelope_median_us"] = (
        statistics.median(timed["envelope_samples_ticks"]) / 1000
    )
    return result


def execute(report, root, repo):
    import resource

    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    faulthandler.enable()
    faulthandler.dump_traceback_later(120, repeat=True)
    report["stage"] = "provenance"
    here = Path(__file__).resolve().parent
    report["tool_files_sha256"] = {}
    for line in (here / "MANIFEST.sha256").read_text().splitlines():
        expected, name = line.split("  ", 1)
        path = (here / name).resolve()
        assert path.is_relative_to(here)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == expected, f"Stage tool changed: {name}"
        report["tool_files_sha256"][name] = digest
    helper = here.parent / "topk-timer-probe/postproc.py"
    digest = hashlib.sha256(helper.read_bytes()).hexdigest()
    assert digest == "baa5a4b442e39fed0edf648dcf3b30a2846d1b7d9ee6a1975e7315f82ff90755", (
        "Probe2 parser changed"
    )
    report["tool_files_sha256"]["../topk-timer-probe/postproc.py"] = digest
    source_relative = "src/tileops/_kernels/attention/topk_select_ascend.py"
    raw = (repo / source_relative).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA256, "Unsupported kernel SHA; do not bypass"
    assert not subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"], text=True
    ).strip(), "Save tracked TileOPs modifications first"
    report["tileops_commit"] = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    report["production_kernel_sha256"] = SOURCE_SHA256
    report["stage"] = "environment"
    assert os.environ.get("ASCEND_HOME_PATH"), "Load the existing CANN environment first"
    report["compiler_version"] = subprocess.check_output(
        ["bisheng", "--version"], text=True, timeout=30
    ).splitlines()[:4]
    report["health_begin"] = subprocess.check_output(
        ["npu-smi", "info", "-t", "health", "-i", str(report["physical_device"])],
        text=True,
        timeout=30,
    )
    assert any(
        "Health Status" in line and line.split(":")[-1].strip() == "OK"
        for line in report["health_begin"].splitlines()
    )

    import tilelang
    import torch
    import torch_npu
    from tilelang.ascend.callback import register_ascend_postproc_callback

    report["runtime"] = {
        "python": sys.executable,
        "torch": torch.__version__,
        "torch_npu": torch_npu.__version__,
        "tilelang": tilelang.__version__,
        "tilelang_path": tilelang.__file__,
        "cann_home": str(Path(os.environ["ASCEND_HOME_PATH"]).resolve()),
    }
    torch.npu.set_device(0)
    report["device"] = torch.npu.get_device_name(0)
    assert "950" in report["device"]
    torch.manual_seed(20261030)
    torch.npu.manual_seed_all(20261030)
    x = torch.randn((1, 16384, 1), device="npu", dtype=torch.float32)
    x_cpu = x.cpu()
    report["input_sha256"] = hashlib.sha256(x_cpu.numpy().tobytes()).hexdigest()
    report["historical_decode_input_matches"] = (
        report["input_sha256"] == "c59b9485e9750eaf04d4668934c0383510a15b2cc9365ef9c6c4b9eaf2bf7593"
    )
    reference = x_cpu.reshape(-1).argsort(descending=True, stable=True)[:2048].sort().values
    starts = torch.zeros(1, device="npu", dtype=torch.int32)
    ends = torch.full_like(starts, 16384)
    (root / "production.py").write_bytes(raw)
    diagnostic = clone_source(raw)
    (root / "diagnostic.py").write_text(diagnostic, encoding="utf-8")
    report["diagnostic_python_sha256"] = hashlib.sha256(diagnostic.encode()).hexdigest()
    production = load(root / "production.py", "topk_stage_production")
    instrumented = load(root / "diagnostic.py", "topk_stage_diagnostic")
    report["captures"] = {}

    def callback(code, target):
        assert target.kind.name == "ascend"
        (root / "last-original.cpp").write_text(str(code), encoding="utf-8")
        patched, info = transform(str(code))
        name = ["traced", "fenced", "timed"][info["mode"]]
        assert name not in report["captures"], "Repeated callback; refuse ambiguous cache identity"
        (root / (name + "-original.cpp")).write_text(str(code), encoding="utf-8")
        (root / (name + "-postproc.cpp")).write_text(patched, encoding="utf-8")
        report["captures"][name] = info
        return patched

    programs, buffers = {}, {}
    cases = report["cases"] = {}
    for index, name in enumerate(("production", "traced", "fenced", "timed")):
        report["stage"] = "compile:" + name
        print("STAGE_COMPILE", name, flush=True)
        if name == "traced":
            register_ascend_postproc_callback(callback, override=True)
        program = (
            production(1, 16384, 2048, 1, 1, COARSE=True, H=128, PARALLEL_SCAN=True)
            if name == "production"
            else instrumented(
                1, 16384, 2048, 1, 1, COARSE=True, H=128, PARALLEL_SCAN=True, DIAG_MODE=index - 1
            )
        )
        code = program.get_kernel_source()
        (root / (name + "-api.cpp")).write_text(code, encoding="utf-8")
        if name != "production":
            assert name in report["captures"], "Postprocessor not observed; refuse stale cache"
            assert (
                hashlib.sha256(code.encode()).hexdigest()
                == report["captures"][name]["postproc_source_sha256"]
            ), "Unexpected source API capture point"
        out = torch.empty((1, 2048), device="npu", dtype=torch.int32)
        ticks = torch.full((128,), -1, device="npu", dtype=torch.int64)
        tags = torch.full((14,), -1, device="npu", dtype=torch.int32)
        trace = torch.full((5, 7), -1, device="npu", dtype=torch.int32)
        args = (x, starts, ends, out) + (() if name == "production" else (ticks, tags, trace))
        for _ in range(5):
            program(*args)
        torch.npu.synchronize()
        assert torch.equal(out.cpu().long().flatten().sort().values, reference), (
            name,
            "Wrong selected set",
        )
        programs[name] = (program, args)
        buffers[name] = (out, ticks, tags, trace)
        cases[name] = {
            "event_samples_us": [],
            "stage_samples_ticks": [],
            "envelope_samples_ticks": [],
            "timestamp_samples_ticks": [],
            "api_source_sha256": hashlib.sha256(code.encode()).hexdigest(),
        }
    begin, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
    for _ in range(5):
        begin.record()
        end.record()
        end.synchronize()
    names = list(programs)
    expected_trace = None
    for iteration in range(50):
        for name in names if iteration % 2 == 0 else names[::-1]:
            report["stage"] = f"sample:{iteration}:{name}"
            if iteration % 10 == 0:
                print("STAGE_SAMPLE", iteration, name, flush=True)
            out, ticks, tags, trace = buffers[name]
            ticks.fill_(-1)
            tags.fill_(-1)
            program, args = programs[name]
            begin.record()
            program(*args)
            end.record()
            end.synchronize()
            event = begin.elapsed_time(end) * 1000
            assert event > 0
            cases[name]["event_samples_us"].append(event)
            values = ticks.cpu().tolist()
            assert tags.cpu().tolist() == [-1] * 14, "Removed marker unexpectedly executed"
            if name == "timed":
                active = values[: 2 * len(SLOTS)]
                assert all(
                    a > 0 and b > a for a, b in zip(active[::2], active[1::2], strict=True)
                ), values
                assert all(a <= b for a, b in zip(active[:-1], active[1:], strict=True)), (
                    "Nonmonotonic stage stamps"
                )
                assert values[126] <= active[0] < active[-1] <= values[127]
                assert values[2 * len(SLOTS) : 126] == [-1] * (126 - 2 * len(SLOTS)), (
                    "Unexpected slot write"
                )
                interval = values[127] - values[126]
                assert interval / 1000 <= event + 0.001, ("Envelope exceeds event", values, event)
                cases[name]["stage_samples_ticks"].append(
                    [b - a for a, b in zip(active[::2], active[1::2], strict=True)]
                )
                cases[name]["envelope_samples_ticks"].append(interval)
                cases[name]["timestamp_samples_ticks"].append([values[126], *active, values[127]])
            else:
                assert values == [-1] * 128
            snapshot = trace.cpu().tolist()  # Same observer transfers outside every event.
            if name != "production":
                expected_trace = snapshot if expected_trace is None else expected_trace
                assert snapshot == expected_trace, (
                    "State trace differs",
                    name,
                    snapshot,
                    expected_trace,
                )
    report["state_trace_fields"] = [
        "quota_remaining",
        "output_committed",
        "threshold_bucket",
        "active_count",
        "accepted_count",
        "previous_candidate_count",
        "next_candidate_count",
    ]
    report["state_trace_after_each_round"] = expected_trace
    report["full_domain_branch_by_round"] = [
        i == 0 or row[5] > 2048 for i, row in enumerate(expected_trace)
    ]
    report["histogram_work_enabled_by_round"] = [True] + [row[0] > 0 for row in expected_trace[:-1]]
    report["full_rescan_by_round"] = [
        branch and enabled
        for branch, enabled in zip(
            report["full_domain_branch_by_round"],
            report["histogram_work_enabled_by_round"],
            strict=True,
        )
    ]
    report["stage"] = "output_validation"
    for name, (out, _, _, _) in buffers.items():
        assert torch.equal(out.cpu().long().flatten().sort().values, reference), name
    assert torch.equal(x.cpu(), x_cpu), "Input changed"
    # One additional untimed adversarial tie check; no new kernel configuration.
    x.fill_(1)
    for name, (program, args) in programs.items():
        program(*args)
        torch.npu.synchronize()
        assert torch.equal(
            buffers[name][0].cpu().long().flatten().sort().values, torch.arange(2048)
        ), (name, "Tie selection failed")
    report["outputs_random_and_all_equal_passed"] = True
    report["summary"] = summarize(cases)
    report["health_end"] = subprocess.check_output(
        ["npu-smi", "info", "-t", "health", "-i", str(report["physical_device"])],
        text=True,
        timeout=30,
    )
    report.update(status="completed", stage="review_required")
    faulthandler.cancel_dump_traceback_later()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", type=int, default=0)
    args = parser.parse_args()
    root = args.output.resolve()
    private = Path("/home/y00937463").resolve()
    assert root.is_relative_to(private) and root != private and args.device >= 0
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
        "version": "20261102-topk-stage1",
        "status": "incomplete",
        "stage": "starting",
        "physical_device": args.device,
        "shape": [1, 16384, 1],
        "k": 2048,
        "workers": 1,
        "threads": 128,
        "coarse": True,
        "documented_ticks_per_us": 1000,
        "stage_profiling_accepted": False,
        "timing_scope": "Diagnostic single-worker stage intervals include observer costs and inserted barriers; not uninstrumented stage costs. Trace writes are included in state_update_with_trace. No empty-cost subtraction.",
    }
    try:
        execute(report, root, args.repo.resolve())
    except Exception as exc:
        report.update(
            status="failed",
            error_type=type(exc).__name__,
            error=str(exc),
            traceback=traceback.format_exc(),
        )
        raise
    finally:
        text = json.dumps(report, indent=2) + "\n"
        (root / "stage-report.json").write_text(text, encoding="utf-8")
        # Return raw samples and useful source in the first reply, including on normal failure.
        names = [
            "production-api.cpp",
            "timed-original.cpp",
            "timed-postproc.cpp",
        ]
        if not (root / "timed-original.cpp").exists():
            names.append("last-original.cpp")
        bundle = {"report": report, "sources": {}}
        for name in names:
            path = root / name
            if path.exists():
                raw = path.read_bytes()
                bundle["sources"][name] = {
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "bytes": len(raw),
                    "text": raw.decode(),
                }
        (root / "stage-return.txt").write_text(
            json.dumps(bundle, indent=2) + "\n", encoding="utf-8"
        )
        print("STAGE_OUTPUT", root, flush=True)


if __name__ == "__main__":
    main()
