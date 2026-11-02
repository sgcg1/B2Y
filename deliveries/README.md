# 当前新服务器指南：r8

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

目录内 r2/r3 ZIP 和 SHA 文件保留用于历史校验，反映当时的传输流程；不作为当前执行入口。r8 直接通过本仓 topk-950pr/ 提供，不另发 ZIP。

本工具尚未在新服务器实测。先完成小规格闭环，再运行完整 Prefill。原始输出留在保密环境，只按 RESULTS_TEMPLATE.md 回传允许披露的摘要。

工具允许 torch2.10.x + torch_npu2.10.x 进入 TopK 兼容性实测，同时记录其不满足项目声明的torch2.13范围；保留已有环境，不因版本门槛强制升级。更新工具后必须新建 EVIDENCE，再运行 preflight 和14项测试。

2026-11-02新增v0.1.4-scan-r1桶扫描候选。扫描候选初始工具版本20261102-r6；专项现场步骤见 [SCAN_OPTIMIZATION.md](../topk-950pr/SCAN_OPTIMIZATION.md)。先更新个人fork和B2Y，再新建EVIDENCE完成CPU检查、14项NPU测试及两轮新旧扫描事件对照；稳定改善后才扩大规格。候选尚无NPU实测结论，未打正式v0.1.4标签。

此前工具20261102-r7补齐control逐版本校验和只诊断模式。发生无版本标识的索引断言时，按 [CONTROL_DIAGNOSTICS.md](../topk-950pr/CONTROL_DIAGNOSTICS.md) 更新B2Y、新建诊断EVIDENCE，再运行preflight和control-diagnose。此步不改内核、不要求先重跑14项，也不产出性能数据。

当前20261102-r8根据逐版本诊断明确拒绝H256分组扫描（253个哨兵未补齐），kernel配置保护只放行H128分组扫描。H256底层原因未修复；正式对照限5项H128相关实现，并打印/记录排除项。按SCAN_OPTIMIZATION.md更新个人fork与B2Y，新建EVIDENCE完成CPU6项、预检、14项契约和两轮对照；H128性能现已回传，见后续分析报告；此处保留r8发布时的变更说明。

新增独立诊断：[最小计时探针20261102-probe1](../diagnostics/topk-timer-probe/README.md)，验证计数器、完成屏障与观察开销。本次仅新增通用探针代码和操作指南，不附带服务器实验结果或分析。已有topk-950pr工具及MANIFEST未改；服务器只需更新B2Y，不必更新TileOPs或重跑契约测试。探针尚未在目标SDK实测，运行后审核probe-summary.txt。

当前统一入口：[仓库README](../README.md)。用户已确认项目完全开源并授权本任务分析报告同步；[H128完整实验分析](scan-r1-results-20261102.md)现纳入本仓。后续待执行命令均先写入本仓并推送，聊天不作为唯一命令来源。

probe1首次现场失败于Counter/fence源码顺序检查，尚无计时校准结果。当前按 [只读源码导出指南](../diagnostics/topk-timer-probe/INSPECT_SOURCE.md) 收集原失败目录源码，不重跑NPU。已建立 [长期实验档案](../experiments/topk/README.md)，保存原始回传、失败和缺失信息；不覆盖历史数据。
