# Finish溢出整行输入UB暂存：有界访问重试r10

r9在compile:finish出现两条ThreadSync屏障外提诊断，工具在正确性检查/计时前停止；没有NPU性能数据，不能将其当性能回退或直接认定误报。原始记录见[失败归档](../../experiments/topk/20261103-formal-decode-r9-200743/analysis.md)。

本次仅将新增溢出缓存动态下标显式限制到[0,16383]。有效读取j满足0<=j<count，且count在该分支为16384，因此约束不改变合法读取；与已有候选缓存的有界下标方式一致。范围不明可能妨碍编译器证明UB区域不相交，但尚未现场证明根因或警告消失。保留ThreadSync拒绝计时守卫，不加入未经证明的T.assume，不改工具链。14项CPU检查通过，现场先验证编译。

候选ec986f88，STAGE_OVERFLOW默认false，限定ADAPTIVE_TIE=True。previous冻结4fd6a00e，双方均128扫描、histogram及compact输入暂存、分组prepare、adaptive finish和quota guard，FUSE_QUOTA/SKIP_INDEX_PREFIX关闭。仅new的finish声明64KiB FP32输入UB，meta[2]>2048时复制整行输入；溢出radix重扫和稳定tie从UB读取。非溢出不执行复制，也不读取该缓存。不改分数精度、索引规则、候选容量、重扫次数和四kernel数量。

r8生成C++中的溢出VF直接读GM，存在重复表达式读取；不能从源文本次数推断最终物理访存次数。暂存旨在降低多轮数据读取成本，DMA/同步及64KiB声明资源也可能影响随机路径调度，需双向检查，不保证净收益。

14项本地CPU测试通过；新增50组溢出暂存对照覆盖随机、特殊值、全同分、候选容量16/17缩放边界、窗口与正反序，精确集合/final_state一致；非溢出缓存保持未复制状态。关闭开关AST保持冻结旧路径。CPU不能证明现场DMA、同步、资源或性能，先编译及正确性再计时。

## 执行

沿用原yjl容器、已加载CANN及现有Python、私人/home/y00937463，确认卡0可用，不改公共环境或频率。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r10/check_sources.py &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r10/run.sh
```

更新/身份失败停止，保留输出，不reset、不改哈希、不在实验中pull。旧r8/r9无需重跑，旧结果均保留。

## 对照与回传

13配置编译，finish-control关闭新开关且必须与冻结previous生成源码一致；双方hist均启用暂存，hist控制与冻结一致，compact/prepare保持冻结哈希守卫。保留原生stderr及编译前源码，ThreadSync诊断拒绝计时。

两独立进程、四输入、四实现（旧默认/previous/new/官方CANN GE TopKV2），独立workspace、同流24顺序、每组50事件，共1600样本；另32组独立profile保留原CSV和阶段/计算和/间隙/包络。事件和设备倍率分开；首段残缺保守标provisional。GE接口/tie契约不完全相同，本轮固定N16384/K2048/G1，不作通用验收。尤其检查溢出净收益及随机资源回退。

原报告/log保留/home/y00937463/topk-formal-decode-r10-时间-进程号并复制AAA_Results；两进程成功自动gzip/base64拆片及生成manifest，按已验证B2Y手动上传，建议附manifest作源端SHA交叉核验。失败停止并回传已有log/报告，不重拆已有文件。终端提示ASCII。

若溢出无稳定净收益或随机退化，应记录权衡，不盲目提升默认。此前r6/r7权衡独立保留。
