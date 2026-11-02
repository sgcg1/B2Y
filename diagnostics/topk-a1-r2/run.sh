#!/usr/bin/env bash
set -euo pipefail
test -n "${ASCEND_HOME_PATH:-}" || { echo '请先恢复现有CANN环境'; exit 1; }
root="/home/y00937463/topk-a1-r2-$(date +%Y%m%d-%H%M%S)-$$"
mkdir "$root"
tools=/home/y00937463/B2Y/diagnostics/topk-a1-r2
for repeat in 1 2; do
  status=0
  /usr/local/python3.12.14/bin/python3 "$tools/run.py" \
    --repo /home/y00937463/TileOPs --device 0 --output "$root/repeat-$repeat" \
    > "$root/repeat-$repeat.log" 2>&1 || status=$?
  target="/home/y00937463/B2Y/AAA_Results/$(basename "$root")-repeat-$repeat"
  cp --no-clobber "$root/repeat-$repeat.log" "$target.log"
  if test -f "$root/repeat-$repeat/a1-return.txt"; then
    cp --no-clobber "$root/repeat-$repeat/a1-return.txt" "$target.txt"
    echo "回传 $target.txt"
  fi
  echo "日志 $target.log"
  if test "$status" -ne 0; then
    echo "本次失败，停止后续进程；请回传已有文件。原始目录 $root"
    exit "$status"
  fi
done
echo "采集完成，待分析，不代表候选已接受。原始目录 $root"
