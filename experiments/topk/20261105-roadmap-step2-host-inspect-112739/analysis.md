# 第2步宿主检查：预约条件不满足

收到提交f79c469，工具31a6ef4。保存Git提交中的原始日志字节与SHA；日志时间11:27:39 UTC，按原文记录，不与此前本地显示时区直接比较推导运行间隔。

## 已确认事实

- yjl运行中，Privileged=false，HostPID=2718947，PidMode为空。
- 宿主PID命名空间pid:[4026531836]，容器pid:[4026543727]，二者不同。
- 宿主/run/lock/ascend-npu及device-0.lock存在，锁文件mode666；存在/权限不证明当前锁持有人、合法性或无设备任务。
- 容器中对应目录/锁均缺失；当前挂载表没有该共享目录。
- /home为宿主与容器间读写bind挂载，驱动lib64/version、dcmi和npu-smi也有挂载。
- PATH和脚本列出的候选路径未发现guard。检索范围有限，不能断言整个宿主从未部署guard。

## 判断

CPU检查结果仍有效，但第2步尚缺共享预约条件和公共BMM收据。不能把宿主已有一个锁文件等同于yjl已经具备预约条件，也不能把独立PID命名空间下的容器私有guard当成站点host guard。

标准Docker不能仅通过docker update将运行中容器的PidMode改为host。若采用文档要求的host PID方式，需要经审查的容器配置变更或等效站点方案；不应直接停止/删除yjl、运行猜测的docker run命令。现有Python/CANN/TileLang可能在容器可写层，重用原始镜像不足以保留当前环境。必须先保留完整配置、可写层与数据，再安排停机。

下一步处理清单见[宿主配置说明](../../../deliveries/topk-roadmap-step2-host-remediation-20261105.md)。本轮无NPU调用、无配置变更。共享锁不得删除或重建，guard和设备配置由站点统一管理。严格顺序保持第2步，不推进第3步。
