# Finish跳过恒定索引高字节：正式对照r7

候选23ff5c63，SKIP_INDEX_PREFIX默认false。previous冻结9a5087dd；两侧均128扫描、UB输入暂存、分组prepare、adaptive finish及quota guard，FUSE_QUOTA保持false。只测试跳过两个无效索引radix轮次。

固定N16384，绝对索引范围[0,16384)，取反uint32索引的高16位恒为0xffff。这两轮无法区分候选或产生接受项；跳过原轮次4/5，保留原轮次0–3的FP32完整键和6/7的索引低16位，仍按低绝对索引精确破同分。不缩减分数精度，不截断候选。循环仍8个迭代，静态开关与轮次条件跳过两轮VF；不声称编译后已完全消除循环。溢出adaptive路径仅执行原0–3四轮及稳定tie，无轮次4/5；新开关不改变其算法路径，但设备生成调度仍需验证。

11项本地CPU测试通过，新增300组集合/final_state对照，覆盖特殊值、随机、全同分、容量16/17缩放边界、窗口、正反序、三种tie模式和quota guard开关；关闭EARLY_EXIT且使用8轮尾段时VF减少16次。另遍历全部16384索引，验证恒定前缀及低16位顺序；不将本固定形状优化推广到任意N。关闭所有开关模块AST保持旧路径。CPU不证明现场编译/同步/性能。

## 执行

沿用原yjl容器、已加载CANN与现有Python、私人/home/y00937463，确认卡0可用。不改公共环境或频率。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r7/check_sources.py &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r7/run.sh
```

更新或身份检查失败立即停止，保留输出，不reset、不改身份哈希，不在实验中pull。旧r5/r6无需重跑。报告保留HEAD及工作/HEAD blob/换行归一化SHA。

## 对照与证据

11个编译配置，finish-control（新开关关闭）必须与冻结previous相同；compact两侧均使用已验证暂存且生成源码一致，其他阶段冻结哈希守卫。原生stderr及编译前C++回传，ThreadSync诊断拒绝计时。

两个独立进程、四输入、四实现（旧默认/previous/new/官方CANN GE TopKV2）、独立workspace、同流24种顺序、每组50事件，共1600样本；32组独立profile保留原CSV及阶段/计算和/间隙/包络。事件和设备倍率分开，首段残缺保守标记provisional，不挑最好值。CANN接口/tie契约不完全相同，固定N16384/K2048/G1，不作完整通用验收。

若随机或同分净收益不足、溢出回退，按证据记录，不强行提升默认。目标是减少真正无效radix处理，不预告设备收益。

## 回传

结果与日志保留/home/y00937463/topk-formal-decode-r7-时间-进程号并复制AAA_Results；两进程成功后自动生成gzip/base64分片和manifest，按现有B2Y手动上传，建议附manifest用于源端SHA独立核对。失败停止，回传已有日志/报告，不重复生成已有分片。终端提示ASCII。
