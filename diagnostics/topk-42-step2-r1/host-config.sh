#!/usr/bin/env bash
set -euo pipefail
container="${1:-yjl}"
[[ "$container" =~ ^[a-zA-Z0-9_.-]+$ ]]
path="/home/y00937463/B2Y/AAA_Results/topk-host-config-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
docker inspect --format 'Container={{.Name}}
ImageID={{.Image}}
ImageName={{.Config.Image}}
WorkingDir={{.Config.WorkingDir}}
User={{.Config.User}}
Runtime={{.HostConfig.Runtime}}
Devices={{json .HostConfig.Devices}}
DeviceRequests={{json .HostConfig.DeviceRequests}}
DeviceCgroupRules={{json .HostConfig.DeviceCgroupRules}}
NetworkMode={{.HostConfig.NetworkMode}}
PortBindings={{json .HostConfig.PortBindings}}
PidMode={{.HostConfig.PidMode}}
IpcMode={{.HostConfig.IpcMode}}
ShmSize={{.HostConfig.ShmSize}}
CapAdd={{json .HostConfig.CapAdd}}
CapDrop={{json .HostConfig.CapDrop}}
SecurityOpt={{json .HostConfig.SecurityOpt}}
Privileged={{.HostConfig.Privileged}}
RestartPolicy={{json .HostConfig.RestartPolicy}}
Ulimits={{json .HostConfig.Ulimits}}
{{range .Mounts}}{{println "Mount=" .Type .Source "->" .Destination "RW=" .RW}}{{end}}' "$container" |
  docker exec -i "$container" sh -c 'umask 077; set -C; cat > "$1"' sh "$path"
printf 'UPLOAD_LOG: %s\n' "$path"
