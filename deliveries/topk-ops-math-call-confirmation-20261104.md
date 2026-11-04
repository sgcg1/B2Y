# ops-math与GE TopKV2关系及真实调用核对

2026-11-04。目标仍为950PR相同环境下稳定优于原生ops-math，截图历史数值不是门槛。用户确认没有额外原始adapter仓库或脚本。

## 名称不是同一层级

- ops-math是CANN数学基础算子库，其中包含多个算子，不是单个算子。
- TopKV2是该库中的Top-K算子。TopKSelectFwdOp是TileOPs的完整公共接口，还包括窗口、索引形状和类型等契约，不能与裸TopKV2直接等同。
- GE是图执行/编译入口，不是另一个独立Top-K算法库。官方ops-math的math/top_k_v2/README明确提供test_geir_top_k_v2图模式示例：经GE构图调用该库算子。
- ACLNN是另一类API入口；math/topk目录提供aclnn接口，其具体调度/转换及最终内核要按版本和参数核对。不能只凭TopK名称把所有API都视为相同调用链。

## 已确认的真实链路

我们此前独立GE基线的构图使用ge::op::TopKV2，旧实验完整报告中的GE编译日志实际引用：

`.../opp/built-in/op_impl/ai_core/tbe/impl/ops_math/dynamic/../ascendc/top_k_v2/top_k_v2_apt.cpp`

因此，在当时CANN9.3环境，这条链路确实是“GE图入口→TopKV2→已安装ops-math TopKV2实现”。不是与ops-math无关的自写Top-K或独立替代库。支持目录保存完整GE构建日志、原报告SHA和当时OM参数；这能确认库/源码归属，不能据include链认定最终具体tiling模板或所有块的实际工作。

官方原生调用参考：[ops-math TopKV2 README](https://gitcode.com/cann/ops-math/blob/master/math/top_k_v2/README.md)、[ops-math TopK/aclnn目录](https://gitcode.com/cann/ops-math/tree/9.0.0/math/topk)。

## 尚未确认的历史网页链路

网页固定snapshot对该行只给library=ops-math、op/case/params、15样本、v2协议和measurement_id。已核查的benchmark_ascend、runner、PR/nightly流程、计时工具、网页renderer及snapshot没有提供该TopKSelect原生adapter函数体。

不能据43.7μs反推用GE、ACLNN、torch封装或哪个参数；也不能认定网站ops-math与我们的GE基线是同一个完整callable。当前只确认“库有关联”，未确认“测量入口和计时边界相同”。这是缺少可追溯材料，不是算子不存在/不支持。

此前我把“还没找到网页adapter”与“GE/ops-math可能是不同对象”混在一起表述，容易造成误解；这里明确纠正。既不能断言完全无关，也不能未核对就直接等同。

## 对下一轮比较的含义

用户不要求复现历史43.7μs，只要求950PR同环境稳定优于ops-math。因此不必强行还原不可追溯的历史数字，可以基于官方支持的原生入口建立新的、命名和调用边界明确的ops-math baseline，双方使用同一输入与设备计时器重测。

若选GE，应标记ops-math/TopKV2/GE，并冻结实现/环境指纹、sorted/indices_dtype等参数，核对其返回完整TopKSelect索引契约所需的窗口/布局/类型适配，完整设备工作一并计时。若选ACLNN，应另列对应API及转换，不能把它们混成同一个baseline。输入构造与编译准备不计入稳态，必要的每次调用设备转换不能隐去。

当前已能验证官方TopKV2图模式的库归属与可用调用路径；未确认网页原始函数，暂不宣称复现其基线。此文不新增设备测试或算法改动。后续比较以新固定入口的同环境实测为准，不再沿用历史事件倍率或截图阈值。

证据：[原GE编译日志](../analyses/topk/20261104-ops-math-call-confirmation/ge-build.log)、[出处/哈希与参数](../analyses/topk/20261104-ops-math-call-confirmation/provenance.json)。
