# 可回传摘要（仅填写当地允许出域的字段）

不要求导出原始 JSON、环境路径、机器名、序列号、完整日志、业务输入或 profiler。允许的数据可手工整理成以下摘要，再通过你自己的 B2Y checkout 传回；服务器不需要克隆 B2Y。不能披露的字段留空或写“保密”。

```text
实验代号：
工具版本：20261031-r4
TileOPs commit（如允许）：
是否与 SOURCE.json 的已知源码相同：是/否/未核实
环境：目标950PR？ Python/torch/torch_npu/TileLang/CANN版本（可披露部分）
正确性：14 passed / 失败阶段 / skipped（不算通过）
首个错误：阶段名、错误类型、退出码（不要附敏感路径）

控制实验：
初版 / v0.1.2 / H128 / H256：各50次事件中位数，单位μs
重复轮次是否接近：
时钟检查：设备事件是否超过包围它的主机区间？
负载遥测：Aicore额定/当前字段，Vector利用率；是否仅空闲时低频？
注：没有单独Vector时钟读数时，不将Aicore字段直接叫作Vector频率。

Decode [1,1,16384,1] K2048：
  CANN 内核中位数 μs：
  TileLang 内核中位数 μs：
  事件中位数（两者分列） μs：
  本轮输入哈希是否一致：
  每组真实 event/profile 样本数量：
  H/W/coarse 配置：
  profiler 是否有缺记录、额外计算任务、flow mapping错误：

128行诊断 K2048：TileLang内核/事件中位数 μs、H/W、样本数
完整 Prefill K1024：同上，包括本轮CANN与匹配输入
完整 Prefill K2048：同上，包括本轮CANN与匹配输入

源码/辅助脚本是否修改：
运行期间是否有其他负载：
当前结论：仅Decode完成 / 四组完成但待审核 / 有失败未完成
```

性能倍数统一为“本轮 CANN 纯内核中位数 / TileLang 纯内核中位数”。不要用历史 CANN 数字替换新服务器基线。128行没有同规格官方基线，不填写×Ascend C。
