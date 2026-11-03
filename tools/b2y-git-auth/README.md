# B2Y容器内永久认证配置

按用户要求永久保存，仅影响/home/y00937463/B2Y。用户名JotaroSSR，提交邮箱1224862686@qq.com。令牌不写入脚本或仓库，执行时在终端隐藏输入。此前在聊天公开过的令牌建议撤销后换新。

容器Git store以明文保存凭据，这是持久化方案的实际限制；目录700、文件600限制普通用户读取，但不能防止容器内其他root读取。路径/home/y00937463/.config/git-b2y/credentials位于已挂载/home，容器重启后仍保留。请勿上传该文件或把它加入仓库。

## 运行

在现有yjl容器，先通过已有可用读取路径获取本脚本（遇到本地待推送提交时不要reset）：

```bash
git -C /home/y00937463/B2Y -c http.version=HTTP/1.1 fetch origin
```

不需要先合并，就可从已fetch的远端提交读取并执行本脚本；这样不会干扰待推送结果或未完成merge：

```bash
git -C /home/y00937463/B2Y show origin/main:tools/b2y-git-auth/configure.sh | bash
```

出现GitCode token提示时输入新令牌，终端不回显。脚本从/dev/tty读取，管道输入不影响令牌输入。只执行一次，之后在同一B2Y仓库使用HTTPS push会复用凭据。没有在线认证测试，公共ls-remote成功不能证明令牌具有写权限；真正权限由后续push检查。

凭据仅按gitcode.com/JotaroSSR/B2Y.git路径保存，适用于当前origin；不配置其他仓库。脚本同时设置当前仓库的user.name和user.email，避免合并时缺committer身份。不改全局Git、代理、TLS或已有merge状态。

认证保存不修复此前curl56 TLS协议断连，也不解决non-fast-forward。若待推送结果历史与远端分叉，仍需fetch、merge成功后正常push，不强推。

令牌轮换时重新运行脚本输入新令牌，Git store更新同路径记录；不需要重新跑实验。凭据文件只存服务器私人路径，不回传，不在命令行、日志或聊天再次粘贴令牌。
