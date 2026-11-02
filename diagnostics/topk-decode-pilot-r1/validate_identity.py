"""Validate immutable source/tool identities without importing TileLang or torch."""
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
    raw = subprocess.check_output(["git", "-C", str(args.repo), "show",
                                   identity["candidate_commit"] + ":" + identity["source_path"]])
    assert hashlib.sha256(raw).hexdigest() == identity["source_sha256"]
    runner = here / "run.py"
    assert hashlib.sha256(runner.read_text(encoding="utf-8").encode()).hexdigest() == identity["run_sha256"]
    namespace = runpy.run_path(str(runner))
    assert callable(namespace["execute"])
    print("Committed probe source and runner identities verified; no NPU imports")
