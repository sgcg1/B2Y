# A2 r1工具错误：冻结基线哈希被全局替换破坏

用户上传提交d2964cd，两文件按Git blob原字节保存。实际TileOPs提交34f3bf36正确；工具在assert digest(baseline)==BASE停止，尚未编译任何kernel，无性能或正确性结果。

生成工具时全局将a1替为a2，错误改动SHA中的e60a14为e60a24。正确基线是987da9f9d314f8744bef05a628e60a14b88e63db320374f36a3b6411ce5eb2e3。不能放宽断言、更新到任意本机值或归咎用户环境。这是工具生成错误，本地语法检查未覆盖身份数据。

r2仅修工具，内核不变；记录实际baseline_sha256及stage，异常显示实际/预期值。新validate_identity.py从冻结提交直接读取Git blob，核对基线、候选、runner及所有嵌入哈希/提交常量。离线验证成功，并对r1复现Baseline digest corrupted，形成针对性回归。脚本语法通过，尚无A2设备编译结果；同步警告守卫不变。

新执行入口diagnostics/topk-a2-r2/README.md，旧r1不覆盖、不重跑。所有成功失败记录保留。
