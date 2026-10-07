# 步骤8·数字分身（童灵）部署与安装包闭环
# 状态：启动中 · T0级 · 2026-09-30
# 来源：机制验证已完成（10项/缺口4处）· 实施本体已确认（[记忆共享中心]/数字分身/：scripts/109项 + steps/ + K2切片 + state_bus.json）
# 目的：把已验证机制从"参考/设计"变为"安装包可执行管线"

## 已确认的实现层存在（非设计层）
- [记忆共享中心]/数字分身/README.md / CHANGELOG.md / state_bus.json
- scripts/ (109 项，含 auto_pass_audit.py 等)
- steps/ (含 step0-determination, calibration-audit 等)
- K2切片蒸馏/ 目录

## 安装包当前缺口（需本步骤填补）
1. 守卫执行自动入口：doenglingz_guard / gate_runner 未在 install_scripts.py ROSTER
2. L7 验证自动接入：08-会话级清单仅为参考，未接入设置
3. 脱敏/污染检查：execution-guidelines 在知识蓝图，desensitize-guard 路径未确认
4. 跨端适配 06 已有 adapter，但缺"启动童灵后自动触发蒸馏/守卫"流程

## 下一步动作（本轮执行）
- [ ] 读取 install_scripts.py ROSTER，确认缺失项
- [ ] 补 step8 文档（本文件）到 references/steps/
- [ ] 提案：新增 setup 流程段，问卷完成后自动触发 step5-file-synthesis → step8-twin-deploy
- [ ] 脱敏确认：对[记忆共享中心]/数字分身/ 中的私有产物做脱敏后再封装

## 证据要求（铁律1）
每项修改前必 read_file 当前内容；每条断言配行号；签名后无追加。
