#!/usr/bin/env bash
# Explicit apply only: snapshot an idle yjl, create separate guard-enabled verifier.
set -euo pipefail
[[ "${1:-}" == --apply-when-yjl-idle ]] || { echo "Read README first. Usage: bash host-setup.sh --apply-when-yjl-idle"; exit 2; }
old=yjl
new=yjl-topk-guard
base=/home/y00937463/B2Y
source=/home/y00937463/topk-42-step2-r1-20261105-111338-4799/TileOPs
python=/usr/local/python3.12.14/bin/python3
[[ $(docker inspect -f '{{.State.Running}}' "$old") == true ]]
[[ $(docker inspect -f '{{.Image}}' "$old") == sha256:5039210f3b913368a1f4ee5e0d43b41a66109eb37da7ed97e50a5dbe9dd76f4d ]] || { echo 'Source image changed; return config before applying.'; exit 1; }
if docker inspect "$new" >/dev/null 2>&1; then echo "ERROR: $new already exists. Do not recreate or delete it; return its logs."; exit 1; fi
test -f /run/lock/ascend-npu/device-0.lock
test -d /run/lock/ascend-npu
[[ ! -L /run/lock/ascend-npu && ! -L /run/lock/ascend-npu/device-0.lock ]]
[[ $(stat -c %u /run/lock/ascend-npu) == 0 ]]
[[ $(docker exec "$old" git -C "$source" rev-parse HEAD) == 4409536e1f0dba8dca7141d6aee6fc6677afa9ce ]]
docker exec "$old" test -f "$source/scripts/npu_guard.py"
# Never replace/truncate the existing cooperative lock. Serialize only this setup.
exec 9<>/run/lock/ascend-npu/device-0.lock
flock -n 9 || { echo "ERROR: shared reservation held; retry setup later."; exit 1; }
# Container filesystem changes are snapshotted; /home stays on its existing host bind.
image="topk-yjl-snapshot:$(date -u +%Y%m%d%H%M%S)-$$"
log="$base/AAA_Results/topk-host-setup-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
{
  echo "SNAPSHOT_IMAGE: $image"
  echo "Creating filesystem snapshot; Docker briefly pauses yjl during commit."
  docker commit "$old" "$image"
  docker create --name "$new" --runtime=ascend --pid=host --ipc=shareable --shm-size=67108864 \
    --network=bridge --cap-add=SYS_ADMIN --security-opt=seccomp=unconfined \
    --device=/dev/davinci0 --device=/dev/davinci_manager --device=/dev/hisi_hdc \
    --env ASCEND_VISIBLE_DEVICES=0 --env ASCEND_RT_VISIBLE_DEVICES=0 \
    --mount type=bind,src=/home,dst=/home \
    --mount type=bind,src=/usr/local/dcmi,dst=/usr/local/dcmi \
    --mount type=bind,src=/etc/ascend_install.info,dst=/etc/ascend_install.info \
    --mount type=bind,src=/usr/local/Ascend/driver/lib64,dst=/usr/local/Ascend/driver/lib64 \
    --mount type=bind,src=/usr/local/Ascend/driver/version.info,dst=/usr/local/Ascend/driver/version.info \
    --mount type=bind,src=/usr/local/bin/npu-smi,dst=/usr/local/bin/npu-smi \
    --mount type=bind,src=/run/lock/ascend-npu,dst=/run/lock/ascend-npu \
    --workdir=/workspace --user=0 --no-healthcheck --entrypoint=/bin/sleep "$image" infinity
  docker start "$new"
  echo 'Shared lock identity (host and verifier must match):'
  stat -Lc 'device=%d inode=%i' /run/lock/ascend-npu/device-0.lock
  docker exec "$new" stat -Lc 'device=%d inode=%i' /run/lock/ascend-npu/device-0.lock
  echo 'PID namespaces (host and verifier must match):'
  readlink /proc/1/ns/pid
  docker exec "$new" readlink /proc/1/ns/pid
  [[ $(stat -Lc '%d:%i' /run/lock/ascend-npu/device-0.lock) == $(docker exec "$new" stat -Lc '%d:%i' /run/lock/ascend-npu/device-0.lock) ]]
  [[ $(readlink /proc/1/ns/pid) == $(docker exec "$new" readlink /proc/1/ns/pid) ]]
  echo "SETUP_DONE: $new"
} 2>&1 | tee "$log"
flock -u 9
printf 'UPLOAD_SETUP_LOG: %s\n' "$log"
echo 'Next: run verifier-run.sh on host. Original yjl was not deleted/recreated.'
