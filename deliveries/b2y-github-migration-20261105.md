# B2Y迁移到GitHub

用户已指定以后使用https://github.com/sgcg1/B2Y，GitCode仅保留历史/备用。最终TileOPs PR目标不变，仍yyttt6/TileOPs:ascend950。

## 本地已完成

D:/04_Project/B2Y的origin fetch/push均为https://github.com/sgcg1/B2Y.git，main跟踪origin/main。gitcode远端保留https://gitcode.com/JotaroSSR/B2Y.git。迁移时本地与GitHub共同HEAD为b436e4ad25d0ecaf7c53d74a8ed43b52fe88e014，ahead/behind均0；未执行reset/强推，原未提交改动及未跟踪文件保留。

## 原yjl容器中的服务器B2Y

直接修改现有checkout，无需重新clone，不影响AAA_Results：

```bash
cd /home/y00937463/B2Y
git remote get-url gitcode >/dev/null 2>&1 || git remote add gitcode https://gitcode.com/JotaroSSR/B2Y.git
git remote set-url origin https://github.com/sgcg1/B2Y.git
git remote set-url --push origin https://github.com/sgcg1/B2Y.git
git fetch origin
git branch --set-upstream-to=origin/main main
git remote -v
git status -sb
```

显式设置push URL，防止原仓另设pushurl时只改fetch地址却仍推向旧站点。命令保留所有本地文件/提交，不自动stash、reset或强推。

若当前分支为main且需更新运行脚本，再执行：

```bash
git pull --ff-only
```

若提示分叉或本地改动将被覆盖，停止，不用reset --hard/强推；先保留本地结果与提交，再处理分叉。改远端本身不要求立即合并，不会丢失服务器未推送的结果。

以后常规使用：

```bash
git pull --ff-only
git push origin main
```

更新脚本后也可继续用tools/b2y-upload-latest/upload.py --upload逐文件上传；其目标检查已改为sgcg1/B2Y GitHub，不再接受GitCode。默认先预览文件清单，上传操作不改已有结果。

## 认证与网络

首次GitHub推送可能要求GitHub账号和GitHub PAT/现有凭据助手。GitCode令牌不能作为GitHub令牌；不要把令牌写进remote URL、提交到仓库或粘贴进聊天。已有GitCode凭据可原样保留，它们不会自动变成GitHub凭据。脚本不改代理或关闭TLS校验；网络仍需能够访问github.com。

新报告/指南以GitHub B2Y为准；历史GitCode链接为已有证据出处，不批量改写。两站不会自动同步，后续只向origin推送，勿同时向旧gitcode远端更新同一流程。
