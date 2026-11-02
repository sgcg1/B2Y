# Decode首轮P1/P2/P4直方图与归并成本验证

状态：TileOPs提交72a84811已推送，新增独立实验模块，不改生产host或默认kernel。A0/A1/A2保持关闭。本地2项CPU检查覆盖分块完整无重复、与生产一致的coarse_byte AST、实际归并AST与独立计数oracle；另有Python/Bash语法及离线身份检查。尚无设备编译或性能结果。

## 这次验证什么

固定Decode N16384/K2048/G1、H128，P=1/2/4。第一个kernel每worker处理连续N/P条，产生私有256桶int32直方图并写GM；第二个kernel精确合并P份计数，分组前缀扫描，输出各桶严格更高计数及[threshold, accepted_above, boundary_count, total]。NaN、±0和FP16粗键定义与原实现一致。

这不是完整TopK，也不是原生产首轮的等价计时。没有compact、最终索引、候选读取/精确后续轮次。GM partial/higher/meta均预分配。原生产直方图只留UB，本工具要写GM，P1也有额外成本；不能将P1事件直接等同历史55.983μs counter阶段。元数据逻辑不依赖原子抢位决定同分最终集合。

目标先判断：分块直方图能否加速；加上第二次launch、GM通信与阈值归并后是否还有净空间。即使双kernel包络变快，也不能宣布完整TopK收益。若没有空间，先分析或停止，不投入完整多kernel流水；若有空间，下一步才做compact与精确后续，并重新量完整调用。

## 已有容器环境

沿用yjl及已加载CANN、现有Python；只写/home/y00937463私人路径。先确认卡0可用，不修改频率、驱动或公共安装。

若在宿主机，先进入容器；已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内更新两仓，失败即停止；不清理本地修改、不在实验中途pull：

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only
```

确认已有CANN环境已加载后运行：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-decode-pilot-r1/run-ascii.sh
```

## 测量与检查

两个独立Python进程，新cache/tmp/logs。每进程编译六个程序（hist与merge各P1/P2/P4），只读回调在Bisheng前保存C++，逐配置捕获原生stderr；ThreadSync诊断出现即停止计时。工具校验源码与脚本SHA，不修改编译器。

先逐分块核对256桶计数、全局higher与四项metadata；分布包括全同分、NaN/Inf/±0和FP16溢出边界，窗口含全窗、部分窗、短窗、空及反向。两个随机seed的实际输入SHA保存，随机输入在NPU生成后以原字节回传CPU建立oracle；校验在计时外。

六个测量配置为hist-p1/p2/p4与pipeline-p1/p2/p4。hist只发第一kernel；pipeline在同一流依次发hist和merge，开始/结束事件包围整个两kernel调用，不把两次单kernel耗时相加冒充墙钟。各seed每配置50个事件，轮换起始位置和正反次序，共每进程600、两进程1200样本。编译、生成/传输、哈希、校验、预分配及warmup均在定时外。事件同步读取在end记录之后。没有profiler纯kernel记录，也没有同轮CANN，不能计算×CANN或声称完成正式性能验收。

所有输出以完整计数和CPU oracle核对，不截断桶。metadata阈值沿用原算法before<=K<through，恰好K条或短窗时允许threshold=-1。没有D2H参与被测流水分支，CPU读取只用于定时外验证。

## 回传

输出/home/y00937463/topk-decode-pilot-r1-时间-进程号，脚本将pilot-return.txt和日志复制到B2Y/AAA_Results并打印路径。按[现有上传指南](../../AAA_Results/README.md)直接上传打印的文件；失败也回传，首次失败不启动第二进程。若未产return文件则回传日志。无需建立额外上传目录或校验清单，不重跑A0/A1/A2及同步复现。


## 终端乱码修正

原run.sh的中文提示误以GBK保存，UTF-8终端会显示乱码。这是启动提示编码问题，不是测量成功或失败的判据。原脚本保留以追溯；后续使用新增纯ASCII的run-ascii.sh，Python测量程序、源码身份、输出目录规则和计时范围不变。已完成的运行不因乱码重跑，直接上传现有AAA_Results结果及日志。

新提示：UPLOAD_RESULT为需上传结果路径，UPLOAD_LOG为日志路径，FAILED为失败并停止后续进程，COLLECTION_COMPLETE仅表示采集结束、待分析，RAW_OUTPUT为私人原始目录。无论成功失败都回传文件。
