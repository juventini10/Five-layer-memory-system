---
normative_vocab: "RFC2119-equivalent (see 指令编写规范 §1.1)"
---

# eval 68 断言（M3首批56·随版增补） × 微内核分家 迁移对账表（M3·v4.8.1）

> 用途：分家（v4.8.0 M1）后逐条确认 eval-set 68 断言（M3首批56·随版增补）的锚点住位与在场性，⛔不留"表说了没验"的第二本账。
> 机械校验：`python3 scripts/eval_anchor_check.py`（run.sh 常驻）——现位每文件必含校验 token。
> 状态口径：**未变**=断言对象本就在内核/既有 reference，分家未触碰；**双锚**=内核一行索引+页全文同 token 在场；**页移行**=全文已在外置页、内核只留异措辞索引（token 只在页在场）。
> 现位多文件用 `+` 连接（token 须在每个所列文件均在场）；`-`=判断层人眼自锚（无外部物理件，对齐 eval-set 头部 C-14 声明）。

| # | 断言摘要 | 分家前锚点 | 现位 | 校验token | 状态 |
|---|---|---|---|---|---|
| 1 | 分析底层逻辑→L1第一性 | SKILL.md对照表 | SKILL.md | 第一性原理 | 未变 |
| 2 | 靠谱吗→L1批判验证 | SKILL.md对照表 | SKILL.md | 靠谱吗 | 未变 |
| 3 | 对比方案→L2路由 | SKILL.md路由表 | SKILL.md | 路由 | 未变 |
| 4 | 全面深度→L3 | SKILL.md对照表 | SKILL.md | 深度 | 未变 |
| 5 | 显式触发→Step0判定 | SKILL.md+Step0 | SKILL.md | 触发词对照 | 未变 |
| 6 | 分析代码不触发 | SKILL.md description | SKILL.md | 纯代码编辑 | 未变 |
| 7 | 闲聊不触发 | SKILL.md description | SKILL.md | 纯闲聊 | 未变 |
| 8 | 写文件不触发 | SKILL.md description | SKILL.md | 纯文件操作 | 未变 |
| 9 | 文件对比不触发 | SKILL.md语境限定 | SKILL.md | 语境限定 | 未变 |
| 10 | 文件分类不触发 | SKILL.md语境限定 | SKILL.md | 语境限定 | 未变 |
| 11 | L1输出+结论块精简 | SKILL.md分层定句 | SKILL.md | 分层定句 | 未变 |
| 12 | Step0文件缺失中止 | SKILL.md熔断器 | SKILL.md+pages/p0-step0.md | 熔断器 | 双锚 |
| 13 | 8要素全正触自爆 | critical-verify | SKILL.md | 自爆 | 未变 |
| 14 | 门禁锁未过退结论块 | SKILL.md模板 | SKILL.md | 门禁锁 | 未变 |
| 15 | Agent B先独立后对照 | full-flow | references/l3/flow-agent-b.md | 盲审 | 再分页v4.8.2 |
| 16 | 格式混入退回 | SKILL.md禁止行为 | SKILL.md | 禁止行为 | 未变 |
| 17 | 段头反贴被拦 | SKILL.md禁止行为#7 | SKILL.md | 禁止行为 | 未变 |
| 18 | 步骤叙述被角色锁拦 | SKILL.md禁止行为#7 | SKILL.md | 禁止行为 | 未变 |
| 19 | B回空读文件即完成 | full-flow失败表 | references/l3/flow-agent-b.md+references/l3/full-flow.md | 精确路径 | 双在场(幂等检查+失败表) |
| 20 | 通配幂等检查违规 | full-flow | references/l3/flow-agent-b.md | 精确路径 | 再分页v4.8.2 |
| 21 | B异常处理须留痕 | full-flow | references/l3/full-flow.md | 异常留痕 | 未变 |
| 22 | 会话戳不一致中止 | SKILL.md十锁索引 | SKILL.md+pages/p-mechanism.md | 会话戳锁 | 双锚 |
| 23 | steps/基准=工作区 | SKILL.md+Step0细则 | SKILL.md+pages/p0-step0.md | 工作区 | 双锚 |
| 24 | A未落盘即返回违规 | full-flow | references/l3/flow-agent-a.md | 落盘硬约束 | 再分页v4.8.2 |
| 25 | streak载体先初始化 | full-flow | references/l3/flow-agent-b.md | agent_b_streak | 再分页v4.8.2 |
| 26 | 戳凭记忆即暴露 | SKILL.md三要点+细则页 | pages/p0-step0.md+pages/p-mechanism.md | 取值防伪 | 页移行 |
| 27 | {ts}须YYYYMMDD_HHMMSS | Step0细则+full-flow | pages/p0-step0.md+references/l3/full-flow.md | 格式规范 | 页移行 |
| 28 | 段头八处一致 | SKILL.md模板+8件 | SKILL.md | 结果 | 未变 |
| 29 | 结论块置底 | SKILL.md模板 | SKILL.md | 紧贴签名 | 未变 |
| 30 | 简报块3行同源投影 | SKILL.md启动简报块 | SKILL.md | 启动简报块 | 未变 |
| 31 | Step4归Agent B | full-flow | references/l3/full-flow.md | 输出前自检 | 未变 |
| 32 | 验证行在结论前 | full-flow+模板 | references/l3/full-flow.md | 信任前置 | 未变 |
| 33 | 并发双键互不覆盖 | SKILL.md+十锁 | SKILL.md+pages/p-mechanism.md | 唯一键 | 双锚 |
| 34 | 正据弱走三问前置 | critical-verify | references/l1/critical-verify.md | 证据链三问 | 未变 |
| 35 | L2不自动展开双轨 | SKILL.md Step2.5 | SKILL.md | Step2.5 | 未变 |
| 36 | 数据类触发判据① | first-principles | references/l1/first-principles.md | 深度触发器 | 未变 |
| 37 | 决策类触发判据② | critical-verify | references/l1/critical-verify.md | 深度触发器 | 未变 |
| 38 | 认知类触发判据③ | first-principles | references/l1/first-principles.md | 深度触发器 | 未变 |
| 39 | 三问未全过继续挖 | first-principles | references/l1/first-principles.md | 两问终止测试 | 未变 |
| 40 | 证据不足用悬置档 | 8element | references/shared/8element.md | 悬置 | 未变 |
| 41 | 结论块信息分层 | SKILL.md模板 | SKILL.md | 信息分层 | 未变 |
| 42 | 收尾跑seal record | SKILL.md封口段+十锁 | pages/p-mechanism.md | triwich_seal | 页移行 |
| 43 | 待回访先筛查再分析 | 十锁 | pages/p-mechanism.md | 回访前置 | 页移行 |
| 44 | 本质未知走换序 | SKILL.md+0.5三闸 | SKILL.md+pages/p05-assumption-gates.md | 思维顺序 | 双锚 |
| 45 | 常规任务走保底 | SKILL.md+0.5三闸 | SKILL.md+pages/p05-assumption-gates.md | 思维顺序 | 双锚 |
| 46 | L2验证架构行 | SKILL.md+dual-routes | SKILL.md+references/l2/dual-routes.md | 单Agent自检链 | 未变 |
| 47 | 标签变化≠进展 | 判断层（人眼） | - | - | 人眼自锚 |
| 48 | 非矛盾不硬凑对立 | 判断层（人眼） | - | - | 人眼自锚 |
| 49 | 形式绿≠判断完成 | 判断层（人眼） | - | - | 人眼自锚 |
| 50 | 自标高须标注 | 判断层（人眼） | - | - | 人眼自锚 |
| 51 | 思维产出物静默落盘 | 十锁 | pages/p-mechanism.md | 静默追加写入 | 页移行 |
| 52 | 8要素空行退回 | 8element | references/shared/8element.md | Fail-Closed | 未变 |
| 53 | 简报与键文件逐字一致 | SKILL.md同源投影 | SKILL.md | 同源投影 | 未变 |
| 54 | L1简报形态无标注 | SKILL.md分层定句 | SKILL.md | 分层定句 | 未变 |
| 55 | 降档须四格举证 | 0.5三闸深度四格 | pages/p05-assumption-gates.md+pages/p-mechanism.md | 深度举证 | 页移行 |
| 56 | 压档渲染声明级行 | 0.5三闸 | pages/p05-assumption-gates.md | 声明级 | 页移行 |
| 57 | 认知格自适应渲染 | 十点包⑩ | SKILL.md+references/shared/result-block-examples.md | 认知格 | 新增v4.9.0 |
| 58 | 证据清单全档落盘 | 十点包② | pages/p05-assumption-gates.md+references/shared/8element.md | 证据清单 | 新增v4.9.0 |
| 59 | 缺料闸具名 | 十点包③④ | SKILL.md+references/l3/full-flow.md | 缺料 | 新增v4.9.0 |
| 60 | 结论即按钮两行 | 十点包⑤ | SKILL.md+references/l2/dual-routes.md | 下一步·系统 | 新增v4.9.0 |
| 61 | 采纳词族零动作 | 十点包⑥ | pages/p-mechanism.md | 词族 | 新增v4.9.0 |
| 62 | 证据档总档最弱 | 十点包⑧ | SKILL.md+references/l1/first-principles.md | 最弱承重柱 | 新增v4.9.0 |
| 63 | 地图机检 | 十点包⑨ | references/四象限地图.md | 四象限地图 | 新增v4.9.0 |
| 64 | 旧形态回流否证族 | 弱锚升级 | scripts/run.sh+scripts/negative_tokens.txt | negative_tokens | 新增v4.9.2 |
| 65 | 盲审复测封顶 | F1 | references/reviewer-protocol.md | 未复测清单 | 新增v4.10.0 |
| 66 | 负担闸判据 | F5 | SKILL.md | 负担闸 | 新增v4.10.0 |
| 67 | 呈现边界+单签名 | F8 | SKILL.md+references/shared/signature.md | 单签名行 | 新增v4.10.0 |
| 68 | 模板同构位齐闸 | 你令统一 | scripts/run.sh+scripts/template_parity_check.py | template_parity_check | 新增v4.10.1 |

> 对账结论（v4.8.1 首跑）：56/56 无断锚（v4.8.1首跑口径）·现 68/68 EVALMAP 常驻；分家触碰面=页移 6 行（#26/27/42/43/51/55/56 系）+双锚 7 行，内核留守红线（结论块模板/分层定句/对照表/四层契约/禁止行为/自检清单）与既有 references 全部未变——与 M1 判耦清单一致。
