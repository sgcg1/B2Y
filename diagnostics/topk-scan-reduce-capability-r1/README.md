# Solution-A 后续能力探针：cumsum / reduce_sum 降型判定（20261104-r1）

承接 `topk-vhist-capability-r1`。前一个探针的 `probe-summary.txt` 显示：TileLang 0.1.15
暴露了 `cumsum` 与 `reduce_sum` 原语，但掩码直方图被降成了标量 O(k·N) 重扫，且**没有**
`histogram`/`vhist`/`sort`/`scatter` 原语。

方案 A 剩余路径的核心假设是：finish / compact 可以改写成「向量前缀和（cumsum）+ 向量归约
（reduce_sum）+ 多核并行」来替代「逐元素原子散布 + 线程 0 串行前缀」。本探针就是验证
`cumsum` / `reduce_sum` 究竟是**真向量降级**（可救 finish/compact），还是**标量串行回退**
（救不动）。

不修改 TopK、不产出最终性能、不写共享环境。服务器只需更新 B2Y，不需更新 TileOPs。

## 前置

沿用此前成功的 Python/CANN 环境（已生效 `ASCEND_HOME_PATH`、`bisheng`、`npu-smi`、
`torch`/`torch_npu`/`tilelang`），确认物理卡 0 无竞争任务、工作区干净。

## 一键执行

```bash
cd /home/y00937463/B2Y/diagnostics/topk-scan-reduce-capability-r1
git -C /home/y00937463/B2Y status --short   # 先确认 B2Y 已是最新
bash run.sh
```

或手动指定设备与输出目录：

```bash
TOPK_DEVICE=0 TOPK_HOME=/home/y00937463 bash run.sh
```

四个内核各编译一次，首次各约 1–2 分钟，`PROBE_COMPILE` 打印当前内核名。全流程在 900s 超时内。

## 回传

```bash
cat "$(ls -dt /home/y00937463/runs/scan-reduce-probe-r1-* | head -1)/probe-summary.txt"
```

把这个文本（以及出现报错时的完整 traceback）复制回来。**务必**一并回传该目录下四个 `*.cpp`：
`cumsum_ub_probe.cpp`、`reduce_sum_ub_probe.cpp`、`vreduce_sum_simd_probe.cpp`、
`serial_prefix_ctrl.cpp`。判定主要靠读这些 C++ 源码。

## 读结果要点

四个内核互为对照：

| 内核 | 角色 | 若正确 | 若回退 |
|---|---|---|---|
| `vreduce_sum_simd_probe` | 正向对照（frag 级 `T.vreduce_sum`）| 应出现 `npu.reduce`/向量 reduce | — |
| `reduce_sum_ub_probe` | buffer 级 `T.reduce_sum` | 出现向量 reduce 指令 | `for` 逐元素累加 |
| `cumsum_ub_probe` | buffer 级 `T.cumsum` 前缀和 | 出现向量 scan/prefix 指令 | `threadIdx.x == 0` 里串行 `for` |
| `serial_prefix_ctrl` | 负向对照（线程 0 串行前缀）| — | 一定是线程 0 串行 `for` |

关键判据（读 `.cpp`）：

1. **`cumsum_ub_probe.cpp`**：如果出现 `asc_*scan*` / `asc_*cumsum*` / 向量累计指令，则 cumsum
   真向量化，finish 的串行前缀有救；如果出现 `if (threadIdx.x == 0)` 里套完整 `for` 串行累加，
   则 cumsum 是糖衣，救不了。
2. **`reduce_sum_ub_probe.cpp` 与 `vreduce_sum_simd_probe.cpp`**：出现 `npu.reduce`/`asc_reduce`
   即向量归约（指向 NBA 归约单元）；出现 `for` 逐元素 `+=` 即标量。
3. **`serial_prefix_ctrl`** 是标量基线，用来和 `cumsum_ub_probe` 的源码直接对比——两者若结构
   雷同（都是线程 0 串行 `for`），说明 cumsum 没有独立的向量前缀和降级路径。

`cross_check` 语义说明：

- `serial_prefix_matches_reference`：负向对照内核输出应等于 `torch.cumsum`（inclusive）。
- `reduce_sum_ub_probe/vreduce_sum_simd_probe_matches_reference`：应等于 `x.sum(dim=1)`。
- `cumsum_semantics`：inclusive / exclusive / unmatched——用于确认 cumsum 的前缀和语义，
  与降型无关。

`status=completed` 仅表示采集完成，最终结论由人基于上述判据与 `.cpp` 源码给出。