# 新服务器从这里开始（20261031-r2）

分工保持不变：**TileOPs 源码从个人 fork main 获取；本工具目录从 B2Y 下载后手动传入。服务器不克隆 B2Y。**

工具包不包含 Docker 镜像、CANN SDK、Python wheel 或旧服务器缓存。镜像和容器尚未准备好时先看 `DOCKER.md`；Python/TileLang 环境尚未通过基础验证时先看 `DEPENDENCIES.md`。

## 1. 只下载 B2Y 中这一份工具包

在可以访问 GitCode 的电脑下载 B2Y 的 `deliveries/topk-950pr-tools-20261031-r2.zip`，或直接下载 `topk-950pr/` 子目录。解压后得到 `topk-950pr/`。

把子目录手动上传到服务器。例如宿主机上的 `/YOUR/UPLOAD/topk-950pr/`。不要上传旧服务器的 `.om`、cache、环境文件或日志。

## 2. 宿主机：传入已有 yjl

```bash
docker ps -a --filter name=yjl
docker inspect yjl --format '{{json .Mounts}}'
```

确认容器可用后，将工具复制到容器内。把第一行源路径改成实际上传目录：

```bash
docker exec yjl mkdir -p /data/yjl/topk/tools
docker cp /YOUR/UPLOAD/topk-950pr/. yjl:/data/yjl/topk/tools/
docker exec -it yjl /bin/bash
```

`/data/yjl/topk` 是这里选择的**容器内目录**。若已有 yjl 仅挂载了 `/home`，这里不会自动与宿主机共享；可以继续使用 docker cp 传入/取出，或把后续 TOPK_ROOT 改为 `/home` 下你获准使用且已挂载的私人目录。不要为了增加挂载删除已有容器。

## 3. 容器内：获取个人 fork

首次执行，目录必须不存在：

```bash
mkdir -p /data/yjl/topk
git clone --branch main https://github.com/sgcg1/TileOPs.git /data/yjl/topk/TileOPs
git -C /data/yjl/topk/TileOPs fetch origin --tags
git -C /data/yjl/topk/TileOPs status -sb
git -C /data/yjl/topk/TileOPs log -1 --oneline
```

已有 checkout 时用 README 的“后续同步”，不要重复 clone 或覆盖源目录。

## 4. 容器内：加载环境

先激活现场已经准备好的私人 Python 环境，并加载实际 CANN 环境。镜像若已经设置有效的 ASCEND_HOME_PATH，可直接继续；若没有，先执行现场真实的 `source /实际/CANN/set_env.sh`。不要照抄旧服务器的安装路径。

```bash
export TOPK_ROOT=/data/yjl/topk
export TOPK_REPO="$TOPK_ROOT/TileOPs"
export TOPK_DEVICE=0
export TOPK_PYTHON=python3
export TOPK_SOC=Ascend950PR_9579
export EVIDENCE="$TOPK_ROOT/runs/newhost-$(date +%Y%m%d-%H%M%S)"
source "$TOPK_ROOT/tools/env.sh"
cd "$TOPK_TOOLS"
sha256sum --check MANIFEST.sha256
cd "$TOPK_REPO"
```

设备号和 SOC 以实际分配与芯片为准。需要由 env.sh 加载特定 CANN 脚本时，在 source env.sh 之前设置 `export CANN_ENV_SCRIPT=/实际/CANN/set_env.sh`。Python 必须满足项目要求的 3.12+、torch2.13.x，并有兼容 torch_npu 和主仓 Ascend TileLang。

**记下输出的 EVIDENCE。** 后续所有步骤在同一个终端、同一个实验目录执行。重开终端时重新激活环境，export EVIDENCE 为记下的原目录，再 source env.sh；新实验才换新的 EVIDENCE。

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

若使用容器内未挂载目录，需要取出允许导出的摘要，可在**宿主机**使用：

```bash
docker cp yjl:/data/yjl/topk/runs/实际实验目录/summary-decode-local.json ./
```

先在保密环境内审核文件是否允许出域。完整流程、失败定位和可选诊断见 README。
