# 溢出预计算限制到有效窗口：正式对照r14

候选928b34fd已推送个人fork main，对照冻结5e01bbeb。两侧均启用r13粗桶缓存、完整键缓存及溢出输入暂存，其他hist/compact暂存、128扫描、分组prepare、adaptive finish和quota guard相同，FUSE_QUOTA/SKIP_INDEX_PREFIX关闭。仅new增加WINDOW_PRECOMPUTE，使已有预计算VF只处理starts<=i<ends的元素。整行DMA、UB缓冲及VF/kernel数量不变。

r13全窗再降3.6%–5.5%，窄窗回退约6.2%；本项检验无效预计算是否是可减成本，不先认定根因。窗外键保持未初始化，不被后续溢出读取：radix与tie已有窗口范围守卫。完整分数键和粗桶号、NaN/零规则和低绝对索引优先均不改变。增加窗口判断可能影响全窗调度，须双向验证。

17项内核CPU测试通过，新增50组窗口预计算对照验证精确集合/final_state/VF次数相同、有效窗口键/粗桶正确及窗外键未填充。关闭开关AST保持旧路径。CPU不能替代现场同步、资源、正确性及性能验证。

## 执行

沿用原yjl容器、已加载CANN和现有Python、私人/home/y00937463，确认卡0可用，不改公共环境或频率。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r14/check_sources.py &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r14/run.sh
```

更新/身份失败停止，保留输出，不reset、不改哈希、不在实验中pull。旧r13无需重跑，生产默认不变。

## 覆盖及比较口径

在r13原七输入外，增加窗口长度2049、8192、12288的溢出，使用不同起点及高分窗外干扰。总10种计时输入；保留原4096窄窗与全窗分布、2048缓存边界、随机控制，以及四项特殊值/短窗/空窗/反向只做正确性检查。输入oracle验证确实命中溢出分支，不设置经验路由阈值。

仅6个全窗有限输入运行CANN比较；4种非全窗仅比较三种TileLang，不计算Ascend C倍率。两个独立进程，共3600事件、72组独立profile，每组按时间选择最后50完整调用；每进程24项验证记录。比r13报告/运行时间增加，请按脚本输出清单上传全部分片，不固定分片数。

13配置编译，finish-control保留粗桶/完整键/输入缓存但关闭窗口限制，必须与冻结previous生成源码一致，其他阶段哈希守卫。ThreadSync诊断立即拒绝计时。保留stderr、编译前源码、原CSV及阶段/计算和/间隙/包络；事件和设备倍率分开，首段残缺保守标provisional，不挑最高倍率。固定N16384/K2048/G1，不作通用验收。

## 回传与判断

两轮成功后自动gzip/base64拆片并生成manifest，原文/log保留/home/y00937463/topk-formal-decode-r14-时间-进程号并复制AAA_Results。上传清单中全部分片，建议附manifest补源端SHA核验。失败停止并上传已有log/报告，不重拆已有文件。提示ASCII。

重点检查新增窗口范围的净收益及全窗判断开销。若仍有窗口回退，按证据记录，不根据单样本随意设阈值。已验证r12输入暂存+完整键缓存继续保留，r13粗桶收益/代价独立记录。
