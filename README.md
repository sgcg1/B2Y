# B2Y执行材料入口

本仓用于同步辅助脚本、操作指南、实验结果和分析。TileOPs实现代码通过个人fork `https://github.com/sgcg1/TileOPs` 的main同步；B2Y辅助材料在服务器容器内直接克隆和更新。

当前进展：已结合Decode阶段数据与交接第4.2节完成[后续性能优化路线复评](deliveries/topk-optimization-roadmap-20261102.md)。主线为首轮粗键复用、分片计数/压缩，再验证Decode首轮分核；缓存溢出、尾部与扫描按证据降级。[本轮阶段结果](experiments/topk/20261102-stage1-decode-163258/analysis.md)及原始数据保留。本轮没有新增待执行命令，也无需重跑旧探针。

## 操作入口

| 需要做什么 | 文档 |
| --- | --- |
| 查看项目阶段进展总结 | [deliveries/topk-progress-summary-20261102.md](deliveries/topk-progress-summary-20261102.md) |
| 当前：后续性能优化路线复评 | [deliveries/topk-optimization-roadmap-20261102.md](deliveries/topk-optimization-roadmap-20261102.md) |
| 查看Decode阶段结果与定位依据 | [阶段结果报告](experiments/topk/20261102-stage1-decode-163258/analysis.md) |
| 重现实验：Decode真实TopK阶段诊断 | [diagnostics/topk-stage-timing/README.md](diagnostics/topk-stage-timing/README.md) |
| 历史：导出已完成probe2的原始样本与源码 | [diagnostics/topk-timer-probe/EXPORT_COMPLETE.md](diagnostics/topk-timer-probe/EXPORT_COMPLETE.md) |
| 上传结果到根目录AAA_Results | [AAA_Results/README.md](AAA_Results/README.md) |
| 查阅全部已归档实验（含失败、原始数据和哈希） | [experiments/topk/README.md](experiments/topk/README.md) |
| 历史probe1源码错误：只读导出与复查 | [diagnostics/topk-timer-probe/INSPECT_SOURCE.md](diagnostics/topk-timer-probe/INSPECT_SOURCE.md) |
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

实验保存规则：以后每次收到的结果均按独立ID归档到experiments/topk/，成功、失败和不完整结果都保留。原始数据不覆盖，并记录来源、版本、状态、缺失项和SHA-256；分析结论与原始数据分开。根目录“实验结果”只作为收件箱，历史数据以实验索引为入口。服务器未回传的文件不能补造。
