# 950PR指定规格：当前保留实现与TopKV2设备耗时

本轮只测量，不增加优化。以现有yjl容器、950PR、卡0为准；同环境实测TopKV2为比较目标，不使用截图43.7微秒作固定门槛，也不称为server2正式验收。

## 在现有容器中执行

先将B2Y更新到包含本目录的版本。保留原有CANN、Python和TileLang环境，不重建容器。TileOPs本地Git对象必须包含已运行过的`5eb130eff798e06341d67fd6899f67a9f66ffb20`；工具从Git读取该版本两个模块到本轮私有目录，不切换分支或覆盖工作区。

```bash
cd /home/y00937463/B2Y
bash diagnostics/topk-950pr-device-compare-r1/run.sh
```

脚本使用`/usr/local/python3.12.14/bin/python3`。如缺少旧提交、环境变量、卡0被占用或原始记录格式不支持，停止并回传日志，不自行改环境或禁用检查。运行期间不启动其他NPU任务。

## 测量范围

- FP32分数`[1,1,16384,1]`、int32 starts/ends`[1,1]`、全窗口`[0,16384)`、int32输出`[1,1,1,2048]`，K=2048，无序。
- 按目标仓固定case seed，在NPU上生成`torch.randn`；同一进程双方读取同一份张量，报告输入SHA。不是溢出压力分布专项测试。
- 当前保留实验组合：r12的hist输入暂存、compact输入暂存、prepare分组偏移、finish自适应tie/提前退出/溢出输入及完整键缓存。四kernel整条路径计时；并非公开目标仓默认实现。
- 原生比较项：GE构建静态TopKV2，largest=true、sorted=false、dim=-1、indices=int32、sort_policy=0、保留FP32精度。复用同一输入存储，形状视图不产生设备拷贝。TopKV2额外产生values输出，已披露；未复原网页历史adapter。
- 每侧3次预热，15个独立单次调用profiling窗口；每次前执行1GiB int32缓存驱逐并同步，驱逐在窗口外。双方交替先后，三个独立Python进程重复。
- 延续目标仓原始记录解析方法：按逻辑任务合并AIC/AIV，再相加各任务设备跨度；覆盖额外AICPU记录。不使用Event、CPU墙钟或四kernel总包络替代。原始布局/任务数/名字不能确认时失败，不输出猜测耗时。
- 输出每侧全部样本、算术平均、标准差、最小/最大值；倍数=`TopKV2平均耗时 / 我们平均耗时`。大于1才表示比本机TopKV2快；需三轮共同判断稳定性。
- 计时前后核验正确性：唯一且合法的索引、TopK分数集合，当前实现另核验稳定tie规则及最终quota；同时检查输入未改写。

## npu-guard与共享设备

npu-guard是目标仓用于共享NPU预约的外部工具，不是TopKV2依赖。本脚本无需安装它。使用私人目录的`flock`避免本脚本重复运行，并在导入运行时前、每次采样前和结束后检查`npu-smi`卡0进程；发现外来进程即停止。该检查不能代替全宿主共享预约，检查间隔仍有并发风险，报告明确记录此限制；不得称为正式独占认证。不杀进程、不重置卡、不改频率。若现场已有预约，请在已有预约内启动本脚本。

## 回传与失败

原始目录为`/home/y00937463/topk-950pr-device-compare-r1-时间-PID/`，保留原始profiling与编译日志。自动复制三份JSON和对应日志到`/home/y00937463/B2Y/AAA_Results/`。

成功后自动生成gzip+Base64分片以及manifest，也放根目录`AAA_Results`。上传本轮打印的分片及manifest即可；不需要手工生成校验文件。分片不可直接阅读是传输编码，原JSON在本地仍保留。若直接上传JSON可行，也可上传三份JSON及日志而不上传分片。

失败时后续轮次停止：上传已生成的本轮JSON和log，先分析失败原因。不要删除原始目录或反复原样运行。JSON包含原始设备关键记录和编译诊断，支持后续复核；未完成的报告不作为性能结果。

## 来源与本地校验

测量协议参考目标仓`ascend950`提交`f0072a85a3ce1a4bcc520ba12cd09a0337871131`的`measure_baselines.py`、`kernel_task_profile.py`和`complete_profile.py`；本目录是950PR开发适配，协议名独立标注。原生构建/执行适配复用已验证r12代码。

`identity.json`固定工具文件和所读内核SHA；`test_support.py`仅在CPU上验证任务去重、截断拒绝、分片回传及脚本语法，不代表950PR已经执行。设备结果尚待本轮运行。
