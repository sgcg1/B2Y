#!/usr/bin/env bash
# Run on the host; inspect configuration only. Do not source guard scripts.
set -euo pipefail
container="${1:-yjl}"
[[ "$container" =~ ^[a-zA-Z0-9_.-]+$ ]] || { echo "Invalid container name"; exit 2; }
command -v docker >/dev/null
running=$(docker inspect --format '{{.State.Running}}' "$container")
[[ "$running" == true ]] || { echo "Container is not running; no changes made."; exit 1; }
base="/home/y00937463/B2Y/AAA_Results/topk-step2-host-inspect-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
docker exec "$container" test -d /home/y00937463/B2Y/AAA_Results
inspect() {
  echo 'HOST_READ_ONLY_INSPECTION_V1'
  date -u
  printf 'CONTAINER: %s\n' "$container"
  printf 'HOST_PID_NAMESPACE: '; readlink /proc/1/ns/pid || true
  docker inspect --format 'Running={{.State.Running}} HostPID={{.State.Pid}} PidMode={{.HostConfig.PidMode}} Privileged={{.HostConfig.Privileged}}' "$container"
  echo 'CONTAINER_MOUNTS (sources and destinations only; no environment/credentials)'
  docker inspect --format '{{range .Mounts}}{{println .Type .Source "->" .Destination "RW=" .RW}}{{end}}' "$container"
  echo 'HOST_GUARD_CANDIDATES'
  command -v npu-guard || true
  for path in /usr/local/libexec/ascend-npu/npu_guard.py /usr/local/bin/npu-guard /usr/bin/npu-guard; do
    if test -f "$path"; then ls -l "$path"; sha256sum "$path"; fi
  done
  echo 'HOST_LOCK (metadata only; never acquire/delete/change it)'
  for path in /run/lock/ascend-npu /run/lock/ascend-npu/device-0.lock; do
    if test -e "$path"; then stat -Lc '%n device=%d inode=%i mode=%a owner=%u:%g' "$path"; else printf 'MISSING %s\n' "$path"; fi
  done
  echo 'CONTAINER_VIEW'
  docker exec "$container" sh -c '
    printf "PID_NAMESPACE: "; readlink /proc/1/ns/pid || true
    for path in /run/lock/ascend-npu /run/lock/ascend-npu/device-0.lock /usr/local/libexec/ascend-npu/npu_guard.py; do
      if test -e "$path"; then stat -Lc "%n device=%d inode=%i mode=%a owner=%u:%g" "$path"; else printf "MISSING %s\n" "$path"; fi
    done
  '
  echo 'END_READ_ONLY_INSPECTION'
}
inspect 2>&1 | docker exec -i "$container" sh -c 'umask 077; set -C; cat > "$1"' sh "$base"
printf 'UPLOAD_LOG: %s\n' "$base"
docker exec "$container" cat "$base"
