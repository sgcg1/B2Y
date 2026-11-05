#!/usr/bin/env bash
set -euo pipefail
base=/home/y00937463/B2Y
exec 9>/home/y00937463/.topk-950pr-device-compare.lock
flock -n 9 || { echo "Another development test is running."; exit 1; }
for round in 1 2 3; do
  log="$base/AAA_Results/topk-step6-compare-console-$(date -u +%Y%m%dT%H%M%SZ)-$$-r$round.log"
  TOPK_COMPARE_ROUND="$round" PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.14/bin/python3 "$base/diagnostics/topk-42-step6-compare-r1/run.py" 2>&1 | tee "$log"
done
