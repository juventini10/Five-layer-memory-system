---
normative_vocab: "RFC2119-equivalent (see 指令编写规范 §1.1)"
---

# L3 Agent B 审查细则页（full-flow 按需再分·v4.8.2·裁判段）

> 装载时机：L3 轮 Agent B 启动（幂等检查→启动参数→两阶段审查→输出）。reviewer-protocol.md 与本件配套。
> 骨架/G2/Step4/结论块/签名/失败处理仍在 `references/l3/full-flow.md`。

## ═══════════ Agent B：验证者（裁判）═══════════

Agent B的职责是两阶段独立审查——先盲审形成独立第一印象，再全量验证推理过程，最后交叉对比做出终判。

### 设计原则

> **v3.0.1 盲审修正**：从纯盲审升级为盲审-全量交叉验证。参考学术同行评审（双盲+开放）、AutoGen Coder-Reviewer角色分离。盲审防锚定、全量审推理、交叉暴露矛盾。

### Agent B 启动前：幂等检查（v3.10.1 新增）

🔌 启动前检查当前会话 `{ts}` **精确路径**下的 `agent_b_review.md` 是否已存在且非空：
- 已存在且非空 → 本次 Agent B 已完成，直接读取该文件，⛔DO NOT再次启动 Agent B
- ⛔DO NOT使用通配符（如 `/tmp/triwich_l3_*/agent_b_review.md`）做幂等检查——旧会话残留文件会跨会话误判"已完成"，导致 Agent B 被静默跳过（2026-08-08 实测：通配 glob 同时命中 16:12 旧文件与 16:42 新文件）

### Agent B 启动参数

使用WorkBuddy Agent工具启动Agent B：

```
Agent(
  name="验证者",
  description="两阶段独立审查Agent A的分析结论——先盲审后全量，交叉验证",
  subagent_type="general-purpose",
  mode="default",
  prompt={见 references/reviewer-protocol.md 完整审查协议（现行版）}
)
```

### Agent B 输入（两阶段）

**🔀 路径基线（v4.10.7 跨平台根治）**：下文 `{tmpdir}` = 系统临时目录**运行时派生**——`python3 -c "import tempfile; print(tempfile.gettempdir())"`（macOS/Linux 通常解析为 `/tmp`；Windows 解析为 `%TEMP%` 值）。⛔DO NOT 硬编码 `/tmp`——Windows 无 `/tmp`，写死=Win 端 Agent B 输入/输出全断链（2026-10-22 布洛陀发布链 D5 检查⑩判红根治）。与 flow-agent-a.md §跨平台声明、p0-step0.md §临时目录声明同源同口径。

**阶段1·盲审输入**（仅结论，不传推导）：
1. `{tmpdir}/triwich_l3_{ts}/user_question.md` — 用户原始问题
2. `{tmpdir}/triwich_l3_{ts}/agent_a_output.md` — Agent A的结论+8要素自评

**阶段2·全量输入**（阶段1完成后追加）：
3. `{tmpdir}/triwich_l3_{ts}/agent_a_reasoning.md` — Agent A的完整推导链

**⚠️ Agent B在阶段1**看不到推导过程——锚点、苏格拉底五问、假设表、跨域映射全部隔离。
**🔴 输入排他性**：以上文件是 Agent B 的**全部**合法输入。⛔DO NOT 在 Agent B 的 prompt 里粘贴推导原文、⛔DO NOT 让其读取主聊上下文——隔离靠"没给"而不是"要求它别看"。

### Agent B 执行 Step3：批判验证（两阶段）

→ 按 `references/reviewer-protocol.md`（现行版）执行（含 ⚔️对抗性验证——委派 `references/l1/critical-verify.md` Step3 单一来源，详见 reviewer-protocol.md §2d）。

**阶段1·盲审**：
- 实事求是检查（独立WebSearch查证事实主张）
- 8要素独立评估（用自己的视角重新填表）
- 输出：盲审初判 ✅/❌ + 独立8要素表 + 盲审印象

**阶段2·全量审查**：
- 锚点验证（两列对立面抓住了真正矛盾吗？）
- 推导验证（推理链有逻辑跳跃吗？假设完整吗？苏格拉底五问是形式还是实质？）
- 对抗性验证（委派 critical-verify.md Step3：假设结论已错→构建最强反方论证→边界条件→综合判断）
- 前提核验（凡结论依赖可测量 artifact 事实——精确行数/标记密度/阈值跨越/真实计分——✅DO 先实测或要求提供真实数字；未测则在结论标 ⚠️前提未实测，不与已验证结论同权）
- 实践检验+认识循环

**交叉验证**：
```
盲审初判(阶段1) vs 全量审查(阶段2) 是否一致？
  ├─ 盲审✅ + 全量✅ → 终判✅（两次独立审查一致）
  ├─ 盲审❌ + 全量✅ → 终判✅（标注"盲审疑虑：xxx"）
  ├─ 盲审✅ + 全量❌ → 终判❌（最危险——结论好看但锚点错）
  └─ 盲审❌ + 全量❌ → 终判❌（两次都不过）
```

### Agent B 质量监控

> 防止Agent B变成橡皮图章——总说✅通过。

**规则**：Agent B连续3次输出✅通过 → 第4次强制执行：**即使结论正确，也必须找出至少1个可改进的方向（不是错误，是改进空间）**。输出格式中加 `[改进建议]` 段。

**计数器载体（v3.0.4 新增·M13修复·v3.0.5 补初始化）**：`{skill根目录}/steps/agent_b_streak.md`，单行内容 `consecutive_pass: N`。
- **路径基准声明（2026-09-06 A2 patch·双向对齐）**：本载体显式带 `{skill根目录}`·= pages/p0-step0.md §路径基准声明"唯一例外：计数器载体 `{skill根目录}/steps/agent_b_streak.md`（路径显式带 `{skill根目录}`·跨会话持久需随 Skill 分发）"。⛔DO NOT解析到当前执行工作区（`pwd`）·否则跨会话断链=机制不存在。与 pages/p0-step0.md §路径基准声明段(引用块粗体句·段锚非节标题·v4.5.1如实标注) "裸 steps/ = 当前工作区" 主句不冲突——唯一例外已显式锚定。
- **初始化（v3.0.5）**：L3 启动时主agent 检查该文件——不存在则**先创建**（内容 `consecutive_pass: 0`）再继续，⛔DO NOT 等 Agent B 终判后才想起建载体。原因是载体缺失=质量监控无从查起（2026-08-09 实测：文件不存在，Agent B 报告自证"文档写了磁盘没有"）。
- 每次 Agent B 终判后由**主agent** 更新该文件：终判✅ → N+1；终判❌ → N 归 0。**写入姿势（2026-09-02 清零批#15·并发 L3 竞态根治）**：✅DO 原子写——先写同目录临时文件再 `mv` 覆盖（`mv steps/agent_b_streak.md.tmp steps/agent_b_streak.md`·同分区 mv 原子，并发读侧只见完整旧值或完整新值，⛔DO NOT 直接 open-write 截断旧文件——读到半行 `consecutive_pass:` 会误判 N=0 触发重置）；读到格式异常/半行 → 视为 N=0 并重写完整内容（容错自愈，不中断 L3 主流程）。
- 读到 N≥3 → 本次 Agent B 启动参数中✅DO追加「强制改进指令」→ 产出 `[改进建议]` 段后将 N 重置为 0。
- 文件不存在 → 视为 N=0 并创建。⛔DO NOT把计数器只放在对话上下文里——跨会话必然归零，等于机制不存在。

### 🔴 混合模式风险缓解（v4.0.0 新增·童灵评估2026-09-04·皮叔认可实施）

> **背景**：L3混合模式（Agent A主agent结构化模板填充 + Agent B真独立子进程审查）提速40%（25→15分钟），但有"Agent A习惯性廉价填充→深度退化"风险（目标侵蚀·系统之美10）。

**缓解措施1：定期严格L3校准**
- ✅DO 每5次混合模式L3后，用1次严格L3（Agent A也真子Agent），对比Agent A深度是否退化——原因是混合模式长期用，Agent A可能"习惯性廉价填充"（依赖Agent B兜底），深度逐渐退化（目标侵蚀）。
- ⛔DO NOT 长期只用混合模式不校准——原因是无校准=深度退化无感知（系统之美10目标侵蚀·标准悄悄降）。

**缓解措施2：Agent B连续逮出cosplay→回退严格L3**
- ✅DO 如果Agent B连续2次逮出Agent A的cosplay（廉价填充/两问走过场/反八股未真执行），回退到严格L3（Agent A真子Agent）——原因是Agent B兜底是"检查端防错"（事后检测），Agent A侧持续退化须从"设计端"修复（真子Agent执行）。
- ⛔DO NOT 把Agent B兜底当"免责金牌"——原因是兜底不是长久之计，Agent A侧退化须回退严格L3根治。

**混合模式成立的3个前提**（缺一不可·Fail-Closed）：
1. Agent B必须真独立子进程（Agent工具启动·非主agent换帽）——防cosplay最后一道防线
2. Agent A结构化模板填充必须"真填"（Fail-Closed·填不出=退回）+反八股检验真执行——防廉价填充
3. 主agent诚实标注混合模式（Agent A是主agent手写·非子Agent）——实事求是

### Agent B 输出

写入 `{tmpdir}/triwich_l3_{ts}/agent_b_review.md`：

```markdown
# Agent B 审查报告

[审查结果: ✅通过 / ❌打回]

{如果❌打回，打回理由至少一条具体可操作的修正建议}

Agent B 独立评估（五维·对齐 reviewer-protocol 终审评分·2026-10-22 R2）：
├─ 实事求是（事实基础）：🟢/🟡/🔴
├─ 锚点质量：🟢/🟡/🔴
├─ 逻辑自洽（推导严谨）：🟢/🟡/🔴
├─ 可验证性：🟢/🟡/🔴
└─ 综合判定：✅通过 / ❌打回

## 未复测清单
{凡承重主张未独立复测者列此（v4.10.0 F1：缺段=流程轴❌）；全部复测则写「无」}

{如果触发质量监控：[改进建议] xxx}
```
