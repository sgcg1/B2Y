# Finish溢出整行输入UB暂存：正式对照r9

候选39bb2f6f，STAGE_OVERFLOW默认false，限定ADAPTIVE_TIE=True。previous冻结4fd6a00e，双方均128扫描、histogram及compact输入暂存、分组prepare、adaptive finish和quota guard，FUSE_QUOTA/SKIP_INDEX_PREFIX关闭。仅new的finish声明64KiB FP32输入UB，meta[2]>2048时复制整行输入；溢出radix重扫和稳定tie从UB读取。非溢出不执行复制，也不读取该缓存。不改分数精度、索引规则、候选容量、重扫次数和四kernel数量。

r8生成C++中的溢出VF直接读GM，存在重复表达式读取；不能从源文本次数推断最终物理访存次数。暂存旨在降低多轮数据读取成本，DMA/同步及64KiB声明资源也可能影响随机路径调度，需双向检查，不保证净收益。

14项本地CPU测试通过；新增50组溢出暂存对照覆盖随机、特殊值、全同分、候选容量16/17缩放边界、窗口与正反序，精确集合/final_state一致；非溢出缓存保持未复制状态。关闭开关AST保持冻结旧路径。CPU不能证明现场DMA、同步、资源或性能，先编译及正确性再计时。

## 执行

沿用原yjl容器、已加载CANN及现有Python、私人/home/y00937463，确认卡0可用，不改公共环境或频率。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r9/check_sources.py &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r9/run.sh
```

更新/身份失败停止，保留输出，不reset、不改哈希、不在实验中pull。旧r8无需重跑，旧结果均保留。

## 对照与回传

13配置编译，finish-control关闭新开关且必须与冻结previous生成源码一致；双方hist均启用暂存，hist控制与冻结一致，compact/prepare保持冻结哈希守卫。保留原生stderr及编译前源码，ThreadSync诊断拒绝计时。

两独立进程、四输入、四实现（旧默认/previous/new/官方CANN GE TopKV2），独立workspace、同流24顺序、每组50事件，共1600样本；另32组独立profile保留原CSV和阶段/计算和/间隙/包络。事件和设备倍率分开；首段残缺保守标provisional。GE接口/tie契约不完全相同，本轮固定N16384/K2048/G1，不作通用验收。尤其检查溢出净收益及随机资源回退。

原报告/log保留/home/y00937463/topk-formal-decode-r9-时间-进程号并复制AAA_Results；两进程成功自动gzip/base64拆片及生成manifest，按已验证B2Y手动上传，建议附manifest作源端SHA交叉核验。失败停止并回传已有log/报告，不重拆已有文件。终端提示ASCII。

若溢出无稳定净收益或随机退化，应记录权衡，不盲目提升默认。此前r6/r7权衡独立保留。
