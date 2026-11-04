# ops-math性能测量链路核对与目标更新

2026-11-04。用户最新目标：在当前950PR环境、同输入和同计时边界下，当前实现稳定优于原生ops-math。不再把截图43.7μs当固定目标；不再要求先具备canonical950DT环境才能进行这项开发比较。最终PR目标仍yyttt6/TileOPs:ascend950，公共验收资格与950PR同环境开发比较分别记录。算法优化暂停，仅做测量链路核对与后续比较准备。

## 1. 用户指定脚本负责什么

[scripts/benchmark_ascend.py](https://github.com/yyttt6/TileOPs/blob/f0072a85a3ce1a4bcc520ba12cd09a0337871131/scripts/benchmark_ascend.py)建立新输出目录，在导入NPU运行时前通过guard运行benchmarks.ascend.runner，并写最终receipt。它不直接import ops-math，也没有硬编码TopKV2或TopKSelect基线调用。

runner通过公共manifest生成case并验证完整输出/输入保护；默认测tileops，额外实现由--implementation-factory module:function返回Implementation对象。factory提供具体callable、参数和reset，不能仅写library=ops-math就认为已接入原生基线。

## 2. 当前PR流程如何对照ops-math

[scripts/ci/pr_performance.py](https://github.com/yyttt6/TileOPs/blob/f0072a85a3ce1a4bcc520ba12cd09a0337871131/scripts/ci/pr_performance.py)先运行公共正确性，再通过nightly_device测TileOPs，读取工作流固定的baseline-cache/snapshot.json，以op+case+params精确匹配原生记录，然后算baseline_us/tileops_us。它并不在每个PR中现场重新跑ops-math。

工作流固定的快照来自yyttt6/TileOPs.github.io提交b1b6bd3ac9b98bcff6cb2b085cd85532cba12411。原始TopKSelect ops-math行已提取保存在支持目录：case=ds-v32-topk-decode-b1，原值43.69473333333333μs，samples=15，protocol=ascend950-isolated-ffts-v2。截图0.0437ms是四舍五入。快照Git blob SHA及整个文件SHA已核验，不能把网页rounded数当原始样本。

快照只提供测量标识及归一化workload，没有公开该条目的实际ops-math callable、适配函数、库commit或完整调用原始trace。因此能确认来源和统计元数据，尚不能据此断言用的是aclnnTopk、torch.topk、GE静态TopKV2或其他入口；不能拿我们旧GE脚本冒充该共享适配器。网页renderer还明确限制公开记录的部分provenance字段。

## 3. 仓内存在不同版本计时路径

- 公共benchmarks/ascend/timing.py：3预热、15独立profiler session、每次reset→1GiB int32 L2 eviction→同步，准备均在窗口外；解析FFTS设备执行区间并集，取算术平均，协议ascend950-profiler-locked-v1。该直接入口要求clock-config。
- 原生测量支持tools/measure_baselines.py和baseline_protocol.py：当前标记ascend950-isolated-ffts-v3，3预热、15独立窗口、同样reset/1GiB清缓存/同步；当前kernel_task_profile按不同逻辑kernel任务的span累加，对同一任务的AIC/AIV角色去重。不把Python提交空隙计入，不用Event或wall-clock代替。
- 当前PR/nightly实际走complete_profile.make_timer，复用上述独立窗口逻辑，并审计原FFTS未覆盖的命名AICPU任务、补计其设备耗时，保留coverage/hash证据。nightly_device使用platform-default时钟，其行为与公共locked-v1直接入口不同。
- 网页截图对应的原生快照仍标记v2，不是当前v3，也不是locked-v1。不能用当前helper源码倒推出历史v2每一项实现细节，或声称所有入口都同一算法。当前PR文档也说明v2原生基线与v3 TileOPs数据分别标识。

设备区间并集与不同任务span求和也不是永远相同；跨任务重叠时会不同。我们的四kernel同流顺序执行时可更接近，但要以raw trace确认，不能直接套用首kernel到末kernel的包络（包络含空隙）。之前仅说“公共协议就是区间并集”过于简化，本核对补正实际调用差异。

## 4. 计时边界

预热前的冷启动/JIT耗时单独记录，不能作稳态成绩。输入构造、reset、L2 eviction不计入目标callable设备耗时，profiling仅括住一次调用及必要同步；最终报告15次均值并保留全部样本/离散情况，不挑最好样本。

如果原生adapter为满足公共Op契约执行mask、转置、类型转换或其他设备操作，原则上这些必须随完整adapter计入同一个窗口。若只测裸TopKV2kernel而忽略必要适配，应明确标为局部算子诊断，不能与返回完整INT32 indexes的TileLang调用直接对比。具体该ops-math条目有哪些适配工作目前未知，不猜测43.7μs与旧20μs差异由哪项造成。

## 5. 后续950PR比较应如何建立

以原生ops-math完整调用作为对手，先确认实际API和薄适配；两实现共同使用用户指定FP32[1,1,16384,1]、INT32窗口[1,1]和INT32输出[1,1,1,2048]，输入取同一份，公开完整输入/输出及同分比较政策。环境、源身份和相同计时方法全部冻结。不要分别生成不同随机数据后称“同规格公平比较”。

两侧必须通过同一正确性/输入保护，并由同一个device timer对完整调用采样。共享设备仍要检查干扰；用户放宽环境差异不等于可以与别的任务争卡或改动公共安装。优先选择当前支持的原始设备记录计时路径，并显式记录950PR/CANN9.3兼容情况，不能无检查套用CANN9.2二进制记录解析布局。必要时验证/适配解析器，不默默回退到Event。

“稳定优于”需要多轮独立复现和全部样本分布，不能只看最小值、单次均值优势或固定43.7μs。统一报告r=同轮ops-math平均设备耗时/本实现平均设备耗时，r>1才是加速；波动覆盖差值时标不确定，不擅自降低为0.8门槛。具体采样重复与轮数在比较脚本中预先固定并公开，而不是跑到赢为止。

当前完成的是代码及数据链路审计，没有新增设备性能结果，没有创建新原生baseline算法，也没有声称原生adapter已找到。下一项必须补齐真实ops-math callable，再准备950PR同环境对照；不以截图或旧GE事件替代。

支持材料：[ops-math快照行](../analyses/topk/20261104-ops-math-measurement-trace/ops-math-topkselect-cache-row.json)、[读取版本和源SHA](../analyses/topk/20261104-ops-math-measurement-trace/provenance.json)。
