# BD6 · 幽灵副本覆盖主版本号（双盲第6次 P1-1 实锤·2026-08-09）

**来源**：QClaw 第6次双盲审计 P1-1——references/SKILL.md（滞后副本 v3.32.0）在 eval_version_uniform 步骤5 遍历 references/*.md 时以 fname='SKILL.md' 覆盖步骤1提取的主版本（3.33.2），versions['SKILL.md'] 输出错值；mismatches 用局部变量 main_ver 故 passed 仍 true（假绿灯·版本不同步可能被掩盖）。

**修复**：①回收幽灵副本（移入记忆琥珀，非 rm）②skill_eval.py 步骤5 跳过 fname=='SKILL.md'（设计端消除）。

**固化形态**：因 version_uniform 不在 scores 断言域（fixture expected.json 只支持 scores），实锤固化为精准单测 `TestVersionUniformGhostCopy`（test_skill_eval.py）——直接断言 versions['SKILL.md']==主版本，未来重构破坏免疫性即当场报红。
