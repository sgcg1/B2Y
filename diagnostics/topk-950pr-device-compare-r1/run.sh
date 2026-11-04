#!/usr/bin/env bash
set -euo pipefail
tools=/home/y00937463/B2Y/diagnostics/topk-950pr-device-compare-r1
python=/usr/local/python3.12.14/bin/python3
test -n "${ASCEND_HOME_PATH:-}" || { echo "ERROR: load the existing CANN environment first."; exit 1; }
test -x "$python"
command -v flock >/dev/null
# This lock only coordinates this user's copies of this benchmark.
exec 9>/home/y00937463/.topk-950pr-device-compare.lock
flock -n 9 || { echo "ERROR: another copy of this benchmark is running."; exit 1; }
root="/home/y00937463/topk-950pr-device-compare-r1-$(date +%Y%m%d-%H%M%S)-$$"
mkdir "$root"
mkdir -p /home/y00937463/B2Y/AAA_Results
for repeat in 1 2 3; do
  status=0
  "$python" "$tools/run.py" --repo /home/y00937463/TileOPs --repeat "$repeat" --output "$root/repeat-$repeat" > "$root/repeat-$repeat.log" 2>&1 || status=$?
  target="/home/y00937463/B2Y/AAA_Results/$(basename "$root")-repeat-$repeat"
  cp --no-clobber "$root/repeat-$repeat.log" "$target.log"
  if test -f "$root/repeat-$repeat/device-return.json"; then
    cp --no-clobber "$root/repeat-$repeat/device-return.json" "$target.json"
    echo "UPLOAD_RESULT: $target.json"
  fi
  echo "UPLOAD_LOG: $target.log"
  if test "$status" -ne 0; then
    echo "FAILED: upload the JSON and log above; do not reset devices or rerun unchanged. RAW_OUTPUT: $root"
    exit "$status"
  fi
done
"$python" "$tools/pack.py" "$root"
echo "COMPLETE: upload the printed parts and manifest together. RAW_OUTPUT: $root"
