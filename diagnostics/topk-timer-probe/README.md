# 最小设备计时探针：20261102-probe1

目的：先验证当前TileLang/CANN能否编译并使用设备计数器，以及完成屏障和时间戳对执行时间的影响。此工具不修改TopK内核，不直接给出TopK各阶段耗时，也不接受最终v0.1.4。主体通过主仓 `target="ascend"` 编译；prelude只提供计数器和屏障辅助函数。

本地只有CPU和静态检查能力。尚未在你的SDK运行；编译失败、计数异常或检查不一致时停在探针阶段，不升级torch/CANN、不改变设备频率、不进入正式阶段插桩。

## 当前失败的下一步

若已遇到Counter/fence source order changed，先按 [只读源码检查指南](INSPECT_SOURCE.md) 导出原失败目录的r1-timed.cpp及标记位置，不要重跑探针或删除断言。源码未回传前，不能确认编译器重排或检查器误报。

## 1. 环境与更新

使用已有Docker容器yjl，以及此前跑通TopK的Python/CANN环境。宿主机进入容器，已经在容器内则跳过：

```bash
docker exec -it yjl /bin/bash
```

在容器内确认B2Y工作区干净，且物理卡0仍获分配、无竞争任务后，再更新B2Y：

```bash
git -C /home/y00937463/B2Y status --short
```

```bash
git -C /home/y00937463/B2Y pull --ff-only origin main
```

本次新增目录为B2Y的 `diagnostics/topk-timer-probe/`，不修改已有 `topk-950pr/` 工具或其MANIFEST。服务器TileOPs不需要更新，不需要重跑14项测试，不需要重建容器或使用Conda。

## 2. 执行探针

以下在容器内、已加载实际CANN toolkit环境的终端执行：

```bash
TOPK_TIMER_RUN="/home/y00937463/runs/timer-probe-$(date +%Y%m%d-%H%M%S)"
timeout --kill-after=10s 900s "${TOPK_PYTHON:-python3}" \
  /home/y00937463/B2Y/diagnostics/topk-timer-probe/probe.py \
  --device 0 --output "$TOPK_TIMER_RUN"
```

设备号按获准物理卡调整，子进程内映射为npu:0。输出目录必须不存在；工具只允许在 `/home/y00937463` 内新建目录。它在自己的子进程内配置独立cache/tmp/logs，不修改HOME、父终端EVIDENCE、现有实验或共享安装。

首次编译10种小型配置可能需要几分钟；PROBE_COMPILE会打印配置名称。超时或编译错误时停止，保留该目录和终端首个错误，不反复延长超时。正常Python异常会写出错误摘要；外部强制终止时文件可能尚未生成。

## 3. 复制一份文本回来

执行结束后：

```bash
cat "$TOPK_TIMER_RUN/probe-summary.txt"
```

直接复制全部文本回来即可。失败时也可复制此文件；若文件不存在，复制最后一个PROBE_COMPILE/PROBE_SAMPLE及其后错误。原始样本在probe-report.json，生成源码在各配置的.cpp，均留在私人目录供后续定位。

## 测了什么

单worker、H128、4096个FP32数，先将输入读入UB，反复进行相互依赖的 `values += 1`，最后写回输出。输入为CPU生成的精确整数，结果逐元素等于输入加重复次数，同时检查输入未被修改。

| 配置 | 含义 |
| --- | --- |
| r1/r16/r64-plain | 原工作负载，无额外屏障/计数器 |
| r1/r16/r64-fenced | 工作区间前后增加PIPE_ALL完成屏障 |
| r1/r16/r64-timed | 相同屏障，加起止系统计数器读取和记录 |
| r0-timed | 同样加载/写回数据，但计时区间没有VF工作，估计空区间观测成本 |

每种预热5次；随后在同进程交替正反序采集50次。NPU事件覆盖整个调用，包含初始化、最终写回与调度；系统计数器区间只覆盖中间VF工作和观测成本，两列不能要求绝对相等。时间戳缓冲预填-1及回读位于事件区间之外，各配置做相同的回读。

## 如何判读

- status=completed仅表示采集与数值计算完成，始终保留stage_profiling_accepted=false。它不表示当前TopK阶段计时已经可靠。
- outputs_equal_reference必须为true；all_counter_intervals_positive、counter_medians_increase_with_work应为true。
- CANN对950的文档换算为1000 ticks/μs。使用64次与16次工作量的中位数差，比较counter差与NPU事件差，减少固定初始化/调度成本影响。rate_within_10_percent_of_documentation只是显式10%诊断窗口，不是硬件认证标准，不自动调整换算倍率；明显不符时继续定位。
- r*-changes给出加入屏障、再加入计数器后的事件耗时变化百分比。允许出现负值，不能强行截成0；变化可能包含噪声或编译调度变化，不能直接解释为某条指令的精确成本。
- 同时报告r1/r16/r64相对空区间的counter差与事件差，尤其检查单次VF是否因未完成而被漏计。差分仍受编译和观测成本影响，不能单独证明完成语义。counter_intervals_fit_inside_events_at_documented_rate检查计数器区间是否能容纳在整个调用的事件区间内。
- 空区间值保留原值，不机械扣除。新增屏障可能改变流水；即使探针通过，真实TopK的histogram/scan/compact依赖还需验证。
- 生成源码检查确保计数器/屏障数量及源代码顺序符合预期，且非空计数区间包含VF调用，但不等于已核实最终指令顺序、完成语义或指令成本。下一步结合源码/必要时反汇编与重复测量审核，再设计TopK阶段统计。

此探针选择 `T.Kernel(prelude=...)` 与 `T.call_extern` 路线。它们在当前公开主仓有文档，但安装的0.1.15构建能否支持仍由实际编译确认；若接口不支持，回传Kernel_signature和失败阶段，再做针对性适配，不盲目升级环境。GetSystemCycle的计数域与Aicore curFreq=1650MHz字段不同。

参考：[CANN GetSystemCycle（950换算及屏障示例）](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSystemCycle_ISASI.md)、[主仓Kernel prelude接口](https://github.com/tile-ai/tilelang/blob/main/tilelang/ascend/language/kernel.py)、[主仓测量说明](https://github.com/tile-ai/tilelang/blob/main/.agents/skills/tilelang-ascend/references/profiling.md)。
