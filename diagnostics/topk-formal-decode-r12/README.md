# 溢出FP32分数键预计算：正式对照r12

候选5eb130ef，对照冻结ec986f88。按已确认偏好，两侧均保留溢出输入暂存、hist/compact暂存、128扫描、分组prepare、adaptive finish及quota guard；FUSE_QUOTA/SKIP_INDEX_PREFIX关闭。仅new启用CACHE_OVERFLOW_KEYS，溢出时新增一个VF为整行预计算完整uint32 FP32排序键，后续radix及稳定tie复用。不改变分数精度、NaN/零规则或低绝对索引tie。

新增64KiB键UB，连同输入暂存128KiB，另有原有约19KiB工作区；最终资源以现场编译为准。非溢出不预计算，但声明资源可能影响调度。预计算与键写入也有成本，不保证净收益。粗键筛选仍按原方式计算，不同时叠加其他优化。动态缓存读取有显式边界，保留ThreadSync拒绝计时。

15项CPU测试通过，新增50组溢出键缓存对照，覆盖随机、特殊值、全同分、量化、接近FP32、窗口和正反序，精确集合/final_state一致；每个已预计算键与独立FP32键一致，非溢出缓存未填充。CPU不能证明现场同步/资源或收益。

## 候选同步与执行

TileOPs GitHub推送因凭据认证失败，本轮候选通过B2Y的candidate.bundle提供，提交身份仍为5eb130ef。bundle只含ec986f88之后这一项内核及其测试提交；不修改远端配置或凭据。apply_candidate.py核对SHA、依赖、提交及文件范围，只允许main干净工作区快进；分叉或修改时停止，绝不reset/强推。GitHub待恢复后可另行同步，不要求提供令牌。

沿用原yjl容器、现有CANN/Python及私人/home/y00937463，确认卡0可用，不改公共环境或频率。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r12/apply_candidate.py &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r12/check_sources.py &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r12/run.sh
```

本轮不从GitHub拉取尚未发布的候选。任一步失败停止并保留输出，不改哈希、不在实验中pull，不重跑旧r11。

## 对照及回传

沿用r11七种计时输入和四项额外正确性，覆盖随机、2048/2049边界、量化、接近FP32、双峰、窄窗及特殊值/短窗/空窗/反向。全窗有限分数对照四实现，窄窗仅三种TileLang、不算CANN倍率；两进程2700事件、54组独立profile，各选最后50次完整调用。随机CANN和窄窗整体计时此前波动大，保留全部样本，不挑最高倍率或用设备耗时替代事件。

13编译配置，finish-control关闭新缓存但保留输入暂存，必须与冻结候选一致；其他阶段哈希守卫。源码/工具身份、原始stderr/编译前源码、CSV均回传，ThreadSync停止。首部残段保守标provisional，不作通用验收。默认host不变。

两进程成功自动gzip/base64拆片，原报告/log保留/home/y00937463/topk-formal-decode-r12-时间-进程号并复制AAA_Results。上传脚本列出的所有分片，建议附manifest。失败停止并回传已有log/报告，不重复拆已有文件。终端提示ASCII。
