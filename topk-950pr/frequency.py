"""Sample read-only device telemetry during bounded single/multi-worker load."""

import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

import torch
import torch_npu  # noqa: F401 -- register the NPU backend

from tileops._kernels.attention.topk_select_ascend import topk_select_ascend

root = Path(os.environ["EVIDENCE"])
torch.npu.set_device(0)
torch.manual_seed(20261030)
torch.npu.manual_seed_all(20261030)
stop = threading.Event()
phase = ["preparing"]
samples = []
sampling_errors = []


def sample():
    while not stop.is_set():
        started = time.monotonic()
        label = phase[0]
        item = {"start_monotonic": started, "phase_start": label}
        for kind in ["common", "usages"]:
            try:
                result = subprocess.run(
                    [
                        os.environ["TOPK_NPU_SMI"],
                        "info",
                        "-t",
                        kind,
                        "-i",
                        os.environ["TOPK_DEVICE"],
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                sampling_errors.append({"phase": label, "query": kind, "error": str(exc)})
                stop.set()
                return
            item[kind] = {
                "returncode": result.returncode,
                "text": result.stdout,
                "fields": dict(re.findall(r"^\s*([^:\n]+?)\s*:\s*(.*?)\s*$", result.stdout, re.M)),
            }
            if result.returncode:
                sampling_errors.append(
                    {
                        "phase": label,
                        "query": kind,
                        "returncode": result.returncode,
                        "output": result.stdout + result.stderr,
                    }
                )
                stop.set()
                return
        item["phase_end"] = phase[0]
        item["end_monotonic"] = time.monotonic()
        samples.append(item)
        stop.wait(0.5)


thread = threading.Thread(target=sample, daemon=True)
thread.start()
loads = []
try:
    for label, rows, length in [("decode", 1, 16384), ("small", 128, 65536)]:
        phase[0] = "preparing-" + label
        x = torch.randn((rows, length, 1), device="npu")
        starts = torch.zeros(rows, device="npu", dtype=torch.int32)
        ends = torch.full_like(starts, length)
        out = torch.empty((rows, 2048), device="npu", dtype=torch.int32)
        workers = min(rows, torch.npu.get_device_properties(0).vector_core_num)
        program = topk_select_ascend(rows, length, 2048, workers, 1, COARSE=True, H=128)
        for _ in range(10):
            program(x, starts, ends, out)
        torch.npu.synchronize()
        ids = out.long()
        assert bool(((ids >= 0) & (ids < length)).all().item())
        assert bool((ids.sort(dim=1).values.diff(dim=1) != 0).all().item())
        threshold = x[:, :, 0].gather(1, ids).min(dim=1).values
        assert bool(((x[:, :, 0] > threshold[:, None]).sum(dim=1) < 2048).all().item())
        torch.npu.synchronize()
        print("LOAD_BEGIN", label, "workers", workers, flush=True)
        phase[0] = label
        started = time.monotonic()
        calls = 0
        while time.monotonic() - started < 8:
            for _ in range(5):
                program(x, starts, ends, out)
            torch.npu.synchronize()
            calls += 5
        finished = time.monotonic()
        phase[0] = "idle"
        loads.append(
            {
                "label": label,
                "workers": workers,
                "calls": calls,
                "host_elapsed_s": finished - started,
                "start_monotonic": started,
                "end_monotonic": finished,
            }
        )
        print("LOAD_DONE", label, calls, flush=True)
finally:
    stop.set()
    thread.join(35)
    if thread.is_alive():
        sampling_errors.append({"error": "Telemetry thread did not stop within 35 seconds"})
result = {
    "loads": loads,
    "samples": samples,
    "sampling_errors": sampling_errors,
    "vector_clock_independently_measured": False,
    "purpose": "telemetry only; not formal latency evidence; no clock settings changed",
}
(root / "frequency-load.json").write_text(json.dumps(result, indent=2))
for item in samples:
    if item["phase_start"] == item["phase_end"] and item["phase_start"] in ["decode", "small"]:
        print(
            "TELEMETRY",
            item["phase_start"],
            item["common"]["fields"].get("Aicore curFreq(MHZ)"),
            item["usages"]["fields"].get("Aivector Usage Rate(%)"),
            flush=True,
        )
assert not sampling_errors, "Telemetry incomplete; inspect frequency-load.json"
