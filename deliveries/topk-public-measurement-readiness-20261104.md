# TopKSelect公共协议正式测量就绪检查

2026-11-04。用户要求按目标仓公共协议得到正式设备耗时，并确认只能使用现有yjl容器。结论：目前不能生成目标仓认可的正式耗时；不生成替代成绩、不运行已知不匹配的空耗测试。没有新增NPU运行。

## 已核实的阻塞

1. 目标分支冻结为yyttt6/TileOPs:ascend950，f0072a85a3ce1a4bcc520ba12cd09a0337871131。其验收锁为ascend950-arm64-v1：Ascend950DT_9582（32 Cube/64 Vector）、Python3.12.15、CANN9.2 release编译器+9.1 runtime/OPP兼容组合、受指纹约束的TileLang0.1.15等。此前yjl为950PR、Python3.12.14、CANN9.3及0176ba14工具链。不是可互换的验收环境。
2. 正式设备任务要求共享host npu-guard、宿主锁和进程可见性；不能用容器私有锁代替。现有环境没有已确认的站点验收配置，不能猜测其已满足，也不删除/重置锁。
3. 当前目标分支公共launcher性能模式强制clock-config，使用3 warmup、15独立profiler session、每次1GiB L2 eviction，读取原始FFTS记录，对多kernel设备执行区间并集取算术平均。没有获批站点配置不能绕过；不修改共享时钟/安装来强行适配。issue与当前文档时钟表述有版本差异，应采用维护者确认的当前入口，不能静默选宽松版本。
4. 目标分支尚未注册TopKSelect Ascend kernel；公共runner先检查注册，直接运行会在测量前拒绝。当前实验分支和目标分支后端/目录接口不同，原始probe函数并非已接入公共Op的候选。需要先在ascend950的独立分支移植薄注册/接口，冻结用户指定Decode b1范围并通过公共正确性；不能测到旧默认或GPU实现后声称测了我们的候选。

只满足“脚本能启动”或包版本字符串为0.1.15，不足以满足该仓认证；公共runner部分宽松检查也不能替代CI的工具链二进制/头文件校验。

## 当前成绩状态

正式设备耗时：未知/未测。历史随机约54–55μs为开发事件计时；已有独立profile的设备阶段、包络及中位数也不符合该正式协议，不能改名复用。网页ops-math43.7μs仍是有待匹配来源/协议的baseline快照，不将其与开发事件强行相除形成验收成绩。

在现有950PR容器上，后续可另取得“950PR开发环境、采用公共计时方法”的设备数据；这需要合法宿主预约和站点时钟条件，且环境标签必须保持非canonical，不宣称正式验收或与网站数据直接可比。用户本次只确认环境，尚未改变正式验收目标，因此本检查不擅自降级为另一种测量。

## 解阻顺序

- 在当前冻结ascend950上准备候选接口/注册，保留GPU与公共契约，代码及源身份可审查；这只是接入，不叠加算法优化。
- 在维护者提供的canonical server2或等价已认证站点，通过环境/CPU检查和本case公共正确性，使用站点guard与时钟策略运行公共性能入口。
- 只读取最终passed且非verify-only的收据与完整15次原始设备样本；回传源码/输入/环境指纹、离散情况、正确性及原trace，然后报告设备时间均值和合法baseline比值。

尚未取得该环境的可用入口和候选接入验证，不能提供“现在直接在yjl执行即可得到正式耗时”的命令，也不要求用户反复运行旧r14。没有访问或变更维护者server2，没有发送issue评论或提交PR。算法优化仍暂停，本次测量请求仅覆盖接入与验收准备。

来源：[公共性能与CI说明](https://github.com/yyttt6/TileOPs/blob/f0072a85a3ce1a4bcc520ba12cd09a0337871131/docs/ascend950/pr-performance.md)、[工具链锁](https://github.com/yyttt6/TileOPs/blob/f0072a85a3ce1a4bcc520ba12cd09a0337871131/config/ascend950-toolchain.json)、[公共runner](https://github.com/yyttt6/TileOPs/blob/f0072a85a3ce1a4bcc520ba12cd09a0337871131/benchmarks/ascend/runner.py)。对应读取文件SHA在同名JSON保留。
