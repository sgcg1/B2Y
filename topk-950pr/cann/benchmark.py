"""Benchmark a fixed-shape OM with preallocated FP32/INT32 buffers."""

import ctypes as C
import hashlib
import json
import os
import statistics
import sys
from pathlib import Path

import torch
import torch_npu

root = Path(os.environ["EVIDENCE"])
rows, length, k = map(int, sys.argv[1:4])
name = sys.argv[4]
print("SET_DEVICE_BEGIN", flush=True)
torch.npu.set_device(0)
print("SET_DEVICE_OK", flush=True)
torch.manual_seed(20261030)
torch.npu.manual_seed_all(20261030)
api = C.CDLL(os.environ["ASCEND_HOME_PATH"] + "/lib64/libascendcl.so", mode=C.RTLD_GLOBAL)
P = C.c_void_p
U = C.c_uint32
S = C.c_size_t


def bind(name, args, ret=C.c_int):
    fn = getattr(api, name)
    fn.argtypes, fn.restype = args, ret
    return fn


def check(status):
    if status:
        raise RuntimeError(f"ACL error {status}")


load = bind("aclmdlLoadFromFile", [C.c_char_p, C.POINTER(U)])
desc_new = bind("aclmdlCreateDesc", [], P)
desc_get = bind("aclmdlGetDesc", [P, U])
num_in = bind("aclmdlGetNumInputs", [P], S)
num_out = bind("aclmdlGetNumOutputs", [P], S)
out_dtype = bind("aclmdlGetOutputDataType", [P, S])
in_size = bind("aclmdlGetInputSizeByIndex", [P, S], S)
out_size = bind("aclmdlGetOutputSizeByIndex", [P, S], S)
dataset_new = bind("aclmdlCreateDataset", [], P)
buffer_new = bind("aclCreateDataBuffer", [P, S], P)
dataset_add = bind("aclmdlAddDatasetBuffer", [P, P])
execute = bind("aclmdlExecuteAsync", [U, P, P, P])
unload = bind("aclmdlUnload", [U])
event_new = bind("aclrtCreateEvent", [C.POINTER(P)])
event_record = bind("aclrtRecordEvent", [P, P])
event_sync = bind("aclrtSynchronizeEvent", [P])
elapsed = bind("aclrtEventElapsedTime", [C.POINTER(C.c_float), P, P])

print("LOAD_MODEL_BEGIN", flush=True)
model = U()
check(load(str(root / (name + ".om")).encode(), C.byref(model)))
print("LOAD_MODEL_OK", flush=True)
desc = desc_new()
check(desc_get(desc, model))
assert num_in(desc) == 1 and num_out(desc) == 2
assert out_dtype(desc, 0) == 0 and out_dtype(desc, 1) == 3
assert in_size(desc, 0) == rows * length * 4
assert [out_size(desc, i) for i in range(2)] == [rows * k * 4] * 2
free, total = torch.npu.mem_get_info()
assert free > (rows * length * 4 + rows * k * 8) * 1.25 + 2**30, (free, total)
x = torch.randn((rows, length), dtype=torch.float32, device="npu")
values = torch.empty((rows, k), dtype=torch.float32, device="npu")
indices = torch.empty((rows, k), dtype=torch.int32, device="npu")
buffers = []


def dataset(tensors):
    ds = dataset_new()
    for tensor in tensors:
        buf = buffer_new(P(tensor.data_ptr()), tensor.numel() * tensor.element_size())
        buffers.append(buf)
        check(dataset_add(ds, buf))
    return ds


inputs, outputs = dataset([x]), dataset([values, indices])
stream = P(torch.npu.current_stream().npu_stream)


def run():
    check(execute(model, inputs, outputs, stream))


print("INPUT_READY", flush=True)
torch.npu.synchronize()
print("INPUT_SYNC_OK", flush=True)
for _ in range(10):
    run()
print("WARMUP_QUEUED", flush=True)
torch.npu.synchronize()
print("WARMUP_OK", flush=True)

# Verify full input domain in bounded chunks outside the timing region.
input_hash = hashlib.sha256()
for start in range(0, rows, 128):
    a = x[start : start + 128]
    input_hash.update(a.cpu().numpy().tobytes())
    ids = indices[start : start + 128].long()
    vals = values[start : start + 128]
    assert bool(((ids >= 0) & (ids < length)).all().item())
    actual = a.gather(1, ids)
    if not bool((actual == vals).all().item()):
        print(
            "value_mismatch",
            "max_abs",
            (actual - vals).abs().max().item(),
            "sample_values",
            vals[0, :8].cpu().tolist(),
            "sample_expected",
            actual[0, :8].cpu().tolist(),
            flush=True,
        )
        raise AssertionError("Gathered FP32 values differ")
    assert bool((ids.sort(dim=1).values.diff(dim=1) != 0).all().item())
    minimum = vals.min(dim=1).values
    assert bool(((a > minimum[:, None]).sum(dim=1) < k).all().item())
torch.npu.synchronize()
for _ in range(10):
    run()
torch.npu.synchronize()
samples = []
begin, end = P(), P()
check(event_new(C.byref(begin)))
check(event_new(C.byref(end)))
for _ in range(50):
    check(event_record(begin, stream))
    run()
    check(event_record(end, stream))
    check(event_sync(end))
    ms = C.c_float()
    check(elapsed(C.byref(ms), begin, end))
    samples.append(ms.value)

result = dict(
    name=name,
    shape=[1, rows, length, 1],
    k=k,
    input_dtype="FP32",
    indices_dtype="INT32",
    largest=True,
    sorted=False,
    sort_policy=0,
    static_model=True,
    correctness="all rows, gather, unique indices, threshold certificate",
    warmup=10,
    input_sha256=input_hash.hexdigest(),
    samples_ms=samples,
    median_ms=statistics.median(samples),
    min_ms=min(samples),
    mean_ms=statistics.mean(samples),
    timing="device events around aclmdlExecuteAsync; model scheduling included",
    physical_device=os.environ["ASCEND_RT_VISIBLE_DEVICES"],
    device_name=torch.npu.get_device_name(0),
)
(root / (name + "-timing.json")).write_text(json.dumps(result, indent=2))
print(json.dumps(result), flush=True)

# Profile only model executions, excluding allocation, RNG, validation and events.
with torch_npu.profiler.profile(
    activities=[torch_npu.profiler.ProfilerActivity.CPU, torch_npu.profiler.ProfilerActivity.NPU],
    schedule=torch_npu.profiler.schedule(wait=0, warmup=1, active=1, repeat=1),
    on_trace_ready=torch_npu.profiler.tensorboard_trace_handler(
        str(root / ("profile-final-" + name))
    ),
) as prof:
    run()
    torch.npu.synchronize()
    prof.step()
    for _ in range(60):
        run()
        torch.npu.synchronize()
    prof.step()
torch.npu.synchronize()
check(unload(model))
