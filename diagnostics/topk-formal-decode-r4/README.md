# Compact 512元素扫描：正式对照r4

候选364fed4c，SCAN_WIDTH默认128。只将compact扫描从每核32轮×128元素改成8轮×512元素；仍128线程、4核、相同原子分配与完整计数，不改容量/精确选择/四kernel数量。可能减少串行循环和改善每线程处理粒度，也可能增加寄存器压力；没有设备结果前不声称收益。

previous冻结949d73c4，使用分组prepare+adaptive finish+quota guard；new仅compact宽度512，finish也保留quota guard。因此本轮不是再次测试quota guard。该候选随机收益15.4%–16.6%、溢出回退1.18%已记录，保留以后按路径启用，不进入默认host。默认128 compact必须生成与冻结相同的源码；hist/prepare/finish冻结哈希核对。共11种编译配置，保留stderr、编译前源码及原始CSV，ThreadSync诊断拒绝计时。

8项本地CPU测试通过，包括新增200组宽窄扫描对照（随机、NaN/inf/零、全同分、容量16/17缩放边界、窗口与正反执行顺序），核对完整索引集合/final_state。CPU不能验证NPU布局、寄存器、同步或性能，现场先编译与正确性检查再计时。

## 执行

沿用已加载CANN的yjl容器及现有Python、私人/home/y00937463，先确认卡0可用。已在容器不重复进入；不修改公共安装、频率或运行环境。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r4/run.sh
```

更新失败停止，不重置用户修改，不在实验中pull。工具校验精确源码身份，旧formal-r3无需重跑。

两个独立进程，各四输入（两个随机、全同分溢出、小边界同分），对照旧默认/previous/new/官方CANN GE TopKV2，独立预分配workspace、同流24种顺序、每实现每输入50事件，共1600样本。独立32组profile保留原CSV，事件和设备倍率分开。GE接口/tie契约与项目不完全相同，本轮固定N16384/K2048/G1，不冒充通用验收。profile首段残缺沿用保守标记，间隙与包络保留，不挑最好倍率。

若compact设备时间或完整事件无稳定净收益，记录否定结果，不扩大。即使有收益，仍需后续向量利用优化才能接近1.0x。

## 回传

ASCII提示；两份formal-return.txt及log复制AAA_Results，原始输出保留在/home/y00937463/topk-formal-decode-r4-时间-进程号。两轮成功后自动gzip/base64拆片，打印分片路径，按已验证的B2Y手动上传方式回传。manifest可一并上传完善源端SHA核验，不是读取结果的硬性要求。失败停止，上传已有日志/报告，不重跑旧实验、不重新生成已有分片。
