#!/usr/bin/env bash
set -euo pipefail
tools=/home/y00937463/B2Y/diagnostics/topk-merge-consumption-probe-r1
python=/usr/local/python3.12.14/bin/python3
test -n "${ASCEND_HOME_PATH:-}" || { echo "ERROR: load the existing CANN environment first."; exit 1; }
test -x "$python"
exec 9>/home/y00937463/.topk-950pr-device-compare.lock
flock -n 9 || { echo "ERROR: another benchmark copy holds the private lock."; exit 1; }
root="/home/y00937463/topk-merge-consumption-probe-r1-$(date +%Y%m%d-%H%M%S)-$$"
mkdir "$root"
status=0
PYTHONDONTWRITEBYTECODE=1 "$python" "$tools/run.py" --output "$root/data" > "$root/run.log" 2>&1 || status=$?
target="/home/y00937463/B2Y/AAA_Results/$(basename "$root")"
mkdir -p /home/y00937463/B2Y/AAA_Results
cp --no-clobber "$root/run.log" "$target.log"
if test -f "$root/data/probe-return.json"; then
  cp --no-clobber "$root/data/probe-return.json" "$target.json"
  echo "UPLOAD_RESULT: $target.json"
fi
echo "UPLOAD_LOG: $target.log"
echo "RAW_OUTPUT: $root"
echo "Upload this run's JSON and log to B2Y AAA_Results, including failures."
exit "$status"
