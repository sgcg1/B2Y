# 同步最小复现r2：编译完成，但未重现生产警告

四配置均编译成功，无失败记录，日志无ThreadSync警告。工具身份与发布一致，四份C++逐份SHA复核，现场thread_storage_sync.cc SHA为3da37679bc87e3f2d6eb3c9ce133abfd5d44da7ba02f5528bf30f3f9836a7dda，与官方0176ba14下载源码逐字节一致。原始Git blob来自cb6ecf5，逐字节归档；提取源码是原文的派生副本，不替代原始回传。

- n4096-uint32.cpp: asc_syncthreads静态出现次数 0。
- n16384-uint8.cpp: asc_syncthreads静态出现次数 2。
- n4096-uint8.cpp: asc_syncthreads静态出现次数 2。
- n16384-uint32.cpp: asc_syncthreads静态出现次数 0。

两种N的uint8版本均在cache写与hist原子之间生成屏障，uint32版本没有。两数组物理上不重叠：uint8 cache字节[0,N)，hist在[N,N+1024)；uint32 cache字节[0,4N)，hist在[4N,4N+1024)。新复现写cache[i]由各线程独占，hist全用atomic_add，跨VF后才读两者。在此访问模型中cache与hist之间没有真实数据依赖；不同屏障结果支持混合dtype导致多余依赖判断的假设。结合源码PointerAccessIsDisjoint未统一元素单位，疑点更具体，但仍未直接导出分析器中的具体冲突对。

本轮把cache写放在原子条件之外，屏障因此可位于所有线程可达的位置，不再触发外提警告。此结果没有重现A1原有的分支内部冲突，不能将“最小复现没有警告”写成“A1同步安全”。也不能把额外屏障代价映射成生产约1%的收益或承诺。

没有执行任何kernel，也没有正确性或性能样本。A1仍默认关闭、accepted=false。下一步应回到固定A1生成布局，对照原三个警告条件定位访问对：重点核查uint8 cache与hist/state等int32原子地址的混合单位；将可能相关的读写移到线程一致的区域或用独立VF分隔时，必须保留窗口初始化与首轮/溢出语义，不能靠T.assume或关闭检查器隐藏警告。不要重复运行此编译复现。
