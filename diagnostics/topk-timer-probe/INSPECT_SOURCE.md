# probe1源代码顺序检查失败：先导出已有源码

本次状态：failed，阶段compile:r1-timed，错误Counter/fence source order changed。此错误来自Python源代码检查器，不能直接等同于“编译器重排”或“NPU计数器不可用”。

检查器假设每个标记的第一个出现位置是定义，后两个位置是调用，再比较全文件字符偏移。它未解析函数作用域，实际生成代码缺失时不足以确定根因。当前不改变断言或kernel，也不重跑探针。

## 1. 更新B2Y

在已有yjl容器内，确认工作区干净后按根README更新B2Y。不更新TileOPs，不删除原探针目录，不修改原.cpp文件。新工具只读取已有文件，生成一份新的源码导出文本，不编译、不导入torch/TileLang、不运行NPU。

## 2. 指定原来失败的目录

如果仍在上次终端，先查看原变量：

```bash
printf '%s\n' "${TOPK_TIMER_RUN:-未设置}"
```

它应是先前失败探针的完整目录，而不是本次新建的目录。若已换终端或变量未设置，先列出目录：

```bash
ls -dt /home/y00937463/runs/timer-probe-*
```

根据先前运行时间选择正确目录，并将下一条中的占位路径改为实际路径：

```bash
TOPK_TIMER_RUN="/home/y00937463/runs/这里替换为原失败探针目录名"
cat "$TOPK_TIMER_RUN/probe-summary.txt"
```

确认summary中的version为20261102-probe1、stage为compile:r1-timed、error为Counter/fence source order changed后继续。变量已正确设置时不用重复赋值。

## 3. 导出一份文本

```bash
TOPK_TIMER_INSPECTION="$TOPK_TIMER_RUN/source-inspection-$(date +%Y%m%d-%H%M%S).txt"
"${TOPK_PYTHON:-python3}" \
  /home/y00937463/B2Y/diagnostics/topk-timer-probe/inspect_source.py \
  --run "$TOPK_TIMER_RUN" --output "$TOPK_TIMER_INSPECTION"
```

成功后：

```bash
cat "$TOPK_TIMER_INSPECTION"
```

将全部文本复制到B2Y的实验结果收件文件或聊天中。若文本太长可分段发送并标注顺序。工具拒绝覆盖已有导出文件；重新执行时使用新的时间戳。

导出包含原失败摘要、三种r1源码的哈希与所有标记行，以及带行号的完整r1-timed.cpp。它保留定义/调用的歧义，不自动接受任何顺序。原报告没有记录该.cpp哈希，因此这是当前目录的源码快照；若文件曾被手工改动，请注明。

## 后续判断

- 若实际调用顺序正确而检查器误识别定义/作用域，再针对真实代码修复检查器。
- 若时钟读取确实被移出目标区间，先修复插桩依赖或边界，不能删除检查强行测量。
- 若证据仍不足，保留不确定状态；不凭正数时间戳或工作量斜率宣布完成同步可靠。

回传后按独立实验ID保存原始文本与哈希，和这次失败记录关联。原始结果不覆盖，分析结论另行更新。
