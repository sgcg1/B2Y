# 当前已存在的 yjl 容器

本版不要求再次创建Docker、不使用Conda。你的实际配置为：

- 容器名：`yjl`。
- 基础镜像：`quay.io/celenewyear/tilelang-ascend:cann9.3.0-weekly.20260930-ubuntu22.04-py3.12`。
- 私人目录：`/home/y00937463`，目前为空。
- 已挂载 `/home:/home`，因此私人目录在宿主机和容器内共享，路径相同。
- 已映射davinci0～7、davinci_manager、hisi_hdc；挂载driver库、版本文件、dcmi和npu-smi；使用seccomp=unconfined和SYS_ADMIN。

**不要重复运行docker run、删除或重建已有容器。** 映射了8张卡不代表应该同时占用8张；本工具只暴露一个获准设备，默认TOPK_DEVICE=0，按实际分配修改。

## 宿主机：检查并进入

```bash
docker ps -a --filter name=yjl
docker inspect yjl --format '{{.Config.Image}}'
docker inspect yjl --format '{{json .Mounts}}'
docker exec -it yjl /bin/bash
```

如果已创建但停止，且允许启动，在宿主机执行 `docker start yjl`，再进入。后续Python、pip、Git clone和NPU测试均在容器内运行；不激活宿主机Conda。

## 私人目录布局

```text
/home/y00937463/
  TileOPs/          # 个人fork main；服务器通过git同步实现
  B2Y/topk-950pr/  # 容器内直接克隆 B2Y 后使用的辅助工具
  runs/             # 每轮独立原始结果、cache和logs
  tmp/              # 私人短临时目录
  python-deps/      # 可选：缺少的小型测试依赖，不用Conda
```

只写这个私人目录。不要更改宿主机driver、其他用户目录、共享Docker daemon或系统时钟。无需新增/data挂载；配置脚本不会修改HOME。

## 镜像内的环境仍需检查

镜像标签表明其发布名称中的CANN Weekly日期是 **20260930**，不是旧服务器的20261021。实际toolkit版本、torch/torch_npu、TileLang主仓后端、编译器和SOC以容器预检为准。driver版本不等于CANN toolkit版本，镜像名含tilelang-ascend也不证明其源码路线。

若ASCEND_HOME_PATH已有效设置，env.sh直接使用它；否则设置CANN_ENV_SCRIPT为容器内真实的toolkit环境脚本。不要默认source /data/setenv.bash，也不要把toolbox的环境脚本当作toolkit激活脚本。直接使用镜像的python3，检查要求见DEPENDENCIES.md。

## 仅供以后需要镜像传输时参考

当前yjl已创建，无需为了本任务重新拉取镜像。确需在获准机器准备同一镜像时：

```bash
export TOPK_IMAGE=quay.io/celenewyear/tilelang-ascend:cann9.3.0-weekly.20260930-ubuntu22.04-py3.12
docker pull "$TOPK_IMAGE"
docker image inspect "$TOPK_IMAGE" --format '{{.Os}}/{{.Architecture}}'
```

服务器为x86_64，不需要开启--platform实验功能。若Docker daemon不能访问Quay，而现场已有skopeo及获准的shell代理，可以在私人目录导出后导入：

```bash
export TOPK_IMAGE=quay.io/celenewyear/tilelang-ascend:cann9.3.0-weekly.20260930-ubuntu22.04-py3.12
skopeo copy "docker://$TOPK_IMAGE" "docker-archive:/home/y00937463/tilelang-ascend.tar:$TOPK_IMAGE"
docker load -i /home/y00937463/tilelang-ascend.tar
```

archive最后使用完整镜像名称，避免导入后标签不匹配。没有skopeo时由现场提供工具或内部镜像源，不为个人任务修改共享daemon或执行系统级安装。镜像tar不提交B2Y。

参考：[Skopeo官方archive格式](https://github.com/containers/skopeo/blob/main/docs/skopeo.1.md)、[Docker镜像复用行为](https://docs.docker.com/reference/cli/docker/container/run/)。
