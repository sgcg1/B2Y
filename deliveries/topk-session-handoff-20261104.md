# TopKSelect会话交接：950PR同规格设备对照已完成

更新日期：2026-11-04（Asia/Shanghai）。本文件是新会话的优先入口。历史20261102交接及“正式验收环境阻塞”文档保留作历史记录；目标和当前状态以本文及最新结果为准。

> 交接后新增：用户已要求继续整体算法审查，最新结论见[整体算法与执行结构](topk-overall-algorithm-execution-audit-20261104.md)。普通路径新增源码/生成CPP和CPU验证；仍未实现新优化或新增NPU结果。以下历史状态保留。

> 最新方向更正：用户要求独立的新算法，不接受围绕旧流程微调。当前明确方案为[分块精确排序＋截断归并](topk-new-algorithm-truncated-merge-20261104.md)，已有正确性证明与30项CPU原型验证；NPU内核未实现、无新性能结果。新会话优先读此方案，上一份审查中阈值选择优先级已被取代。

> 2026-11-05新证据：[独立消费数设备探针](../experiments/topk/20261105-merge-consumption-probe-r1-090941/analysis.md)已完成，二分/显式树各96组×3次通过；scan_control编译失败是对照结果，非整轮失败。消费数无scan硬依赖已验证，实际设备排序/多批归并及性能仍待验证。本轮无需重跑。

> 当前下一步入口：[M实际设备归并r1](../diagnostics/topk-merge-execution-r1/README.md)。用户已要求继续设备验证；新候选以SIMT并行排名生成真实归并输出并按消费数推进，64项实际AST的CPU检查通过，尚无此轮设备结果。只测归并节点，不得将其耗时称为完整TopK。

> 最新实际归并r1结果：[同步诊断归档](../experiments/topk/20261105-merge-execution-r1-093046/analysis.md)。两档均被守卫拒绝执行，无设备归并正确性/耗时；下一步用[独立r2入口](../diagnostics/topk-merge-execution-r2/README.md)，保留ThreadSync守卫，不原样重跑r1。

> 最新r2结果：[实际设备归并正确但慢](../experiments/topk/20261105-merge-execution-r2-093737/analysis.md)。R128/R256分别58.458/55.391μs，仅单个节点；停止直接集成此SIMT排名路径，先验证低成本向量排序/归并能力。本轮无需重跑。用户明确后续按28核PR开发，完整性能保持原验收规格，不缩数据为7/8，不线性外推DT32核。

> 最新路线建议：[T完整键阈值选择](topk-route-selection-and-performance-budget-20261105.md)。基于M单节点55μs负面结果，停止其SIMT排名落地集成；优先验证真向量hist/收集，原生SIMD归并保留备选。条件预算不是预测，无新方案设备成绩，原验收规格和28核PR约束保持。

> 当前测试入口：[阈值关键原语r1](../diagnostics/topk-threshold-primitives-r1/README.md)。用户已授权测试：完整键、给定阈值收集和后端源码能力证据；48项实际AST CPU检查通过，尚无本轮设备结果。没有调用未确认的hist接口，也不把SIMT收集当原生压缩；完整T能力仍未闭合。

> 最新阈值原语r1结果：[正确但SIMT成本过高、发现嵌套SIMD直方图](../experiments/topk/20261105-threshold-primitives-r1-102742/analysis.md)。转换46.002μs、含转换收集67.951μs不可相加；均24组×3次通过。源码找到simd.py频数/累计hist与codegen线索，下一步核对现场签名并测真正SIMD；本轮不重跑，无完整新TopK性能。

## 我们在做什么任务

优化TileOPs的TopKSelectFwd。用户最新目标是：在**同一现有950PR环境、指定规格下，当前实现稳定优于原生ops-math TopKV2**。不再把截图43.7μs作为固定门槛，也不要求先取得server2环境才能测量。最终应对接`yyttt6/TileOPs`的`ascend950`分支，遵守其[issue #1](https://github.com/yyttt6/TileOPs/issues/1)及仓库规范。准备PR前应重新读取实际规范，不能凭本文推断全部验收细节。

指定case为`TopKSelectFwdOp::ds-v32-topk-decode-b1`：FP32 index_score `[1,1,16384,1]`；int32 starts/ends `[1,1]`，全窗口`[0,16384)`；K=2048；输出int32 indexes `[1,1,1,2048]`，无序。

ops-math是算子库，TopKV2是其中算子；GE是调用/模型执行途径。现场编译日志已确认加载`ops_math/.../ascendc/top_k_v2/top_k_v2_apt.cpp`。公开网站历史ops-math adapter未完整暴露，不能称“已复现网页43.7μs”。当前明确采用新建的**原生GE TopKV2同环境基线**。ops-math也存在其他Top-K相关算子，不能通过“只有一个同类算子”的错误排除法认定历史入口。

用户此前因溢出约20倍差距，要求暂停细节优化、先审计算法。该暂停没有被本轮测量授权自动取消。本轮只新增测量工具和分析，未新增内核优化、未创建PR。

## 已经完成了什么

历史A0/A1/A2与decode r1–r14的工具、结果及失败记录已归档。本轮不必重做历史实验。缓存、执行粒度等多轮实验中保留的通用实验组合是**r12 / `5eb130eff798e06341d67fd6899f67a9f66ffb20`**；r13粗桶缓存与r14窗口预计算存在分布权衡，未替代该通用起点。

本轮完成950PR同规格设备对照，入口为[diagnostics/topk-950pr-device-compare-r1/README.md](../diagnostics/topk-950pr-device-compare-r1/README.md)。从Git读取固定5eb130ef两个内核模块到私有目录，不要求服务器回退checkout。配置如下：

- hist：`decode_histogram(16384,4,STAGE_INPUT=True)`。
- prepare：`decode_prepare(4,2048,GROUPED_OFFSETS=True)`。
- compact：`decode_compact(4,STAGE_INPUT=True)`，扫描宽度128。
- finish：`decode_finish(ADAPTIVE_TIE=True,EARLY_EXIT=True,STAGE_OVERFLOW=True,CACHE_OVERFLOW_KEYS=True)`。
- 不启用FUSE_QUOTA、SKIP_INDEX_PREFIX、CACHE_OVERFLOW_COARSE、WINDOW_PRECOMPUTE。这是保留实验组合，不能称公开目标仓的默认实现。

原生比较项：GE静态TopKV2，largest=true、sorted=false、dim=-1、indices=int32、sort_policy=0、must_keep_origin_dtype；输入仅做零拷贝视图，原生额外values输出已计入并披露。双方复用同一分数张量。

计时参考目标仓固定快照的原始设备记录方法，明确命名为`950PR-development-isolated-device-task-sum-v1`：每侧3次预热；每次调用前在窗口外执行1GiB int32驱逐并同步；每窗口一次完整调用；每侧15次，三个独立Python进程，交替先后顺序。按逻辑任务合并AIC/AIV角色后求任务跨度之和，包含额外AICPU，不使用Event或总包络替代。四kernel之间的主机发射空隙不在该设备任务和中。

用户最后上传了三组各4片及manifest。全部校验、无损还原成功；1107份嵌入证据SHA验证，90个窗口逐一离线重放与服务器汇总一致；三轮计时前后正确性检查通过，同输入SHA一致。结果如下，单位μs，每格为15次算术平均：

| 轮次 | 当前保留实现 | 原生GE TopKV2 | TopKV2耗时/我们耗时 |
|---|---:|---:|---:|
| 1 | 57.7244 | 10.5376 | 0.1826x |
| 2 | 57.4222 | 10.7675 | 0.1875x |
| 3 | 57.7704 | 10.6127 | 0.1837x |
| 合并45次/侧 | **57.6390** | **10.6392** | **0.1846x** |

我们的耗时是TopKV2的5.4176倍。若固定本轮基线，到1.0x需降低当前延迟约81.54%。双方45样本范围分别56.527–59.200μs、10.006–11.309μs，差距远大于本轮波动。

四阶段均值为hist 11.210μs、prepare 5.152μs、compact 14.502μs、finish 26.774μs。finish占46.45%；其他三段合计30.865μs，已为TopKV2全调用的约2.90倍。即使finish免费也不达标，因此不能只优化finish。不能把阶段耗时全部说成启动开销，也不能承诺简单融合就够。

这是普通随机非溢出输入：seed3360520785，NPU torch.randn；输入SHA `23d29e94a909789eac603a61bd3f8b4c1fa5a9d701de237471ae9ad4792eb5ce`；meta `[188,1744,894,16384]`，边界桶894<2048，走候选缓存路径。不能把本轮5.42倍直接当成溢出测试结果。

已推送B2Y结果提交`e367e52d57499dcbbfb9b7f3720ea6bd86eca35d`。主要证据：

- [完整分析](../experiments/topk/20261104-950pr-device-compare-r1-113714/analysis.md)。
- 同目录`metadata.json`记录来源、文件SHA与限制；`replay-summary.json`是90窗口重新解析的派生汇总。
- `raw/`保存三份还原JSON；`transport/`保存manifest与12片；`AAA_Results/`是上传收件箱，不作长期唯一归档。
- [溢出算法审计](topk-overflow-algorithm-audit-20261104.md)已指出候选容量断崖、单核重扫、热点直方图原子和多轮依赖等结构问题；其历史Event/包络数字只按原口径引用。

## 当前卡在哪

**没有传输或运行阻塞，本轮已成功完成，无需原样重跑。** 当前阻塞是性能目标未达：普通随机路径只有0.1846x TopKV2，不能包装成“已基本接近目标”。

算法上：候选容量2048把相邻输入切到成本悬殊的路线；溢出后finish转为单block反复扫描全行，计数热点与多轮VF依赖可能限制向量吞吐；候选收缩后扫描域不随之收缩。本轮又证明非溢出也有整体多阶段成本问题。上述结构事实已有源码/记录支持，但没有硬件计数可以精确分摊每个机制的损失，不能把推测写成已证实的物理指令或访存耗时。

尚未完成：新的整体算法设计与选择、同环境同计时协议下的优化后对照、溢出场景迁移到本轮新口径的测试、目标仓接口/PR接入。尚未提交上游PR。

环境边界仍在：不能使用server2 canonical环境；现有结果是用户授权的950PR开发比较，不是正式server2成绩。网页历史adapter仍未知，但不妨碍以明确GE TopKV2入口建立新基线。

## 下一步计划是什么

1. 新会话先读本文、最新完整结果、溢出算法审计及目标仓规范，确认新目标和测量口径。不要重新询问用户是否允许950PR测量，也不要再次以server2差异阻止当前任务。
2. 继续**算法审计/方案设计**，先对照实际TopKV2调用、公开对应源码和我们的hist→prepare→compact→finish。区分目标case普通路径与退化分布；考虑边界规模B、剩余q、窗口长度和重复度，而非只看K或2048缓存容量。
3. 给出可审查的整体方案与成本模型：包括压缩后缩小工作集、并行计数/局部选择再合并、向量直方图/排序能力、减少跨kernel中间结果与重复扫描等候选。这里只是待评估方向，未决定采用哪个，也未证明更快。不要继续堆缓存开关代替算法选择。
4. 由用户的新指示明确恢复实现/设备实验后，再做最小内核改动。不得把本次“写交接”视为恢复优化授权。必要正确性覆盖包括稳定tie、NaN/±0、短/空/偏移窗口、容量边界和分布退化，避免改算法时只通过随机数据。
5. 后续性能必须与同环境原生TopKV2配对，保持当前输入/计时/证据保留；先重现当前起点再比较候选，若代码未变则不为恢复上下文重跑已完成基准。需要改变计时口径时新命名、说明原因，不能与旧数据直接串接。
6. 满足性能与正确性后，按目标仓实际规范组织PR；目标是`yyttt6/TileOPs`的`ascend950`，个人fork用于开发同步，B2Y用于辅助工具与结果。PR提交/合并状态必须实际核验。

## 有哪些踩过的坑，绝对不要再踩

- **仓库混淆**：B2Y在GitCode，不是GitHub。TileOPs origin是个人fork `sgcg1/TileOPs`；真正验收/最终PR目标是`yyttt6/TileOPs`，不能默认推去别的TileOPs源仓。每次推送核验remote和分支。
- **目标过期**：不以截图43.7μs为固定门槛，不把server2不匹配当作本轮测量阻塞；同样不能把950PR结果冒称正式server2验收。
- **比值颠倒/口径混用**：用户要“基线时间/我们时间”。耗时两倍写0.5x；本轮0.1846x意味着我们慢5.42倍。历史0.3–0.4x来自不同输入/计时流程，不能直接说现在内核回退一半。禁止混用Event、任务和、设备包络或墙钟。
- **假设原生唯一入口**：TopKV2属于ops-math，但不是只有它功能类似。当前GE路径已现场核实；历史网页adapter未核实，不得补造。
- **临时目录过长**：首轮GE初始化报`AF_UNIX path too long`，外层EC0009“资源不足”是包装，不能误诊显存不足。TMPDIR/TMP/TEMP现改用独立700权限`/tmp/tk-随机值`，并在导入NPU运行时前做Manager实测预检。不要恢复长工作目录下的TMPDIR或改全局环境。
- **注册信息当执行**：第二轮解析器把每窗口重复出现的GE unaging模型注册当作必须计时的任务。现仅针对已观察到的unaging且字段v[4]=109、同时无aging启动及任何设备执行记录的任务登记inactive；若实际启动/执行仍必须计入。不要删TopKV2名字或取消coverage守卫来“通过”。实际45个TopKV2窗口都计入了一个原生设备任务。
- **弱化校验**：原始布局、任务数、名字或覆盖异常时保留日志并停止；不能静默退回Event、只取可解析部分或忽略AICPU。现有10项CPU检查中包含本次失败原始二进制回放；CPU通过不代表设备已验证。
- **共享卡干扰**：仅用卡0，不重置/杀进程/改频率，不碰其他人的任务。npu-guard是外部预约工具，不是TopKV2依赖；本轮私人flock+进程检查不等于全宿主独占认证。不要要求用户安装它才能继续当前开发比较。
- **反复折腾环境**：不SSH、重建Docker、换Conda、改共享CANN或工具链。只能现有yjl容器。出现报错先读原始证据，不让用户无目的重复运行。
- **传输约定**：用户设备隔离，只能经B2Y。所有要用户执行的新命令必须先写入B2Y指南/脚本并成功推送，再给链接；聊天不能是唯一命令来源。不要要求另发网盘/附件。分片为gzip+Base64，不可阅读是正常编码，不是乱码；上传manifest与全部分片才能直接校验还原。原JSON仍保留。
- **档案与文件破坏**：每次回传独立归档（包括失败），不覆盖旧结果，不把最新收件箱当历史档案。raw和transport用`-text`保留字节，否则Windows autocrlf会使已记录SHA与Git对象不符。派生摘要必须注明来源。不要提交用户无关文件或清理其工作区。
- **Git网络判断**：此前代理下TLS push/web上传都曾失败，取消代理后DNS也失败；分片一度无效，后来手动上传成功，不能把“拆分必然解决TLS”或“永远无用”当事实。push报错后核对远端SHA，`Everything up-to-date`不能单独证明成功。非快进先fetch/整合，禁止强推覆盖。不要把令牌写进脚本、URL、日志或仓库；本文不保存任何凭据。

## 写给一个完全没有上下文的新会话

你接手的是一个**已经拿到完整同环境设备数据、但性能未达标**的TopK实现审计任务。请先读结果再决定行动。用户偏好：先检查错误前提、逻辑跳跃与缺失信息；独立判断、不迎合；数据与人物/结论尽量核实来源；有误直接指出依据和风险；提醒遗漏变量、成本和认知偏差。沟通中文，简明解释动作与证据；不要把新会话当作授权清零反复征求已确认事项。

本地Windows工作区：

| 项目 | 路径 / remote | 当前已核验状态 |
|---|---|---|
| TileOPs开发checkout | `D:\04_Project\TileOPs` | main HEAD `928b34fd2b36c3c1c29eafed87bb8dbf43d342d2`，不是本轮固定内核版本 |
| TileOPs个人fork origin | https://github.com/sgcg1/TileOPs.git | 开发同步，不是最终验收目标 |
| TileOPs目标upstream | https://github.com/yyttt6/TileOPs.git | 已抓取ascend950 ref `f0072a85a3ce1a4bcc520ba12cd09a0337871131`；新会话应检查是否更新 |
| B2Y辅助材料checkout | `D:\04_Project\B2Y` | origin https://gitcode.com/JotaroSSR/B2Y.git ，main；本交接前结果提交e367e52 |

B2Y不在TileOPs默认可写根目录时，使用环境提供的正常提权审批执行授权读写/推送；不要因此改到错误仓库。禁止绕过实际拒绝或保护规则。

服务器既有路径：容器yjl，私人目录`/home/y00937463`；源码`/home/y00937463/TileOPs`，辅助仓`/home/y00937463/B2Y`；Python `/usr/local/python3.12.14/bin/python3`；CANN通过现有`ASCEND_HOME_PATH`加载（现场`/usr/local/Ascend/cann-current`，对应9.3）；950PR_9579。无直接设备工具连接，本地Windows不能执行NPU测量；用户执行B2Y发布脚本并上传结果。不要编造自己已在NPU测试。

本轮现场运行ID `topk-950pr-device-compare-r1-20261104-113714-178290`，三轮私有目录在该目录下repeat-1/2/3；原始现场目录仍应保留。用户最后上传已完成，不欠manifest或分片，不要再次索要。

当前本地需保留的无关改动：TileOPs未跟踪`docs/design/topk-select-session-handoff-20261102.md`；B2Y修改过`deliveries/topk-handoff-20261102.md`，未跟踪`.idea/`、`main.py`及若干`__pycache__/`。本会话没有把它们提交或清理，不要使用git add .、reset --hard或clean。实际状态应进入新会话后重新检查。

建议新会话首个反馈：说明已掌握“57.639μs vs 10.639μs、0.1846x、普通非溢出也慢5.42倍”的事实，接下来优先整体算法审计，等待用户下一条工作指示；不要直接重新运行现有测量，也不要自行继续r15缓存微调。关键文件按顺序读：本文→最新analysis/metadata/replay-summary→溢出算法审计→目标仓规范→两份固定内核源码及当前测量工具。其他历史档案按需追溯即可。
