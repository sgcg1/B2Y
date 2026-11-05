# 第2步宿主配置已核对

镜像为cann9.3.0 weekly，runtime=ascend；映射davinci0..7及manager/hdc；bridge网络无端口映射；IPC=shareable、shm64MiB；SYS_ADMIN、seccomp=unconfined；非privileged。六项bind含/home和驱动/DCMI等。原始字节及SHA见metadata。

方案：保留原yjl，创建独立yjl-topk-guard验证容器，使用原容器可写层快照保留工具链，只映射卡0和管理设备，复用原挂载，再增加host PID和真实宿主共享锁目录。共享/home仍是同一数据源，不等于隔离副本；验证不修改旧源码和公共reference。快照不包含bind数据，也不是内存/checkpoint恢复。docker commit会短暂暂停原容器，因此只在原容器无任务时手动执行配置脚本。

本轮仅准备脚本，没有在远端生成镜像/容器、安装或执行NPU。guard使用冻结目标仓4409536e的原始脚本，不修改预约校验。站点安装后的实际预约/进程验证和BMM收据仍须回传；不因配置命令执行就宣称canonical认证通过。
