"""Offline regression: verify immutable identities before publishing a runner."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess


def validate(tool, repo):
    runner = tool / "run.py"
    namespace = runpy.run_path(str(runner))
    identity = json.loads((tool / "identity.json").read_text())
    source = namespace["SOURCE"]
    baseline_commit = identity["baseline_commit"]

    def blob(commit):
        return subprocess.check_output(["git", "-C", str(repo), "show", commit + ":" + source])

    assert hashlib.sha256(blob(baseline_commit)).hexdigest() == namespace["BASE"], "Baseline digest corrupted"
    assert hashlib.sha256(blob(identity["candidate_commit"])).hexdigest() == identity["candidate_sha256"]
    text = runner.read_text(encoding="utf-8")
    # Source text is committed with LF; Windows checkout newlines are not evidence bytes.
    assert hashlib.sha256(text.encode()).hexdigest() == identity["run_sha256"]
    constants = re.findall(r"[0-9a-f]{40,64}", text)
    assert set(constants) == {namespace["BASE"], baseline_commit}, constants
    calls = [n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Call)]
    assert any(isinstance(n.func, ast.Attribute) and n.func.attr == "topk_select_ascend"
               for n in calls)
    return namespace


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    validate(Path(__file__).resolve().parent, args.repo)
    print("Frozen baseline, candidate, runner and embedded identities verified; no NPU imports")
