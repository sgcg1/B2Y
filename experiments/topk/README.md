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
