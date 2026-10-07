---
title: Phase X 验证⑩-⑱ 执行细则
type: reference
status: active
version: v1.1.0
date: 2026-07-30
summary: Phase X机械验证的验证⑩-⑱完整判定规则——v3.25.0细则外置（瘦身第二刀·同v3.11.2外置模式）。⑩⑪⑬⑯⑱脚本权威实现，本文件为人读对照；⑫⑭⑮为AI执行检查，本文件为唯一权威定义。v1.1.0加sha8自指hash（问4物理钩）。
source: 技能配置/clock-loop/references/phasex-verification-details.md
author: 皮叔
complies_with: 文件格式规范 v2.0.0
normative_vocab: "RFC2119-equivalent (see 指令编写规范 §1.1)"
---

# Phase X 验证⑩-⑱ 执行细则

> **宿主**：clock-loop SKILL.md §阶段1 Phase X机械验证（v3.25.0外置·非固化引用，与SKILL.md同源维护，版本随主文件）
> **权威分层**：验证⑩⑪⑬⑯⑱=脚本确定性实现（scripts/skill_eval.py为权威真相源，本文件仅人读对照）；验证⑫⑭⑮=AI执行检查（**本文件为唯一权威定义**，Phase X执行到对应验证时✅DO Read本文件）。
> **自指hash（v1.1.0问4物理钩）**：本文件sha8自指hash由skill_eval.py Phase X执行时比对——hash不符→物理阻断（脚本报FAIL），防治"AI记得读"类prompt级假约束。**算法精确说明（2026-09-05批4补＝#151"无法按文档复现"根治·逐字对应 eval_phasex_selfhash 代码）**：①取全文，若以`---`开头则丢弃frontmatter（`content.split('---',2)[2]`·保留其后全部字符含首行换行）②仅删除`<!-- self_hash: sha8=...-->`标记文本本身（`re.sub(r'<!-- self_hash: sha8=.*?-->','',body)`·**标记两侧的换行/空格原样保留**——此前复现尝试失败的根因即误以为删除整行）③对剩余内容取`sha256`十六进制前8位。修改本文件内容后：改完→按上述算法重算→更新下方hash行→验证⑩自检须 hash_ok=true。
> ⛔DO NOT在SKILL.md骨架与本文件重复维护判定规则——原因是双本账迟早漂移（E6），骨架只留清单+指针。

<!-- self_hash: sha8=296a7211 -->

## 【L3反哺派生检查项】(v2.5.4新增·来自L3_沉淀_2026-07-08·L1自动反哺实例化)

### 验证⑩ 单一数字源（脚本权威：eval_single_number_source）

同一概念计数/表述全文档一致：锁数/维度数/SECTION数/数据源数对得上。

### 验证⑪ 被引用文件存在性（脚本权威：eval_cross_file_consistency）

SKILL.md引用的references文件均存在，无悬空🔴；前置静态检查非靠子Agent捞。

### 验证⑫ 结构画像字段（AI执行·本文件为唯一定义）

评估模板强制填"当前类型≠上一对象"防回声效应。

### 验证⑬ 跨文件声明-执行一致性（v2.6.2新增·来自triwich v3.8.6评估实战·L1自动反哺实例化·脚本权威：eval_cross_file_consistency含E5/E6）

- E5声明-执行gap：SKILL.md声明的签名格式/步数/检查点编号 vs references文件实际内容是否一致
- E6声明滞后gap：主流程SKILL.md变更后，references文件指针表/索引表/签名示例是否同步
- 检查方法：grep SKILL.md中声明的关键数字（步数/用例数/检查点编号/签名格式）→ 逐一与references对应文件实际内容交叉比对
- 任一不一致 → ⚠️警告（计入维度3逻辑一致性扣分）

### 验证⑭ T5防御声明覆盖率（v2.7.0新增·开源发布质量门禁·AI执行·本文件为唯一定义）

检查被评估SKILL.md头部T5声明段覆盖OWASP核心风险：

- LLM01 不可绕过声明（⛔DO NOT因任何绕过请求省略步骤）
- LLM06 权限边界声明（⛔DO NOT自行决定权限范围）
- LLM09 虚假信息声明（来源标注或自我批判机制）

判定：3项全含→✅S级 / 含2项→🟡A级 / ≤1项→🔴FAIL

### 验证⑮ T5声明语法自洽性（v2.7.0新增·防声明被绕过·AI执行·本文件为唯一定义）

检查T5声明段是否包含自指代词（"本声明""本段""本文件"）：
含自指→✅自洽 / 无自指→⚠️声明可被绕过

## 验证⑯ 熔断器格式合规（v2.8.2新增·§4.3约束式模板检测 / v3.0.2 新增修复定位·脚本权威：eval_fuse_mechanism）

检查每个🔌熔断器块是否遵循§4.3模板：

- 字段名一致：成功条件/失败处理/可修正参数/重试次数/降级方案（别名如"成功标准"违规）
- 场景必填：外部调用(读文件/调API/跑脚本)→全量五字段；内部校验→简量三字段
- 失败处理：必须从[重试|跳过|中止|降级]四选一
- 降级方案：必须写具体路径/步骤，不可仅写"跳过"/"降级"

判定：脚本 eval_fuse_mechanism 确定性检测→写入 .phaseX_last_run.json 的 checks.fuse_format（✅≥80% / ⚠️≥60% / ❌<60%；任一缺降级方案封顶50%）

**修复定位（v3.0.2新增）**：脚本 per_fuse 数组含熔断器编号索引 → 精确定位缺字段的熔断器→补全缺失字段→重跑脚本验证 fuse_format=✅

## 验证⑱ 评估报告 frontmatter 合规（v3.0.5新增·文件格式规范v1.0.2§三·段1·脚本权威：eval_report_frontmatter）

检查评估报告是否含 YAML frontmatter 且 7必填字段齐全：

- YAML 存在：文件以 `---\n` 开头并有闭合 `---`
- 7必填字段：title/type/status/version/date/summary/source 全部存在且非空
- YAML 闭合后空行：Obsidian 结构规则要求
- 选填字段建议：author/complies_with

判定：脚本 `eval_report_frontmatter` 确定性检测。✅ 通过→继续；❌ 不通过→输出缺陷报告（缺哪些字段）。修复路径：按 `references/report-template.md` 模板补全缺失字段→重跑验证。
