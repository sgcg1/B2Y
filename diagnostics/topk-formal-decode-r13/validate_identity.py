"""Offline source and baseline-contract checks; never imports torch or ACL."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    identity = json.loads((here / "identity.json").read_text())

    def blob(commit, path):
        return subprocess.check_output(["git", "-C", str(args.repo), "show", commit + ":" + path])

    for path, expected in identity["sources"].items():
        assert hashlib.sha256(blob(identity["candidate_commit"], path)).hexdigest() == expected
    assert hashlib.sha256(blob(identity["baseline_commit"], "src/tileops/_kernels/attention/topk_select_ascend.py")).hexdigest() == identity["baseline_sha256"]
    for path, expected in identity["tool_files"].items():
        assert hashlib.sha256((here / path).read_text(encoding="utf-8").encode()).hexdigest() == expected, path
    assert hashlib.sha256(blob(identity["r3_commit"], "src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py")).hexdigest() == identity["r3_pipeline_sha256"]
    assert hashlib.sha256(blob(identity["r3_commit"], "src/tileops/_kernels/attention/topk_select_decode_probe_ascend.py")).hexdigest() == identity["previous_hist_sha256"]
    runner = here / "run.py"
    assert hashlib.sha256(runner.read_text(encoding="utf-8").encode()).hexdigest() == identity["run_sha256"]
    assert callable(runpy.run_path(str(runner))["execute"])
    assert (here / "run.sh").read_bytes().isascii()
    cpp = (here / "cann/build.cpp").read_text(encoding="utf-8")
    for required in ["must_keep_origin_dtype", "set_attr_largest(true)", "set_attr_sorted(false)",
                     "set_attr_indices_dtype(ge::DT_INT32)", "set_attr_sort_policy(0)"]:
        assert required in cpp, required
    print("Frozen kernel sources, official GE attributes, tool manifest and ASCII launcher verified")
