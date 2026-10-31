# 当前新服务器交付：r3

下载 `topk-950pr-tools-20261031-r3.zip` 及同名 `.sha256`。本版对应用户已有yjl、Weekly 20260930镜像、私人目录/home/y00937463、/home:/home挂载；直接使用容器python3，不使用Conda。

工具源文件在本仓库 `topk-950pr/`。ZIP仅含辅助材料，不含TileOPs实现、镜像或SDK。源码仍通过个人fork main同步，服务器不克隆B2Y。

将ZIP和SHA文件手动上传到宿主机/home/y00937463，然后按包内START_HERE.md在宿主机校验、使用yjl内Python解压，再进入容器运行。

```bash
cd /home/y00937463
sha256sum --check topk-950pr-tools-20261031-r3.zip.sha256
mkdir -p /home/y00937463/tools
docker exec yjl python3 -m zipfile -e /home/y00937463/topk-950pr-tools-20261031-r3.zip /home/y00937463/unpacked-tools
cp -R /home/y00937463/unpacked-tools/topk-950pr/. /home/y00937463/tools/
docker exec -it yjl /bin/bash
```

本包未在新服务器实测；先完成小规格闭环，再运行完整Prefill。原始输出留在保密环境，按RESULTS_TEMPLATE.md仅回传允许披露的摘要。

r2 ZIP保留历史校验，不再作为这台机器的操作入口；其通用/data路径与新提供的实际配置不同。
