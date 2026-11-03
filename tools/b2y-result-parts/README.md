# 两份结果压缩拆分为小文本

本工具只读原文件，不启动NPU，不改已有提交或输出。针对已上传日志对应的运行topk-formal-decode-r2-20261103-101431-41662，读取两份repeat-1/2结果；优先AAA_Results原txt，若副本被撤销提交删除，则读私人实验目录的repeat-1/2/formal-return.txt。

先gzip压缩，再base64编码拆成每片≤64KiB的ASCII .txt。自动生成一个manifest.json，含原始大小/SHA、压缩大小/SHA、各片顺序/大小/SHA。manifest是恢复必需部分，自动生成，不需手写校验清单。原始JSON的换行和所有字节在恢复后保持相同，不改写实验数据。

拆分仅用于尝试绕过大请求写入故障，不保证修复TLS。日志小文件已成功到达，但这不足以证明故障一定由大小引起。

## 容器内执行

在原yjl容器，不需要加载CANN或重新跑实验。读取新脚本只需fetch，不必先解决本地结果历史的合并：

```bash
git -C /home/y00937463/B2Y -c http.version=HTTP/1.1 fetch origin
```

fetch成功后直接执行远端已发布版本：

```bash
git -C /home/y00937463/B2Y show origin/main:tools/b2y-result-parts/split_results.py | /usr/local/python3.12.14/bin/python3 - split
```

脚本默认已知本轮运行名。若原文件都找不到，保留错误反馈，不重新运行NPU。若需指定另一轮，使用split --run后跟实际topk-formal-decode-r2-时间-进程号；不要把其他版本结果改名冒充本轮。

输出在/home/y00937463/B2Y/AAA_Results，名称以parts-UTC时间开头。终端MANIFEST为清单路径，UPLOAD为各分片路径；SOURCE显示实际读取的原文件。原txt和log均保留。重复运行会生成新批次，不要混传不同批次清单与分片。

## 上传策略

先通过B2Y网页上传一个64KiB分片测试，再上传同批manifest和其余分片；无需再上传大txt。两个log已在远端，无需重复。记录名称有repeat-1或repeat-2，全部片和对应清单到齐后agent才能恢复、逐字节校验并分析。

如果使用git push：一次提交全部分片，HTTP总请求可能仍很大；Git本来就压缩传输，拆文件本身不减少所有对象总量。应少量分片分批提交/推送，而且本地未推送历史若仍包含原大文件，Git仍会把那部分历史一起发送。不要为此盲目reset或强推，先告知当前状态。工具不自动add、commit或push。

64KiB仍失败时可把执行命令末尾改为split --part-kib 16，生成新的独立批次；不要无限缩小重试。网页编辑、上传或Git写入若连小请求都失败，应继续按网络/代理故障处理。

## 恢复与验证

接收端使用同脚本的restore子命令，传入manifest路径并指定新的输出目录；会先核对所有分片，再验证gzip及恢复原文SHA。缺片、损坏、错误顺序或目标已存在均停止，不覆盖旧证据。用户只需把同批清单和分片上传B2Y，恢复由agent处理。

两项CPU回归通过：非文本原始字节/CRLF的无损往返、片大小/ASCII及不覆盖检查，缺片/损坏拒绝且不产生错误输出。另已对本地较大的历史正式结果做实际往返。脚本仅依赖Python标准库，适配容器Python3.12；不读取Git凭据或令牌。
