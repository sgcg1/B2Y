"""Keep one source/tool/device identity for all stages of a measurement run."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def snapshot():
    repo = Path(os.environ["TOPK_REPO"])
    tools = Path(os.environ["TOPK_TOOLS"])
    status = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True)
    assert not status.strip(), "Commit or separately preserve source changes before a formal run"
    hashes = {}
    for line in (tools / "MANIFEST.sha256").read_text().splitlines():
        expected, name = line.split("  ", 1)
        path = (tools / name).resolve()
        assert path.is_relative_to(tools.resolve()), name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, f"Tool changed or transfer incomplete: {name}"
        hashes[name] = actual
    sources = [
        "src/tileops/_kernels/attention/topk_select_ascend.py",
        "src/tileops/ascend/topk_select.py",
        "tests/ops/test_topk_select_ascend.py",
    ]
    return {
        "python_executable": str(Path(sys.executable).resolve()),
        "tileops_commit": subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip(),
        "source_sha256": {
            name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in sources
        },
        "tool_sha256": hashes,
        "physical_device": os.environ["ASCEND_RT_VISIBLE_DEVICES"],
        "soc": os.environ["TOPK_SOC"],
        "cann_cxx11_abi": os.environ.get("TOPK_CXX11_ABI", "0"),
        "runtime_environment": {
            name: os.environ.get(name)
            for name in [
                "ASCEND_HOME_PATH",
                "ASCEND_OPP_PATH",
                "LD_LIBRARY_PATH",
                "BISHENG_HOME",
                "ASCEND_NPU_ARCH",
            ]
        },
        "cache_directories": {
            name: os.environ[name]
            for name in [
                "TILELANG_CACHE_DIR",
                "ASCEND_CACHE_PATH",
                "ASCEND_WORK_PATH",
                "XDG_CACHE_HOME",
            ]
        },
    }


def check():
    path = Path(os.environ["EVIDENCE"]) / "run-context.json"
    saved = json.loads(path.read_text())
    assert saved == snapshot(), "Source, tools, device or cache changed: start a new EVIDENCE run"
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["create", "check"])
    args = parser.parse_args()
    if args.mode == "create":
        path = Path(os.environ["EVIDENCE"]) / "run-context.json"
        value = snapshot()
        with path.open("x") as handle:
            handle.write(json.dumps(value, indent=2) + "\n")
        print("RUN_CONTEXT_CREATED", flush=True)
    else:
        check()
        print("RUN_CONTEXT_OK", flush=True)
