# 从服务器容器直接上传TopK结果到B2Y

可以直接通过git提交、推送结果，无需经过PC下载或复制文本。以下命令全部在已有yjl容器内执行，使用私人仓库/home/y00937463/B2Y。等实验结束后再更新仓库。

本次只需上传stage-return.txt；其中已包含报告、原始样本和关键源码。每次上传建立独立目录incoming/topk/<运行名>-upload-<时间戳>/，不覆盖历史结果。这里是收件区，后续复核时再加入experiments/topk正式档案。

## 1. 确认原结果文件

在刚刚运行阶段诊断的同一终端执行：

```bash
B2Y_REPO=/home/y00937463/B2Y
RESULT_FILE="${TOPK_STAGE_RUN:?请先设置本次运行目录}/stage-return.txt"
test -s "$RESULT_FILE"
```

test成功没有输出。如果变量已丢失，先列出历史目录：

```bash
ls -dt /home/y00937463/runs/topk-stage1-*
```

仅在变量丢失或指错时，将下面的“实际时间戳”替换为真实运行目录名称，再重新执行本节第一组命令：

```bash
TOPK_STAGE_RUN="/home/y00937463/runs/topk-stage1-实际时间戳"
```

如果stage-return.txt不存在，不上传空文件；保留运行目录并回传最后错误。

## 2. 更新B2Y，检查提交范围

```bash
git -C "$B2Y_REPO" status --short
git -C "$B2Y_REPO" branch --show-current
```

当前分支应为main。已有修改先保存，不使用reset/clean覆盖。下面检查确认暂存区没有其他文件，再快进更新；任何命令报错就停止，不继续后面的提交步骤。

```bash
test "$(git -C "$B2Y_REPO" branch --show-current)" = main
test -z "$(git -C "$B2Y_REPO" diff --cached --name-only)"
git -C "$B2Y_REPO" pull --ff-only origin main
```

## 3. 复制结果并生成校验文件

```bash
UPLOAD_DIR="incoming/topk/$(basename "$TOPK_STAGE_RUN")-upload-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$B2Y_REPO/incoming/topk"
mkdir "$B2Y_REPO/$UPLOAD_DIR"
cp -- "$RESULT_FILE" "$B2Y_REPO/$UPLOAD_DIR/stage-return.txt"
cmp -- "$RESULT_FILE" "$B2Y_REPO/$UPLOAD_DIR/stage-return.txt"
(cd "$B2Y_REPO/$UPLOAD_DIR" && sha256sum stage-return.txt > SHA256SUMS)
```

cmp成功没有输出。只有复制和校验都成功才继续。原运行文件保持原位；不上传整个runs、cache或环境目录。收件区.gitattributes保留txt原始字节，避免Git换行转换改变校验值。

## 4. 提交并推送

只暂存本次目录，不使用git add .或git add -A：

```bash
git -C "$B2Y_REPO" add -- "$UPLOAD_DIR"
git -C "$B2Y_REPO" diff --cached --stat
```

预期仅有本次目录的stage-return.txt和SHA256SUMS两个文件；若有其他文件，先处理后再提交。

```bash
git -C "$B2Y_REPO" commit -m "Upload TopK result $(basename "$UPLOAD_DIR")"
git -C "$B2Y_REPO" push origin main
```

沿用你已经配置的GitCode凭据；推送需要B2Y写权限。若提示Author identity unknown，只为这个私人仓库设置署名，把示例替换为自己的信息后重新执行commit和push：

```bash
git -C "$B2Y_REPO" config --local user.name "你的GitCode显示名"
git -C "$B2Y_REPO" config --local user.email "你的GitCode邮箱"
```

这些是提交署名，不是登录令牌；--local不改变其他仓库或用户的Git配置。

若push提示远端有新提交（non-fast-forward/fetch first），确认没有本地未保存修改后合并远端并重试；不使用force push：

```bash
git -C "$B2Y_REPO" pull --no-rebase --no-edit origin main
git -C "$B2Y_REPO" push origin main
```

如出现冲突，停下并提供错误，不覆盖文件。

## 5. 告知已上传的位置

推送成功后执行：

```bash
printf '上传目录：%s\n' "$UPLOAD_DIR"
git -C "$B2Y_REPO" log -1 --format='%h %s'
```

把输出的目录名或提交号告诉我即可，无需再粘贴整个结果文本。我会拉取该文件、校验SHA并独立归档分析。
