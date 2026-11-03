# 已加载代理时的GitCode TLS排查

适用现场：服务器B2Y本地结果已提交，user.name/email已配置，merge至少成功一次，但push反复curl 56 / GnuTLS TLS断连。已确认终端加载代理，尚未证明代理是根因。本指南通过独立文档分支发布，不更新main，避免制造新的main并发提交。

所有命令在现有容器/home/y00937463/B2Y执行，不重新运行实验、不修改全局Git/共享代理环境。

## 1. 当前代理连接只读检查

```bash
timeout 25s git -c http.version=HTTP/1.1 ls-remote origin refs/heads/main
```

## 2. 定义仅对这次调用绕过代理的函数

以下只创建当前终端中的函数，不改配置文件。移除代理环境并覆盖常见Git代理配置，TLS校验开启；不打印代理URL或凭据：

```bash
git_direct() {
  env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY       -u all_proxy -u ALL_PROXY -u GIT_SSL_NO_VERIFY     git -c http.proxy= -c remote.origin.proxy=         -c http.https://gitcode.com.proxy=         -c http.version=HTTP/1.1 -c http.sslVerify=true "$@"
}
```

直连只读测试：

```bash
git_direct -c http.lowSpeedLimit=1 -c http.lowSpeedTime=20 ls-remote origin refs/heads/main
```

若输出远端提交号和refs/heads/main，表示直连读成功；不代表写入一定成功。若报无法连接/超时/证书错误，停止并回传这两项只读测试的原始错误，不继续猜测或反复push。证书错误不通过关闭校验解决。

## 3. 仅在直连读成功后恢复推送

逐步执行，任一步失败就停止；不要一口气执行后续步骤：

```bash
git status --short
git_direct fetch origin
```

确保结果已提交且无未解决的已跟踪修改，成功fetch后执行：

```bash
git merge --no-edit origin/main
```

出现冲突则停止保留现场；合并成功后：

```bash
git_direct push origin main
```

若仍TLS断连，不无限重试。一次核验远端是否实际包含本地结果：

```bash
git_direct fetch origin
```

fetch成功后才执行：

```bash
git merge-base --is-ancestor main origin/main
echo $?
```

0表示远端已包含本地main，1表示尚未包含，其他非零是检查错误。fetch失败时origin/main可能过时，不据此判定本次送达。

如果直连读成功而写仍断连，这还不能单独证明是GitCode服务端或代理故障，需要结合错误进一步判断。保留本地提交c768891及后续merge，不force push、不reset、不重新提交同一结果。

若现有文件传输方式可以取回本次两个txt和两个log，可直接附到聊天，由agent分析并归档B2Y，先绕过服务器Git写入问题。无需重跑NPU。
