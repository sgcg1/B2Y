# 实验结果上传目录

在运行实验的同一个yjl容器终端执行（保留TOPK_STAGE_RUN变量）：

```bash
cd /home/y00937463/B2Y
git pull --ff-only origin main
mkdir -p AAA_Results
cp "$TOPK_STAGE_RUN/stage-return.txt" "AAA_Results/$(basename "$TOPK_STAGE_RUN").txt"
git add -- AAA_Results
git commit -m "Upload experiment result"
git push origin main
```

结果直接放在本目录，以运行目录名命名，不需要额外校验文件或子目录。变量丢失时，把cp命令中的$TOPK_STAGE_RUN替换为实际运行目录；命令报错时先停下。

推送成功后告诉我“已上传”即可，我会拉取并分析。
