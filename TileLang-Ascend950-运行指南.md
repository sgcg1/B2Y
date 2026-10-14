# Ascend 950：TileLang 首次运行指南

本文针对当前 TileLang 仓库的 Ascend 950 后端，供在公用 Linux 服务器的 `yjl` Docker 容器内手动执行。已确认使用宿主机 7 号 Ascend 设备，CANN 环境脚本为 `/data/setenv.bash`。整理时 PC 上的源码版本为 `8df3fed1`；以下步骤尚未在服务器上验证。

每个编号下的代码框算一次输入：整框复制到 Linux 终端，按回车，等待完成后再进行下一步。包含 `PY` 的多行代码框也必须整体复制。如果某一步报错，停在该步，保留执行命令、第一处错误和末尾约 80 行日志。

## Docker 容器入口

### 0.1. 创建容器（仅首次，在宿主机执行）

如果 `yjl` 已经创建且正在运行，跳过此步，直接执行 0.2。以下沿用提供的配置，将重复的 `--shm-size` 合并为 `300g`。

```bash
docker run -u 0 -dit --name=yjl --net=host --privileged=true --shm-size=300g --ulimit memlock=150000000000:150000000000 -e ASCEND_RT_VISIBLE_DEVICES=7 -v /data:/data -v /home:/home -v /root/.ssh:/root/.ssh -v /usr/local/Ascend/driver/:/usr/local/Ascend/driver/ -v /etc/ascend_install.info:/etc/ascend_install.info triton_op_pipeline:v1.0 /bin/bash
```

镜像需要包含匹配的 CANN toolkit、PyTorch 和 torch_npu；driver 挂载本身不提供完整设备编译环境。`--privileged` 并不隔离设备访问权限，按团队分配仅使用 7 号设备。

### 0.2. 进入容器（在宿主机执行）

```bash
docker exec -it yjl /bin/bash
```

后续第 1–20 步和增量构建均在这个容器终端执行。新开容器终端后，重新执行第 1、1.1 步。

## 环境检查

### 1. 加载 CANN 环境

使用已确认的服务器环境脚本。在容器内加载，宿主机上执行 source 不会自动传入新的容器终端。

```bash
source /data/setenv.bash
```

### 1.1. 明确使用宿主机 7 号设备

在 CANN 环境脚本之后执行，保证本终端后续启动的 Python 进程继承此设置。

```bash
export ASCEND_RT_VISIBLE_DEVICES=7
```

### 1.2. 核对设备选择

```bash
printenv ASCEND_RT_VISIBLE_DEVICES
```

预期输出 `7`。该变量限制运行时设备可见性，不是 Docker 设备权限隔离。容器内逻辑设备编号可能与宿主机编号不同；不要据此直接写 `torch.npu.set_device(7)` 或 `device="npu:7"`。

### 2. 查看 NPU 信息

```bash
npu-smi info
```

确认设备为 Ascend 950。npu-smi 可能显示宿主机多个设备；不要仅凭列表判断 PyTorch 的运行时可见设备。

### 3. 查看 Python 版本

```bash
python3 --version
```

要求 Python 3.10 或更新版本。

### 4. 检查设备编译器

```bash
which bisheng
```

应输出可执行文件路径。

### 5. 检查链接器

```bash
which ld.lld
```

应输出路径，并确保它是 CANN 配套、支持 CCE 的链接器，而非仅有同名主机链接器。

### 6. 检查主机 C++ 编译器

```bash
g++ --version
```

### 7. 验证 PyTorch 能使用 NPU

整个代码框一次性复制，包括最后一行 `PY`。

```bash
python3 - <<'PY'
import os
import torch
import torch_npu

print("ASCEND_RT_VISIBLE_DEVICES:", os.environ.get("ASCEND_RT_VISIBLE_DEVICES"))
print("torch:", torch.__version__)
print("torch_npu:", torch_npu.__version__)
print("NPU available:", torch.npu.is_available())
assert torch.npu.is_available()
print("visible device count:", torch.npu.device_count())
print("current logical device:", torch.npu.current_device())

x = torch.ones(4, device="npu")
print((x + x).cpu())
PY
```

预期 `NPU available: True`，最后输出四个 `2`。若导入失败，先使用管理员提供的配套 Python 环境或容器；PyTorch、torch_npu 与 CANN 版本必须匹配。

## 源码与开发安装

### 8. 进入服务器上的 TileLang 仓库

先将 PC 上的源码传到自己独立的服务器目录，例如 `/data/yjl/tilelang`。`/data` 和 `/home` 已挂载，宿主机与容器内对应路径可见，文件修改也会作用到宿主机。不要与同事共用源码或 build 目录。将下面路径替换为实际路径后执行。

```bash
cd /你的实际路径/tilelang
```

### 9. 确认当前目录

```bash
pwd
```

应显示 TileLang 仓库路径。后续命令均在仓库根目录执行。

### 10. 查看源码版本

```bash
git rev-parse --short HEAD
```

建议与正在修改的 PC 仓库使用同一版本。整理本指南时 PC 的版本为 `8df3fed1`。

### 11. 初始化子模块

```bash
git submodule update --init --recursive
```

此步骤可能需要访问 GitHub。服务器不能联网时，应一起传入完整的 `3rdparty/tvm`、`3rdparty/cutlass` 及其所需子模块。主仓库 ZIP 通常不包含子模块。

### 12. 安装构建依赖

继续使用第 7 步已经能访问 NPU 的容器 Python 环境，保留镜像中配套的 PyTorch/torch_npu，不自行升级。安装仅在自己的容器中进行。

```bash
python3 -m pip install -r requirements-dev.txt
```

### 13. 安装测试工具

```bash
python3 -m pip install pytest
```

### 14. 设置 Ascend 构建选项

```bash
export CMAKE_ARGS="-DUSE_ASCEND=ON -DUSE_CUDA=OFF -DUSE_ROCM=OFF -DUSE_METAL=OFF"
```

成功时通常没有输出。该设置对当前终端有效；这里明确使用 CMake 参数，也可覆盖已有构建缓存中的后端设置。

### 15. 构建并开发安装 TileLang

```bash
python3 -m pip install -e . -v --no-build-isolation
```

构建可能耗时较长。等待完成后继续。Python 源码修改通常直接生效；C++ 源码修改需要重新构建。

### 16. 检查 TileLang 导入路径

```bash
python3 - <<'PY'
import torch_npu
import tilelang

print("version:", tilelang.__version__)
print("source:", tilelang.__file__)
PY
```

`source` 应指向服务器上正在使用的 TileLang 仓库。本地开发模式会从仓库 `build` 目录加载 native 库。

## 首次正确性验证

### 17. 运行向量加法

```bash
python3 examples/ascend/example_vecadd.py --mode simt --no-bench
```

验证 GM→UB 搬运、向量加法、UB→GM 搬运。成功时打印：

```text
vecadd (simt): correctness passed
```

首次运行会编译设备 kernel，可能比后续运行慢。此命令关闭性能测量。

### 18. 运行 BF16 GEMM

```bash
python3 -m pytest examples/ascend/test_gemm.py -v -k bf16-persistent -x
```

选中的测试应显示 `PASSED`。`SKIPPED` 不代表跑通设备，需要检查 NPU 检测和构建配置。先完成第 18 步，即可确认安装、设备编译及基础 kernel 执行链路。

### 19. 运行 copy lowering 测试

```bash
ASCEND_NPU_ARCH=dav-3510 python3 -m pytest testing/ascend/transform/test_ascend_lower_copy.py -v -x
```

该测试检查 copy lowering，不执行设备 kernel，但仍需包含 Ascend 后端的 TileLang 构建。

### 20. 运行设备 DMA 测试

```bash
python3 -m pytest testing/ascend/language/test_tilelang_ascend_dma_copy.py -v -x
```

该测试在 NPU 上验证 DMA 搬运数值结果。失败时 `-x` 会在首个失败处停止。

## 后续 C++ 增量构建

修改 `src/ascend/op/copy.cc` 等 C++ 文件后执行，再重跑相关测试。首次安装完成后不必额外执行。

```bash
cmake --build build -j8
```

## 仓库内参考

- `tilelang/ascend/README.md`：Ascend 950 安装和运行说明。
- `.agents/skills/tilelang-build/SKILL.md`：构建与增量编译说明。
- `examples/ascend/README.md`：示例与正确性测试。
- `testing/ascend/README.md`：Ascend 测试分层和运行要求。

本指南仅包含 TileLang 的安装与基线验证。E5M2 矩阵 copy 的 SDK 类型匹配缺口需单独修复和回归，不由基础测试通过推断已解决。
