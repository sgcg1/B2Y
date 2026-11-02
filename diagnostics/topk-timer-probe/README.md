# 最小设备计时探针：20261102-probe2

当前下一步：在独立新目录运行probe2，验证源码后处理插桩、计数器单位和观察开销。它不修改TopK、不接受最终v0.1.4，也不直接给出TopK各阶段耗时。服务器只需更新B2Y，不需更新TileOPs或重跑14项。

## 为什么替换probe1

回传源码SHA为0c3c1d405730f844ed6ea28a96f9cdbe769f2b98d37a0e92bd4bbb5d97220b91。实际entry第40～46行顺序为：初始化VF → 开始计数器 → 工作VF → 屏障 → 结束计数器 → 屏障 → 输出VF。第一个屏障不在开始读取之前，旧检查器此次没有误报。这只证明生成C++不符合预期边界，不能据此证明最终指令或硬件同步行为。

probe2先让主仓生成普通VF负载，再用register_ascend_postproc_callback，在TileLang调度完成后，对唯一标记的Vector入口严格后处理。begin/end辅助调用分别包围工作区间，每次内部固定“完成屏障 → 计数器读取 → 记录”。这样避开先前在TileLang生成流程中观察到的移动；具体责任pass尚未定位，CANN编译后的行为仍需探针验证。

probe1失败和源码回传保存在[实验档案](../../experiments/topk/README.md)。旧目录不删除；历史只读导出见[INSPECT_SOURCE.md](INSPECT_SOURCE.md)，该指南不用于判断probe2。

## 1. 更新B2Y

在已有yjl容器内，沿用此前成功的Python/CANN环境，确认获准物理卡0无竞争任务。工作区干净后更新：

```bash
git -C /home/y00937463/B2Y status --short
```

```bash
git -C /home/y00937463/B2Y pull --ff-only origin main
```

不升级torch/CANN、不重建容器。若当前构建缺少主仓后处理接口，工具在postprocessor_registration阶段停止，回传摘要即可。

## 2. 在新目录执行

```bash
TOPK_TIMER_RUN="/home/y00937463/runs/timer-probe2-$(date +%Y%m%d-%H%M%S)"
timeout --kill-after=10s 900s "${TOPK_PYTHON:-python3}" \
  /home/y00937463/B2Y/diagnostics/topk-timer-probe/probe.py \
  --device 0 --output "$TOPK_TIMER_RUN"
```

不能复用probe1目录。设备号按实际获准物理卡调整，进程内映射npu:0。工具只写私人目录，独立cache/tmp/logs只在子进程中设置，不改HOME、父终端EVIDENCE或旧实验。首次编译10种配置可能需要几分钟，PROBE_COMPILE显示当前名称。

## 3. 回传一份文本

完成或正常Python报错后：

```bash
cat "$TOPK_TIMER_RUN/probe-summary.txt"
```

将全部文本复制回来或提交B2Y收件文件。强制终止导致文件未生成时，复制最后一个PROBE_COMPILE/PROBE_SAMPLE及其后错误。原始样本在probe-report.json，每次回传按独立ID归档。

每种配置保存后处理前的*-original.cpp、回调返回给编译的*-postproc.cpp、get_kernel_source接口返回的*.cpp，以及各自SHA。接口可能处于不同捕获点，是否与后处理源码相同会记录。要求回调实际执行，未观察到时拒绝缓存命中，不继续测量。

## 测量设计与限制

单worker、H128、4096个FP32数驻留UB。加载输入，重复进行有数据依赖的加1，最终写回；逐元素检查结果和输入未修改。

| 配置 | 工作量和插桩 |
| --- | --- |
| r1/r16/r64-plain | 无测量屏障或计数器 |
| r1/r16/r64-fenced | 加载与最终输出之间，用屏障包围工作VF |
| r1/r16/r64-timed | 相同边界，用屏障与计数器包围工作VF |
| r0-timed | 无工作VF，空计数区间放在输出之后，仅参考观察成本 |

每种预热5次，同进程交替正反序采50次。事件包含整个调用、初始化、写回及调度；counter只覆盖中间VF与观察成本。全部配置在事件外回读同样的时间戳缓冲。plain/fenced保留相同ticks参数ABI，但不写入测量时间戳。

TIR中仅用无效ABI锚点保留ticks参数，后处理时移除。每种模式带独立源码标记区分缓存。入口、VF布局/数量、输入输出及注入边界均严格检查，未知形态不猜测、不放宽。回调仅在独立Python进程注册，不影响其他进程或公共编译器。

status=completed只指采集完成；stage_profiling_accepted始终false。先看输出正确、时间戳递增、区间能否容纳于完整事件、随工作量增长关系，再审阅源码和观察扰动。还需验证完成语义和真实TopK依赖。

950文档值为1000 ticks/μs，与Aicore curFreq=1650MHz无关。用64轮减16轮的counter/事件中位数差检查尺度；10%窗口只是诊断启发式，不自动调整倍率。屏障/计数器引入的事件变化和所有原始数值保留，不把负变化截为0，也不机械扣除空区间。

空区间可能经历不同VF融合/调度，counter和事件差分只是辅助信息，不能视为原始阶段真实成本。源代码顺序正确仍不等于最终指令或硬件完成语义正确。本地只有CPU与静态回归，没有NPU运行结果。

参考：[主仓后处理接口](https://github.com/tile-ai/tilelang/blob/main/tilelang/ascend/callback.py)、[CANN GetSystemCycle及950换算](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSystemCycle_ISASI.md)。
