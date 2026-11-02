# control 索引校验失败：只定位，不测性能

现场回传14项契约测试通过（231.59秒），随后旧control脚本在没有版本标识的索引范围断言处失败。旧脚本先运行全部实现，再从v0.1.0开始校验，因此该断言首先观察到的是v0.1.0输出；尚不能判断它单独执行就错误，还是后续执行影响了其输出。也不能只凭14项通过排除Decode特定形状或H256的错误。

新版工具不修改内核，增加以下检查：

- 编译、执行、校验都打印版本标识。
- 每个实现单次执行后立即校验，20次warmup后再次校验；所有版本运行完再回查，区分独立失败和后续输出变化。
- 输出预填-1，并与CPU稳定排序得到的独立参考集合比较，不把历史初版当成正确性参考。
- validation.json记录版本、阶段、越界数量及最多8个越界值，另检查重复索引与错误集合。此输入是脚本固定种子的随机有限FP32分数。
- 正式control仍遇错即停。control-diagnose检查所有版本的结果，不输出任何性能数据；发现错误会以非零状态退出。

## 后续定位结果

逐版本输出已确认本轮仅candidate-h256失败，single_call即有253个16384哨兵，after_all_versions相同；其余实现各阶段通过。当前r8已禁止此配置，控制范围缩为H128，CONTROL_EXCLUDED及JSON保存H256拒绝状态。内核也加了保护，因此需要按SCAN_OPTIMIZATION.md更新两个仓库，而不是只更新B2Y。此前仅从旧脚本顺序推断历史初版失败的说法不构成根因结论。

以下是仅诊断工具更新的通用步骤；本次r8请优先按SCAN_OPTIMIZATION.md执行新源码完整流程。若只需检查当前允许的5项，可在新一轮preflight后运行control-diagnose；它不会重新执行被禁止的H256组合，也不表示H256已修复。

## 容器内执行

本次r8先按SCAN_OPTIMIZATION.md更新两个仓库；仅后续纯诊断工具更新时可只更新B2Y。先保留原失败实验，确认B2Y工作区干净后更新：

```bash
git -C /home/y00937463/B2Y status --short
```

```bash
git -C /home/y00937463/B2Y pull --ff-only origin main
```

工具已变化，旧EVIDENCE里的身份记录不能继续复用。新建诊断轮次，使用此前同一个容器Python和CANN环境：

```bash
export TOPK_ROOT=/home/y00937463
export TOPK_REPO="$TOPK_ROOT/TileOPs"
export TOPK_DEVICE=0
export TOPK_PYTHON="$(command -v python3)"
export TOPK_SOC=Ascend950PR_9579
export EVIDENCE="$TOPK_ROOT/runs/control-diagnostic-$(date +%Y%m%d-%H%M%S)"
source "$TOPK_ROOT/B2Y/topk-950pr/env.sh"
```

设备与SOC按实际分配调整，CANN环境沿用先前成功设置。先执行：

```bash
bash "$TOPK_TOOLS/run.sh" preflight
```

预检成功后执行本次诊断；此时不要求先重跑14项测试：

```bash
bash "$TOPK_TOOLS/run.sh" control-diagnose
```

重点看 `CONTROL_CHECK` 和末尾 `CONTROL_DIAGNOSTIC_FAILED_VERSIONS`。有错误时的非零退出是诊断结果，不表示脚本忽略或接受了错误。运行时/编译器异常仍立即停止，日志中的CONTROL_COMPILE或CONTROL_RUN标识用于定位。

结果保存在本轮 `$EVIDENCE/control-diagnostic/validation.json`，终端日志在 `$EVIDENCE/control-diagnostic.log`。按当地要求，只回传允许披露的首个失败CONTROL_CHECK及最终失败版本列表即可，不要求导出原始分数或整份环境信息。

例如单次执行即出现 `v0.1.0 / out_of_bounds`，说明历史路径自身在该轮失败；若单次及warmup都通过、仅after_all_versions失败，则需要继续排查输出在后续执行期间变化的原因。H128、H256和串行消融的失败分别记录，不混为同一个候选结论。

本轮诊断不生成control.json、不计算加速比，不可替代正式control两轮、14项契约或CANN测量。根因定位、修复后，再用完整正式流程验收；不要删除失败记录或通过跳过错误实现制造通过结论。
