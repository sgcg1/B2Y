# FP4 GM→L1 转置修复代码评审讲稿

日期：2026-10-27。建议讲解时长：8～10 分钟。

评审对象：[FP4 PR #9](https://github.com/yangsichan/tilelang-asc/pull/9)。本文固定对应处理冲突后的提交 `5a5fb725dbe4d3eac52c845e6f7ab7fba3d5c6b2`，相对目标基线 `87605f43a2ba1012ff002eca1712d2ce3f629d29` 说明修改，不代表其他仓库或分支的实现情况。

## 1. 开场：这次修复解决什么问题

> 这次修改解决的是 Ascend 上 FP4 GM→L1 转置复制静默产生错误结果的问题。
>
> 用户调用 `T.copy(src, dst_l1, transpose=True)` 后，程序可以编译和运行，但 L1 中的 FP4 元素顺序不正确，最终导致 GEMM 结果错误。
>
> 修改涉及 7 个已有文件，新增 493 行、删除 2 行。其中三个编译器文件新增 160 行，其余主要是回归测试和接口文档。行数采用 Git 文本统计口径，包含空行、注释和跨行表达式。

## 2. 根因：字节转置不等于 FP4 元素转置

> FP4 每个元素占四位，一个字节包含两个元素。原来的实现把 FP4 当作字节存储，再使用字节级 DN2NZ 搬运。
>
> 普通复制可以保留这种打包关系，但转置要求重新组合来自不同位置的四位编码，不能只搬动整个字节。

下面数字代表四位编码，不是浮点数值。小矩阵只用于解释打包关系，不表示本实现支持该尺寸。

```text
原矩阵：          转置后：
1  2             1  3
3  4             2  4

原打包字节：     正确的转置结果：
0x21、0x43       0x31、0x42
```

> 同时要区分两个需求：
>
> 第一种只是 GEMM 数学上需要 `A.T` 或 `B.T`，可以保持 GM→L1 原始朝向，使用已有的 L1→L0 硬件转置加载。这条路径没有重新实现，主要补充了测试。
>
> 第二种要求 L1 中的数据本身已经转置，这是本次新增的功能。

## 3. 整体方案

> 本次没有新增独立 pass，而是在已有的 `InsertNd2Nz` 变换中生成一段替代程序，在自动调度之前完成改写。

```text
GM 中的打包 FP4
       ↓ SIMT 读取源字节
寄存器中拆分、重新组合四位编码
       ↓
UB：保存已转置、按 NZ 布局排列的字节
       ↓ UB→L1 DMA
L1：供 Cube 加载和计算
```

> 这里没有先调用一条独立的 GM→UB DMA 搬入整块原始数据。SIMT 直接读取 GM，重排后把结果写入 UB。
>
> 整个过程操作原始四位编码，不经过浮点数值转换，因此不会引入舍入，也可以保留正零、负零等位模式。

## 4. 每个文件分别改了什么

以下源码链接固定到本次评审提交。

| 文件 | 修改量 | 主要职责 |
| --- | ---: | --- |
| [insert_nd2nz.cc](https://github.com/yangsichan/tilelang-asc/blob/5a5fb725dbe4d3eac52c845e6f7ab7fba3d5c6b2/src/ascend/transform/insert_nd2nz.cc#L535) | +146 | 生成 FP4 重排及 UB→L1 搬运 |
| [codegen_ascend.cc](https://github.com/yangsichan/tilelang-asc/blob/5a5fb725dbe4d3eac52c845e6f7ab7fba3d5c6b2/src/ascend/codegen/codegen_ascend.cc#L1612) | +9 | 限定 AIV0 执行目标 L1 写入 |
| [copy.cc](https://github.com/yangsichan/tilelang-asc/blob/5a5fb725dbe4d3eac52c845e6f7ab7fba3d5c6b2/src/ascend/op/copy.cc#L606) | +5 | 拦截未经改写的错误 DMA 转置 |
| [test_tilelang_ascend_dma_copy.py](https://github.com/yangsichan/tilelang-asc/blob/5a5fb725dbe4d3eac52c845e6f7ab7fba3d5c6b2/testing/ascend/language/test_tilelang_ascend_dma_copy.py) | +181 | 设备数值、打包字节及 L1 重用测试 |
| [test_ascend_insert_nd2nz.py](https://github.com/yangsichan/tilelang-asc/blob/5a5fb725dbe4d3eac52c845e6f7ab7fba3d5c6b2/testing/ascend/transform/test_ascend_insert_nd2nz.py#L278) | +135 / −2 | 改写、索引、边界和诊断测试 |
| [test_ascend_lower_copy.py](https://github.com/yangsichan/tilelang-asc/blob/5a5fb725dbe4d3eac52c845e6f7ab7fba3d5c6b2/testing/ascend/transform/test_ascend_lower_copy.py#L74) | +9 | DMA 兜底保护和 L0 几何条件测试 |
| [copy_op.py](https://github.com/yangsichan/tilelang-asc/blob/5a5fb725dbe4d3eac52c845e6f7ab7fba3d5c6b2/tilelang/ascend/language/copy_op.py#L278) | +8 | 说明接口支持范围，无新增执行逻辑 |

## 5. 核心实现：insert_nd2nz.cc

以下 C++ 主要是在编译时构造 IR，即生成将来在 NPU 上运行的程序。`BufferLoad`、`BufferStore` 等不是编译器当场搬运 NPU 数据。

### 5.1 识别需要改写的操作

> 新增的 `RewriteFP4Transpose` 只处理 GM→L1、源类型为 FP4 E2M1、并且请求转置的复制。其他操作返回空，继续走已有流程。

```cpp
if (!IsGlobalBuffer(copy.src) || !IsL1Buffer(copy.dst) ||
    !copy.src->dtype.is_float4_e2m1fn() || !copy.transpose)
  return std::nullopt;
```

### 5.2 检查实现前提

> 当前要求源和目标类型一致，都是完整、静态二维缓冲区，形状互为转置，区域和元素偏移为零；源是紧凑存储，且没有本实现排除的源物理布局，目标是标准 NZ 布局。
>
> 目标行数必须是 16 的倍数，列数必须是 64 的倍数。执行方式要求普通 `T.Kernel` 的自动调度。
>
> 这些条件是后续地址公式成立的前提。不满足时明确报错，而不是尝试生成未经验证的搬运。

编译变换还记录 PTO 目标和显式执行范围，拒绝本实现未适配的情况。访问嵌套范围时，采用“进入时保存、内部更新、退出时恢复”的状态管理方式。

### 5.3 建立源字节视图和 UB 临时缓冲区

> 源缓冲区通过写时复制建立一维 `uint8` 描述，仍然访问原来的 GM 地址，没有复制 GM 数据，也没有进行数值转换。
>
> UB 临时空间大小为 `rows × cols / 2` 字节，正好容纳完整的打包 FP4 结果。

```cpp
PrimExpr byte_count = Integer(rows * cols / 2);
```

源视图改为一维紧凑字节数组，清除原二维步长，并将已证明为零的元素偏移规范成零。UB 缓冲区使用 `shared.dyn` 存储范围，加入当前块的待分配列表，交给已有分配逻辑处理。

### 5.4 生成 SIMT 重排

> 使用 128 个线程，每个工作项读取两个源字节，将四个 FP4 编码重新组合成两个目标字节。两个源字节的高低四位都会被使用，避免重复读取。

核心位运算可用下面的普通 C++ 伪代码解释：

```cpp
low  = (first_byte & 0x0F) | ((second_byte & 0x0F) << 4);
high = (first_byte >> 4)   | ((second_byte >> 4) << 4);
```

> `low` 对应转置后的一行，`high` 对应相邻的下一行。两个结果直接按 NZ 地址写入 UB，不需要再做一次布局转换。

实际编译器使用 `bitwise_and`、`bitwise_or`、`left_shift`、`right_shift` 构造等价 IR。源字节绑定为 `uint32` 临时变量，复用两次；写入 UB 时再收回为 `uint8`。

若评审者追问索引，可展示以下公式，除法均为整数除法：

```text
R = 目标行数
C = 目标列数
源形状 = (C, R)
i = 工作项编号 = chunk * 128 + thread

row       = (i / 32) % (R / 2)
col       = (i / (R * 16)) * 64 + (i % 32) * 2
dst_index = (i / 32) * 64 + i % 32
```

> 源矩阵每行占 `R/2` 字节，读取地址分别是：

```cpp
source[col       * (R / 2) + row]
source[(col + 1) * (R / 2) + row]
```

> 这相当于从相邻两条源行中，读取同一对列元素。重组后得到目标相邻两行的数据。
>
> 输出位置分别为 `dst_index` 和 `dst_index+32`。在这里采用的 FP4 NZ 排列中，一个 64 元素的行片段占 32 字节，因此加 32 对应同一列片段的下一行。
>
> 以 32 个工作项为一组，使目标写入地址连续。

编译器将这些操作包装成串行 `chunk` 循环、SIMT VF 属性和线程范围：x 维度 128，y/z 维度各 1，最后构造 `SIMT_VF` 块供后续阶段识别。

### 5.5 生成 UB→L1 搬运

> UB 中已经是完整的转置后 NZ 字节序，因此只需要一次连续搬运，长度使用 `byte_count/32` 个 32 字节块表示，源和目标间隔都为零。
>
> 最后返回“SIMT 重排”和“UB→L1 搬运”两个语句，让后续自动调度分析依赖并安排同步。

仅有源码顺序不能保证跨流水线完成关系，仍需要后续同步处理。

## 6. 唯一写入者：codegen_ascend.cc

> 一个 Cube 对应两个 AIV，两个 AIV 各自拥有 UB，但这里写入的是同一个目标 L1 区域。
>
> 当前两个 AIV 都可能执行重排，各自在自己的 UB 中得到结果，但只需要其中一个把结果写入 L1。

因此，改写时添加内部标记：

```cpp
{{"single_aiv", Integer(1)}}
```

代码生成阶段检查该标记是否存在，输出：

```cpp
if (asc_get_sub_block_id() == 0) {
    asc_copy_ub2l1(...);
}
```

> 这 9 行不实现转置，也不增加另一条搬运，而是让 AIV0 成为唯一写入者，避免两个 AIV 重复写入同一片 L1 地址。
>
> 条件只包住搬运指令，外围同步没有一起包进去，两个 AIV 仍参与生成的同步流程。

内部 UB→L1 操作参数中的 `sub_blockid=0` 本身不完成此限制；当前生成路径不把该参数传给 `asc_copy_ub2l1`，真正的限制来自标记生成的条件。

## 7. 最后一道保护：copy.cc

> 前面的改写负责生成正确实现；这里负责保证没被改写的 FP4 转置不会落回错误的字节 DMA。
>
> 如果它进入普通 FP4 DMA 分支时仍然需要转置，就抛出明确错误。

```cpp
TVM_FFI_CHECK(!needs_transpose, ValueError)
    << "... byte DN2NZ cannot transpose individual FP4 elements ...";
```

> 这是最后一道保护。否则某条未覆盖的编译路径绕过改写后，仍可能复现原来的静默错误。

## 8. 三个测试文件和接口文档

> 测试从三个层次覆盖，而不只看最终 GEMM 是否正确。
>
> 第一层是设备数值，位于 `test_tilelang_ascend_dma_copy.py`。覆盖普通搬运、A/B 实际转置、A/B 的 L1→L0 数学转置，以及随机 MX 缩放因子。`64×64` 恒等矩阵探针要求精确匹配。
>
> 同一文件还检查 L1 中的打包字节，覆盖全部 256 种字节值，避免浮点数值相等掩盖编码变化；用三个不同输入先后写入同一块 L1，检查旧数据残留。
>
> 第二层是 `test_ascend_insert_nd2nz.py`。在 CPU 上执行生成的地址和位运算，验证读写没有越界、输出没有遗漏或重复，并与独立的解包、转置、重新打包参考结果比较。覆盖 `48×192` 对齐但非二次幂的尺寸，以及不支持情况的诊断。
>
> 第三层是 `test_ascend_lower_copy.py`。验证未改写的 FP4 DMA 转置会报错，并补充 L1→L0 转置加载的合法、非法几何条件。
>
> `copy_op.py` 只补充接口文档，说明实际转置的实现方式、支持范围，以及数学转置的替代路径，没有新增 Python 执行逻辑。

需要主动说明：流水线用例使用相同输入，负责检查循环和调度集成；不同输入重用 L1 由另一组静态复制用例覆盖。不能描述为已经验证所有不同输入的流水线竞态或保证执行了双缓冲版本切换。

## 9. 验证结果与当前边界

> 2026-10-26 合入最新 `main`、解决 FP4/FP8 测试冲突后，重新完成了构建：
>
> - 原始 issue 两个随机种子均为 0/4096 错误，最大误差为 0。
> - FP4 编译专项 28 项通过。
> - FP4/FP8 设备专项 32 项通过。
> - 六文件相关回归 264 项通过、67 项未选，6 条既有 `ascend` pytest 标记警告。
>
> 专项包含在较大回归中，不叠加计数。Ruff 和 diff 检查通过；完整 pre-commit 因钩子下载网络阻塞未完成，已记录。上述结果不代表全仓测试全部通过。

验证环境：Linux x86_64 / Ubuntu 20.04，Ascend950PR_9579 卡0，Python 3.11.15，PyTorch 2.14.0+cpu，Torch-NPU 2.14.0，CANN toolkit 9.3.0 / V100R001C12B140，runtime/Bisheng 组件元数据 9.2.0（20261009），Bisheng clang 15.0.5，driver 25.7.0，执行后端 `tvm_ffi`。使用隔离源码/构建及独立 JIT 缓存，并确认实际加载路径。

> 当前不支持 PTO、子区域、动态或非紧凑存储，以及源物理布局、显式 core/VF、MixedKernel、Task/PerCoreTask 和 `l2_cache_ctrl`。这些情况明确报错。这是本次实现范围，不代表硬件永远无法实现。
>
> 实际转置增加了 SIMT 重排、UB 临时空间和 UB→L1 搬运成本。只有 GEMM 数学转置需求时，应优先使用已有 L1→L0 硬件转置加载。

## 10. 提交组织与性能数据边界

| 提交 | 内容 |
| --- | --- |
| `b31d33c3` | 阻止错误字节 DMA 转置，覆盖已有 L1→L0 数学转置路径 |
| `620e368e` | 实现 FP4 元素转置、UB 中转、单 AIV 写入、诊断和回归测试 |
| `acda78bf` | 复用源字节的高低四位，减少重复加载和索引工作 |
| `5a5fb725` | 合入 `main` 的 E5M2 修复，保留 FP4/FP8 两组测试，未修改 FP4 编译器实现 |

> 前三个是功能和优化提交，第四个是处理目标分支更新的普通合并提交，没有强制推送重写前三条记录。
>
> 此前约 6%～39% 的性能改善，是重基前两版正确实现之间的单核 GEMM 历史测量，不是应用端到端收益，也没有与错误实现作有效性能比较。处理合并冲突后没有重新测量性能。

## 11. 请评审者重点检查的内容

> 这次希望重点 review 四部分：
>
> 1. 源读取地址、四位重组和 NZ 输出地址是否正确。
> 2. 源字节视图、UB 容量和 DMA 搬运长度是否一致。
> 3. AIV0 唯一写入与外围同步是否安全。
> 4. 支持条件是否足以保证算法成立，未改写路径是否可靠报错。

## 12. 可能被问到的问题

### 为什么不能直接使用原来的 DMA 转置？

因为 DMA 按字节处理，而两个 FP4 元素共享一个字节。正确的元素转置需要跨字节重新组合四位编码。

### 为什么两个 AIV 都有结果，却只让 AIV0 搬运？

两个 AIV 有各自 UB，目标却是同一片 L1。只需一个写入者；这不代表已经把整个重排计算限制在 AIV0 上。

### 是否必须经过 UB？

本次采用 SIMT 直接读 GM、重排后写 UB、再搬到 L1 的实现。它不是对所有潜在实现方式作出的硬件限制结论。

### 为什么还保留 DMA 兜底检查？

前面的改写处理正确路径，后面的检查阻止漏过改写的操作静默退回错误路径，两者职责不同。

### 是否还有生产代码精简空间？

当前对齐限制下，工作项数量 `R*C/4` 一定能被 128 整除。因此尾部判断恒成立，循环次数可直接整除计算。这是已经识别、但本文对应提交尚未实施的局部精简点。进一步复用线程构造或执行范围机制，需要证明语义、同步和性能不变后再改。
