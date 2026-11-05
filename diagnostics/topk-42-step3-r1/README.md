第3步已完成，当前下一步为[第4步12项边界回归](../topk-42-step4-r1/README.md)，更新TileOPs至c70ffa3a。下文r1脚本只接受历史727132f7，不要更新后重复运行旧入口。

## 本轮结果与后续交付方式

**第3步已通过，不需要重跑。** 公共Op分派/编译/调用及完整Decode输出检查通过，CPU279+101项通过/14 skip，详见[归档分析](../../experiments/topk/20261105-roadmap-step3-r1-142731/analysis.md)。无性能计时；下一步第4步边界/确定性回归，尚不调参。

按用户新指示，实现已直接推送[个人fork开发分支](https://github.com/sgcg1/TileOPs/tree/codex/topk-select-ascend950-42)，源码727132f7。当前脚本已改为读取已有checkout，不再还原bundle；下文旧bundle描述仅为历史运行方式。

后续在服务器更新TileOPs（先确认原工作区改动已保留；命令不含reset或强推）：

```bash
cd /home/y00937463/TileOPs
git fetch origin
git switch codex/topk-select-ascend950-42
git pull --ff-only
```

B2Y照常更新。当前run.sh默认TileOPs路径/home/y00937463/TileOPs，实际路径不同时用TILEOPS_REPO=/实际路径/TileOPs bash diagnostics/topk-42-step3-r1/run.sh。脚本核对完整727132f7 SHA及已跟踪文件无改动，失败不自行切换/覆盖代码。只在需要复现本轮时运行；下一轮边界测试会提供单独入口。无需pip安装或变更环境。

# 第3步：TopK公共后端接入，原yjl开发验证

用户最新要求覆盖此前配置安排：跳过第2步剩余事项，直接使用原yjl；不执行host-setup/verifier-run，不要求新容器。第2步只记录CPU passed，BMM/共享预约/canonical环境未完成，不伪造通过。

## 执行

更新B2Y，在**原yjl容器**加载已有CANN环境后运行：

```bash
cd /home/y00937463/B2Y
bash diagnostics/topk-42-step3-r1/run.sh
```

原环境已有Python/CANN/TileLang保持不变，不安装包、不下载依赖。当前脚本读取上文已有TileOPs checkout，不改动源码；原bundle运行结果保留供溯源。

## 改动与顺序

目标起点4409536e，候选727132f7，分支codex/topk-select-ascend950-42。新增Ascend attention模块导入、Kernel/Interface实现及register_kernel_type，公共Op、manifest、workload/reference、GPU实现未改。

先复用个人main已有精确radix内核表达（逐字节移植），不是新算法或性能升级。adapter只服务用户冻结的ds-v32-topk-decode-b1：FP32[1,1,16384,1]、K2048、int32 starts/ends/output；其他规格明确refusal。一行单block，无28/32核数硬编码。

先跑候选公共CPU检查，再检查公共Op能选中AscendTopKSelectKernel并完成编译；ThreadSync诊断则不执行。第3步完成后，同一脚本才调用公共benchmark_case、manifest case binder和原verification进行完整输出/输入保护检查，不重新写reference或放宽精度。只验证冻结Decode case，边界回归待此入口跑通后补齐第4步；不调参、不计时，不进入第5步。

CPU检查后显式导入源后端tileops.ascend，使未安装tileops元数据的yjl能验证源注册；这不是已安装entry-point自动发现验收。保留该限制。使用私人flock和卡0占用预检，仅开发检查，**没有宿主共享guard/正式公共launcher收据**。运行时不要启动其他设备任务，检测占用时不绕过。

## 回传

上传AAA_Results中新topk-42-step3-r1-时间-PID.json和topk-step3-console-*.log；或JSON全部分片+manifest+console日志。成功失败都上传。报告保留源码SHA、CPU receipt、选中Kernel、CPP与异常。development_decode_correctness_passed只表示开发case正确性，不等于正式验收、全部边界或新算法验证通过。
