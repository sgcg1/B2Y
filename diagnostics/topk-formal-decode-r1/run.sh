#!/usr/bin/env bash
set -euo pipefail
test -n "${ASCEND_HOME_PATH:-}" || { echo "ERROR: load the existing CANN environment first."; exit 1; }
root="/home/y00937463/topk-formal-decode-r1-$(date +%Y%m%d-%H%M%S)-$$"
mkdir "$root"
tools=/home/y00937463/B2Y/diagnostics/topk-formal-decode-r1
for repeat in 1 2; do
  status=0
  /usr/local/python3.12.14/bin/python3 "$tools/run.py" \
    --repo /home/y00937463/TileOPs --device 0 --output "$root/repeat-$repeat" \
    > "$root/repeat-$repeat.log" 2>&1 || status=$?
  target="/home/y00937463/B2Y/AAA_Results/$(basename "$root")-repeat-$repeat"
  cp --no-clobber "$root/repeat-$repeat.log" "$target.log"
  if test -f "$root/repeat-$repeat/formal-return.txt"; then
    cp --no-clobber "$root/repeat-$repeat/formal-return.txt" "$target.txt"
    echo "UPLOAD_RESULT: $target.txt"
  fi
  echo "UPLOAD_LOG: $target.log"
  if test "$status" -ne 0; then
    echo "FAILED: stopping repeats; upload existing files. RAW_OUTPUT: $root"
    exit "$status"
  fi
done
echo "COLLECTION_COMPLETE: review required, not accepted. RAW_OUTPUT: $root"
