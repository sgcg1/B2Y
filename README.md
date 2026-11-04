调用归属核对：[ops-math与GE TopKV2关系](deliveries/topk-ops-math-call-confirmation-20261104.md)。ops-math是库，TopKV2是其中算子；旧GE日志确认加载ops_math实现，但网页历史adapter仍未公开核实。后续950PR同环境对照需固定官方原生入口与完整适配边界。

最新目标：[950PR同环境稳定优于ops-math](deliveries/topk-ops-math-measurement-trace-20261104.md)，不以截图43.7μs为固定阈值。已核对launcher/PR快照/原生计时链路；实际TopKSelect ops-math适配入口尚待确认，不能用旧GE事件代替。

正式测量状态：[公共协议就绪检查](deliveries/topk-public-measurement-readiness-20261104.md)。用户仅能用旧yjl 950PR环境，目标canonical环境不匹配且TopKSelect尚未接入目标分支；正式耗时未知，不伪造或降级验收，无新NPU运行。

交付目标校正：[TopKSelect单case规格与PR规范](deliveries/topk-delivery-contract-20261104.md)。最终PR目标yyttt6/TileOPs:ascend950，当前范围ds-v32-topk-decode-b1；截图ops-math=0.0437ms，历史开发倍率不能作正式验收。算法审计暂停状态保持。

当前状态：按用户要求暂停新增优化/设备试跑，转入[TopK溢出算法审计](deliveries/topk-overflow-algorithm-audit-20261104.md)。确认缓存阈值断崖、单核全行多轮扫描及热点计数等结构问题；先审查完整算法方案，历史结果全部保留。

最新复核：[r14窗口预计算结果](experiments/topk/20261104-formal-decode-r14-091517/analysis.md)：非全窗快1.36%–9.20%，全窗有回退，随机仍约0.36x；保留窗口专门候选，后续主线返回候选可缓存路径，无需重跑。

最新入口：[窗口内预计算r14](diagnostics/topk-formal-decode-r14/README.md)：928b34fd已推送个人fork，仅限制粗桶/完整键预计算范围，保留整行DMA；新增窗口长度覆盖，尚无设备结果。

最新复核：[粗桶缓存r13窗口权衡](experiments/topk/20261103-formal-decode-r13-213748/analysis.md)：全窗溢出再降3.59%–5.51%，窄窗回退6.12%–6.22%，不全局启用；通用起点仍保留5eb130ef输入+完整键缓存，无需重跑。

最新入口：[溢出粗桶复用r13](diagnostics/topk-formal-decode-r13/README.md)：5e01bbeb已推送个人fork，保留溢出暂存/完整键缓存，复用原输入UB缓存粗桶，不增缓冲或VF，尚无设备结果。

最新复核：[溢出键缓存r12收益](experiments/topk/20261103-formal-decode-r12-210254/analysis.md)：全窗溢出进一步减少3.69%–5.79%，缓存路径小回退，按已确认取舍保留实验组合，默认不变，无需重跑。

最新入口：[溢出分数键缓存r12](diagnostics/topk-formal-decode-r12/README.md)：5eb130ef默认关闭，保留溢出暂存；GitHub认证失败，候选用B2Y校验bundle快进同步，尚无设备结果。

最新复核：[溢出暂存扩大验证r11](experiments/topk/20261103-formal-decode-r11-204010/analysis.md)：四类全窗溢出事件减少29.15%–32.49%，额外窗口/特殊值通过；随机CANN及窄窗整体计时波动保留，默认不变，无需重跑。

最新执行入口：[溢出扩大验证r11](diagnostics/topk-formal-decode-r11/README.md)：内核仍ec986f88，不叠加优化；新增容量边界/量化/接近分数/窄窗和特殊值验证，窄窗不算CANN倍率，尚无本轮设备结果。

最新复核：[溢出finish UB暂存约28.1%收益](experiments/topk/20261103-formal-decode-r10-201614/analysis.md)：同步诊断未再出现；全同分事件约417μs、0.060–0.063xAscend C，缓存路径小回退，保留候选待扩大溢出验证，默认不变，无需重跑。

最新入口：[r9同步诊断后的有界访问重试r10](diagnostics/topk-formal-decode-r10/README.md)：ec986f88补充溢出UB读取范围，14项CPU检查通过；现场同步诊断仍需验证，守卫保留，无r9性能数据。

最新执行入口：[finish溢出输入暂存r9](diagnostics/topk-formal-decode-r9/README.md)：39bb2f6f默认关闭，溢出时增加64KiB输入UB缓存，双方均保留hist/compact暂存及quota guard，尚无设备结果。

最新复核：[histogram UB暂存稳定收益](experiments/topk/20261103-formal-decode-r8-194515/analysis.md)：随机事件减少1.62%–3.50%，0.362–0.373xAscend C；8组均改善，保留为后续实验起点，默认不变，profile待复核，无需重跑。

最新执行入口：[histogram UB输入暂存r8](diagnostics/topk-formal-decode-r8/README.md)：4fd6a00e默认关闭，仅改变histogram访存，两侧保留compact暂存及quota guard，关闭r6/r7开关，尚无设备结果。

最新复核：[跳过恒定索引轮的分布权衡](experiments/topk/20261103-formal-decode-r7-192613/analysis.md)：小边界finish减少约24.8%，随机近持平，溢出回退约0.71%；不提升通用默认，下轮以9a5087dd组合为起点，无需重跑。

最新执行入口：[finish跳过恒定索引高字节r7](diagnostics/topk-formal-decode-r7/README.md)：候选23ff5c63默认关闭；跳过两轮无效索引radix，保留UB暂存/quota guard，FUSE_QUOTA关闭，尚无设备结果。

最新复核：[quota VF合并未获足够净收益](experiments/topk/20261103-formal-decode-r6-191334/analysis.md)：随机仅改善0.21%–0.70%，小边界回退2.74%–3.03%、溢出回退0.80%–0.87%。FUSE_QUOTA继续关闭，下轮以9a5087dd UB暂存组合为起点，无需重跑。

最新执行入口：[finish quota更新合并VF r6](diagnostics/topk-formal-decode-r6/README.md)：93af88eb默认关闭，每个执行轮次少一次VF；两侧保留UB暂存、128扫描、quota guard，尚无设备结果。

最新复核：[UB输入暂存筛选收益](experiments/topk/20261103-formal-decode-r5-173420/analysis.md)：随机事件减少2.6%–3.6%，0.343–0.360xAscend C；保留实验候选，profile待复核，默认不变，无需重跑。

最新执行入口：[compact UB输入暂存r5](diagnostics/topk-formal-decode-r5/README.md)：候选9a5087dd默认关闭，仅增加每核16KiB输入暂存；两侧均128扫描并保留quota guard，尚无设备结果。

最新复核：[compact 512扫描否定结果](experiments/topk/20261103-formal-decode-r4-170633/analysis.md)：两份报告及源端SHA已核验；全部事件回退，保持128，不扩大512测试。quota guard收益独立保留，无需重跑。

最新执行入口：[compact 512扫描正式对照r4](diagnostics/topk-formal-decode-r4/README.md)：只改compact执行粒度，沿用quota guard；候选364fed4c默认关闭，尚无设备结果。

最新复核：[20261103-formal-decode-r3-161729](experiments/topk/20261103-formal-decode-r3-161729/analysis.md)：两份分片报告已还原；随机事件0.329–0.350xAscend C，较上版快15.4%–16.6%；全同分溢出回退约1.18%。保持实验候选，默认不变；profile待复核，无需重跑。

# B2Y执行材料入口

**当前回传辅助：[两份正式结果小文本拆分](tools/b2y-result-parts/README.md)。** formal-decode-r2两份log已收到，txt尚缺；脚本只读原始结果，gzip+base64拆片并自动生成无损恢复清单，不重跑NPU。先小批次测试上传，不假设拆分能解决TLS。

**当前执行入口：[prepare分组并行归约正式对照](diagnostics/topk-formal-decode-r2/README.md)。** cd94fb34已推送、默认关闭；同轮对照CANN/旧默认/冻结r3/新prepare，仅改offset归约，保留原始CSV与残缺采集标记。

**当前执行入口：[正式Decode基线与设备拆解](diagnostics/topk-formal-decode-r1/README.md)。** 冻结r3实现不改算法，同输入同轮比较官方CANN/旧TileLang/r3；独立记录事件倍率、四kernel设备耗时和间隙，原始CSV回传。此前full-r3无需重跑。

**当前下一步：[Decode full-r2稳定tie对照](diagnostics/topk-decode-full-r2/README.md)。** 候选0d4063e6只改精确尾段，默认关闭；比较默认基线、冻结P4-r1及新P4-r2，尚无r2设备结果。

**当前执行入口：[完整Decode四kernel实验候选](diagnostics/topk-decode-full-r1/README.md)。** 提交03c8f916已推送，P2/P4完成选择并与冻结基线对照；默认路由不变，尚无本候选NPU结果。成本探针已完成，无需重跑。

**当前执行入口：[Decode首轮P1/P2/P4成本验证](diagnostics/topk-decode-pilot-r1/README.md)。** 独立探针72a84811已推送，测直方图和两kernel阈值归并事件；不是完整TopK，不启用A0/A1/A2。此前候选与失败记录见下方历史进展。

本仓用于同步辅助脚本、操作指南、实验结果和分析。TileOPs实现代码通过个人fork `https://github.com/sgcg1/TileOPs` 的main同步；B2Y辅助材料在服务器容器内直接克隆和更新。

**新会话接手先读：[2026-11-02完整交接](deliveries/topk-handoff-20261102.md)。** 包含当前实测版本、证据入口、下一步候选、已踩坑和最新协作条件。 用户已确认B2Y（GitCode）与TileOPs（GitHub）均推送成功。

当前进展：已结合Decode阶段数据与交接第4.2节完成[后续性能优化路线复评](deliveries/topk-optimization-roadmap-20261102.md)。主线为首轮粗键复用、分片计数/压缩，再验证Decode首轮分核；缓存溢出、尾部与扫描按证据降级。[本轮阶段结果](experiments/topk/20261102-stage1-decode-163258/analysis.md)及原始数据保留。新增默认关闭的A0粗键表达式复用候选；[当前设备筛选入口](diagnostics/topk-a0-r1/README.md)。用户已确认两个仓库均推送成功，按指南更新仓库后可开始设备筛选；[A0双进程筛选已复核](experiments/topk/20261102-a0-r1-201744/analysis.md)：未证明稳定收益，保持默认关闭，不再扩大A0测试；独立A1粗键缓存候选已实现并推送944bc00d，默认关闭，当前请按[A1设备筛选指南](diagnostics/topk-a1-r2/README.md)执行，无需重跑旧探针。

## 操作入口

| 需要做什么 | 文档 |
| --- | --- |
| 当前：A1独立候选设备筛选 | [diagnostics/topk-a1-r2/README.md](diagnostics/topk-a1-r2/README.md) |
| 历史：A0独立候选设备筛选 | [diagnostics/topk-a0-r1/README.md](diagnostics/topk-a0-r1/README.md) |
| 新会话接手：完整交接 | [deliveries/topk-handoff-20261102.md](deliveries/topk-handoff-20261102.md) |
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

A1 r1两次前端嵌套失败已归档，当前使用r2修复指南；尚无A1性能结果。

最新：[A1 r2结果复核](experiments/topk/20261102-a1-r2-203417/analysis.md)：600事件完整，耗时下降约0.91%–1.14%，但ThreadSync竞争警告未解，保持关闭；先查同步，不原样重跑或直接扩大测试。

当前下一步：[A1同步最小编译复现](diagnostics/topk-a1-sync-repro/README.md)。已发现官方0176ba14原子指针别名检查疑似混合dtype单位问题；尚未证明全部警告误报，A1保持关闭。仅编译四个小kernel，不运行性能测试，不改安装。

当前仅编译诊断改用[r2入口](diagnostics/topk-a1-sync-repro-r2/README.md)：首版因uint8x2代码生成失败，未完成同步对照。A1仍关闭，不重跑旧诊断。

最新：[同步最小复现r2已复核](experiments/topk/20261102-a1-sync-repro-r2-204739/analysis.md)，四配置编译通过；uint8有额外屏障、uint32无，但未重现生产外提警告，A1仍关闭。下一步回到生产访问对排查，无需重跑此复现。

最新：[A1同步源码审计及候选补丁](diagnostics/topk-a1-sync-source-review/README.md)。指针区间混合元素单位缺陷可构造；补丁仅做应用及4项CPU算术检查，未编译/未安装，A1继续关闭。约1%收益暂不值得主线依赖工具链重建，下一项优先独立A2 int32分片histogram；没有新服务器指令。

当前执行入口：[A2 r1首轮4组int32直方图](diagnostics/topk-a2-r1/README.md)。候选34f3bf36已推送GitHub，默认关闭；A0/A1关闭，10项CPU检查通过，尚无A2 NPU结果。先编译/正确性后对照，ThreadSync诊断出现即拒绝计时。

当前使用[A2 r2指南](diagnostics/topk-a2-r2/README.md)，r1工具生成误改基线哈希，已归档并修正。内核仍34f3bf36；离线身份回归已捕获r1并验证r2，尚无A2设备结果。

当前入口：[A2 r3](diagnostics/topk-a2-r3/README.md)。r2在布局推导失败，候选67b9e72f已改成常量并行长度并推送；12项CPU检查与离线身份通过，尚待现场编译，无A2性能结果。

当前入口：[A2 r4](diagnostics/topk-a2-r4/README.md)。r3已过布局但Bisheng因原子条件下标生成语句失败；4774e7ea改为显式int32索引，13项CPU检查通过，工具预存生成源码；尚无A2性能结果。

最新：[A2 r4复核](experiments/topk/20261102-a2-r4-211000/analysis.md)：四组事件耗时增加4.04%–4.36%，无编译同步警告，筛选正确性通过但性能回退；保持关闭，不扩大或重跑。下一步评估Decode首轮小P并行成本，尚无新指令。

最新：[Decode成本探针已复核](experiments/topk/20261102-decode-pilot-r1-211917/analysis.md)，P4直方图+归并约18.87–19.05μs，有继续实现compact与精确后续的空间，但不是完整TopK收益。两进程成功，1200样本完整，不因提示编码重跑。

最新：[完整Decode full-r1已复核](experiments/topk/20261102-decode-full-r1-213318/analysis.md)。P4随机耗时下降42.7%–43.1%，小边界下降61.3%–61.9%，全同分溢出增加约42%；1200事件及校验通过、编译无同步诊断，但不接受默认。下一步优先改进溢出尾段，暂不重跑。

最新：[Decode full-r2已复核](experiments/topk/20261102-decode-full-r2-214318/analysis.md)。随机较默认下降43.5%–44.1%，溢出下降17.4%；小边界仍比默认快约30%，但比r1慢约82%。下一步设备内按候选容量选择尾段，不能D2H路由；当前未接受默认，无需重跑。

当前入口：[Decode full-r3设备容量路由](diagnostics/topk-decode-full-r3/README.md)，c022114c已推送、默认关闭。≤2048用r1、溢出用r2，无D2H；5项CPU测试及身份/语法通过，尚无r3设备结果。一次对照默认/r1/r2/r3，完整调用事件，新增2048/2049边界校验。

最新：[Decode full-r3复核](experiments/topk/20261103-decode-full-r3-090700/analysis.md)：随机较默认下降43.2%–43.4%、溢出下降16.1%–16.2%、小边界下降61.8%；1600事件及容量边界校验通过，编译诊断为空，路由有额外成本。优先进入更广泛Decode验证及同轮CANN/设备流水记录，尚未默认接受，无需重跑。

最新：[正式基线设备拆解](experiments/topk/20261103-formal-decode-r1-094013/analysis.md)。随机r3约0.105–0.107x Ascend C设备包络、0.213–0.216x事件；prepare约28.7μs、finish约31.6μs，gap总计约0.066μs。第一进程完整，第二因239条部分流水失败，其最后50完整调用仅作补充，缺第二CANN设备复现。下一步优先prepare并行归约，随后finish执行粒度与向量统计；默认不接受，旧测量无需立即重跑。

最新：[prepare并行归约复核](experiments/topk/20261103-formal-decode-r2-101431/analysis.md)。10片gzip/CRC恢复两报告，1600事件和64 CSV内部核对通过；原文SHA未与源端manifest比对但不阻断分析。prepare约28.7→4.75μs，随机事件0.277–0.284x Ascend C，较冻结r3少25.1%–25.9%；profile gap波动和残段仍待复核。下一项finish的设备quota终止/执行粒度，默认不启用，无需重跑或重拆。

当前入口：[finish设备quota守卫](diagnostics/topk-formal-decode-r3/README.md)，949d73c4已推送，EARLY_EXIT默认false。保留已测分组prepare/容量路由，仅跳过quota归零后的VF工作；7项内核测试、8项解析及身份/语法通过，尚无新设备结果。对照CANN/旧默认/冻结cd94fb34/新守卫，两进程结果后自动拆为小片回传。
