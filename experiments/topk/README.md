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

说明：日期以原日志为准；未提供执行日期的记录明确标注未知，ID中的日期可能只是归档批次。摘录或重建摘要均已标明，不能当作完整原始日志。原始profiler文件未回传时不会补造。后续结论修正用补充分析文件或新的版本记录，不修改原始数据。

更早的v0.1.0～v0.1.3数值和历史证据见[个人fork性能目录](https://github.com/sgcg1/TileOPs/tree/main/docs/performance/topk-select-950pr)。

当前下一步：[只读导出失败探针源码](../../diagnostics/topk-timer-probe/INSPECT_SOURCE.md)。无需重跑探针或TopK测试。
