# finish设备quota守卫：正式对照r3

候选949d73c4已推送，EARLY_EXIT默认false，不改生产host。保留已验证的分组prepare和容量路由，只在radix轮次开始检查设备UB中的state[0]；归零后跳过该轮所有VF，循环本身仍保留。必要的overflow稳定tie只有quota>0时执行，不删同分规则。没有D2H决策，没有增加kernel数或其他优化。

7项本地CPU测试通过，覆盖全部旧prepare/尾段模式、容量边界、特殊值与窗口，以及打开quota守卫后集合/final_state一致、短窗/空窗VF调用减少；关闭新开关的模块AST仍与冻结旧路径一致。源代码普通语法通过不能证明eager改写、主kernel读取UB状态或VF同步通过，实际编译/资源/警告需现场确认。

## 执行

沿用已加载CANN的yjl容器、现有Python，私人/home/y00937463。先确认卡0可用，不修改公共安装或频率。

宿主机进入容器，已在容器则跳过：

```bash
docker exec -it yjl /bin/bash
```

容器内更新两仓，失败停止，不重置修改、不在实验途中pull：

```bash
git -C /home/y00937463/B2Y pull --ff-only &&
git -C /home/y00937463/TileOPs pull --ff-only
```

确认现有CANN环境加载后：

```bash
bash /home/y00937463/B2Y/diagnostics/topk-formal-decode-r3/run.sh
```

## 对照与证据

四版本为冻结旧默认、cd94fb34分组prepare旧尾段（previous）、新quota守卫（new）、官方GE TopKV2。同输入/同流及独立预分配workspace。当前模块关闭EARLY_EXIT的finish-control必须与冻结previous生成相同C++，其余四段冻结身份核对。旧r3命名只在内部prepare-r3键沿用，实际对照来源明确为cd94fb34，不是慢prepare版本。

两个独立进程，新cache/tmp/logs；四输入（两个随机、全同分溢出、小边界同分），每版本50事件，共1600样本。保留同轮CANN事件及独立设备profile，每进程16个profile，检查四kernel的4/1/4/1顺序及各段、gap、同次包络。事件与设备倍率分开，不挑最好值。

本工具共9个编译配置，包含冻结finish和关闭守卫的control；全部捕获原生stderr和Bisheng前源码，ThreadSync诊断拒绝计时。关闭新开关的源一致性与GE属性/工具身份、8项解析回归及Python/Bash语法已在本地核验，尚无本候选设备结果。

原formal-r2已知profile gap波动，本轮不把profile间隙全部归咎观察者，也不把sum_kernel当包络。首部残段按相同保守规则只标provisional，整体completed_with_profile_review，保留原CSV；错误顺序、重叠、缺样仍拒绝。固定N16384/K2048/G1全窗有限分数的基线比较，不冒充完整通用契约。

若新尾段未实际减少VF调用或事件无稳定净收益，应记录失败而不是扩大测试；即使有效，也不能保证1.0x，因为hist和compact成本仍在。

## 分片回传

所有提示ASCII。结果在/home/y00937463/topk-formal-decode-r3-时间-进程号，formal-return.txt和日志复制AAA_Results。两进程都产结果后，启动脚本自动调用标准库拆分工具，生成gzip/base64分片及manifest并打印UPLOAD路径；原文不修改。若第一进程编译失败，仅回传其日志/结果，不强行拆两份不存在的报告。

沿用B2Y手动上传同批分片的方式。manifest可附带完善源端SHA验证，不作为读取报告的硬性障碍；不需手写清单。若自动拆分因工具版本落后失败，保留原报告并告知，不重跑NPU。不得一次git push所有未推送大原文历史来假装小请求。不需重跑旧formal-r2。
