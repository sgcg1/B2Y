#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOPK_HOME="${TOPK_HOME:-/home/y00937463}"
RUN_ROOT="$TOPK_HOME/runs"
OUT="$RUN_ROOT/scan-reduce-probe-r1-$(date +%Y%m%d-%H%M%S)-$$"

timeout --kill-after=10s 900s "${TOPK_PYTHON:-python3}" \
  "$HERE/probe.py" \
  --device "${TOPK_DEVICE:-0}" \
  --output "$OUT"

echo "=== probe-summary.txt ==="
cat "$OUT/probe-summary.txt"
echo "=== PROBE_OUTPUT ==="
echo "$OUT"