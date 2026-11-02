# Decode full-r2：四轮FP32后按绝对索引稳定处理tie

候选0d4063e6，默认STABLE_TIE=false保留已测r1，实验显式打开新尾段；生产host没有新路由。新尾段只做4轮FP32径向筛选，余下同分者按原索引连续分段计数、前缀分配及升序写出，替代r1的后4轮补码索引radix。新增128个int32（512字节）tie前缀数组；小候选、溢出重扫和前三个kernel算法不变。

本地5项CPU测试通过，含缩放的prepare→compact→finish实际AST、两种尾段、P2/P4、正反遍历、特殊值、窗口、小候选与溢出，且关闭STABLE_TIE后整个模块AST与冻结03c8f916一致。另有身份和Python/Bash语法检查。尚无r2 NPU编译或性能结果。

本次假设是减少溢出的全窗索引radix成本。新tie仍需两遍原窗口读和前缀处理，即使边界≤2048也可能付出这些成本；不能提前保证随机或小边界收益。没有省略同分小索引规则，也没有根据D2H结果做host路由。

## 执行

沿用yjl容器、现有CANN环境、容器Python和私人目录/home/y00937463。先确认卡0可用。不重新部署或改共享环境。

若在宿主机先进入容器；已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内更新两仓，失败停止，不重置用户修改、不在实验中途pull：

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only
```

确认CANN环境已加载后运行：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-decode-full-r2/run.sh
```

终端提示全ASCII，UPLOAD_RESULT/UPLOAD_LOG是待上传路径，FAILED表示停止后续进程，COLLECTION_COMPLETE只是采集结束。

## 对照范围

只对照P4：冻结7247ad4f单kernel基线、冻结03c8f916的P4-r1、新P4-r2。当前源码关闭新开关的finish额外编译作control，必须与冻结r1生成C++完全相同；hist/prepare/compact及baseline也必须与上一回传生成SHA一致。control只编译作身份检查，不增加被测版本。

两个独立进程，新cache/tmp/logs。七个编译配置分别保存原生stderr及Bisheng前原始C++；ThreadSync诊断出现拒绝计时。所有输入输出及GM workspace预分配，baseline与两个流水版本各用自己的输出/工作区，同流依次调用四kernel。

同r1的校验：NaN/Inf/±0、FP16边界、FP32近分值、窗口、全同分溢出、小边界同分、两个随机seed；逐版本核对精确索引集合及哨兵，流水核对quota归零和窗口总计数。前后校验均在定时外。不是完整14项通用契约，不含其他K、G、非连续或Prefill。

计时四种输入：两个随机seed、全同分溢出、小边界同分。每版本50个事件，六种顺序轮换，每进程600、共1200样本。每个流水事件完整包围四kernel，无中途D2H。编译、哈希、H2D、校验及warmup不计时。分别看r2相对默认及r1，不能只挑有利输入；有主场景回退不启用默认。

无profiler全部任务/间隙或同轮CANN，暂不计算正式×CANN。实际新尾段同步、资源与性能必须以现场记录判断，不因本地AST通过而接受。

## 回传

脚本在/home/y00937463/topk-decode-full-r2-时间-进程号保存原文，并复制full-return.txt和日志到B2Y/AAA_Results。直接按打印路径和[现有上传指南](../../AAA_Results/README.md)上传；失败也回传，首次失败不启动第二进程。没有return时上传日志。不需额外目录或校验清单，不重跑r1或成本探针。
