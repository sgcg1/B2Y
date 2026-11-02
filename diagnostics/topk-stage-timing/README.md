# 当前下一步：Decode真实TopK阶段诊断

Probe2完整回传已经复核：21份文件哈希、500个事件样本、200个counter样本及10组源码转换一致。counter随重复工作量增长稳定，完整事件有明显轮次漂移，不能用原摘要的百分之零点几差异证明“插桩零开销”。详见[完整探针审阅](../../experiments/topk/20261102-timer-probe2-complete/analysis.md)。

现在只运行Decode：R=1、N=16384、K=2048、worker=1、H128、coarse=true、grouped scan。新工具只通过CPU/静态回归，尚未在NPU运行；本轮用于检验真实TopK上的计时适用性，不接受最终性能版本。

## 1. 在已有yjl容器内更新B2Y

沿用已成功运行的Python/CANN环境，不重装软件、不修改共享环境。已在容器内时执行：

```bash
git -C /home/y00937463/B2Y status --short
```

工作区干净且没有实验运行时：

```bash
git -C /home/y00937463/B2Y pull --ff-only origin main
```

有修改先保存，不用reset/clean覆盖。TileOPs实现没有改变，此次无需pull TileOPs或重跑14项测试。工具要求生产内核SHA为987da9f9d314f8744bef05a628e60a14b88e63db320374f36a3b6411ce5eb2e3，且TileOPs已跟踪文件无修改；docs提交差异可以存在。SHA不匹配时回传错误，不放宽校验。

## 2. 查看物理卡0状态

```bash
npu-smi info
```

确认获准卡0健康、无竞争任务。仅使用这一张卡；不重置设备、不改频率。如果卡号不同，修改下一步的--device为获准物理卡号，进程内仍映射npu:0。

## 3. 在新目录执行

```bash
TOPK_STAGE_RUN="/home/y00937463/runs/topk-stage1-$(date +%Y%m%d-%H%M%S)"
timeout --kill-after=10s 900s "${TOPK_PYTHON:-python3}" -B \
  /home/y00937463/B2Y/diagnostics/topk-stage-timing/run.py \
  --repo /home/y00937463/TileOPs --device 0 --output "$TOPK_STAGE_RUN"
```

保持原目录不动，每次使用新目录。输出STAGE_COMPILE显示production/traced/fenced/timed，STAGE_SAMPLE显示当前轮次。首次4组编译可能需要数分钟，最长15分钟；强制终止不会保证生成最终报告，保留目录和最后日志。

脚本只在新目录生成生产源码快照和带诊断参数的AST副本，不修改TileOPs仓库或安装包。生产工作逻辑经CPU AST比较一致；诊断版本新增每轮状态快照，以及用于确认阶段身份的VF标记。后处理通过唯一标记识别14个VF，再删除全部标记写入与无效ABI锚点。若VF融合、标记、顺序、五轮循环或控制流不符合预期，立即停止并保存捕获源码，不猜测阶段映射。

源码后处理只在专用Python子进程注册。cache/tmp/logs和可见设备只对该子进程生效，全部写入私人runs目录，不改HOME、父终端EVIDENCE或共享SDK。

## 4. 一次回传原始结果和源码

正常完成或Python报错后执行：

```bash
cat "$TOPK_STAGE_RUN/stage-return.txt"
```

将完整JSON复制回来，或提交B2Y根目录“实验结果”收件文件。该文本已包含逐次事件/阶段样本、状态轨迹、生产和timed源码；本轮不再先回传只有中位数的摘要。文本较长，注意终端滚动区不要截断。

若最终文本未生成，回传最后一条STAGE_COMPILE/STAGE_SAMPLE之后的完整错误，不删除目录、不改生成源码、不重装依赖。

## 测量和判读

| 版本 | 用途 |
| --- | --- |
| production | 原始生产TopK，无诊断参数或计时插桩 |
| traced | 同一工作逻辑加每轮7字段状态快照；VF身份标记已删除，无计时屏障/时钟 |
| fenced | traced加与timed相同的完成屏障，无时钟记录 |
| timed | 相同边界加GetSystemCycle和GM记录 |

每种预热5次，另预热事件，再同进程交替正反序采50轮；输入、输出和记录缓冲预分配。每个版本都在事件外进行相同记录缓冲回读。使用与历史Decode相同的NPU RNG种子，实际输入SHA另行记录，不假定软件栈的随机数一定一致。所有版本检查精确选择集合与输入未修改，另做一次不计时的全相等输入tie检查。

共27个动态区间：初始化1段；5轮各记录round_reset、histogram、scan、compact、state_update_with_trace；最终tie/收尾1段。scan合并其4个VF，不逐条插入屏障；histogram与compact均包含自身的加载/键计算。**这不是把加载、原子指令和算术分别计时。** state_update_with_trace包含额外状态快照写入，不能当作原生产状态更新的纯成本。

每轮状态字段依次为剩余quota、已提交输出数、阈值桶、active数量、accepted数量、上一轮候选数、下一轮候选数；首轮或上一轮候选数大于2048时选择全域分支。只有该轮开始时quota仍大于0才标记全量重扫，避免把工作已停用的空循环算作输入重扫。这有助于解释相同阶段为何在不同轮次耗时不同。

时间按1000ticks/μs换算，保留原始ticks，不扣除probe2的0.092μs空区间。完整事件覆盖调用；外层counter包络包含阶段间观察成本；各阶段含自身完成屏障/时钟观察成本。三者范围不同，不能强行相等，也不能把27个中位数之和当成原生产总耗时。报告另保存同次运行各区间之和的中位数用于核对。

先检查正确性、时间戳顺序、包络/事件容纳、候选轨迹一致性，再比较production→traced→fenced→timed的扰动与原始分布。短阶段接近观察成本时不能凭单个比例宣布瓶颈；若总耗时显著改变，阶段数据只用于提出假设，再用低扰动消融确认。多worker/Prefill尚未覆盖，不能从Decode直接推广。

stage_profiling_accepted始终false，completed只代表采集完成。主机侧AST和C++检查不证明最终Bisheng指令顺序；真实设备结果仍须审阅。
