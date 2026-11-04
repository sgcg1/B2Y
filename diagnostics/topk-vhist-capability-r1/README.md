# Solution-A P0 能力探针：直方图降型判定（20261104-r1）

回答前一阶段算法审计遗留的两个阻塞问题：在服务器当前 TileLang 主线构建上，

1. `tilelang.ascend.language` 暴露了哪些 histogram / scan / sort / atomic 相关原语；
2. 256 桶直方图究竟被降成「逐元素原子散布」还是「向量/掩码归约」——这决定方案 A（向量直方图 + 阈值选择 + 统一收集）是否可行。

不修改 TopK、不产出最终性能、不写入共享环境。服务器只需更新 B2Y，不需要更新 TileOPs。

## 前置

沿用此前成功的 Python/CANN 环境（已生效 `ASCEND_HOME_PATH`、`bisheng`、`npu-smi`、`torch`/`torch_npu`/`tilelang`），确认获准物理卡 0 无竞争任务、工作区干净。

## 一键执行

```bash
cd /home/y00937463/B2Y/diagnostics/topk-vhist-capability-r1
git -C /home/y00937463/B2Y status --short   # 先确认 B2Y 已是最新
bash run.sh
```

或手动指定设备与输出目录：

```bash
TOPK_DEVICE=0 TOPK_HOME=/home/y00937463 bash run.sh
```

首次编译两种配置可能各需 1–2 分钟，`PROBE_COMPILE` 打印当前内核名。全流程在 900s 超时内。

## 回传

运行结束（或正常 Python 报错）后：

```bash
cat "$(ls -dt /home/y00937463/runs/vhist-probe-r1-* | head -1)/probe-summary.txt"
```

把这个文本（以及出现报错时的完整 traceback）复制回来。可选回传该目录下两个 `*.cpp`（`hist_atomic_scatter.cpp`、`hist_bucket_reduce.cpp`），用于二次确认降型细节。

## 读结果要点

- `introspection.matching_exports`：看是否存在 `vhist`/`histogram`/`cumsum`/`sort` 等原语（这是方案 A 直接依赖项）。
- `cases.hist_atomic_scatter.source_markers`：预期含 `atomic`（对照，当前慢路径）。
- `cases.hist_bucket_reduce.source_markers` / `has_atomic_marker`：**关键判据**——若 bucket_reduce 生成源码里没有 `atomic`，说明存在原子无关的 SIMD 直方图降型路径，方案 A 可推进；若仍出现 `atomic`，则归约被回退成散布原子，方案 A 的直方图环节受阻，需转分片私有直方图或方案 B。
- `cross_check`：两个内核直方图应一致且 `both_sum_to_n=true`（证明语义正确，与降型无关）。

`status=completed` 仅表示采集完成，最终结论由人基于上述判据给出，不自动判定方案 A 可行与否。