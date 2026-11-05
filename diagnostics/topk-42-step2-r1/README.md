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
