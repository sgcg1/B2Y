#!/usr/bin/env bash
set -euo pipefail
base=/home/y00937463/B2Y
exec 9>/home/y00937463/.topk-950pr-device-compare.lock
flock -n 9 || { echo "Another development test is running."; exit 1; }
log="$base/AAA_Results/topk-step5-console-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.14/bin/python3 "$base/diagnostics/topk-42-step5-r1/run.py" 2>&1 | tee "$log"
