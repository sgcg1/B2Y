# Ascend 950：TileLang 首次运行指南

本文针对当前 TileLang 仓库的 Ascend 950 后端，供在公用 Linux 服务器的 `yjl` Docker 容器内手动执行。当前使用宿主机 0 号 Ascend 设备，CANN 环境脚本为 `/data/setenv.bash`。整理时 PC 上的源码版本为 `8df3fed1`；用户已确认切换至 0 号设备后基础 PyTorch NPU 计算通过；TileLang 构建与 kernel 测试尚待验证。

每个编号下的代码框算一次输入：整框复制到 Linux 终端，按回车，等待完成后再进行下一步。包含 `PY` 的多行代码框也必须整体复制。如果某一步报错，停在该步，保留执行命令、第一处错误和末尾约 80 行日志。

## Docker 容器入口

### 0.1. 创建容器（仅首次，外部 Linux 终端／宿主机执行）

如果 `yjl` 已经创建且正在运行，跳过此步，直接执行 0.2。以下沿用提供的配置，将重复的 `--shm-size` 合并为 `300g`。

```bash
docker run -u 0 -dit --name=yjl --net=host --privileged=true --shm-size=300g --ulimit memlock=150000000000:150000000000 -e ASCEND_RT_VISIBLE_DEVICES=0 -v /data:/data -v /home:/home -v /root/.ssh:/root/.ssh -v /usr/local/Ascend/driver/:/usr/local/Ascend/driver/ -v /etc/ascend_install.info:/etc/ascend_install.info triton_op_pipeline:v1.0 /bin/bash
```

镜像需要包含匹配的 CANN toolkit、PyTorch 和 torch_npu；driver 挂载本身不提供完整设备编译环境。`--privileged` 并不隔离设备访问权限，按团队分配仅使用已分配的 0 号设备。

### 0.2. 进入容器（外部 Linux 终端／宿主机执行）

```bash
docker exec -it yjl /bin/bash
```

后续第 1–20 步和增量构建均在容器内执行。未设置下方 Bash 默认配置时，新开容器终端需重新执行第 1、1.1 步。

## 已有容器默认使用 0 号卡

已有 `yjl` 容器的创建配置可能仍是设备 7。下面让交互式 Bash 每次启动时加载 CANN，并使用设备 0。每个代码框分别执行；这里只修改容器内 root 用户的 Bash 配置。

### D1. 进入已有容器【外部 Linux 终端／宿主机执行】

若已经在容器内，跳过此步。

```bash
docker exec -it yjl /bin/bash
```

### D2. 写入 Bash 默认配置【容器内执行，仅执行一次】

如果已经按聊天中的步骤写入过，不要重复执行。

```bash
cat >> /root/.bashrc <<'EOF'

# Ascend environment and default device
source /data/setenv.bash
export ASCEND_RT_VISIBLE_DEVICES=0
EOF
```

### D3. 使当前终端立即生效【容器内执行】

```bash
source /root/.bashrc
```

### D4. 检查配置【容器内执行】

```bash
printenv ASCEND_RT_VISIBLE_DEVICES
```

预期输出 `0`。

### D5. 退出容器终端【容器内执行】

```bash
exit
```

返回宿主机终端，不会删除容器。

### D6. 重新进入容器【外部 Linux 终端／宿主机执行】

```bash
docker exec -it yjl /bin/bash
```

### D7. 验证默认配置【容器内执行】

```bash
printenv ASCEND_RT_VISIBLE_DEVICES
```

预期输出 `0`，然后继续环境检查。

此配置适用于 `docker exec -it yjl /bin/bash` 启动的交互式 Bash 及其子进程，不会改变 Docker 保存的容器环境变量。直接通过 docker exec 启动其他程序时不会读取 `.bashrc`；应显式传入设备变量，并根据程序需要加载 CANN。下次新建容器时使用上方已改为设备 0 的创建命令，无需为此删除现有容器。

## 环境检查

### 1. 加载 CANN 环境【容器内执行】

使用已确认的服务器环境脚本。在容器内加载，宿主机上执行 source 不会自动传入新的容器终端。

```bash
source /data/setenv.bash
```

### 1.1. 明确使用宿主机 0 号设备【容器内执行】

在 CANN 环境脚本之后执行，保证本终端后续启动的 Python 进程继承此设置。

```bash
export ASCEND_RT_VISIBLE_DEVICES=0
```

### 1.2. 核对设备选择【容器内执行】

```bash
printenv ASCEND_RT_VISIBLE_DEVICES
```

预期输出 `0`。该变量限制运行时设备可见性，不是 Docker 设备权限隔离。容器内逻辑设备编号可能与宿主机编号不同；不要据此直接写 `torch.npu.set_device(7)` 或 `device="npu:7"`。

### 2. 查看 NPU 信息【容器内执行】

```bash
npu-smi info
```

确认设备为 Ascend 950。npu-smi 可能显示宿主机多个设备；不要仅凭列表判断 PyTorch 的运行时可见设备。若容器提示命令不存在，可在容器内尝试 `/usr/local/Ascend/driver/tools/npu-smi info`；仍不可用时，在外部 Linux 终端／宿主机执行 `npu-smi info`。该工具缺失本身不代表 NPU 无法计算，第 7 步检查实际执行能力。

### 3. 查看 Python 版本【容器内执行】

```bash
python3 --version
```

要求 Python 3.10 或更新版本。

### 4. 检查设备编译器【容器内执行】

```bash
which bisheng
```

应输出可执行文件路径。

### 5. 检查链接器【容器内执行】

```bash
which ld.lld
```

应输出路径，并确保它是 CANN 配套、支持 CCE 的链接器，而非仅有同名主机链接器。

### 6. 检查主机 C++ 编译器【容器内执行】

```bash
g++ --version
```

### 7. 验证 PyTorch 能使用 NPU【容器内执行】

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

### 7.1. 基础验证卡住时的分步定位【容器内执行】

先结束之前的测试进程，再整体复制下方代码。正常通过第 7 步时跳过本步骤。

```bash
python3 -u - <<'PY'
import os
import torch
import torch_npu

print("visible devices:", os.environ.get("ASCEND_RT_VISIBLE_DEVICES"), flush=True)

print("1. 开始创建 NPU 张量", flush=True)
x = torch.ones(4, device="npu")
print("2. 张量创建已返回", flush=True)

torch.npu.synchronize()
print("3. 创建操作同步完成", flush=True)

y = x + x
print("4. 加法操作已返回", flush=True)

torch.npu.synchronize()
print("5. 加法操作同步完成", flush=True)

print("6. 开始拷回 CPU", flush=True)
print(y.cpu(), flush=True)
print("7. 全部完成", flush=True)
PY
```

预期 `NPU available: True`，最后输出四个 `2`。若导入失败，先使用管理员提供的配套 Python 环境或容器；PyTorch、torch_npu 与 CANN 版本必须匹配。

## 源码与开发安装

### 8. 进入服务器上的 TileLang 仓库【容器内执行】

先将 PC 上的源码传到自己独立的服务器目录，例如 `/data/yjl/tilelang`。`/data` 和 `/home` 已挂载，宿主机与容器内对应路径可见，文件修改也会作用到宿主机。不要与同事共用源码或 build 目录。将下面路径替换为实际路径后执行。

```bash
cd /你的实际路径/tilelang
```

### 9. 确认当前目录【容器内执行】

```bash
pwd
```

应显示 TileLang 仓库路径。后续命令均在仓库根目录执行。

### 10. 查看源码版本【容器内执行】

```bash
git rev-parse --short HEAD
```

建议与正在修改的 PC 仓库使用同一版本。整理本指南时 PC 的版本为 `8df3fed1`。

### 11. 初始化子模块【容器内执行】

```bash
git submodule update --init --recursive
```

此步骤可能需要访问 GitHub。服务器不能联网时，应一起传入完整的 `3rdparty/tvm`、`3rdparty/cutlass` 及其所需子模块。主仓库 ZIP 通常不包含子模块。

### 12. 安装构建依赖【容器内执行】

继续使用第 7 步已经能访问 NPU 的容器 Python 环境，保留镜像中配套的 PyTorch/torch_npu，不自行升级。安装仅在自己的容器中进行。

```bash
python3 -m pip install -r requirements-dev.txt
```

### 13. 安装测试工具【容器内执行】

```bash
python3 -m pip install pytest
```

### 14. 设置 Ascend 构建选项【容器内执行】

```bash
export CMAKE_ARGS="-DUSE_ASCEND=ON -DUSE_CUDA=OFF -DUSE_ROCM=OFF -DUSE_METAL=OFF"
```

成功时通常没有输出。该设置对当前终端有效；这里明确使用 CMake 参数，也可覆盖已有构建缓存中的后端设置。

### 15. 构建并开发安装 TileLang【容器内执行】

```bash
python3 -m pip install -e . -v --no-build-isolation
```

构建可能耗时较长。等待完成后继续。Python 源码修改通常直接生效；C++ 源码修改需要重新构建。

### 16. 检查 TileLang 导入路径【容器内执行】

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

### 17. 运行向量加法【容器内执行】

```bash
python3 examples/ascend/example_vecadd.py --mode simt --no-bench
```

验证 GM→UB 搬运、向量加法、UB→GM 搬运。成功时打印：

```text
vecadd (simt): correctness passed
```

首次运行会编译设备 kernel，可能比后续运行慢。此命令关闭性能测量。

### 18. 运行 BF16 GEMM【容器内执行】

```bash
python3 -m pytest examples/ascend/test_gemm.py -v -k bf16-persistent -x
```

选中的测试应显示 `PASSED`。`SKIPPED` 不代表跑通设备，需要检查 NPU 检测和构建配置。先完成第 18 步，即可确认安装、设备编译及基础 kernel 执行链路。

### 19. 运行 copy lowering 测试【容器内执行】

```bash
ASCEND_NPU_ARCH=dav-3510 python3 -m pytest testing/ascend/transform/test_ascend_lower_copy.py -v -x
```

该测试检查 copy lowering，不执行设备 kernel，但仍需包含 Ascend 后端的 TileLang 构建。

### 20. 运行设备 DMA 测试【容器内执行】

```bash
python3 -m pytest testing/ascend/language/test_tilelang_ascend_dma_copy.py -v -x
```

该测试在 NPU 上验证 DMA 搬运数值结果。失败时 `-x` 会在首个失败处停止。

## 后续 C++ 增量构建【容器内执行】

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



python3 -u - <<'PY'
import importlib
import os
import shutil
import sys

print("Python:", sys.version)
print("Executable:", sys.executable)
print("Device setting:", os.environ.get("ASCEND_RT_VISIBLE_DEVICES"))

modules = [
    "torch", "torch_npu", "numpy", "tvm_ffi",
    "Cython", "scikit_build_core", "setuptools",
    "packaging", "z3", "pytest",
    "cloudpickle", "ml_dtypes", "psutil", "tqdm",
    "typing_extensions",
]
missing = []

print("\n=== Python dependencies ===")
for name in modules:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", "version unavailable")
        print(f"OK   {name}: {version}")
    except Exception as exc:
        missing.append(name)
        print(f"FAIL {name}: {type(exc).__name__}: {exc}")

print("\n=== Build tools ===")
for name in ["git", "cmake", "ninja", "g++", "bisheng", "ld.lld", "patchelf"]:
    print(f"{name}: {shutil.which(name) or 'NOT FOUND'}")

print("\n=== TileLang ===")
try:
    import tilelang
    print("Version:", tilelang.__version__)
    print("Source:", tilelang.__file__)
except Exception as exc:
    print(f"FAIL: {type(exc).__name__}: {exc}")

print("\nFailed Python imports:", missing)
PY
