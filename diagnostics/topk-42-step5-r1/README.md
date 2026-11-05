# 第5步：真实TileLang AutoTuner有限配置搜索

使用原yjl。TileOPs个人fork分支codex/topk-select-ascend950-42，源码8b27718757f42175dc940326a1278be22bf97c3d；新增tuning.py作为原内核TIR入口，生产默认Kernel及radix算法未改，不是新算法或已获得性能提升。目标PR仍yyttt6/TileOPs:ascend950。

## 更新与执行

在原yjl更新TileOPs，先保留已有改动，不使用reset：

```bash
cd /home/y00937463/TileOPs
git fetch origin
git switch codex/topk-select-ascend950-42
git pull --ff-only
```

更新B2Y、加载原有CANN环境后：

```bash
cd /home/y00937463/B2Y
bash diagnostics/topk-42-step5-r1/run.sh
```

源码路径不同时设置TILEOPS_REPO=/实际路径/TileOPs。脚本核对完整候选SHA及已跟踪文件无改动，不安装依赖、不改变共享环境、不重新创建容器，不用bundle。第2步余项按用户指示暂缓；继续私人flock/物理卡0占用预检，无宿主共享预约/正式收据，不并发运行其他NPU任务。

## 搜索空间及合法性

| H | PARALLEL_SCAN | 作用 |
| ---: | --- | --- |
| 128 | true | 已通过第4步的原配置，必须保留 |
| 64 | false | 较小SIMT线程组，串行小扫描 |
| 128 | false | 固定线程数对比扫描调度 |
| 256 | false | 较大SIMT线程组，串行扫描 |

H=256并行扫描已知有问题，不进入候选。W固定1：本case只有1行，增加空闲block不增加有效并行度。其余算法/缓冲/粗桶/缓存开关保持原值，不同时混入算法优化。原配置经Kernel.tuning_candidates合入，参数名对应builder的H/PARALLEL_SCAN且实际改变TIR。

## 实际执行顺序

1. 公共Op原配置先编译并复查manifest Decode；保留ThreadSync守卫。
2. 保存现场AutoTuner模块原文SHA和方法签名；契约不支持则明确失败，不换手工计时冒充AutoTuner。
3. 各候选编译，保存CPP与stderr；编译失败/同步诊断分别记录并不执行。基线必须通过，至少2档通过才搜索。
4. 各可执行候选调用源仓12项边界测试的同一测试体，各3次。这里将其调用入口绑定到待测compiled program，以验证各配置；使用的reference/validator/输入保护/确定性规则不改。**这是候选kernel回归，不假装每个候选已成为公共Op默认配置**。若出现运行/正确性错误立即停止。
5. 调用真正的AutoTuner.from_kernel(...).set_compile_args(target=ascend,out_idx=[3]).set_profile_args(...).run()，仅搜索已验证候选。同一固定随机完整窗口输入，显式供给正确starts=0、ends=16384，绝不随机生成整数窗口。
6. 保存优选config、源码、选择latency及可用on_trial事件/完整console，确认搜索输入位模式未改变；优选kernel再跑12项各3次。

AutoTuner内部skip_check=True是**显式采用前置公共完整验证**：索引输出无序且tie集合可能与torch.topk不同，不能用通用逐元素allclose代替语义验证。所有入选配置已在计时前跑过原测试体；优选后再回归，不把内置not_run标成内置验证通过。ref_prog不再交给tuner作索引逐位置比较，不影响公共reference在前后检查中执行。

## 计时边界与结果解释

使用AutoTuner的event配置选择后端，warmup参数25、rep参数50，具体循环/时长由现场库实现，源码随结果保留；这不等价于正式3次warmup/15次独立profiler。只用于当前随机输入选配置，不能当作正式设备耗时、不能与旧FFTS或截图数据直接相除。不会升级工具链来适配；现场AutoTuner不支持NPU或签名不同则保留实际错误。

当前默认仍不变。拿到搜索结果后先审查各配置是否实际完成测量、收益是否可信，再将优选配置接回公共Kernel并完整回归；不会自动把单次最快配置当作稳定收益或算子验收成绩。

## 回传

上传AAA_Results/topk-42-step5-r1-时间-PID.json、topk-step5-console-*.log；或JSON全部分片+manifest+console。失败同样上传，原始私有目录保留，避免盲目重复。报告含现场API源码、候选CPP/诊断、各候选回归、tuner事件、winner与前后输入保护。

本地仅语法、4档参数合法性/去重/基线保留检查及生产源码未变核对通过；现场编译、AutoTuner、正确性及耗时均待回传。没有预报收益。
