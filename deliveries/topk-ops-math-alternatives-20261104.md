# 直接检查ops-math的其他Top-K同类算子

2026-11-04。直接枚举公开ops-math源码快照e287c428bf5bcdb8279b0e4764f4b7914ec66003的math目录，读取算子README、图定义及TopK API调度源码。不是根据博客或名称猜测；API/图定义下载blob已核对Git SHA，支持目录保留原文件和版本记录。该快照是公开镜像，不冒充当前服务器已安装库的逐字源码。

## 直接回答

有其他“取前K极值及索引”的同类算子，因此不能用“没有别的，所以必然TopKV2”的排除法。但对用户指定950PR、FP32、N16384、K2048的原生AiCore Top-K，所核查版本的调度证据支持TopKV2为主要底层实现；这是比名称推断更直接的依据。

| 算子/入口 | 同类功能 | 与当前规格的关系 |
| --- | --- | --- |
| TopKV2 / math/top_k_v2 | 指定维度K极值和索引，支持FP32，索引INT32/INT64 | 文档支持950PR，可作官方原生基线；有GE示例 |
| TopK / math/topk | 同样返回K极值和索引，图定义输出INT32 | 文档支持950PR与FLOAT，不是“库中不存在其他同功能算子”；通用API会按硬件分派 |
| TopKV2D / math/top_k_v2_d | 同类Top-K，额外assist_seq辅助输入 | 文档支持950PR/FLOAT，但接口不同；需要额外适配，不能说与TopKV2完全相同 |
| RadixTopK / math/radix_top_k | 同类Top-K选择 | 此版本README不支持950PR/DT，输入仅FLOAT16/BFLOAT16，不匹配本FP32 case |
| TopKV3调度名 | TopK API内存在该分支 | 所核查IsAscendCSupport只在310P、FP16、小K<16时启用，不匹配本case |

目录还包含TopKPQDistance、TopKPQDistanceV2、InplaceTopKDistance等检索专用算子；这些带专用输入/处理语义，不能仅凭TopK名称当作当前普通FP32分数选择的直接替代。

“同类功能”指核心K极值选择，不代表任何裸算子与TopKSelectFwdOp完整窗口/padding/索引输出契约逐项相同。

## 实际调度源码证据

固定快照math/topk/op_api/topk.cpp：

- IsAiCoreSupport覆盖该RegBase普通FP32情况，额外小轴回退针对INT64等条件，不是本FP32输入。
- IsAscendCSupport第148–154行只在ASCEND310P、FLOAT16、K<16返回true，决定TopKV3分支；本case不满足。
- TopkCommon第250–260行在非TopKV3且IsRegBase时调用TopkV2AiCoreForDavid；其他条件再考虑RadixTopK或TopkV2AiCore。
- TopkV2AiCoreForDavid第169–177行通过ADD_TO_LAUNCHER_LIST_AICORE(TopKV2, ...)提交TopKV2，不是另一个独立排序实现。

也就是说，名为TopK的通用入口在该硬件分支会落到TopKV2底层。API名字不同不一定表示内核不同；同样，裸GE图TopK与通用ACLNN TopK也不能未经检查视为完全相同路径。

我们的旧GE实际编译日志已证明加载安装CANN9.3的ops_math/top_k_v2实现，两条证据相互支持，但不能据公开快照调度替代对当前安装API的实际执行核验。仍要固定所选GE/ACLNN入口及其参数和完整适配成本。

## 对基线选择的结论

可以把“ops-math TopKV2”明确列为本规格的新原生基线，不必继续把GE TopKV2与ops-math当互不相关的库。理由是官方支持及调度/编译日志证据，而不是库内不存在其他同类算子。之后在950PR同环境中测该原生入口及完整适配，与TileLang同输入、同计时器比较。

不能进一步声称网页43.7μs那条历史记录已被还原：它仍缺原始adapter。用户已不要求复现历史数值，故这一缺口不应阻碍建立可审查、可追溯的新TopKV2对照。若未来发现适用于本case的另一个有效更快原生入口，应披露对照，不能只挑容易击败的版本。

参考：[官方TopKV2说明](https://gitcode.com/cann/ops-math/blob/master/math/top_k_v2/README.md)、[TopK目录](https://gitcode.com/cann/ops-math/tree/9.0.0/math/topk)、[固定版本调度源码副本](../analyses/topk/20261104-ops-math-topk-catalog/topk-op_api-topk.cpp)、[目录及定义证据](../analyses/topk/20261104-ops-math-topk-catalog/provenance.json)。本次没有设备运行或新算法修改。
