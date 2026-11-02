"""Compile-only reproduction of mixed-dtype atomic alias warnings."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback


def execute(report, repo, root):
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    import tilelang
    import torch_npu
    from itertools import product
    here = Path(__file__).resolve().parent
    identity = json.loads((here / "identity.json").read_text())
    for name, expected in identity.items():
        assert hashlib.sha256((here / name).read_bytes()).hexdigest() == expected
    report["identity"] = identity
    report["runtime"] = {"tilelang": tilelang.__version__, "path": tilelang.__file__}
    report["scope"] = "Compile only, no kernel execution, no performance samples"
    spec = importlib.util.spec_from_file_location("sync_repro", here / "repro.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    report["generated"] = {}
    report["failures"] = {}
    # Save the installed compiler analysis source if present; do not modify it.
    source = Path("/home/y00937463/tilelang/src/ascend/transform/thread_storage_sync.cc")
    if source.exists():
        raw = source.read_bytes()
        (root / "installed-thread-storage-sync.txt").write_bytes(raw)
        report["installed_sync_source_sha256"] = hashlib.sha256(raw).hexdigest()
        report["installed_sync_source"] = raw.decode()

    for n, byte in product([4096, 16384], [True, False]):
        name = f"n{n}-" + ("uint8" if byte else "uint32")
        report["stage"] = "compile:" + name
        print("SYNC_COMPILE_BEGIN", name, flush=True)
        try:
            program = module.repro(n, byte)
            code = program.get_kernel_source()
            (root / (name + ".cpp")).write_text(code)
            report["generated"][name] = hashlib.sha256(code.encode()).hexdigest()
        except Exception:
            report["failures"][name] = traceback.format_exc()
            print("SYNC_COMPILE_FAILED", name, report["failures"][name], flush=True)
        print("SYNC_COMPILE_END", name, flush=True)
    report.update(status="completed" if not report["failures"] else "completed_with_failures",
                  stage="review_required", accepted=False)


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
    report = {"version": "20261102-a1-sync-repro-r2", "status": "incomplete",
              "physical_device": args.device, "accepted": False,
              "timing_scope": "Compile-only, no NPU kernel execution"}
    try:
        execute(report, args.repo.resolve(), root)
    except Exception:
        report.update(status="failed", traceback=traceback.format_exc())
        raise
    finally:
        sources = {p.name: p.read_text() for p in root.glob("*.cpp")}
        (root / "sync-return.txt").write_text(json.dumps({"report": report, "sources": sources}, indent=2) + "\n")
        print("SYNC_OUTPUT", root, flush=True)


if __name__ == "__main__":
    main()
