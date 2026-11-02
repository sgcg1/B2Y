# 完整Decode四kernel实验候选：P2/P4独立筛选

状态：TileOPs提交03c8f916已推送，独立模块不接入生产host，A0/A1/A2关闭。4项CPU测试通过：包含分块/归并及缩放后的prepare→compact→finish实际AST，覆盖P2/P4、正反遍历、特殊值、窗口、小候选/溢出回退和确定性同分集合。Python/Bash语法及离线身份通过；尚无本候选NPU编译、同步或性能结果。

## 实现与边界

固定R1/N16384/K2048/G1、FP32、H128。依次调用四个TileLang kernel：

1. 每分块私有histogram，复用已实测探针实现。
2. prepare：全局阈值及每分块accepted/boundary前缀偏移，初始化输出为16384哨兵。
3. compact：P2/P4使用独立UB游标，在互不重叠的分块区间写已确定入选索引及边界候选。边界前缀来自完整int32计数，不依赖抢位决定同分最终集合。
4. finish：单worker处理边界，先按4字节FP32规范键、再按4字节补码绝对索引做精确radix，保证同分较小索引优先；输出槽位无序。候选≤2048时装入UB，超过2048时忽略截断缓存并完整重扫原窗口的边界桶。短窗/空窗全部有效索引与哨兵由前三段处理，finish校验quota最终归零。

这是新的完整实验路径，不是此前18.87–19.05μs成本探针的改名。finish暂用固定8轮逻辑前缀过滤，不假装已经具备生产kernel的所有缓存收窄优化，可能抵消分核收益。Overflow重扫也可能很慢，因此本轮同时测全同分溢出和小边界同分分布。默认路由和Prefill不变，不声称完成原通用接口全部规格。

## 在已有环境执行

使用现有yjl容器、已加载的CANN环境与容器Python，私人路径/home/y00937463。先确认设备0可用，不重置设备、不修改公共安装或频率。

若在宿主机，先进入容器；已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内更新两仓；失败即停止，不清理本地修改，不在实验中途pull：

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only
```

确认已有CANN环境已加载后执行：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-decode-full-r1/run.sh
```

启动提示全为ASCII。UPLOAD_RESULT和UPLOAD_LOG是待上传路径，FAILED为失败并停止后续进程，COLLECTION_COMPLETE仅表示采集结束。无需调整终端编码。

## 校验、计时与回传

两个独立Python进程，全新cache/tmp/logs；冻结7247ad4f/H128为baseline，对照p2、p4。两个实现源文件、baseline与run.py均核对SHA。八个程序（基线、finish、各P的hist/prepare/compact）独立记录编译stderr，在Bisheng前保存原始C++，ThreadSync诊断出现即拒绝计时，不改安装或放宽检查。

计时前校验全部三版本选中索引集合和哨兵，P2/P4还核对最终quota/committed及窗口总计数。覆盖NaN/Inf/±0、FP16溢出边界、部分窗/短窗/空窗/反向窗、全同分、FP32极近分值、大候选溢出、小边界同分及两个随机seed。这里的校验仍不是完整14项通用契约，不覆盖其他K、G、非连续输入或Prefill。

四个计时输入为两个随机seed、全同分溢出、小边界同分。每版本各50个事件，轮换六种执行顺序；每进程600，两进程1200样本。输入输出、所有GM工作区和事件预分配，编译、哈希、H2D、校验及warmup在定时外；抽样结束再核对一次正确性。每个p2/p4事件包围全部四kernel，同一流按顺序执行，无中途D2H分支；不能把分kernel耗时相加冒充完整调用。

没有profiler设备任务/间隙记录或同轮CANN，因此只报告完整调用事件，不算正式×CANN，也不宣称正式验收。即使随机输入加速，溢出或同分回退仍需纳入接受判断。

输出/home/y00937463/topk-decode-full-r1-时间-进程号。脚本自动将full-return.txt和日志复制到B2Y/AAA_Results并打印路径，按[上传指南](../../AAA_Results/README.md)直接上传这些文件。失败同样回传，首次失败不启动第二进程；若未产return则上传日志。不生成额外清单或上传子目录，不重跑旧成本探针。
