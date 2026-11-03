"""Verify and fast-forward the single candidate commit from B2Y; no resets."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/y00937463/TileOPs")
identity = json.loads((here / "identity.json").read_text())
bundle = here / "candidate.bundle"
assert hashlib.sha256(bundle.read_bytes()).hexdigest() == identity["candidate_bundle_sha256"], "Bundle SHA mismatch"
def git(*args):
    return subprocess.check_output(["git", "-C", str(repo), *args])
assert git("branch", "--show-current").decode().strip() == "main", "Expected main; preserve existing branch"
assert not git("status", "--porcelain", "--untracked-files=no").strip(), "Tracked changes present; preserve them"
subprocess.check_call(["git", "-C", str(repo), "bundle", "verify", str(bundle)])
ref = "refs/remotes/b2y-overflow-keys/main"
subprocess.check_call(["git", "-C", str(repo), "fetch", str(bundle), "refs/heads/main:" + ref])
assert git("rev-parse", ref).decode().strip() == identity["candidate_commit_full"]
changed = set(git("diff", "--name-only", identity["r3_commit"], ref).decode().splitlines())
assert changed == {"src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py", "tests/kernels/test_topk_select_decode_pipeline_ascend.py"}, changed
subprocess.check_call(["git", "-C", str(repo), "merge", "--ff-only", ref])
print("CANDIDATE_FAST_FORWARD_COMPLETE")
