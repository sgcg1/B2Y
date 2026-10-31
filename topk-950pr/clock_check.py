"""Check device-event intervals against enclosing host monotonic intervals."""

import hashlib
import json
import os
import statistics
import time
from pathlib import Path

import torch
import torch_npu  # noqa: F401 -- register the NPU backend

from tileops._kernels.attention.topk_select_ascend import topk_select_ascend

torch.npu.set_device(0)
torch.manual_seed(20261030)
torch.npu.manual_seed_all(20261030)
x = torch.randn((1, 16384, 1), device="npu")
starts = torch.zeros(1, device="npu", dtype=torch.int32)
ends = torch.full_like(starts, 16384)
out = torch.empty((1, 2048), device="npu", dtype=torch.int32)
program = topk_select_ascend(1, 16384, 2048, 1, 1, COARSE=True, H=128)
for _ in range(20):
    program(x, starts, ends, out)
torch.npu.synchronize()
begin, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
device = []
host = []
for _ in range(50):
    start = time.perf_counter_ns()
    begin.record()
    program(x, starts, ends, out)
    end.record()
    end.synchronize()
    stop = time.perf_counter_ns()
    device.append(begin.elapsed_time(end) * 1000)
    host.append((stop - start) / 1000)
result = {
    "device_event_samples_us": device,
    "enclosing_host_samples_us": host,
    "device_event_median_us": statistics.median(device),
    "enclosing_host_median_us": statistics.median(host),
    "device_interval_exceeds_enclosing_host_count": sum(
        d > h for d, h in zip(device, host, strict=True)
    ),
    "generated_source_sha256": hashlib.sha256(program.get_kernel_source().encode()).hexdigest(),
    "method": "host perf_counter_ns starts before begin.record and stops after end.synchronize",
    "host_clock": str(time.get_clock_info("perf_counter")),
}
Path(os.environ["EVIDENCE"], "clock-check.json").write_text(json.dumps(result, indent=2))
print(json.dumps({k: v for k, v in result.items() if "samples" not in k}), flush=True)
