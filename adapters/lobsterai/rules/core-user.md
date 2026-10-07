---
title: USER.md — LobsterAI 端承载模板
platform: lobsterai
layer: end-specific          # ⛔ 端专属层·不进 references/templates 公共层
version: v1.0-lobsterai
date: 2026-10-06
real_file: USER.md
inject_channel: OpenClaw workspace bootstrap（每会话加载·state/workspace-main/）
official_role: "directive-based user model"
char_budget: 4000
budget_authority: "OpenClaw 官方 docs/concepts/agent-workspace.md（⛔ 本数字仅本端成立·他端无此机制）"
contains: 称呼·当前关注·认知风格·协作模式
end_note: |
  ⚠️ **本端最易踩的坑**：OpenClaw 官方给 USER.md **独立 4,000 字符预算**（不受 bootstrapMaxChars 约束），且它是 **optional 文件**（缺失静默省略·无 marker）⇒ 超限失效完全不可见。⛔ persona/切片一律不进本件·一律进 SOUL.md。
source: |
  正文基线 ← references/templates/USER.md（公共脱敏层·单真源）
  本 frontmatter（char_budget / official_role / end_note）← LobsterAI 端专属（2026-10-06 立）
  ⛔ 字数上限不得上提到公共层：他端无 bootstrapMaxChars/bootstrapTotalMaxChars/USER.md-4,000 这套机制
---

# USER.md — 关于 {称呼}

- **称呼**：{Step2 Q1}
- **一句话身份简介**：{Step2 Q2}
- **AI工具环境**：{由用户安装时确认，默认WorkBuddy}
- **记忆系统**：布洛陀1.0

---

## 当前关注

- **核心目标**：{Q24} — 接下来3个月必须达成的目标
- **当前需要**：{Q28} — 现在最需要什么
- **最希望解决的问题**：{Step2 Q3}

---

## 认知风格（来源：33题问卷）

- **归因模式**：{从Q8答题提炼——失败时归咎于什么}
- **驱动模式**：{从Q9答题提炼——改变主意通常因为什么}
- **判断标准**：{从Q12答题提炼——怎么判断建议值不值得听}
- **争议处理**：{从Q13答题提炼——AI方案和自己想法不一样时怎么处理}

---

> 描述式写法：纯用户画像，不写指令/规则。版本：v1.1（2026-10-03·新增童灵节占位） | 布洛陀1.0通用骨架 | `{...}` 由答题数据填充

---

## 数字分身·童灵（造芯后填入·安装时为占位）

> 本节是童灵K2恒驻核的嵌入位。造芯完成后，将生成器产出的 core_slice 和 L6 反向约束粘贴到下方对应标记之间。
> ⛔ 安装包不预置任何人格数据——本节为空壳，由你造芯后填入。
> 各端加载方式：有自动注入端→系统自动加载；豆包办公端→T0 Read指令加载+造芯第4步把切片粘进「工作任务偏好指令」。

### core_slice（恒驻核·L1骨架+核心人格向量）

<!-- CORE_SLICE:START -->
（造芯后将 k2_slice_generator.py 产出的 core_slice 内容粘贴于此）
<!-- CORE_SLICE:END -->

### L6（反向约束·行为边界与禁区）

<!-- L6_CONSTRAINT:START -->
（造芯后将生成器产出的 L6 反向约束内容粘贴于此）
<!-- L6_CONSTRAINT:END -->

### 切片索引（L2-L5按需加载·不常驻）

> L2认知风格/L3行为规则/L4表达DNA/L5盲区与边界 的切片文件在 `<记忆共享中心>/数字分身/K2切片蒸馏/slices/`，由 doenglingz-slice-nav Skill 按需加载，不粘贴到本文件（防上下文膨胀）。
