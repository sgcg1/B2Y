"""Solution-A P0 capability probe: how does TileLang lower a 256-bin histogram?

Determines, on the server's TileLang build:
  1. Which histogram/scan/sort/atomic primitives does tilelang.ascend.language expose?
  2. Does the per-element atomic histogram lower to atomic scatter (control)?
  3. Does the per-bucket masked-reduction histogram lower atomic-free?
  4. Do the two forms agree on a real input (correctness)?

Writes per-candidate generated C++ (*.cpp), probe-report.json and probe-summary.txt
into a fresh private output directory. This does not modify TopK or the shared env.
"""

import argparse
import datetime
import faulthandler
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

VERSION = "20261104-vhist-probe-r1"
N = 16384

INTROSPECT_KEYWORDS = [
    "hist", "scan", "cumsum", "prefix", "reduce", "sort", "topk",
    "atomic", "sum", "gather", "scatter", "shuffle", "bucket", "rank",
]

CURATED_ATTRS = [
    "histogram", "vhist", "cumsum", "prefix_sum", "segmented_sum", "reduce_sum",
    "sort", "argsort", "topk", "gather", "scatter", "atomic_add", "atomic_max",
    "atomic_min", "inclusive_scan", "exclusive_scan",
]

MARKERS = ["vhist", "histogram", "atomic", "reduce", "vcmp", "compare", "gather"]


def marker_counts(source: str):
    low = source.lower()
    return {m: low.count(m) for m in MARKERS if m in low}


def introspect(T):
    exported = [n for n in dir(T) if not n.startswith("_")]
    matching = {}
    for name in exported:
        if any(kw in name.lower() for kw in INTROSPECT_KEYWORDS):
            obj = getattr(T, name)
            matching[name] = (
                str(inspect.signature(obj)) if callable(obj) else type(obj).__name__
            )
    return {
        "matching_exports": matching,
        "curated_hasattr": {n: hasattr(T, n) for n in CURATED_ATTRS},
    }


def execute(report, root, device):
    import torch
    import torch_npu
    import tilelang
    import tilelang.ascend.language as T
    from kernels import hist_atomic_scatter, hist_bucket_reduce

    report["runtime"] = {
        "python": sys.executable,
        "torch": torch.__version__,
        "torch_npu": torch_npu.__version__,
        "tilelang": getattr(tilelang, "__version__", None),
        "tilelang_path": tilelang.__file__,
    }
    report["introspection"] = introspect(T)

    assert torch.npu.is_available()
    torch.npu.set_device(0)
    chip = torch.npu.get_device_name(0)
    report["device"] = chip

    torch.manual_seed(0)
    x = torch.randn(N, dtype=torch.float32).npu()

    cases = report["cases"] = {}
    tensors = {}
    factories = [
        ("hist_atomic_scatter", hist_atomic_scatter),
        ("hist_bucket_reduce", hist_bucket_reduce),
    ]
    for name, factory in factories:
        report["stage"] = "compile:" + name
        print("PROBE_COMPILE", name, flush=True)
        case = {"status": "compiled"}
        try:
            program = factory(N)
            source = program.get_kernel_source()
        except Exception as exc:
            case.update(
                status="compile_failed",
                error_type=type(exc).__name__,
                error=str(exc),
                traceback=traceback.format_exc(),
            )
            cases[name] = case
            continue
        (root / (name + ".cpp")).write_text(source)
        case.update(
            source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            source_len=len(source),
            source_markers=marker_counts(source),
            has_atomic_marker=("atomic" in source.lower()),
            has_vhist_marker=("vhist" in source.lower()),
            has_histogram_marker=("histogram" in source.lower()),
            execution_backend=str(getattr(program, "execution_backend", None)),
        )
        out = torch.empty(256, dtype=torch.int32, device="npu")
        program(x, out)
        torch.npu.synchronize()
        case["hist_sum"] = int(out.sum().item())
        cases[name] = case
        tensors[name] = out.cpu()

    if set(tensors) == {"hist_atomic_scatter", "hist_bucket_reduce"}:
        a = tensors["hist_atomic_scatter"]
        b = tensors["hist_bucket_reduce"]
        report["cross_check"] = {
            "histograms_equal": bool(torch.equal(a, b)),
            "both_sum_to_n": bool(a.sum().item() == N and b.sum().item() == N),
        }

    report["status"] = "completed"
    report["stage"] = "review_required"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=int(os.environ.get("TOPK_DEVICE", "0")))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    private = Path(os.environ.get("TOPK_HOME", "/home/y00937463")).resolve()
    root = (
        args.output
        or private / "runs" / datetime.datetime.now().strftime("vhist-probe-r1-%Y%m%d-%H%M%S")
    ).resolve()
    assert root.is_relative_to(private) and root != private, (
        "Use a fresh directory under TOPK_HOME"
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
        "purpose": "Determine TileLang histogram lowering (atomic scatter vs vector/SIMD).",
    }
    try:
        faulthandler.enable()
        execute(report, root, args.device)
    except Exception as exc:
        report.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        faulthandler.disable()
        (root / "probe-report.json").write_text(json.dumps(report, indent=2) + "\n")
        brief = {key: value for key, value in report.items() if key != "cases"}
        text = json.dumps(brief, indent=2) + "\n"
        (root / "probe-summary.txt").write_text(text)
        print(text, flush=True)
        print("PROBE_OUTPUT", root, flush=True)


if __name__ == "__main__":
    main()