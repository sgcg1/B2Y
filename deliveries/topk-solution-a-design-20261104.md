# TopKSelectFwd 方案 A 设计：目标数据流与预期成本

- 日期：2026-11-04
- 范围：算法与执行结构审计结论 → 方案 A（向量直方图 + 阈值选择 + 统一收集）的目标数据流与预期成本
- 状态：设计稿；不包含设备试跑、不创建 PR、不向 issue 评论。以[交付契约](topk-delivery-contract-20261104.md)为验收口径。

## 0. 口径对齐

- 目标仓库 `yyttt6/TileOPs`，PR 基分支 `ascend950`；用户验收 case `ds-v32-topk-decode-b1`（B=1 S=1 S_kv=16384 G=1 topk=2048，index_score fp32）。
- 形式门槛 `r = 最快baseline延迟 / ours延迟 ≥ 0.8`（即 ours ≤ 1.25×baseline）；用户个人目标 1.0×。
- 同一 950PR 环境下原生 GE TopKV2 基线 10.639μs；当前四段实现 57.639μs（0.1846×），其中普通非溢出输入即已慢 5.42×，溢出场景 17×+。
- 结论建立在[溢出算法审计](topk-overflow-algorithm-audit-20261104.md)与两份固定内核源码之上；此处只给出目标，不重复现状证据。

## 1. 三条反向病灶 → 目标机制

| 病灶 | 当前机制 | 方案 A 目标机制 |
| --- | --- | --- |
| ① 归约用原子 | 逐元素 `atomic_add(hist[digit])`（P=4 各 4096 次） | 向量/掩码归约直方图，热路径 0 散布原子 |
| ② 键重复算 + 全窗重扫 | hist + compact 各算一次 coarse；finish 反复算 score_key | 单趟出键并缓存 UB；score_key 仅对候选算一次 |
| ③ finish 单块多轮串行前缀 | P=1 + 8 轮 × ~8 region + 线程0串行前缀 | 多核 + 并行前缀 + 轮次退化为 O(1) 小候选精确化 |

## 2. 方案 A 目标数据流

```
x[16384] fp32, starts/ends[1]        (P 核, P≥4)
   │
   ▼ S1 fused histogram + key cache（多核）
   │   每核扫 N/P 连续块:
   │     SIMD 载入 x[slice]
   │     SIMD 算 coarse = coarse_byte(x)  ─┐ 键只算一次
   │     写 uint8 coarse_cache[slice] 到 UB ◄┘（UB, 不落 GM）
   │     向量/掩码归约直方图 hist_w[256]    ← 0 散布原子
   │   归并 P 个 hist_w → 全局 hist[256]   ← 寄存器/UB 归并, 非 GM
   ▼
   ▼ S2 threshold（并行前缀）
   │   并行前缀 over hist[256] → t(阈值桶), before(>t 数), b(=t 数)
   ▼ meta: t, before, b
   ▼
   ▼ S3 select / collect（多核, 消原子, 复用缓存键）
   │   每核扫 coarse_cache[slice]（UB, 不读 GM x, 不重算键）:
   │     byte > t  → 写 out[本核分段槽位]         ← 分段写, 无原子
   │     byte == t → 收 (index, score) 到边界候选   ← 分段收, 无原子
   ▼ out(已接受) + 边界候选 b 条
   ▼
   ▼ S4 refine boundary（并行, 小候选）
   │   对 b 条候选精确选前 (K-before) 个, 小索引优先(确定性)
   │   无全窗 tie 扫描
   ▼ out[2048], final_state
```

## 3. 逐项成本对比表

当前实测（非溢出 P=4，boundary=894）：hist 11.21 / prepare 5.15 / compact 14.50 / finish 26.77，合计 57.639μs。

| # | 成本项 | 当前实现 | 方案 A 目标 | 变化 |
| --- | --- | --- | --- | --- |
| 1 | GM 读 x（全窗趟数） | 2 趟（hist+compact）= 32768 元素 | 1 趟 = 16384 | −50% |
| 2 | coarse_byte 计算 | 2× 全窗 = 32768 次 | 1× 全窗 = 16384（并缓存） | −50% |
| 3 | score_key 计算 | finish 反复 ≈ 7152 + tie 32768 | 仅候选 b 次（≈894） | ≈−90% |
| 4 | 热路径原子数 | ≈ 39888 | 0（仅归并/前缀均匀归约） | −100% |
| 5 | finish 块并行度 | 1 block / 128 线程 | P block（≥4） | ≥4× |
| 6 | 串行前缀（线程0） | 8 轮 × 2 段 = 16 | 并行前缀 1–2 次 | 大幅降低延迟 |
| 7 | finish region 启动 | ~64 次 SimtVF region | 每段 O(1)，无多轮 | 起停开销归零 |
| 8 | 全窗 tie 重扫 | 2×16384 strided（32768） | 0（候选内确定性 tie） | −100% |
| 9 | GM 往返缓冲 | partial[4,256]+meta[4]+offsets[4,2]+candidate[2048]×2+out | meta[4]+out[2048]（候选留 UB） | 往返最小化 |

## 4. 预算校验（r 门槛）

- 基线 TopKV2 = 10.639μs；r≥0.8 ⇒ ours ≤ 13.3μs；r=1.0 ⇒ ours ≤ 10.64μs。
- 方案 A 预期分解（保守）：

| 段 | 预算 | 依据 |
| --- | --- | --- |
| S1 fuse hist+cache | 3–5 μs | 1 趟 64KB GM 读 + SIMD 直方图/键转换 |
| S2 并行前缀 | 0.5–1 μs | 256 桶 parallel scan |
| S3 select（UB 读缓存键） | 2–4 μs | 纯比较 + 分段写 |
| S4 refine 候选 | 2–4 μs | b≈894 小工作集 |
| 合计 | 8–14 μs | 落进 r≈0.8–1.3 区间 |

结论：r≥0.8 可达区，r=1.0 为紧目标；S1/S3 是否真正降成硬件向量指令决定落点 8μs 还是 14μs。

## 5. P0 前提（先于一切设备试跑）

方案 A 的胜负手是「直方图能否脱离逐元素原子」。已交付最小能力探针：

- `diagnostics/topk-vhist-capability-r1/`（`kernels.py` / `probe.py` / `run.sh` / `README.md`）

探针回答两件事：主仓是否暴露 `vhist`/`histogram`/`cumsum`/`sort` 原语；`hist_bucket_reduce` 生成源码是否无 `atomic`。

三态出口：

- (a) 存在向量/掩码归约直方图降型 → 全量方案 A；
- (b) 只能多 bank 私有直方图 + block 归约 → 目标原子降 P×，落点偏 14μs；
- (c) 归约仍回退成散布原子且无原语 → 方案 A 直方图环节受阻，转分片私有直方图或方案 B（硬件批排序 + 分层归并）。

## 6. 不做的事

- 不在探针返回前按方案 A 修改 TileOPs 内核。
- 不把本表当成验收倍率；正式倍率以维护者协议、baseline 版本与输入匹配后为准。
- 不删除既有 14 项契约、小索引 tie / NaN 全序实现，未经与公共契约核对不擅自放宽。