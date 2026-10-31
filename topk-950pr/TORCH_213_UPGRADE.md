# yjl 容器内升级 torch / torch_npu 到 2.13

适用现场：已有 Docker 容器 `yjl`、私人目录 `/home/y00937463`、Python3.12.14、CANN `9.3.0.20260930 Weekly`。原环境为 torch2.10.0+cpu / torch_npu2.10.0；操作者已编译 TileLang0.1.15+cpu.git0176ba14 并通过仓内测试，且已下载两个2.13 wheel。

目标是使用 TileOPs 声明的 torch2.13 版本范围继续验证 TopK。**尚未确认该 CANN Weekly 与下载的2.13包完全兼容，安装后必须重新验证。** 本文只操作自己的 yjl，不使用 Conda，不更改宿主机、驱动或全局 pip 配置。确认没有自己的测试任务运行后再安装。

每步成功后再执行下一步；任一步报错就停下，保留完整输出。环境升级后不能继续使用旧实验目录。

## 1. 宿主机：进入已有容器

```bash
docker exec -it yjl /bin/bash
```

若已在 yjl 内，不必重复进入。以下命令全部在容器内执行，使用之前编译、测试 TileLang 的同一个 Python。

## 2. 核实解释器和已下载文件

```bash
command -v python3
python3 --version
ls -lh /home/y00937463/wheels/torch213/
```

本次预期解释器为 `/usr/local/python3.12.14/bin/python3`，目录包含：

```text
torch-2.13.0+cpu-cp312-cp312-manylinux_2_28_x86_64.whl
torch_npu-2.13.0-cp312-cp312-manylinux_2_28_x86_64.whl
```

两个文件已经下载成功时直接继续；缺文件才使用文末的下载命令。

## 3. 保存原包清单并安装

```bash
python3 -m pip freeze > \
  "/home/y00937463/wheels/before-torch213-$(date +%Y%m%d-%H%M%S).txt"
```

清单用于追溯，不是环境备份，不能保证一条命令恢复原环境。随后同时安装两份本地 wheel，让 pip 正常解析所需依赖：

```bash
python3 -m pip install \
  --index-url https://pypi.org/simple \
  /home/y00937463/wheels/torch213/torch-2.13.0+cpu-cp312-cp312-manylinux_2_28_x86_64.whl \
  /home/y00937463/wheels/torch213/torch_npu-2.13.0-cp312-cp312-manylinux_2_28_x86_64.whl
```

这一步替换 yjl 内的 torch / torch_npu，依赖若缺失仍可能需要联网。不要先卸载2.10，不使用 `--no-deps` 跳过安装依赖，也不执行无版本限制的全环境升级。安装失败时不要继续跑 NPU 测试。

## 4. 验证版本、TileLang 导入及真实 NPU 运算

在已加载容器实际 CANN toolkit 环境的终端执行。下面只暴露物理卡0，若实际分配不同，请更改设备号；进程内仍用 `npu:0`。

```bash
ASCEND_RT_VISIBLE_DEVICES=0 python3 - <<'PY'
import sys
import torch
import torch_npu
import tilelang

print("Python:", sys.executable)
for name, module in [("torch", torch), ("torch_npu", torch_npu), ("tilelang", tilelang)]:
    print(name, "version:", getattr(module, "__version__", "unknown"))
    print(name, "path:", module.__file__)

assert torch.__version__.split("+")[0].split(".")[:2] == ["2", "13"]
assert torch_npu.__version__.split("+")[0].split(".")[:2] == ["2", "13"]
assert torch.npu.is_available(), "NPU is unavailable"
torch.npu.set_device(0)
x = torch.tensor([1.0, 2.0], device="npu:0")
assert (x + x).cpu().tolist() == [2.0, 4.0]
print("NPU computation PASS")
PY
```

应打印两项2.13版本、TileLang的实际加载路径和 `NPU computation PASS`。`+cpu` 后缀不能单独用于判断 NPU 能否工作，以实际计算为准。

随后重新运行你此前通过的 TileLang 仓内测试，使用相同的测试命令、范围及当前 python3。原来在2.10下的通过不替代升级后的验证。若导入或测试报错，保留完整输出；按该 TileLang checkout 原有构建流程判断是否需重编译，不直接替换为通用 PyPI tilelang 包。

## 5. 新建 TopK 实验并运行预检

TileLang 复测通过后，在同一个已加载 CANN 的终端执行：

```bash
export TOPK_ROOT=/home/y00937463
export TOPK_DEVICE=0
export TOPK_PYTHON="$(command -v python3)"
export TOPK_SOC=Ascend950PR_9579
export EVIDENCE="$TOPK_ROOT/runs/topk213-$(date +%Y%m%d-%H%M%S)"

source "$TOPK_ROOT/B2Y/topk-950pr/env.sh"
```

设备号和 SOC 按现场实际分配修改。若 env.sh 报 CANN 未加载，设置 `CANN_ENV_SCRIPT` 为容器内真实 toolkit 环境脚本，再重新 source；不照抄旧服务器路径。

```bash
bash "$TOPK_TOOLS/run.sh" preflight
```

预检成功后再执行：

```bash
bash "$TOPK_TOOLS/run.sh" test
```

成功条件是 **14项全部通过、无跳过**。然后回到 [START_HERE.md](START_HERE.md) 第5步，从 `control 1` 继续，在本轮相同 EVIDENCE 内完成 Decode 和后续完整规格。不要再次运行已完成的 preflight/test，也不要合并旧2.10或失败实验的数据。

## 可选：缺少 wheel 时重新下载

已有两个 wheel 时跳过本节。只下载，不安装：

```bash
mkdir -p /home/y00937463/wheels/torch213

python3 -m pip download \
  --dest /home/y00937463/wheels/torch213 \
  --only-binary=:all: --no-deps \
  --index-url https://download.pytorch.org/whl/cpu \
  'torch==2.13.0+cpu'
```

```bash
python3 -m pip download \
  --dest /home/y00937463/wheels/torch213 \
  --only-binary=:all: --no-deps \
  --index-url https://pypi.org/simple \
  'torch_npu==2.13.0'
```

若 torch 下载遇到本次已出现的 `self-signed certificate in certificate chain`，优先在下载命令中使用 `--cert /实际路径/可信CA证书包.pem`。现场允许临时跳过证书验证时，才使用以下单次重试：

```bash
python3 -m pip download \
  --dest /home/y00937463/wheels/torch213 \
  --only-binary=:all: --no-deps \
  --index-url https://download.pytorch.org/whl/cpu \
  --trusted-host download.pytorch.org \
  --trusted-host download-r2.pytorch.org \
  'torch==2.13.0+cpu'
```

这两个参数只对本次命令生效，不修改全局配置，但会跳过指定域名的 TLS 证书身份验证。wheel 留在私人目录，不提交 B2Y。

参考：[pip 证书与 CA 配置](https://pip.pypa.io/en/stable/topics/https-certificates/)、[Ascend PyTorch 版本配套说明](https://github.com/Ascend/pytorch/blob/master/COMPATIBILITY.md)。公开配套说明不作为本次特定 Weekly 已验证的证明。
