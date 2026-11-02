# A1同步警告：最小编译复现r2

上一工具在n4096-uint8代码生成时报SimtVF不支持uint8x2，未完成dtype对照。r2去掉缓存零值else写，改为始终写入已截断digit；消费循环改为serial tile+Parallel(128)分块，尝试避免不支持的向量类型。具体哪次向量化产生uint8x2尚未取得pass IR，不能断言已修复。新工具逐配置捕获失败并继续，结束时可能completed_with_failures；无论状态都需要回传。现场同步分析源码在首配置前只读保存，避免首项失败丢失证据。


当前不是新优化性能测试，也不是正式修复。A1保持默认关闭。源码静态检查发现0176ba14的PointerAccessIsDisjoint直接比较touched元素区间，未像普通访存路径按dtype.bytes()换算；这可能使uint8缓存与int32原子地址发生混合单位误判。尚未获得具体冲突访问对，不能把全部警告认定为误报。

本工具只编译四个最小kernel，不执行kernel、不测性能、不改TileLang安装或共享环境。两个N（4096/16384）×uint8/uint32缓存，保留同一cache写+hist原子模式，生成源码与完整编译日志供定位。若只在特定uint8布局出现警告，则支持单位误判假设；若全部出现或没有复现，应以实际布局及访问对进一步判断，不能强行归因。uint32仅是诊断对照，不是已决定的产品方案，会增加缓存开销。

## 操作

沿用已加载CANN的yjl容器和原Python。仅需更新B2Y，不重跑A1 r2，不改TileOPs源码。若在宿主机，先进入容器；已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内：

```bash
git -C /home/y00937463/B2Y pull --ff-only
```

更新成功且现有CANN环境已加载后：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-a1-sync-repro-r2/run.sh
```

新建私人/home/y00937463/topk-a1-sync-repro-r2-时间-进程号，单个Python进程和全新cache/tmp/logs。日志以SYNC_COMPILE_BEGIN/END标记各配置；保存四份C++、SHA和工具身份。如果已存在/home/y00937463/tilelang/src/ascend/transform/thread_storage_sync.cc，会只读保存其原文和SHA以核对服务器实际源码，不改编译器或安装。

成功或失败均将打印的AAA_Results文件按现有方式直接上传。脚本只启动一次诊断进程，不需重复执行。completed仅表示编译采集完成，不是同步风险已解除。本地Python与Bash语法检查通过，但新前端编译尚待现场。
