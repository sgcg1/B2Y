#!/usr/bin/env bash
set -euo pipefail
: "${TOPK_REPO:?source env.sh first}"
: "${TOPK_TOOLS:?source env.sh first}"
: "${EVIDENCE:?source env.sh first}"
cd "$TOPK_REPO"
case "${1:-}" in
  preflight)
    smi="$(command -v npu-smi || true)"
    if [ -z "$smi" ]; then smi=/usr/local/Ascend/driver/tools/npu-smi; fi
    timeout --kill-after=5s 30s "$smi" info | tee "$EVIDENCE/device-before.txt"
    timeout --kill-after=5s 30s "$smi" info -t health -i "$TOPK_DEVICE" | tee "$EVIDENCE/health-before.txt"
    timeout --kill-after=10s 300s "$TOPK_PYTHON" -u "$TOPK_TOOLS/preflight.py" 2>&1 | tee "$EVIDENCE/preflight.log"
    ;;
  test)
    mkdir -p "$EVIDENCE/candidate"
    test ! -e "$EVIDENCE/candidate/tests.log" || { echo 'Existing tests.log: use a new run'; exit 1; }
    "$TOPK_PYTHON" -u -m pytest tests/ops/test_topk_select_ascend.py --tileops-device=npu:0 \
      -x -q -s --timeout=180 --timeout-method=thread 2>&1 | tee "$EVIDENCE/candidate/tests.log"
    ;;
  control)
    repetition="${2:-1}"
    timeout --kill-after=10s 600s "$TOPK_PYTHON" -u "$TOPK_TOOLS/control_portable.py" \
      --repo "$TOPK_REPO" --output "$EVIDENCE/control-decode-$repetition" \
      2>&1 | tee "$EVIDENCE/control-decode-$repetition.log"
    ;;
  measure)
    mkdir -p "$EVIDENCE/candidate"
    "$TOPK_PYTHON" -u "$TOPK_TOOLS/measure.py" --version candidate --case all \
      --samples 50 --profile-samples 50 2>&1 | tee "$EVIDENCE/candidate/benchmark.log"
    ;;
  cann-build)
    test ! -e "$EVIDENCE/cann" || { echo 'Existing cann directory: use a new run'; exit 1; }
    mkdir -p "$EVIDENCE/cann"
    cp "$TOPK_TOOLS/cann/"* "$EVIDENCE/cann/"
    cd "$EVIDENCE/cann"
    : "${ASCEND_HOME_PATH:?CANN is not activated}"
    g++ -std=c++17 -D_GLIBCXX_USE_CXX11_ABI=0 build.cpp \
      -I"$ASCEND_HOME_PATH/include" -I"$ASCEND_HOME_PATH/include/external" \
      -I"$ASCEND_HOME_PATH/include/external/graph" -I. -L"$ASCEND_HOME_PATH/lib64" \
      -lge_compiler -lgraph -lgraph_base -lge_runner -o build 2>&1 | tee compile.log
    ./build 1 16384 2048 decode 2>&1 | tee build-decode.log
    ./build 32768 65536 1024 prefill-k1024 2>&1 | tee build-prefill-k1024.log
    ./build 32768 65536 2048 prefill-k2048 2>&1 | tee build-prefill-k2048.log
    ;;
  cann-measure)
    cd "$EVIDENCE/cann"
    test ! -e decode-timing.json || { echo 'Baseline exists: use a new run'; exit 1; }
    export EVIDENCE="$EVIDENCE/cann"
    "$TOPK_PYTHON" -u benchmark.py 1 16384 2048 decode 2>&1 | tee decode.log
    "$TOPK_PYTHON" -u benchmark.py 32768 65536 1024 prefill-k1024 2>&1 | tee prefill-k1024.log
    "$TOPK_PYTHON" -u benchmark.py 32768 65536 2048 prefill-k2048 2>&1 | tee prefill-k2048.log
    "$TOPK_PYTHON" profile-summary.py | tee profile-summary.txt
    ;;
  summary)
    "$TOPK_PYTHON" "$TOPK_TOOLS/summarize.py" --evidence "$EVIDENCE"
    ;;
  *) echo 'Usage: bash run.sh {preflight|test|control [1/2]|cann-build|cann-measure|measure|summary}'; exit 2 ;;
esac
