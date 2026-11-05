**本轮已完成，无需重跑。** [结果分析](../../experiments/topk/20261105-roadmap-step4-r1-151116/analysis.md)：12项各3次通过，0失败/错误/skip；公共manifest也通过，无计时。下文保留复现入口。

# 第4步：Decode边界与确定性回归

使用原yjl，算法和接口保持727132f7版本不变，本次TileOPs仅新增tests/ops/test_topk_select_ascend_decode.py。当前源码c70ffa3a，分支codex/topk-select-ascend950-42，个人fork sgcg1/TileOPs；最终PR目标仍yyttt6/TileOPs:ascend950。第2步剩余事项按用户决定暂停，不把开发检查标为正式共享预约验收。

## 更新两仓并执行

在原yjl中，先确认现有改动已保留，再更新TileOPs：

```bash
cd /home/y00937463/TileOPs
git fetch origin
git switch codex/topk-select-ascend950-42
git pull --ff-only
```

更新B2Y，加载已有CANN环境后：

```bash
cd /home/y00937463/B2Y
bash diagnostics/topk-42-step4-r1/run.sh
```

若TileOPs实际路径不同：

```bash
TILEOPS_REPO=/实际路径/TileOPs bash diagnostics/topk-42-step4-r1/run.sh
```

脚本核对完整候选SHA及已跟踪源码无改动；不自动checkout/reset、不安装依赖、不使用bundle。仅测试新增文件，不执行原有其他shape的TopK测试，因为当前adapter只认冻结Decode规格。已有公共CPU检查通过，本次算法未改，不重复整套CPU；保存test_node_delta收集报告。

## 本轮检查

全部仍是FP32[1,1,16384,1]、K2048，窗口/数据覆盖：完整manifest窗口，末尾空窗，向量边界单元素窗，K-1/K/K+1窗，非对齐尾窗，全同分、量化边界ties、相邻FP32值、全负和±0。12项各有独立分支/数值目的；每项3次。

先复跑公共manifest Decode检查，再运行源仓pytest文件。每次使用公共TopKSelectWorkload的reference和Custom验证，核对完整输出、窗口、唯一索引、精确padding及选中分数；公共Request输入保护之外补充score int32位模式检查，防止±0变化被数值比较忽略。重复调用只比较排序后的索引集合，遵守公共契约允许输出排列变化，不要求与torch.topk的tie索引相同。

本轮不加入未明确契约的NaN政策，不声称所有非有限输入已支持；没有缩数据量、放宽阈值、改reference或排除失败项。Prefill等未认领case不是本轮通过范围。

保留卡0占用预检、私人flock、短临时目录与ThreadSync守卫；无host共享guard，仍仅开发结果。算法源码不变，先通过公共Op预编译核对选中Kernel，再执行pytest，不启动其他NPU任务。不调参、不计时、不计算性能倍率。

## 回传

上传AAA_Results/topk-42-step4-r1-时间-PID.json及topk-step4-console-*.log；或全部JSON分片+manifest+console日志。报告保留公共manifest检查、JUnit、源码SHA、CPP及node-delta；成功要求12 passed、0skip/失败/错误，不接受空跑。失败也回传，不原样盲目重跑。

本地仅语法、源码未改核对及fixture边界检查完成。本机缺pytest/Torch/TileLang，test_node_delta已尝试但收集失败，未伪称CPU/设备测试通过；现场运行会补实际收集和设备JUnit。通过后再评估第5步AutoTuner的合法搜索空间。
