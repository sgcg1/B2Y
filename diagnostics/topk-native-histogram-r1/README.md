# 原生SIMD直方图验证 r1

本轮承接阈值原语r1的源码发现，直接验证嵌套 `T.simd.dhistv2/chistv2`，不继续旧TopK开关微调。**首次运行在输出dtype参数检查失败，已修复，需要更新后重试。**

## 首次回传与修复

[失败分析与原始证据](../../experiments/topk/20261105-native-histogram-r1-105405/analysis.md)：full_zero编译通过并含原生hist标记，但int16输出直接传入uint16签名，FFI在首用例调用前拒绝；没有设备正确性或耗时。现保留int16 storage做初始化/解码，传入共享storage的uint16 view；不改内核与oracle。请更新本仓后按下方入口重试一次。

## 现有 yjl 容器执行

保持原Python/CANN/TileLang环境，更新B2Y后，在已运行的容器内执行：

```bash
cd /home/y00937463/B2Y
bash diagnostics/topk-native-histogram-r1/run.sh
```

固定Python `/usr/local/python3.12.14/bin/python3`、物理卡0，按28核PR开发；此探针仅启动1个block。保留短临时目录预检、卡占用检查、私人flock和ThreadSync守卫。运行时不启动其他NPU任务；不需要重建容器、更新后端、重置卡或改共享配置。

## 验证内容

每次输入16384个预先生成的uint8数字，分64个256字节向量；同一kernel逐向量累计：

- dhistv2 bin0/1：256桶频数，各128个uint16输出。
- chistv2 bin0/1：累计频数；独立oracle要求bin1包含低128桶贡献。
- 三档：全mask、任意mask、任意mask且频数初值7/累计初值11。

18组输入覆盖全同0/127/128/255、随机、递增、空mask、前缀边界、交替/非二进制mask、向量边界。每档各3次，检查全部512项输出及两个输入未改写；错误停止，不修改oracle迎合设备。最大计数16395，不触及uint16溢出。本地54项检查是数学模型和Python语法检查，**不是设备指令模拟或内核AST执行**。

候选用法来自本地TileLang主仓 `18baa3d1b6a96a5ab1bbe72d66dfd7c9a8b92279` 的 `testing/ascend/language/simdvf/test_simdvf_histv2.py`、`test_tilelang_ascend_intrinsics.py`。本地simd.py与服务器上次清单哈希不同，不能认定版本等同。脚本先保存现场simd.py、定义、签名和可用codegen片段，再检查接口契约，最后验证生成代码包含原生hist及两个bin标记。接口缺失、签名不匹配、编译失败或标记未确认均明确报告，不退回逐桶扫描，也不据此断言所有后端都不支持。

## 计时边界

每档正确性通过后，使用相同递增输入、全有效tags，3次预热、5个独立单调用原始设备窗口；1GiB驱逐和输入准备在窗口外。保持原始FFTS/STARS证据，解析失败不以Event或墙钟替代。

此kernel每向量同时执行**两次频数和两次累计直方图**，读入预制字节而非完整FP32分数；有mask档还读入tags。测得的是该测试组合，不能当作单条指令成本、单轮完整键选择成本或直接乘4预测TopK。没有执行FP32键转换、四轮精确阈值选择、最终收集，也没有比较TopKV2。因此不能报告完整算子倍率或DT卡预测。

## 结果回传

脚本自动保存到 `/home/y00937463/B2Y/AAA_Results/topk-native-histogram-r1-时间-PID.json/.log`，并打印无损分片与manifest路径。上传JSON+log，或全部分片+manifest+log。失败也上传同批产物，无需截图或另做校验文件。

原始目录 `/home/y00937463/topk-native-histogram-r1-时间-PID/` 保留。`complete`仅表示三个直方图组合的正确性与采样完成，不代表完整TopK达标。拿到结果后，再决定是否实现完整键的四轮选择与原生向量收集。
