# 溢出粗桶缓存复用输入UB：正式对照r13

候选5e01bbeb已推送个人fork main，对照冻结5eb130ef。两侧均启用hist/compact输入暂存、溢出输入暂存、完整FP32键缓存、128扫描、分组prepare、adaptive finish和quota guard；FUSE_QUOTA/SKIP_INDEX_PREFIX关闭。仅new启用CACHE_OVERFLOW_COARSE。

在已有预计算VF内，先读取原始FP32值并缓存完整uint32排序键，再将原overflow_x位置写成FP32表示的粗桶号0–255。所有桶号均能被FP32精确表示。后续radix只读桶号和完整键；同分尾段只读完整键，因此不再需要原FP32暂存值。不改变NaN/有符号零语义、分数精度或低绝对索引优先。开关要求CACHE_OVERFLOW_KEYS=True，避免丢失仍需使用的原始值。

不增加UB缓冲、不新增VF或kernel；原位读写的实际调度/同步和预计算成本仍可能造成回退，不能从源码省操作直接保证收益。保留ThreadSync拒绝计时守卫。

16项CPU测试通过；新增50组粗桶缓存对照覆盖随机、特殊值、全同分、量化、接近FP32、窗口及正反执行序，检查精确集合、final_state、每个完整分数键和粗桶号，以及VF调用数相同；非溢出不改写缓存。关闭新开关AST保持原路径。尚无本候选NPU结果。

## 执行

沿用原yjl容器、已加载CANN及现有Python、私人/home/y00937463，确认卡0可用，不改公共环境或频率。本轮GitHub个人fork推送成功，不需r12 bundle步骤。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r13/check_sources.py &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r13/run.sh
```

更新或身份失败停止，保留输出，不reset、不改哈希、不在实验中pull；旧r12无需重跑。生产默认不变。

## 对照与回传

13配置编译，finish-control保留输入/完整键缓存但关闭新粗桶缓存，必须与冻结previous生成源码一致；其他阶段哈希守卫。源码/工具身份、stderr、编译前C++及CSV均回传，ThreadSync立即拒绝计时。

沿用七种计时输入及四项额外正确性，覆盖随机、2048/2049边界、量化、接近FP32、双峰、窄窗和特殊值/短窗/空窗/反向。全窗有限分数四版本比较，窄窗只对照三种TileLang、不算CANN倍率。两个独立进程2700事件、54组独立profile各选最后50次完整调用。事件、设备包络与阶段耗时分开；首段残缺保守标provisional，不挑最好倍率，不以跨轮波动宣称改善。

完成后原报告/log保留/home/y00937463/topk-formal-decode-r13-时间-进程号并复制AAA_Results；两轮成功自动gzip/base64拆片及manifest。按脚本打印清单上传全部分片，建议附manifest完善源端SHA核验。失败停止并回传已有log/报告，不重拆已有文件。终端提示ASCII。

按已确认取舍，继续保留已验证的溢出输入和完整键缓存。本项粗桶复用若无稳定净收益则记录否定结果，不影响此前收益结论。
