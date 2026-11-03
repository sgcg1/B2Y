# B2Y协作约定

本任务最新交接见[deliveries/topk-handoff-20261102.md](deliveries/topk-handoff-20261102.md)。新会话先读该文，历史未提交/权限/环境状态不作为当前前提。

交接同步状态（2026-11-02）：用户确认两个仓库均已推送成功：B2Y远端为GitCode，TileOPs远端为GitHub，候选fda84f78及其祖先e444083d已同步。此状态来源为用户确认，不冒称agent独立核验。A0双进程结果已归档，未证明收益，保持关闭。A1候选944bc00d已推送GitHub，当前入口diagnostics/topk-a1-r2/README.md；更新两个仓库后运行，工具核对候选SHA。尚无A1 NPU结果。

用户于2026-11-02确认：

- 两台电脑间不能直接复制粘贴。要求操作者执行的任何新命令，都先写入B2Y的指南或脚本、校验并推送。聊天只给已发布入口和必要说明，不能成为唯一命令来源。
- 在根README维护当前下一步入口；文档区分宿主机/容器、已有环境、输出与失败处理。当前环境为Docker容器yjl，私人目录/home/y00937463，使用容器自带Python。
- 用户最新要求：服务器上传结果直接放根目录AAA_Results，不要求用户生成校验文件或额外子目录。接收后的内部归档规则继续适用。
- TileOPs实现通过个人fork sgcg1/TileOPs的main同步，B2Y放辅助材料、实验结果与分析。不要把实现源码副本混入B2Y。
- 项目完全开源；用户已明确同意把本任务分析报告及相关实验结果发布到B2Y。早期不能传出服务器产出或缺少分析发布授权的限制已被后续指示更新。该授权不包括把密码、令牌等凭据提交到Git，也不扩展为修改其他用户或共享系统环境。
- 保留用户文件；不要提交原有未跟踪的.idea/、main.py，也不修改信息.txt或实验结果来夹带工具更新。
- 先检查错误前提、逻辑跳跃和信息缺失；保持独立判断。数据和结论尽量核实来源，区分事实与假设；发现错误直接指出依据与风险，并提醒遗漏的变量、成本和认知偏差。

## 实验结果长期保存

用户要求保存每次实验结果以便日后回顾。收到结果后，先将原始回传（含失败/不完整）按独立ID存入experiments/topk/，记录来源、版本、执行日期或未知、状态、缺失项、字节数和SHA-256，并维护README和index.json。不得用根目录“实验结果”收件箱的最新内容覆盖旧档案。原始数据不改写；摘录、重建摘要必须标明，不补造未回传数据。后续分析修正另写补充说明或新增分析版本，保留历史结论的出处。所有下一步指令仍须先写入本仓再通知用户。

A1 r1两次前端嵌套失败已归档，当前使用r2修复指南；尚无A1性能结果。

最新：[A1 r2结果复核](experiments/topk/20261102-a1-r2-203417/analysis.md)：600事件完整，耗时下降约0.91%–1.14%，但ThreadSync竞争警告未解，保持关闭；先查同步，不原样重跑或直接扩大测试。

当前下一步：[A1同步最小编译复现](diagnostics/topk-a1-sync-repro/README.md)。已发现官方0176ba14原子指针别名检查疑似混合dtype单位问题；尚未证明全部警告误报，A1保持关闭。仅编译四个小kernel，不运行性能测试，不改安装。

当前仅编译诊断改用[r2入口](diagnostics/topk-a1-sync-repro-r2/README.md)：首版因uint8x2代码生成失败，未完成同步对照。A1仍关闭，不重跑旧诊断。

最新：[同步最小复现r2已复核](experiments/topk/20261102-a1-sync-repro-r2-204739/analysis.md)，四配置编译通过；uint8有额外屏障、uint32无，但未重现生产外提警告，A1仍关闭。下一步回到生产访问对排查，无需重跑此复现。

最新：[A1同步源码审计及候选补丁](diagnostics/topk-a1-sync-source-review/README.md)。指针区间混合元素单位缺陷可构造；补丁仅做应用及4项CPU算术检查，未编译/未安装，A1继续关闭。约1%收益暂不值得主线依赖工具链重建，下一项优先独立A2 int32分片histogram；没有新服务器指令。

当前执行入口：[A2 r1首轮4组int32直方图](diagnostics/topk-a2-r1/README.md)。候选34f3bf36已推送GitHub，默认关闭；A0/A1关闭，10项CPU检查通过，尚无A2 NPU结果。先编译/正确性后对照，ThreadSync诊断出现即拒绝计时。

当前使用[A2 r2指南](diagnostics/topk-a2-r2/README.md)，r1工具生成误改基线哈希，已归档并修正。内核仍34f3bf36；离线身份回归已捕获r1并验证r2，尚无A2设备结果。

当前入口：[A2 r3](diagnostics/topk-a2-r3/README.md)。r2在布局推导失败，候选67b9e72f已改成常量并行长度并推送；12项CPU检查与离线身份通过，尚待现场编译，无A2性能结果。

当前入口：[A2 r4](diagnostics/topk-a2-r4/README.md)。r3已过布局但Bisheng因原子条件下标生成语句失败；4774e7ea改为显式int32索引，13项CPU检查通过，工具预存生成源码；尚无A2性能结果。

最新：[A2 r4复核](experiments/topk/20261102-a2-r4-211000/analysis.md)：四组事件耗时增加4.04%–4.36%，无编译同步警告，筛选正确性通过但性能回退；保持关闭，不扩大或重跑。下一步评估Decode首轮小P并行成本，尚无新指令。

最新主线：Decode首轮分块成本探针72a84811已推送GitHub；执行入口diagnostics/topk-decode-pilot-r1/README.md。测P1/P2/P4私有直方图及hist+merge两kernel事件；尚未做compact和后续精确选择，不能当完整TopK结果。2项CPU AST/分块检查、离线身份与语法通过；尚无本探针NPU结果。旧A0/A1/A2保持关闭，不重跑。

Decode pilot启动脚本run.sh原中文提示误以GBK保存，保留原件；当前指南使用新增run-ascii.sh。run.py和identity未变；用户已运行结果不因提示乱码重跑，照常上传。后续终端脚本提示一律ASCII，并检查原始字节可按ASCII解码。

最新：[Decode成本探针已复核](experiments/topk/20261102-decode-pilot-r1-211917/analysis.md)，P4直方图+归并约18.87–19.05μs，有继续实现compact与精确后续的空间，但不是完整TopK收益。两进程成功，1200样本完整，不因提示编码重跑。

最新任务：完整Decode四kernel实验候选03c8f916已推送GitHub，入口diagnostics/topk-decode-full-r1/README.md。hist→prepare→compact→finish，P2/P4、固定N16384/K2048/G1；边界≤2048装UB，溢出重扫原窗口，FP32+小索引精确选择。4项CPU AST/分块检查、离线身份与语法通过，尚无本候选NPU结果，不进入默认。完整四kernel事件与冻结baseline对照，含随机和溢出分布；ASCII启动提示，源码预捕获、同步诊断守卫保留。

最新：[完整Decode full-r1已复核](experiments/topk/20261102-decode-full-r1-213318/analysis.md)。P4随机耗时下降42.7%–43.1%，小边界下降61.3%–61.9%，全同分溢出增加约42%；1200事件及校验通过、编译无同步诊断，但不接受默认。下一步优先改进溢出尾段，暂不重跑。

当前任务：Decode full-r2 0d4063e6，将4轮FP32后的4轮索引radix替为按绝对索引稳定tie；STABLE_TIE默认false。5项CPU测试及旧模块AST一致性、离线身份与语法通过。入口diagnostics/topk-decode-full-r2/README.md，P4-r1/r2/default同轮比较，保留四输入和完整四kernel事件、同步守卫。尚无r2设备结果。

最新：[Decode full-r2已复核](experiments/topk/20261102-decode-full-r2-214318/analysis.md)。随机较默认下降43.5%–44.1%，溢出下降17.4%；小边界仍比默认快约30%，但比r1慢约82%。下一步设备内按候选容量选择尾段，不能D2H路由；当前未接受默认，无需重跑。

当前入口：[Decode full-r3设备容量路由](diagnostics/topk-decode-full-r3/README.md)，c022114c已推送、默认关闭。≤2048用r1、溢出用r2，无D2H；5项CPU测试及身份/语法通过，尚无r3设备结果。一次对照默认/r1/r2/r3，完整调用事件，新增2048/2049边界校验。

最新：[Decode full-r3复核](experiments/topk/20261103-decode-full-r3-090700/analysis.md)：随机较默认下降43.2%–43.4%、溢出下降16.1%–16.2%、小边界下降61.8%；1600事件及容量边界校验通过，编译诊断为空，路由有额外成本。优先进入更广泛Decode验证及同轮CANN/设备流水记录，尚未默认接受，无需重跑。

当前最高优先级：diagnostics/topk-formal-decode-r1/README.md，固定c022114c的r3，不改内核。官方GE TopKV2同进程同输入/同流事件，对照旧TileLang；独立profile CANN单kernel与r3四kernel包络/各段/gap，保留全部kernel_details.csv与task_time.csv。6项CPU解析回归、离线身份/GE属性和语法通过，尚无此工具设备结果。不再混用旧9.23μs与r3事件算倍率；下一优化依据最大设备成本选执行粒度/向量路径。
