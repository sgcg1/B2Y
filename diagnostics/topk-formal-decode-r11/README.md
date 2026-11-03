# 溢出UB暂存扩大验证r11：不叠加新内核优化

沿用ec986f88候选与冻结4fd6a00e，算法及开关与r10相同，继续保留hist/compact暂存和quota guard，FUSE_QUOTA/SKIP_INDEX_PREFIX关闭。r10全同分事件改善约28%，但仅一种计时溢出分布，且缓存路径小回退；本轮验证能否推广，再决定后续专用路径，不能以单样本过拟合。

## 新覆盖

7种计时输入：随机控制、边界桶2048（缓存）、2049（溢出）、四级量化、接近FP32分数、打乱双峰、窄窗口溢出（窗口512:4608，1024高分+3072边界）。每次验证显式核对期望分支与meta。另4项只做正确性：NaN/inf/有符号零/FP16溢出边界、短窗、空窗、反向窗口。

两个CPU用例验证生成器确定性及独立FP16桶oracle，保证2048/2049和窄窗确实命中指定路径。复用14项内核CPU测试结果，不宣称已通过新增NPU分布。静态源身份与原始同步诊断守卫保留。

全窗有限分数比较旧默认/previous/new/CANN GE；窄窗仅比较三种TileLang实现，不运行CANN或报告xAscend C，避免偷换全窗基线。特殊值只检查项目精确索引集合，不对CANN确定性tie作错误要求。

## 执行

沿用原yjl容器、现有CANN/Python及私人/home/y00937463，确认卡0可用，不改公共环境或频率。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r11/check_sources.py &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r11/run.sh
```

更新/身份失败停止，保留输出，不reset、不改哈希、不在实验中pull。旧r10无需重跑。没有新TileOPs提交。

## 证据与成本

两独立进程，每实现/输入50事件，总2700样本；54组独立profile各选最后50次完整调用，保留原CSV、阶段/计算和/间隙/包络。每进程18项验证记录，含计时前后及额外正确性。相较r10覆盖更多，运行及报告/分片数量会增加，不固定要求每份5片，上传启动脚本打印的全部分片。

13配置编译、源码/冻结控制哈希、ThreadSync拒绝计时守卫保留。新增输入生成器也纳入工具SHA身份。profile首段残缺继续保守标provisional；事件和设备倍率分开，不挑最好值。固定N16384/K2048/G1，不是通用验收。优先比较相同输入同轮previous与new，不用跨轮CANN波动宣称收益。

原报告/log保留/home/y00937463/topk-formal-decode-r11-时间-进程号并复制AAA_Results；两轮成功自动生成gzip/base64分片和manifest，按现有B2Y手动上传，建议附manifest。失败停止，上传已有log/报告，不重拆已有文件。提示ASCII。

多种溢出分布若收益不一致，记录范围及原因，不直接提升默认；全部保持默认host不变。
