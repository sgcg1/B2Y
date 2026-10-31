# 新服务器辅助工具交付

下载 `topk-950pr-tools-20261031-r2.zip` 及同名 `.sha256` 校验文件。工具源文件也在本仓库 `topk-950pr/` 中。

该ZIP只包含辅助脚本和指南，不含TileOPs实现、镜像、SDK或旧机器缓存。实现通过个人fork的main同步；服务器不克隆B2Y。

Linux校验、解压：

```bash
sha256sum --check topk-950pr-tools-20261031-r2.zip.sha256
python3 -m zipfile -e topk-950pr-tools-20261031-r2.zip ./unpacked-tools
```

Windows可以直接解压ZIP。手动传入 `unpacked-tools/topk-950pr/`，从其中 `START_HERE.md` 开始，区分宿主机和yjl容器命令。

包中的NPU工具尚未在新服务器实测；先完成小规格闭环，再运行完整Prefill。原始输出留在保密环境，按RESULTS_TEMPLATE.md仅回传允许披露的摘要。
