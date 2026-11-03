# Finish quota更新合并VF：正式对照r6

候选93af88eb，FUSE_QUOTA默认false。previous冻结9a5087dd、new当前候选；两侧都用128扫描、UB输入暂存、分组prepare、adaptive finish和quota guard。只将finish每轮独立quota更新VF合并到轮末已有状态更新VF。写出阶段只读取state[3]/state[1]，不读取state[0]，因此延后减quota不改变写出决定；轮末更新仍在下一轮quota guard之前。稳定tie也在循环结束后读取最终quota。

每个执行的radix轮少1次VF调用，不改变hist/扫描/原子操作数，不增加UB或kernel。预期收益取决于真实VF调度成本，尚无设备结果，不保证净收益。9项本地CPU测试通过，其中新增300组融合对照（随机、特殊值、同分、容量边界、窗口、正反序、三种tie策略、quota guard开关），验证精确集合/final_state以及VF数不增加并在执行轮次时减少。关闭所有开关模块AST仍与冻结r1一致。CPU不能验证实际编译或同步。

## 执行

沿用已加载CANN的原yjl容器、现有Python与私人/home/y00937463，确认卡0可用；不修改公共环境或频率。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r6/check_sources.py &&
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r6/run.sh
```

更新或身份检查失败立即停止，保留输出，不reset、不替换身份哈希，不在实验中pull。原r5成功结果已归档，无需重跑。报告包含HEAD/工作文件/HEAD blob/换行归一化SHA，便于诊断版本问题。

## 对照与回传

11个编译配置，默认finish-control与冻结finish-previous生成C++必须一致；compact-control与冻结已启用暂存的compact-previous一致，其他未改阶段冻结哈希核对。保留编译stderr和编译前源码，ThreadSync诊断拒绝计时。

两个独立进程，四输入、四实现（旧默认/previous/new/官方CANN GE TopKV2），独立workspace、同流24顺序、每组50事件，共1600样本；另32组独立profile，保留原CSV和阶段/计算和/间隙/包络。设备与事件倍率分开，不挑最好值。首段残缺仍保守标provisional。CANN接口/tie契约不完全相同，固定N16384/K2048/G1，不等于全契约验收。

完成后原报告和日志保留在/home/y00937463/topk-formal-decode-r6-时间-进程号并复制AAA_Results；两轮成功自动生成gzip/base64分片及manifest，按已验证B2Y手动上传，建议同时上传manifest。失败停止并回传已有日志/报告，不强行重跑或重拆已有文件。全部终端提示ASCII。

若finish设备或完整事件没有稳定净收益，归档否定结果。quota guard的溢出代价、512扫描否定结果及UB暂存收益各自保留；本轮不改默认host。
