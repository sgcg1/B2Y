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
