# B2Y执行材料入口

本仓用于同步辅助脚本、操作指南、实验结果和分析。TileOPs实现代码通过个人fork `https://github.com/sgcg1/TileOPs` 的main同步；B2Y辅助材料在服务器容器内直接克隆和更新。

当前下一步：打开 [最小设备计时探针指南](diagnostics/topk-timer-probe/README.md)，在现有yjl容器内运行探针，复制其中要求的probe-summary.txt。此步骤只需更新B2Y，不需要更新服务器TileOPs或重跑14项测试。

## 操作入口

| 需要做什么 | 文档 |
| --- | --- |
| 最小计时探针：验证计数器、完成屏障和观察开销 | [diagnostics/topk-timer-probe/README.md](diagnostics/topk-timer-probe/README.md) |
| 查看已完成的H128扫描实验结论 | [deliveries/scan-r1-results-20261102.md](deliveries/scan-r1-results-20261102.md) |
| 新服务器部署与完整实验流程 | [topk-950pr/START_HERE.md](topk-950pr/START_HERE.md) |
| 扫描优化候选的专项验证 | [topk-950pr/SCAN_OPTIMIZATION.md](topk-950pr/SCAN_OPTIMIZATION.md) |
| control校验错误定位 | [topk-950pr/CONTROL_DIAGNOSTICS.md](topk-950pr/CONTROL_DIAGNOSTICS.md) |
| torch / torch_npu升级到2.13 | [topk-950pr/TORCH_213_UPGRADE.md](topk-950pr/TORCH_213_UPGRADE.md) |

## 在服务器更新B2Y

宿主机执行；已经在yjl内则跳过：

```bash
docker exec -it yjl /bin/bash
```

随后在容器内检查：

```bash
git -C /home/y00937463/B2Y status --short
```

确认工作区干净且没有相关实验运行时，再更新：

```bash
git -C /home/y00937463/B2Y pull --ff-only origin main
```

有修改时先保存差异，不通过reset/clean覆盖。更新后按目标文档逐条执行，不把首次部署、环境升级和当前诊断的命令混在一起。

## 协作约定

两台电脑之间无法直接复制粘贴。今后所有要求操作者执行的命令，必须先写入本仓的指南或脚本并推送；聊天提供文档链接、目的和结果，不把聊天当作唯一命令来源。执行位置、所用环境、输出文件及失败处理应在文档中说明。

用户已确认本项目完全开源，并明确授权将本任务的相关实验结果、分析报告、脚本和指南同步到B2Y。此前关于服务器产出不能传出或不能发布的限制已更新，不应继续作为该范围内同步的阻塞理由。账户令牌、密码等凭据不进入仓库。
