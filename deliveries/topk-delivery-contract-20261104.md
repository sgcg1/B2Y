# TopKSelect交付目标与验收规格校正

用户于2026-11-04指定最终跟踪及PR目标为https://github.com/yyttt6/TileOPs ，PR基分支ascend950；规范入口https://github.com/yyttt6/TileOPs/issues/1 。个人fork sgcg1/TileOPs继续作为开发提交副本，B2Y用于材料/结果传输，二者不是最终验收目标。已在本地添加upstream指向yyttt6/TileOPs并fetch，记录目标分支f0072a85a3ce1a4bcc520ba12cd09a0337871131。

## 用户指定当前验收case

- 公共Op：TopKSelectFwdOp；页面名称TopKSelectFwd。
- case ID：ds-v32-topk-decode-b1。
- B=1，S=1，S_kv=16384，G=1，topk=2048。
- index_score [1,1,16384,1]，float32。
- starts、ends [1,1]，int32。
- indexes [1,1,1,2048]，int32。
- manifest生成窗口starts=0、ends=16384。Op仍有窗口及短窗填S_kv契约，输出topk轴无序且选择应可复现；其他边界要求以冻结manifest/workload及用户明确要求为准。

目标分支manifest还含两个Prefill case；本次用户明确提供的是Decode b1，不能把本case通过描述为整个TopKSelect所有case已通过。后续共享路径改动需检查受影响范围，不擅自删改公共case。页面dtype的点号不表示张量无dtype，实际类型以上述manifest为准。

## 截图及网页列位核对

用户截图和官网HTML一致，三个数位于Alternatives/ms：

| baseline | ms | μs |
| --- | ---: | ---: |
| ops-math | 0.0437 | 43.7 |
| ops-transformer | 0.8124 | 812.4 |
| sgl-kernel-npu | 2.7534 | 2753.4 |

不是TFLOP/s。页面TileOPs Device time为破折号、Ratio为NaN，说明该页面没有可据此计算的有效ours耗时/倍率，不表示算子运行结果NaN。页面：https://yyttt6.github.io/TileOPs.github.io/benchmarks/attention/#topkselectfwd 。

用户个人目标仍是1.0xAscend C。页面最快列出的alternative为ops-math；若使用该行作为目标参考，1.0x对应43.7μs，倍率=43.7μs/正式可比TileOPs耗时。但网页只是基线快照，尚需匹配baseline版本、输入及正式协议；不能把以往约20μs的独立GE事件基线静默换成43.7μs，再宣称性能提升或已达标。当前既不能用43.7/约55的历史事件直接形成验收倍率，也不能把旧0.36x直接搬到网站。

## 与目标仓规范对齐

已读取目标分支CLAUDE.md、CONTRIBUTING.md、TopKSelect manifest/workload/Op、Ascend development及PR performance说明。正式提交从ascend950独立算子分支出发，记录基线SHA，遵循公共后端/注册接口和PR模板。当前历史实验分支与目标分支已有较大架构差异，不直接用个人main发包含全部历史提交的PR，也不在算法审计暂停期间强行合并迁移。

历史r1–r14为开发诊断：独立脚本、事件中位数与独立profile包络，不是该仓正式验收数据。保留所有原始数据和既有相对优化证据，不将其提升为正式成绩。

正式验收使用维护者公共入口、完整正确性和有效收据，计时依据原始设备记录及多kernel执行区间并集；共享宿主guard、输入保护、环境/源码/case指纹和原始样本需齐备。issue与目标分支文档对时钟政策、性能入口就绪程度等有版本差异，恢复设备实验前须以维护者确认的当前协议/环境锁和脚本为准，不修改共享环境或频率来强行适配。历史环境CANN9.3/0176ba14指纹不能仅凭同为TileLang0.1.15视为匹配。

issue列逐case工程门槛0.8，但用户目标1.0不降低；当前目标分支PR性能文档又明确未引入数值merge门槛，应记录此差异，不自行宣布0.8即完成。最终按维护者当前验收规则及用户目标分别报告。

目标workload验证选中值集合、唯一索引和padding，公开Op要求可复现选择；尚不能由页面推导低索引tie或NaN全部政策。历史实现的小索引tie/NaN全序是更具体的实现要求，重新设计前需与目标公共契约核对，未经确认不删除也不当作基线必须具备的功能。

当前状态仍为按用户要求暂停新增优化/设备试跑，继续算法审计及交付契约核对；本文件不新增服务器执行任务、不创建PR、不向issue发送评论。
