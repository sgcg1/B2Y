# 独立验证M的消费数统计是否依赖scan

用户要求自行设计新测试，不采用另一方案的探针结论。此目录只使用本目录的独立kernels和固定输入；不导入、不执行另一方案的探针，不以其报告作为判断输入。复用旧对照工具的标准库设备占用与短TMPDIR预检，未复用任何能力测试结果。

## 在既有yjl容器运行

更新B2Y至包含本目录和当前identity.json的版本，沿用已成功的CANN/TileLang/Python环境。仅使用物理卡0；不要同时运行其他NPU任务，不改系统配置或频率。

```bash
cd /home/y00937463/B2Y
bash diagnostics/topk-merge-consumption-probe-r1/run.sh
```

固定Python为`/usr/local/python3.12.14/bin/python3`，无需更新TileOPs或安装依赖。工具采用独立短TMPDIR，导入NPU运行时前和每方法执行前后检查占用，私人flock避免重复启动；不等于共享宿主预约。发现外来进程则停止，不杀进程、不重置设备。

## 三项独立设备测试

| 测试 | 设备上实际执行 | 所回答的问题 |
|---|---|---|
| binary_consumption | 线程0对左侧有序头块做至多9步二分，比较完整uint32键与绝对索引；cR=m-cL | 是否能不依赖scan、reduce API和逐元素atomic计算两个消费总数 |
| tree_consumption | 256个来源标签分8层成对归约，每层双缓冲、两个VF保持依赖，不调用库reduce/scan或atomic | 是否存在显式并行树的独立可编译实现；不证明它开销低 |
| scan_control | 独立尝试256项T.cumsum，并与CPU前缀核验 | 本次运行环境是否支持这条具体scan调用，成功或失败都保留实际证据 |

每个消费数方法验证96组输入，连续执行3次与CPU独立答案逐元素比较，并检查输入未被改写。使用完整uint32排序键的int32位模式存储，在设备上reinterpret后比较，避免误用有符号排序；含0/0x7fffffff/0x80000000/0xffffffff、同分按索引、全从左/全从右、空输入、m=0、短尾和随机分布。

CPU oracle对带来源标签的左右段进行全排序并截取前m项，直接得到正确消费数，不使用待验证的二分或树归约算法。CPU自检已通过96例；设备编译和正确性须以本次服务器运行结果为准。

## 为什么要区分scan与消费总数

M每批已经要输出有序前缀Y[0:m]，它的位置是连续的，不需要给每个原始输入元素分配compact位置。需要的是两个数cL、cR，而非每个元素的前缀数组。

若Y非空，令z=Y[m-1]。使用“完整键降序、索引升序”的唯一全序，cL等于左有序头块中不劣于z的元素数，二分可得，cR=m-cL。若m=0，两者均为0。R=256时二分最多9步，不需要T.cumsum、T.reduce_sum或atomic。

树归约另验证cL=sum(来源为左的标签)，它只产生一个总和，不产生256个前缀。8层、每层两个VF的依赖可能有显著控制开销，测试成功也不能把这部分成本当成零。

## 结果判读与范围

- `cases`逐项记录compile_failed、wrong_result或passed；scan失败不会阻止另外两项独立尝试。设备运行错误则停止并保存现场，避免带错误状态继续运行。
- `verdict=non_scan_consumption_demonstrated`：至少一个消费数实现已在设备正确执行，且生成文本未发现atomic/cumsum标记；结合完整源码复核，可反驳“必须依赖scan或逐项原子”的绝对说法。
- `verdict=no_non_scan_method_confirmed`：本轮没有确认替代实现；依据每项错误继续定位，不能据此证明所有替代算法都不可能。
- `status=complete`仅表示本轮采集完成；结论看verdict与逐项状态，不能只看进程返回码。

**本探针不执行设备排序/归并。** 正确归并前缀的标签及最后一项由CPU输入，故只能验证消费数子问题。没有设备计时，不判断批量归并开销，不宣称方案M可在10.639μs内完成，也不证明M整体正确。排序/归并原语、完整键语义、UB布局和逐批控制成本仍需另行验证。

## 回传

脚本自动复制本轮JSON和log至`/home/y00937463/B2Y/AAA_Results/`，名字为`topk-merge-consumption-probe-r1-时间-PID.json/.log`。JSON包含各方法状态、实际输出、编译traceback、生成CPP与编译日志的无损嵌入证据。**把本轮两份文件上传到B2Y的AAA_Results即可，包括失败时的结果。** 本轮通常不需要分片；若上传受限，保留原文件再按既有分片流程传输，不重新跑设备。

原始现场目录`/home/y00937463/topk-merge-consumption-probe-r1-时间-PID/`保持不动。不要求复制终端长文本，不把聊天当唯一命令来源。
