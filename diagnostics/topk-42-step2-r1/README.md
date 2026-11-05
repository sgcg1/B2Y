## 当前操作：独立验证容器（配置已核对，无需继续采集）

**先确保yjl没有正在运行的任务。** 下面第一条命令创建可写层快照，Docker会在快照期间短暂暂停yjl；不删除/重建原容器，但需在空闲时执行。快照可能占用较多本机磁盘，所需空间取决于原容器可写层。若磁盘不足则停止并回传错误，不清理其他镜像。

新验证容器名yjl-topk-guard，共享宿主PID和已有锁，只暴露卡0及管理设备；沿用原来的SYS_ADMIN/seccomp设置，host PID增加宿主进程可见性。/home仍共享，不能在新旧容器同时修改同一源码或运行设备任务。快照仅保留文件系统，不保存进程内存，bind数据由原挂载继续提供。镜像可能含本地认证配置，仅保留本机，不推送镜像。

更新B2Y后，在**宿主机**依次执行：

```bash
docker exec yjl cat /home/y00937463/B2Y/diagnostics/topk-42-step2-r1/host-setup.sh | bash -s -- --apply-when-yjl-idle
```

第一条成功后：

```bash
docker exec yjl cat /home/y00937463/B2Y/diagnostics/topk-42-step2-r1/verifier-run.sh | bash
```

第一条从yjl生成快照，创建验证容器，保留真实共享锁inode并输出主机/容器锁及PID命名空间标识。不会初始化、替换锁或影响其他卡。已有同名容器时拒绝覆盖。失败保留新镜像/容器用于排查，不自动删除。

第二条只在新容器本地editable注册冻结TileOPs，禁止下载/升级依赖；随后重新运行公共CPU（新容器包注册状态发生变化，故需重验）及通过原始公共guard运行BMM。使用冻结目标仓自带guard，不安装/修改宿主全局脚本，不伪装站点认证。guard负责设备空闲与外来进程检查，预约失败不绕过。

上传AAA_Results/topk-host-setup-*.log、topk-verifier-run-*.log，以及新step2 JSON或其全部分片+manifest。失败也上传现有日志。不重复运行首次host-inspect/host-config探针。

宿主检查已回传，**不需要再运行同一检查脚本**。当前需要落实[宿主预约配置](../../deliveries/topk-roadmap-step2-host-remediation-20261105.md)，并非重跑CPU或BMM。以下保留历史入口。

## 当前下一步：在宿主机只读检查

用户已确认可以进入宿主机终端。更新容器内B2Y后，在**宿主机**执行：

```bash
docker exec yjl cat /home/y00937463/B2Y/diagnostics/topk-42-step2-r1/host-inspect.sh | bash -s -- yjl
```

此命令不是在容器内运行。若容器名并非yjl，将命令中两处yjl改为实际容器名。脚本只查看guard候选文件、共享锁元数据、容器挂载及PID命名空间，不运行NPU、不创建锁、不重启容器、不打印环境变量或令牌。

结果自动写回容器B2Y/AAA_Results/topk-step2-host-inspect-时间-PID.log；上传该日志即可。先据结果决定是否复用已有宿主预约或需要站点配置；不盲目重建容器，也不原样重跑公共CPU。

本轮CPU检查已通过，BMM被共享预约条件阻塞；**不要原样重跑本脚本**。先阅读[结果](../../experiments/topk/20261105-roadmap-step2-r1-111338/analysis.md)与[环境处理说明](../../deliveries/topk-roadmap-step2-environment-blocker-20261105.md)。下文保留首次执行的复现入口。

# 4.2 第2步：公共环境检查（先完成此步）

遵用户要求跳过认领手续，其余严格按issue4.2顺序推进。停止新的算法/性能探针；上轮直方图修复保留，但先不要重跑。

已从目标仓最新ascend950建立本地独立分支codex/topk-select-ascend950-42，冻结起点4409536e1f0dba8dca7141d6aee6fc6677afa9ce。源码bundle按6MiB无损拆成3份以适配GitCode单文件10MiB限制，脚本自动拼接并校验整体SHA；无需手动合并。此bundle来自该分支的原始Git历史，不含历史个人main算法改动。脚本离线clone到新的私有目录，保留完整commit身份，不覆盖现有TileOPs，不安装依赖、不改环境、不推送目标仓。

## 现有容器执行

更新B2Y，在已运行yjl容器执行：

```bash
cd /home/y00937463/B2Y
bash diagnostics/topk-42-step2-r1/run.sh
```

脚本先校验bundle及源码SHA，记录包版本（不导入NPU），再执行**原封不动的公共CPU检查**：scripts/ci/ascend950.py --phase cpu。CPU子进程设置TORCH_DEVICE_BACKEND_AUTOLOAD=0，按公共CI支持方式避免CPU阶段自动加载NPU。失败立即停在第2步，不跳过失败测试/修改契约/自动安装任何依赖。

CPU通过后，只有检测到已有宿主guard脚本及共享锁挂载，才调用公共benchmark_ascend.py --op BmmFwdOp --verify-only。默认guard路径/usr/local/libexec/ascend-npu/npu_guard.py；已有站点可通过TILEOPS_NPU_GUARD指定其审计过的Python入口。不得把变量指向容器私有锁实现；不会新建挂载或修改共享配置。挂载检查采取保守策略，站点采用其他合法共享路径时需要维护者提供证据后修订，不盲目绕过。

公共guard仍负责真实进程/所有权检查。缺共享入口会记录blocked_host_guard_not_available；这不是TopK实现失败。950PR/CANN9.3与维护者环境锁不同，即使CPU/BMM通过，仍标environment_acceptance_pending，不冒充canonical环境通过。无需申请新环境后才回传：先把实际检查结果送回，明确剩余缺口。

## 回传

终端打印AAA_Results中的JSON、全部分片与manifest。上传JSON，或全部分片+manifest。JSON内嵌检查日志、公共receipt和XML；失败也保留，原始独立目录不会删除。

## 后续闸门

2：公共CPU检查、已有BMM收据、环境与共享预约证据齐备 → 3：移植首个正确TopK到公共kernel/注册接口 → 4：公共Op完整正确性及边界收据 → 5：有限合法AutoTuner配置搜索 → 6：瓶颈优化及全量回归 → 7：公共baseline与正式协议对照（缺维护者交付则待验收） → 8：面向yyttt6/TileOPs:ascend950的PR。

目前仅第2步准备完成，检查待服务器执行，后续步骤不提前勾选。既有单独TopKV2测量仅作开发诊断；不伪装维护者交付的baseline，也不把微基准填入正式成绩。
