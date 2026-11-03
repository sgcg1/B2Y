# Histogram UB输入暂存正式对照r8

候选4fd6a00e，histogram新增STAGE_INPUT默认false。previous冻结9a5087dd；两侧128扫描、compact UB暂存、分组prepare、adaptive finish和quota guard一致，FUSE_QUOTA/SKIP_INDEX_PREFIX均关闭。仅new在histogram VF前用T.copy批量搬运每核连续输入至UB，再从UB读取粗键。P4每核新增16KiB声明暂存，不改原子次数、桶数、候选容量或四kernel数量。

compact暂存此前随机事件已改善2.6%–3.6%；histogram同样直接读GM，但不能据此保证同样收益，DMA/同步和原子冲突成本可能抵消。现场须核验实际生成代码、同步与性能。

13项本地CPU测试通过；新增histogram AST对照180组（3输入×5窗口×3分核×2执行序×2开关），每桶计数与独立oracle一致，覆盖随机、全同分、NaN/inf/零/FP16溢出边界；关闭暂存模块AST与冻结9a5087dd一致。其余9项pipeline测试继续通过。CPU不替代NPU编译/正确性验收。

## 执行

沿用原yjl容器、已加载CANN、现有Python、私人/home/y00937463，确认卡0可用。不改公共环境或频率。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r8/check_sources.py &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r8/run.sh
```

更新/身份失败停止并保留输出，不reset、不改哈希、不在实验中pull。r5/r6/r7无需重跑。

## 对照与回传

13种编译配置：hist-previous来自冻结模块，hist-control为当前关闭暂存，要求生成源码一致；new单独启用hist暂存。其余prepare/compact/finish控制及冻结哈希守卫，原始stderr/编译前源码保留，ThreadSync诊断拒绝计时。

两独立进程、四输入、四实现（旧默认/previous/new/官方CANN GE TopKV2），独立workspace、同流24种顺序，每组50事件共1600样本；32组独立profile保留原CSV及阶段/计算和/间隙/包络。事件与设备倍率分开，首段残缺保守标provisional。GE接口/tie契约不完全相同，固定N16384/K2048/G1，不作完整通用验收。

完成后结果和log保留/home/y00937463/topk-formal-decode-r8-时间-进程号，并复制AAA_Results。两进程成功自动生成gzip/base64分片及manifest，按现有B2Y手动上传，建议附manifest用于源端SHA交叉核验。失败停止并回传已有报告/log，不重复生成已有分片。提示全部ASCII。

若hist设备或完整事件无稳定净收益，记录否定结果，不提升默认。此前r6/r7分布权衡独立保留，本轮只测hist暂存。
