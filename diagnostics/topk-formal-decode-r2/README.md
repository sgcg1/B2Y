# prepare分组并行归约：同轮CANN与冻结r3对照

候选cd94fb34已推送。只改decode_prepare的offset计算，GROUPED_OFFSETS默认false；实验打开后按P×16分组，每任务串行16桶，结果存UB，再从UB归约到各分块前缀。P4新增声明64个int32（256字节，实际布局由后端决定）及一个VF。原来少数线程最多串行768次桶读取，改为64个分组任务并行；原子次数不增加，阈值、offset、输出哨兵定义不变。hist/compact/finish保持冻结r3。

本轮只验证这项改动，不声称它能直接达到1.0x。若其他成本不变，即使prepare/finish归零也约0.33x，后续仍要改执行粒度与向量统计。

## 执行

沿用已有yjl、已加载CANN和现有Python，私人/home/y00937463。先确认卡0可用，不改公共安装/驱动/频率。

若在宿主机，先进入容器；已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内更新两仓，失败停止，不重置用户修改、不在测量中途pull：

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only
```

确认CANN环境加载后执行：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r2/run.sh
```

ASCII提示，UPLOAD_RESULT/UPLOAD_LOG是需上传路径。COLLECTION_COMPLETE不等于验收通过，PROFILE_BOUNDARY_REVIEW_REQUIRED表示有不完整采集需复核。

## 冻结与校验

四版本：7247ad4f旧默认、c022114c冻结r3、新prepare、官方GE TopKV2。同一输入地址/同一流/预分配工作区；新旧流水使用独立输出及workspace，没有D2H路由。冻结r3的prepare单独加载，当前模块关闭GROUPED_OFFSETS的control必须生成相同C++。其余四个程序（baseline/hist/compact/finish）核对上一正式回传SHA；工具及GE构建源文件全部核对身份。

本地6项内核CPU测试通过：缩放实际流水AST覆盖两种prepare/三种尾段/P2-P4/遍历顺序/特殊值/窗口/容量边界，另有实际K2048的offset oracle、关闭开关模块AST一致性及分块归并检查。设备端先核对严格TileLang集合、quota及总计数；CANN按合法唯一索引、FP32 gather和top-score多重集合校验，不冒称稳定tie。本轮基线比较仍限定全窗有限FP32、N16384/K2048/G1，非完整14项通用契约。

## 事件与设备拆解

两个独立进程，全新cache/tmp/logs。四输入：两个随机seed、全同分溢出、小边界同分。每版本50事件，轮换24种顺序，每进程800、两进程1600。编译、GE加载、生成/哈希、H2D、校验、分配及warmup在定时外。事件倍率为CANN/候选完整调用；r3和new各含四kernel。

每输入每版本独立profile，共两进程32个profile，各发60调用，固定取最后50完整调用。保留原始kernel_details.csv与task_time.csv，核对计算任务、单流、无重叠、r3/new的Block Num 4/1/4/1。逐次计算各段、gap、kernel和及首尾包络再取中位数。设备包络倍率与事件倍率分开，不将各段中位数相加冒充一次运行，不混用旧基线。

首版曾丢失首个hist，239条记录开头1/4/1、末尾完整。本版显式验证首部最多3条残段与后续完整Block模式，原始残段仍返回，只取固定最后200条进行诊断。出现此情形不停止收集后续CANN，但该输入设备倍率写入provisional_device_x_ascend_c并标记review_required_partial_capture，整体completed_with_profile_review；不冒称完整正式复现。仅凭block模式不能排除所有内部丢失或同周期错位，需原始记录复核。尾部残缺、无Block列无法对齐、重叠/多流/缺样等仍拒绝。

profiler可能扰动gap，设备包络不含首kernel前的模型调度或最后kernel后的返回，不能和无profile事件机械相减分摊launch成本。未测最终指令/带宽，不把阶段收益直接写成微架构因果。

8项CPU解析测试通过：原6项加首部残段保留及尾部残段拒绝；身份/GE属性和Python/Bash语法通过。尚无新prepare的NPU编译/同步/性能结果，默认关闭。ThreadSync诊断拒绝计时，Bisheng前捕获原始C++。

## 回传

私人输出/home/y00937463/topk-formal-decode-r2-时间-进程号。脚本复制formal-return.txt和日志到B2Y/AAA_Results并打印路径，按[现有上传指南](../../AAA_Results/README.md)直接上传，失败或completed_with_profile_review也回传。首次异常失败不启动第二进程，若无return则上传日志。无需新目录、校验清单或重跑旧工具。此测量包含GE构建及32个profile，耗时长于事件筛选。
