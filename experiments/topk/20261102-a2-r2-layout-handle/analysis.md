# A2 r2：布局推导handle/int32错误

报告版本r2、实际内核34f3bf36、工具身份匹配。基线及control均生成C++，SHA751a8288…且相同，编译stderr为空；之前基线哈希错误已消除。A2在AscendLayoutInference的FragmentThreadIndexProbe/IntSet::FromRange路径失败，stderr pos_inf 0，Cannot match type handle vs int32。尚未产生A2源码，无正确性或性能数据。

最直接的嫌疑是新增T.Parallel长度使用round相关if_then_else，导致布局推导不能取得有限线程范围；回传没有pass IR，不能断言唯一根因或排除后续其他限制。修复67b9e72f将原257项常量清零与首轮1024项常量清零分开，避免动态Parallel长度，保持首轮才付bank初始化成本；不改bank映射、归并或精确选择。

本地12项CPU回归通过，新增对所有Parallel长度只含编译期H/K/HIST_BANKS及无Call的检查、首轮初始化与后续不清bank检查；默认关闭AST仍等于冻结基线。r3工具离线身份及Python/Bash语法通过。NPU布局是否通过仍待现场，默认关闭，不放宽同步守卫。

原文按d1a6c7d Git blob两文件独立保存并记录SHA。重试使用新r3目录，不覆盖r2，也不重复旧探针。
