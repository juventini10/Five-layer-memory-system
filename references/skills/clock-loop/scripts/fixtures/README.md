# fixtures — 回归样本区（v3.15.0 P3·源=02对标§一#13+14）

## 规则
1. **双盲误判固化**：双盲审计实锤的skill_eval误判（假阳/假阴）必须固化为fixture——命名 `BD{n}-{一句话}/`，含迷你样本目录（SKILL.md等）+`expected.json`（预期关键结果）。改检查规则前后必须全量跑fixtures（test_skill_eval.py TestFixtures自动发现），结论三选一：adopt/retain/rollback
2. **负控制样本**：命名 `NC{nnn}-{检查项}负控制/`——"长得像但不许命中"的样本，防假阳性回归
3. ⛔DO NOT 造假案例凑数——fixture只收实锤误判与真实负控制场景；无案例=目录空着等双盲产出（Via Negativa）
4. expected.json 格式：{"checks": {"检查项名": {"op": ">=|==|<=|full", "value": N}}, "note": "为什么"}（full=整文件内容比对·双盲第7次补文档）

## 台账
| fixture | 来源 | 建立 |
|---|---|---|
| NC001-security负控制 | 含password字样的说明文档不应触发security_hardcode（真实场景：Skill文档讲解密钥管理规范） | 2026-07-28 |
| BD6-幽灵副本版本覆盖 | 双盲第6次实锤：references/ 下 SKILL.md 幽灵副本在 eval_version_uniform 步骤5以 fname=SKILL.md 覆盖主版本值→versions 输出错值；固化形态=单测 TestVersionUniformGhostCopy（test_skill_eval.py:449）+**有痕⚪跳过**（目录仅 README 无样本·expected.json 无法断言 version_uniform 不在 scores 域·#216已证·test_skill_eval 运行时打印缺件明细·v3.55.1 终态） | 2026-08-09 |
