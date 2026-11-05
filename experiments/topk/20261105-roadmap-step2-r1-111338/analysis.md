# 4.2 第2步：CPU检查通过，设备环境尚未闭环

收到提交264cee2，工具51ae902，冻结源码4409536e1f0dba8dca7141d6aee6fc6677afa9ce。直接JSON与分片解压逐字节一致，分片/压缩/原文及全部内嵌证据SHA通过，JUnit独立重新计数通过。

| 公共检查 | 结果 |
| --- | --- |
| manifest schema/signature/bench | passed |
| contracts | 279 passed，0失败/错误/跳过；日志另有2 deselected |
| benchmark-contracts | 101 passed，14 skipped，0失败/错误 |
| packaging-coverage | passed；44项收集属于覆盖检查，不是44项设备执行通过 |
| CPU最终receipt | passed |
| BmmFwdOp公共verify-only | 未执行，无设备收据 |

14项skip来自未修改的公共CPU测试规则，不计为通过。test_ascend_toolchain.py通过表示工具链检查逻辑的单元测试通过，**不是现场二进制/环境锁已通过认证**。tileops包元数据为not_installed，CPU用源路径可导入；不能推断NPU后端entrypoint已经安装可用。

## 阻塞及证据边界

预期/usr/local/libexec/ascend-npu/npu_guard.py不存在，/proc/self/mountinfo未显示/run/lock/ascend-npu的独立挂载。只说明当前探针未发现所要求的入口/挂载，不证明宿主机上没有guard，也不排除合法站点采用其他共享配置。没有运行BMM、访问NPU或生成性能数据；next_step_allowed=false。

保持第2步，不能因CPU passed就提前开始第3步移植。无需原样重跑CPU，它不会修复共享预约。下一步先确认宿主共享guard、锁挂载及宿主PID可见性；由站点维护者提供审计入口/配置和现有PR环境的开发使用认可，或提供满足其规范的环境。不能安装一个容器私有guard冒充宿主共享预约。

## 后续

见[环境阻塞处理说明](../../../deliveries/topk-roadmap-step2-environment-blocker-20261105.md)。不自动更换CANN/TileLang，不修改公共CI、reference或验收锁。保留原冻结源码目录与CPU收据；环境可用后补BMM收据，再进入第3步。现有直方图回传保留，暂停性能路线推进。
