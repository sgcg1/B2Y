**172510失败处理：先按[源码身份恢复指南](SOURCE_RECOVERY.md)诊断。失败在编译前，不代表UB暂存方案失败。**

# Compact UB输入暂存正式对照r5

候选9a5087dd，STAGE_INPUT默认false。冻结949d73c4（previous）与新暂存版本（new）都使用128扫描、分组prepare、adaptive finish和quota guard。仅new将每核连续4096个FP32输入通过T.copy搬到UB后读取，每核增加16KiB声明暂存；保持4核、128线程、相同原子分配/候选计数/精确选择和四kernel数量。P2支持增加32KiB，但本轮仅P4。

r4生成C++显示compact VF直接读GM，粗键分支包含重复加载表达式；这不证明最终汇编发生等量物理访存。批量搬运能改变数据路径，也会增加搬运/同步成本，因此须实测，不预告收益。T.copy在VF前执行，由编译器插入依赖同步，实际布局/同步/资源必须通过现场编译及检查。同步诊断立即拒绝计时。

8项CPU测试通过：暂存与非暂存的完整索引集合、final_state一致，覆盖128/512扫描、P2/P4、正反序、NaN/inf/零、随机、全同分、容量边界与窗口，共400组暂存对照。关闭开关模块AST与冻结旧路径一致。CPU无法证明真实DMA或同步；仍需NPU正确性检查。

## 执行

沿用已加载CANN的yjl容器与现有Python，私人/home/y00937463，先确认卡0可用。不修改公共安装、频率或环境；已在容器无需重复进入。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r5/run.sh
```

更新失败停止，不重置修改、不在实验中pull。旧r4无需重跑，512扫描否定结果保留，不用于本轮计时。

## 对照与回传

沿用正式四版本对照：旧默认/冻结previous/new/官方CANN GE TopKV2，同轮同输入同流、独立预分配workspace、24种顺序。两独立进程、四输入，每实现每输入50事件，共1600样本；另32组独立profile，保留阶段/计算和/间隙/包络及原始CSV。事件与设备倍率分开。CANN接口/tie契约不完全相同，固定N16384/K2048/G1，不代表通用验收。

11种编译配置，保留stderr和编译前源码；默认compact必须与冻结一致，hist/prepare/finish哈希守卫。profile首段残缺保守标记，其他顺序/缺样/重叠问题拒绝，不挑最好值。若设备时间与事件无稳定净收益，记录否定结果，不扩大。

结果和log保留在/home/y00937463/topk-formal-decode-r5-时间-进程号，并复制到AAA_Results。两进程成功后自动生成gzip/base64分片与manifest，按现有B2Y手动上传方式回传，建议附manifest核验源端SHA。失败停止并回传已有日志/报告，不重跑旧实验，不改原文件。全部终端提示ASCII。
