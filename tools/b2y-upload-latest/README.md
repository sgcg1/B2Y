当前远端已迁移至[GitHub sgcg1/B2Y](https://github.com/sgcg1/B2Y)，脚本只允许该GitHub仓库，拒绝继续向GitCode误推。GitHub迁移后不再受此前GitCode网页单文件问题约束；本工具仍保留用户要求的逐文件/断点续传方式。历史GitCode故障描述仅作背景。

# 最新一轮结果逐文件提交/推送

用于服务器B2Y GitHub仓（sgcg1/B2Y），每次仅新增一个文件commit并push成功，再处理下一个。不是网页自动点击上传，也不依赖浏览器或GitCode私有上传API。网页单文件限制不一定适用于Git协议；本脚本实现的是你要求的逐文件Git推送，不能保证修复代理/TLS故障。

## 执行（测试全部结束之后）

在原yjl中先更新B2Y脚本。先查看本轮清单，不修改Git、不联网：

```bash
cd /home/y00937463/B2Y
/usr/local/python3.12.14/bin/python3 tools/b2y-upload-latest/upload.py
```

确认清单后上传：

```bash
/usr/local/python3.12.14/bin/python3 tools/b2y-upload-latest/upload.py --upload
```

复用现有Git凭据/代理，不在脚本中写令牌或关闭TLS验证。HTTP推送使用HTTP/1.1。每次push只有一个文件的新增提交，但Git自身仍会传递commit/tree/blob等多个对象，不能据此保证每次HTTP请求只有一个对象。

## 最新一轮识别

取AAA_Results最近修改的log。当前step6三进程共一轮，按console文件中的共同shell PID收集r1/r2/r3三份日志，再按日志打印的UPLOAD_RESULT/MANIFEST/PART找到各报告。三份console不齐则拒绝。应在测试结束后运行，不能边生成边上传。

优先发送每份报告的全部分片+manifest+console，不再重复推原始大JSON；逐片校验manifest中大小与SHA。其他近期单进程脚本则按最新log的打印路径识别。没有可靠结果引用则报错，不猜测其他历史文件。

全部测试产物仍保留，脚本不删除/改写它们，不包括无关源码或历史轮次。每个文件提交后立即push，成功并核对远端后才进行下一个；已上传文件跳过。同一清单重复运行可继续。若TLS报错但远端实际已接收，下一次fetch会识别；若未接收，只允许重试脚本自己产生的一个单文件待推提交。

要求B2Y main、暂存区为空、origin为sgcg1/B2Y GitHub。无关未暂存改动保留；不stash/reset/强推。遇远端并发更新导致分叉，或存在其他未推提交时停止，不擅自推送/合并它们。执行期间不要让另一个终端同时操作该B2Y Git索引或推送。

## 本地验证

已使用临时本地bare remote验证三进程9文件的逐文件提交/推送；模拟首次push断开后，重跑先推回单文件待推提交；再次重跑不增加提交。逐一核对9个新增commit各只包含一个文件。测试没有访问GitCode或使用真实结果，不能据此保证TLS链路已经修复。
