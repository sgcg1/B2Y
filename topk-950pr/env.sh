# Source this file inside the existing yjl container, after choosing paths.
export TOPK_ROOT="${TOPK_ROOT:-/data/yjl/topk}"
export TOPK_REPO="${TOPK_REPO:-$TOPK_ROOT/TileOPs}"
export TOPK_TOOLS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export TOPK_DEVICE="${TOPK_DEVICE:-0}"
export TOPK_PYTHON="${TOPK_PYTHON:-python3}"
export CANN_ENV_SCRIPT="${CANN_ENV_SCRIPT:-/data/setenv.bash}"
if [ ! -f "$CANN_ENV_SCRIPT" ]; then
    echo "Set CANN_ENV_SCRIPT to the container's actual CANN activation script" >&2
    return 1
fi
source "$CANN_ENV_SCRIPT" || return 1
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
export PYTHONPATH="$TOPK_REPO:$TOPK_REPO/src${PYTHONPATH:+:$PYTHONPATH}"
ulimit -c 0
printf 'REPO=%s\nTOOLS=%s\nEVIDENCE=%s\nPHYSICAL_DEVICE=%s\n' "$TOPK_REPO" "$TOPK_TOOLS" "$EVIDENCE" "$TOPK_DEVICE"
