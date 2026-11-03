# GitCode TLS断连后的核验与恢复

用户报告：对象写出约492KiB后，curl 56 / GnuTLS unexpected TLS packet、sideband disconnect，同时出现Everything up-to-date。最后一行不能单独证明成功。2026-11-03 agent核验远端main为33b8a9a，只新增信息.txt修改，仍无本轮topk-formal-decode-r2结果。

对象已经写出不代表远端分支引用更新成功；也可能远端接受但确认响应丢失。必须检查实际远端引用/提交。当前不能据日志确定根因是代理、网络还是TLS服务端；HTTP/1.1重试是兼容性尝试，不保证修复。此次结果文件应保留在本地提交中，无需重跑NPU。

## 容器内：保留结果提交，合并远端后重试

在/home/y00937463/B2Y执行。先检查当前分支和提交，确认结果已提交：

```bash
git branch --show-current
git log -1 --oneline
git status --short
```

应为main。如果有未提交的已跟踪修改，先停下保留现场，不自动stash或重置；原有未跟踪.idea/、main.py不属于结果，不要一并提交。不要重新生成或覆盖AAA_Results原始文件。

先读取远端更新，单次Git命令使用HTTP/1.1：

```bash
git -c http.version=HTTP/1.1 fetch origin
```

成功后将远端新增指南/信息等合入自己的结果提交历史：

```bash
git merge --no-edit origin/main
```

若出现冲突或署名错误，停止并回传终端信息，保留当前状态。成功后正常推送：

```bash
git -c http.version=HTTP/1.1 push origin main
```

若再次TLS断连，可以同样正常重试一次；不重复无限重试。不要force push，也不关闭TLS校验、不修改公共代理或全局Git配置。普通fetch/merge不会删除已提交的实验结果。

## 核验是否真的到达

```bash
git -c http.version=HTTP/1.1 fetch origin
git merge-base --is-ancestor main origin/main
echo $?
```

最后输出0表示刚fetch到的远端历史已包含本地main，即使前一次push显示断连，也可按已送达处理。1表示未包含；其他非零为检查错误。fetch失败时不要继续使用旧origin/main判断本次是否送达。

若仍未成功，保留结果提交和终端日志，告知本地git log -1显示的提交号。文件不丢失，不需要重新跑实验。


## 当前现场：merge因Committer identity unknown停止

本地main为c768891（Upload experiment result3），工作区检查无输出，fetch已成功。merge因未配置committer身份而未完成，之后push被non-fast-forward拒绝是正常保护。不要force push或reset；结果仍在本地提交里。

在容器/home/y00937463/B2Y执行，先显示已有结果提交的身份：

```bash
git show -s --format=fuller c768891
```

以下沿用该私人仓库已有结果提交的作者作为本次合并的提交者，只设置本仓local配置。如果上面显示的作者并非你希望使用的身份，停下告知实际署名，不借用其他人的身份。

```bash
git config --local user.name "$(git show -s --format=%an c768891)"
git config --local user.email "$(git show -s --format=%ae c768891)"
git var GIT_COMMITTER_IDENT
```

然后检查合并状态：

```bash
git status
git rev-parse -q --verify MERGE_HEAD
git diff --name-only --diff-filter=U
```

最后一个命令若列出文件，说明有未解决冲突，停止并回传状态，不继续提交。

若MERGE_HEAD打印提交号，且无冲突文件，完成已开始的merge：

```bash
git -c core.editor=true merge --continue
```

若MERGE_HEAD没有输出，则重新发起合并：

```bash
git merge --no-edit origin/main
```

合并必须成功后才执行：

```bash
git -c http.version=HTTP/1.1 push origin main
```

如果由于本指南的新发布等并发提交，再次出现non-fast-forward，则fetch、merge成功后再正常push，不改用强推。推送断连则按前文fetch和祖先关系核验。无需重新运行NPU实验，也不要重新提交同一份结果。
