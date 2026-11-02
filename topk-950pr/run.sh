#!/usr/bin/env bash
set -euo pipefail
: "${TOPK_REPO:?source env.sh first}"
: "${TOPK_TOOLS:?source env.sh first}"
: "${EVIDENCE:?source env.sh first}"
cd "$TOPK_REPO"
fresh_log() { test ! -e "$1" || { echo "Existing output: $1; use a new EVIDENCE run" >&2; exit 1; }; }
bench_limit() {
    case "$1" in decode) echo 300 ;; small) echo 600 ;; *) echo 3600 ;; esac
}
case_spec() {
    case "$1" in
        decode) echo '1 16384 2048' ;;
        prefill-k1024) echo '32768 65536 1024' ;;
        prefill-k2048) echo '32768 65536 2048' ;;
        *) echo 'Expected decode, prefill-k1024 or prefill-k2048' >&2; return 2 ;;
    esac
}
build_case() (
    local name="$1" rows length k directory
    read -r rows length k <<<"$(case_spec "$name")"
    directory="$EVIDENCE/cann/$name"
    test ! -e "$directory" || { echo "Existing model directory: $directory" >&2; exit 1; }
    mkdir -p "$directory"
    cp "$TOPK_TOOLS/cann/"* "$directory/"
    cd "$directory"
    g++ -std=c++17 -D_GLIBCXX_USE_CXX11_ABI="${TOPK_CXX11_ABI:-0}" build.cpp \
        -I"$ASCEND_HOME_PATH/include" -I"$ASCEND_HOME_PATH/include/external" \
        -I"$ASCEND_HOME_PATH/include/external/graph" -I. -L"$ASCEND_HOME_PATH/lib64" \
        -lge_compiler -lgraph -lgraph_base -lge_runner -o build 2>&1 | tee compile.log
    ./build "$rows" "$length" "$k" "$name" 2>&1 | tee model-build.log
    sha256sum "$name.om" build.cpp top_k_v2_proto.h > build-files.sha256
)
measure_cann_case() (
    local name="$1" rows length k
    read -r rows length k <<<"$(case_spec "$name")"
    export EVIDENCE="$EVIDENCE/cann/$name"
    cd "$EVIDENCE"
    test -f "$name.om"
    fresh_log "$name.log"
    timeout --kill-after=10s "${TOPK_BENCH_TIMEOUT:-$(bench_limit "$name")}s" \
        "$TOPK_PYTHON" -u benchmark.py "$rows" "$length" "$k" "$name" 2>&1 | tee "$name.log"
    "$TOPK_PYTHON" profile-summary.py --case "$name" | tee profile-summary.txt
)
stage="${1:-}"
if [ "$stage" = preflight ]; then
    "$TOPK_PYTHON" "$TOPK_TOOLS/provenance.py" create
else
    "$TOPK_PYTHON" "$TOPK_TOOLS/provenance.py" check
fi
case "$stage" in
    preflight)
        fresh_log "$EVIDENCE/preflight.log"
        timeout --kill-after=5s 30s "$TOPK_NPU_SMI" info | tee "$EVIDENCE/device-before.txt"
        timeout --kill-after=5s 30s "$TOPK_NPU_SMI" info -t health -i "$TOPK_DEVICE" | tee "$EVIDENCE/health-before.txt"
        grep -Eq 'Health Status[[:space:]]*:[[:space:]]*OK' "$EVIDENCE/health-before.txt" || { echo 'Device health is not OK; stop here'; exit 1; }
        timeout --kill-after=10s 300s "$TOPK_PYTHON" -u "$TOPK_TOOLS/preflight.py" 2>&1 | tee "$EVIDENCE/preflight.log"
        ;;
    test)
        mkdir -p "$EVIDENCE/candidate"
        fresh_log "$EVIDENCE/candidate/tests.log"
        timeout --kill-after=10s 1200s "$TOPK_PYTHON" -u -m pytest \
            tests/ops/test_topk_select_ascend.py --tileops-device=npu:0 -x -v -s \
            --timeout=180 --timeout-method=thread --junitxml="$EVIDENCE/candidate/tests.xml" \
            2>&1 | tee "$EVIDENCE/candidate/tests.log"
        ;;
    control)
        repetition="${2:-1}"
        [[ "$repetition" =~ ^[0-9]+$ ]]
        fresh_log "$EVIDENCE/control-decode-$repetition.log"
        timeout --kill-after=10s 600s "$TOPK_PYTHON" -u "$TOPK_TOOLS/control_portable.py" \
            --repo "$TOPK_REPO" --output "$EVIDENCE/control-decode-$repetition" \
            2>&1 | tee "$EVIDENCE/control-decode-$repetition.log"
        ;;
    control-diagnose)
        fresh_log "$EVIDENCE/control-diagnostic.log"
        timeout --kill-after=10s 600s "$TOPK_PYTHON" -u "$TOPK_TOOLS/control_portable.py" \
            --repo "$TOPK_REPO" --output "$EVIDENCE/control-diagnostic" --diagnostic \
            2>&1 | tee "$EVIDENCE/control-diagnostic.log"
        ;;
    clock|frequency|transfer|binary)
        fresh_log "$EVIDENCE/diagnostic-$stage.log"
        case "$stage" in
            clock) script=clock_check.py ;;
            frequency) script=frequency.py ;;
            transfer) script=transfer_check.py ;;
            binary) script=binary_check.py ;;
        esac
        timeout --kill-after=10s 300s "$TOPK_PYTHON" -u "$TOPK_TOOLS/$script" \
            2>&1 | tee "$EVIDENCE/diagnostic-$stage.log"
        ;;
    cann-build|cann-measure)
        selection="${2:-decode}"
        if [ "$selection" = all ]; then names=(decode prefill-k1024 prefill-k2048); else names=("$selection"); fi
        for name in "${names[@]}"; do
            case_spec "$name" >/dev/null
            if [ "$stage" = cann-build ]; then build_case "$name"; else measure_cann_case "$name"; fi
        done
        ;;
    measure)
        name="${2:-decode}"
        case "$name" in all|decode|small|prefill-k1024|prefill-k2048) ;; *) exit 2 ;; esac
        mkdir -p "$EVIDENCE/candidate"
        fresh_log "$EVIDENCE/candidate/$name-measure.log"
        timeout --kill-after=10s "${TOPK_BENCH_TIMEOUT:-$(bench_limit "$name")}s" \
            "$TOPK_PYTHON" -u "$TOPK_TOOLS/measure.py" --version candidate --case "$name" \
            --samples 50 --profile-samples 50 2>&1 | tee "$EVIDENCE/candidate/$name-measure.log"
        ;;
    summary)
        "$TOPK_PYTHON" "$TOPK_TOOLS/summarize.py" --evidence "$EVIDENCE" --scope "${2:-all}"
        ;;
    *) echo 'Usage: bash run.sh {preflight|test|control [1/2]|control-diagnose|clock|frequency|transfer|binary|cann-build [case/all]|cann-measure [case/all]|measure [case/all]|summary [decode/all]}'; exit 2 ;;
esac
