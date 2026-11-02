# A1 r1：前端Python嵌套失败

两次启动（202906、203005）均在compile:control导入新源码时失败，TileLang eager改写后Python编译报告too many statically nested blocks。baseline已生成C++；尚未生成control或A1 C++，没有正确性或性能结果。不是UB容量故障证据，也不是性能失败。

根因是新增缓存首轮if/elif让原完整compact路径位于额外else下，eager将if转为多层循环，超过Python静态块限制。普通源码py_compile及CPU分支语义测试不能覆盖这一前端改写。此次实现遗漏了交接明确记录的嵌套风险。

修复944bc00d让缓存首轮与旧分支同级，旧首轮入口仅在CACHE_COARSE=false时进入；CACHE首轮state[5]=0，旧候选循环为空。state初始化、轮次、乒乓关系及完整溢出计数保持。8项CPU检查通过；对回传eager源码复现失败，抬出对应外层else后Python编译通过。这是结构回放，不是重新执行TileLang前端或NPU验证。

原始Git blob来自1dc0a60，四文件逐字节保存并记录SHA；两次失败均保留，不将它们当作两个独立性能复现。新测量使用topk-a1-r2目录与新身份，不修改r1工具。仅需按r2指南重试，小规格通过后再判断是否扩大。
