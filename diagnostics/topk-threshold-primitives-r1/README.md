# 阈值路线关键原语r1：完整键、给定阈值收集与后端能力证据

2026-11-05。按用户要求继续测试。当前没有已确认签名/降型的向量histogram入口，故本轮**不猜API、不把O(256N)逐桶比较当成向量hist**。先测可审查的完整键与收集表达，同时采集当前安装后端的接口/源码证据，为下一步是否存在真正向量统计路径提供依据。

## 本轮已完成：无需重跑

两项24组×3次通过，键转换46.002μs、含键转换的收集67.951μs；10个计时窗口已复核，二者不可相加。本轮源码清单发现嵌套SIMD直方图实现与codegen线索，但未实际调用，完整T仍未验证。详见[结果及下一道关卡](../../experiments/topk/20261105-threshold-primitives-r1-102742/analysis.md)。以下为已完成实验的复现入口。

## 现有yjl容器执行

更新B2Y，保持原有Python/CANN/TileLang环境，在已运行的容器内执行：

```bash
cd /home/y00937463/B2Y
bash diagnostics/topk-threshold-primitives-r1/run.sh
```

固定Python `/usr/local/python3.12.14/bin/python3`，物理卡0，28核PR开发环境。计时kernel只启动1个block，不依赖32核或满28核。保留已有短TMPDIR/Manager预检、卡0占用检查与私人flock；不修改共享工具链、系统配置或频率，不重置卡。私人检查不等于共享宿主预约，运行时不启动其他NPU任务。

## 本轮具体做什么

| 项目 | 实际工作 | 结果范围 |
|---|---|---|
| encode_keys | 16384项FP32→完整canonical uint32键，按int32位模式输出 | 转换正确性与该独立表达设备时间；包含64KiB键GM写出 |
| collect_given_threshold | 单kernel载入分数、构建UB完整键、分组计数、128组小前缀、按阈值收集及稳定tie | 当前SIMT收集表达的正确性与成本，不是原生向量压缩 |
| backend_inventory | 只读枚举语言导出、签名/文档及限定后端目录内hist/sort/compress等源码线索 | 不执行未知API，不能据名字存在就判定能编译/高效 |

性能输入保持原case数据量：FP32分数16384项、全窗口、K2048，不缩为7/8。组件用扁平视图；不是完整公共TopKSelectFwdOp。收集kernel的**精确阈值由CPU oracle提供**，没有在设备上执行四轮阈值选择。因此时间不能作为完整T性能，也不能用于正式验收倍率。

完整键规则包括NaN最大、±0同分、其余按完整FP32数值次序。collect不丢弃边界精度、不分配2048候选桶、不使用逐元素atomic、库scan或库reduce；组内是SIMT串行计数/写出，组前缀是线程0的128项小循环。这是明确的可编译候选表达，**不是已确认的最快收集方式**。其时间高只说明该表达要被替换，不能证明所有原生向量收集都慢。

逻辑UB包含原分数64KiB+完整键64KiB和少量组计数/偏移；现场编译布局才是最终资源依据。源码索引有界、共享计数写在有效性分支之外；继续保留ThreadSync守卫，有诊断就不执行，不用无依据T.assume绕过。

## 正确性与计时

24组输入每方法各运行3次，包括随机、全同分、四级量化、接近FP32、NaN/±Inf/±0/次正规数、全负值、空/短/2048/2049/跨组窗口及混合分布。收集结果与独立数值排序选中集合核对；同时验证精确确定性输出、计数meta和输入位模式未改写。NaN输入保护按int32位模式比较，避免torch.equal对NaN的误判。

本地已经解释执行实际kernels.py的AST，48项检查通过，包含索引边界、padding和每个有效输出恰有一次收集写。CPU检查不等于设备编译与SIMT同步已经验证。

正确性通过后，每方法测同一份普通随机全窗口输入：3次窗口外预热、5个独立单调用原始设备profiling窗口，每次前1GiB int32驱逐并同步。要求1个逻辑任务，保留全部样本、编译源码与原始设备证据；不以Event/墙钟替代。元数据/输入准备在窗口外。

**禁止把两个均值相加**：独立encode含键GM写出，而fused collect已经包含键转换，二者工作重叠。也不能将fused collect当成对所有实现都适用的数学下界；后续融合、布局与原语会改变成本。这里只判断这条具体表达是否有继续投入的依据。

## 直方图能力的判读

`backend_inventory.histogram_device_test`明确标为`not_exercised_no_verified_callable_signature`。这不是编译失败或隐藏跳过，而是没有凭空发明接口。源码清单含检索根目录、SHA、匹配行与截断标记，受限定范围与数量上限约束；检索没发现不等于硬件不支持。

拿到明确接口或合法lowering后，仍需单独验证256桶正确性、特殊分布、生成指令及实际耗时。当前`route_feasibility`固定为`unresolved_histogram_and_native_collection_not_verified`，即使两个测量方法通过也不宣称整个T可行或达标。

## 回传与失败

输出自动复制到`/home/y00937463/B2Y/AAA_Results/topk-threshold-primitives-r1-时间-PID.json/.log`，同时生成JSON无损分片与manifest并打印路径。上传JSON+log，或全部分片+manifest+log即可；无需另生成校验文件或复制长终端文本。

单方法编译失败会继续记录另一方法；ThreadSync守卫拒绝执行。运行错误/结果不匹配则停止，保留产物。原始解析不支持时明确记录无耗时。`complete`只表示本轮两个具体表达的检查与计时完成，不表示直方图已验证或完整TopK通过。

无论成功失败都保留原始私有目录`/home/y00937463/topk-threshold-primitives-r1-时间-PID/`并上传本轮产物，不删除旧结果或盲目重复运行。
