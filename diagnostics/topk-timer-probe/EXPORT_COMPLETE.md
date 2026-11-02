# Probe2已完成后的只读导出

当前下一步：导出刚刚完成的probe2原始样本和生成源码。已有摘要的尺度检查通过，但短区间差分仍需解释；[本轮分析与归档](../../experiments/topk/20261102-timer-probe2-summary/analysis.md)记录了结论和限制。无需重新运行probe.py、编译内核或重跑TopK测试。

## 1. 在已有yjl容器内更新B2Y

沿用此前成功运行的环境。若已经在容器内，直接执行：

```bash
git -C /home/y00937463/B2Y status --short
```

工作区干净、没有实验运行时：

```bash
git -C /home/y00937463/B2Y pull --ff-only origin main
```

有本地修改先保存差异，不用reset/clean覆盖。此次只新增导出材料，不更新TileOPs、torch、TileLang或CANN。

## 2. 选择刚刚完成的原运行目录

如果仍在原终端，先检查变量及原报告：

```bash
printf 'TOPK_TIMER_RUN=%s\n' "${TOPK_TIMER_RUN:-未设置}"
test -n "${TOPK_TIMER_RUN:-}" && ls -l "$TOPK_TIMER_RUN/probe-report.json"
```

如果变量丢失，用下面命令列出历史目录：

```bash
ls -dt /home/y00937463/runs/timer-probe2-*
```

然后仅在变量丢失或指错时，把下方“实际时间戳”替换为本次成功目录的真实名称：

```bash
TOPK_TIMER_RUN="/home/y00937463/runs/timer-probe2-实际时间戳"
```

不要选择probe1目录，不要新建或清空运行目录。导出器要求版本为20261102-probe2、状态completed、10个配置及相应50次样本完整。

## 3. 生成一份可复制的文本

```bash
TOPK_TIMER_EXPORT="$TOPK_TIMER_RUN/complete-evidence-$(date +%Y%m%d-%H%M%S).txt"
"${TOPK_PYTHON:-python3}" -B \
  /home/y00937463/B2Y/diagnostics/topk-timer-probe/export_complete.py \
  --run "$TOPK_TIMER_RUN" --output "$TOPK_TIMER_EXPORT"
```

成功时显示EXPORT_OUTPUT及字节数。只读取原目录中已存在的probe-report.json、10组original/postproc源码和API源码；导出前按原报告SHA核对源码。API源码若与上述之一相同只记引用，减少重复文本。每份收录文件均含原UTF-8文本、字节数及SHA，可按字节还原。不会导入torch/TileLang或访问NPU，只新建一个文本，不覆盖已有文件。

如果提示找不到文件、SHA不一致或样本不完整，保留目录，回传完整错误；不要修改源码、报告或重跑来绕过检查。该工具没有改变计时方案或自动接受结果。

## 4. 回传全部文本

```bash
cat "$TOPK_TIMER_EXPORT"
```

把从第一个`{`到最后一个`}`的全部内容复制回来，或提交B2Y根目录“实验结果”收件文件；注意终端滚动区不要截断。无需逐个传文件。文本略长，因为包含500个事件样本、200个counter样本及20份前后处理源码；这是检查分布和插桩边界所需的原证据。

本轮资料以独立实验ID保存，不覆盖此前probe1、H128或本轮已收摘要。收到后先复算中位数、离散度和顺序趋势，检查实际源码，再决定真实TopK阶段插桩范围。
