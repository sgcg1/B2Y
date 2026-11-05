# 第3步：TopK公共后端接入，原yjl开发验证

用户最新要求覆盖此前配置安排：跳过第2步剩余事项，直接使用原yjl；不执行host-setup/verifier-run，不要求新容器。第2步只记录CPU passed，BMM/共享预约/canonical环境未完成，不伪造通过。

## 执行

更新B2Y，在**原yjl容器**加载已有CANN环境后运行：

```bash
cd /home/y00937463/B2Y
bash diagnostics/topk-42-step3-r1/run.sh
```

原环境已有Python/CANN/TileLang保持不变，不安装包、不下载依赖、不修改原TileOPs checkout。用此前B2Y的冻结基础bundle及本次增量bundle还原独立目录；不需要GitHub访问。依赖diagnostics/topk-42-step2-r1的三份原始bundle，请完整更新B2Y。

## 改动与顺序

目标起点4409536e，候选727132f7，分支codex/topk-select-ascend950-42。新增Ascend attention模块导入、Kernel/Interface实现及register_kernel_type，公共Op、manifest、workload/reference、GPU实现未改。

先复用个人main已有精确radix内核表达（逐字节移植），不是新算法或性能升级。adapter只服务用户冻结的ds-v32-topk-decode-b1：FP32[1,1,16384,1]、K2048、int32 starts/ends/output；其他规格明确refusal。一行单block，无28/32核数硬编码。

先跑候选公共CPU检查，再检查公共Op能选中AscendTopKSelectKernel并完成编译；ThreadSync诊断则不执行。第3步完成后，同一脚本才调用公共benchmark_case、manifest case binder和原verification进行完整输出/输入保护检查，不重新写reference或放宽精度。只验证冻结Decode case，边界回归待此入口跑通后补齐第4步；不调参、不计时，不进入第5步。

CPU检查后显式导入源后端tileops.ascend，使未安装tileops元数据的yjl能验证源注册；这不是已安装entry-point自动发现验收。保留该限制。使用私人flock和卡0占用预检，仅开发检查，**没有宿主共享guard/正式公共launcher收据**。运行时不要启动其他设备任务，检测占用时不绕过。

## 回传

上传AAA_Results中新topk-42-step3-r1-时间-PID.json和topk-step3-console-*.log；或JSON全部分片+manifest+console日志。成功失败都上传。报告保留源码SHA、CPU receipt、选中Kernel、CPP与异常。development_decode_correctness_passed只表示开发case正确性，不等于正式验收、全部边界或新算法验证通过。
