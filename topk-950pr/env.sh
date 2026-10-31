# Source this file inside the existing yjl container, after choosing paths.
export TOPK_ROOT="${TOPK_ROOT:-/home/y00937463}"
export TOPK_REPO="${TOPK_REPO:-$TOPK_ROOT/TileOPs}"
export TOPK_TOOLS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export TOPK_DEVICE="${TOPK_DEVICE:-0}"
[[ "$TOPK_DEVICE" =~ ^[0-9]+$ ]] || { echo 'Select exactly one allocated physical device ID' >&2; return 1; }
export TOPK_PYTHON="${TOPK_PYTHON:-python3}"
export TOPK_SOC="${TOPK_SOC:-Ascend950PR_9579}"
if [ -n "${CANN_ENV_SCRIPT:-}" ]; then
    test -f "$CANN_ENV_SCRIPT" || { echo 'CANN_ENV_SCRIPT does not exist' >&2; return 1; }
    source "$CANN_ENV_SCRIPT" || return 1
elif [ -z "${ASCEND_HOME_PATH:-}" ] || [ ! -d "$ASCEND_HOME_PATH" ]; then
    echo 'Load the actual CANN environment, or set CANN_ENV_SCRIPT, then source env.sh again' >&2
    return 1
fi
export ASCEND_RT_VISIBLE_DEVICES="$TOPK_DEVICE"
export EVIDENCE="${EVIDENCE:-$TOPK_ROOT/runs/$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$EVIDENCE/cache/cann" "$EVIDENCE/cache/work" "$EVIDENCE/logs" "$TOPK_ROOT/tmp" || return 1
export TMPDIR="$TOPK_ROOT/tmp"
export XDG_CACHE_HOME="$EVIDENCE/cache"
export TILELANG_CACHE_DIR="$EVIDENCE/cache/tilelang"
export ASCEND_CACHE_PATH="$EVIDENCE/cache/cann"
export ASCEND_WORK_PATH="$EVIDENCE/cache/work"
export ASCEND_PROCESS_LOG_PATH="$EVIDENCE/logs"
export TORCH_EXTENSIONS_DIR="$EVIDENCE/cache/torch"
export TORCHINDUCTOR_CACHE_DIR="$EVIDENCE/cache/inductor"
export PYTHONDONTWRITEBYTECODE=1
export TASK_QUEUE_ENABLE=0
export PYTHONPATH="$TOPK_REPO:$TOPK_REPO/src:$TOPK_ROOT/python-deps${PYTHONPATH:+:$PYTHONPATH}"
export TOPK_NPU_SMI="${TOPK_NPU_SMI:-$(command -v npu-smi || true)}"
if [ -z "$TOPK_NPU_SMI" ]; then export TOPK_NPU_SMI=/usr/local/Ascend/driver/tools/npu-smi; fi
ulimit -c 0
printf 'REPO=%s\nTOOLS=%s\nEVIDENCE=%s\nPHYSICAL_DEVICE=%s\n' "$TOPK_REPO" "$TOPK_TOOLS" "$EVIDENCE" "$TOPK_DEVICE"
