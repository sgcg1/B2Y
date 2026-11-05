最新结果：[第2步宿主预约配置阻塞](20261105-roadmap-step2-host-inspect-112739/analysis.md)。宿主共享锁存在，yjl不可见且PID命名空间独立；CPU通过，BMM未执行。

最新结果：[4.2第2步CPU通过、宿主预约阻塞](20261105-roadmap-step2-r1-111338/analysis.md)。公共receipt通过，279+101项通过/14项skip；BMM未执行，继续停在第2步，不重复CPU或开展性能优化。

最新回传：[原生直方图r1调用前dtype失败](20261105-native-histogram-r1-105405/analysis.md)。full_zero编译及原生标记通过；int16输出未转uint16 view导致FFI拒绝，0项设备验证、无耗时。已修复runner绑定，更新后按原生直方图r1入口重试；不改内核/oracle，不据失败判断硬件能力。

最新结果：[阈值原语r1](20261105-threshold-primitives-r1-102742/analysis.md)：两项24组×3次通过，SIMT键转换46.002μs、融合收集67.951μs，不可相加。发现嵌套SIMD频数/累计histogram源码与codegen线索，实际API/指令/耗时尚待验证。

最新结果：[实际归并r2正确但慢](20261105-merge-execution-r2-093737/analysis.md)：两档32组×3次设备验证通过，R128为58.458μs、R256为55.391μs/节点。10窗口重放一致；暂停直接集成SIMT排名路径，下一道关卡是低成本向量排序/归并表达。

最新复核：[实际归并r1同步诊断](20261105-merge-execution-r1-093046/analysis.md)：两档完成编译，但ThreadSync守卫拒绝执行，设备正确性和耗时未知。r2已改有界访问与分歧写表达，继续保留守卫。

最新结果：[独立M消费数探针](20261105-merge-consumption-probe-r1-090941/analysis.md)：二分与树归约通过，scan对照失败；无scan/atomic硬依赖的反例已设备验证，无完整M性能数据。

最新结果：[950PR完整同规格对照](20261104-950pr-device-compare-r1-113714/analysis.md)：45样本/侧，57.639μs vs 10.639μs，0.1846x TopKV2；90窗口原始设备记录重放一致。普通随机路径未达目标，尚未新增优化。

最新复核：[950PR计时解析修复](20261104-950pr-device-compare-r1-112402/analysis.md)：GE构建与双方计时前正确性已通过；持久模型注册误报为缺失执行。原始记录已离线重放验证，尚无完整TopKV2对照。

最新复核：[950PR对照GE临时路径失败](20261104-950pr-device-compare-r1-110915/analysis.md)：自研四kernel编译完成，GE内部AF_UNIX路径过长，尚无设备耗时；工具已改短临时目录并增加Manager预检。

最新复核：[r14窗口预计算结果](20261104-formal-decode-r14-091517/analysis.md)：非全窗快1.36%–9.20%，全窗有回退，随机仍约0.36x；保留窗口专门候选，后续主线返回候选可缓存路径，无需重跑。

最新复核：[粗桶缓存r13窗口权衡](20261103-formal-decode-r13-213748/analysis.md)：全窗溢出再降3.59%–5.51%，窄窗回退6.12%–6.22%，不全局启用；通用起点仍保留5eb130ef输入+完整键缓存，无需重跑。

最新复核：[溢出键缓存r12收益](20261103-formal-decode-r12-210254/analysis.md)：全窗溢出进一步减少3.69%–5.79%，缓存路径小回退，按已确认取舍保留实验组合，默认不变，无需重跑。

最新复核：[溢出暂存扩大验证r11](20261103-formal-decode-r11-204010/analysis.md)：四类全窗溢出事件减少29.15%–32.49%，额外窗口/特殊值通过；随机CANN及窄窗整体计时波动保留，默认不变，无需重跑。

最新复核：[溢出finish UB暂存约28.1%收益](20261103-formal-decode-r10-201614/analysis.md)：同步诊断未再出现；全同分事件约417μs、0.060–0.063xAscend C，缓存路径小回退，保留候选待扩大溢出验证，默认不变，无需重跑。

最新复核：[histogram UB暂存稳定收益](20261103-formal-decode-r8-194515/analysis.md)：随机事件减少1.62%–3.50%，0.362–0.373xAscend C；8组均改善，保留为后续实验起点，默认不变，profile待复核，无需重跑。

最新复核：[跳过恒定索引轮的分布权衡](20261103-formal-decode-r7-192613/analysis.md)：小边界finish减少约24.8%，随机近持平，溢出回退约0.71%；不提升通用默认，下轮以9a5087dd组合为起点，无需重跑。

最新复核：[quota VF合并未获足够净收益](20261103-formal-decode-r6-191334/analysis.md)：随机仅改善0.21%–0.70%，小边界回退2.74%–3.03%、溢出回退0.80%–0.87%。FUSE_QUOTA继续关闭，下轮以9a5087dd UB暂存组合为起点，无需重跑。

最新复核：[UB输入暂存筛选收益](20261103-formal-decode-r5-173420/analysis.md)：随机事件减少2.6%–3.6%，0.343–0.360xAscend C；保留实验候选，profile待复核，默认不变，无需重跑。

最新复核：[compact 512扫描否定结果](20261103-formal-decode-r4-170633/analysis.md)：两份报告及源端SHA已核验；全部事件回退，保持128，不扩大512测试。quota guard收益独立保留，无需重跑。

最新复核：[20261103-formal-decode-r3-161729](20261103-formal-decode-r3-161729/analysis.md)：两份分片报告已还原；随机事件0.329–0.350xAscend C，较上版快15.4%–16.6%；全同分溢出回退约1.18%。保持实验候选，默认不变；profile待复核，无需重跑。

# TopK实验档案

收到的成功、失败和不完整结果按独立ID归档；原始数据不覆盖。metadata.json记录来源、版本、状态、文件大小及SHA-256。根目录“实验结果”只是收件箱，不作为唯一档案。

| ID | 内容 | 状态 |
| --- | --- | --- |
| [20261031-preflight-torch-version](20261031-preflight-torch-version/metadata.json) | 初次预检版本门槛失败 | failed_preflight |
| [undated-before-scan-decode](undated-before-scan-decode/metadata.json) | 优化前Decode摘要 | reported_measurement |
| [20261102-control-unlabeled-bounds](20261102-control-unlabeled-bounds/metadata.json) | 初始control无版本标识的范围断言 | failed_unlabeled_control |
| [20261102-grouped-h256-diagnostic](20261102-grouped-h256-diagnostic/metadata.json) | 逐版本诊断定位H256未填槽位 | failed_grouped_h256 |
| [20261102-scan-r1-h128-complete](20261102-scan-r1-h128-complete/metadata.json) | H128完整回传及两轮控制 | measured_candidate_not_final_accepted |
| [20261102-timer-probe1-source-order](20261102-timer-probe1-source-order/metadata.json) | 计时探针源码顺序检查失败 | failed_source_validation |
| [20261102-timer-probe1-source-inspection](20261102-timer-probe1-source-inspection/metadata.json) | probe1生成源码确认预期屏障/计时顺序未保留 | source_sequence_mismatch_confirmed |
| [20261102-timer-probe2-summary](20261102-timer-probe2-summary/metadata.json) | probe2完成最小采样；缺原始样本和源码 | summary_calibration_promising_raw_review_pending |
| [20261102-timer-probe2-complete](20261102-timer-probe2-complete/metadata.json) | probe2原始样本与20份源码；同一运行的完整补充 | minimal_probe_reviewed_topk_diagnostic_pending |
| [20261102-stage1-decode-163258](20261102-stage1-decode-163258/metadata.json) | Decode首轮histogram/compact为主耗时；原始时间戳齐全 | decode_stage_evidence_reviewed_candidate_optimization_pending |

说明：日期以原日志为准；未提供执行日期的记录明确标注未知，ID中的日期可能只是归档批次。摘录或重建摘要均已标明，不能当作完整原始日志。原始profiler文件未回传时不会补造。后续结论修正用补充分析文件或新的版本记录，不修改原始数据。

更早的v0.1.0～v0.1.3数值和历史证据见[个人fork性能目录](https://github.com/sgcg1/TileOPs/tree/main/docs/performance/topk-select-950pr)。

当前操作入口见[仓库首页](../../README.md)。[Decode阶段结果](20261102-stage1-decode-163258/analysis.md)已复核，首轮histogram/compact占已测区间约81%；当前无需重复运行stage1。生产版本与全规格性能仍未接受，历史数据和结论均保留。

- [A0 r1双进程筛选：未证明稳定收益](20261102-a0-r1-201744/analysis.md)，原始上传、SHA及复算见同目录。

- [A1 r1前端嵌套失败与修复](20261102-a1-r1-eager-nesting/analysis.md)，两次失败原文均保存。

最新：[A1 r2结果复核](20261102-a1-r2-203417/analysis.md)：600事件完整，耗时下降约0.91%–1.14%，但ThreadSync竞争警告未解，保持关闭；先查同步，不原样重跑或直接扩大测试。

- [同步复现uint8x2失败](20261102-a1-sync-repro-uint8x2/analysis.md)，原始记录保留。

最新：[同步最小复现r2已复核](20261102-a1-sync-repro-r2-204739/analysis.md)，四配置编译通过；uint8有额外屏障、uint32无，但未重现生产外提警告，A1仍关闭。下一步回到生产访问对排查，无需重跑此复现。

- [A2 r1工具身份错误](20261102-a2-r1-baseline-digest/analysis.md)，未开始设备编译。

- [A2 r2布局失败](20261102-a2-r2-layout-handle/analysis.md)，基线/control编译成功，A2未产源码。

- [A2 r3原子参数代码生成失败](20261102-a2-r3-atomic-codegen/analysis.md)，已提取回传C++。

- [A2 r4性能回退](20261102-a2-r4-211000/analysis.md)，600事件完整，候选不接受。

- [Decode小P成本结果](20261102-decode-pilot-r1-211917/analysis.md)，1200事件完整，不是完整TopK。

- [完整Decode full-r1结果](20261102-decode-full-r1-213318/analysis.md)：1200事件完整，默认拒绝因溢出回退。

- [Decode full-r2尾段权衡](20261102-decode-full-r2-214318/analysis.md)，1200事件完整，默认未接受。

- [Decode full-r3容量路由结果](20261103-decode-full-r3-090700/analysis.md)，1600事件完整，待扩展验证。

- [正式Decode基线与设备拆解](20261103-formal-decode-r1-094013/analysis.md)：一完整进程、一部分采集失败；750事件及全部原始CSV保留。

- [prepare并行归约结果与分片恢复](20261103-formal-decode-r2-101431/analysis.md)：1600事件内部复核，源端manifest未到，保留profile待复核状态。
