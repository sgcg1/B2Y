# 原生直方图 r1：调用前输出类型错误

用户提交f7556dd，工具465bdbe，运行20261105-105405-3212。原始JSON与分片解压逐字节一致，manifest的原始/压缩/分片SHA均通过，8份内嵌证据SHA通过。

## 结论

失败位置是TVM FFI参数检查：`kernel main input out dtype mismatch, expected uint16`。runner创建int16输出storage后直接传入；内核签名是uint16。首个ramp用例尚未执行直方图kernel，设备验证0项、计时0窗口。不能说设备直方图错误或性能差，也不能说已验证成功。

现场simd.py SHA仍为9a7403dadb15ab5842988deb33d90bfbaec2f916ebc6de3bae273de1a611c302，codegen SHA仍为e406224ad3c3a33050e1125ee3495ba35f531e4148ad0f4a80a03a5bedc30d6e。API契约检查通过；full_zero编译完成，生成CPP含dhistv2/chistv2、Bin_N0/Bin_N1，无atomic标记且未触发ThreadSync守卫。其他两档尚未编译/验证。编译通过不等于设备正确性通过。

## 修复及重试

同目录runner保留int16 storage用于fill与CPU解码，另创建共享storage的uint16 view，**仅将uint16 view传入kernel**。这是dtype元数据修复，不做数值转换，不改内核、数学oracle或计时边界。本地TileLang原始单测也明确使用int16 storage.view(torch.uint16)；此前漏掉view是本测试错误。

更新B2Y后按[原入口](../../../diagnostics/topk-native-histogram-r1/README.md)再运行一次，产生全新目录。保留本轮失败证据。下一轮仍需验证64向量累计语义、mask、非零初值及全部设备输出，不能预先判定算法可行。
