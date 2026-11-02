# A2 r3：首轮4组int32直方图独立筛选

候选67b9e72f已推送TileOPs的GitHub main；默认HIST_BANKS=1不变，只有实验显式设4。A0/A1均关闭，不应用未编译的编译器补丁。12项本地CPU检查通过，Python/Bash语法通过；尚无A2 NPU编译或性能结果。

r1工具SHA错误已修复；r2基线/control编译通过，A2在AscendLayoutInference遇handle vs int32。r3将随round变化的Parallel长度改成固定257和首轮固定1024两个循环。直接根因尚待设备验证，不宣称已编译成功。新增静态循环长度与初始化回归通过，保留身份和同步守卫。

## 改动与代价

仅round=0按lane%4将256桶计数分到4组，每组int32。它们位于原hist[257]之后，共增加4096字节；首轮初始化全部1281个int32，独立VF按桶合并4组到原hist[0:256]，再走已有H128 grouped scan和compact。后续轮次只清零原257项、只计原桶，不进入合并VF。hist[256]仍保留，完整候选计数、乒乓、tie、溢出精确回退不变。不复用分片计数做compact，不引入跨核方案。

原子总次数不减少，只分散地址竞争；首轮增加1024项清零、1024次读及256项写和一个合并VF。收益是待测假设，可能被新增成本抵消。本轮不用uint8新缓存，不代表可忽略同步检查：工具逐版本捕获原生编译stderr，出现ThreadSync诊断即保存源码与日志并拒绝计时。

## 执行位置

沿用yjl容器、现有CANN环境和容器Python，私人目录/home/y00937463。不部署新环境、不改共享安装。操作者先确认设备0可用。

若在宿主机，进入容器；已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内更新两个现有仓库，失败即停止，不重置用户修改，不在实验中途pull：

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only
```

确认已有CANN环境加载后执行：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-a2-r3/run.sh
```

## 验证与回传

两个独立进程各使用新cache/tmp/logs。冻结7247ad4f基线，对比新源码默认关闭control和HIST_BANKS=4的a2；R1/N16384/K2048/W1/H128、COARSE=true。校验发布源码和工具SHA，要求baseline/control生成C++一致。各配置保存生成源码、编译stderr和身份，编译失败也回传。

每进程两个seed，各版本各50个无插桩调用事件，轮换六种执行顺序。编译、输入生成/哈希、正确性和warmup都在定时外；不是纯kernel profiler时间，不与历史CANN混算倍数。保留全部样本，不挑最快值。

未计时检查覆盖随机集合、同分、NaN/Inf/±0、粗边界桶溢出、部分窗口、短窗、空和反向窗口。不是完整14项契约；K>2048、非连续、多分组及Prefill仍需后续有希望时回归。completed不等于accepted。出现同步或资源问题先分析，不放宽断言重复计时。

输出为/home/y00937463/topk-a2-r3-时间-进程号。脚本将a2-return.txt和日志复制到B2Y/AAA_Results并打印路径，按[现有指南](../../AAA_Results/README.md)直接上传打印的文件即可。失败同样回传，首次失败后不启动第二个进程；没有return文件时回传日志。不生成额外校验清单，不重跑A0/A1或同步最小复现。
