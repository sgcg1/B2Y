"""Offline immutable identity check; imports only the stdlib runner definitions."""
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
        assert hashlib.sha256(blob(identity["candidate_commit"], path)).hexdigest() == expected, path
    baseline = blob(identity["baseline_commit"], "src/tileops/_kernels/attention/topk_select_ascend.py")
    assert hashlib.sha256(baseline).hexdigest() == identity["baseline_sha256"]
    assert hashlib.sha256(blob(identity["r1_commit"], "src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py")).hexdigest() == identity["r1_pipeline_sha256"]
    assert hashlib.sha256(blob(identity["r2_commit"], "src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py")).hexdigest() == identity["r2_pipeline_sha256"]
    runner = here / "run.py"
    assert hashlib.sha256(runner.read_text(encoding="utf-8").encode()).hexdigest() == identity["run_sha256"]
    assert callable(runpy.run_path(str(runner))["execute"])
    assert (here / "run.sh").read_bytes().isascii()
    print("Frozen baseline, both kernel sources, runner and ASCII launcher verified")
