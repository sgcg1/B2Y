#!/usr/bin/env bash
set -euo pipefail
base=/home/y00937463/B2Y
log="$base/AAA_Results/topk-verifier-run-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
# Package registration changes only the new verification container, not yjl.
docker exec yjl-topk-guard /bin/bash -lc '
set -eo pipefail
source /usr/local/Ascend/cann-current/set_env.sh
export PYTHONDONTWRITEBYTECODE=1
python=/usr/local/python3.12.14/bin/python3
repo=/home/y00937463/topk-42-step2-r1-20261105-111338-4799/TileOPs
test "$(git -C "$repo" rev-parse HEAD)" = 4409536e1f0dba8dca7141d6aee6fc6677afa9ce
# No dependency downloads/upgrades. Missing build prerequisites are reported.
TORCH_DEVICE_BACKEND_AUTOLOAD=0 "$python" -m pip install --no-index --no-deps --no-build-isolation -e "$repo"
export TILEOPS_NPU_GUARD="$repo/scripts/npu_guard.py"
exec "$python" /home/y00937463/B2Y/diagnostics/topk-42-step2-r1/run.py
' 2>&1 | tee "$log"
printf 'UPLOAD_VERIFIER_LOG: %s\n' "$log"
