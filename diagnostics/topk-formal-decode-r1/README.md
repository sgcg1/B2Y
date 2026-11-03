# 正式Decode基线与四kernel设备时间拆解

本轮只测量，不改优化实现。固定c022114c的r3 P4容量路由、冻结7247ad4f旧TileLang基线及官方CANN TopKV2。目标是获得同轮xAscend C，并定位hist/prepare/compact/finish及阶段间隙；不再从旧9.2275μs纯kernel与新事件混算倍率。

现有GE build.cpp/proto复用自topk-950pr/cann，内容按LF保存、属性不改：FP32输入、INT32索引、largest=true、sorted=false、sort_policy=0、dim=-1，must_keep_origin_dtype。每独立进程在私人新目录构建静态[1,16384]/K2048 OM，记录源文件、命令、SOC、模型大小/SHA及ACL实际I/O描述。不是自写Ascend C基线，也不用INT64+Cast旧路线。

## 已有环境与执行

使用现有yjl容器、已加载CANN、/usr/local/python3.12.14/bin/python3，私人/home/y00937463。不更新安装、修改驱动/频率或停止共享任务。先确认卡0可用。GE SOC默认沿用已确认Ascend950PR_9579，可用现有TOPK_SOC覆盖，实际值入报告。CXX11 ABI沿用原工具默认0或已有TOPK_CXX11_ABI。

若在宿主机，先进入容器；已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内更新两仓，失败停止，不重置本地修改、不在实验中途pull：

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only
```

确认已有CANN环境加载后运行：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r1/run.sh
```

ASCII终端提示。UPLOAD_RESULT和UPLOAD_LOG是待上传路径，FAILED为失败停止，COLLECTION_COMPLETE只是采集结束。此次包含GE构建和多次独立profile，耗时会比只测事件的筛选更长。

## 同轮事件口径

两个独立进程，新cache/tmp/logs。三个被测实现使用同一预分配输入地址、同一torch NPU流及同类torch NPU事件。CANN调用aclmdlExecuteAsync，返回values和indices；r3返回indices，这是已接受的核心基线功能差异，不隐瞒CANN多输出成本。默认旧TileLang作为桥接对照。

固定全窗、有限FP32、G1、N16384/K2048。四输入为两个随机seed、全同分、小边界同分；每版本50事件，六种顺序轮换，两进程共1200事件。编译/GE加载、生成、哈希、H2D、分配、校验及warmup在定时外；r3事件包含完整四kernel和host提交造成的间隙，不根据D2H结果选路径。

TileLang核对严格小索引tie集合及quota/committed；CANN不被强加未承诺的稳定tie，改核对索引范围/唯一性、FP32 gather一致以及完整top-score多重集合。全同分时CANN可返回不同合法索引集合，不能因此放宽TileLang契约。基线比较不包含NaN或局部窗口，其契约已在此前筛选另测，本次不外推到全功能一致。

事件倍数：CANN事件中位数/候选完整调用事件中位数，标记event xAscend C。

## 独立profiler与拆解

事件采样后，每输入、每实现分别启用一个新profile；无事件计时、分配、RNG或正确性检查混入。预热区后发60次调用并按设备时间固定取最后50个完整调用，不挑最快值。每进程12个profile，两进程24个。

单kernel基线/CANN要求每调用1条kernel_details记录；r3要求4条、同顺序、无重叠，Block Num若存在须为4/1/4/1。task_time底层计算记录必须完整且不能有AICPU。意外多流、额外任务名、部分流水或缺样会拒绝输出设备倍率，保留原始文件供分析，不放宽断言硬凑50次。

每次r3分别保存四段duration、三个gap、四段和及首kernel开始到末kernel结束的envelope。先按同次计算再取中位数，不把各段中位数相加当一次运行。设备包络倍数：CANN单kernel设备中位数/r3四kernel设备包络中位数；另报告sum_kernel和gap，不把sum_kernel冒充包络。这里的包络不含首kernel之前的提交/调度及末kernel后的返回成本。

profiler会扰动执行，尤其可能放大host提交间隙；profile包络与无profile事件分开报告，不机械相减，不把profile内gap认定为无扰动launch成本。未采最终汇编、带宽或逐指令数据，不直接宣称某项微架构瓶颈。

## 本地检查与证据

6项CPU解析回归通过：大时间戳精度、四kernel同次分组、固定尾部选择、缺样/重叠/多流拒绝、block顺序拒绝，以及sum-of-medians陷阱。离线源码/工具身份和GE关键属性检查、Python/Bash语法通过。尚未在设备执行本工具，不宣称正式倍率已有结论。

冻结生成SHA核对r3五个程序与原实测身份，编译前原样捕获C++，ThreadSync诊断拒绝进入计时。原始kernel_details.csv、task_time.csv完整文本、大小/SHA随返回文件保存，采集失败也返回现有文件；profile原目录及Chrome trace留在私人输出目录，必要时再取，不先要求额外打包。

## 回传

目录/home/y00937463/topk-formal-decode-r1-时间-进程号。脚本复制formal-return.txt及日志到B2Y/AAA_Results并打印路径，直接按[现有指南](../../AAA_Results/README.md)上传。成功失败均回传，首次失败不启动第二进程；没有return时上传日志。不建额外上传层级或校验清单，不重跑旧筛选。

本轮测量通过也不等于完整14项通用契约或默认接受。结果将用于选定一个高收益改造方向，而非同时叠加更多缓存/分片/worker参数。
