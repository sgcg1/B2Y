# r5源码身份不匹配恢复

本次172510失败停在provenance，未编译、未运行NPU、没有性能数据。日志未包含服务器HEAD和实际SHA，不能确定原因，也不能认为UB暂存编译失败。保留原报告，不重跑r4、不reset、不关闭哈希检查。

先在原容器运行以下步骤；任一步失败停止，保留终端输出。fetch与快进合并不会丢弃本地提交或强制覆盖修改；若有冲突/分叉需另行处理。

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs fetch origin main &&
git -C /home/y00937463/TileOPs merge --ff-only origin/main &&
/usr/local/python3.12.14/bin/python3 /home/y00937463/B2Y/diagnostics/topk-formal-decode-r5/check_sources.py
```

检查会输出HEAD、候选是否祖先、工作区状态，以及期望/工作文件/HEAD文件/换行归一化SHA。不会输出远端URL或凭据，不修改源码。如仍不匹配，把终端输出保存为B2Y小文本回传；不要自行替换identity中的哈希。正常时打印SOURCE_CHECK_PASSED，然后才执行：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r5/run.sh
```

新报告也内嵌source_checks与HEAD，之后失败不再丢失这些诊断信息。算法、候选提交9a5087dd及测量配置均未改变。新运行使用新目录，已有结果保留。
