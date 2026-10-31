# 新服务器从这里开始（20261031-r5）

当前分工：**在 yjl 内直接克隆两个仓库。TileOPs 源码从个人 fork main 获取，辅助工具从 B2Y/topk-950pr 运行。**

工具包不包含 Docker 镜像、CANN SDK、Python wheel 或旧服务器缓存。镜像和容器尚未准备好时先看 `DOCKER.md`；Python/TileLang 环境尚未通过基础验证时先看 `DEPENDENCIES.md`。

本版按你的实际配置编写：**已有容器 yjl，私人目录 /home/y00937463，/home:/home 已挂载，镜像为 CANN Weekly 20260930 / Ubuntu22.04 / Python3.12。直接使用容器内 python3，不使用 Conda。**

## 1. 宿主机：进入已有 yjl

```bash
docker ps -a --filter name=yjl
docker exec -it yjl /bin/bash
```

如果容器已停止，先执行 `docker start yjl`。以下步骤全部在容器内运行，直接使用镜像自带的 python3。无需安装或激活 Conda，也无需重新创建容器。

## 2. 容器内：克隆 B2Y 和个人 fork

首次执行，两个目标目录必须不存在：

```bash
mkdir -p /home/y00937463
git clone --branch main https://gitcode.com/JotaroSSR/B2Y.git /home/y00937463/B2Y
git clone --branch main https://github.com/sgcg1/TileOPs.git /home/y00937463/TileOPs
git -C /home/y00937463/TileOPs fetch origin --tags
git -C /home/y00937463/TileOPs status -sb
git -C /home/y00937463/TileOPs log -1 --oneline
```

B2Y 工具直接从 `/home/y00937463/B2Y/topk-950pr` 运行；不再创建 tools 目录，也不需要下载或解压交付 ZIP。源码仍只通过个人 fork 同步。

## 3. 容器内：已有仓库的后续更新

只有目录已经存在时执行，首次 clone 后可跳过。先检查两个工作区均干净，再逐条更新；存在修改时先保存差异，不覆盖：

```bash
git -C /home/y00937463/B2Y status --short
git -C /home/y00937463/TileOPs status --short
# 确认两个工作区干净，且没有实验运行后，再执行：
git -C /home/y00937463/B2Y pull --ff-only origin main
git -C /home/y00937463/TileOPs pull --ff-only origin main
git -C /home/y00937463/TileOPs fetch origin --tags
```

工具、源码更新后使用新的 EVIDENCE，不能混入已开始的实验。

## 4. 容器内：使用镜像 Python，核实 CANN

不执行 conda activate。先在容器内检查：

```bash
cd /home/y00937463
python3 --version
printf 'ASCEND_HOME_PATH=%s\n' "${ASCEND_HOME_PATH:-未设置}"
command -v bisheng || true
```

镜像若已经设置有效的 ASCEND_HOME_PATH，可直接继续；若没有，先加载容器内真实的 CANN toolkit 环境脚本。不要照抄旧服务器路径，也不要把 toolbox 脚本当作 toolkit 脚本。具体检查见 DEPENDENCIES.md。

```bash
export TOPK_ROOT=/home/y00937463
export TOPK_REPO="$TOPK_ROOT/TileOPs"
export TOPK_DEVICE=0
export TOPK_PYTHON=python3
export TOPK_SOC=Ascend950PR_9579
export EVIDENCE="$TOPK_ROOT/runs/newhost-$(date +%Y%m%d-%H%M%S)"
source "$TOPK_ROOT/B2Y/topk-950pr/env.sh"
cd "$TOPK_TOOLS"
sha256sum --check MANIFEST.sha256
cd "$TOPK_REPO"
```

设备号和 SOC 以实际分配与芯片为准。需要由 env.sh 加载特定 CANN 脚本时，在 source env.sh 之前设置 `export CANN_ENV_SCRIPT=/实际/CANN/set_env.sh`。Python 必须为 3.12+，并有主仓 Ascend TileLang。项目声明 torch2.13.x；本工具也允许 torch2.10.x + torch_npu2.10.x 进入 TopK 兼容性实测，会输出警告并在 environment.json 记录未满足项目声明，不代表项目整体支持2.10。

**记下输出的 EVIDENCE。** 后续所有步骤在同一个容器终端、同一个实验目录执行。重开终端时先 docker exec 进入 yjl，按需加载 CANN，export EVIDENCE 为记下的原目录，再 source env.sh；不激活 Conda。新实验才换新的 EVIDENCE。

## 5. 先完成小规格闭环，逐条执行

```bash
bash "$TOPK_TOOLS/run.sh" preflight
bash "$TOPK_TOOLS/run.sh" test
bash "$TOPK_TOOLS/run.sh" control 1
bash "$TOPK_TOOLS/run.sh" control 2
bash "$TOPK_TOOLS/run.sh" clock
bash "$TOPK_TOOLS/run.sh" frequency
bash "$TOPK_TOOLS/run.sh" cann-build decode
bash "$TOPK_TOOLS/run.sh" cann-measure decode
bash "$TOPK_TOOLS/run.sh" measure decode
bash "$TOPK_TOOLS/run.sh" summary decode
```

每条成功并检查输出后再执行下一条，不要整组无条件粘贴。test 必须 **14 passed**，不能 skipped。frequency 输出的 Aicore 字段不是单独的 Vector 时钟证明；若负载期间持续低频，先核实平台策略，不自动调频。旧服务器的频率和延迟不能直接用于新服务器结论。

`summary decode` 保存 `summary-decode-local.json`，只代表 Decode 闭环，未完成完整规格。clock/frequency 失败时阅读该步日志；接口不支持或采样不足不等于硬件损坏。

## 6. 确认小规格正常后再跑完整规格

以下延续同一轮实验，不重新测已经完成的 Decode：

```bash
bash "$TOPK_TOOLS/run.sh" measure small
bash "$TOPK_TOOLS/run.sh" cann-build prefill-k1024
bash "$TOPK_TOOLS/run.sh" cann-measure prefill-k1024
bash "$TOPK_TOOLS/run.sh" measure prefill-k1024
bash "$TOPK_TOOLS/run.sh" cann-build prefill-k2048
bash "$TOPK_TOOLS/run.sh" cann-measure prefill-k2048
bash "$TOPK_TOOLS/run.sh" measure prefill-k2048
bash "$TOPK_TOOLS/run.sh" summary all
```

完整 scores 约 8 GiB，仍需输出和临时内存。每组正式采集 50 次事件和独立的 50 条有效 kernel 记录；脚本会检查本轮 CANN/TileLang 输入哈希一致。

默认外部超时：Decode 300 秒、128行诊断 600 秒、完整 Prefill 3600 秒。确需更长、且设备运行条件已确认时，可在该步前设置 `export TOPK_BENCH_TIMEOUT=7200`；不要用加大超时掩盖等待。失败结果保留，重跑使用新 EVIDENCE，不覆盖或拼接旧 profile。

## 7. 回传最少必要结果

原始结果留在服务器。按照 `RESULTS_TEMPLATE.md`，只填写当地允许披露的摘要，经手动取回后放入 B2Y 即可；不能出域的字段留空。这里不要求你导出 environment.json、完整 profiler、业务输入或机器路径。

由于私人目录已通过 /home 挂载共享，摘要文件也会直接出现在宿主机相同路径。若希望显式复制到宿主机当前目录，可使用：

```bash
docker cp yjl:/home/y00937463/runs/实际实验目录/summary-decode-local.json ./
```

先在保密环境内审核文件是否允许出域。完整流程、失败定位和可选诊断见 README。
