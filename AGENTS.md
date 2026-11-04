当前执行入口：[950PR指定规格设备耗时对照](diagnostics/topk-950pr-device-compare-r1/README.md)。同输入、同设备计时比较当前保留r12组合与原生GE TopKV2；三个独立进程，各侧15次单调用采样。仅测量、不新增优化；尚无本轮NPU结果，不使用截图历史耗时作为固定目标。

直接源码核对：[ops-math Top-K同类算子](deliveries/topk-ops-math-alternatives-20261104.md)。存在TopK/TopKV2D等，不能凭排除法认定唯一；950PR普通FP32 AiCore调度指向TopKV2，可据此建立新原生基线，网页历史adapter仍未还原。

调用归属核对：[ops-math与GE TopKV2关系](deliveries/topk-ops-math-call-confirmation-20261104.md)。ops-math是库，TopKV2是其中算子；旧GE日志确认加载ops_math实现，但网页历史adapter仍未公开核实。后续950PR同环境对照需固定官方原生入口与完整适配边界。

最新目标：[950PR同环境稳定优于ops-math](deliveries/topk-ops-math-measurement-trace-20261104.md)，不以截图43.7μs为固定阈值。已核对launcher/PR快照/原生计时链路；实际TopKSelect ops-math适配入口尚待确认，不能用旧GE事件代替。

正式测量状态：[公共协议就绪检查](deliveries/topk-public-measurement-readiness-20261104.md)。用户仅能用旧yjl 950PR环境，目标canonical环境不匹配且TopKSelect尚未接入目标分支；正式耗时未知，不伪造或降级验收，无新NPU运行。

交付目标校正：[TopKSelect单case规格与PR规范](deliveries/topk-delivery-contract-20261104.md)。最终PR目标yyttt6/TileOPs:ascend950，当前范围ds-v32-topk-decode-b1；截图ops-math=0.0437ms，历史开发倍率不能作正式验收。算法审计暂停状态保持。

当前状态：按用户要求暂停新增优化/设备试跑，转入[TopK溢出算法审计](deliveries/topk-overflow-algorithm-audit-20261104.md)。确认缓存阈值断崖、单核全行多轮扫描及热点计数等结构问题；先审查完整算法方案，历史结果全部保留。

最新复核：[r14窗口预计算结果](experiments/topk/20261104-formal-decode-r14-091517/analysis.md)：非全窗快1.36%–9.20%，全窗有回退，随机仍约0.36x；保留窗口专门候选，后续主线返回候选可缓存路径，无需重跑。

最新入口：[窗口内预计算r14](diagnostics/topk-formal-decode-r14/README.md)：928b34fd已推送个人fork，仅限制粗桶/完整键预计算范围，保留整行DMA；新增窗口长度覆盖，尚无设备结果。

最新复核：[粗桶缓存r13窗口权衡](experiments/topk/20261103-formal-decode-r13-213748/analysis.md)：全窗溢出再降3.59%–5.51%，窄窗回退6.12%–6.22%，不全局启用；通用起点仍保留5eb130ef输入+完整键缓存，无需重跑。

最新入口：[溢出粗桶复用r13](diagnostics/topk-formal-decode-r13/README.md)：5e01bbeb已推送个人fork，保留溢出暂存/完整键缓存，复用原输入UB缓存粗桶，不增缓冲或VF，尚无设备结果。

最新复核：[溢出键缓存r12收益](experiments/topk/20261103-formal-decode-r12-210254/analysis.md)：全窗溢出进一步减少3.69%–5.79%，缓存路径小回退，按已确认取舍保留实验组合，默认不变，无需重跑。

最新入口：[溢出分数键缓存r12](diagnostics/topk-formal-decode-r12/README.md)：5eb130ef默认关闭，保留溢出暂存；GitHub认证失败，候选用B2Y校验bundle快进同步，尚无设备结果。

最新复核：[溢出暂存扩大验证r11](experiments/topk/20261103-formal-decode-r11-204010/analysis.md)：四类全窗溢出事件减少29.15%–32.49%，额外窗口/特殊值通过；随机CANN及窄窗整体计时波动保留，默认不变，无需重跑。

最新执行入口：[溢出扩大验证r11](diagnostics/topk-formal-decode-r11/README.md)：内核仍ec986f88，不叠加优化；新增容量边界/量化/接近分数/窄窗和特殊值验证，窄窗不算CANN倍率，尚无本轮设备结果。

最新复核：[溢出finish UB暂存约28.1%收益](experiments/topk/20261103-formal-decode-r10-201614/analysis.md)：同步诊断未再出现；全同分事件约417μs、0.060–0.063xAscend C，缓存路径小回退，保留候选待扩大溢出验证，默认不变，无需重跑。

最新入口：[r9同步诊断后的有界访问重试r10](diagnostics/topk-formal-decode-r10/README.md)：ec986f88补充溢出UB读取范围，14项CPU检查通过；现场同步诊断仍需验证，守卫保留，无r9性能数据。

最新执行入口：[finish溢出输入暂存r9](diagnostics/topk-formal-decode-r9/README.md)：39bb2f6f默认关闭，溢出时增加64KiB输入UB缓存，双方均保留hist/compact暂存及quota guard，尚无设备结果。

最新复核：[histogram UB暂存稳定收益](experiments/topk/20261103-formal-decode-r8-194515/analysis.md)：随机事件减少1.62%–3.50%，0.362–0.373xAscend C；8组均改善，保留为后续实验起点，默认不变，profile待复核，无需重跑。

最新执行入口：[histogram UB输入暂存r8](diagnostics/topk-formal-decode-r8/README.md)：4fd6a00e默认关闭，仅改变histogram访存，两侧保留compact暂存及quota guard，关闭r6/r7开关，尚无设备结果。

最新复核：[跳过恒定索引轮的分布权衡](experiments/topk/20261103-formal-decode-r7-192613/analysis.md)：小边界finish减少约24.8%，随机近持平，溢出回退约0.71%；不提升通用默认，下轮以9a5087dd组合为起点，无需重跑。

最新执行入口：[finish跳过恒定索引高字节r7](diagnostics/topk-formal-decode-r7/README.md)：候选23ff5c63默认关闭；跳过两轮无效索引radix，保留UB暂存/quota guard，FUSE_QUOTA关闭，尚无设备结果。

最新复核：[quota VF合并未获足够净收益](experiments/topk/20261103-formal-decode-r6-191334/analysis.md)：随机仅改善0.21%–0.70%，小边界回退2.74%–3.03%、溢出回退0.80%–0.87%。FUSE_QUOTA继续关闭，下轮以9a5087dd UB暂存组合为起点，无需重跑。

最新执行入口：[finish quota更新合并VF r6](diagnostics/topk-formal-decode-r6/README.md)：93af88eb默认关闭，每个执行轮次少一次VF；两侧保留UB暂存、128扫描、quota guard，尚无设备结果。

最新复核：[UB输入暂存筛选收益](experiments/topk/20261103-formal-decode-r5-173420/analysis.md)：随机事件减少2.6%–3.6%，0.343–0.360xAscend C；保留实验候选，profile待复核，默认不变，无需重跑。

最新执行入口：[compact UB输入暂存r5](diagnostics/topk-formal-decode-r5/README.md)：候选9a5087dd默认关闭，仅增加每核16KiB输入暂存；两侧均128扫描并保留quota guard，尚无设备结果。

最新复核：[compact 512扫描否定结果](experiments/topk/20261103-formal-decode-r4-170633/analysis.md)：两份报告及源端SHA已核验；全部事件回退，保持128，不扩大512测试。quota guard收益独立保留，无需重跑。

最新执行入口：[compact 512扫描正式对照r4](diagnostics/topk-formal-decode-r4/README.md)：只改compact执行粒度，沿用quota guard；候选364fed4c默认关闭，尚无设备结果。

最新复核：[20261103-formal-decode-r3-161729](experiments/topk/20261103-formal-decode-r3-161729/analysis.md)：两份分片报告已还原；随机事件0.329–0.350xAscend C，较上版快15.4%–16.6%；全同分溢出回退约1.18%。保持实验候选，默认不变；profile待复核，无需重跑。

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

最新：[正式基线设备拆解](experiments/topk/20261103-formal-decode-r1-094013/analysis.md)。随机r3约0.105–0.107x Ascend C设备包络、0.213–0.216x事件；prepare约28.7μs、finish约31.6μs，gap总计约0.066μs。第一进程完整，第二因239条部分流水失败，其最后50完整调用仅作补充，缺第二CANN设备复现。下一步优先prepare并行归约，随后finish执行粒度与向量统计；默认不接受，旧测量无需立即重跑。

当前：prepare分组并行归约cd94fb34，GROUPED_OFFSETS默认false，6项CPU内核测试、8项解析回归及身份/语法通过；入口diagnostics/topk-formal-decode-r2/README.md。同轮CANN、旧默认、冻结r3及新prepare，尚无新候选设备结果。首部残段只在明确block后缀/尾部完整时诊断性保留，相关设备倍率provisional、整体completed_with_profile_review，不冒称完整采集；不因头部缺一条而丢失后续CANN测量。

回传约束：用户当前两设备网络隔离，仅能通过B2Y，不能再建议聊天附件或其他外部渠道。formal-decode-r2-20261103-101431-41662两份log已收到，两份txt待传。用户要求拆分，入口tools/b2y-result-parts/README.md：只读原文件或私人run副本，gzip/base64 ASCII片≤64KiB及自动manifest，无损SHA恢复；原文保留、不自动commit/push，Git分片应分批且未推送旧大对象仍会被发送。收到后先恢复校验再分析，不能据日志冒称完整结果。

最新：[prepare并行归约复核](experiments/topk/20261103-formal-decode-r2-101431/analysis.md)。10片gzip/CRC恢复两报告，1600事件和64 CSV内部核对通过；原文SHA未与源端manifest比对但不阻断分析。prepare约28.7→4.75μs，随机事件0.277–0.284x Ascend C，较冻结r3少25.1%–25.9%；profile gap波动和残段仍待复核。下一项finish的设备quota终止/执行粒度，默认不启用，无需重跑或重拆。

当前入口：[finish设备quota守卫](diagnostics/topk-formal-decode-r3/README.md)，949d73c4已推送，EARLY_EXIT默认false。保留已测分组prepare/容量路由，仅跳过quota归零后的VF工作；7项内核测试、8项解析及身份/语法通过，尚无新设备结果。对照CANN/旧默认/冻结cd94fb34/新守卫，两进程结果后自动拆为小片回传。
