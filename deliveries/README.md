# 当前新服务器指南：r5

当前流程在已有 yjl 容器内直接克隆 B2Y，使用镜像自带 python3。工具入口为 `/home/y00937463/B2Y/topk-950pr`，完整步骤见 `../topk-950pr/START_HERE.md`。

在宿主机进入容器：

```bash
docker exec -it yjl /bin/bash
```

随后在容器内首次克隆：

```bash
git clone --branch main https://gitcode.com/JotaroSSR/B2Y.git /home/y00937463/B2Y
git clone --branch main https://github.com/sgcg1/TileOPs.git /home/y00937463/TileOPs
git -C /home/y00937463/TileOPs fetch origin --tags
```

无需下载交付 ZIP、创建额外 tools 目录或安装 Conda。已有仓库应检查工作区干净后 pull，不重复 clone。后续读取 START_HERE.md，核实 Python/CANN 依赖并设置本轮 EVIDENCE，再运行 preflight。

配置仍为已有 yjl、Weekly 20260930 镜像、私人目录 /home/y00937463、/home:/home 挂载。源码仅通过个人 fork main 同步。本仓只提供辅助材料，不包含镜像、SDK或源码副本。

目录内 r2/r3 ZIP 和 SHA 文件保留用于历史校验，反映当时的传输流程；不作为当前执行入口。r5 直接通过本仓 topk-950pr/ 提供，不另发 ZIP。

本工具尚未在新服务器实测。先完成小规格闭环，再运行完整 Prefill。原始输出留在保密环境，只按 RESULTS_TEMPLATE.md 回传允许披露的摘要。

当前 r5 允许 torch2.10.x + torch_npu2.10.x 进入 TopK 兼容性实测，同时记录其不满足项目声明的torch2.13范围；保留已有环境，不因版本门槛强制升级。更新工具后必须新建 EVIDENCE，再运行 preflight 和14项测试。
