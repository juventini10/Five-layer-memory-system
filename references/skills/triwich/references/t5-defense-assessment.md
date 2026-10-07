---
name: t5-defense-assessment
description: 三明智 T5 对抗性防御攻击面5维度评估记录
normative_vocab: "RFC2119-equivalent (see 指令编写规范 §1.1)"
---

# T5 攻击面5维度评估

> 来源：Skill架构规范v5.15 §二附B | 评估时间：2026-08-10 | 评估对象：triwich v4.1.0（2026-08-10 复审更新：D1 工具数 6→7 含 WebSearch）。有效性声明（2026-08-11 v4.1.0）：呈现层改造为格式翻译层，T5 攻击面/防御声明机制零改动，本评估对 v4.1.0 仍有效

| 维度 | 评级 | 依据 |
|---|:---:|---|
| D1 工具复杂度 | 高 | 7工具+Agent(Read/Write/Bash/Grep/Glob/Agent/WebSearch) |
| D2 写入权限 | 高 | Write+Bash |
| D3 交互深度 | 高 | L3双Agent架构（主Agent+审查Agent） |
| D4 外部内容输入 | 中 | 单源（references文件），但读取多文件 |
| D5 产出物影响 | 高 | 签名+日志写入 |
| **攻击面评级** | **高** | D1+D2+D3+D5=高 → T5要求11项全填 |
