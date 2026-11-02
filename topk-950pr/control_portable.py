"""Run same-process alternating controls without changing the deployed kernel."""

import argparse
import hashlib
import importlib.util
import json
import os
import statistics
import subprocess
from pathlib import Path

import torch
import torch_npu  # noqa: F401

from tileops._kernels.attention.topk_select_ascend import topk_select_ascend


def check_indices(indices, reference, length):
    invalid = [
        {"row": row, "slot": slot, "value": value}
        for row, values in enumerate(indices)
        for slot, value in enumerate(values)
        if not 0 <= value < length
    ]
    result = {"invalid_count": len(invalid), "invalid_examples": invalid[:8]}
    if invalid:
        result["status"] = "out_of_bounds"
    elif any(len(set(row)) != len(row) for row in indices):
        result["status"] = "duplicate_indices"
    elif [sorted(row) for row in indices] != reference:
        result["status"] = "wrong_selected_set"
    else:
        result["status"] = "passed"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=1)
    parser.add_argument("--length", type=int, default=16384)
    parser.add_argument("--k", type=int, default=2048)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--diagnostic", action="store_true", help="Check all versions; do not time")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    torch.npu.set_device(0)
    torch.manual_seed(20261030)
    torch.npu.manual_seed_all(20261030)
    x = torch.randn((args.rows, args.length, 1), device="npu", dtype=torch.float32)
    starts = torch.zeros(args.rows, device="npu", dtype=torch.int32)
    ends = torch.full_like(starts, args.length)
    reference = (
        x[:, :, 0]
        .cpu()
        .argsort(dim=1, descending=True, stable=True)[:, : args.k]
        .sort(dim=1)
        .values.tolist()
    )
    programs = {}
    source_refs = {
        "v0.1.0": "topk-npu-v0.1.0",
        "v0.1.2": "topk-npu-v0.1.2",
        "v0.1.4-before-scan": "49aaea3608d97d666f535053e974903547f94ad3",
    }
    source_hashes = {}
    for version, ref in source_refs.items():
        print("CONTROL_COMPILE", version, ref, flush=True)
        source_path = args.output / f"kernel-{version}.py"
        source_path.write_bytes(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(args.repo),
                    "show",
                    f"{ref}:src/tileops/_kernels/attention/topk_select_ascend.py",
                ]
            )
        )
        source_hashes[version] = hashlib.sha256(source_path.read_bytes()).hexdigest()
        spec = importlib.util.spec_from_file_location(
            version.replace(".", "_").replace("-", "_"), source_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        programs[version] = module.topk_select_ascend(
            args.rows, args.length, args.k, args.workers, 1
        )
    for threads in [128, 256]:
        print("CONTROL_COMPILE", f"candidate-h{threads}", flush=True)
        programs[f"candidate-h{threads}"] = topk_select_ascend(
            args.rows, args.length, args.k, args.workers, 1, COARSE=True, H=threads
        )
    print("CONTROL_COMPILE candidate-serial-h128", flush=True)
    programs["candidate-serial-h128"] = topk_select_ascend(
        args.rows, args.length, args.k, args.workers, 1, COARSE=True, H=128, PARALLEL_SCAN=False
    )
    outputs = {
        name: torch.empty((args.rows, args.k), device="npu", dtype=torch.int32) for name in programs
    }
    sources = {}
    validation = {
        "diagnostic_only": args.diagnostic,
        "tileops_commit": subprocess.check_output(
            ["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True
        ).strip(),
        "input_sha256": hashlib.sha256(x.cpu().numpy().tobytes()).hexdigest(),
        "generated_source_sha256": sources,
        "checks": [],
    }

    def validate(name, phase):
        result = {"version": name, "phase": phase}
        result.update(check_indices(outputs[name].cpu().tolist(), reference, args.length))
        validation["checks"].append(result)
        (args.output / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
        print("CONTROL_CHECK", json.dumps(result), flush=True)
        if result["status"] != "passed" and not args.diagnostic:
            raise AssertionError(f"{name}: {phase}: {result['status']}; see validation.json")
        return result["status"] == "passed"

    for name, program in programs.items():
        source = program.get_kernel_source()
        (args.output / f"{name}.cpp").write_text(source)
        sources[name] = hashlib.sha256(source.encode()).hexdigest()
        print("CONTROL_RUN", name, flush=True)
        outputs[name].fill_(-1)
        program(x, starts, ends, outputs[name])
        torch.npu.synchronize()
        if not validate(name, "single_call"):
            continue
        for _ in range(20):
            program(x, starts, ends, outputs[name])
        torch.npu.synchronize()
        validate(name, "after_warmup")
    torch.npu.synchronize()
    for name in outputs:
        validate(name, "after_all_versions")
    if args.diagnostic:
        failed = sorted(
            {row["version"] for row in validation["checks"] if row["status"] != "passed"}
        )
        print("CONTROL_DIAGNOSTIC_FAILED_VERSIONS", json.dumps(failed), flush=True)
        assert not failed, "Diagnostic failures recorded in validation.json; no timings produced"
        return
    for name, program in programs.items():
        for _ in range(10):
            program(x, starts, ends, outputs[name])
    torch.npu.synchronize()
    begin, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
    samples = {name: [] for name in programs}
    names = list(programs)
    for iteration in range(50):
        for name in names if iteration % 2 == 0 else names[::-1]:
            begin.record()
            programs[name](x, starts, ends, outputs[name])
            end.record()
            end.synchronize()
            samples[name].append(begin.elapsed_time(end) * 1000)
    for name in outputs:
        validate(name, "after_timing")
    result = {
        "shape": [args.rows, args.length, 1],
        "k": args.k,
        "workers": args.workers,
        "input_sha256": hashlib.sha256(x.cpu().numpy().tobytes()).hexdigest(),
        "physical_device": os.environ["ASCEND_RT_VISIBLE_DEVICES"],
        "generated_source_sha256": sources,
        "source_refs": source_refs,
        "historical_kernel_source_sha256": source_hashes,
        "candidate_scan_modes": {
            "candidate-h128": "parallel-16x16",
            "candidate-h256": "parallel-16x16",
            "candidate-serial-h128": "serial-256",
        },
        "event_samples_us": samples,
        "event_median_us": {name: statistics.median(v) for name, v in samples.items()},
        "scan_event_speedup_vs_previous_h128": statistics.median(samples["v0.1.4-before-scan"])
        / statistics.median(samples["candidate-h128"]),
        "scan_event_speedup_vs_serial_ablation_h128": statistics.median(
            samples["candidate-serial-h128"]
        )
        / statistics.median(samples["candidate-h128"]),
        "correctness": "finite random input; bounds, unique, threshold, equal selected sets",
        "timing": "same process, alternating forward/reverse order; preallocated device events",
    }
    (args.output / "control.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["event_median_us"], indent=2), flush=True)
    print(
        "Scan event speedup vs previous H128:",
        result["scan_event_speedup_vs_previous_h128"],
        flush=True,
    )


if __name__ == "__main__":
    main()
