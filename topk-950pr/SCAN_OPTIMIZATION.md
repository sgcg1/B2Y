# v0.1.4-scan-r1：桶扫描候选的现场验证

本轮依据交接文档4.2.2第4项，将256桶单线程扫描改为16×16分组并行扫描，另加256桶并行阈值判定。保持H128、worker策略、FP32完整键、缓存溢出重扫及同分选择规则。代码在个人fork，辅助工具在B2Y；仍使用已有yjl及容器Python，不要求重建或升级环境。

**这是待NPU验证的优化候选，没有实测加速结论，未发布正式v0.1.4标签。** 本地通过的CPU算术检查不能证明设备编译或同步正确。新增1088字节显式UB scratch，实际编译资源需现场核查。出现编译错误、unsafe ThreadSync/race警告或结果不一致时停止，保留原始日志，不继续大规模测量。

## 1. 更新两个仓库

宿主机进入容器；已经在yjl内就跳过：

```bash
docker exec -it yjl /bin/bash
```

以下均在容器内。先确认没有本轮任务运行，并检查两仓工作区：

```bash
git -C /home/y00937463/TileOPs status --short
git -C /home/y00937463/B2Y status --short
```

有修改时先保存，不使用reset/clean覆盖。确认工作区干净、两仓均在main后，逐条更新：

```bash
git -C /home/y00937463/TileOPs pull --ff-only origin main
git -C /home/y00937463/TileOPs fetch origin --tags
git -C /home/y00937463/B2Y pull --ff-only origin main
git -C /home/y00937463/TileOPs log -1 --oneline
git -C /home/y00937463/B2Y log -1 --oneline
```

仅更新B2Y不会改变内核。不要修改项目依赖或重新pip install项目。

## 2. 新建一轮，并做CPU算术检查

沿用此前成功的Python和实际CANN toolkit环境。设备号与SOC按获准分配修改，以下默认卡0：

```bash
export TOPK_ROOT=/home/y00937463
export TOPK_REPO="$TOPK_ROOT/TileOPs"
export TOPK_DEVICE=0
export TOPK_PYTHON="$(command -v python3)"
export TOPK_SOC=Ascend950PR_9579
export EVIDENCE="$TOPK_ROOT/runs/scan-r1-$(date +%Y%m%d-%H%M%S)"
source "$TOPK_ROOT/B2Y/topk-950pr/env.sh"
```

```bash
"$TOPK_PYTHON" "$TOPK_REPO/tests/kernels/test_topk_select_ascend_scan.py"
```

预期5项CPU检查通过；这不会执行NPU kernel。检查的是实际kernel扫描AST的整数算术，不是完整设备模拟。

## 3. 预检与14项设备契约

逐条执行，上一条成功再执行下一条：

```bash
bash "$TOPK_TOOLS/run.sh" preflight
```

```bash
bash "$TOPK_TOOLS/run.sh" test
```

必须14 passed、无skip/error/failure。它们验证当前host默认的并行扫描H128路径；此前旧源码的通过不能替代本轮结果。`project_torch_requirement_met=false` 表示走2.10兼容性实测路线，不等于项目整体支持2.10。

## 4. 两轮同进程事件对照

```bash
bash "$TOPK_TOOLS/run.sh" control 1
```

```bash
bash "$TOPK_TOOLS/run.sh" control 2
```

每轮比较以下6项，采用同一输入、预分配输出、50次事件采样，交替正反序执行：

| 名称 | 含义 |
| --- | --- |
| v0.1.0 / v0.1.2 | 历史控制，源码取自已有标签 |
| v0.1.4-before-scan | 优化前保存点49aaea36，内核与用户回传的252ad607相同 |
| candidate-h128 | 新候选，分组并行扫描，H128；当前host默认 |
| candidate-h256 | 分组并行扫描，H256；仅诊断，不改host默认 |
| candidate-serial-h128 | 同一新kernel中关闭PARALLEL_SCAN，保留串行256桶扫描，做消融对照 |

控制会检查随机有限输入的范围、唯一性、阈值及选中集合一致；它不代替第3步特殊值契约。每轮的control.json记录原始样本、中位数、引用与源码哈希。

`scan_event_speedup_vs_previous_h128` = 旧v0.1.4事件中位数 / 新H128事件中位数。大于1才更快。`scan_event_speedup_vs_serial_ablation_h128` 用候选串行路径作分子，用于隔离扫描变化。两者均为设备事件比，不是CANN纯内核倍数。

**两轮没有稳定改善或任一路径错误时先停在这里。** 回传允许披露的6项中位数和首个错误；不要继续放大到完整Prefill，也不要以一次最小值决定默认。

## 5. 小规格正式测量

两轮对照通过后，沿用本轮EVIDENCE逐条执行：

```bash
bash "$TOPK_TOOLS/run.sh" clock
bash "$TOPK_TOOLS/run.sh" frequency
bash "$TOPK_TOOLS/run.sh" cann-build decode
bash "$TOPK_TOOLS/run.sh" cann-measure decode
bash "$TOPK_TOOLS/run.sh" measure decode
bash "$TOPK_TOOLS/run.sh" summary decode
```

本轮输出将包含 `parallel_scan: true`。仍按同轮CANN内核/TileLang内核中位数计算 `performance_x_cann`，不复用以前的9.2215μs当成本轮基线。clock/frequency只做诊断，不调频。

## 6. 最后再扩大规格

Decode正确、重复对照稳定且测量无异常后，按START_HERE.md第6步跑128行诊断和完整Prefill两组。四组均需本轮同一源码、50事件/50有效profiling记录。完整Prefill输入约8GiB，不以小规模线性外推代替实测。

任一主规格回退都保留为试验，尚不能接受最终v0.1.4。新增同步开销可能抵消串行扫描减少；若回退，后续根据同轮数据决定恢复旧默认或继续实验，不伪造成功结论。

原始证据留在现场。可按RESULTS_TEMPLATE.md仅回传允许出域的摘要；本轮优先需要14项结果、两轮控制中位数和Decode的同轮CANN/候选内核中位数。
