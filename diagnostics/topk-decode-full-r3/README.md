# Decode full-r3：设备内按候选容量选择尾段

候选c022114c已推送。ADAPTIVE_TIE默认false，不接入生产host；实验打开后，meta[2]≤2048运行8轮（r1），溢出运行4轮FP32加稳定tie（r2）。循环长度及tie分支由设备meta决定，无D2H路由。前三段不变。新控制流尚未在设备编译或计时，不预告能无代价取得两者最优值。

本地5项CPU测试通过：实际缩放流水AST的三种尾段、正反遍历、特殊值、窗口、小候选、溢出、容量恰等/超过上限；关闭开关时模块AST与冻结r1一致。身份与Python/Bash语法通过，不等于设备同步安全或完整契约通过。

## 执行

沿用已加载CANN的yjl容器、现有Python、私人/home/y00937463，先确认卡0可用。若在宿主机，进入容器；已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内更新两仓，失败停止，不重置修改、不在实验途中pull：

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only
```

确认CANN环境加载后执行：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-decode-full-r3/run.sh
```

提示全ASCII。UPLOAD_RESULT/UPLOAD_LOG是需上传路径，FAILED为失败，COLLECTION_COMPLETE仅为采集完成。

## 对照与验证

两个独立进程，全新cache/tmp/logs。四个被测版本：冻结7247ad4f默认基线、冻结03c8f916的P4-r1、冻结0d4063e6的P4-r2、新P4-r3。另编译当前模块的关闭/固定稳定尾段control，要求与冻结r1/r2生成C++完全一致；前三段及baseline同样核对既有SHA。九个编译配置记录stderr和Bisheng前原始源码；出现ThreadSync诊断拒绝计时。

先核对每版本集合、哨兵、quota/committed和窗口总计数，覆盖原r2特殊值/窗口/溢出/近分值，以及额外边界2048和2049。当前固定N16384/K2048/G1/H128，不是完整14项通用契约；不测其他K/G/非连续/Prefill。

计时输入仍为两个随机seed、全同分溢出、小边界同分。每版本50事件，轮换四版本24种顺序，每进程800、两进程1600样本。输入输出、GM workspace及事件预分配，生成/哈希/H2D/编译/校验/warmup均在定时外，抽样后复核。每个流水事件覆盖完整四kernel，不在Python根据meta分支，不从D2H读结果后挑选输出。

没有profiler全部设备任务/间隙或同轮CANN，不能混算正式×CANN。分别判断r3较默认与旧候选的变化，随机收益和溢出成本都保留，不挑最快值。

输出/home/y00937463/topk-decode-full-r3-时间-进程号。脚本将full-return.txt和日志复制到B2Y/AAA_Results并打印路径，按[现有上传指南](../../AAA_Results/README.md)直接上传。成功失败均回传；首次失败不启动第二进程，没有return则上传日志。无需校验清单或额外层级，不重跑r1/r2。
