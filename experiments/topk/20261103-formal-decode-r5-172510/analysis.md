# r5源码身份检查失败

阶段provenance，pipeline工作文件SHA不等于候选预期。未进入编译或NPU运行，无性能或正确性结论。服务器实际HEAD和工作SHA未记录，根因未定。保留原始log/txt，源码候选不修改；新增只读check_sources.py和SOURCE_RECOVERY.md，补充HEAD/工作文件/HEAD blob/换行归一化SHA，继续严格身份校验，不覆盖本地修改。
