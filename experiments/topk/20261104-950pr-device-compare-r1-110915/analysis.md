# 950PR对照首轮失败分析

来源：用户上传提交`55f8045`。原始JSON与log逐字节存于raw，SHA和字节数见metadata.json；ge-build.decoded.log是从JSON内Base64无损解码的摘出证据，非补造现场日志。

四个自研kernel均完成编译。失败阶段是`build-ge`，在GE初始化内部的Python `multiprocessing.Manager`创建AF_UNIX监听地址时抛出`OSError: AF_UNIX path too long`。其后GE输出EC0009“资源不足”；因有明确更底层错误，不据此诊断内存不足。

原工具将TMPDIR设置为`/home/y00937463/topk-950pr-device-compare-r1-20261104-110915-176844/repeat-1/tmp`。该目录追加CPython的pymp及listener文件名后超过Linux Unix-domain socket地址长度限制。此路径是本轮脚本引入的问题，与TopK算法是否正确或性能是否达标无关。

修复仅改工具：使用`/tmp/tk-随机值`的独立700权限短目录；TMPDIR/TMP/TEMP仅对子进程树生效，不修改系统配置；在加载NPU运行时前检查socket路径长度并实际执行一次标准库Manager预检。编译缓存与设备记录仍保留在原私有运行目录。记录短目录路径供排查，不删除此前运行产物。GE失败时直接将底层日志打印到回传log。

该轮尚未执行正确性核验及设备计时，因此没有可用耗时或性能倍数。修复后才可重新运行这轮同规格对照；不需要改内核、重建容器或重置NPU。
