# 环境准备与边界

本包只提供可审阅的小型工具，不包含 Docker 镜像、CANN SDK、驱动、Python 环境或旧服务器 .om/缓存。这些依赖由现场已有镜像、内部包源和环境负责人提供。

| 项目 | 当前要求 / 用途 |
| --- | --- |
| Linux x86_64，目标 Ascend950PR | 本次目标机器架构和算子支持范围 |
| Python >=3.12 | 当前 TileOPs pyproject 要求 |
| torch >=2.13,<2.14 + 兼容 torch_npu | 当前声明的框架范围；torch 的 +cpu 标签不等于不能用 NPU |
| TileLang 主仓 Ascend 后端 | 必须有 tilelang.ascend.language、Ascend target、SIMT lowering 和运行时支持 |
| 兼容的 CANN toolkit、算子包及宿主机驱动 | 必须含 bisheng；不能仅挂载 driver 就认定开发环境完整 |
| git、pytest、pytest-timeout、PyYAML | 源码加载和契约测试；按实际导入缺项补齐私人环境 |
| g++、CANN GE 头文件及编译/graph/runner 库 | 官方 TopKV2 静态模型构建 |
| npu-smi 或 driver tools 中对应程序 | 设备健康、利用率与频率的只读检查 |

首先在容器内检查：

```bash
python3 --version
printenv ASCEND_HOME_PATH
command -v bisheng
python3 -c 'import torch, torch_npu, tilelang; print(torch.__version__, torch_npu.__version__, tilelang.__version__); print(tilelang.__file__)'
```

CANN 未激活时，找现场实际脚本，例如查看 `/usr/local/Ascend` 中安装布局及 `/home/CANN`（如存在）。toolbox 的 set_env.sh 不一定等同于 toolkit 激活脚本。不要复制别人的代理地址、执行全局 Git 配置清空命令或关闭 TLS 校验来“修复”环境。

如已有与 CANN 匹配的私人 Python 环境，先激活它，再执行 START_HERE 中的 env.sh。不要执行无约束的 `pip install -e .`：项目将 tilelang 固定为 0.1.12，依赖解析可能覆盖已准备的 Ascend 构建。源码通过 PYTHONPATH 加载，不必安装整个项目的 CUDA bench/dev 依赖组。

确认已激活私人环境且允许安装时，仅为测试补齐缺项，例如通过现场内部源执行：

```bash
python3 -m pip install 'pytest>=8' 'pytest-timeout>=2.3' 'pyyaml>=6,<7'
```

这条命令不安装/升级 torch、torch_npu、TileLang、CANN 或系统驱动。缺框架时应安装现场适配的完整组合，不根据旧服务器版本盲目覆盖共享环境。旧服务器参考是 Python3.12.16 / torch2.13.0 / torch_npu2.13.0 / 私人主仓 TileLang0.1.15 / CANN9.3.0 Weekly，并非已证明的新服务器必选构建。

若需要自行构建 TileLang，使用 B2Y 已有《TileLang-Ascend950-运行指南.md》及实际主仓说明，先通过 SIMT 向量加法。独立 tilelang-ascend 仓不作为本任务交付路线；版本号或镜像名字不足以证明源码来自主仓。无法追溯 commit 时如实记 unknown。

本工具的 GE 构建默认 `_GLIBCXX_USE_CXX11_ABI=0`。新 SDK 有差异时先看 compile.log，由环境负责人确认库/ABI；必要时在新一轮前设置 TOPK_CXX11_ABI，或修改工具、更新清单再新建 EVIDENCE。不要为了通过编译修改共享 SDK。
