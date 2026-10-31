# TopKSelect 950PR：B2Y 辅助材料与 yjl 容器操作

## 两条同步通道

- **实现代码、测试和正式版本文档**：`https://github.com/sgcg1/TileOPs.git` 的 `main`。本地开发后经个人 fork 同步，服务器按 commit 测试。
- **本目录辅助工具**：经 B2Y/GitCode 同步到你可下载文件的电脑，再由你选择本目录需要的文件传入服务器。**服务器不克隆 B2Y**，不通过 ZIP 覆盖 TileOPs 代码。

本目录没有 TileOPs 实现源码副本。历史对照实现从个人 fork 的 `topk-npu-v0.1.0/v0.1.2` 标签提取。不要浅克隆或只传当前 src，否则历史对照缺失。当前候选虽已进入 Git 历史，仍不代表 v0.1.4 已完成验收。

## 0. 文件清单和传输方式

| 文件 | 用途 |
| --- | --- |
| env.sh | 指定源码、工具、实验目录和设备；加载容器 CANN 环境 |
| run.sh | 分阶段入口，遇到命令失败即退出，保留日志 |
| preflight.py | 设备实算、模块路径、源码 commit、库路径/哈希 |
| control_portable.py | 同进程初版/v0.1.2/候选 H128/H256 对照 |
| measure.py | 四组 TileLang 原始 kernel 事件及 profiling 测量 |
| summarize.py | 检查 14 项测试和 50/50 采样，核对输入，生成汇总 |
| cann/ | 官方 TopKV2 静态模型构建、测量和 profiler 汇总 |
| MANIFEST.sha256 | 本目录文件校验清单 |

第一次建议只将 B2Y 的 `topk-950pr/` **整个子目录**下载并上传，约几十 KB；这不是克隆 B2Y。后续可仅替换有变更的工具，但更换后使用新实验目录并更新清单。只跑正确性时仅需 env.sh、run.sh、preflight.py；正式对照还需其余 Python 和 cann/。

以下约定宿主机允许的私人目录为 `/data/yjl/topk`，且现有 yjl 把 `/data` 挂载到容器。**先核实，若不同就统一替换路径**。

### 宿主机执行：检查现有容器

```bash
docker ps -a --filter name=yjl
docker inspect yjl --format '{{json .Mounts}}'
```

本指南不重建容器、不修改公共驱动。若 yjl 已存在但未运行且允许启动，执行 `docker start yjl`。在你获准的宿主机目录接收上传的 `topk-950pr` 后，若目录被挂载，可直接在容器访问。例如将文件上传为 `/data/yjl/topk/tools/`，其中直接包含 env.sh、run.sh、cann/。

若上传目录未挂载，使用 docker cp（目标是容器内获准目录）：

```bash
docker exec yjl mkdir -p /data/yjl/topk/tools
docker cp /YOUR/UPLOADED/topk-950pr/. yjl:/data/yjl/topk/tools/
```

然后进入现有容器：

```bash
docker exec -it yjl /bin/bash
```

**以下所有命令均在 yjl 容器内执行**。宿主机的 source/conda 设置不会自动传入 docker exec。

## 1. 从个人 fork 获取实现

首次克隆（目录不存在时）：

```bash
mkdir -p /data/yjl/topk
git clone --branch main https://github.com/sgcg1/TileOPs.git /data/yjl/topk/TileOPs
git -C /data/yjl/topk/TileOPs fetch origin --tags
git -C /data/yjl/topk/TileOPs status --short
git -C /data/yjl/topk/TileOPs log -1 --oneline
git -C /data/yjl/topk/TileOPs tag --list 'topk-npu-*'
```

已有克隆时，不覆盖目录：

```bash
cd /data/yjl/topk/TileOPs
git status --short
git remote -v
git switch main
git pull --ff-only origin main
git fetch origin --tags
```

必须确认 origin 是个人 fork，工作区干净。dirty 时先单独保存改动，不 reset/clean/stash 掩盖现场。每轮本地改代码→个人 fork push main→容器 pull --ff-only→记录 commit。运行测试期间不 pull、不修改源码。不能直连 GitHub 时按现场获准渠道访问个人 fork；不要改成从 B2Y 拷贝源码。

## 2. 加载容器环境

先激活你已准备好的私人 Python 环境。如果上一份 TileLang 首跑指南尚未完成，先确保**主仓 Ascend 后端**的向量加法可正确运行。这个工具目录不提供 Python、CANN、TileLang native 库或 Docker 镜像。

```bash
export TOPK_ROOT=/data/yjl/topk
export TOPK_REPO="$TOPK_ROOT/TileOPs"
export TOPK_DEVICE=0
export TOPK_PYTHON=python3
export CANN_ENV_SCRIPT=/data/setenv.bash
export EVIDENCE="$TOPK_ROOT/runs/first-topk-$(date +%Y%m%d-%H%M%S)"
source "$TOPK_ROOT/tools/env.sh"
```

设备 0 来自 B2Y 现有容器指南，只是可覆盖默认值；以本次分配为准。暴露一个物理设备后程序使用逻辑 `npu:0`。Python 必须 >=3.12，且 torch/torch_npu 与容器 CANN/驱动兼容；本地旧参考为 Python3.12、torch2.13、torch_npu2.13、主仓 TileLang0.1.15，不要求凭版本号认定同一构建。

激活脚本 `/data/setenv.bash` 如不同就修改 CANN_ENV_SCRIPT。不修改 `.bashrc` 或容器创建参数。不要重新 pip install 项目：pyproject 的 TileLang0.1.12 pin 会覆盖当前 Ascend 构建。通过 PYTHONPATH 运行源码；缺 pytest、pytest-timeout、PyYAML 等依赖时用内部包源安装在获准的私人环境，不安装全部 CUDA bench/dev 依赖。

新开终端重新激活 Python 并 source env.sh，继续同轮实验时把 EVIDENCE 指回原目录；开始新轮则用新目录。所有缓存、tmp、trace、日志写入 TOPK_ROOT，HOME 不改。

完整传输时先验证材料：

```bash
cd "$TOPK_TOOLS"
sha256sum --check MANIFEST.sha256
cd "$TOPK_REPO"
```

## 3. 设备与环境检查

```bash
bash "$TOPK_TOOLS/run.sh" preflight
```

查看 health-before.txt，要求目标设备健康正常；查看 preflight.log/environment.json，要求 torch 实算成功、TileLang Ascend 可导入、TileOPs 路径指向个人 fork checkout、源码无未提交修改。npu-smi 可能显示所有宿主机卡，不代表 Python 可见全部设备。

有 Alarm、初始化失败、编译器缺失或版本接口异常就停在此步处理。新服务器的 SDK 是独立环境，不复用旧缓存；不因警告擅自升级共享驱动或重置卡。完整 Prefill 的 scores 约 8 GiB，还需临时校验与 runtime 空间；实际以测量器内存断言为准。

## 4. 完整正确性测试

```bash
bash "$TOPK_TOOLS/run.sh" test
```

要求最后 **14 passed**；skipped 不算。覆盖 NaN/Inf/±0、边界/溢出、同分取小索引、缓存溢出、K>2048、分组、非连续输入和窗口语义。失败时保留首个失败和 traceback，不改用 FP16 近似放行。超时是需要调查的失败，不自动归因于硬件。

`torch.compile` 目前仅覆盖 eager backend/fullgraph，不代表 Inductor 或 NPU graph 已验证。

## 5. 同进程控制，先做两轮

```bash
bash "$TOPK_TOOLS/run.sh" control 1
bash "$TOPK_TOOLS/run.sh" control 2
```

每轮固定输入和预分配缓冲，初版、v0.1.2、当前 H128/H256 按正反顺序交替，每个配置50次事件。结果在 control-decode-*/control.json，并保存生成 C++。目录存在就拒绝覆盖。

v0.1.2 与当前 H128 可能生成相同 C++；相同源码不等于已核对加载二进制。出现显著漂移时先查编译选项、实际二进制/加载库及设备状态，不继续叠加优化。工具会记录映射的主机库哈希，但这不是设备 kernel 二进制哈希。控制实验只验证有限随机输入，不替代14项。

## 6. 新建官方 CANN 基线

```bash
bash "$TOPK_TOOLS/run.sh" cann-build
bash "$TOPK_TOOLS/run.sh" cann-measure
```

依赖 CANN GE 头文件、编译库和 g++；build.cpp 指定 Ascend950PR_9579，ABI=0 与库列表来自旧环境。现场不同应在辅助脚本私人副本中调整并记录，不能修改 SDK 本身。如果 GE 报缺 decorator/attrs/scipy，使用获准内部包源补齐私人依赖。

基线为官方 TopKV2，必须保留 FP32、INT32 indices、largest=true、sorted=false、dim=-1、sort_policy=0、must_keep_origin_dtype。构建入口不是自写 TopK 算子。每个 shape/K 单独生成模型；不用旧服务器的 .om 或耗时。

本工具的 CANN profiling 发射60次，汇总严格按设备时间取最后50条真实记录，另有50次非profiling事件。只允许一个 profile 目录；不足50条或混入旧目录就失败。查看 task_time.csv，确认没有额外 Cast/Transpose/AICPU 计算；MODEL_EXECUTE/NOTIFY 等模型控制任务不算 TopKV2 内核。

## 7. 四组候选测量

```bash
bash "$TOPK_TOOLS/run.sh" measure
bash "$TOPK_TOOLS/run.sh" summary
```

测量四组：Decode1×16384/K2048；诊断128×65536/K2048；Prefill32768×65536/K1024、K2048。每组50次事件、独立50条有效profile，输入生成/分配/校验/编译不在计时内，校验后重新warmup。

新软件栈随机序列可能不同。measure.py 明确记录 historical_input_match，而不把旧输入哈希强加给新环境；summary 必须确认同规格 **本轮 CANN 与 TileLang 的完整输入哈希一致**，否则拒绝计算倍数。这是新批次，不宣称与旧服务器输入一致。

当前实现 H128，workers=min(rows,实际 Vector 核数)，65536/K1024走直接FP32，其余粗筛。覆盖 threads/workers 做诊断并不修改 host 默认；最终改默认后必须重新提交源码，并重跑检查、14项和四组测量。可在固定输入小规格上试 W32/W56，先确认实际核数：

```bash
"$TOPK_PYTHON" "$TOPK_TOOLS/measure.py" --version tune-w32 --case small --workers 32 --threads 128 --profile-samples 50
"$TOPK_PYTHON" "$TOPK_TOOLS/measure.py" --version tune-w56 --case small --workers 56 --threads 128 --profile-samples 50
```

这两条是独立进程诊断，不能称为同进程AB/BA。反向顺序用新 version 重复，再评估完整规格。

性能倍数=CANN纯内核中位数/TileLang纯内核中位数；单位统一μs。事件与profile单列，不把静态模型调度算作纯内核。128行没有同规格CANN基线，不换算×Ascend C。四组 kernel Python 源码哈希应一致，生成C++因shape不同不要求一致。不得把旧服务器历史数字拼入新批次。

summary-local.json 只做证据完整性检查，不自动认证性能成功；还须人工确认健康、稳定性和任务类型。没有整体收益时记录experimental/rejected，不打正式成功标签。

## 8. 结果与代码如何返回

实现或测试要修改：优先在本地 TileOPs main 改、提交并推送个人fork，容器pull。若在服务器临时诊断修改过代码，先保留diff，再明确迁回同一提交链，不能带着dirty源码出正式性能结论。

实验原始输出只保存在新服务器 TOPK_ROOT/runs；不要求导出。允许出域的汇总或脚本修改，由你手动取回，在B2Y单独目录显式git add 后同步，不要求服务器克隆B2Y。允许传回的摘要可包含：commit代号、14项状态、四组shape/K、配置、事件/内核中位数、采样数、同轮输入是否匹配、错误类型及是否改源码。

原始environment.json、profiler、路径和完整trace可能含环境信息，按当地规定审核；不能导出的结果留在服务器。不要把SDK、缓存、凭据和业务数据上传到任何仓库。

## 9. 常见阻塞

- Python<3.12：切换已准备的私人Python，不能只因TileLang示例支持3.10就忽略TileOPs要求。
- tilelang.ascend缺失/设备编译失败：先完成B2Y已有《TileLang-Ascend950-运行指南.md》的主仓构建与SIMT向量加法；不安装独立tilelang-ascend替代。
- 历史标签不存在：在个人fork checkout执行git fetch origin --tags，确认本地推送端已同步历史标签。
- npu-smi不存在：入口会尝试驱动tools路径；仍不可用则在宿主机检查健康，保留环境检查失败现场，不自动跳过验收。
- 某一步失败：不要连续执行后续命令；只在允许披露范围回报阶段、首个错误类型、退出码和是否改代码。
- 重跑：新EVIDENCE最简单；如重用旧目录，必须自行分离旧trace/结果，不删掉失败证据。

工具通过Python语法、Ruff、Bash语法和离线模拟汇总检查；尚未在新容器实际运行，现场编译器/SDK差异需按失败点调整。
