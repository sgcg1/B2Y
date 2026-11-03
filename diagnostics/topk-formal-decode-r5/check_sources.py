"""Read-only source identity diagnosis; no NPU imports or credentials."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/y00937463/TileOPs")
here = Path(__file__).resolve().parent
identity = json.loads((here / "identity.json").read_text())
def git(*args):
    return subprocess.check_output(["git", "-C", str(repo), *args])
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
print("HEAD", git("rev-parse", "HEAD").decode().strip())
print("STATUS", git("status", "--short", "--untracked-files=no").decode())
ancestor = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", identity["candidate_commit"], "HEAD"], capture_output=True)
print("CANDIDATE_IS_ANCESTOR", ancestor.returncode == 0)
passed = ancestor.returncode == 0
for path, expected in identity["sources"].items():
    raw = (repo / path).read_bytes()
    head = git("show", "HEAD:" + path)
    match = sha(raw) == expected
    print(json.dumps({"path": path, "expected": expected, "working": sha(raw), "head_blob": sha(head), "working_lf": sha(raw.replace(b"\r\n", b"\n")), "match": match}))
    passed = passed and match
if not passed:
    raise SystemExit("SOURCE_CHECK_FAILED: preserve changes; upload this output; do not bypass hashes")
print("SOURCE_CHECK_PASSED")
