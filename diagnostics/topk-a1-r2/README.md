# A1 r2：首轮uint8粗键缓存独立筛选

状态：TileOPs候选944bc00d已推送GitHub，默认关闭（CACHE_COARSE=false）；A0仍关闭。8项本地CPU检查及Python/Bash语法检查通过，尚无A1 NPU编译、资源或性能结果。A0已因未证明稳定收益停止扩大测试。

r1两次均因eager改写后的Python静态嵌套失败，尚无A1设备结果。r2消除新增外层else；已用回传改写源码做结构编译回放，尚未重新执行TileLang前端。详见[失败归档](../../experiments/topk/20261102-a1-r1-eager-nesting/analysis.md)。请仅运行r2，不重跑r1。

## 候选范围与风险

首轮histogram将粗键写入uint8[N]共享缓存；首轮compact读取缓存，已确定入选者只写索引，边界桶中前2048条读取FP32完整键进入候选缓存。边界总数仍完整累计，溢出后的轮次沿用原全窗精确回退。缓存读写跨原有VF边界；只有有效窗口且有quota时初始化，compact只在相应有效范围且active>0时读取。候选和轮次编号不重排，不改host默认路由。

新增缓存Decode每worker16KiB，连同已有声明数组约50.6KiB，未计编译器布局、对齐及隐藏开销。N65536新增64KiB，当前不据此推广Prefill。额外UB写读、编译器资源开销可能抵消收益；全同分/大边界桶仍需FP32读取或溢出重扫。粗键不能替代最终FP32精度，缓存满不能截断总计数。

## 操作位置与已有环境

使用现有yjl容器和已加载的CANN环境、容器Python。只写/home/y00937463私人目录，不重新部署环境。操作者先确认设备0可用；不重置设备、不终止其他任务。

若在宿主机，进入容器；已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内更新两个现有仓库；任一步失败即停止，不清理用户修改，不在实验途中pull：

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only
```

确认已有CANN环境加载后运行：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-a1-r2/run.sh
```

## 测量与返回

两个独立Python进程，各自全新cache/tmp/logs；冻结7247ad4f基线，对比新源码默认关闭control与仅CACHE_COARSE=true的a1。R1/N16384/K2048/W1/H128、COARSE=true、REUSE_COARSE=false。先检查发布源码和工具SHA，再要求baseline/control生成C++完全相同，否则拒绝计时。各自保存三份生成源码。

每进程两个seed，各版本各50个事件，按六种排列轮换执行顺序（50非6整倍数，各排列计数相差1）。计时为预分配后的无插桩单kernel调用事件，编译、输入生成/哈希、校验及warmup均在计时外；不是profiler纯kernel，不计算CANN倍数。保留所有样本，不挑最快值。生成源码资源和设备编译警告需随日志一起分析。

未计时校验覆盖随机集合、同分、NaN/Inf/±0、大边界桶、部分窗口、短窗口、空及反向窗口。本工具不是完整14项契约，不覆盖全部K/G/非连续规格；有希望的候选才进入完整测试与主规格回归。completed不等于accepted。

输出/home/y00937463/topk-a1-r2-时间-进程号，子进程保留原始a1-return.txt和日志。脚本将回传文件复制到B2Y/AAA_Results并打印路径，直接按[上传指南](../../AAA_Results/README.md)上传这些文件即可，不需额外层级或校验清单。失败也回传，首次失败后停止第二个进程；如外部杀死未产return文件则回传日志。不覆盖旧结果，不重跑A0或旧stage/probe工具。
