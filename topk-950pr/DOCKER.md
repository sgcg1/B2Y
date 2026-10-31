# yjl 容器与镜像（所有创建/导入命令在服务器宿主机执行）

已有可用 yjl 时，只执行 `docker exec -it yjl /bin/bash`，不要重复创建或删除容器。

## 镜像拉取

服务器已确认 x86_64。本指南不使用需要实验功能的 `--platform`：

```bash
export TOPK_IMAGE=quay.io/celenewyear/tilelang-ascend:cann9.3.0-weekly.20261021-ubuntu22.04-py3.12
docker pull "$TOPK_IMAGE"
docker image inspect "$TOPK_IMAGE" --format '{{.Os}}/{{.Architecture}}'
```

应显示 linux/amd64。`Unable to find image ... locally` 只是本地没有镜像；`context deadline exceeded` 等后续信息才说明访问仓库失败。

Docker daemon 拉取镜像不一定使用当前 shell 的代理变量。不要为了个人镜像重启或修改共享 Docker daemon。若现场已有 skopeo，可使用获准的 shell 网络/代理配置下载到私人目录，再让 Docker 离线导入：

```bash
export TOPK_HOST_ROOT="$HOME/yjl-topk"
mkdir -p "$TOPK_HOST_ROOT"
skopeo copy \
  "docker://$TOPK_IMAGE" \
  "docker-archive:$TOPK_HOST_ROOT/tilelang-ascend.tar:$TOPK_IMAGE"
docker load -i "$TOPK_HOST_ROOT/tilelang-ascend.tar"
docker image inspect "$TOPK_IMAGE" --format '{{.Os}}/{{.Architecture}}'
```

确保 `$TOPK_IMAGE` 已按上方完整名称设置。archive 的最后一段也使用完整镜像名称，避免导入后标签与 docker run 不匹配。没有 skopeo 时先询问环境负责人提供获准工具或内部镜像源；这里不执行系统级 apt/yum 安装。

archive 格式参考 [Skopeo 官方说明](https://github.com/containers/skopeo/blob/main/docs/skopeo.1.md)。

如果已有 tar 从别的获准机器传入，只需 docker load。若导入的镜像名不一致，先 `docker image ls` 核实，再用 `docker tag 实际镜像ID "$TOPK_IMAGE"` 添加正确标签。不要把多 GB 镜像放进普通 Git 历史，也不需要上传到 B2Y。

## 仅在 yjl 尚不存在时创建

先确认分配的设备号和设备文件。下例仅暴露获准的物理卡 0；保留之前使用的 seccomp/SYS_ADMIN 配置，不新增 privileged：

```bash
export TOPK_IMAGE=quay.io/celenewyear/tilelang-ascend:cann9.3.0-weekly.20261021-ubuntu22.04-py3.12
export TOPK_HOST_ROOT="$HOME/yjl-topk"
mkdir -p "$TOPK_HOST_ROOT"
docker image inspect "$TOPK_IMAGE" >/dev/null
docker run -it -d \
  --name yjl \
  --security-opt seccomp=unconfined \
  --cap-add SYS_ADMIN \
  --device /dev/davinci0 \
  --device /dev/davinci_manager \
  --device /dev/hisi_hdc \
  -e ASCEND_RT_VISIBLE_DEVICES=0 \
  -v "$TOPK_HOST_ROOT:/data/yjl/topk" \
  -v /home:/home \
  -v /usr/local/dcmi:/usr/local/dcmi \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
  -v /usr/local/Ascend/driver/lib64/:/usr/local/Ascend/driver/lib64/ \
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
  -v /etc/ascend_install.info:/etc/ascend_install.info \
  "$TOPK_IMAGE" /bin/bash
docker exec -it yjl /bin/bash
```

先检查这些宿主机路径确实存在，再运行。分配其他卡时同步替换 davinci0 和设备环境变量。某些平台还要求 `/dev/devmm_svm` 等设备，按该机器的官方部署规范补充，不凭旧服务器配置猜测；不要挂载不存在的设备。

此命令使用本地已有的相同镜像标签，默认不会重复拉取。为兼容较旧的 Docker，没有要求 `--pull` 或 `--platform` 实验开关。

本地镜像复用行为参考 [Docker run 官方说明](https://docs.docker.com/reference/cli/docker/container/run/)。

镜像名含 tilelang-ascend 不代表其中一定是最终交付要求的主仓后端。进入容器后仍需按 DEPENDENCIES.md 和 preflight 检查实际安装。镜像标签中的 CANN 版本也要以容器实际安装信息核实；宿主机 driver 版本不是 toolkit 版本。
