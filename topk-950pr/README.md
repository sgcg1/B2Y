# TopKSelect 950PR 新服务器工具包（20261031-r3）

**第一次使用只看 [START_HERE.md](START_HERE.md)**，按“宿主机 → yjl 容器 → 个人 fork → 预检 → 14项 → Decode → 完整Prefill”逐步执行。这里是补充说明和故障定位。

## 交付内容与当前状态

- 实现代码唯一同步入口：`https://github.com/sgcg1/TileOPs.git` 的 `main`。
- B2Y 仅放本工具目录；服务器不克隆 B2Y。可下载 B2Y 的 `deliveries/topk-950pr-tools-20261031-r3.zip`，解压后手动传入所需子目录。
- 包中没有 TileOPs 实现源码副本、镜像、SDK、旧服务器 .om/缓存、凭据或业务数据。历史对照代码由脚本从个人 fork 标签读取。
- `SOURCE.json` 给出已知源码哈希、参考 main 提交和实际通过14项的源码提交。旧服务器 H128 默认已在独立缓存下通过14项；**新服务器必须重新验证**。H256仍为试验配置，v0.1.4尚未完成四组性能验收。
- 不需要、也不会连接你的新服务器。原始输出留在现场，回传方式见 RESULTS_TEMPLATE.md。

本版目标固定为已有 **yjl** 容器，基础镜像 Weekly **20260930**，私人目录 **/home/y00937463**。/home 已挂载共享；使用容器内 python3，不执行 Conda 激活、宿主机pip安装或重新创建容器。env.sh默认目录、所有命令和SOURCE.json均已按这个配置更新。

## 文件地图

| 文件 | 用途 |
| --- | --- |
| START_HERE.md | 按执行位置排列的完整操作步骤 |
| DOCKER.md | 镜像、已有yjl、首次创建、shell代理与离线导入 |
| DEPENDENCIES.md | 私人Python/CANN/主仓TileLang要求，缺项处理 |
| RESULTS_TEMPLATE.md | 可手填、可审核的最少回传摘要 |
| SOURCE.json / MANIFEST.sha256 | 源码参考与工具完整性 |
| env.sh | 选择设备/SOC/源码目录；每轮独立缓存、tmp、日志 |
| run.sh | 分阶段执行；失败即退出；不覆盖旧输出 |
| provenance.py | 防止一轮中混入不同源码、工具、Python、设备或缓存 |
| preflight.py | 模块路径/版本、真实NPU运算与512KiB往返拷贝、库哈希 |
| control_portable.py | 同进程初版/v0.1.2/H128/H256，正反顺序、固定输入 |
| clock_check.py | 设备事件与包围它的主机单调时钟交叉核对 |
| frequency.py | 单worker/56核以内的诊断负载期间只读遥测；不调频 |
| transfer_check.py | 不导入TileLang的最小传输诊断 |
| binary_check.py | 同源对照的实际主机库、设备缓存键/二进制哈希 |
| measure.py | 四组预分配原始kernel事件与独立profiling |
| summarize.py | 检查14项JUnit、50/50采样、相同commit和本轮输入 |
| cann/ | 官方TopKV2模型构建入口、协议头、基线测量和真实记录汇总 |

## 后续更新源码

在容器内、没有测试运行时执行：

```bash
cd "$TOPK_REPO"
git status --short
git remote -v
git switch main
git pull --ff-only origin main
git fetch origin --tags
```

工作区必须干净，origin必须是个人fork。dirty时先另外保存差异，不reset/clean覆盖。实现修改优先本地main提交并推送，再由你在服务器pull；每次改代码后换新EVIDENCE并重新preflight。工具修改也先经B2Y同步并更新清单，不在已有实验中混用不同脚本。

如果服务器不能访问GitHub，应先使用现场获准网络/代理渠道。也可在获准中转电脑从个人fork完整克隆、制作Git bundle，经获准文件通道传入（**不把源码bundle提交到B2Y**）：

```bash
# 中转电脑已有git即可，不需要Docker；在新目录操作。
git clone --branch main https://github.com/sgcg1/TileOPs.git TileOPs-transfer
git -C TileOPs-transfer fetch origin --tags
git -C TileOPs-transfer bundle create ../TileOPs-main.bundle main --tags
```

容器首次获取：

```bash
git clone --branch main /实际传入路径/TileOPs-main.bundle /home/y00937463/TileOPs
git -C /home/y00937463/TileOPs remote set-url origin https://github.com/sgcg1/TileOPs.git
```

已有checkout离线更新：

```bash
git -C "$TOPK_REPO" status --short
git -C "$TOPK_REPO" fetch --tags /实际传入路径/更新后的TileOPs-main.bundle main:refs/remotes/origin/main
git -C "$TOPK_REPO" merge --ff-only origin/main
```

这保留个人fork历史和标签，不通过B2Y覆盖源码文件。只下载GitHub源码ZIP不含Git历史，无法执行历史对照和commit核查。

## 每轮输出和缓存

```text
EVIDENCE/
  run-context.json         # 此轮身份；运行期间不改代码或工具
  environment.json         # 内部环境详情，不要求导出
  candidate/
    tests.log, tests.xml
    decode.json, small.json, prefill-k1024.json, prefill-k2048.json
    profile-*/             # 每次独立PID目录
  control-decode-1/, control-decode-2/
  clock-check.json, frequency-load.json
  cann/
    decode/                # 当前机器重新构建的模型和独立profiling
    prefill-k1024/
    prefill-k2048/
  cache/, logs/            # 本轮私人缓存和日志
  summary-decode-local.json / summary-all-local.json
```

旧服务器存在原缓存下等待、独立缓存下通过的现象，根因尚未证明。本包默认每轮新目录、新缓存，保留失败证据；不复用旧服务器缓存，也不自动删除目录。重开终端继续同一轮时必须显式恢复同一个EVIDENCE。切换环境、工具或源码后应新建一轮。

## 测量和验收口径

- 正确性必须14项真实通过，JUnit不得有skip/error/failure；不因随机输入证书通过就跳过NaN/Inf/±0、全同分、K>2048、窗口和分组测试。
- 每组50次非profiling设备事件，另发60次profile请求并按设备时间取最后50条真实记录；不足50条就失败，不补造、不选最快、不聚合重跑的旧trace。
- 事件、profiling分别记录。CANN静态模型事件含模型调度，不冒充纯内核；两列来自独立采样，不能相减得出精确开销。
- 新服务器完整FP32输入在本轮CANN/TileLang之间必须逐字节匹配。新torch/RNG序列不同于历史允许记录为新批次；输入哈希不匹配时summary拒绝计算倍数。
- 性能倍数 = 本轮CANN纯内核中位数 / TileLang纯内核中位数。128行诊断规格没有同规格官方基线，不换算×Ascend C。
- 全部四组kernel Python源码哈希必须一致；生成C++因shape/K不同不要求一致。
- summary只是完整性检查，不自动批准版本或打标签。旧服务器结果不作为新机器性能目标，也不通过MFU/95%宣传达标。
- 当前host默认H128、workers=min(rows,实际Vector核数)、L65536/K1024直接FP32，其余粗筛。命令行覆盖线程/worker只做诊断，不会改默认。最终默认变化必须进入个人fork，并重新做完整契约和四组测量。

## 可选调度实验

先确认实际Vector核数足够，再用小规格；每个version仅跑一次。下例是相近时段独立进程，不叫同进程AB/BA：

```bash
"$TOPK_PYTHON" "$TOPK_TOOLS/measure.py" --version tune-w32 --case small --workers 32 --threads 128 --profile-samples 50
"$TOPK_PYTHON" "$TOPK_TOOLS/measure.py" --version tune-w56 --case small --workers 56 --threads 128 --profile-samples 50
"$TOPK_PYTHON" "$TOPK_TOOLS/measure.py" --version tune-w56-repeat --case small --workers 56 --threads 128 --profile-samples 50
"$TOPK_PYTHON" "$TOPK_TOOLS/measure.py" --version tune-w32-repeat --case small --workers 32 --threads 128 --profile-samples 50
```

H64/H128/H256受支持。不要拿单次最小值改默认，也不把诊断结果放进正式candidate文件冒充默认配置的验收。

## 故障定位顺序

1. **preflight失败**：看最后一个IMPORT/TRANSFER阶段、Python是否3.12+、torch是否2.13.x、主仓Ascend是否真的安装、实际SOC是否与TOPK_SOC一致。环境安装看DEPENDENCIES.md。
2. **健康不是OK**：先由平台管理员处理；不重置共享卡或升级驱动。
3. **test超时**：保留首个完整栈。超时在CPU→NPU或NPU→CPU拷贝不证明TopK算法错误。另开新实验可用 `bash "$TOPK_TOOLS/run.sh" transfer`；默认和单CPU线程都不是自动修复。
4. **延迟显著漂移**：先control两轮，必要时执行 `bash "$TOPK_TOOLS/run.sh" binary`（需control 1已完成）。binary_check依赖主仓当前缓存API，版本布局变化时保留错误，不虚构二进制哈希。
5. **计时可疑**：clock记录设备时间和从begin.record之前至end.synchronize之后的主机区间。主机区间含提交/同步开销，不是纯内核；不依据一次读数手工缩放时间。
6. **频率低**：frequency在约8秒单worker和约8秒多worker负载期间查询common/usages。Aicore字段不能直接证明Vector同频；低利用率也可能自然低频。确认持续负载与频率策略，不执行set命令。
7. **CANN构建失败**：看单case目录compile.log/model-build.log。保留must_keep_origin_dtype、largest=true、sorted=false、INT32 indices、sort_policy=0、dim=-1；不要换成自写TopK或INT64+Cast基线。
8. **CANN等待**：benchmark打印SET_DEVICE/LOAD_MODEL/INPUT_SYNC/WARMUP标记，按最后阶段定位。不要只加大timeout或丢弃失败日志。
9. **profiling失败**：检查真实kernel记录是否足够、目录是否唯一。自定义FFI算子可能出现ACL→NPU flow mapping错误；不能仅凭错误名抹掉所有数据，也不能假称调用链已验证。保留警告并核实底层任务。

若需修改辅助脚本适配SDK，请在工具源目录修改，重新生成MANIFEST.sha256，再新建EVIDENCE；不要在已有结果目录悄悄修改build.cpp或拼接旧输出。全部路径与设备按新服务器实际配置，不包含旧服务器登录信息。

维护已有清单中的文件时，可在工具目录执行以下命令，只更新已列入包的文件，不把本机配置或结果加进清单：

```bash
cd "$TOPK_TOOLS"
python3 - <<'PY'
import hashlib
from pathlib import Path
manifest = Path('MANIFEST.sha256')
names = [line.split('  ', 1)[1] for line in manifest.read_text().splitlines()]
lines = []
for name in sorted(names):
    path = Path(name)
    assert not path.is_absolute() and '..' not in path.parts
    data = path.read_bytes().replace(b'\r\n', b'\n')
    path.write_bytes(data)
    lines.append(hashlib.sha256(data).hexdigest() + '  ' + name)
manifest.write_text('\n'.join(lines) + '\n')
PY
```

保留工具diff，并在允许的范围通过B2Y同步；新增工具文件应由包维护者一并加入清单。

## 验证范围

工具基于旧服务器已经实际运行的对照、时钟、频率和传输检查整理。本次整理另外执行Python/Ruff/Bash静态检查、压缩包/清单校验和离线正反例汇总验证；**尚未在你的新服务器或yjl镜像内实测**。旧服务器14项通过不能替代新环境验收。
