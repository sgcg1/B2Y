"""Check a 512-KiB transfer without importing TileLang or TopK."""

import argparse
import json
import os
import time
from pathlib import Path

import torch
import torch_npu  # noqa: F401 -- register the NPU backend

parser = argparse.ArgumentParser()
parser.add_argument("--threads", type=int)
args = parser.parse_args()
if args.threads is not None:
    torch.set_num_threads(args.threads)
print("TORCH_CPU_THREADS", torch.get_num_threads(), flush=True)
print("DEVICE_BEGIN", flush=True)
torch.npu.set_device(0)
print("DEVICE_OK", flush=True)
x = torch.arange(131072, dtype=torch.float32)
print("H2D_BEGIN", flush=True)
start = time.monotonic()
y = x.npu()
torch.npu.synchronize()
print("H2D_OK", time.monotonic() - start, flush=True)
print("D2H_BEGIN", flush=True)
actual = y.cpu()
assert torch.equal(actual, x)
result = {
    "threads": torch.get_num_threads(),
    "elements": x.numel(),
    "bytes": x.numel() * 4,
    "roundtrip_ok": True,
    "wall_s": time.monotonic() - start,
}
Path(os.environ["EVIDENCE"], "transfer-" + str(args.threads) + ".json").write_text(
    json.dumps(result, indent=2)
)
print(json.dumps(result), flush=True)
