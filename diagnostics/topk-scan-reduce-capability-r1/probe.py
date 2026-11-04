"""Solution-A follow-up capability probe: how do cumsum / reduce_sum lower?

Follows up on topk-vhist-capability-r1, whose probe-summary.txt showed ``cumsum`` and
``reduce_sum`` exist as primitives but whose masked histogram reduced to a scalar
O(k*N) rescan. This probe compiles and exports the generated C++ for four kernels and
checks, from the source, whether the scan/reduce primitives actually lower to vector
SIMD instructions or fall back to scalar serial loops.

Writes per-candidate generated C++ (*.cpp), probe-report.json and probe-summary.txt
into a fresh private output directory. Does not modify TopK or the shared env.
"""

import argparse
import datetime
import faulthandler
import hashlib
import inspect
import json
import os
import sys
import traceback
from pathlib import Path

VERSION = "20261104-scan-reduce-probe-r1"

INTROSPECT_KEYWORDS = [
    "cumsum", "scan", "prefix", "reduce", "sum", "frag", "sort", "hist",
    "atomic", "gather", "scatter", "shuffle", "reducer",
]

CURATED_ATTRS = [
    "cumsum", "prefix_sum", "inclusive_scan", "exclusive_scan",
    "reduce_sum", "vreduce_sum", "reduce", "alloc_frag", "alloc_shared",
    "SimdVF", "SimtVF", "atomic_add", "alloc_reducer", "finalize_reducer",
]

# Substrings that indicate a vector lowering in the generated C++.
VECTOR_MARKERS = [
    "npu.reduce", "asc_reduce", "reduce", "cumsum", "scan", "prefix",
    "vadd", "vcmp", "vsub", "broadcast", "redsum", "vreduce",
]
# Substrings that indicate a scalar / serial lowering.
SCALAR_MARKERS = [
    "asc_atomic", "atomic", "threadIdx.x == 0", "thread == 0", "thread_id == 0",
]


def marker_counts(source: str):
    low = source.lower()
    return {m: low.count(m) for m in VECTOR_MARKERS + SCALAR_MARKERS if m in low}


def symbols(source: str):
    low = source.lower()
    return {
        "has_cumsum_symbol": "cumsum" in low,
        "has_reduce_symbol": ("reduce" in low),
        "has_scan_symbol": ("scan" in low) and ("asc_" in low or "npu" in low),
        "has_atomic_symbol": "atomic" in low,
        "has_thread0_serial": (
            "threadidx.x == 0" in low or "thread == 0" in low or "thread_id == 0" in low
        ),
    }


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
    from kernels import (
        cumsum_ub_probe,
        reduce_sum_ub_probe,
        vreduce_sum_simd_probe,
        serial_prefix_ctrl,
    )

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
    report["device"] = torch.npu.get_device_name(0)

    N = 4096
    R, C = 32, 32

    x1 = torch.arange(N, dtype=torch.int32).npu() + 1
    x2 = torch.randint(0, 8, (R, C), dtype=torch.int32).npu()

    cases = report["cases"] = {}
    tensors = {}

    factories = [
        ("cumsum_ub_probe", cumsum_ub_probe, (N,), x1, (N,)),
        ("serial_prefix_ctrl", serial_prefix_ctrl, (N,), x1, (N,)),
        ("reduce_sum_ub_probe", reduce_sum_ub_probe, (R, C), x2, (R,)),
        ("vreduce_sum_simd_probe", vreduce_sum_simd_probe, (R, C), x2, (R,)),
    ]

    for name, factory, sizes, x, out_shape in factories:
        report["stage"] = "compile:" + name
        print("PROBE_COMPILE", name, flush=True)
        case = {"status": "compiled"}
        try:
            program = factory(*sizes)
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
            symbols=symbols(source),
        )
        out = torch.empty(out_shape, dtype=torch.int32, device="npu")
        try:
            program(x, out)
            torch.npu.synchronize()
            case["ran"] = True
            cpu = out.cpu()
            case["out_head"] = cpu.flatten().tolist()[:8]
            case["out_sum"] = int(cpu.sum().item())
            tensors[name] = cpu
        except Exception as exc:
            case.update(
                ran=False,
                run_error_type=type(exc).__name__,
                run_error=str(exc),
                run_traceback=traceback.format_exc(),
            )
        cases[name] = case

    ref_prefix = torch.cumsum(x1.cpu(), dim=0)
    ref_rowsum = x2.cpu().sum(dim=1)

    cross = report["cross_check"] = {}
    if "serial_prefix_ctrl" in tensors:
        cross["serial_prefix_matches_reference"] = bool(
            torch.equal(tensors["serial_prefix_ctrl"], ref_prefix)
        )
    for name in ("reduce_sum_ub_probe", "vreduce_sum_simd_probe"):
        if name in tensors:
            cross[name + "_matches_reference"] = bool(torch.equal(tensors[name], ref_rowsum))
    if "cumsum_ub_probe" in tensors and "serial_prefix_ctrl" in tensors:
        cum = tensors["cumsum_ub_probe"]
        ser = tensors["serial_prefix_ctrl"]
        cross["cumsum_vs_serial_equal"] = bool(torch.equal(cum, ser))
        if cross["cumsum_vs_serial_equal"]:
            cross["cumsum_semantics"] = "inclusive (matches serial ctrl)"
        else:
            shifted = torch.cat((torch.zeros(1, dtype=torch.int32), ser[:-1]))
            cross["cumsum_semantics"] = (
                "exclusive" if torch.equal(cum, shifted) else "unmatched"
            )

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
        or private / "runs" / datetime.datetime.now().strftime("scan-reduce-probe-r1-%Y%m%d-%H%M%S")
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
        "purpose": "Determine TileLang cumsum/reduce_sum lowering (vector vs scalar serial).",
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