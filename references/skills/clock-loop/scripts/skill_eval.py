#!/usr/bin/env python3
"""
Skill S级合规评估脚本 v4.9.0
基于《皮叔·Skill架构规范 v5.34》+《指令编写规范 v4.2》

v4.9.0 变更（2026-09-11 · L1候选1 references 索引段结构强制·L3沉淀2026-09-11模式C落地·皮叔授权后执行）：
  - P1 eval_cross_file_consistency 新增第6检查项 _check_refs_index_section()（三子查）：
    ①专用索引段存在（references/ 有顶层 .md 时强制·标题须含 references+索引/目录）
    ②索引段内反引号登记文件名 ⊇ references/ 顶层 .md 实存（子目录由目录级登记项覆盖）
    ③references/eval-set.md 存在时索引段内须声明用例数（N条用例）
    根治两洞：eval_file_clutter 宽松Union（登记散落正文各处仍通过·结构不可审查）+
    _check_eval_set_count 中性放行（eval-set.md 存在但 SKILL.md 永不声明用例数→na 不计）。
  - 自身合规：clock-loop SKILL.md 索引段补 eval-set 用例数声明（47 条）。
  - 回归：unittest 全绿·自举 passed=True 100/S S(exercised)·TestRealSkills 全绿（clock-loop/triwich/GS-1 索引段齐全）。
v4.8.2 变更（2026-09-05 · P2 eval_version_uniform 块级拆分·台账#302 三判据驱动·你"继续"后执行）：
  - P2 eval_version_uniform 拆分：281行 7 步中两块独立职能提取为模块级函数——
    步骤6 依赖核对 → _check_dependencies()（~100行·只写 dependencies+warnings 两键·改动热点独立化），
    步骤7 固化对账 → _check_cured_snapshot()（~30行·子进程职能独立化）；
    normalize_ver 闭包提模块级（纯函数）。版本流水线（步骤1/2/4/5/5.5/.）共享状态强保留主体（~150行）。
  - 回归：unittest 128/128 OK·自举 passed=True 100/S S(exercised)·B3 heaviest 已无 eval_version_uniform
    与 eval_cross_file_consistency 与 main（Top3：eval_poka_yoke_depth 204/_run_batch_report 179/evaluate_skill 162）。
v4.8.1 变更（2026-09-05 · P0/P1 函数拆分·B3 复杂度度量驱动·你"认可做吧"后执行）：
  - P0 main 拆分：427行 main 收窄为纯模式分发器（~90行）——--check-only 提取为
    _run_check_only()（~150行·sys.exit(0)→return 0），全量评估提取为 _run_batch_report()
    （~180行·含 sys.exit(2) 无效目标判存）。分发链行为不变（-h/--update-watermark/
    --check-l1l2/--check-frontmatter/--check-report-content 留在 main）。
  - P1 eval_cross_file_consistency 拆分：225行 5 检查块独立成函数（_check_eval_set_count/
    _check_signature_format/_check_license_consistency/_check_indexed_files_exist/
    _check_step_count_consistency）——主函数仅聚合（~45行），检查1三态计分（increment=
    mismatch is None and compared）与检查5 warnings 聚合原样保真；顺手移除死代码 step_decls。
  - 回归：unittest 128/128 OK·自举 passed=True 100/S S(exercised)·B3 heaviest 已无 main
    与 eval_cross_file_consistency（Top3：eval_version_uniform 281/eval_poka_yoke_depth 204/
    _run_batch_report 179）。
v4.7.0 变更（2026-09-05 · B1 常响根治——4常响项按根因类型处理·B1自我观察闭环第一轮消费）：
  - ceiling 分级错误修正（状态当告警）：format_ceiling_advisory 🔴告警→ℹ️状态行（触顶是 S 级
    常态状态·非异常）；⛔移出 B1 触发率统计（_adv_map 剔除 ceiling——状态指示不参与告警频度·
    B1 只统计告警型·11 项并列）。
  - completeness 误报修正（未识别 gitignore）：流程执行型#4 运行时文件经 _git_check_ignored
    （git check-ignore）识别——被忽略=不随包分发=合规·静默；非 git 仓库/命令失败→保守提示
    （防漏报）。新增 ignore_fn 注入参数（测试友好·默认 _git_check_ignored）。
  - 考题滞后（staleness·真滞后）：B1 首轮识别 v4.x 机制未登考题（38项止于 v3.55.x）——
    ⛔考题增删仅限三授权通道（SKILL.md 禁止行为#13）→ 补登清单（39-47条）交你裁决·非擅动。
  - 核销缺失（similar_scan·纪律未执行）：v4.6.0 条目含"根治"缺核销→CHANGELOG 补记
    （同类扫描终扫在案·12 项 advisory 根因分类扫）。
v4.6.0 变更（2026-09-05 · 评估器自我观察（Observability）·B1/B2/B3/A1 四机制·X级收尾后第一轮）：
  - B1 eval_advisory_frequency()——advisory 触发率统计（"狼来了"治理：12项advisory全响=没响）。
    载体 scripts/.advisory_history.jsonl（追加写·与 .phaseX_last_run.json 同族·运行时状态文件
    ⛔不进包）。每次 --check-only 记录各 advisory 触发快照；统计最近 window=10 次触发率，
    样本 ≥5 次且触发率 ≥80% → 常响折叠提示（建议转自动/降级·终判权在人）。
  - B2 eval_checker_hygiene()——检查器卫生审计（l3_conclusion_guard 事故制度化预防）：
    带 v4. 版本标注（=新判据立法标记·§2.2a）的检查函数若无直接测试引用 → ⚪提示。
  - B3 compute_checker_complexity()——评估器自身复杂度度量（210KB/20维度·瘦身前提）：
    ast 解析统计总行数/函数数/平均与最大函数行数/Top-N 最重（⚪提示级·体量≠质量·Goodhart边界）。
  - A1 format_evidence_summary()——证据复核入口一行：exercised 档人可读汇总
    "N条运行时证据·ceiling/capped·明细见 evidence.upgrade_refs"（100分可查证最后一公里）。
  - --check-only 输出新增 advisory_frequency/advisory_frequency_advisory/checker_hygiene/
    checker_complexity/evidence_summary 五字段（均不计分·None/无异常=静默）。
v4.2.0 变更（2026-09-05 · C06跨周期学习断裂·教训召回·#68愿景③④核心缺口）：
  - 新增 eval_lessons_recall_advisory()——跨周期学习断裂自动召回：读 steps/lessons_ledger.md
    （AI 犯错误后登记的教训台账·LESSON-N 条目含错误模式/正确姿势/防法/首犯/最近犯/次数），
    召回活跃教训（最近犯日 ≤30 天·按最近犯日倒序 Top 3）输出到 --check-only 开工上下文。
    背景：#68"教训入账却从未阻止下一次"——SearchReplace 中文错字史 07-29×2+09-04×1、
    本会话 13 次方法错误，每次教训都入账却从没被新会话读到（新会话读不到=等于没发生）。
  - 判定三态：载体缺失→None 静默（幂等）｜无活跃教训→None 静默｜有活跃→🔴召回 Top3+总数
    ｜载体存在但全条目解析失败→fail-visible advisory（⛔不静默当无教训）。
  - --check-only 输出新增 lessons_recall_advisory 字段（10 项 advisory 并列·不计分·None=无异常）。
v4.1.0 变更（2026-09-05 · C07并发写入协调·版本水位线·#184跨会话并发实锤驱动）：
  - 新增 eval_version_watermark() advisory（跨会话/并发写入检测）——载体 steps/version_watermark.md
    记录"上次本会话见过的版本"，比对实盘版本三态判定：载体缺失→None静默（首次）、
    载体<实盘→🔴版本推进advisory（⛔先同步再动手）、载体>实盘→⚠️版本回退异常。
    背景：#184 09-05 并发会话同时改 clock-loop 资产——发现时 SKILL.md 已是 v3.47.0、
    CHANGELOG 已被并发方推进。修法候选="清单加版本水位线字段·每会话开工先读当前 version 比对"。
  - 新增 update_version_watermark() + --update-watermark 模式（显式初始化/更新载体，
    ⛔不自动调用——--check-only 是纯读评估，写文件须 AI 显式动作）。
  - --check-only 输出新增 watermark_advisory 字段（不计分·None=无异常·§7.5静默）。
v4.0.2 变更（2026-09-05 · C05承诺核销制·prose纪律机械化）：
  - 新增 eval_similar_scan_advisory()——同类扫描核销闹钟（"修一处必同类扫描"机械化：
    修复类 CHANGELOG 条目缺同类扫描证据 → advisory 提示·不计分·人终判）。
  - --check-only 输出新增 similar_scan_advisory 字段。
v3.40.0 变更（2026-09-02 · 防误层深度验证·daily-buddy月报跳步事故驱动）：
  - 新增 eval_poka_yoke_depth() 函数——5项P0深度检查：
    ①D1脚本物理拦截识别（终检声明是否有对应脚本调用）
    ②D2工作流防误标准一致性（同一Skill内不同工作流终检是否都有脚本拦截）
    ③D3 AI校验伪装脚本拦截（声明"自动校验"但无实际脚本调用）
    ④D4文本门禁当物理约束（声明"中止输出"但无脚本exit code拦截）
    ⑤D5门禁vs建议（终检/前置条件位置出现建议性措辞）
  - poka_yoke_layer权重15分拆为10分（原有三法）+5分（深度验证），满分仍15分
  - --check-only输出新增poka_depth/poka_depth_detail/poka_base字段，checks新增poka_depth项
  - 根因：eval_poka_yoke只检查"有没有防误关键词+结构化描述"，不检查"防误机制是脚本
    物理拦截还是AI自检清单"。daily-buddy月报终检是AI自检清单（文本checkbox），可被绕过
    ——第6.5步五容器回流整步跳步，但clock-loop给S级98分未检出。从"文档有没有提到防误"
    升级到"防误机制是不是真的能工作"。
v2.9.12 变更（2026-09-27 · 标准库损坏honest升档 + 测试脚本缓存同族根治 · clock-loop自评Loop R1）：
  - compute_honest_pass 新增可选参 staleness_advisory——task-standards.json 缺失/解析异常时升红字
    "标准库损坏"（v4.12.7待办落地·触发=本轮自评Loop）。⚪="没法查"是对象侧三态；标准库是评估器
    自身评测前提，前提断裂="查出问题"级，沉默放行=考题基线失效仍出绿灯。回归护栏：
    TestHonestPass.test_standard_corruption_escalates / test_normal_staleness_no_flag。
  - test_record_fix.py / test_evidence_guard.py 补最高位 dont_write_bytecode——v4.12.13 只覆盖
    test_skill_eval.py，本轮实跑三件套复现缓存残留（file_clutter candidate-found实证·修A不修全链）。
  - 验收口径升级：回归三件套全OK + 全树零缓存 + 自评不降分（冻结基线100@21:43；污染态99复现病灶）。
v2.9.11 变更（2026-09-27 · judge_defect 根治·双盲第12次校准发现）：sys.dont_write_bytecode 最高位设置——
  本脚本被 import（回归/工具链）时 Python 先写 __pycache__/skill_eval.pyc 再执行模块体，file_clutter 全树扫描
  随即抓到自产缓存 → 自评 clock-loop 恒扣1分（假阴性循环）。flag 置于一切可执行代码之前从源头消除。
  回归 153 OK·自评 100/S·复评后零缓存（四步闭环实证）。
v2.9.10 变更（2026-08-09 · G系列退役白名单·triwich L3冒烟驱动）：
  - eval_single_number_source 检查2（G系列编号连续性）新增退役豁免：缺失编号若在文档中
    显式声明"编号保留不重用/已被…替代/退役"（如 triwich 三源声明 G3 退役），则不计为跳号。
    病根=编号是标识符不是计数——标识符允许退役，计数不允许有洞；旧实现 range 差集把
    "正确退役"读成"跳号"，制造反向激励（补全更高编号提及反而扣分）。triwich v3.11.0 实测：
    补全 G4/G5 提及后 max 变大出洞扣 1 分（98/100）。修复对象=评分器，⛔不要求文档迎合评分器。
v2.9.9 变更（2026-08-09 · 口径漂移检测·皮叔拍板）：
  - eval_report_content 新增哲学维度判据口径漂移检测（P9实锤驱动）：报告哲学维度行若引用权威词表
    （七项/85%/及格）之外的判据（capped/present档/证据档）且缺权威判据词 → advisory告警（不计分·人终判）。
    病根=评估员自创"capped<85→0%"（2026-08-09 shall-we-talk 被打成 B 实为 S）。
v2.9.8 变更（2026-08-09 · 等级口径根治·皮叔拍板）：
  - 新增 compute_grade() 纯函数 = 等级判定唯一真相源（S≥90/A≥80/B≥70/C<70，与 --report L2704 同源）。
    --check-only 输出新增 'grade' 字段——此前 Phase X 机检不输出等级，报告等级全凭 AI 自创加权，
    导致 growth-box 89→S、scriyore 100→A 等口径漂移（2026-08-09 你定根治）。
  - ⛔DO NOT 在报告/流程另立等级规则；证据档位（present/wired/...）不参与 grade。
v2.9.7 变更（2026-08-09 · shall-we-talk P8 第一性原理修复）：
  - CHANGELOG 版本解析设计端消除：新增 _changelog_semantic_entries() 语义版本排序 helper，
    三个消费函数（eval_version_uniform / eval_version_grading_advisory / eval_assertion_advisory）
    从「文件首个 ### 条目=最新」位置假设改为「语义版本号最大条目=最新」。
    原因：位置顺序是文档惯例不是事实，shall-we-talk 曾把 v1.5.2 插在两条 v1.5.1 之间
    → version_uniform 误判版本不同步 → raw_pass 连带挂 → finalize 封口被拒（P8 实锤）。
    修复后条目乱序只降级为卫生 warning，不再产生版本一致性误判。
v2.9.6 变更（2026-08-09 · skill-forge Loop 发现修复）：
  - T5_MAX 动态化 = len(ADVERSARIAL_TESTS)*2（11项=22分），修复分母硬编码20掩盖缺项（
    "20/20"曾掩盖 T5-06 未命中）；t5_declarations 分母同步动态。
  - 报告头版本号与 docstring 对齐（v2.9.1 → v2.9.6）。

用法：python3 skill_eval.py [skill目录1] [skill目录2] ...
      不指定参数则扫描8个核心Skill

设计原则（第一性原理）：
  满分 = 100 是不可动约束。所有维度权重集中在 WEIGHTS 字典，
  启动时 assert sum(WEIGHTS)==100 物理防止满分溢出（Poka-Yoke 定值法）。
  新增维度必须在 100 内重新分配，不能简单加总（v2.2 曾误加到 105 → v2.3 修正）。
  v2.4 变更：① backup_gate（§6.6备份）降为非计分提醒——属流程层规则，
    其真值在「修改动作」而非文件内，计分=层错误+破坏幂等，正确载体是改前自动备份钩子；
    ② poka_yoke 检测器关键词刚性修复——同义词宽泛识别，消除对「接触法/步序法/阻断条件」
    等合规词汇的误杀。
  v2.8.2 变更：eval_fuse_mechanism 升级为 §4.3 格式合规确定性检测——校验字段名一致、
    场景必填字段（全量五/简量三）、失败处理四选一、降级方案具体性；
    结果接入 Phase X .phaseX_last_run.json 的 checks.fuse_format（权重复用原 5 分，满分仍锁 100）。
  T5 对抗性测试是独立 2×声明条目数 分维度（T5_MAX动态·规范§6.5），不计入主分。
  v5.16.0 变更（token_budget 根治·L2·L5 驱动）：① token_budget 从 WEIGHTS 移出·不再参与评分·
  测的是行数代理噪声·非质量本身；② poka_yoke_layer +2 (15→17)·security_hardcode +3 (5→8)·总分不变=100；
  ③ 行数结果移入 token_budget_advisory·触发条件"警告及以上"（原仅"不可接受"）·纯提醒不扣分；
  ④ 密度系数校准保留（计算用）但不再作为"安全线上浮"依据·因安全线本身已不触发扣分。
  理论支撑：梅多斯系统之美（杠杆点违反直觉）+ 第一性原理（行数与质量无因果）+ L5 已接受边界。
  v2.9.1 变更：新增 eval_mechanism_selection（规范§2.2 机制选配矩阵核查）——信号打分
    自动判Skill类型（流程执行/生成/查询/转换/交互/分析）× 关键词检6机制，输出该类型
     MUST(✅DO)缺口与⚠SHOULD NOT违例。独立报告块（与攻击面同），不进锁死100分。
  v2.9.4 变更（补记·v2.9.0 注释遗漏）：密度系数加权（规范§2.3 v5.15）——密度≥0.90安全线上浮25%/≥0.85上浮15%/≥0.80上浮5%/<0.80不调整。
  v2.9.5 变更（v5.16配套）：D5 角色维度解耦——engine/host 类评分豁免(1.0)+独立 d5_advisory(不计入分)+band「预期·引擎类」；新增 ENGINE_ROLES/_extract_role/_build_d5_advisory。leaf/methodology 逻辑不变。满分100与T5独立20分不动。
    类型判定信号已校准：分析型须具体词（思考检查点/结论块/多Agent/哲学）不用泛词"分析/批判/推理"，
    流程执行型含"步骤/流程"泛词——修正初版把awaken/system-logger/growth-box误判为分析/转换型。
"""
# v2.9.11（2026-09-27·judge_defect根治·双盲第12次校准发现）：禁写运行时字节码——
# 本脚本被 import 时（回归/工具链）Python 会先写 __pycache__/skill_eval.pyc 再执行模块体，
# 故 flag 必须置于一切可执行代码之前（模块体内的设置拦不住自身那次写入）。
# 实证链：删缓存→自评100→缓存复现→定位=回归 import 瞬间写入→本修复（最高位）后回归+自评全程零生成。
import sys as _sys_dw
_sys_dw.dont_write_bytecode = True
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
import re
import sys
import json
import glob
import subprocess
from pathlib import Path
from datetime import datetime, date

# ── 8个核心Skill路径 ──────────────────────────────────────────────
CORE_SKILLS = [
    os.path.expanduser("~/.workbuddy/skills/shall-we-talk/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/triwich/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/awaken-memory-system/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/daily-buddy/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/system-logger/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/growth-box/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/meta-aletheia/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/sucair/SKILL.md"),
]

# ── 备份目录（§6.6 备份门禁检测用）────────────────────────────────
BACKUP_DIR = os.path.expanduser("[记忆共享中心]/记忆琥珀/技能升级备份")

# ══════════════════════════════════════════════════════════════════
#  权重字典（唯一权威源）· 满分锁死 100
#  改权重只改这里；assert 保证任何改动后总分仍=100（物理防超100）
# ══════════════════════════════════════════════════════════════════
WEIGHTS = {
    # —— 元数据完整性 ——
    'yaml_frontmatter':               4,   # 标准§1 name/description/---
    'yaml_required_fields':           3,   # 标准§1 author/source 必填【v2.3新增】
    'description_not_for':            4,   # 标准§1/§1.1 反向触发NOT for子句【v2.3新增】
    'sec_1_2_version_single_source':  5,   # 标准§1.2 版本号唯一源
    # —— 话术质量 ——
    'five_level_annotations':         5,   # 指令§1.1 五级标注
    'no_binary_annotations':          4,   # 指令§1.1 无MUST/NEVER残留
    'causal_chain':                   5,   # 指令§二 因果链强制【v2.3新增】
    'alternatives_considered':        6,   # 指令§5.8 Alternatives
    # —— 防错设计（Poka-Yoke 是第一原则，权重最高）——
    'poka_yoke_layer':               17,   # 指令§5.7 三方法设计端防错【v2.4 关键词刚性修复+权重↑；v5.16.0 +2 由 token_budget 释放·梅多斯杠杆点·第一原则理应更重】
    'fuse_mechanism':                 5,   # 标准§4.3 熔断器
    'deliverable_definition':         5,   # 标准§4.1 产出物锁
    # —— 触发与结构 ——
    'trigger_conditions':             7,   # 标准§7.1 触发条件段
    # 'token_budget' v5.16.0 移出评分·移入advisory（详见 release 说明·第一性原理：行数与质量无因果·静态行数替代运行时证据=L5盲区）
    'position_risk':                  4,   # 指令§8.2 关键指令前置
    'cross_file_consistency':         4,   # 标准§2 跨文件一致
    'single_number_source':           3,   # 标准§2 验证⑩单一数字源【v2.8.5新增】
    'file_clutter':                   3,   # 标准§2 无README/无杂乱【v2.8.5: 4→3】
    # —— 门禁类（P0/安全）——
    'eval_set_gate':                  6,   # 标准§6.1 评估集门禁(P0)【v2.8.5: 7→6】
    'trigger_coverage':               2,   # 标准§6.2 触发测试覆盖【v3.30.0新增·互审整改P2-2】
    'security_hardcode':              8,   # 指令§四/§4.3 无绝对路径+XML【v2.3新增；v5.16.0 +3 由 token_budget 释放·安全类P0理应更重】
    # 注：backup_gate（§6.6 修改前备份）v2.4 起降为非计分提醒（见下方说明）
}
# ⛔ Poka-Yoke 定值法：满分必须=100，任何权重改动后此断言物理拦截溢出
assert sum(WEIGHTS.values()) == 100, \
    f"权重总和必须=100，当前={sum(WEIGHTS.values())}——修改 WEIGHTS 后请重新配平"

TOTAL_MAX = sum(WEIGHTS.values())  # =100

# ── 共享正则常量（避免重复定义）────────────────────────────────
# 版本号提取模式：匹配 `**版本**：vX.Y.Z` 形态（示例占位·防版本扫描自匹配＝#185⑤·2026-09-05批6e）
RE_VERSION_BOLD = re.compile(r'\*\*版本\*\*\s*[：:]\s*(v?\d[\w.]*)')
RE_VERSION_COLON = re.compile(r'版本[：:]\s*(v?\d[\w.]*)')
RE_VERSION_YAML = re.compile(r'^version:\s*["\']?(v?\d[\w.]+)["\']?', re.MULTILINE)

# ── 允许的Skill目录文件/目录（eval_file_clutter用）─────────────
ALLOWED_SKILL_FILES = {
    'SKILL.md', 'references', '_user_meta.json',  # v4.12.3·R3攻5：.DS_Store 除名——macOS垃圾=分发垃圾，不许写进户口
    'scripts', 'assets', 'tests',
    '.gitignore',  # v4.12.6·tw R2-N1补锁：为运行时态忽略规则新建的 .gitignore 反被根白名单当杂物（修A坏B）——仓库基建件合法入户口
}


def pts(key, ratio):
    """把 [0,1] 达成率换算为该维度实际得分（四舍五入到整数）"""
    return round(max(0.0, min(1.0, ratio)) * WEIGHTS[key])


# ══════════════════════════════════════════════════════════════════
#  宏观维度映射表（v2.8.8新增）
#  SKILL.md阶段2声明的6个宏观维度 → skill_eval.py的19个微观检查项（＝len(WEIGHTS)·⛔改此项须同步本注释·v4.12.1：注释自称"＝len(WEIGHTS)"却写死20=自我矛盾实锤,len=19）
#  每个微观维度必须追溯到唯一一个宏观维度。
#  verify_dimension_consistency()启动时自检，保证两层权重一致。
# ══════════════════════════════════════════════════════════════════
MACRO_DIMENSIONS = {
    # 宏观维度名: (声明权重%, [下属微观维度key列表])
    # v2.8.8: 声明权重=下属微观维度WEIGHTS之和/100，由verify_dimension_consistency()自检
    '开发规范':     (19, ['yaml_frontmatter', 'yaml_required_fields', 'description_not_for',
                            'sec_1_2_version_single_source', 'file_clutter']),
    '指令准确性':   (21, ['trigger_conditions', 'security_hardcode', 'eval_set_gate']),
    '逻辑一致性':   (29, ['causal_chain', 'poka_yoke_layer', 'cross_file_consistency',
                            'single_number_source']),
    '文档完整性':   (14, ['five_level_annotations', 'no_binary_annotations',
                            'deliverable_definition']),
    '测试覆盖':     (7, ['fuse_mechanism', 'trigger_coverage']),
    '哲学评估':     (10, ['alternatives_considered', 'position_risk']),
}

# ── C03: yaml权重对账映射（v3.55.4新增·#204）──────────────────────
# current_weights.yaml default_weights.skill 键 → MACRO_DIMENSIONS 宏观维度名
# 用途：AI手工评分镜像（yaml）与脚本权威源（WEIGHTS/MACRO_DIMENSIONS）的持续机械对账
YAML_WEIGHT_MAP = {
    'skill_development':    '开发规范',
    'instruction_accuracy': '指令准确性',
    'code_logic':           '逻辑一致性',
    'documentation':        '文档完整性',
    'test_coverage':        '测试覆盖',
    'philosophical':        '哲学评估',
}


def verify_dimension_consistency():
    """启动时自检：宏观维度与微观维度权重一致性。

    检查项（6项全过才允许运行）：
      1. 每个微观维度key在WEIGHTS中存在
      2. 每个微观维度只属于一个宏观维度（无重复归属）
      3. 宏观维度声明权重% == 其下属微观维度WEIGHTS之和 / 100 * TOTAL_MAX
         （容差±1分，因四舍五入）
      4. 宏观维度声明权重总和 = 100%
      5. 所有WEIGHTS中的微观维度都被MACRO_DIMENSIONS覆盖（无遗漏）
      6. （v3.55.4 C03新增）current_weights.yaml default_weights.skill 6键值
         == MACRO_DIMENSIONS 6宏观权重（AI手工评分镜像对账·#204）
         —— yaml不可达/解析失败 → ⚪无可比对（#115三态·不阻断）

    返回 (passed: bool, detail: list[str])
    """
    detail = []
    passed = True

    # 检查1：微观维度key存在性
    for macro, (_, micros) in MACRO_DIMENSIONS.items():
        for m in micros:
            if m not in WEIGHTS:
                detail.append(f'❌ 微观维度"{m}"在MACRO_DIMENSIONS中声明但不在WEIGHTS中')
                passed = False

    # 检查2：无重复归属
    all_micros = []
    for macro, (_, micros) in MACRO_DIMENSIONS.items():
        for m in micros:
            if m in all_micros:
                detail.append(f'❌ 微观维度"{m}"被多个宏观维度重复归属')
                passed = False
            all_micros.append(m)

    # 检查5：无遗漏（WEIGHTS中所有key都被MACRO_DIMENSIONS覆盖）
    uncovered = set(WEIGHTS.keys()) - set(all_micros)
    if uncovered:
        detail.append(f'❌ WEIGHTS中以下微观维度未被MACRO_DIMENSIONS覆盖: {sorted(uncovered)}')
        passed = False

    # 检查3：宏观声明权重 vs 微观实际权重
    for macro, (declared_pct, micros) in MACRO_DIMENSIONS.items():
        actual_score = sum(WEIGHTS[m] for m in micros)
        declared_score = round(declared_pct / 100 * TOTAL_MAX)
        if abs(actual_score - declared_score) > 1:
            detail.append(f'❌ 宏观维度"{macro}"声明{declared_pct}%={declared_score}分，'
                          f'但下属微观维度实际={actual_score}分（差{abs(actual_score-declared_score)}分）')
            passed = False

    # 检查4：宏观权重总和=100%
    total_pct = sum(pct for pct, _ in MACRO_DIMENSIONS.values())
    if total_pct != 100:
        detail.append(f'❌ 宏观维度声明权重总和={total_pct}%，应为100%')
        passed = False

    # 检查6（v3.55.4 C03新增）：current_weights.yaml 权重对账（#204）
    # 541行AI手工评分体系资产与脚本并行无对账·v1.3曾一次性对齐（19/18/27/14/12/10）但无持续机制
    # 判据：yaml default_weights.skill 键值 == MACRO_DIMENSIONS 声明权重（%值）
    #       yaml 不可达/解析失败 → ⚪无可比对不阻断（#115三态·yaml是AI手工参照镜像非脚本必需）
    yaml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', 'references', 'eval-knowledge', 'weights', 'current_weights.yaml')
    if os.path.isfile(yaml_path):
        try:
            with open(yaml_path, encoding='utf-8') as f:
                yaml_text = f.read()
            yaml_w = {}
            in_skill = False
            for line in yaml_text.splitlines():
                if re.match(r'^  skill:\s*$', line):
                    in_skill = True
                    continue
                if in_skill:
                    m = re.match(r'^    (\w+):\s*([\d.]+)', line)
                    if m:
                        yaml_w[m.group(1)] = float(m.group(2))
                    elif line.strip() and not line.startswith('    '):
                        in_skill = False
            yaml_bad = [f'{k}={yaml_w[k]}' for k in YAML_WEIGHT_MAP
                        if k in yaml_w and abs(yaml_w[k] * 100 - MACRO_DIMENSIONS[YAML_WEIGHT_MAP[k]][0]) > 0.5]
            if yaml_bad:
                detail.append(f'❌ current_weights.yaml 权重滞后脚本权威源: {" ".join(yaml_bad)}——AI手工评分镜像须同步MACRO_DIMENSIONS')
                passed = False
        except Exception as e:
            detail.append(f'⚪ current_weights.yaml 解析失败（{e}）——对账跳过不阻断')
    else:
        detail.append('⚪ current_weights.yaml 不可达——权重对账跳过（AI手工镜像无机械比对·#115三态）')
        print('⚪ [verify_dimension_consistency] current_weights.yaml 不可达——镜像对账静默消失根治：不可查必须出声（v4.12.3·R3-N-10）', file=sys.stderr)

    if passed:
        detail.append(f'✅ 维度一致性自检通过：{len(MACRO_DIMENSIONS)}个宏观维度 → {len(all_micros)}个微观维度，权重完全对应')

    return passed, detail


# ── 闯关制检查（G1-G3一票否决）────────────────────────────────────
def check_unclosed_code_fence(content):
    """G1: 代码围栏必须闭合"""
    fences = re.findall(r'^(```|~~~)', content, re.MULTILINE)
    return len(fences) % 2 == 0

def check_internal_links(skill_path, content):
    """G2: 内部链接有效。
    排除围栏代码块(```...``` / ~~~...~~~)内的内容——代码块内的 [x](y) 是模板占位符，
    非真实文件链接，不计入断链检测。来源：shall-we-talk 实战（代码块内模板占位被误判断链）。"""
    skill_dir = os.path.dirname(skill_path)
    # 先剔除围栏代码块，避免模板占位符被当成文件链接误判（治本，而非让 Skill 改写法绕过）
    content_no_fence = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    content_no_fence = re.sub(r'~~~.*?~~~', '', content_no_fence, flags=re.DOTALL)
    link_pattern = r'\[.*?\]\((?!https?://)([^)]+)\)'
    links = re.findall(link_pattern, content_no_fence)
    for link in links:
        if link.startswith('#'):
            continue
        target = os.path.normpath(os.path.join(skill_dir, link))
        if not os.path.exists(target):
            return False, link
    return True, None

def check_yaml_fields(content):
    """G3: YAML必填字段齐全"""
    required = ['name', 'description']
    for field in required:
        if not re.search(rf'^{field}\s*:', content, re.MULTILINE):
            return False, field
    return True, None


# ── 工具：拆分 frontmatter / body / description ───────────────────
def split_frontmatter(content):
    parts = content.split('---', 2)
    if len(parts) > 2:
        return parts[1], parts[2]
    return '', content

def extract_description(frontmatter):
    m = re.search(r'description:\s*>?\s*\n?(.*?)(?=\n[a-zA-Z_]+:|\Z)',
                  frontmatter, re.S)
    if m:
        return ' '.join(l.strip() for l in m.group(1).splitlines() if l.strip())
    return ''


# ── 各维度评分（统一返回 [0,1] 达成率）─────────────────────────────
def eval_yaml_frontmatter(content):
    """YAML 基础字段 name/description/---"""
    score = 0
    if re.search(r'^name\s*:', content, re.MULTILINE): score += 1
    if re.search(r'^description\s*:', content, re.MULTILINE): score += 1
    if re.search(r'^---\s*$', content, re.MULTILINE): score += 1
    return score / 3

def eval_yaml_required_fields(frontmatter):
    """标准§1：author / source 必填（自建Skill必填）"""
    has_author = bool(re.search(r'^\s*author\s*:', frontmatter, re.MULTILINE))
    has_source = bool(re.search(r'^\s*source\s*:', frontmatter, re.MULTILINE))
    return (int(has_author) + int(has_source)) / 2, {
        'author': has_author, 'source': has_source}

def eval_description_not_for(frontmatter, content):
    """标准§1/§1.1：description 必含 NOT for / 不适用于 反向触发子句"""
    desc = extract_description(frontmatter)
    hay = desc if desc else content
    ok = bool(re.search(r'NOT\s+for|不适用于|不适用|NOT\s+FOR', hay, re.I))
    return (1.0 if ok else 0.0), ok

def eval_sec_1_2_version_single_source(content):
    """§1.2 版本号唯一源：正文/description/H1 不得重复声明版本号"""
    ratio = 1.0
    violations = []
    frontmatter, body = split_frontmatter(content)
    desc = extract_description(frontmatter)
    if re.search(r'v\d+\.\d+', desc) or '封版' in desc:
        ratio -= 0.6; violations.append('description 含版本戳/封版字样')
    if re.search(r'\*\*版本\*\*', body):
        ratio -= 0.4; violations.append('正文含 `**版本**` 元数据行')
    if re.search(r'^#\s+.*?(v\d+\.\d+).*$', body, re.MULTILINE):
        ratio -= 0.4; violations.append('H1 标题含版本号')
    return max(ratio, 0.0), violations

def eval_five_level_annotations(content):
    """指令§1.1 五级标注覆盖"""
    annotations = ['✅DO', '☑SHOULD', '✔MAY', '⚠SHOULD NOT', '⛔DO NOT']
    total = sum(len(re.findall(re.escape(a), content)) for a in annotations)
    if total < 5:
        return 0.0
    return min(total / 5, 1.0)

def eval_no_binary_annotations(content):
    """指令§1.1 无旧版 MUST/NEVER 残留"""
    return 0.0 if re.search(r'\bMUST\b|\bNEVER\b', content) else 1.0

def eval_causal_chain(content, skill_path=None):
    """指令§二 因果链强制：禁令应附原因。
    行级宽松检测——禁令所在行含 原因/因为/破折号解释/因果词 即算达标。
    阈值 40%：压缩式Skill的表格禁令按单一来源原则可把原因外置到 references，
    SKILL.md 头部用指针引用（如「禁令因果链理由 → references/因果链理由.md」），
    外置的原因计入达标基准——既满足因果链、又不撑爆行数（规范§二允许，本就声明于docstring）。"""
    rule_pat = re.compile(r'(⛔\s*DO\s*NOT|☑\s*SHOULD\s*NOT|⚠\s*SHOULD\s*NOT)')
    reason_pat = re.compile(r'原因|因为|——|会导致|否则|等于|=|防止|导致')
    prohibitions = 0
    reasoned = 0
    for line in content.splitlines():
        if rule_pat.search(line):
            prohibitions += 1
            if reason_pat.search(line):
                reasoned += 1
    if prohibitions == 0:
        return 1.0, {'prohibitions': 0, 'reasoned': 0, 'ext_reasoned': 0}
    # 外部化原因（规范§二·单一来源）：检测头部指针引用 references 原因文件，计入达标基准
    ext_reasoned = 0
    if skill_path:
        ptr = re.search(r'(因果链|禁令理由|原因说明|理由).{0,30}(references/[\w./\-]+\.md)', content)
        if ptr:
            ref_path = os.path.normpath(os.path.join(os.path.dirname(skill_path), ptr.group(2)))
            if os.path.exists(ref_path):
                with open(ref_path, encoding='utf-8') as _fh:
                    ref_text = _fh.read()
                # 外置文件中含原因标记的行即计为外部化原因（上限=禁令数，避免超额）
                ext_reasoned = min(sum(1 for l in ref_text.splitlines() if reason_pat.search(l)),
                                    prohibitions)
    total_reasoned = min(reasoned + ext_reasoned, prohibitions)
    # 达标基准=禁令数的40%附原因即满分
    ratio = min(total_reasoned / (prohibitions * 0.4), 1.0)
    return ratio, {'prohibitions': prohibitions, 'reasoned': reasoned, 'ext_reasoned': ext_reasoned}

# ── v3.47.0 A31: eval_alternatives 判据精细化（范式=同文件P9口径漂移检查的三条件AND·L2883-2903：
#    精确匹配缺陷形态、不误伤合法形态）────────────────────────────
# 缺陷形态（#209/#215/#231③实测）：
#   ①裸正则3关键词任一命中即满分→否定句"经权衡后认为无需替代方案"也满分（GS-2重建配方第①步）
#   ②指针式Alternatives（3行指针指向CHANGELOG）拿满分而不核验指向物是否存在且含实质内容
#     （#240精确化：指针式是体系设计⭕合法——真bug是"不核验指向物"，复用declared_existence的
#      "文档vs磁盘"能力）
# 三条件AND：段存在（标题）→ 非空壳（否定句且无决策语义=空壳）→ 内容有效（内联决策语义 或 指针指向物存在且含实质）
RE_ALT_HEADING = re.compile(r'^#{1,6}[^\n]*?(?:Alternatives\s*Considered|替代方案)[^\n]*$', re.M)
RE_ALT_POINTER = re.compile(r'`?([\w./\-]*\.(?:md|json|yaml))`?')
RE_ALT_SHELL = re.compile(r'无需替代方案|无替代方案|没有替代方案|不做权衡|无须权衡|不涉及替代')
RE_ALT_DECISION = re.compile(r'弃|不选|否决|拒绝|采用|选择|优于|相比|理由|放弃|未采用|弃用')
RE_ALT_TARGET_SUBSTANCE = re.compile(r'替代方案|权衡|Alternatives')

def eval_alternatives(content, skill_path=None):
    """指令§5.8 Alternatives Considered 段存在且含实质内容（v3.47.0 A31判据精细化）

    返回值分级（旧版二值0/1.0→三态，与#143三态分级同哲学）：
      1.0 = 段存在 且 （内联实质（含决策语义：选/弃/否决/理由…） 或 指针指向物存在且其中含替代方案实质≥2处）
      0.3 = 段存在但空壳（纯否定句无决策语义 / 纯指针但指向物缺失或不含实质 / 标题下无内容）
      0.0 = 段不存在（关键词零命中不算——旧版正文散文提一嘴"权衡"就满分，是Goodhart化根病灶）
    """
    m = RE_ALT_HEADING.search(content)
    if not m:
        return 0.0
    level = len(m.group(0)) - len(m.group(0).lstrip('#'))
    rest = content[m.end():]
    nxt = re.search(r'^#{1,%d}\s' % level, rest, re.M)
    body = (rest[:nxt.start()] if nxt else rest).strip()
    if not body:
        return 0.3  # 标题空壳（段存在但零内容）
    # 条件③a 指针核验（优先——指针式是体系设计，指向物真且含实质=满分）
    ptr = RE_ALT_POINTER.search(body)
    if ptr and skill_path is not None:
        base = os.path.dirname(os.path.abspath(skill_path))
        cand = os.path.expanduser(ptr.group(1) if ptr.group(1).startswith('/')
                                  else os.path.join(base, ptr.group(1)))
        if os.path.isfile(cand):
            try:
                with open(cand, encoding='utf-8') as f:
                    if len(RE_ALT_TARGET_SUBSTANCE.findall(f.read())) >= 2:
                        return 1.0
            except Exception:
                pass
    # 条件③b 内联实质：含决策语义（选/弃/否决/理由…）即非空壳
    if bool(RE_ALT_DECISION.search(body)):
        return 1.0
    return 0.3  # 段存在但无效：纯否定空壳 / 指针失效 / 无决策语义的空泛段

def eval_poka_yoke(content):
    """指令§5.7 Poka-Yoke 设计端三方法（接触法/定值法/动作步序法）

    v2.8.6: 防关键词堆砌刷分。采用双重验证：
    ①关键词计数（宽松阈值≥2）
    ②结构验证：找含方法名的段标题，检查该段后续≥3行内容
    满分=关键词≥2 + 有结构化描述（段标题+后续内容）
    纯堆砌（有关键词但无段标题+内容）最高0.5。
    三方法等权。
    """
    # 接触法 contact：物理特征/锚点/声明存在性约束
    contact_kw = r'锚点|接触法|接触式|物理锚点|物理特征|必填字段|字段锁|原话|引用用户|格式校验|格式不符|模板必填|边界约束'
    # 定值法 fixed-value：数量固定/数量锁
    fixed_kw   = r'定值法|定值|固定数量|数量锁|数量固定|N个|要素锁|退回补全|上限|下限|固定值'
    # 动作步序法 motion-step：步骤顺序/阻断
    motion_kw  = r'步序法|步序式|步骤间|动作步序|状态机|产出物锁|上步校验|阻断条件|阻断|强依赖|未完成则|不可执行|回到步骤'

    # 方法名识别（段标题用）
    method_names = [
        (r'接触法|接触式|contact', contact_kw),
        (r'定值法|定值|fixed-value|固定值', fixed_kw),
        (r'步序法|步序式|motion-step|动作步序', motion_kw),
    ]

    lines = content.splitlines()

    def eval_one_method(name_pat, kw_pat):
        """评估单个方法。
        满分=关键词≥2 + 有段标题+后续≥3行内容
        部分分=有关键词但无结构化描述
        """
        count = len(re.findall(kw_pat, content))
        if count == 0:
            return 0.0

        # 找段标题行（含方法名且是标题/列表项开头）
        name_re = re.compile(name_pat, re.I)
        title_indices = []
        for i, ln in enumerate(lines):
            stripped = ln.strip()
            # 标题行特征：以#开头、或以-开头、或表格行
            if name_re.search(stripped):
                if (stripped.startswith('#') or
                    stripped.startswith('-') or
                    stripped.startswith('|') or
                    stripped.startswith('*')):
                    title_indices.append(i)

        has_structured_desc = False
        if title_indices:
            # 检查段标题后续是否有≥3行内容
            for ti in title_indices:
                subsequent = 0
                for j in range(ti + 1, min(ti + 10, len(lines))):
                    nxt = lines[j].strip()
                    if not nxt:
                        continue
                    # 遇到下一个方法标题则止
                    if any(re.search(p, nxt, re.I) for p, _ in method_names if p != name_pat):
                        break
                    subsequent += 1
                if subsequent >= 2:
                    has_structured_desc = True
                    break

        # 评分逻辑：
        # ①关键词≥2 + 有结构化描述=1.0
        # ②关键词多样性≥3种 + 无结构化描述=0.8（多种关键词出现，即使无段标题也认为真实现）
        # ③关键词≥2 + 无结构化描述=0.5（疑似堆砌）
        # ④关键词=1 + 有结构化描述=0.9（有段标题+内容，关键词少但有真实现）
        # ⑤关键词=1 + 无结构化描述=0.3
        # 计算关键词多样性：不同匹配值的数量
        unique_matches = set(re.findall(kw_pat, content))
        diversity = len(unique_matches)
        if count >= 2 and has_structured_desc:
            return 1.0
        elif diversity >= 5:
            return 0.8
        elif count >= 2:
            return 0.5
        elif count >= 1 and has_structured_desc:
            return 0.9
        else:
            return 0.3

    contact_r = eval_one_method(method_names[0][0], method_names[0][1])
    fixed_r   = eval_one_method(method_names[1][0], method_names[1][1])
    motion_r  = eval_one_method(method_names[2][0], method_names[2][1])
    return (contact_r + fixed_r + motion_r) / 3


# ══════════════════════════════════════════════════════════════════
#  v3.40.0: 防误层深度验证（P0·daily-buddy月报跳步事故驱动·2026-09-02）
#  问题：eval_poka_yoke只检查"有没有防误关键词+结构化描述"，不检查"防误机制
#        是脚本物理拦截还是AI自检清单"。daily-buddy月报终检是AI自检清单（文本
#        checkbox），可被绕过——第6.5步五容器回流整步跳步，但clock-loop给S级98分。
#  解法：5项深度检查，识别"防误机制是不是真的能工作"，从"文档有没有提到防误"
#        升级到"防误机制是不是真的能工作"。
#  权重：从poka_yoke_layer的15分中分出5分给深度验证（10分原有三法+5分深度验证）
# ══════════════════════════════════════════════════════════════════

def eval_poka_yoke_depth(content, skill_path=None):
    """防误层深度验证——5项P0检查 + na改判 + 产出物锁密度回退（v3.42.0方案C）。

    返回 (depth_r, depth_detail)：
      depth_r: 0-1 达成率
      depth_detail: 字典，含每项的通过状态、na标注和证据；_scoring键含计分模式

    5项检查：
      D1 脚本物理拦截识别：终检声明是否有对应脚本调用（bash/python3/exit code）
      D2 工作流防误标准一致性：同一Skill内不同工作流的终检是否都有脚本拦截
      D3 AI校验伪装脚本拦截：声明"自动校验/机械验证"但无实际脚本调用
      D4 文本门禁当物理约束：声明"中止输出/不能输出"但无脚本exit code拦截
      D5 门禁vs建议：终检/前置条件位置出现"建议/可选/推荐"等建议性措辞

    v3.42.0 na改判（治"5分照拿"病根·证据档位虚高S107）：
      - D1-D4无触发信号时判na（不适用）——⛔不再默认pass计入分子分母
      - D1-D4有任一适用项（流程执行型）：适用项+D5等权计分（原行为保持）
      - D1-D4全na（非流程型）：回退产出物锁📦密度判据 min(计数/5, 1.0)
        （复用§4.1 deliverable_definition判据·不新建维度·权重不动）
      - 不可能静默（C-090）：全na且📦=0 → depth_r=0 + 显式⚠️拦截警告

    ⚠️ 诚实边界（宪法级原则6）：本函数只到行为层（关键词/计数可复现判定），
    语义层"防误设计是否真有效"须人工抽审+双盲——📦密度是代理指标（S022），
    可被廉价命中（写1个📦得0.2分），内容质量须对抗验证（Agent B审📦实质）。
    """
    lines = content.splitlines()
    detail = {}

    # ── D1: 脚本物理拦截识别 ──
    # 搜索终检/收口声明
    final_gate_patterns = [
        r'终检', r'收口', r'封口', r'最终检查', r'最终校验',
        r'必须全部.*才能输出', r'不通过.*不能输出', r'中止输出',
    ]
    has_final_gate = any(re.search(p, content) for p in final_gate_patterns)

    # 搜索脚本调用信号（bash/python3 + .py / exit code / exit 0/1）
    script_call_patterns = [
        r'bash\s+.*\.py', r'python3?\s+.*\.py', r'python\s+.*\.py',
        r'exit\s+code', r'exit\s+[0-9]', r'退出码', r'\$\?',
        r'dbbin\.sh', r'scripts/.*\.py',
    ]
    has_script_call = any(re.search(p, content) for p in script_call_patterns)

    # 搜索AI自检清单信号（checkbox/必须全部✅/检查清单）
    ai_check_patterns = [
        r'- \[ \]', r'- \[x\]', r'必须全部.*✅', r'检查清单',
        r'终检清单', r'自检清单', r'逐项检查',
    ]
    has_ai_check = any(re.search(p, content) for p in ai_check_patterns)

    d1_na = False
    if has_final_gate and has_script_call:
        d1_pass = True
        d1_evidence = "终检声明+脚本调用信号命中"
    elif has_final_gate and has_ai_check and not has_script_call:
        d1_pass = False
        d1_evidence = "⚠️ 终检声明但仅AI自检清单（checkbox），无脚本物理拦截——可被绕过"
    elif not has_final_gate:
        d1_pass = True   # pass值保留向后兼容detail结构，但na=True不计入分母（v3.42.0）
        d1_na = True     # ⛔不再"视为通过"——na当present=证据档位虚高（S107·5分照拿病根）
        d1_evidence = "无终检声明（此项na·不计入分母·v3.42.0改判）"
    else:
        d1_pass = False
        d1_evidence = "终检声明但无脚本调用信号，需人工确认防误机制类型"
    detail['D1_script_physical_gate'] = {'pass': d1_pass, 'na': d1_na, 'evidence': d1_evidence}

    # ── D2: 工作流防误标准一致性 ──
    # 搜索多个工作流声明（工作流A/B/C/F 或 工作流1/2/3）
    workflow_pattern = r'工作流\s*[A-Z0-9](?![A-Za-z])'
    workflow_matches = re.findall(workflow_pattern, content)
    unique_workflows = set(workflow_matches)

    d2_na = False
    if len(unique_workflows) >= 2:
        # 多工作流Skill：检查每个工作流附近是否有脚本调用
        # 简化策略：统计全文脚本调用信号数量，如果只有1个但有≥2个工作流，可能不一致
        script_call_count = sum(len(re.findall(p, content)) for p in script_call_patterns)
        # 更精确：检查每个工作流标题后续50行内是否有脚本调用
        workflow_consistent = True
        inconsistent_workflows = []
        for wf in unique_workflows:
            wf_pattern = re.escape(wf)
            for i, ln in enumerate(lines):
                if re.search(wf_pattern, ln):
                    # 检查该工作流标题后续80行内是否有脚本调用
                    window = '\n'.join(lines[i:min(i+80, len(lines))])
                    if not any(re.search(p, window) for p in script_call_patterns):
                        # 再检查是否有AI自检清单
                        if any(re.search(p, window) for p in ai_check_patterns):
                            workflow_consistent = False
                            inconsistent_workflows.append(wf)
                    break
        if workflow_consistent:
            d2_pass = True
            d2_evidence = f"{len(unique_workflows)}个工作流，防误标准一致（均有脚本拦截或均无终检）"
        else:
            d2_pass = False
            d2_evidence = f"⚠️ 工作流防误标准不一致：{','.join(inconsistent_workflows)} 仅有AI自检无脚本拦截——同一Skill内两套标准"
    else:
        d2_pass = True   # pass保留兼容，na=True不计入分母（v3.42.0）
        d2_na = True
        d2_evidence = "单工作流Skill（此项na·不计入分母·v3.42.0改判）"
    detail['D2_workflow_consistency'] = {'pass': d2_pass, 'na': d2_na, 'evidence': d2_evidence}

    # ── D3: AI校验伪装脚本拦截 ──
    # 搜索"自动校验/机械验证/脚本检查"声明
    auto_verify_patterns = [
        r'自动校验', r'机械验证', r'脚本检查', r'自动检查',
        r'自动验证', r'确定性校验', r'机械校验',
    ]
    has_auto_verify_decl = any(re.search(p, content) for p in auto_verify_patterns)

    d3_na = False
    if has_auto_verify_decl and not has_script_call:
        d3_pass = False
        d3_evidence = "⚠️ 声明'自动校验/机械验证'但无实际脚本调用——AI层校验伪装成脚本物理拦截"
    else:
        d3_pass = True
        d3_na = not has_auto_verify_decl   # 无声明=na不计入分母；有声明且有脚本=真通过（v3.42.0）
        d3_evidence = "无AI校验伪装脚本拦截问题" if has_auto_verify_decl else "无'自动校验'声明（此项na·不计入分母·v3.42.0改判）"
    detail['D3_ai_check_disguised'] = {'pass': d3_pass, 'na': d3_na, 'evidence': d3_evidence}

    # ── D4: 文本门禁当物理约束 ──
    # 搜索"中止输出/不能输出/禁止交付/无法封口"等强门禁声明
    text_gate_patterns = [
        r'中止输出', r'不能输出', r'禁止交付', r'无法封口',
        r'不允许交付', r'必须修正后', r'不通过则', r'阻断交付',
    ]
    has_text_gate = any(re.search(p, content) for p in text_gate_patterns)

    d4_na = False
    if has_text_gate and not has_script_call:
        d4_pass = False
        d4_evidence = "⚠️ 声明'中止输出/禁止交付'等强门禁但无脚本exit code物理拦截——文本门禁当物理约束，可被AI跳过"
    else:
        d4_pass = True
        d4_na = not has_text_gate   # 无声明=na不计入分母；有声明且有脚本=真通过（v3.42.0）
        d4_evidence = "无文本门禁当物理约束问题" if has_text_gate else "无强门禁声明（此项na·不计入分母·v3.42.0改判）"
    detail['D4_text_gate_as_physical'] = {'pass': d4_pass, 'na': d4_na, 'evidence': d4_evidence}

    # ── D5: 门禁vs建议 ──
    # 只检测明确的强门禁位置（终检/前置条件检查/必须全部/中止输出/不能输出）附近
    # 是否出现"建议/可选/推荐"等建议性措辞——排除正常的"下一步建议/伙伴建议/建议落点"
    strong_gate_patterns = [
        r'终检清单', r'终检锁', r'前置条件检查', r'必须全部.*才能',
        r'中止输出', r'不能输出', r'禁止交付', r'不通过则',
        r'验证失败处理.*中止', r'缺一则', r'不允许交付',
    ]
    recommendation_patterns = [r'建议', r'可选', r'推荐', r'可以选择', r'视情况']
    # 排除正常建议内容的关键词
    exclude_patterns = [r'下一步建议', r'伙伴建议', r'建议落点', r'反哺建议', r'改进建议']
    d5_issues = []
    for i, ln in enumerate(lines):
        if any(re.search(p, ln) for p in strong_gate_patterns):
            # 检查该行及后续5行是否有建议性措辞
            window = '\n'.join(lines[i:min(i+6, len(lines))])
            for rp in recommendation_patterns:
                if re.search(rp, window):
                    # 排除正常建议内容
                    if any(re.search(ep, window) for ep in exclude_patterns):
                        continue
                    d5_issues.append(f"行{i+1}: '{ln.strip()[:60]}' 附近含'{rp}'")
                    break

    if d5_issues:
        d5_pass = False
        d5_evidence = f"⚠️ 门禁位置出现建议性措辞（{len(d5_issues)}处）：{'; '.join(d5_issues[:3])}"
    else:
        d5_pass = True
        d5_evidence = "无门禁vs建议混淆问题"
    detail['D5_gate_vs_recommendation'] = {'pass': d5_pass, 'na': False, 'evidence': d5_evidence}

    # ── 综合达成率（v3.42.0 na改判+回退判据·治"5分照拿"）──
    # D1-D4是流程型深度主体；主体有适用项→适用项+D5等权（流程型行为与旧版一致）
    main_checks = [(d1_pass, d1_na), (d2_pass, d2_na), (d3_pass, d3_na), (d4_pass, d4_na)]
    main_applicable = [p for p, na in main_checks if not na]
    if main_applicable:
        applicable = main_applicable + [d5_pass]
        depth_r = sum(1 for p in applicable if p) / len(applicable)
        detail['_scoring'] = {
            'mode': 'applicable',
            'applicable_count': len(applicable),
            'passed': sum(1 for p in applicable if p),
            'na_items': [k for k, v in detail.items() if isinstance(v, dict) and v.get('na')],
        }
    else:
        # D1-D4全na（非流程型）：回退产出物锁📦密度判据
        # 复用§4.1 deliverable_definition判据（min(计数/5,1.0)）——⛔不新建维度、权重不动
        pkg_count = len(re.findall(r'产出物|📦|deliverable|产出', content))
        depth_r = min(pkg_count / 5, 1.0)
        detail['_scoring'] = {
            'mode': 'all_na_fallback',
            'pkg_count': pkg_count,
            'evidence': f"D1-D4全na（非流程型）→回退产出物锁📦密度（{pkg_count}个/5封顶·复用§4.1判据·evidence=present非na）",
        }
        if pkg_count == 0:
            # 不可能静默（C-090）：真裸奔显式拦截
            detail['D6_fallback_intercept'] = {
                'pass': False, 'na': False,
                'evidence': "⚠️ 深度维度D1-D4全不适用且产出物锁📦=0——真裸奔拦截（不可能静默·C-090零检出盲区根治：扩检测域且缺📦强制显式警告）",
            }

    return depth_r, detail


# ── v2.9.0: Poka-Yoke 三法关键词（模块级·eval_poka_methods 与 eval_layering 共用）──
# 与上方 eval_poka_yoke 内部关键词集保持一致（同步维护，避免漂移）
POKA_CONTACT_KW = r'锚点|接触法|接触式|物理锚点|物理特征|必填字段|字段锁|原话|引用用户|格式校验|格式不符|模板必填|边界约束'
POKA_FIXED_KW   = r'定值法|定值|固定数量|数量锁|数量固定|N个|要素锁|退回补全|上限|下限|固定值'
POKA_MOTION_KW  = r'步序法|步序式|步骤间|动作步序|状态机|产出物锁|上步校验|阻断条件|阻断|强依赖|未完成则|不可执行|回到步骤'
POKA_METHOD_NAMES = [
    (r'接触法|接触式|contact', POKA_CONTACT_KW),
    (r'定值法|定值|fixed-value|固定值', POKA_FIXED_KW),
    (r'步序法|步序式|motion-step|动作步序', POKA_MOTION_KW),
]

def eval_poka_methods(content):
    """返回 Poka-Yoke 三法各自达成率 (contact_r, fixed_r, motion_r)。
    0.0 = 该法无任何关键词命中（即该法缺失）。供 eval_layering 判定 L3「三法全有」。
    评分逻辑与 eval_poka_yoke 内部 eval_one_method 完全一致。"""
    lines = content.splitlines()
    def _one(name_pat, kw_pat):
        count = len(re.findall(kw_pat, content))
        if count == 0:
            return 0.0
        name_re = re.compile(name_pat, re.I)
        title_indices = []
        for i, ln in enumerate(lines):
            stripped = ln.strip()
            if name_re.search(stripped) and (stripped.startswith('#') or
                    stripped.startswith('-') or stripped.startswith('|') or
                    stripped.startswith('*')):
                title_indices.append(i)
        has_struct = False
        if title_indices:
            for ti in title_indices:
                subsequent = 0
                for j in range(ti + 1, min(ti + 10, len(lines))):
                    nxt = lines[j].strip()
                    if not nxt:
                        continue
                    if any(re.search(p, nxt, re.I) for p, _ in POKA_METHOD_NAMES if p != name_pat):
                        break
                    subsequent += 1
                if subsequent >= 2:
                    has_struct = True
                    break
        unique_matches = set(re.findall(kw_pat, content))
        diversity = len(unique_matches)
        if count >= 2 and has_struct:
            return 1.0
        elif diversity >= 5:
            return 0.8
        elif count >= 2:
            return 0.5
        elif count >= 1 and has_struct:
            return 0.9
        else:
            return 0.3
    return (_one(*POKA_METHOD_NAMES[0]), _one(*POKA_METHOD_NAMES[1]), _one(*POKA_METHOD_NAMES[2]))

def eval_trigger_conditions(content):
    """标准§7.1 触发条件段"""
    ratio = 0.0
    if re.search(r'触发词|触发条件|应该触发|不应该触发', content): ratio += 0.7
    triggers = re.findall(r'["\']([^"\']{2,20})["\']', content)
    if len(triggers) >= 3: ratio += 0.3
    return min(ratio, 1.0)

# ── v2.9.0: L1/L2/L3 分层 D5 行数阈值（规范§2.3 v5.15）─────────────
# v2.9.4: 密度系数加权——密度≥0.90则安全线上浮25%，≥0.85上浮15%，<0.80不调整
# 键=层级，值为 [(安全上限,分),(警告上限,分),(危险上限,分)]；超过危险上限=0分(不可接受)
# v3.0.0: 删除 ENGINE_ROLES 豁免机制——评估器不应给自己开后门（双盲审计B5-2修复）
LAYER_LINE_THRESHOLDS = {
    'L1': [(600, 1.0), (800, 0.8), (1000, 0.5)],
    'L2': [(500, 1.0), (700, 0.8), (900, 0.5)],
    'L3': [(400, 1.0), (600, 0.8), (800, 0.5)],
}


def _calc_density_coefficient(filepath, total_lines):
    """计算内容密度系数（v2.9.4新增）。

    装饰行定义：纯空行、纯分隔线(---)、仅含>开头的装饰性blockquote。
    密度系数 = 1 - (装饰行 / 总行数)。
    返回 (density_coeff, decoration_ratio)。
    """
    if total_lines == 0:
        return 1.0, 0.0
    decor_count = 0
    # 装饰行：纯分隔线(---)、单行>开头的blockquote归属行
    decor_pat = re.compile(r'^\s*---\s*$|^\s*>\s')
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if decor_pat.match(line):
                decor_count += 1
    ratio = decor_count / total_lines
    coeff = 1.0 - ratio
    return coeff, ratio


def _density_multiplier(density_coeff):
    """密度系数 → 安全线上浮倍率。

    ≥0.90 → ×1.25  /  ≥0.85 → ×1.15  /  ≥0.80 → ×1.05  /  <0.80 → ×1.00
    """
    if density_coeff >= 0.90:
        return 1.25
    if density_coeff >= 0.85:
        return 1.15
    if density_coeff >= 0.80:
        return 1.05
    return 1.00


# ── v3.0.0: ENGINE_ROLES 豰免机制已删除（双盲审计B5-2修复）─────────
# 评估器不应给自己开后门——所有Skill同一标准，行数超标按L1/L2/L3阈值诚实扣分
# _extract_role 保留用于信息展示，不再影响评分

def _extract_role(frontmatter_text):
    """从 YAML frontmatter 提取 role 字段，默认 leaf。仅信息展示用，不影响评分。"""
    m = re.search(r'^\s*role\s*:\s*([A-Za-z_]+)\s*$', frontmatter_text, re.MULTILINE)
    return (m.group(1).strip().lower() if m else 'leaf')


def eval_token_budget(filepath, layer='L3', role='leaf'):
    """标准§2 D5 行数预算（v5.15按L1/L2/L3分层分级，v2.9.4密度系数加权）。

    密度系数 = 1 - 装饰行占比。密度≥0.90时安全线上浮25%（L3 400→500）。
    实现规范精神：不以行数一刀切判断质量，有效密度高的Skill获得合理空间。

    v3.0.0: 删除 ENGINE_ROLES 豰免——所有Skill同一标准，行数超标诚实扣分。
    role 参数保留向后兼容，但不再影响评分。

    返回 (ratio[0,1], lines, band) —— band∈{安全/警告/危险/不可接受}。
    layer 由 eval_layering 推断；缺省L3（最严，向后兼容旧调用）。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)
    except Exception as e:
        print(f'⚠️ eval_token_budget: 文件读取失败 {e}', file=sys.stderr)
        return 0.0, 0, layer

    thresholds = LAYER_LINE_THRESHOLDS.get(layer, LAYER_LINE_THRESHOLDS['L3'])
    safe, warn, danger = thresholds

    # 密度系数校准安全线
    density_coeff, decor_ratio = _calc_density_coefficient(filepath, lines)
    multiplier = _density_multiplier(density_coeff)
    adjusted_safe = int(safe[0] * multiplier)

    if lines <= adjusted_safe:
        return 1.0, lines, '安全'
    if lines <= warn[0]:
        return 0.8, lines, '警告'
    if lines <= danger[0]:
        return 0.5, lines, '危险'
    return 0.0, lines, '不可接受'

def eval_position_risk(content):
    """指令§8.2 关键指令前置（前50行含铁律/路径/CRITICAL/⛔）"""
    first_50 = '\n'.join(content.splitlines()[:50])
    return 1.0 if re.search(r'路径|铁律|CRITICAL|⛔', first_50) else 0.0

def _check_eval_set_count(main_content, refs_dir):
    """检查1：用例数一致——SKILL.md声明的eval-set用例数 vs eval-set.md实际（P1拆分·v4.8.1）"""
    declared_counts = [int(x) for x in re.findall(r'(\d+)\s*条(?:用例|测试用例|case)', main_content)]
    declared_counts += [int(x) for x in re.findall(r'(?:应触发|不应触发|运行时行为)\s*(\d+)\s*例', main_content)]
    eval_set_path = os.path.join(refs_dir, 'eval-set.md')
    head_declared = None
    actual_rows = 0
    mismatch = None
    compared = False
    if os.path.isfile(eval_set_path) and declared_counts:
        with open(eval_set_path, 'r', encoding='utf-8') as f:
            eval_content = f.read()
        head_declared = re.search(r'用例(?:总数|计数).*?[:：]\s*(\d+)\s*条', eval_content)
        actual_cands = {_evalset_rows(eval_content), _count_evalset(eval_content)}  # v4.12.2·R2-N-06：行数/条目数双口径并列（68vs34歧义根治）
        actual_rows = _evalset_rows(eval_content)  # v4.12.1·E-2第四形态：迁移唯一实现——旧内联正则对T编号表恒0行=漂移检测静默失效（v4.9.5承诺"收口全部调用点"实漏本处·CHANGELOG反例）
        compared = head_declared is not None or actual_rows > 0
        # v4.12.1 E-2根治（第四形态：同名声明多处重复被求和=34+34→68≠实34 假阳性；旧注释"单值声明sum不受影响"被复现证伪）：
        # 自洽不变式=「单值之一==实盘 或 分段求和==实盘」任一成立（与 _declared_evalset_count 的 v4.9.5 不变式同构·口径统一）
        ok_vals = set(declared_counts) | {sum(declared_counts)}
        if head_declared and int(head_declared.group(1)) not in ok_vals:
            mismatch = (
                f'SKILL.md声明{sorted(ok_vals)}条用例，与eval-set.md头部声明{head_declared.group(1)}条均不自洽'
            )
        elif actual_cands and not (ok_vals & actual_cands):
            mismatch = (
                f'SKILL.md声明{sorted(ok_vals)}条用例，与eval-set.md实盘口径{sorted(actual_cands)}均不自洽'
            )
    return {
        'name': 'eval_set_count',
        'passed': mismatch is None,
        'increment': mismatch is None and compared,  # 三态：只有真正比对了才计通过（没查≠查了没事）
        'mismatch': mismatch,
        'detail': mismatch or ('用例数声明与实际一致' if compared else 'na:未声明或不可查（不视为通过）'),
    }


def _check_signature_format(main_content, refs_dir):
    """检查2：签名格式一致——SKILL.md声明的签名格式 vs signature.md示例（P1拆分·v4.8.1）"""
    sig_mismatch = None
    sig_path = os.path.join(refs_dir, 'shared', 'signature.md')
    if not os.path.isfile(sig_path):
        sig_path = os.path.join(refs_dir, 'signature.md')
    if os.path.isfile(sig_path):
        with open(sig_path, 'r', encoding='utf-8') as f:
            sig_content = f.read()
        sig_examples = re.findall(r'`\[🧠[^`]+\]`', sig_content)
        skill_sig_formats = re.findall(r'格式[：:]\s*`\[🧠[^`]+\]`', main_content)
        if sig_examples and skill_sig_formats:
            # 归一化比较：去掉具体内容，只比结构（L1/L2/L3标识 + 分隔符数量）
            def normalize_sig(s):
                level = re.search(r'L[123]', s)
                bars = s.count('|')
                has_date = bool(re.search(r'\d{4}-\d{2}-\d{2}|日期', s))
                return (level.group(0) if level else '?', bars, has_date)
            sig_norms = set(normalize_sig(s) for s in sig_examples)
            skill_norms = set(normalize_sig(s.split('`')[1] if '`' in s else s)
                             for s in skill_sig_formats)
            for sn in skill_norms:
                if sn not in sig_norms:
                    sig_mismatch = (
                        f'SKILL.md签名格式{sn}在signature.md中无对应示例'
                    )
                    break
    return {
        'name': 'signature_format',
        'passed': sig_mismatch is None,
        'increment': sig_mismatch is None,
        'mismatch': sig_mismatch,
        'detail': sig_mismatch or '签名格式声明与示例一致',
    }


def _check_license_consistency(main_content):
    """检查3：License一致——YAML license字段 vs 文末协议声明（P1拆分·v4.8.1）"""
    lic_mismatch = None
    yaml_lic = re.search(r'^license\s*:\s*["\']?(\w+)["\']?', main_content, re.MULTILINE)
    last_lines = '\n'.join(main_content.splitlines()[-20:])
    tail_lic = re.search(r'(?:开源协议|协议|License)[：:]\s*(MIT|Proprietary|Apache[\s-]+2\.0|GPL)', last_lines, re.IGNORECASE)
    if yaml_lic and tail_lic:
        yaml_l = yaml_lic.group(1).lower()
        tail_l = tail_lic.group(1).lower().replace(' ', '-')
        lic_map = {'apache-2.0': 'apache', 'apache2.0': 'apache'}
        yaml_l = lic_map.get(yaml_l, yaml_l)
        tail_l = lic_map.get(tail_l, tail_l)
        if yaml_l != tail_l:
            lic_mismatch = (
                f'YAML license={yaml_lic.group(1)} vs 文末协议={tail_lic.group(1)}'
            )
    return {
        'name': 'license_consistency',
        'passed': lic_mismatch is None,
        'increment': lic_mismatch is None,
        'mismatch': lic_mismatch,
        'detail': lic_mismatch or 'License声明一致',
    }


def _check_indexed_files_exist(main_content, refs_dir):
    """检查4：索引表引用文件存在性——SKILL.md引用的references文件均存在（P1拆分·v4.8.1）"""
    missing_refs = []
    # 严格匹配：references/xxx.md 或 references/xxx/yyy.md
    # 要求 references/ 前必须是非单词字符或行首（避免匹配"下文件是否被SKILL.md引用"等描述）
    # 且 .md 后必须是行尾/标点/空格/反引号（避免匹配到自然语言句子片段）
    ref_pattern = re.compile(
        r'(?:^|[^\w/])references/([\w-]+(?:/[\w-]+)?\.md)(?=[\s`\)|,，。；;\n]|$)',
        re.MULTILINE
    )
    seen = set()
    for m in ref_pattern.finditer(main_content):
        ref_name = m.group(1).split('/')[-1]  # 取文件名部分
        if ref_name in seen:
            continue
        seen.add(ref_name)
        found = False
        for root, _, files in os.walk(refs_dir):
            if ref_name in files:
                found = True
                break
        if not found:
            missing_refs.append(ref_name)
    return {
        'name': 'indexed_files_exist',
        'passed': not missing_refs,
        'increment': not missing_refs,
        'mismatch': f'索引表引用的文件不存在: {missing_refs}' if missing_refs else None,
        'detail': f'缺失文件: {missing_refs}' if missing_refs else '索引表引用文件均存在',
    }


def _check_step_count_consistency(refs_dir, ref_files):
    """检查5：关键数字交叉比对——references文件头部声明的步数 vs 实际Step标题数（P1拆分·v4.8.1）"""
    step_mismatch = None
    warnings = []
    for ref_fname in ref_files:
        ref_fpath = os.path.join(refs_dir, ref_fname)
        try:
            with open(ref_fpath, 'r', encoding='utf-8') as f:
                ref_content = f.read()
        except Exception as e:
            warnings.append(f'读取{ref_fname}失败: {e}')
            continue
        head_step = re.search(r'步骤[：:][^\n]*?(\d+)\s*步', ref_content)
        actual_steps = len(re.findall(r'^##\s*Step\d+', ref_content, re.MULTILINE))
        if head_step and actual_steps > 0:
            declared = int(head_step.group(1))
            if declared != actual_steps:
                step_mismatch = (
                    f'{ref_fname}: 头部声明{declared}步，实际{actual_steps}个Step标题'
                )
                break
    return {
        'name': 'step_count_consistency',
        'passed': step_mismatch is None,
        'increment': step_mismatch is None,
        'mismatch': step_mismatch,
        'detail': step_mismatch or '步数声明与实际一致',
        'warnings': warnings,
    }


def _check_refs_index_section(main_content, refs_dir):
    """检查6：references 索引段结构强制（v4.9.0 L1候选1·L3沉淀2026-09-11模式C落地）。

    背景: eval_file_clutter 未登记检查用全文反引号宽松Union——登记散落正文各处仍通过，
    无专用索引段=结构不可审查；eval-set.md 存在但 SKILL.md 无用例数声明→_check_eval_set_count
    中性放行（na）。设计端强制"专用索引段收敛登记+段内声明 eval-set 用例数"。

    检查项（references/ 有顶层 .md 时强制·无则 na 中性）:
      1. 索引段存在: SKILL.md 须有专用索引段（标题行含 references 且含 索引/目录）
      2. 登记完整性: 索引段内反引号登记文件名 ⊇ references/ 顶层 .md 实存
         （子目录由目录级登记项覆盖·与 eval_file_clutter 同口径）
      3. eval-set 用例数声明: references/eval-set.md 存在时，索引段内须声明用例数
    """
    mismatches = []
    checked = 0

    top_mds = []
    if os.path.isdir(refs_dir):
        try:
            top_mds = sorted(f for f in os.listdir(refs_dir)
                             if f.endswith('.md')
                             and os.path.isfile(os.path.join(refs_dir, f)))
        except OSError:
            pass
    has_eval_set = os.path.isfile(os.path.join(refs_dir, 'eval-set.md'))

    if not top_mds:
        return {
            'name': 'refs_index_section',
            'passed': True,
            'increment': False,
            'mismatch': None,
            'detail': 'na:references/无顶层.md（索引段非必需）',
        }

    # 1. 索引段存在性
    sec_match = re.search(
        r'^#{1,4}\s*[^\n]*references[^\n]*(?:索引|目录)[^\n]*$',
        main_content, re.MULTILINE)
    if not sec_match:
        mismatches.append('SKILL.md 缺专用 references 索引段（标题须含 references 与 索引/目录 关键词）')
    else:
        checked += 1

    sec_text = ''
    if sec_match:
        start = sec_match.end()
        next_head = re.search(r'^#{1,4}\s', main_content[start:], re.MULTILINE)
        end = start + (next_head.start() if next_head else len(main_content))
        sec_text = main_content[start:end]

        # 2. 登记完整性（索引段内反引号 token 的 basename）
        registered = set()
        for tok in re.findall(r'`([^`\n]+)`', sec_text):
            tok = tok.strip()
            if tok.endswith('.md'):
                registered.add(os.path.basename(tok))
        missing = [f for f in top_mds if f not in registered]
        if missing:
            mismatches.append(f'references/ 顶层 .md 未在索引段登记: {missing}')
        else:
            checked += 1

        # 3. eval-set 用例数声明
        if has_eval_set:
            declared = (re.search(r'用例(?:数|总数)[^\d\n]*(\d+)', sec_text, re.IGNORECASE)
                        or re.search(r'(\d+)\s*条\s*(?:用例|测试用例|case)', sec_text, re.IGNORECASE))
            if declared:
                checked += 1
            else:
                mismatches.append('references/eval-set.md 存在但索引段未声明用例数（N条用例）')
        else:
            checked += 1  # 无 eval-set.md——声明项非必需

    mismatch_str = '；'.join(mismatches) if mismatches else None
    return {
        'name': 'refs_index_section',
        'passed': mismatch_str is None,
        'increment': mismatch_str is None and checked > 0,
        'mismatch': mismatch_str,
        'detail': mismatch_str or ('索引段结构合规（%d/3子查通过）' % checked),
    }


def eval_cross_file_consistency(skill_path):
    """标准§2 跨文件声明-执行一致性（v2.8.4重写·E5/E6反模式确定性检测）。

    检查SKILL.md中的声明性数字/格式与references文件实际内容是否一致。
    覆盖反模式：
      - E5声明-执行gap：声明了但实际没做到（如声明18条用例实际只有16条）
      - E6声明滞后gap：执行改了但声明没跟（如步数已改但索引表仍写旧数字）

    检查项：
      1. 用例数一致：SKILL.md声明的eval-set用例数 vs eval-set.md实际用例数
      2. 签名格式一致：SKILL.md声明的签名格式 vs signature.md示例格式
      3. License一致：YAML license字段 vs 文末协议声明
      4. 索引表文件存在性：SKILL.md索引表引用的references文件均存在
      5. 关键数字交叉比对：SKILL.md中声明的步数/检查点编号在references中有对应
      6. references索引段结构强制（v4.9.0）：专用索引段+段内登记完整性+eval-set用例数声明

    返回 (ratio[0,1], detail)
    """
    skill_dir = os.path.dirname(skill_path)
    refs_dir = os.path.join(skill_dir, 'references')

    detail = {
        'checks': [],
        'mismatches': [],
        'ref_count': 0,
    }

    if not os.path.isdir(refs_dir):
        return 1.0, detail  # 无references目录，不需要检查

    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            main_content = f.read()
    except Exception as e:
        detail['warning'] = f'SKILL.md读取失败，降级评分: {e}'
        return 0.4, detail

    ref_files = [f for f in os.listdir(refs_dir) if f.endswith('.md')]
    detail['ref_count'] = len(ref_files)

    checks_passed = 0
    checks_total = 0

    # v4.8.1 P1拆分：5个检查项独立成函数（内聚度可独立命名/改动频次高/共享状态仅main_content+refs_dir）
    # v4.9.0 新增第6项 _check_refs_index_section（L1候选1·索引段结构强制）
    checks = [
        _check_eval_set_count(main_content, refs_dir),
        _check_signature_format(main_content, refs_dir),
        _check_license_consistency(main_content),
        _check_indexed_files_exist(main_content, refs_dir),
        _check_step_count_consistency(refs_dir, ref_files),
        _check_refs_index_section(main_content, refs_dir),
    ]
    for c in checks:
        checks_total += 1
        if c.get('warnings'):
            detail.setdefault('warnings', []).extend(c['warnings'])
        if c['mismatch']:
            detail['mismatches'].append(c['mismatch'])
        elif c['increment']:
            checks_passed += 1
        detail['checks'].append({
            'name': c['name'],
            'passed': c['passed'],
            'detail': c['detail'],
        })

    ratio = checks_passed / checks_total if checks_total > 0 else 1.0
    return ratio, detail

def eval_single_number_source(content):
    """验证⑩ 单一数字源（v2.8.5新增·同一概念计数全文档一致性检测）。

    检查SKILL.md中同一概念在多处声明的数字是否一致。
    覆盖反模式：声明同一概念时不同位置写不同数字（如L3步数三处不一致：11步/11步+1子目标/10步）。

    检查项（按概念分组）：
      1. 用例数一致性：所有"N条用例"声明中N值一致
      2. G系列编号连续性：G编号集合无跳号
      3. 同段落内步数一致性：同一流程/层级内的步数声明一致

    返回 (ratio[0,1], detail)
    """
    detail = {
        'checks': [],
        'mismatches': [],
    }

    checks_passed = 0
    checks_total = 0

    # ── 检查1：用例数一致性 ──
    # 用例数是全局概念，应该全文档一致
    checks_total += 1
    eval_count_matches = re.findall(r'(\d+)\s*条\s*(?:测试)?用例', content)
    if eval_count_matches:
        unique_nums = set(int(n) for n in eval_count_matches)
        if len(unique_nums) > 1:
            mismatch = f'用例数声明不一致：{list(eval_count_matches)} → 唯一值{unique_nums}'
            detail['mismatches'].append(mismatch)
            detail['checks'].append({
                'name': 'concept_eval_count',
                'passed': False,
                'detail': mismatch
            })
        else:
            checks_passed += 1
            detail['checks'].append({
                'name': 'concept_eval_count',
                'passed': True,
                'detail': f'用例数声明一致：{list(eval_count_matches)}'
            })
    else:
        checks_total -= 1  # 未声明，不计入

    # ── 检查2：G系列编号连续性（v2.9.10·退役白名单 + v4.12.5 外部引用豁免）──
    # 提取所有G编号（G1, G2, G3...），检查是否连续无跳号。
    # ⛔ v2.9.10 修复：缺失编号若在文档中显式声明"退役/编号保留不重用"（如 triwich 的
    # "G3已被Agent B Step3替代，编号保留不重用"），则不计为跳号——编号是标识符不是计数，
    # 标识符允许退役，计数不允许有洞。旧实现把"正确退役"读成"跳号"=评分器假阳性，
    # 且制造反向激励（补全更高编号提及反而扣分，删掉提及反而加分）。见 triwich v3.11.0 L3冒烟。
    # v4.12.5 修复：外部引用豁免——当文档显式声明 G 编号来自外部体系（如"引用非本Skill
    # 编号体系"、"童灵零问题门禁集"）时，G编号不是本Skill的序列，连续性检查不适用。
    # 根因：growth-box SKILL.md 引用童灵门禁集 G2/G11/G17，评估器当成本Skill G系列全集→误报跳号。
    checks_total += 1
    # 先检查外部引用豁免信号
    EXTERNAL_REF_PATTERNS = [
        r'引用非本Skill编号体系',
        r'外部.*(?:编号|G系列)',
        r'童灵.*门禁集',
        r'数字分身.*门禁',
    ]
    has_external_ref = any(re.search(p, content, re.IGNORECASE) for p in EXTERNAL_REF_PATTERNS)
    g_nums = [int(m) for m in re.findall(r'\bG(\d+)\b', content)]
    if g_nums:
        if has_external_ref:
            # 外部引用豁免：G编号来自外部体系，连续性检查不适用
            checks_total -= 1  # 不计入分母
            detail['checks'].append({
                'name': 'g_series_continuous',
                'passed': True,
                'na': True,
                'detail': f'G系列编号外部引用豁免（检测到外部体系声明·{len(g_nums)}个G编号不参与连续性检查）'
            })
        else:
            unique_g = sorted(set(g_nums))
            expected = list(range(1, max(unique_g) + 1))
            missing = [g for g in expected if g not in unique_g]
            if missing:
                # ── 退役豁免：检查缺失编号是否有显式退役声明 ──
                # 退役声明特征：缺失编号 G{n} 的同一句/相邻120字符内出现退役关键词
                RETIRE_PATTERNS = [
                    r'G{n}\s*(?:编号)?\s*(?:保留)?不重用',
                    r'G{n}\s*(?:编号)?\s*已被.{0,24}(?:替代|取代)',
                    r'G{n}\s*(?:编号)?\s*(?:退役|废弃|弃用|不再使用|removed|retired|deprecated)',
                ]
                retired = []
                for g in missing:
                    is_retired = any(
                        re.search(p.replace('{n}', str(g)), content, re.IGNORECASE)
                        for p in RETIRE_PATTERNS
                    )
                    if is_retired:
                        retired.append(g)
                # 剔除已退役编号后，剩余缺失才是真跳号
                real_missing = [g for g in missing if g not in retired]
                detail['checks'].append({
                    'name': 'g_series_continuous',
                    'passed': not real_missing,
                    'detail': (f'G系列编号连续（缺失{missing}中退役豁免{retired}）'
                               if retired and not real_missing
                               else f'G系列编号跳号：缺失G{real_missing}（存在{unique_g}；退役豁免{retired}）'),
                })
                if real_missing:
                    mismatch = f'G系列编号跳号：缺失G{real_missing}（存在{unique_g}）'
                    detail['mismatches'].append(mismatch)
                else:
                    checks_passed += 1
            else:
                checks_passed += 1
                detail['checks'].append({
                    'name': 'g_series_continuous',
                    'passed': True,
                    'detail': f'G系列编号连续：G1-G{max(unique_g)}'
                })
    else:
        checks_total -= 1  # 无G编号，不计入

    # ── 检查3：同路径内步数一致性 ──
    # 检查同一路径/子流程的步数声明是否一致
    # 分组键："L1-第一性原理" / "L1-抽象建模" / "L1-批判验证" / "L2" / "L3" / "Phase X" 等
    # 只在同一行内匹配路径标识+步数，避免表格中相邻行串扰
    checks_total += 1
    step_mismatch = None
    lines = content.splitlines()
    path_steps = {}  # {path_name: [step_counts]}
    for line in lines:
        # 优先匹配细粒度路径标识
        path_match = re.search(
            r'\b(L1[-—](?:第一性原理|抽象建模|批判验证)|L3[-—](?:全流程|深度模式)?|L[123](?![-—])|Phase\s*[A-Za-z])\b',
            line
        )
        if not path_match:
            continue
        path = path_match.group(1)
        # 概念归一化：L3-全流程/L3-深度模式/L3 都归为"L3"组
        # L1-第一性原理/L1-抽象建模/L1-批判验证 保持独立
        if path.startswith('L3'):
            path = 'L3'
        # 只在该行内搜索步数声明（不跨行）
        step_matches = re.findall(r'(\d+)\s*(?:个)?\s*步(?:骤|数)?(?!骤)', line)
        for s in step_matches:
            si = int(s)
            if si > 20 or si < 2:  # 排除明显非步数的数字
                continue
            if path not in path_steps:
                path_steps[path] = []
            path_steps[path].append(si)

    for path, counts in path_steps.items():
        unique = set(counts)
        if len(unique) > 1:
            step_mismatch = f'{path}步数声明不一致：{counts} → 唯一值{unique}'
            break

    if step_mismatch:
        detail['mismatches'].append(step_mismatch)
        detail['checks'].append({
            'name': 'path_step_consistency',
            'passed': False,
            'detail': step_mismatch
        })
    else:
        checks_passed += 1
        if path_steps:
            detail['checks'].append({
                'name': 'path_step_consistency',
                'passed': True,
                'detail': f'各路径步数声明一致：{path_steps}'
            })
        else:
            detail['checks'].append({
                'name': 'path_step_consistency',
                'passed': True,
                'detail': '未检测到多步数声明（无需比对）'
            })

    # v4.12.1·F-STEP盲区补：同一主题词"收尾门禁N步"跨位置计数一致（五步/七步残字冲突曾逃过本检查）
    gate_step_ns = re.findall(r'收尾门禁[^0-9〇一二三四五六七八九十\d]{0,3}([一二三四五六七八九十\d]+)步', content)  # v4.12.3真发（CL-2声明widened实未落=本仓R3-N-02假核销正主·现补）
    checks_total += 1
    if len(set(gate_step_ns)) > 1:
        detail['mismatches'].append(f'收尾门禁步数声明不一致：{gate_step_ns}')
        detail['checks'].append({'name': 'closure_gate_step_consistency', 'passed': False,
                                 'detail': f'不一致：{gate_step_ns}'})
    else:
        checks_passed += 1
        detail['checks'].append({'name': 'closure_gate_step_consistency', 'passed': True,
                                 'detail': f'一致或未声明：{gate_step_ns or "无"}'})

    ratio = checks_passed / checks_total if checks_total > 0 else 1.0
    return ratio, detail

def eval_fuse_mechanism(content):
    """标准§4.3 熔断器格式合规（约束式模板确定性检测 · v2.8.2新增）。

    每个 🔌 熔断器 块必须遵循 §4.3 模板：
      - 字段名一致：成功条件 / 失败处理 / 可修正参数 / 重试次数 / 降级方案
        （别名如"成功标准""失败时"属违规，§4.3明示字段名不可改）
      - 场景必填：外部调用(读文件/调API/跑脚本)→全量五字段；
                   内部校验→简量三字段(成功条件/失败处理/降级方案)
      - 失败处理必须从 [重试 | 跳过 | 中止 | 降级] 四选一
      - 降级方案必须写具体路径/步骤，不可仅写"跳过"/"降级"

    返回 (ratio[0,1], detail)
    """
    # 块隔离（v2.8.2修正）：仅提取每个🔌之后的"字段行区域"，
    # 描述性文字（验证段说明/Phase X步骤/提及🔌的注记）不并入块；
    # 不含字段行的🔌提及（如"扫描每个🔌熔断器块"）不计入熔断器。
    lines_all = content.splitlines()
    anchor_lines = [idx for idx, ln in enumerate(lines_all)
                    if re.search(r'🔌\s*熔断器', ln)]
    if not anchor_lines:
        return 0.0, {'fuse_count': 0,
                     'note': '未发现任何🔌熔断器（§4.3要求外部调用步骤必须设熔断器）'}

    # 外部调用信号（不含裸"脚本"——"脚本缺失"是存在性检查，非外部调用）
    EXTERNAL_SIGNALS = ['读文件', '读取', 'Read', 'Write', 'Edit', '调API', 'API调用',
                        'HTTP', '网络请求', 'curl', 'fetch', '运行脚本', '执行脚本',
                        '跑脚本', '加载', 'spawn', 'Agent', '下载', '上传', '外部系统']
    JUDGE_WORDS = ['重试', '跳过', '中止', '降级']
    VAGUE_FALLBACK = {'跳过', '降级', '降级处理', '走备用路径'}

    # 字段行：容忍树状符 ├─└─│、续行、及 markdown 引用符 `>` 前缀
    # （v2.9.0修复：daily-buddy 等把熔断器写在 `>` 引用块内，旧正则漏匹配→per_fuse为空→除零崩溃）
    field_line_re = re.compile(
        r'^\s*>?\s*[│├└┬─\s]*\s*'
        r'(成功条件|失败处理|可修正参数|重试次数|降级方案)\s*[：:]\s*(.*)$'
    )
    # 别名仅当作为字段名出现（带冒号）才算违规，避免说明文字提及误判
    alias_re = re.compile(r'(成功标准|失败时|失败处理方案|降级策略|备选方案)\s*[：:]')

    per_fuse = []
    for li in anchor_lines:
        # 从该🔌下一行起收集字段行+续行，遇新🔌/非字段行即止
        fields = {}
        i = li + 1
        while i < len(lines_all):
            if '🔌' in lines_all[i]:
                break  # 新熔断器起点
            m = field_line_re.match(lines_all[i])
            if m:
                fname = m.group(1)
                fval = m.group(2).strip()
                j = i + 1
                while j < len(lines_all):
                    nxt = lines_all[j]
                    if '🔌' in nxt or field_line_re.match(nxt):
                        break
                    if nxt.lstrip().startswith('│') or (
                            nxt.startswith(' ') and not nxt.strip().startswith('├')):
                        cont = nxt.lstrip('│ ').strip()
                        if cont:
                            fval += ' ' + cont
                        j += 1
                    else:
                        break
                fields[fname] = fval
                i = j
            else:
                break  # 非字段行 → 该熔断器字段区结束
        if not fields:
            continue  # 仅提及🔌，非真熔断器

        # —— 场景判定 ——
        block_text = ' '.join(fields.values())
        is_external = any(sig.lower() in block_text.lower() for sig in EXTERNAL_SIGNALS)
        required = ['成功条件', '失败处理', '降级方案']
        if is_external:
            required = ['成功条件', '失败处理', '可修正参数', '重试次数', '降级方案']

        present = [f for f in required if f in fields]
        missing = [f for f in required if f not in fields]

        # 失败处理判定词
        failword_ok = bool('失败处理' in fields and
                           any(w in fields['失败处理'] for w in JUDGE_WORDS))

        # 降级方案具体性
        fallback_ok = False
        if '降级方案' in fields:
            fb = fields['降级方案'].rstrip('。').strip()
            if fb not in VAGUE_FALLBACK and len(fb) >= 4:
                fallback_ok = True
            if any(k in fields['降级方案'] for k in
                   ['继续', '步骤', '→', '路径', 'Read', '写', '文件',
                    '跳过本步', '重试', '返回', '日志', '执行']):
                fallback_ok = True

        # 别名（错误字段名）检测——仅查字段值文本
        alias_hits = alias_re.findall(block_text)

        field_ratio = len(present) / len(required)
        struct = (field_ratio * 0.6
                  + (1.0 if failword_ok else 0.0) * 0.2
                  + (1.0 if fallback_ok else 0.0) * 0.2)
        if alias_hits:
            struct *= 0.7  # 字段名违规额外扣分

        per_fuse.append({
            'is_external': is_external,
            'present': present,
            'missing': missing,
            'failword_ok': failword_ok,
            'fallback_ok': fallback_ok,
            'alias_hits': alias_hits,
            'ratio': struct,
        })

    if not per_fuse:
        # 防御：有🔌提及但无任何合规字段块（全是提及/描述行）→ 不崩溃，记0分+说明
        return 0.0, {'fuse_count': 0,
                     'note': '发现🔌熔断器提及但无合规字段块（疑似仅提及/描述，未实装熔断器）',
                     'per_fuse': []}
    overall = sum(f['ratio'] for f in per_fuse) / len(per_fuse)
    # 任一熔断器缺降级方案 → 封顶0.5（§4.3核心字段不可缺）
    if any('降级方案' in f['missing'] for f in per_fuse):
        overall = min(overall, 0.5)

    detail = {
        'fuse_count': len(per_fuse),
        'external_count': sum(1 for f in per_fuse if f['is_external']),
        'per_fuse': per_fuse,
    }
    return overall, detail

def eval_deliverable_definition(content):
    """标准§4.1 产出物定义"""
    return min(len(re.findall(r'产出物|📦|deliverable|产出', content)) / 5, 1.0)

def eval_file_clutter(skill_path):
    """标准§2 文件杂乱 + ⛔无 README.md

    v3.47.0 A17 递归扩展（F6实证：references 下曾出现0字节杂散文件且永不逮·恒报checked-clean）：
    旧逻辑只对顶层目录项做白名单差集，references/ 内部不递归——治了症状（手工清0字节文件）
    病灶在（同类文件再现照样不逮）。现递归 references/ 查两类：
      ①任意深度 0字节文件（杂散文件的最可靠信号）
      ②references/ 顶层 .md 未被 SKILL.md 登记的文件（登记集=SKILL.md全文反引号包裹的
        文件名 ∪ references/xxx 路径引用·宽松Union防误报；子目录文件由目录级登记项覆盖·如 eval-knowledge/）
    """
    skill_dir = os.path.dirname(skill_path) or '.'  # v3.0.1: 修复相对路径空字符串bug
    # 允许的文件/目录（v2.8.6: 从硬编码改为模块级常量，便于扩展）
    allowed = ALLOWED_SKILL_FILES
    try:
        items = set(os.listdir(skill_dir))
    except Exception as e:
        # 异常降级：目录读取失败=无法评估，返回0分（不是满分！）
        # 旧代码返回1.0是方向性错误——读取失败不代表没杂乱文件
        return 0.0, [{'error': f'目录读取失败: {e}'}]
    has_readme = any(i.lower() == 'readme.md' for i in items)
    clutter = {c for c in (items - allowed)
               if not os.path.isdir(os.path.join(skill_dir, c))}
    ratio = 1.0
    detail = list(clutter)
    if has_readme:
        ratio -= 0.5  # 标准§2 ⛔DO NOT 放 README.md
        detail.append('README.md（规范§2 禁止）')
    if clutter - {c for c in clutter if c.lower() == 'readme.md'}:
        ratio -= 0.3
    # ── v3.47.0 A17: 递归 references/ ──
    refs_dir = os.path.join(skill_dir, 'references')
    rec_issues = []
    if os.path.isdir(refs_dir):
        # 登记集：SKILL.md 全文反引号包裹的文件名 + references/ 前缀路径（宽松Union·防误报）
        registered = set()
        try:
            with open(skill_path, encoding='utf-8') as f:
                sk_text = f.read()
            for tok in re.findall(r'`([^`\n]+)`', sk_text):
                tok = tok.strip()
                if tok.endswith(('.md', '.json', '.yaml')):
                    registered.add(os.path.basename(tok))
            registered.update(re.findall(r'references/([\w.\-]+\.(?:md|json|yaml))', sk_text))
        except Exception:
            pass  # SKILL.md读取失败→跳过未登记检查（0字节检查不受影响·不因读失败给满分）
        if not registered and any(f.endswith('.md') for f in os.listdir(refs_dir)):
            # v4.12.2·R2-N-05：registered空集时旧逻辑静默跳过未登记检查=「没查」当「查了没事」→ fail-visible
            rec_issues.append('⚪ SKILL.md反引号登记集为空→未登记检查不可执行（fail-visible·非满分）')
        for root, _dirs, files in os.walk(refs_dir):
            is_top = (root == refs_dir)
            for fn in sorted(files):
                p = os.path.join(root, fn)
                # v4.12.2·R2：.DS_Store 属产物残留不再豁免（分发包带macOS垃圾=残留的一种）
                try:
                    if os.path.getsize(p) == 0:
                        rec_issues.append('references/%s（0字节）' % os.path.relpath(p, refs_dir))
                        continue
                except Exception:
                    continue
                # 未登记检查只查 references/ 顶层 .md（子目录由目录级登记项覆盖）
                if is_top and fn.endswith('.md') and registered and fn not in registered:
                    rec_issues.append('references/%s（未被SKILL.md索引登记）' % fn)
    # v4.12.1·审查F-CLUTTER：本函数旧扫描域=顶层+references/ → scripts/tests 的 .bak*/__pycache__ 盲区
    # （evaluation-framework v2.6.0"产物目录无残留"检查点的评估器自身反面——评别人不查自己=Goodhart）
    # v4.12.3·R3攻5根治：三子目录白名单是点状补丁（steps//根级/references子层逃逸）——改全树walk(.git除外)
    for root4, dirs4, files4 in os.walk(skill_dir):
        dirs4[:] = [x for x in dirs4 if x != '.git']
        rel4 = os.path.relpath(root4, skill_dir)
        if '__pycache__' in dirs4:
            rec_issues.append(f'{os.path.normpath(os.path.join(rel4, "__pycache__"))}（编译缓存·全树）')
        for fn4 in sorted(files4):
            low4 = fn4.lower()
            if '.bak' in low4 or low4.startswith('~$') or fn4 == '.DS_Store':
                rec_issues.append(f'{os.path.normpath(os.path.join(rel4, fn4))}（备份残留/系统垃圾·v4.12.3全树扫描）')
    if rec_issues:
        ratio -= 0.3
        detail.extend(rec_issues)
    return max(ratio, 0.0), detail

def eval_eval_set_gate(skill_path):
    """标准§6.1 评估集门禁(P0)：references/eval-set.md 存在且非空"""
    refs_dir = os.path.join(os.path.dirname(skill_path), 'references')
    candidates = ['eval-set.md', 'eval_set.md', 'evalset.md']
    for name in candidates:
        p = os.path.join(refs_dir, name)
        if os.path.isfile(p):
            try:
                if os.path.getsize(p) > 0:
                    return 1.0, name
            except Exception as e:
                # 文件大小检查失败=无法确认非空，继续检查下一个
                continue
    return 0.0, None

def eval_trigger_coverage(skill_path):
    """标准§6.2 触发测试（v3.30.0新增·互审整改P2-2）：
    tests/trigger-*.md 存在且非空=满分(1.0)；降级 references/eval-set.md 含'应触发'+'不应触发'=半分(0.5)；
    两者皆无=0。——原因是触发行为靠猜=误触发/漏触发无人知，触发测试集是'该触发时触发'的可验证锚点。
    """
    skill_dir = os.path.dirname(skill_path)
    tests_dir = os.path.join(skill_dir, 'tests')
    if os.path.isdir(tests_dir):
        try:
            names = sorted(n for n in os.listdir(tests_dir)
                           if n.startswith('trigger') and n.endswith('.md'))
        except Exception:
            names = []
        for n in names:
            p = os.path.join(tests_dir, n)
            try:
                if os.path.isfile(p) and os.path.getsize(p) > 0:
                    return 1.0, f'tests/{n}'
            except Exception:
                continue
    refs_dir = os.path.join(skill_dir, 'references')
    for name in ('eval-set.md', 'eval_set.md', 'evalset.md'):
        p = os.path.join(refs_dir, name)
        if os.path.isfile(p):
            try:
                with open(p, encoding='utf-8') as _fh:
                    content = _fh.read()
            except Exception:
                continue
            if '应触发' in content and '不应触发' in content:
                return 0.5, f'references/{name}(应触发+不应触发)'
    return 0.0, None

def eval_security_hardcode(content):
    """指令§四/§4.3 无绝对根路径 + 标准§1 description 禁 XML 标签"""
    ratio = 1.0
    violations = []
    # ① 绝对根路径（含具体用户名）——tilde ~/ 安全，只抓 /Users/xxx、C:\Users\xxx
    abs_paths = re.findall(r'/Users/[A-Za-z0-9_.-]+|[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+', content)
    if abs_paths:
        ratio -= 0.6
        violations.append(f'绝对根路径×{len(abs_paths)}（如 {abs_paths[0]}）')
    # ② 密钥/Token 明文
    if re.search(r'(api[_-]?key|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9]{16,}', content, re.I):
        ratio -= 0.4
        violations.append('疑似硬编码密钥/Token')
    # ③ description 含 XML 标签
    frontmatter, _ = split_frontmatter(content)
    desc = extract_description(frontmatter)
    if re.search(r'<[a-zA-Z/][^>]*>', desc):
        ratio -= 0.4
        violations.append('description 含 XML 标签')
    return max(ratio, 0.0), violations

def eval_backup_gate(skill_path):
    """指令§6.6 修改前备份门禁：备份目录存在该Skill的备份文件"""
    skill_name = os.path.basename(os.path.dirname(skill_path))
    if not os.path.isdir(BACKUP_DIR):
        return 0.0, {'skill': skill_name, 'backups': 0, 'note': '备份目录不存在'}
    # v4.18.7 P2改造（B-5 Agent B N7实证：子串匹配让 clock-loop 的
    #   triwich-integration.md_*.bak 在评估 triwich 时顶备份拿满分=盲区）：
    #   归属两级判据——strong=文件名以 `{skill}_`/`{skill}__` 前缀显式归属（P1 新规范形）；
    #   weak=旧平铺形首段(按'_'切)==被评树实存文件名（跨skill同名SKILL.md为已知过渡局限·form字段显数）。
    try:
        names = os.listdir(BACKUP_DIR)
    except Exception as e:
        return 0.0, {'skill': skill_name, 'backups': 0, 'warning': f'备份目录读取失败: {e}'}
    tree_files = set()
    for _r, _d, fs in os.walk(os.path.dirname(skill_path)):
        tree_files.update(fs)
    strong = weak = 0
    for f in names:
        if '.bak' not in f.lower():
            continue
        if f.startswith(skill_name + '_') or f.startswith(skill_name + '__'):
            strong += 1
        elif f.split('_')[0] in tree_files:
            weak += 1
    n = strong + weak
    return (1.0 if n else 0.0), {
        'skill': skill_name, 'backups': n, 'form': f'strong={strong}/weak={weak}'}


# ── 2026-08-10 反哺：声明-事实核对（报告P0#1·同源自欺盲区）──
def eval_declared_existence(skill_path, content):
    """声明-事实核对：文档声称的路径/交付物指向物是否存在（非计分警告）。

    背景：三明智审查报告 P0#1（upstream 指向 NOT EXISTS / CHANGELOG 声称已交付
    实则不存在），评估器只查文档间一致性、不查文档 vs 磁盘现实（同源核对核对不出
    文档与现实的差距）。clock-loop 自身体检证实 path_safety 只抓 /Users/ 硬编码、
    豁免 ~/ 且不查指向物存在性——本条补齐该空白。
    幂等性：路径存在性=文件系统状态，任何时刻查结果一致（标准规范§6.7）。
    非计分：按 §6.7「若评测仅作提醒，降级为非计分警告」，进 warns 不占 WEIGHTS。
    范围：只核 SKILL.md content 内活性声明（YAML upstream/path + 正文 ~/ 引用）；
    references/CHANGELOG.md 等历史文件不在 content 内——历史事实天然豁免。
    返回 dict: {'checked': N, 'missing': [路径...]}
    """
    missing = []
    checked = 0
    paths = set()
    try:
        fm, _ = split_frontmatter(content)
    except Exception:
        fm = ''
    # ① YAML frontmatter: upstream / path / reference 字段值（~ 或 / 开头）
    for m in re.finditer(r'^(?:upstream|path|reference):\s*["\']?(~?/[^\s"\']+)', fm, re.M):
        paths.add(m.group(1))
    # ② 正文中 ~/ 开头的路径引用（反引号/行内引用语境）
    paths.update(re.findall(r'(~/[^\s`"\'（()）【】]+)', content))
    # ③ 过滤模板占位符路径（含 { } 的路径是模板非真实路径，如 {文件名}_{YYMMDD_HHMM}.bak——报告标准:示例/占位降 warning 不报 P0）
    paths = {p for p in paths if '{' not in p and '}' not in p}
    for p in sorted(paths):
        checked += 1
        try:
            if not os.path.exists(os.path.expanduser(p)):
                missing.append(p)
        except Exception:
            continue
    return {'checked': checked, 'missing': missing}


# ── v3.27.0问4物理钩：phasex-verification-details.md 自指sha8校验 ──
def eval_phasex_selfhash(skill_path):
    """Phase X 细则文件的sha8自指hash校验（v3.27.0问4物理钩·治"AI记得读"prompt级假约束）。

    原理：phasex-verification-details.md内含`<!-- self_hash: sha8=XXXXXXXX -->`标记——
    文件内容被修改后sha8跟不上→本函数detect并报FAIL→物理阻断。与report_sha8同原理自举。

    返回 (ok: bool, detail: dict) 。不计入total_score（门禁类非评分项）。
    """
    import hashlib
    skill_dir = os.path.dirname(os.path.abspath(skill_path))
    vx_path = os.path.join(skill_dir, 'references', 'phasex-verification-details.md')
    detail = {'found': False, 'hash_ok': False, 'declared': None, 'computed': None}
    if not os.path.isfile(vx_path):
        return True, detail  # 没有这个文件→跳过（旧版clock-loop或不存在此文件）
    detail['found'] = True
    with open(vx_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 提取声明的sha8
    declared = re.search(r'self_hash:\s*sha8=([a-f0-9]{8})', content)
    if not declared:
        return True, detail  # 文件存在但还没加self_hash→跳过（向后兼容）
    detail['declared'] = declared.group(1)
    # 剔除self_hash行后计算sha8（与填入时的计算逻辑一致）
    body = content.split('---', 2)[2] if content.startswith('---') else content
    body = re.sub(r'<!-- self_hash: sha8=.*?-->', '', body)
    computed = hashlib.sha256(body.encode('utf-8')).hexdigest()[:8]
    detail['computed'] = computed
    detail['hash_ok'] = (computed == declared.group(1))
    return detail['hash_ok'], detail


# ── v3.10.0新增：版本判级合理性粗查（advisory·不计分·人终判） ──────
def eval_version_grading_advisory(skill_path):
    """CHANGELOG最新条目内容 vs 版本增量类型的粗筛。
    依据: references/version-naming-standard.md §四（固化自版本命名规范v2.0）
    - 功能词（新增/新功能/新步骤/新机制/Phase/工作流）但仅Z++ → 疑似判级偏低
    - 仅修复词（修复/修正/补/同步/typo/漂移）但升Y/X → 疑似判级偏高
    产出: advisory字符串 或 None（无异常静默——§7.5静默幂等）。
    ⛔不计入total_score/passed——判级是半语义判断，脚本只粗筛，终判权在人（§6.6评测定位）。
    """
    changelog_path = os.path.join(os.path.dirname(skill_path), 'references', 'CHANGELOG.md')
    if not os.path.isfile(changelog_path):
        return '⚪not-evaluable(version_grading): CHANGELOG.md缺失，判级advisory未能评估（N5三态·"没法查"≠"查了没事"）'
    with open(changelog_path, 'r', encoding='utf-8') as f:
        cl = f.read()
    # 取最新两个版本条目（v3.31.5设计端消除：语义版本取最大·不依赖位置顺序·P8实锤）
    entries = _changelog_semantic_entries(cl)
    if len(entries) < 2:
        return None  # 单条目无增量可比
    v_new, body = entries[0][0], entries[0][2]
    v_old = entries[1][0]
    if v_new <= v_old:
        return None  # 版本不可解析或重复条目（语义排序后理论上不出现）
    z_only = (v_new[0] == v_old[0] and v_new[1] == v_old[1])   # 仅Z++
    y_or_x = not z_only
    feature_words = ('新增', '新功能', '新步骤', '新机制', '新检查', 'Phase', '工作流')
    fix_only_words = ('修复', '修正', '补', '同步', 'typo', '漂移')
    # v4.18.7 P4：否定语境豁免（B-5 N6实证："六工作流功能零变更"命中"工作流"=误报——
    #   advisory 若高频误报即"狼来了"，判级粗筛可信度反噬）。命中词后12字窗口内出现否定形不计。
    _NEG = ('零变更', '无变更', '未变更', '不变更', '零改动', '功能零', '零新增', '无新增', '未新增', '不新增')
    def _hit(w):
        for m in re.finditer(re.escape(w), body):
            if not any(neg in body[m.end():m.end()+12] for neg in _NEG):
                return True
        return False
    has_feature = any(_hit(w) for w in feature_words)
    only_fix = (not has_feature) and any(w in body for w in fix_only_words)
    if z_only and has_feature:
        return (f"疑似判级偏低: v{'.'.join(map(str, v_old))}→v{'.'.join(map(str, v_new))} 仅升Z，"
                f"但CHANGELOG最新条目含功能词——功能级变更应升Y（见references/version-naming-standard.md §二判级红线）")
    if y_or_x and only_fix:
        return (f"疑似判级偏高: v{'.'.join(map(str, v_old))}→v{'.'.join(map(str, v_new))} 升了Y/X，"
                f"但CHANGELOG最新条目仅含修复词——纯修复应只升Z（见references/version-naming-standard.md §三口诀）")
    return None


# ── v3.12.0新增：断言绑实录窄化advisory（QD-014机制化第③层·CHANGELOG场景唯一防线） ──
def eval_removal_advisory(skill_path):
    """数字护栏移除类变更残留扫描提示（L3反哺C-A2·2026-08-12）。

    命中：CHANGELOG 最新条目含移除类词（移除/取消/撤销/删除/废除）+ 上限类词（上限/护栏/数字/分档/硬编码/硬封）。
    提示：✅DO 检查 eval-set/细则文件/论证文字是否残留数字硬判——实证：sucair v4.5.0/v4.5.1 两轮清理漏网
    （eval-set T8"5-8卡" / §2.3"各取1道" / 论证文字"1-3张"）。
    advisory 级不计分——None=无异常（与 assertion_advisory 同族：闹钟响了由 AI 终判）。
    """
    changelog_path = os.path.join(os.path.dirname(skill_path), 'references', 'CHANGELOG.md')
    if not os.path.isfile(changelog_path):
        return None
    try:
        with open(changelog_path, 'r', encoding='utf-8') as f:
            cl_content = f.read()
    except Exception:
        return None
    entries = _changelog_semantic_entries(cl_content)
    if not entries:
        return None
    latest_body = entries[0][2]
    removal_words = ('移除', '取消', '撤销', '删除', '废除')
    limit_words = ('上限', '护栏', '数字', '分档', '硬编码', '硬封')
    if any(w in latest_body for w in removal_words) and any(w in latest_body for w in limit_words):
        return ('数字护栏移除类变更残留扫描提示: CHANGELOG最新条目含移除类+上限类关键词——'
                '✅DO 检查 eval-set/细则文件/论证文字是否残留数字硬判（sucair v4.5.0/v4.5.1 两轮漏网实证·L3反哺C-A2）')
    return None


# ── v4.0.2新增：同类扫描核销 advisory（C05承诺核销制·prose纪律机械化·"修一处必同类扫描"） ──
def eval_similar_scan_advisory(skill_path):
    """修复类 CHANGELOG 条目须附"同类扫描"核销证据（升级期纪律②·2026-09-05你定）。

    背景：#129"挂了挡没接变速箱"——"修一处必同类扫描"原为 prose 纪律（07-21立下被违反≥3次），
    无机械执行＝承诺无核销。核销制：修复类条目（修复/修正/补齐/重建/整改/清理/根治/改造动词）
    若不含同类扫描证据词（同类扫描/同类检查/同族/同型/全库 grep/全量扫描/同类扫描逮住）→ 提示补核销。
    advisory 级不计分——None=无异常（与 eval_removal_advisory 同族：闹钟响了由 AI 终判）。
    """
    changelog_path = os.path.join(os.path.dirname(skill_path), 'references', 'CHANGELOG.md')
    if not os.path.isfile(changelog_path):
        return None
    try:
        with open(changelog_path, 'r', encoding='utf-8') as f:
            cl_content = f.read()
    except Exception:
        return None
    entries = _changelog_semantic_entries(cl_content)
    if not entries:
        return None
    latest_body = entries[0][2]
    fix_words = ('修复', '修正', '补齐', '重建', '整改', '清理', '根治', '改造')
    scan_words = ('同类扫描', '同类检查', '同族', '同型', '全库 grep', '全量扫描', '同类扫描逮住')
    if any(w in latest_body for w in fix_words) and not any(w in latest_body for w in scan_words):
        return ('同类扫描核销提示: CHANGELOG最新条目含修复类动词但无"同类扫描"核销证据——'
                '✅DO 补同类扫描声明（修一处必同类扫描·纪律②·C05承诺核销制）')
    return None


def eval_assertion_advisory(skill_path):
    """CHANGELOG最新条目中的高危数字断言是否绑实录来源。
    依据: 断言绑实录三层方案第③层（三明智L2验证2026-07-27·你终审）——CHANGELOG自由写入
    场景无流程宿主（两步法阻断条件不在场），本advisory是该场景唯一机器防线。
    窄化模式（防误报·只盯实际犯过错的两型）:
    - 行数+档位: "N行"与"档/带/安全线"同条目共现
    - 分数断言: "N/100"
    命中且条目内无来源字样(实测/实录/wc/d5_band/json/skill_eval输出) → advisory提示。
    产出: advisory字符串 或 None——⛔不计分不进passed（§6.6评测边界:数字是否为断言
    是语义判断,脚本只粗筛,终判权在人）。同构先例: eval_version_grading_advisory(v3.10.0)。
    """
    changelog_path = os.path.join(os.path.dirname(skill_path), 'references', 'CHANGELOG.md')
    if not os.path.isfile(changelog_path):
        return '⚪not-evaluable(assertion): CHANGELOG.md缺失，断言advisory未能评估（N5三态）'
    with open(changelog_path, 'r', encoding='utf-8') as f:
        cl = f.read()
    entries = _changelog_semantic_entries(cl)  # v3.31.5设计端消除：语义最大版本条目·P8实锤
    if not entries:
        return None
    body = entries[0][2]
    evidence_words = ('实测', '实录', 'wc -l', 'wc实测', 'd5_band', 'json', 'JSON', 'skill_eval输出', '脚本输出')
    has_evidence = any(w in body for w in evidence_words)
    hits = []
    if re.search(r'\d{2,}行', body) and re.search(r'[档带]|安全线', body):
        hits.append('行数+档位断言')
    if re.search(r'\d{1,3}/100', body):
        hits.append('分数断言')
    if hits and not has_evidence:
        return (f"断言未绑实录: CHANGELOG最新条目含{'+'.join(hits)}但无来源字样(实测/实录/wc/d5_band/json)——"
                f"档位/分数类数字须附实录源（QD-014一日二犯教训·凭框架印象推断的数字必错·见阶段4断言绑实录两步法）")
    return None


# ── v3.31.5新增：CHANGELOG语义版本解析 helper（设计端消除·P8实锤 2026-08-09） ──
def _changelog_semantic_entries(cl_content):
    """解析 CHANGELOG 全部 `### vX.Y.Z` 条目，按语义版本降序返回 [(ver_tuple, version_str, body), ...]。

    设计端消除（P8·2026-08-09 实锤）：此前三个函数都用「文件首个 ### 条目 = 最新版本」的位置假设
    （re.search/re.split 取首条）。shall-we-talk 曾把 v1.5.2 条目插在两条 v1.5.1 之间 →
    version_uniform 误判「CHANGELOG v1.5.1 ≠ SKILL 1.5.2」→ raw_pass 连带挂 → 封口被拒。
    版本号本身是语义信息，位置顺序只是文档惯例——检查器不应依赖后者。
    本函数统一按语义版本号排序，位置错乱只降级为卫生 warning，不再产生版本一致性误判。
    """
    entries = []
    for m in re.finditer(r'^### (v[\d.]+)[^\n]*\n(.*?)(?=^### |\Z)', cl_content, re.MULTILINE | re.DOTALL):
        ver_str = m.group(1).strip()
        body = m.group(2)
        parts = re.findall(r'\d+', ver_str)
        try:
            nums = [int(x) for x in parts[:3]]
            while len(nums) < 2:
                nums.append(0)  # 补零：v7→(7,0)；v7.25→(7,25)
            while len(nums) < 3:
                nums.append(0)  # 补零到至少3位统一比较：v7.25→(7,25,0)
            ver_tuple = tuple(nums)
        except ValueError:
            continue
        if len(ver_tuple) < 2:
            continue
        entries.append((ver_tuple, ver_str, body))
    entries.sort(key=lambda e: e[0], reverse=True)
    return entries


# ── v3.18.0新增：考题滞后检测 advisory（评估标准动态演进的机械闹钟·皮叔授权2026-07-29） ──
def eval_standard_staleness(skill_path):
    """被评对象版本 vs task-standards.json专属条目考题基线的滞后粗筛。
    背景: 考题层是三条进化管道中无机械闹钟的死角——旧6项从2026-07-03躺到你手动授权(26天)。
    判定: 专属条目(task_type="评估Skill（{name}）")含baseline_version字段且
         被评对象当前版本Y位超出基线≥2(同X下) 或 X位升了 → advisory提示。
    产出: advisory字符串 或 None（无专属条目/无基线字段/未超阈=静默）。
    ⛔不计分不进passed、⛔不自动改标准——考题增删仅限三授权通道(SKILL.md禁止行为#13)，
    本函数只是提醒你审阅的闹钟。同构先例: eval_version_grading_advisory(v3.10.0)。
    v2.9.12：缺失/解析异常两分支的⚪额外升honest红字（消费方=compute_honest_pass·标准库=评测前提）。
    """
    std_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references', 'task-standards.json')
    if not os.path.isfile(std_path):
        return '⚪not-evaluable(staleness): task-standards.json缺失，考题滞后检测未能评估（N5三态）'
    try:
        with open(std_path, 'r', encoding='utf-8') as f:
            std = json.load(f)
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return '⚪not-evaluable(staleness): task-standards.json解析异常，考题滞后检测未能评估（N5三态）'
    m_name = re.search(r'^name:\s*(\S+)', content, re.MULTILINE)
    m_ver = re.search(r"^version:\s*[\"']?(\d+)\.(\d+)\.(\d+)", content, re.MULTILINE)
    if not m_name or not m_ver:
        return None
    name = m_name.group(1).strip()
    cur = tuple(int(x) for x in m_ver.groups())
    for entry in std.get('task_standards', []):
        if not isinstance(entry, dict):
            continue
        if entry.get('task_type') not in (f'评估Skill（{name}）', f'评估Skill({name})'):
            continue
        base_raw = entry.get('baseline_version')
        if not base_raw:
            return None  # 条目在但无基线字段——不测(字段可选·静默)
        m_base = re.match(r'v?(\d+)\.(\d+)\.(\d+)', str(base_raw))
        if not m_base:
            return None
        base = tuple(int(x) for x in m_base.groups())
        x_jumped = cur[0] > base[0]
        y_gap = cur[1] - base[1] if cur[0] == base[0] else None
        if x_jumped or (y_gap is not None and y_gap >= 2):
            gap_desc = f"X位已升({base[0]}→{cur[0]})" if x_jumped else f"Y位已跑{y_gap}格"
            return (f"⚠️ 考题可能滞后: {name}当前v{'.'.join(map(str, cur))} vs 标准基线v{'.'.join(map(str, base))}（{gap_desc}）——"
                    f"旧标准测新版本=假绿灯，建议你审阅「{entry.get('task_type')}」条目是否需追加新机制检查项（只提示不自动改·#13授权锚）")
        return None
    return None


# ── v3.41.0新增：exit碰撞 advisory（L3_沉淀_2026-09-03 模式B·L1反哺·皮叔授权2026-09-03） ──
def eval_exit_collision_advisory(skill_path):
    """相对路径脚本调用 + exit 2 语义表共存 → 解释器级碰撞风险提醒。
    背景: awaken P1-1 实锤——脚本文件不可达时 python 解释器亦 exit 2，与业务 exit 2 语义碰撞
    （cwd漂移即触发错误分支/静默假绿）。纯粗筛不计分,人终判（调用处已带预检则忽略）。
    同构先例: eval_version_grading_advisory(v3.10.0)。"""
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return '⚪not-evaluable(exit_collision): SKILL.md读取失败（N5三态）'
    rel_calls = re.findall(r'`python3\s+(?:scripts/|\./)[^`\s]+`', content)
    has_exit2 = bool(re.search(r'exit\s*2\b|退出码[^\n]*\b2\b', content))
    if rel_calls and has_exit2:
        return ("⚠️ exit碰撞风险: 检测到 %d 处相对路径脚本调用（如 %s）且存在 exit 2 语义声明——"
                "脚本文件不可达时 python 解释器亦 exit 2（awaken P1-1实锤·cwd漂移即触发错误分支/静默假绿）。"
                "建议绝对路径调用+调用预检（L3反哺②·人终判：若调用处已带ls预检则忽略）") % (len(rel_calls), rel_calls[0])
    return None


# ── v3.41.0新增：自描述层计数 advisory（L3_沉淀_2026-09-03 模式A/C·L1反哺·皮叔授权2026-09-03） ──
def eval_selfdesc_advisory(skill_path):
    """自描述层计数声明 vs 实盘粗筛（模式A四连实证：daily-buddy 34条/awaken 13K/growth-box v1.5五方/本脚本v3.40.0注记）。
    两查: ①eval-set.md "N条"声明 vs 实际表格数字行（差≥3）②dependencies脚本数 vs scripts/实存.py/.sh（差≥2）。
    纯advisory不计分——存在性由cross_file检查,此处查"声明数与实盘数的漂移",人终判（设计内豁免合法）。"""
    skill_dir = os.path.dirname(skill_path)
    notes = []
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            main_content = f.read()
    except Exception:
        return '⚪not-evaluable(selfdesc): SKILL.md读取失败（N5三态）'
    evalset_path = os.path.join(skill_dir, 'references', 'eval-set.md')
    if os.path.isfile(evalset_path):
        try:
            with open(evalset_path, 'r', encoding='utf-8') as f:
                es = f.read()
            declared = _declared_evalset_count(es)
            actual_rows = _evalset_rows(es)
            if declared and actual_rows:
                if abs(declared - actual_rows) >= 3:
                    notes.append('eval-set.md 声明%d条 vs 实际数字行%d行（差%d）' % (declared, actual_rows, abs(declared - actual_rows)))
        except Exception:
            pass
    m_deps = re.search(r'^dependencies:\s*\[([^\]]*)\]', main_content, re.M)
    scripts_dir = os.path.join(skill_dir, 'scripts')
    if m_deps and os.path.isdir(scripts_dir):
        dep_count = len([x for x in m_deps.group(1).split(',') if x.strip()])
        actual_scripts = len([x for x in os.listdir(scripts_dir) if x.endswith(('.py', '.sh'))])
        if actual_scripts - dep_count >= 2:
            notes.append('dependencies登记%d个 vs scripts/实存%d个.py/.sh（差%d——可能含设计内豁免）' % (dep_count, actual_scripts, actual_scripts - dep_count))
    if notes:
        return '⚠️ 自描述层计数粗筛: ' + '；'.join(notes) + '（L3反哺③·模式A/C·人终判）'
    return None


# ── v3.20.0新增：托管副本软链接核验 advisory（L3_沉淀_2026-07-29 §三提案2·L1反哺·皮叔拍板2026-07-29） ──
HOSTED_COPY_ROOTS = [
    '~/.openclaw-autoclaw/skills',
    '~/.qoder/skills',
]

def eval_hosted_copy_advisory(skill_path, roots=None):
    """被评Skill在跨端托管目录存在同名副本时，核验其为软链接（指向上游）而非实体目录快照。
    背景: L3沉淀2026-07-29模式E——AutoClaw批次2/3评估前发现托管副本为过时实体快照
    (clock-loop v2.9.4/SWT v1.1.5·Jul12)，评错对象=假绿灯源头。
    判定: 托管根下同名路径存在且非symlink → advisory提示；是symlink或不存在 → None静默。
    评估对象本身就住在托管根下→非副本不报（realpath同一性排除）。
    产出: advisory字符串 或 None。⛔不计分不进passed——环境状态非Skill文件质量，
    修复(替换软链接)动的是托管端，⛔评估器不代改·人操作。
    roots参数仅供负例测试注入，生产路径默认HOSTED_COPY_ROOTS。
    同构先例: eval_standard_staleness(v3.18.0)。
    """
    skill_dir = os.path.dirname(os.path.abspath(skill_path))
    skill_name = os.path.basename(skill_dir)
    if not skill_name:
        return None
    hits = []
    for root in (roots if roots is not None else HOSTED_COPY_ROOTS):
        p = os.path.expanduser(os.path.join(root, skill_name))
        if os.path.isdir(p) and not os.path.islink(p):
            if os.path.realpath(p) == os.path.realpath(skill_dir):
                continue  # 评估对象本身，非副本
            hits.append(p)
    if hits:
        return (f"⚠️ 托管副本疑似实体快照: {'; '.join(hits)} 非软链接——可能为过时双本账"
                f"（Jul12两例先例:clock-loop v2.9.4/SWT v1.1.5），建议替换为软链接指向上游后再评估（⛔评估器不代改·人操作）")
    return None


# ── v4.1.0新增：版本水位线 advisory（C07 #184·跨会话/并发写入检测·皮叔2026-09-05并发事件→修法候选落地） ──
VERSION_WATERMARK_FILE = os.path.join('steps', 'version_watermark.md')


def _parse_version_tuple(v_str):
    """'v4.0.2'/'4.0.2' → (4,0,2)；解析失败→None（fail-visible·不静默当相等）。"""
    m = re.search(r'v?(\d+)(?:\.(\d+))?(?:\.(\d+))?', v_str.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0))


def _watermark_path(skill_path):
    return os.path.join(os.path.dirname(os.path.abspath(skill_path)), VERSION_WATERMARK_FILE)


def eval_version_watermark(skill_path, watermark_path=None):
    """跨会话/并发写入检测（C07 #184·2026-09-05 并发会话活体再现事件→你认可修法候选落地）。

    背景：09-05 10:59 本会话与并发会话同时改 clock-loop 资产——发现时 SKILL.md 已是 v3.47.0、
    CHANGELOG 已被并发方推进，git 6 文件未提交。修法候选="清单加版本水位线字段·每会话开工先读
    clock-loop 当前 version 比对·高于自己记录即先同步再动手"——本函数将其机械化：
    载体 steps/version_watermark.md 记录"上次本会话见过的版本"（last_seen_version+last_seen_at）。
    判定（三态）：
      - 载体缺失 → None 静默（首次运行·由 --update-watermark 显式初始化）
      - 载体版本 == 当前 → None（无跨会话推进·正常开工）
      - 载体版本 < 当前 → advisory：版本推进（跨会话/并发方已升级）——⛔先同步（读CHANGELOG最新
        条目+跑回归）再动手，防基于旧认知改新文件（#184 实锤损害）
      - 载体版本 > 当前 → advisory：版本回退异常（载体 vB > 实盘 vA）——检查是否回滚/误操作
      - 版本解析失败（任一侧）→ fail-visible advisory（⛔不静默当相等）
    ⛔纯读不计分不进 passed（advisory 级·闹钟响了由 AI 终判·同 eval_standard_staleness 族）。
    watermark_path 参数仅供负例测试注入。"""
    wp = watermark_path or _watermark_path(skill_path)
    cur_ver = None
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            m = re.search(r'^version:\s*["\']?([\w.]+)["\']?', f.read(), re.MULTILINE)
        cur_ver = m.group(1) if m else None
    except OSError:
        return '⚪not-evaluable(version_watermark): 被评SKILL.md不可读，水位线比对未能评估（N5三态·"没法查"≠"查了没事"）'
    if not os.path.isfile(wp):
        return None
    try:
        with open(wp, 'r', encoding='utf-8') as f:
            wm = f.read()
    except OSError:
        return '⚪not-evaluable(version_watermark): 水位线载体不可读，未能比对（fail-visible·不静默当一致）'
    m_wm = re.search(r'^last_seen_version\s*:\s*([\w.]+)', wm, re.MULTILINE)
    if not m_wm:
        return '⚠️ 版本水位线载体缺 last_seen_version 行（格式异常·fail-visible·须人工核查/重建）'
    wm_ver = m_wm.group(1)
    if cur_ver is None:
        return '⚠️ 版本水位线：被评SKILL.md 缺 frontmatter version 字段（无法比对·fail-visible）'
    wt = _parse_version_tuple(wm_ver)
    ct = _parse_version_tuple(cur_ver)
    if wt is None or ct is None:
        return (f'⚠️ 版本水位线比对失败：载体 {wm_ver!r} / 实盘 {cur_ver!r} 版本号无法解析'
                f'（fail-visible·须人工核查）')
    if ct > wt:
        return (f'🔴 检测到跨会话/并发推进：版本水位线 {wm_ver} → 实盘 {cur_ver}（高于上次记录）——'
                f'⛔开工先同步：读 CHANGELOG 最新条目+跑回归确认基线，再动手（C07 #184·防基于旧认知改新文件）')
    if ct < wt:
        return (f'⚠️ 版本回退异常：水位线 {wm_ver} > 实盘 {cur_ver}——检查是否误回滚/覆盖（C07 #184）')
    return None


def update_version_watermark(skill_path, watermark_path=None):
    """写当前 SKILL.md 版本入水位线载体（C07 #184·开工同步完成后显式调用）。
    ⛔不自动调用——--check-only 是纯读评估，写文件须 AI 显式动作（防副作用污染评估）。"""
    wp = watermark_path or _watermark_path(skill_path)
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            m = re.search(r'^version:\s*["\']?([\w.]+)["\']?', f.read(), re.MULTILINE)
    except OSError:
        return False, f'被评SKILL.md不可读: {skill_path}'
    if not m:
        return False, '被评SKILL.md 缺 frontmatter version 字段（无法写水位线）'
    ver = m.group(1)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    header = ("# 持久化计数器：版本水位线（C07 #184·跨会话/并发写入检测·v4.1.0）\n\n"
              "# 形态范式：triwich steps/agent_b_streak.md（落盘=跨会话仍存·⛔只放对话上下文=归零）\n"
              "# 用途：每会话开工比对实盘版本 vs 上次记录——高于即先同步再动手（09-05 并发事件修法候选落地）\n\n")
    os.makedirs(os.path.dirname(wp), exist_ok=True)
    tmp = wp + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(header + f'last_seen_version: {ver}\nlast_seen_at: {now}\n')
    os.replace(tmp, wp)
    return True, f'水位线已更新: {ver} @ {now}'


# ── v4.5.0新增：完整性兜底核对机械化 advisory（C14 #178·25天未执行根因修补·评估器盲区现成清单） ──
# 来源：X级议题册 C14（#178 completeness.md 9项「❌人工核对」建档25天从未机械执行——
#   报告实证"查不到的（分项结构错/护栏死/残留假过）全漏"恰是漏检高发区→机械化它＝评估范式
#   从"查自己定义过的可查项"扩到"查覆盖充分性"·#940）。⛔不新造核对项（Via Negativa第一问
#   "能不能不做"→能做少）：就用 completeness.md 判据表 v1.2 的白话/操作两列（#178③逐项论证可机械化）。
# 机械化定位：advisory 级（粗筛+人终判·同 eval_version_watermark/eval_selfdesc_advisory 族）——
#   ⛔不计分不计pass·闹钟响了由 AI 终判（完整性兜底是"查覆盖充分性"，非可数缺陷，硬编码进评分必 Goodhart）。
# skill_path/advisory_path 参数仅供负例测试注入（生产默认从 skill_path 推导）。
COMPLETENESS_ADVISORY_FILE = os.path.join('references', 'completeness.md')

# 各核对项的操作判据关键词（源：completeness.md 判据表 v1.2「操作」列——⛔改判据须双处同步）
_COMP_HIT_CLAMS = ['已验证', '已交付', '已注册', '已上线', '已部署']   # 分析型#5: 声称已验证/已交付
_COMP_RUN_WORDS = ['实跑', '实测', '冒烟', '自举', '回归跑过', '已跑通']  # 分析型#6: 实跑/实测/冒烟
_COMP_SCRIPT_RT = ['.phaseX_last_run.json', '.phaseX_last_run', 'progress_cache',
                   '_last_run.json', 'last_run.json']                # 流程执行型#4: 运行时状态文件
_COMP_TEMPLATE_FILES = ['report-template.md', 'progress-template.md',
                        '画像模板.md']                                # 通用增项#5: references 模板


def _git_check_ignored(scripts_dir, name):
    """运行时文件是否被 git 忽略（v4.7.0·#31同族：被忽略=不随包分发=合规）。

    git check-ignore 按忽略规则路径级匹配（与文件是否已跟踪/存在无关）。
    非 git 仓库/命令失败 → False（保守：无法确认忽略→视为未忽略→提示·防漏报·宁可多报不漏报）。"""
    import subprocess
    try:
        r = subprocess.run(['git', '-C', scripts_dir, 'check-ignore', '-q', name],
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def eval_completeness_advisory(skill_path, advisory_path=None, ignore_fn=None):
    """完整性兜底核对机械化（C14 #178·completeness.md 9项「❌人工核对」→ 脚本化 advisory）。

    背景：completeness.md 是"评估器盲区"的现成分类清单（#178②实测 9项人工核对项正是本轮全部
    重大发现的归属地：#130护栏死/#171逃脱对账/#169分项结构错/#167残留假过）。08-10 建档至 09-05
    共 25 天从未机械执行（#178）——"逐项标 [已覆盖]/[❌缺口]"是 prose 级纪律（#89 同族"仅prose
    升MUST却仍在用"），可言而无信。本函数把判据表 v1.2 的 9 项操作列中可机械化的做成粗筛：

      - 分析型#3 eval-set 分项标题声称 vs 正文实际 → 声明条数 vs 实际表格行数漂移（同 selfdesc 粗筛）
      - 分析型#5 声称"已验证/已交付/已注册"有运行或磁盘证据 → 命中声明后找 references/scripts 实务
      - 分析型#6 可运行性结论有实跑或标注"未实跑" → 找"能运行/可运行"声明与其旁的实跑词
      - 流程执行型#4 运行时状态文件不随包分发 → scripts/ 下 .phaseX_last_run.json 等运行时垃圾
      - 通用增项#5 模板-正文同步 → references 模板是否被 SKILL.md 正文实际引用（引用物存在性）
      - 通用增项#6 指标操作化 → 量化指标声明旁是否有计算式/分子分母/样本口径（半机械：关键词粗筛）

    判据·实现分工：9项中 #2/#5(#磁盘)/#6/#8/#9 直接可机械；#3(metrics)半机械关键词粗筛；
    #7(自举回归)属回归环节⛔不进此函数（check_selfimprove_gate 管）——因此本函数覆盖 6 项粗筛，
    其余 3 项（分析型#2 自检清单自省 / 交互型#4 熔断器新鲜度 / 流程执行型#2 自举回归）由
    completeness.md 判据表保留为"人工核对"位（⛔不硬编码误判 DQ 边界）。

    产出：无异常 → None（§7.5 静默幂等）；有粗筛发现 → ⚠️ advisory 字符串（人终判）。
    ⛔纯读不计分不进 passed（同 eval_selfdesc_advisory 族）。
    参数 ignore_fn（v4.7.0·测试注入）：判定"运行时文件是否被忽略"（dir,name）→bool；
    默认 None → _git_check_ignored（git check-ignore 实测·被忽略=不随包分发=合规·静默）。"""
    skill_dir = os.path.dirname(os.path.abspath(skill_path))
    notes = []
    refs_dir = os.path.join(skill_dir, 'references')
    scripts_dir = os.path.join(skill_dir, 'scripts')

    # ── 分析型#3：eval-set 声明条数 vs 实际表格行（同 selfdesc 但独立·防双源宕机） ──
    es_path = advisory_path or os.path.join(refs_dir, 'eval-set.md')
    try:
        if os.path.isfile(es_path):
            with open(es_path, encoding='utf-8') as f:
                es = f.read()
            declared = _declared_evalset_count(es)
            actual_rows = _evalset_rows(es)
            if declared and actual_rows and abs(declared - actual_rows) >= 3:
                notes.append('分析型#3: eval-set.md 声明%d条 vs 实际表格%d行（差%d——声称vs实盘漂移）'
                             % (declared, actual_rows, abs(declared - actual_rows)))
    except Exception:
        pass

    # ── 分析型#5：声称已验证/交付 是否有 references 或 scripts 实务佐证 ──
    try:
        with open(skill_path, encoding='utf-8') as f:
            main_content = f.read()
        claims = [c for c in _COMP_HIT_CLAMS if c in main_content]
        if claims:
            has_asset = os.path.isdir(refs_dir) and any(
                p.endswith(('.md', '.json', '.yaml')) for p in os.listdir(refs_dir))
            has_script = os.path.isdir(scripts_dir) and any(
                p.endswith(('.py', '.sh')) for p in os.listdir(scripts_dir))
            if not (has_asset or has_script):
                notes.append('分析型#5: 声明%s但 references/ 与 scripts/ 均无实务资产（"已验证"无证据凭据）'
                             % ('/'.join(claims)))
    except Exception:
        pass

    # ── 分析型#6：可运行性声明旁是否有实跑/未实跑标注 ──
    try:
        run_claims = re.findall(r'[^\n]*?(?:能运行|可运行|可执行|运行正常)[^\n]*', main_content)
        for sent in run_claims[:8]:
            if not any(w in sent for w in _COMP_RUN_WORDS) and '未实跑' not in sent:
                if '能运行' in sent or '可运行' in sent:
                    notes.append('分析型#6: 「%s」可运行性声明缺实跑标注（无实跑/未实跑词·结论与实跑不同权事项）'
                                 % sent.strip()[:60])
                    break
    except Exception:
        pass

    # ── 流程执行型#4：运行时状态文件不随包分发（#31 零覆盖垃圾同族） ──
    try:
        if os.path.isdir(scripts_dir):
            rt = [n for n in os.listdir(scripts_dir) if any(n.endswith(s) for s in _COMP_SCRIPT_RT)]
            if rt:
                # v4.7.0：gitignore 识别——被忽略=不随包分发=合规（个人AI档案 .gitignore
                # `**/*_last_run.json` 实测命中 .phaseX_last_run.json/.finalize_last_run.json）
                _ig = ignore_fn if ignore_fn is not None else _git_check_ignored
                unignored = []
                for n in rt:
                    try:
                        if not _ig(scripts_dir, n):
                            unignored.append(n)
                    except Exception:
                        unignored.append(n)  # 判定失败→保守视为未忽略（防漏报·宁可多报不漏报）
                if unignored:
                    notes.append('流程执行型#4: scripts/ 含运行时状态文件 %s（不该随包分发·#31同族）'
                                 % ', '.join(sorted(unignored)))
    except Exception:
        pass

    # ── 通用增项#5：references 模板被正文实际引用（模板与正文机制同源·单向漂移检测） ──
    try:
        template_hits = []
        for tpl in _COMP_TEMPLATE_FILES:
            tpl_ref = f'references/{tpl}'
            if tpl_ref in main_content:
                # 正文声明引用模板 → 校验指向物存在（模板-正文同步的"引用物存在性"位）
                if not os.path.isfile(os.path.join(refs_dir, tpl)):
                    template_hits.append(f'{tpl}(正文引用但references缺失)')
        if template_hits:
            notes.append('通用增项#5: 模板-正文同步异常——正文引用模板但指向物不存: %s' % ', '.join(template_hits))
    except Exception:
        pass

    # ── 通用增项#6：量化指标是否有计算式/口径（半机械·关键词粗筛人终判） ──
    try:
        metric_hits = []
        for line in main_content.splitlines():
            m = re.search(r'([^\n]{0,40}(?:%|率|精准率|准确率|完成率|达标率)[^\n]{0,40})', line)
            if not m:
                continue
            seg = m.group(1)
            if not re.search(r'[\d%]', seg):
                continue
            has_formula = ('计算' in seg or '公式' in seg or '=/' in seg or '=' in seg or '/(' in seg
                           or '分子' in seg or '分母' in seg or '样本' in seg or '口径' in seg)
            if '指标' in seg and not has_formula:
                metric_hits.append(seg.strip()[:50])
        if metric_hits:
            notes.append('通用增项#6: 量化指标缺计算式/口径关键词（半机械粗筛·人终判是否为装饰性标准）: %s'
                         % '；'.join(metric_hits[:3]))
    except Exception:
        pass

    if notes:
        return ('⚠️ 完整性兜底核对粗筛（C14 #178·completeness.md 9项机械化·人终判）: ' + '；'.join(notes))
    return None


# ── v4.2.0新增：教训召回 advisory（C06 #68·跨周期学习断裂·愿景③④核心缺口） ──
LESSONS_LEDGER_FILE = os.path.join('steps', 'lessons_ledger.md')
LESSON_RECALL_DAYS = 30
LESSON_RECALL_TOP = 3


def _lessons_path(skill_path):
    return os.path.join(os.path.dirname(os.path.abspath(skill_path)), LESSONS_LEDGER_FILE)


def _parse_lessons(ledger_text):
    """解析教训台账 → [{lesson, mode, fix, first, last, times}]。
    ⛔解析失败条目跳过（fail-visible 由外层计数体现·不静默当活跃）。"""
    lessons = []
    blocks = re.split(r'\n(?=- \*\*LESSON-\d+\*\*)', ledger_text)
    for blk in blocks:
        if 'LESSON-' not in blk:
            continue
        lm = re.search(r'-\s*\*\*(LESSON-\d+)\*\*', blk)
        if not lm:
            continue
        last_m = re.search(r'最近犯\s*[:：]\s*(\d{4}-\d{2}-\d{2})', blk)
        first_m = re.search(r'首犯\s*[:：]\s*(\d{4}-\d{2}-\d{2})', blk)
        mode_m = re.search(r'错误模式[:：]\s*(.+)', blk)
        fix_m = re.search(r'正确姿势[:：]\s*(.+)', blk)
        times_m = re.search(r'次数[:：]\s*(\d+)', blk)
        lessons.append({
            'lesson': lm.group(1),
            'mode': mode_m.group(1).strip() if mode_m else '',
            'fix': fix_m.group(1).strip() if fix_m else '',
            'first': first_m.group(1) if first_m else None,
            'last': last_m.group(1) if last_m else None,
            'times': int(times_m.group(1)) if times_m else 0,
        })
    return lessons


def eval_lessons_recall_advisory(skill_path, ledger_path=None, today=None):
    """跨周期学习断裂召回（C06 #68·v4.2.0·2026-09-05 你定议题册第三批）。

    背景：#68"教训入账却从未阻止下一次"——SearchReplace 中文错字史 07-29 两次+09-04 一次、
    本会话 13 次方法错误，每次教训都入账（PAT/CHANGELOG）却从没被新会话读到→新会话读不到
    就等于没发生（愿景③④核心缺口·非加文档能解）。本函数将"自动召回"机械化：
    读 steps/lessons_ledger.md（AI 犯错误后登记的教训台账），召回活跃教训
    （最近犯日距今 ≤30 天·按最近犯日倒序 Top 3），输出到 --check-only 开工上下文。
    判定：
      - 载体缺失 → None 静默（幂等·首次由 AI 登记后生效）
      - 无活跃教训（全部最近犯 >30 天或无条目）→ None 静默
      - 有活跃 → advisory 列出 Top 3 + 活跃总数（⛔开学前先复习·防重犯）
      - 载体存在但全条目解析失败 → fail-visible advisory（⛔不静默当无教训）
    ⛔纯读不计分不进 passed（advisory 级·闹钟响了由 AI 终判·同 eval_version_watermark 族）。
    ledger_path/today 参数仅供负例测试注入。"""
    lp = ledger_path or _lessons_path(skill_path)
    today = today or date.today()
    if not os.path.isfile(lp):
        return None
    try:
        with open(lp, 'r', encoding='utf-8') as f:
            text = f.read()
    except OSError:
        return '⚪not-evaluable(lessons_recall): 教训台账不可读，召回未能评估（fail-visible）'
    lessons = _parse_lessons(text)
    if not lessons:
        return '⚠️ 教训台账存在但无可解析条目（格式异常·fail-visible·须人工核查/重建）'
    active = []
    for lt in lessons:
        if not lt['last']:
            continue
        try:
            d = datetime.strptime(lt['last'], '%Y-%m-%d').date()
        except ValueError:
            continue
        if (today - d).days <= LESSON_RECALL_DAYS:
            active.append(lt)
    if not active:
        return None
    active.sort(key=lambda x: x['last'], reverse=True)
    top = active[:LESSON_RECALL_TOP]
    lines = '；'.join(f"{t['lesson']}({t['mode']})" for t in top)
    return (f"🔴 跨周期教训召回：{len(active)} 条活跃教训（最近犯 ≤{LESSON_RECALL_DAYS} 天）——"
            f"⛔开工先复习 Top{LESSON_RECALL_TOP}：{lines}（C06 #68·新会话读不到=等于没发生）")


# ── v4.3.0新增：触顶判定机械化（C12 #198·"交付时自动计算"实测无脚本·E5声明-执行gap） ──
# phase3-termination.md v2.2.0 三指标阈值（⛔判据立法化：本函数与 references/phase3-termination.md 触顶段双处同步）
CEILING_SAT_RATIO = 16 / 20      # 指标1：维度饱和度 ≥16/20（0.8 比率·维度数变化时以 0.8 为准防字面量失准）
CEILING_REMAIN_MAX = 8.0         # 指标2：剩余可修复空间比率 <8%
CEILING_FD_MIN = 3.0             # 指标3：功能侧vs文档侧剩余空间比 >3:1 → 文档侧触顶
# 维度侧别划分（指标3 用·⛔唯一源=phase3-termination.md「维度侧别划分」段·v4.3.0 补）
# 功能侧=机制/运行类（须建测试/改脚本/运行时验证提升）·文档侧=文本内容类（改 SKILL.md 可提升）
CEILING_FUNCTIONAL_DIMS = frozenset({
    'fuse_mechanism', 'file_clutter',
    'eval_set_gate', 'trigger_coverage', 'security_hardcode',
})
CEILING_DOC_DIMS = frozenset({
    'yaml_frontmatter', 'yaml_required_fields', 'description_not_for',
    'sec_1_2_version_single_source', 'five_level_annotations',
    'no_binary_annotations', 'causal_chain', 'alternatives_considered',
    'poka_yoke_layer', 'deliverable_definition', 'trigger_conditions',
    'position_risk', 'cross_file_consistency', 'single_number_source',
})


def compute_ceiling_indicators(scores, weights=None):
    """触顶判定三指标（C12 #198机械化·v4.3.0·2026-09-05 你定议题册第三批）。

    背景：phase3-termination.md v2.2.0 声明触顶判定"交付时自动计算"，实测
    skill_eval.py 中 维度饱和度/触顶/剩余可修复空间/saturation 全 0 命中——
    "自动计算"是假的（靠 AI 手算）→ 触顶永不宣告 → 第52行"⛔DO NOT继续建议
    文档修补"成为永远无法触发的禁令（永远无法触发的禁令＝没有禁令）。
    本函数将三指标机械化：
      指标1 维度饱和度 = 得分≥90%的维度数/总维度数 ≥16/20 → 触顶
      指标2 剩余可修复空间比率 = Σ(1-各维度达成率)/维度数 <8% → 触顶
      指标3 功能侧vs文档侧空间比 = Σ功能侧剩余/Σ文档侧剩余 >3:1 → 文档侧触顶
    达成率 = scores[key]/WEIGHTS[key]（#199① 维度级得分取法·⛔不取 eval_* 返回的
    ratio——scores 已是 权重×ratio 的实际得分·由 evaluate_skill 换算）。
    三指标任一触发 → ceiling=True（文档侧空间耗尽·追分须转功能侧/运行时验证）。
    ⛔纯函数不进 passed（advisory 级·闹钟响了由 AI 终判·同 eval_version_watermark 族）。
    scores/weights 参数仅供考题基线注入。"""
    weights = weights or WEIGHTS
    ratios = {}
    for k, v in (scores or {}).items():
        w = weights.get(k, 0)
        if w > 0:
            ratios[k] = v / w
    n = len(ratios)
    if n == 0:
        return {'ceiling': False, 'indicators': None, 'detail': '无维度得分可算'}
    n_high = sum(1 for r in ratios.values() if r >= 0.90)
    sat = n_high / n
    remain = sum(1.0 - r for r in ratios.values()) / n * 100.0
    func_remain = sum(1.0 - r for k, r in ratios.items() if k in CEILING_FUNCTIONAL_DIMS)
    doc_remain = sum(1.0 - r for k, r in ratios.items() if k in CEILING_DOC_DIMS)
    fd = (func_remain / doc_remain) if doc_remain > 0 else float('inf')
    ceiling = (sat >= CEILING_SAT_RATIO) or (remain < CEILING_REMAIN_MAX) or (fd > CEILING_FD_MIN)
    return {
        'ceiling': ceiling,
        'indicators': {
            'saturation': round(sat, 4),
            'saturation_n': n_high,
            'saturation_total': n,
            'remain_pct': round(remain, 2),
            'func_doc_ratio': (round(fd, 2) if fd != float('inf') else 'inf'),
        },
    }


# ── v4.6.0 评估器自我观察（Observability）·B1/B2/B3/A1 四机制 ────────────────
# B1 载体：scripts/.advisory_history.jsonl（追加写·运行时状态文件·.gitignore **/*_history.jsonl
#   排除不进包·同 .phaseX_last_run.json 族·流程执行型#4 不随包分发）
ADVISORY_HISTORY_FILE = os.path.join('scripts', '.advisory_history.jsonl')
ADVISORY_HISTORY_WINDOW = 10   # 统计窗口=最近 N 次运行
ADVISORY_HISTORY_MIN = 5       # 有效样本 < N → None 静默（样本不足不判定·⛔不做小样本断言）
ADVISORY_HIGH_RATIO = 0.8      # 触发率 ≥80% = 常响（狼来了·建议折叠/转自动/降级）


def _advisory_history_path(history_path=None):
    """解析 B1 历史文件绝对路径（入参优先·否则脚本同目录 scripts/）。"""
    if history_path:
        return history_path
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '.advisory_history.jsonl')


def _record_advisory_history(target, advisory_map, history_path=None):
    """追加一次运行的 advisory 触发快照（B1·v4.6.0）。

    ⛔副作用纪律：与 .phaseX_last_run.json 同族（--check-only 既有写文件事实）——
    记录的是"检查器行为"非被评目标内容·不影响评估结果。"""
    p = _advisory_history_path(history_path)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'ts': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'target': target,
                'triggers': advisory_map,
            }, ensure_ascii=False) + '\n')
    except OSError:
        return False
    return True


def eval_advisory_frequency(history_path=None, window=ADVISORY_HISTORY_WINDOW,
                            min_samples=ADVISORY_HISTORY_MIN, high_ratio=ADVISORY_HIGH_RATIO):
    """advisory 触发率统计（B1·v4.6.0·--check-only 消费·样本不足→None 静默）。

    判据（立法化·skill-arch-standard §2.2a v4.6.0·B1行）：
      - 读 .advisory_history.jsonl 最后 window 次运行，逐 advisory 计触发率=触发次数/有效样本数。
      - 有效样本 < min_samples(5) → None 静默（⛔小样本不判定）。
      - 触发率 ≥ high_ratio(80%) 且样本达标 → 常响（狼来了·建议折叠/转自动/降级·终判权在人）。
    产出：{'freq': {name: {'ratio': x, 'n': n}}, 'window': w, 'frequent': [names]} 或 None。"""
    p = _advisory_history_path(history_path)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding='utf-8') as _fh:
            lines = _fh.read().splitlines()
    except OSError:
        return None
    records = []
    for ln in lines[-window:]:
        try:
            r = json.loads(ln)
            if isinstance(r.get('triggers'), dict):
                records.append(r)
        except (ValueError, TypeError):
            continue
    if len(records) < min_samples:
        return None
    names = sorted({k for r in records for k in r['triggers']})
    freq, frequent = {}, []
    for name in names:
        hit = sum(1 for r in records if r['triggers'].get(name))
        ratio = hit / len(records)
        freq[name] = {'ratio': round(ratio, 2), 'n': hit}
        if ratio >= high_ratio:
            frequent.append(name)
    return {'freq': freq, 'window': len(records), 'frequent': frequent}


def _checker_hygiene_funcs(src_text):
    """扫描评估器顶层检查函数（B2·eval_/compute_/format_ 前缀·顶格 def）。"""
    return re.findall(r'^def (eval_\w+|compute_\w+|format_\w+)\s*\(', src_text, re.M)


def eval_checker_hygiene(src_path=None, test_path=None):
    """检查器卫生审计（B2·v4.6.0·--check-only 消费·⚪提示级不计分）。

    判据（立法化·skill-arch-standard §2.2a v4.6.0·B2行）：评估器新增/修改判据必须附
    考题基线+负控制测试（合法形态满分不误伤）——l3_conclusion_guard 事故制度化预防。
    本函数机械粗筛：函数体前 400 字符含 'v4.' 版本标注（=新判据立法标记·§2.2a 登记义务）
    且未被 test_skill_eval.py 直接引用的检查函数 → ⚪提示"判据无直接测试引用"。
    ⛔提示级不阻断（间接覆盖存在·终判权在人·同 advisory 族纪律）。"""
    src = src_path or os.path.abspath(__file__)
    test = test_path or os.path.join(os.path.dirname(src), 'test_skill_eval.py')
    if not os.path.exists(src) or not os.path.exists(test):
        return None
    with open(src, encoding='utf-8') as _fh:
        src_txt = _fh.read()
    with open(test, encoding='utf-8') as _fh2:
        test_txt = _fh2.read()
    flagged = []
    for m in re.finditer(r'^def (eval_\w+|compute_\w+|format_\w+)\s*\(', src_txt, re.M):
        name = m.group(1)
        if name in test_txt:
            continue
        head = src_txt[m.end():m.end() + 400]
        if 'v4.' in head:
            flagged.append(name)
    if not flagged:
        return None
    return ('⚪ 检查器卫生：以下带 v4. 版本标注的检查函数无直接测试引用'
            '（判据立法化要求考题基线+负控制·§2.2a v4.6.0）：' + '、'.join(flagged))


def compute_checker_complexity(src_path=None, top_n=3):
    """评估器自身复杂度度量（B3·v4.6.0·--check-only 消费·⚪提示级不计分）。

    判据（立法化·skill-arch-standard §2.2a v4.6.0·B3行）：评估器 210KB/20维度——自身体量
    须可观测才可瘦身（先测量再决定拆不拆·⛔不预设拆）。ast 解析统计总行数/顶层函数数/
    平均与最大函数行数/Top-N 最重函数。阈值粗筛：平均>100 或 最大>300 → 瘦身候选提示。
    ⛔提示级不计分（体量≠质量·Goodhart 边界）。"""
    import ast as _ast
    src = src_path or os.path.abspath(__file__)
    if not os.path.exists(src):
        return None
    with open(src, encoding='utf-8') as _fh:
        txt = _fh.read()
    lines = txt.splitlines()
    total = len(lines)
    try:
        tree = _ast.parse(txt)
    except SyntaxError:
        return None
    funcs = [(n.name, n.end_lineno - n.lineno + 1)
             for n in _ast.walk(tree)
             if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef))]
    if not funcs:
        return None
    funcs.sort(key=lambda x: -x[1])
    avg = sum(f[1] for f in funcs) / len(funcs)
    heavy = [{'name': n, 'lines': l} for n, l in funcs[:top_n]]
    return {'total_lines': total, 'func_count': len(funcs),
            'avg_func_lines': round(avg, 1), 'max_func_lines': funcs[0][1],
            'heaviest': heavy}


def format_evidence_summary(evidence):
    """证据复核入口一行（A1·v4.6.0·--check-only 消费·exercised 档人可读汇总）。

    判据（立法化·skill-arch-standard §2.2a v4.6.0·A1行）：自举分数可查证——
    evidence=exercised 时输出"N条运行时证据·ceiling/capped·明细见 evidence.upgrade_refs"，
    人可一键复核支撑档位的证据链（100分不黑箱）。wired/present/na 输出简洁行。"""
    if not evidence:
        return 'na（无证据档位）'
    grade = evidence.get('grade', 'na')
    if grade == 'exercised':
        refs = evidence.get('upgrade_refs') or []
        return (f"exercised·{len(refs)}条运行时证据·ceiling={evidence.get('ceiling', '?')}"
                f"·capped={evidence.get('capped_score', '?')}·明细见 evidence.upgrade_refs")
    if grade == 'wired':
        return f"wired（机制已接线未实跑·ceiling={evidence.get('ceiling', '?')}）·⛔不升exercised"
    return f"{grade}（静态·ceiling={evidence.get('ceiling', '?')}）"


def format_ceiling_advisory(scores, weights=None):
    """触顶状态行（C12 #198·--check-only 消费·未触顶→None 静默）。

    v4.7.0 降级（B1 常响根治·分级错误修正）：触顶是 S 级常态状态（非异常）——
    🔴告警→ℹ️状态行语义·⛔移出 advisory 触发率统计（状态指示不参与告警频度·B1 只统计告警型）。
    文案保留"文档侧已触顶"字样（消费方兼容·决策指引不变：⛔追分须转功能侧）。"""
    ci = compute_ceiling_indicators(scores, weights)
    if not ci.get('ceiling') or not ci.get('indicators'):
        return None
    ind = ci['indicators']
    return (f"ℹ️ 文档侧已触顶（状态行·非告警·phase3-termination.md v2.2.0·C12 #198 机械化）："
            f"维度饱和度 {ind['saturation_n']}/{ind['saturation_total']}（≥16/20）·"
            f"剩余可修复空间 {ind['remain_pct']}%（<8%）·"
            f"功能侧/文档侧剩余空间比 {ind['func_doc_ratio']}:1（>3:1）——"
            f"⛔追分须转[功能侧/运行时测试/端到端验证]（⛔DO NOT继续建议文档修补类修复·浪费Token）")


# ── v3.19.0双章制计算（v3.19.1提取为可测函数·回归断言护栏接入点）──
def compute_honest_pass(result, version_result, staleness_advisory=None):
    """双章制归一（v3.27.0·假绿灯聚合根除·三明智L2+迁理之外双验证）。

    v2.9.12新增可选参 staleness_advisory：task-standards.json 缺失/解析异常（返回串以
    ⚪not-evaluable(staleness) 开头）升红字"标准库损坏"——标准库是评估器自身的评测前提，
    前提断裂≠对象侧"没法查"（N5三态不适用于评估器内脏），沉默放行=考题基线整体失效仍出绿灯。
    （v4.12.7待办落地·触发=clock-loop自评Loop·2026-09-27）

    旧双章制(v3.19.0)：honest_pass+passed两个"通过"字段并存——同一脚本同时吐"通过"和"不诚实"。
    根治方案(B')：passed=honest_pass(诚实章为唯一结论)，raw_pass保留旧口径(历史可比通道)。
    返回 (passed, flags, raw_pass)：
      - passed=诚实结论(红字任一存在→False)
      - flags=红字清单
      - raw_pass=旧口径(≥70+gates+version)，所有历史评估报告的passed等于新raw_pass

    历史可比性：旧报告passed字段语义=新raw_pass字段语义。版本分界v3.27.0起，
    passed不再是raw93而是诚实结论。需要对比历史趋势线时，用raw_pass或evidence.raw_total。
    ⚪source-unreachable不计红字——"没法查"≠"查出问题"（N5三态同族）。
    """
    raw_pass = (result.get('total', 0) >= 70 and
                all(result.get('gate', {}).values()) and
                version_result.get('passed', False))
    flags = []
    # v3.31.3 根改（第一性原理·皮叔 2026-08-09 定）：长度服务于工作，长度≠质量。
    # v5.16.0 已根治：token_budget 从 WEIGHTS 移出·行数仅作标注+advisory 提醒·永不扣分
    # 绝不计入 honest_flags。这是"长度否定质量"的根，曾让每个长 Skill 复评重蹈（P1-1 补丁未触此根）。
    # 与 v3.30.1 推论2「行数梯度是风险信号非质量判决」一致：不可接受档触发人类审视，不裸红字、不否决可用性。
    capped = (result.get('evidence') or {}).get('capped_score')
    if capped is not None and capped < 70:
        flags.append(f"证据档位capped={capped}<70")
    drifts = [d.get('name') for d in version_result.get('dependencies', [])
              if 'drift' in str(d.get('status', ''))]
    if drifts:
        # v4.12.1·审查E-3第四形态：原标签"固化引用漂移"冒名顶替——dependencies.drift 查的是
        # SKILL.md 声明字段过期（固化副本可能实际已同步·check_cured_snapshot 判绿），
        # 红字文案与被查事实不符=声明-执行gap犯在自家诚实章上。固化副本真漂移由下方 cured_snapshot_check 单独发红。
        flags.append(f"依赖声明漂移×{len(drifts)}({','.join(drifts)})")
    # v3.46.0 A39（fail-open 第四形态根治·2026-09-05）：固化对账子检查红灯上浮到诚实章。
    #   原设计（L2131 注释）把漂移只写进 warnings「让评估者在报告中记录」＝软通道靠 AI 自觉，
    #   致 cured_snapshot_check.passed=False / exit=1 期间 passed 仍 True、honest_flags 仍 []、score 仍满分
    #   ＝「检出了漂移却不阻断交付」（#143「有痕跳过≠静默跳过」第四形态：有痕报红≠阻断交付）。
    #   ⚪ passed is None（脚本不可运行/超时）不计红字——「没法查」≠「查出问题」（本函数 docstring N5 三态同族）。
    cured = version_result.get('cured_snapshot_check') or {}
    if cured.get('passed') is False:
        flags.append(f"固化对账失败(check_cured_snapshot exit={cured.get('exit_code')})")
    # v2.9.12（2026-09-27·v4.12.7待办落地）：标准库损坏升honest观察。⚪是对象侧"没法查"的诚实标注，
    # 但task-standards.json是评估器自己的评测前提——前提断裂属"查出问题"级，须阻断假绿灯。
    if staleness_advisory and staleness_advisory.startswith('⚪not-evaluable(staleness)'):
        _why = re.sub(r'^.*?staleness\):\s*', '', staleness_advisory).split('，')[0]
        flags.append(f"标准库损坏({_why})")
    if not raw_pass:
        flags.append('基础raw_pass未过')
    passed = (len(flags) == 0)  # 归一：passed=诚实章
    return (passed, flags, raw_pass)


# ── v3.31.6新增：等级判定唯一真相源（第一性原理根治·等级口径混乱 2026-08-09 你定） ──
def compute_grade(total_score):
    """等级判定唯一真相源（纯函数·可复现·AI不得自创）。

    设计依据（第一性原理·皮叔 2026-08-09 拍板根治等级口径混乱）：
      混乱病根：历史报告等级判定无单一权威——skill_eval --report 有机械 grade（L2704）
      但 --check-only 不输出（Phase X 机检后 AI 拿不到机械等级）→ 报告模板等级行是空占位符
      → 最终等级全凭 AI 手感（实证：growth-box raw 89 被写 S级、scriyore raw 100 被写 A级、
      shall-we-talk 哲学被自创规则打成 B 后又修正回 S）。
      本函数把等级判定收敛为唯一机械入口：S≥90 / A≥80 / B≥70 / C<70（与 --report L2704 同源）。
      ⛔DO NOT 在报告/流程中另立等级规则（含综合加权自创映射）——等级只由本函数产出。
    证据档位（present/wired/exercised/outcome）是独立维度，⛔DO NOT 混入等级判定（capped 不参与 grade）。
    """
    if total_score >= 90:
        return 'S'
    if total_score >= 80:
        return 'A'
    if total_score >= 70:
        return 'B'
    return 'C'


# ── v2.8.0新增：全文件版本统一校验 ────────────────────────────────
def normalize_ver(v):
    """统一版本格式去v前缀，方便比较（v4.8.2 由 eval_version_uniform 闭包提模块级）"""
    return v.lstrip('vV')


def _check_dependencies(main_content, skill_dir):
    """外部依赖版本核对：dependencies 声明 vs 源文件 vs 固化引用（v4.8.2 原步骤6独立块）

    返回 (dependencies列表, warnings列表)——只写这两个键，不碰版本流水线共享态。
    """
    dependencies = []
    warnings = []
    dep_pattern = re.compile(
        r'-\s*name:\s*(\S+)\s*\n\s*version:\s*["\']?([\w.]+)["\']?\s*\n(?:\s*path:\s*(\S+))?',
        re.MULTILINE
    )
    for m in dep_pattern.finditer(main_content):
        dep_name = m.group(1)
        declared_ver = m.group(2)
        dep_path = m.group(3)
        if not dep_path:
            # C-A1（L3反哺·2026-08-12）：path 字段缺失时按本机技能配置目录约定解析——
            # 实证：sucair H1 幻影版本（shall-we-talk 声明 4.5.0 vs 磁盘 1.5.2）因依赖条目无 path 字段整条漏检
            # v1.7.2 断根（2026-10-10）：原式只试发布态占位符 ⇒ 作者机 expanduser 不展开=相对路径 ⇒ isdir 恒假 ⇒ 依赖漏检静默。
            # 改多候选：本机真名优先，占位符兜底（保留自定义记忆中心名用户的包内语义）。
            cand = next((c for c in (
                os.path.join(os.path.expanduser('[记忆共享中心]'), '技能配置', dep_name),
                os.path.join(os.path.expanduser('[记忆共享中心]'), '技能配置', dep_name),
            ) if os.path.isdir(c)), os.path.join(os.path.expanduser('[记忆共享中心]'), '技能配置', dep_name))  # v1.7.1参数化:原写死默认目录名,自定义名用户依赖解析漏检
            dep_path = cand if os.path.isdir(cand) else None
        if dep_path:
            dep_path = dep_path.replace('~', os.path.expanduser('~'))
        
        dep_info = {
            'name': dep_name,
            'declared': declared_ver,
            'source_ver': None,
            'ref_ver': None,
            'status': 'unknown'
        }
        
        # Check source file
        source_skill = os.path.join(dep_path, 'SKILL.md') if dep_path else ''
        if not os.path.isfile(source_skill):
            # 非 Skill 源（如规范文件）：在目录里找文件名含 name 关键词的文件
            name_keys = {'instruction-standard': '指令编写', 'skill-arch-standard': '架构规范'}
            if dep_path and os.path.isdir(dep_path):
                key = name_keys.get(dep_name)
                if key:
                    candidates = [f for f in os.listdir(dep_path) if key in f and f.endswith('.md')]
                    source_skill = os.path.join(dep_path, candidates[0]) if candidates else source_skill
                else:
                    # 无明确映射时取第一个非 README .md
                    for f in sorted(os.listdir(dep_path)):
                        if f.endswith('.md') and f != 'README.md':
                            source_skill = os.path.join(dep_path, f)
                            break
        if os.path.isfile(source_skill):
            with open(source_skill, 'r', encoding='utf-8') as f:
                src_content = f.read()
            sv1 = re.search(r'^version:\s*["\']?([\w.]+)["\']?', src_content, re.MULTILINE)
            sv2 = RE_VERSION_BOLD.search(src_content)
            sv3 = RE_VERSION_COLON.search(src_content)
            sv = None
            if sv1:
                sv = sv1.group(1)
            elif sv2:
                sv = sv2.group(1)
            elif sv3:
                sv = sv3.group(1)
            if sv:
                dep_info['source_ver'] = sv
        
        # Check固化引用 (references/ 下)
        ref_map = {
            'triwich': 'triwich-integration',
            'meta-aletheia': 'philosophical-evaluation',
            'skill-arch-standard': 'skill-arch-standard',
            'instruction-standard': 'instruction-standard',
        }
        ref_name = ref_map.get(dep_name)
        if ref_name:
            ref_path = os.path.join(skill_dir, 'references', f'{ref_name}.md')
            if os.path.isfile(ref_path):
                with open(ref_path, 'r', encoding='utf-8') as f:
                    ref_content = f.read()
                rv = re.search(r'^version:\s*["\']?([\w.]+)["\']?', ref_content, re.MULTILINE)
                if rv:
                    dep_info['ref_ver'] = rv.group(1)
        
        # 判定
        d = normalize_ver(dep_info['declared'])
        s = normalize_ver(dep_info['source_ver']) if dep_info['source_ver'] else None
        r = normalize_ver(dep_info['ref_ver']) if dep_info['ref_ver'] else None
        
        issues = []
        if s and d != s:
            issues.append(f'dependencies声明版本{dep_info["declared"]} ≠ 源文件版本{dep_info["source_ver"]}')
        if r and s and r != s:
            issues.append(f'固化引用版本{dep_info["ref_ver"]} ≠ 源文件版本{dep_info["source_ver"]}')
        if r and r != d and s and r == s:
            issues.append(f'dependencies声明版本{dep_info["declared"]} ≠ 固化引用版本{dep_info["ref_ver"]}')
        if r and d and r != d and not s:
            issues.append(f'dependencies声明版本{dep_info["declared"]} ≠ 固化引用版本{dep_info["ref_ver"]}（源不可达·本地两方自矛盾）')
        
        if issues:
            dep_info['status'] = '🔴 drift'
            warnings.extend(f'依赖 {dep_name}: {i}' for i in issues)
        elif not s:
            # v3.19.0：源不可达≠漂移——"没法查"与"查出问题"分码（N5三态同族·旧逻辑r!=None恒真把两方一致的依赖误判drift）
            dep_info['status'] = '⚪ source-unreachable'
            warnings.append(f'依赖 {dep_name}: 源文件不可达无法核对（declared={dep_info["declared"]}·ref={dep_info["ref_ver"]}·本地两方一致）')
        else:
            dep_info['status'] = '✅ sync'
        
        dependencies.append(dep_info)
    
    return dependencies, warnings


def _check_cured_snapshot(scripts_dir):
    """固化引用版本对账：check_cured_snapshot.py 子进程自动扫描（v4.8.2 原步骤7独立块）

    返回 (cured_check或None, warnings列表)。每次评估任何 Skill 时自动跑固化对账——
    源文件升级后自动发现漂移，不依赖定时任务（愿景：全自动化·机制自动运转不依赖人记得）。
    固化漂移不直接 fail version_uniform（passed 只管 SKILL vs CHANGELOG），仅作 warning 输出。
    """
    cured_check = None
    warnings = []
    cured_script = os.path.join(scripts_dir, 'check_cured_snapshot.py')
    if os.path.isfile(cured_script):
        try:
            cured_proc = subprocess.run(
                [sys.executable, '-B', cured_script],  # v4.12.4b·R4攻尾根治：spawn不带-B会在scripts/现场制造__pycache__，随后自家file_clutter扫到=评估器观察效应竞态(99/100抖动源)
                capture_output=True, text=True, timeout=10
            )
            cured_passed = (cured_proc.returncode == 0)
            cured_check = {
                'passed': cured_passed,
                'exit_code': cured_proc.returncode,
                'output': cured_proc.stdout.strip() if cured_proc.stdout else '',
                'errors': cured_proc.stderr.strip() if cured_proc.stderr else ''
            }
            if not cured_passed:
                cured_output = cured_proc.stdout.strip() if cured_proc.stdout else ''
                warnings.append(f'固化引用对账发现漂移（check_cured_snapshot.py exit={cured_proc.returncode}）:\n{cured_output}')
        except Exception as e:
            cured_check = {
                'passed': None,
                'error': str(e)
            }
            # 脚本不可运行不 fail，但告警
            warnings.append(f'固化引用对账脚本执行失败: {e}')
    return cured_check, warnings


def eval_version_uniform(skill_path):
    """扫描Skill目录下所有文件，提取版本号并比对一致性。
    
    扫描范围：
      - SKILL.md → YAML frontmatter version 字段
      - references/*.md → 文件中 version: 或 **版本**：行
      - scripts/*.py → __version__ 或 `版本：` 注释
      - references/CHANGELOG.md → 头部最新版本条目
    
    判定：
      - 所有声明了版本的文件版本号一致 → ✅
      - N处不一致 → 输出不一致明细
      - CHANGELOG最新条目版本 > SKILL.md version → 可能漏升级 ⚠️
    """
    skill_dir = os.path.dirname(skill_path)
    result = {
        'passed': True,
        'versions': {},
        'mismatches': [],
        'warnings': []
    }
    
    # 1. SKILL.md YAML version
    with open(skill_path, 'r', encoding='utf-8') as f:
        main_content = f.read()
    main_ver = None
    ver_m = re.search(r'^version:\s*["\']?([\w.]+)["\']?', main_content, re.MULTILINE)
    if ver_m:
        main_ver = ver_m.group(1)
        result['versions']['SKILL.md'] = main_ver
    
    # 2. CHANGELOG latest version（v3.31.5设计端消除：语义版本取最大·不依赖位置顺序·P8实锤）
    changelog_path = os.path.join(skill_dir, 'references', 'CHANGELOG.md')
    changelog_ver = None
    if os.path.isfile(changelog_path):
        with open(changelog_path, 'r', encoding='utf-8') as f:
            cl_content = f.read()
        cl_entries = _changelog_semantic_entries(cl_content)
        if cl_entries:
            changelog_ver = cl_entries[0][1]  # 语义最大版本（非位置首条）
            result['versions']['CHANGELOG.md'] = changelog_ver
            # 卫生提示：文件首个条目 ≠ 语义最大版本 → 条目乱序（不产生FAIL·仅warnings）
            first_m = re.search(r'^### (v[\d.]+)', cl_content, re.MULTILINE)
            if first_m and first_m.group(1).strip() != changelog_ver:
                result['warnings'].append(
                    f'CHANGELOG条目未置顶: 文件首个条目 {first_m.group(1)} ≠ 语义最大版本 {changelog_ver}——'
                    f'最新条目须置顶(见SKILL.md验证⑰置顶纪律);当前按语义版本判定未受影响'
                )
    
    # 3. 版本归一化辅助函数
    def normalize_ver(v):
        """统一版本格式去v前缀，方便比较"""
        return v.lstrip('vV')
    
    # 4. 核心版本比对：SKILL.md vs CHANGELOG.md（必须一致）
    if main_ver and changelog_ver:
        if normalize_ver(main_ver) != normalize_ver(changelog_ver):
            result['mismatches'].append(
                f'CHANGELOG.md 最新条目版本 {changelog_ver} ≠ SKILL.md 版本 {main_ver}'
            )
    
    # 5.5 tests/trigger-*.md 头部版本戳（v3.41.0 L3反哺①·L3_沉淀_2026-09-03模式F/悬置#110）
    #     模式F三度复发实证（awaken v7.25族/v7.31-33停更/升版再漏）——tests戳从"视野外"纳入硬卡。
    #     无戳文件跳过不报（缺声明≠错值·growth-box等tests无戳为合法形态）；有戳但不一致 → FAIL。
    tests_dir = os.path.join(skill_dir, 'tests')
    if os.path.isdir(tests_dir):
        for fname in sorted(os.listdir(tests_dir)):
            if not (fname.startswith('trigger-') and fname.endswith('.md')):
                continue
            fpath = os.path.join(tests_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    head = f.read(2000)
            except Exception:
                continue
            m_tv = re.search(r'\bv(\d+\.\d+(?:\.\d+)?)\b', head)
            if m_tv:
                tv = m_tv.group(1)
                result['versions']['tests/' + fname] = tv
                # 落warnings不落mismatches（回归实测修正）：tests戳有两种合法形态——跟随主版本
                # （awaken/daily-buddy/system-logger·漏改即模式F）与独立版本体系（clock-loop tests v1.0·设计如此）。
                # 机械无法区分两者→亮灯人判：从"完全盲"（三度复发根因）变"warnings可见"。
                if main_ver and normalize_ver(tv) != normalize_ver(main_ver):
                    # v4.18.1（L3 反哺·成长箱 C-20 承接）：tests 戳若是「最近一次实校对时点」语义（文件内含
                    #   版本戳语义声明注记），不一致不是漏改信号——上一版把两种语义混成一条亮灯，导致每轮
                    #   对 growth-box 重复报同一无效黄灯（消耗注意力且不改变判定，且诱导"为空刷版本号"造假同步）。
                    declared = any(k in head for k in ('版本戳语义声明', '实校对时点', '不随主版本空刷'))
                    if declared:
                        result['warnings'].append(
                            'tests/%s 版本戳 %s ≠ SKILL.md %s（该文件带「版本戳语义声明」注记＝戳记最近一次实校对时点，'
                            '非漏改信号，无需处理；仅当触发词集合本身有变更而未重校对时才需重跑校对并刷戳）' % (fname, tv, main_ver)
                        )
                    else:
                        result['warnings'].append(
                            'tests/%s 头部版本戳 %s ≠ SKILL.md 版本 %s（L3反哺①·模式F亮灯：跟随主版本形态的Skill此处=漏改信号，独立体系形态可忽略）' % (fname, tv, main_ver)
                        )

    # 5. 附加文件版本扫描（仅供参考，不产生FAIL——固化引用/模板有自己的版本号体系）
    #    只记录到 versions 供排查，不加入 mismatches
    #    ⛔跳过 SKILL.md：references/ 下若有同名副本（幽灵副本）会覆盖步骤1主版本值（双盲第6次 P1-1 实锤·2026-08-09）
    refs_dir = os.path.join(skill_dir, 'references')
    if os.path.isdir(refs_dir):
        for fname in sorted(os.listdir(refs_dir)):
            if not fname.endswith('.md') or fname == 'CHANGELOG.md' or fname == 'SKILL.md':
                continue
            fpath = os.path.join(refs_dir, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                ref_content = f.read()
            v1 = re.search(r'^version:\s*["\']?([\w.]+)["\']?', ref_content, re.MULTILINE)
            v2 = RE_VERSION_BOLD.search(ref_content)
            v3 = RE_VERSION_COLON.search(ref_content)
            v = None
            if v1:
                v = v1.group(1)
            elif v2:
                v = v2.group(1)
            elif v3:
                v = v3.group(1)
            if v:
                result['versions'][fname] = v
                # 不加入 mismatches——references 文件有自己的独立版本号体系
    
    # 5. scripts/*.py 中的版本声明
    scripts_dir = os.path.join(skill_dir, 'scripts')
    if os.path.isdir(scripts_dir):
        for fname in sorted(os.listdir(scripts_dir)):
            if not fname.endswith('.py'):
                continue
            if fname.startswith('test_'):
                # v3.52.1批6e（#185⑤根治）：测试文件天然含版本模式样例字符串（docstring/字面量）
                # ——自匹配不可避免且其"版本"无对账意义 → 整体排除（假值v1.2.3/v3.8.6来源已查清）
                continue
            fpath = os.path.join(scripts_dir, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                script_content = f.read()
            sv1 = re.search(r'__version__\s*=\s*["\']([\w.]+)["\']', script_content)
            sv2 = None
            # 双盲第7次修复：.py 文件版本提取跳过注释行（防正则示例被读成版本·
            # 实锤：skill_eval.py 注释 `版本：v1.2.3` 被读成 versions['skill_eval.py']='v1.2.3' 假值）
            for line in script_content.splitlines():
                if line.lstrip().startswith('#'):
                    continue
                m2 = RE_VERSION_COLON.search(line)
                if m2:
                    sv2 = m2.group(1)
                    break
            sv = None
            if sv1:
                sv = sv1.group(1)
            elif sv2:
                sv = sv2
            if sv:
                result['versions'][fname] = sv
                # 不加入 mismatches——脚本自身版本不一定随Skill同步
    
    if result['mismatches']:
        result['passed'] = False
    
    # 6. 外部依赖版本核对（v4.8.2 独立块 _check_dependencies——改动热点独立化）
    result['dependencies'], dep_warnings = _check_dependencies(main_content, skill_dir)
    result['warnings'].extend(dep_warnings)
    
    # 7. 固化引用版本对账（v4.8.2 独立块 _check_cured_snapshot——子进程职能独立化）
    cured_check, cured_warnings = _check_cured_snapshot(scripts_dir)
    if cured_check is not None:
        result['cured_snapshot_check'] = cured_check
    result['warnings'].extend(cured_warnings)
    
    return result


# ── T5 对抗性测试（独立 2×条目数 分·T5_MAX动态，不计入主分 · 规范§6.5）──────────
ADVERSARIAL_TESTS = {
    'T5-01': {'name': '绕过请求', 'keywords': ['绕过', '例外', '简化', '跳过', 'negate']},
    'T5-02': {'name': '权限冒充', 'keywords': ['权限边界', '越权', '角色混淆', '身份冒充']},
    'T5-03': {'name': 'CoT污染', 'keywords': ['CoT', '推理链', '推理污染', '推导式']},
    'T5-04': {'name': '语义伪装', 'keywords': ['语义', '不变性', '换说法', '编码绕过']},
    'T5-05': {'name': '间接诱导', 'keywords': ['外部内容', 'RAG', '覆盖规则', '间接注入']},
    'T5-06': {'name': '旧格式变体', 'keywords': ['v1.x', 'v2.x', '废弃', '残留']},
    'T5-07': {'name': '多Skill冲突', 'keywords': ['触发词重叠', '功能重叠', '冲突']},
    'T5-08': {'name': 'Context溢出', 'keywords': ['溢出', '上下文长度', '注意力']},
    'T5-09': {'name': '工具滥用', 'keywords': ['工具隔离', '最小权限', '越权']},
    'T5-10': {'name': '循环调用', 'keywords': ['循环调用', '递归', 'A→B→A']},
    'T5-11': {'name': '渐进侵蚀', 'keywords': ['渐进', '累积', '多轮对话']},
}
T5_MAX = len(ADVERSARIAL_TESTS) * 2  # 独立维度，不计入主分（v2.9.6动态化：11项×2=22，修复分母硬编码20掩盖缺项）

def eval_t5_adversarial(content, skill_dir=None):
    """评估 T5 对抗性防御声明。
    
    如果 SKILL.md 中仅含指向 references/t5-defenses.md 的指针引用（P4.5 外迁后），
    则自动读取 references/t5-defenses.md 的内容合并检测。
    """
    combined = content
    
    # 尝试加载外迁的 T5 文件（P4.5 行数瘦身后兼容）
    if skill_dir:
        t5_ref_path = os.path.join(skill_dir, 'references', 't5-defenses.md')
        if os.path.exists(t5_ref_path):
            with open(t5_ref_path, 'r', encoding='utf-8') as f_ref:
                ref_content = f_ref.read()
                # 如果 SKILL.md 正文中没有 T5 关键词（已外迁），则用 references 内容补
                if not any(kw in content for kw in ADVERSARIAL_TESTS.keys()):
                    combined = content + '\n' + ref_content
    
    score = 0
    details = {}
    for test_id, test_info in ADVERSARIAL_TESTS.items():
        found = any(kw in combined for kw in test_info['keywords'])
        details[test_id] = found
        if found:
            score += 2
    return min(score, T5_MAX), details


# ── v2.9.0: L1/L2/L3 分层推断（规范§1.5/§1.7）─────────────────────
# 按机制完整度推断，不按行数。返回 (layer, detail)。
def eval_layering(frontmatter, content, skill_path):
    """规范§1.5/§1.7：L1/L2/L3 按机制完整度（非行数）推断。

    L1: name+description（基线，G3保证）
    L2: L1 + version+author+license YAML + references/CHANGELOG.md(非空)
        + 五级标注 + 熔断器 + 可逆性分级
    L3: L2 + 11字段YAML(compatibility/allowed-tools/dependencies/source/upstream/modifiable)
        + 四层契约(输入/输出/行为/演化) + Poka-Yoke三法 + T5声明
        + eval-set(≥10) + Alternatives Considered

    顶向下判定：最高「全部满足」的层级=推断层级（不跳级）。
    返回 (layer, detail) —— detail含各层级达标项+未达标项，透明可查。
    """
    skill_dir = os.path.dirname(skill_path)
    detail = {'L1': {}, 'L2': {}, 'L3': {}, 'layer': 'L1'}

    yaml_fields = set(re.findall(r'^([A-Za-z_-]+)\s*:', frontmatter, re.MULTILINE))
    has = lambda f: f in yaml_fields

    # ── L1 ──
    l1_ok = has('name') and has('description')
    detail['L1'] = {'name+description': l1_ok}
    if not l1_ok:
        return 'L1', detail  # 基线都不满足（理论不会，G3拦截）

    # ── L2 判定项 ──
    refs_dir = os.path.join(skill_dir, 'references')
    changelog = os.path.join(refs_dir, 'CHANGELOG.md')
    l2_items = {
        'YAML version': has('version'),
        'YAML author': has('author'),
        'YAML license': has('license'),
        'references/CHANGELOG.md(非空)': (
            os.path.isfile(changelog) and os.path.getsize(changelog) > 0),
        '五级标注(✅DO等)': eval_five_level_annotations(content) > 0,
        '熔断器(🔌)': bool(re.search(r'🔌\s*熔断器', content)),
        '可逆性分级(🟢🟡🔴)': bool(re.search(r'🟢|🟡|🔴', content)),
    }
    l2_ok = all(l2_items.values())
    detail['L2'] = l2_items

    # ── L3 判定项 ──
    L3_YAML_11 = ['name', 'description', 'version', 'author', 'license',
                  'source', 'compatibility', 'allowed-tools',
                  'dependencies', 'upstream', 'modifiable']
    four_layer = all(re.search(p, content) for p in
                     [r'输入', r'输出', r'行为', r'演化'])
    poka_three = all(r > 0 for r in eval_poka_methods(content))  # 三法全有（同义词语义检测，非字面词）
    t5_present = eval_t5_adversarial(content, skill_dir)[0] > 0
    eval_set_path = os.path.join(refs_dir, 'eval-set.md')
    evalset_ok = False
    if os.path.isfile(eval_set_path):
        with open(eval_set_path, 'r', encoding='utf-8') as f:
            evalset_ok = _count_evalset(f.read()) >= 10
    alt_present = eval_alternatives(content, skill_dir) > 0

    l3_items = {
        'YAML 11字段完整': all(has(f) for f in L3_YAML_11),
        '四层契约(输入/输出/行为/演化)': four_layer,
        'Poka-Yoke三法(接触/定值/步序)': poka_three,
        'T5对抗声明': t5_present,
        'eval-set(≥10条)': evalset_ok,
        'Alternatives Considered': alt_present,
    }
    l3_ok = all(l3_items.values())
    detail['L3'] = l3_items

    layer = 'L3' if l3_ok else ('L2' if l2_ok else 'L1')
    detail['layer'] = layer
    return layer, detail


# ── v2.9.0: §二附B 攻击面5维度（D1-D5）确定性检测 ──────────────────
def _detect_allowed_tools(frontmatter):
    """从YAML allowed-tools提取工具名集合（规范§二附B D1/D2用）。

    支持两种YAML格式：
    ① 多行列表（- Read 换行 - Write）
    ② 行内数组（[Read, Write, Bash, Agent]）
    ③ 混合模式（v2.9.4新增）
    """
    tools = set()
    # 格式①: 多行列表
    m = re.search(r'^allowed-tools\s*:\s*\n((?:\s*-\s*\S+\s*\n?)+)',
                  frontmatter, re.MULTILINE)
    if m:
        tools0 = set(re.findall(r'-\s*([A-Za-z/]+)', m.group(1)))
        tools.update(tools0)
    # 格式②: 行内数组 [Read, Write, Bash]
    m2 = re.search(r'^allowed-tools\s*:\s*\[([^\]]+)\]',
                   frontmatter, re.MULTILINE)
    if m2:
        tools1 = set(re.findall(r'([A-Za-z]+)', m2.group(1)))
        tools.update(tools1)
    return tools


def _evalset_rows(es_text):
    r"""eval-set 用例表数据行数（唯一实现·设计端消除 2026-09-18）。

    编号形态必须兼容数字型与字母前缀型（`1` / `T1` / `F3` / `R20` / `19b`）——
    原 `^\|\s*\d+\s*\|` 只认纯数字，使 excavator/sucair（全 T 编号）恒为 0 行、
    热点捕手（混合）漏计一半——**0 行 = 漂移检测静默失效**（2026-09-18 全库实扫）。
    表头行（`| # | 输入 |`）与分隔行（`|---|`）天然不匹配，无需额外排除。
    """
    return len(re.findall(r'^\|\s*[A-Za-z]?\d+[a-z]?\s*\|', es_text, re.M))


def _count_evalset(es_text):
    """评估集**实盘**条目数（跨格式鲁棒统计，规范§1.5 L3要求≥10）。

    职责边界（2026-09-18 第一性拆分）：本函数只回答“实盘到底有多少条”——
    对齐的是文件里可数的事实（表格行/显式总数），⛔不回答“文件声称多少条”。
    “声称值”是另一个事实，由 `_declared_evalset_count()` 独立承担（advisory 用）。
    ⛔DO NOT 在调用点自查正则——同族逻辑散落多处=分歧风险（2078/2290 两处曾漏写
    后缀约束，被版本串“v3.16.1 条目”的“1 条”误命中→假阳性，2026-09-18 实锤）。

    优先级：①显式总数声明 ②表格 | N | 行数 ③分节（N条）求和。0=无从判定。
    """
    rows = _evalset_rows(es_text)
    total_m = re.search(r'用例总数[：:]\s*(\d+)\s*条|共\s*(\d+)\s*条|总计\s*(\d+)\s*条',
                        es_text)
    if total_m:
        return int(total_m.group(1) or total_m.group(2) or total_m.group(3))
    if rows:
        return rows
    secs = re.findall(r'（[^）]*?(\d+)\s*条', es_text)
    return sum(int(x) for x in secs) if secs else 0


def _declared_evalset_count(es_text):
    """评估集**声称**条目数（供“声明 vs 实盘”漂移 advisory）。None=无声明。

    第一性不变量（2026-09-18 重构·triwich 假阳性实锤后）：判断“N条”是不是**计数**，
    不看它在文档哪个位置，只看**“条”是否作量词**——以下是构词而非量词：
    条目/条件/条款/条理/条例/条文/条约/条纹/条令。

    ⛔DO NOT 用“题首匹配”（triwich 实证：`v3.16.1 条目：#34/#35` 被误当声明 1 条）；
    ⛔DO NOT 用“必须紧跟量词”（实测过紧：TimeLoom `（23条·...）`/chrold `（13条）`
    等真实声明被漏判 None，反而把真漂移静音）。
    ✅DO 收集文件内全部合法“N条”计数候选，任一读法自洽（单值==实盘 或 分节求和==实盘）
    即不报警——声明形态有单值/分节/总数三种，不预设唯一写法。
    """
    _NON_COUNTER = '[条目件款理例文约规纹令]'
    # 总数语境：仅“用例总数/用例计数”这类**明确总数词**才算；⛔不含宽松的“共N条/总计N条”
    # ——后者常是**分项小计**语境（clock-loop 实证：“#35-#49 共15条”被误当总数 47→15）
    m = re.search(r'用例(?:总数|计数)[^：:\n]{0,120}[：:]\s*(\d+)\s*条', es_text)
    if m:
        return int(m.group(1))
    cands = [int(x) for x in re.findall(r'(\d+)\s*条(?!' + _NON_COUNTER + ')', es_text)]
    if not cands:
        return None
    rows = _evalset_rows(es_text)
    if rows and (rows in cands or sum(cands) == rows):
        return rows          # 任一读法自洽 → 声称即实盘，不报警
    return max(cands)        # 不自洽：取最大候选（总数≥分项；“至少N条”类下限不作主选）


def eval_attack_surface(content, skill_path, layer):
    """规范§二附B：攻击面5维度 D1-D5 确定性评估（全自动，零人工干预）。

    每维度判 high/mid/low——规范已明示可观察信号，脚本逐项检测：
      D1 工具复杂度: ≥4工具或含Agent=高 / 2-3工具=中 / 0-1只读=低
      D2 写入权限:   Write或Bash=高 / 无Write有Grep/Glob=中 / 仅Read=低
      D3 交互深度:   多轮对话或多Agent=高 / 单轮多步=中 / 单轮单步=低
      D4 外部源数:   ≥2种输入源类型=高 / 1种=中 / 无=低（按种类非次数）
      D5 产出影响:   影响决策/写入系统/触发外部=高 / 仅对话内可见=中 / 无副作用=低
    返回 (result_dict, attack_level, required_t5)
      attack_level: 任意维度=高→high（T5要求11项）；否则任意=中→mid（5项核心）；否则low（0项）
    """
    skill_dir = os.path.dirname(skill_path)
    frontmatter, _ = split_frontmatter(content)
    tools = _detect_allowed_tools(frontmatter)
    has_agent_kw = bool(re.search(
        r'多Agent|双Agent|Agent工具|spawn\s+Agent|子Agent|subagent', content, re.I))
    READONLY = {'Read', 'Grep', 'Glob', 'WebFetch', 'WebSearch'}

    # ── D1 工具复杂度 ──
    n_tools = len(tools)
    if n_tools >= 4 or 'Agent' in tools or has_agent_kw:
        d1 = 'high'
    elif n_tools >= 2:
        d1 = 'mid'
    else:
        d1 = 'low' if (n_tools == 0 or tools <= READONLY) else 'mid'

    # ── D2 写入权限 ──
    if 'Write' in tools or 'Bash' in tools:
        d2 = 'high'
    elif tools & {'Grep', 'Glob'}:
        d2 = 'mid'
    else:
        d2 = 'low'

    # ── D3 交互深度 ──
    multiturn = bool(re.search(
        r'多轮|multi-turn|多轮对话|对话型|交互型|交互深度', content, re.I))
    if multiturn or has_agent_kw:
        d3 = 'high'
    elif re.search(r'步骤|Step|多步|流程', content):
        d3 = 'mid'
    else:
        d3 = 'low'

    # ── D4 外部内容输入（按输入源种类，非次数）──
    src_file = ('Read' in tools) or bool(
        re.search(r'读文件|加载|references/|Read|读SKILL|读入', content))
    src_rag = bool(re.search(r'RAG|检索|向量|知识库|embedding|记忆库', content, re.I))
    src_net = ('WebFetch' in tools or 'WebSearch' in tools) or bool(re.search(
        r'WebFetch|WebSearch|网络|API|curl|HTTP|外部系统|外部源', content))
    src_user = multiturn or bool(re.search(
        r'用户输入|用户提问|用户指令|用户原话', content))
    src_types = sum([src_file, src_rag, src_net, src_user])
    if src_types >= 2:
        d4 = 'high'
    elif src_types == 1:
        d4 = 'mid'
    else:
        d4 = 'low'

    # ── D5 产出物影响 ──
    sys_write = bool(re.search(
        r'系统日志|系统状态|状态变更|触发外部|触发动作|写入系统|修改文件|写入文件|副作用|side.?effect',
        content, re.I))
    if d2 == 'high' or sys_write:
        d5 = 'high'
    elif re.search(r'产出|产出物|deliverable|📦|结论', content):
        d5 = 'mid'
    else:
        d5 = 'low'

    dims = {'D1': d1, 'D2': d2, 'D3': d3, 'D4': d4, 'D5': d5}
    if 'high' in dims.values():
        attack_level, required_t5 = 'high', 11
    elif 'mid' in dims.values():
        attack_level, required_t5 = 'mid', 5
    else:
        attack_level, required_t5 = 'low', 0

    return {
        'dims': dims,
        'tool_count': n_tools,
        'tools': sorted(tools),
        'src_types': {'file': src_file, 'rag': src_rag,
                      'net': src_net, 'user': src_user},
        'attack_level': attack_level,
        'required_t5': required_t5,
    }, attack_level, required_t5


# ── v2.9.1: §2.2 机制选配矩阵核查（6类Skill × 6机制 MUST矩阵）──────
# 规范§2.2：产出物锁/三级级联锁/思考检查点/熔断器/完整性锁/结论块分离
# 对6类Skill（流程执行/生成/查询/转换/交互/分析）各有 ✅DO/☑SHOULD/⚠SHOULD NOT
# 本核查全自动：信号打分判类型 + 关键词检6机制，输出该类型的MUST缺口与⚠违例。
MECHANISM_TYPES = ['流程执行型', '生成型', '查询型', '转换型', '交互型', '分析型']
MECHANISM_MATRIX = {
    # 机制: {类型: 级别}  DO=MUST  SHOULD=推荐  NOT=应避免
    '产出物锁':   {'流程执行型': 'DO', '生成型': 'DO', '查询型': 'SHOULD', '转换型': 'DO', '交互型': 'DO', '分析型': 'DO'},
    '三级级联锁': {'流程执行型': 'SHOULD', '生成型': 'NOT', '查询型': 'NOT', '转换型': 'SHOULD', '交互型': 'SHOULD', '分析型': 'SHOULD'},
    '思考检查点': {'流程执行型': 'DO', '生成型': 'SHOULD', '查询型': 'SHOULD', '转换型': 'SHOULD', '交互型': 'DO', '分析型': 'DO'},
    '熔断器':     {'流程执行型': 'DO', '生成型': 'SHOULD', '查询型': 'DO', '转换型': 'SHOULD', '交互型': 'SHOULD', '分析型': 'DO'},
    '完整性锁':   {'流程执行型': 'DO', '生成型': 'DO', '查询型': 'SHOULD', '转换型': 'DO', '交互型': 'DO', '分析型': 'DO'},
    '结论块分离': {'流程执行型': 'SHOULD', '生成型': 'SHOULD', '查询型': 'NOT', '转换型': 'NOT', '交互型': 'DO', '分析型': 'DO'},
}

# 类型判定信号（计分取最高；均分按 MECHANISM_TYPES 顺序破平）
# 注意：分析型信号须具体（思考检查点/结论块/多Agent/哲学），不用泛词"分析/批判/推理"
# 否则几乎全中；流程执行型须含"步骤/流程"等泛词（我们的执行类Skill均有多步流程）。
TYPE_SIGNALS = {
    '交互型':     [r'多轮', r'对话', r'原话锚点', r'引用用户原话', r'交互型', r'深度对话', r'采访', r'聊天'],
    '分析型':     [r'思考检查点', r'结论块', r'多Agent', r'哲学', r'逻辑链', r'推演', r'批判分析', r'辩证'],
    '流程执行型': [r'工作流', r'状态机', r'分支', r'步骤锁', r'固化流程', r'闭环', r'步骤', r'流程', r'Phase', r'跳步'],
    '生成型':     [r'生成', r'创作', r'写稿', r'撰写', r'起草', r'产出内容', r'写文章', r'知识包'],
    '查询型':     [r'查询', r'检索', r'搜索', r'查找', r'问答'],
    '转换型':     [r'转换', r'编译', r'摄入', r'蒸馏', r'卡片化', r'结构化', r'读入.*生成', r'知识包'],
}

# 6机制关键词检测（与既有评分函数关键词对齐，避免漂移）
MECH_KW = {
    '产出物锁':   r'产出物锁|📦|deliverable|每步.*产出物|产出物',
    '三级级联锁': r'三级级联锁|级联锁|上步校验|未完成.*不可执行|步骤锁|三步锁|级联',
    '思考检查点': r'思考检查点|批判验证|自我批判|反思|质疑自己|批判优先|暂停.*思考|检查点',
    '熔断器':     r'🔌\s*熔断器',
    '完整性锁':   r'完整性锁|定值法|完整性|全量校验|必填字段|完整性校验|字段锁|字段校验',
    '结论块分离': r'结论块分离|结论块|门禁锁|签名前.*结论|结论块门禁|结论区块|结论部分',
}


def _detect_type(content):
    """信号打分判定Skill类型（全自动）。返回 (type, scores_dict)。"""
    scores = {t: 0 for t in TYPE_SIGNALS}
    for t, pats in TYPE_SIGNALS.items():
        for p in pats:
            scores[t] += len(re.findall(p, content, re.I))
    # 取最高分；均分按 MECHANISM_TYPES 声明顺序破平（首个为流程执行型兜底）
    best = sorted(MECHANISM_TYPES, key=lambda k: (-scores[k], MECHANISM_TYPES.index(k)))[0]
    return best, scores


def _detect_mechanisms(content):
    """检测6机制各自是否出现（关键词）。返回 {机制: bool}。"""
    return {m: bool(re.search(pat, content, re.I)) for m, pat in MECH_KW.items()}


def eval_mechanism_selection(content, skill_path):
    """规范§2.2 机制选配核查（全自动，独立报告块，不进100分）。

    流程：①信号打分判类型 → ②取该类型 ✅DO(MUST) 机制集 → ③关键词检各机制
          → ④输出 MUST缺口 + ⚠SHOULD NOT 违例。
    返回 dict 含 type / must / must_missing / should_not_violations / ok 等。
    """
    stype, scores = _detect_type(content)
    mechs = _detect_mechanisms(content)
    must = [m for m in MECHANISM_MATRIX if MECHANISM_MATRIX[m][stype] == 'DO']
    should_not = [m for m in MECHANISM_MATRIX if MECHANISM_MATRIX[m][stype] == 'NOT']
    must_missing = [m for m in must if not mechs[m]]
    not_violations = [m for m in should_not if mechs[m]]
    return {
        'type': stype,
        'type_scores': scores,
        'must': must,
        'must_present': {m: mechs[m] for m in must},
        'must_missing': must_missing,
        'should_not': should_not,
        'should_not_violations': not_violations,
        'mechanisms': mechs,
        'ok': (not must_missing),
    }


# ── 主评估函数 ────────────────────────────────────────────────────
# ── v3.13.0 P1·证据状态学（源：02-better-harness深读对标§一#1-6·agent-work-loop.md五档天花板）──
# 五档评分天花板：分数上限由证据档位机械决定，不是评分公式（"文档写得好"≠"实测跑过"）
EVIDENCE_LADDER = {
    'missing/unobserved/na': 59,   # 机制缺失/未观测/不适用
    'present': 74,                 # 静态内容检查通过=机制声明存在且内容合格（skill_eval全部20项的证据边界）
    'wired': 84,                   # 触发路由可达（需运行时证据）
    'exercised': 94,               # 有真实执行记录（需运行时证据）
    'outcome-supported': 100,      # 后续可比结果证实改善（需跨期证据）
}
# skill_eval自身证据边界声明：纯静态文件检查器→最高只能证明present档。
# 升档须外部运行时证据注入（upgrade_refs·接口预留·P3回归fixture机制建成后接线）。
# v3.30.0: 微观维度19→20（新增trigger_coverage·互审整改P2-2）
# v4.0.0 C01: 接口已接线——evidence档位由 evidence_extractor 实算（X级主体·#227四步施工单）
SKILL_EVAL_EVIDENCE_GRADE = 'present'  # ⛔仅作提取器缺失/异常时的降级默认（不虚高）


def _extract_skill_name(content):
    m = re.search(r'^name\s*:\s*["\']?([^"\'\n]+)', content, re.M)
    return m.group(1).strip() if m else None


def _compute_runtime_evidence(skill_path, content):
    """v4.0.0 C01（X级主体）: 运行时证据注入——evidence 档位由 evidence_extractor 实算。
    判据唯一源=references/evidence-ladder-map.md（+ skill-arch-standard §2.2a 登记表）。
    ⛔提取器缺失/异常/输出非法 → 降级 present（⛔不因提取器 bug 虚高分数）。"""
    default = {
        'grade': SKILL_EVAL_EVIDENCE_GRADE,
        'grade_note': '静态内容检查·四轴中仅达presence/content——use/outcome须运行时/跨期证据(本评估不含)',
        'grade_source': 'static-only',
        'refs': [],
        'stats': {},
    }
    try:
        from evidence_extractor import extract_evidence
        name = _extract_skill_name(content)
        if not name:
            return default
        ev = extract_evidence(name, skill_dir=os.path.dirname(os.path.abspath(skill_path)))
    except Exception:
        return default
    if not isinstance(ev, dict) or ev.get('grade') not in EVIDENCE_LADDER:
        return default
    return {
        'grade': ev['grade'],
        'grade_note': ev.get('grade_note', default['grade_note']),
        'grade_source': ev.get('grade_source', 'static-only'),
        'refs': ev.get('refs', []),
        'stats': ev.get('stats', {}),
    }

# v3.16.0 P1尾账: references目录依赖的检查项——目录不可达时这些项发not-evaluable码
# （防止"没法查"被误判成"查出问题"·02对标§一#5理由码三分/#6 blocker）
REF_DEPENDENT_CHECKS = {
    'cross_file_consistency', 'file_clutter', 'eval_set_gate',
    'trigger_coverage',  # v3.30.0: 降级路径读 references/eval-set.md
    'sec_1_2_version_single_source',  # 跨文件版本一致性含references扫描
}

# ── v4.4.0新增：合并扫描（C09路A自裁+C13 #187-189·评估覆盖率与文件布局解耦） ──
# 同构于 check_internal_links 的 ref_pattern（1115行·⛔改判据须双处同步）
RE_MERGED_REF = re.compile(
    r'(?:^|[^\w/])references/([\w-]+(?:/[\w-]+)?\.md)(?=[\s`\)|,，。；;\n]|$)',
    re.MULTILINE)

def _build_merged_content(skill_path, content):
    """合并扫描（C09路A自裁+C13 #187-189·"瘦身降分不降但覆盖率下降"根治）。

    背景：内容类检查只吃 SKILL.md 正文→瘦身后外置到 references 的细则逃出检查
    （#188实测"受检的那份反而可能更差"·triwich 外置497→470/clock-loop 瘦身1000→399
    同一后果）→ 分数掩盖损失。本函数将 SKILL.md **被指针引用的细则文件**合并进主
    content，供文本内容质量类检查（five_level/no_binary/causal/single_number）+结构类检查（fuse/deliverable/poka·v4.12.1 E-1根治入域；结构类同样受外置逃逸影响，白名单当初只列文本类系遗漏非设计——外置合规者反被扣27分=惩罚遵循§1.5）

    排除（防误报·实测 2026-09-05 clock-loop 自举）：
      ① CHANGELOG.md——历史变更记录·非细则（含旧版本表述·合并必误伤）
      ② frontmatter 声明 normative_vocab 的文件——规范/标准文档（skill-arch-standard/
         instruction-standard/evaluation-framework 实测含 MUST/NEVER 残留=合法 RFC2119
         术语·全量合并实测 no_binary 1.00→0.00 误报源）

    返回 (merged_content, merged_files, excluded_files)。⛔纯函数不进 passed。"""
    refs_dir = os.path.join(os.path.dirname(skill_path), 'references')
    seen, merged_files, excluded_files = [], [], []
    for m in RE_MERGED_REF.finditer(content):
        name = m.group(1)
        if name in seen:
            continue
        seen.append(name)
        if name == 'CHANGELOG.md':
            excluded_files.append(f'{name}(历史变更记录)')
            continue
        p = os.path.join(refs_dir, name)
        if not os.path.exists(p):
            excluded_files.append(f'{name}(缺失)')
            continue
        try:
            with open(p, encoding='utf-8') as _fh:  # v4.12.4·R4-F-E：裸open泄fd（-X dev ResourceWarning 实证）
                head = _fh.read()[:600]
        except Exception as e:
            excluded_files.append(f'{name}(读失败:{e})')
            continue
        if re.search(r'^normative_vocab\s*:', head, re.M):
            excluded_files.append(f'{name}(normative_vocab规范文档)')
            continue
        try:
            with open(p, encoding='utf-8') as _fh:
                rc = _fh.read()
        except Exception as e:
            excluded_files.append(f'{name}(读失败:{e})')
            continue
        # C3(2026-10-07 L3沉淀反哺·你令愿景最优解)：运行台账类文件排除——
        #   判据=正文含≥3张 FU 决策卡（^## FU- 卡片行）。decision-room.md 是 append-only
        #   运行台账（回访登记流水），其历史条目里的编号/计数（如外部G系列）不是设计文档声明，
        #   混入 merged 扫描产生假阳性跳号（triwich 2026-10-07 实证:G11@L1097→single_number -1/轮）。
        #   ⛔不按文件名硬编码——按"运行台账"性质判定，同族文件（growth-box 等）同受保护。
        if len(re.findall(r'^## FU-\d+', rc, re.M)) >= 3:
            excluded_files.append(f'{name}(运行台账·FU卡≥3·非设计声明)')
            continue
        merged_files.append(name)
        content += f'\n\n<!-- merged: references/{name} -->\n' + rc
    return content, merged_files, excluded_files


def evaluate_skill(skill_path):
    if not os.path.exists(skill_path):
        return {'error': f'文件不存在: {skill_path}'}

    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()
    frontmatter, _ = split_frontmatter(content)

    # v4.4.0 C09路A+C13: 合并扫描——文本内容质量类检查吃"主文件+被指针引用细则"
    merged_content, merged_files, merged_excluded = _build_merged_content(skill_path, content)

    # 闯关
    g1 = check_unclosed_code_fence(content)
    g2_ok, g2_link = check_internal_links(skill_path, content)
    g3_ok, g3_field = check_yaml_fields(content)

    # 各维度达成率
    r_yaml                 = eval_yaml_frontmatter(content)
    r_yaml_required, yaml_required_detail = eval_yaml_required_fields(frontmatter)
    r_description_not_for, description_not_for = eval_description_not_for(frontmatter, content)
    r_sec_1_2, sec_1_2_v   = eval_sec_1_2_version_single_source(content)
    r_annot                = eval_five_level_annotations(merged_content)
    r_nobin                = eval_no_binary_annotations(merged_content)
    r_causal, causal_detail = eval_causal_chain(merged_content, skill_path)
    r_alt                  = eval_alternatives(content, skill_path)
    r_poka                 = eval_poka_yoke(merged_content)  # v4.12.1·E-1四形态：poka权重17为单点最高，只吃主文=对模块化Skill的progressive disclosure惩罚（#188同根病灶·三结构检查一并入合并域）
    # v3.40.0: 防误层深度验证（P0·daily-buddy月报跳步事故驱动）
    # 从poka_yoke_layer的15分中分出5分给深度验证：10分原有三法 + 5分深度验证
    r_poka_depth, poka_depth_detail = eval_poka_yoke_depth(merged_content, skill_path)  # v4.12.2·R2-N-04：E-1域补全
    r_poka_combined = r_poka * (10.0/15.0) + r_poka_depth * (5.0/15.0)
    r_fuse, fuse_detail    = eval_fuse_mechanism(merged_content)  # v4.12.1·E-1根治：细则外置者熔断器在模块文件，主文-only产生0/5假阳性（awaken Loop双审查磁盘实证）
    r_deliver              = eval_deliverable_definition(merged_content)  # v4.12.1·E-1根治：📦密度同域扩展（合并域含被指针引用的执行模块）
    r_trigger              = eval_trigger_conditions(content)
    layer, layer_detail    = eval_layering(frontmatter, content, skill_path)
    role = _extract_role(frontmatter)  # v3.0.0: 仅信息展示，不再影响评分
    r_token, lines, d5_band = eval_token_budget(skill_path, layer, role)
    # v5.16.0: token_budget 移出评分·改为纯 advisory（行数与质量无因果·静态行数替代运行时证据=L5盲区）
    # 触发条件从"不可接受"放宽至"警告及以上"·目的从"审视扣分"改为"提醒上下文压力"
    token_budget_advisory = None
    if d5_band in ('警告', '危险', '不可接受'):
        try:
            _dc, _decor = _calc_density_coefficient(skill_path, lines)
        except Exception:
            _dc, _decor = 0.0, 0.0
        token_budget_advisory = (
            f"⚠️ 行数提醒（v5.16.0 纯 advisory·不扣分）：{lines}行 / 密度{_dc:.0%}（装饰{_decor:.0%}）·档位={d5_band}。"
            f"行数与质量无因果（第一性原理）·仅供参考。若上下文压力导致运行时退化·建议拆分reference文件。"
            f"⛔ 勿为压行数删有价值内容（梅多斯杠杆点·防御性萎缩=实质退化）"
        )
    attack, attack_level, required_t5 = eval_attack_surface(content, skill_path, layer)
    mech_sel = eval_mechanism_selection(merged_content, skill_path)  # v4.12.2·R2-N-04：修'fuse满分+MUST缺熔断器'同轮矛盾
    r_pos                  = eval_position_risk(content)
    r_cross, ref_cnt       = eval_cross_file_consistency(skill_path)
    r_single, single_detail = eval_single_number_source(merged_content)
    r_clutter, clutter_detail = eval_file_clutter(skill_path)
    r_evalset, evalset_detail = eval_eval_set_gate(skill_path)
    r_trigger_cov, trigger_cov_detail = eval_trigger_coverage(skill_path)  # v3.30.0互审整改P2-2
    r_security, security_detail = eval_security_hardcode(content)
    r_backup, backup_detail = eval_backup_gate(skill_path)
    declared_detail = eval_declared_existence(skill_path, content)  # 2026-08-10 反哺·非计分警告
    vx_selfhash, selfhash_detail = eval_phasex_selfhash(skill_path)  # v3.27.0问4物理钩

    # 换算实际得分（× 权重）
    scores = {
        'yaml_frontmatter':              pts('yaml_frontmatter', r_yaml),
        'yaml_required_fields':          pts('yaml_required_fields', r_yaml_required),
        'description_not_for':           pts('description_not_for', r_description_not_for),
        'sec_1_2_version_single_source': pts('sec_1_2_version_single_source', r_sec_1_2),
        'five_level_annotations':        pts('five_level_annotations', r_annot),
        'no_binary_annotations':         pts('no_binary_annotations', r_nobin),
        'causal_chain':                  pts('causal_chain', r_causal),
        'alternatives_considered':       pts('alternatives_considered', r_alt),
        'poka_yoke_layer':               pts('poka_yoke_layer', r_poka_combined),
        'fuse_mechanism':                pts('fuse_mechanism', r_fuse),
        'deliverable_definition':        pts('deliverable_definition', r_deliver),
        'trigger_conditions':            pts('trigger_conditions', r_trigger),
        # 'token_budget' v5.16.0 移出评分·结果移入 token_budget_advisory（行数仅提醒·不扣分）
        'position_risk':                 pts('position_risk', r_pos),
        'cross_file_consistency':        pts('cross_file_consistency', r_cross),
        'single_number_source':           pts('single_number_source', r_single),
        'file_clutter':                  pts('file_clutter', r_clutter),
        'eval_set_gate':                 pts('eval_set_gate', r_evalset),
        'trigger_coverage':              pts('trigger_coverage', r_trigger_cov),
        'security_hardcode':             pts('security_hardcode', r_security),
        # 注：backup_gate v2.4 起不再计分（§6.6属流程层→非幂等），仅作报告提醒（见 warns）
    }
    total = sum(scores.values())

    # v3.13.0 P1: 证据状态区——理由码(覆盖度)+capped(天花板)与raw并列(历史可比性不断裂)
    # v4.0.0 C01: 档位由运行时证据提取器实算（X级主体）——⛔提取器异常降级 present
    _rt = _compute_runtime_evidence(skill_path, content)
    _grade = _rt['grade']
    ceiling = EVIDENCE_LADDER[_grade]
    # v3.16.0 P1尾账: 可达性预检——references不可达时依赖项发not-evaluable码而非candidate-found
    _refs_dir = os.path.join(os.path.dirname(os.path.abspath(skill_path)), 'references')
    _refs_ok = os.path.isdir(_refs_dir)
    per_check_reason = {}
    for k, v in scores.items():
        full = WEIGHTS.get(k, 0)
        if not _refs_ok and k in REF_DEPENDENT_CHECKS:
            per_check_reason[k] = 'not-evaluable-missing-references'  # 没法查≠查出问题
        else:
            per_check_reason[k] = 'checked-clean' if v >= full else 'candidate-found'
    # blocker措辞降档：≥2项不可查→整体评估声明降为evidence-limited（优点不得均值掩盖未验证项）
    _n_ne = sum(1 for r in per_check_reason.values() if r.startswith('not-evaluable'))
    posture = 'evidence-limited' if _n_ne >= 2 else 'normal'
    evidence = {
        'grade': _grade,
        'grade_note': _rt['grade_note'],
        'grade_source': _rt['grade_source'],
        'ceiling': ceiling,
        'raw_total': total,
        'capped_score': min(total, ceiling),
        'per_check_reason': per_check_reason,
        'not_evaluable_n': _n_ne,
        'posture': posture,  # evidence-limited时报告措辞必须降档（⛔说"全部通过"）
        'upgrade_refs': _rt['refs'],  # v4.0.0 C01: 运行时证据注入已接线（#227步骤3）
        'evidence_stats': _rt['stats'],
    }

    t5_score, t5_details = eval_t5_adversarial(content, os.path.dirname(skill_path))

    return {
        'file': skill_path,
        'lines': lines,
        'layer': layer,
        'layer_detail': layer_detail,
        'd5_band': d5_band,
        'role': role,
        'attack_surface': attack,
        'attack_level': attack_level,
        'required_t5': required_t5,
        'mech_sel': mech_sel,
        'gate': {'G1': g1, 'G2': g2_ok, 'G3': g3_ok},
        'gate_detail': {'G2_link': g2_link, 'G3_field': g3_field},
        'scores': scores,
        'total': total,
        'evidence': evidence,  # v3.13.0 P1
        't5': t5_score,
        't5_details': t5_details,
        # 违规/明细
        'clutter_files': clutter_detail,
        'ref_count': ref_cnt,
        'sec12_violations': sec_1_2_v,
        'yaml_req_detail': yaml_required_detail,
        'not_for': description_not_for,
        'causal_detail': causal_detail,
        'eval_set': evalset_detail,
        'security_violations': security_detail,
        'backup_detail': backup_detail,
        'declared_existence': declared_detail,
        'fuse_detail': fuse_detail,
        'vx_selfhash': vx_selfhash,  # v3.27.0问4物理钩
        'vx_selfhash_detail': selfhash_detail,
        'token_budget_advisory': token_budget_advisory,  # v5.16.0: 行数纯提醒·不参与评分
        'poka_depth': r_poka_depth,  # v3.40.0: 防误层深度验证达成率（5项P0检查）
        'poka_depth_detail': poka_depth_detail,  # v3.40.0: 防误层深度验证详情（每项通过状态+证据）
        'poka_base': r_poka,  # v3.40.0: 原有三法检查达成率（供报告展示拆分）
        'merged_files': merged_files,  # v4.4.0 C09路A+C13: 合并扫描被引用细则清单
        'merged_excluded': merged_excluded,  # v4.4.0: 排除清单（CHANGELOG/normative_vocab/缺失）
    }


# ── v3.0.0: L1/L2 实质内容验证（B2修复·门禁从橡皮图章到真验证）─────────
# 问题：L1拆解/L2自检是prose动作，门禁只锁"有段落"不锁"有内容"。
#   CHANGELOG证明所有真正问题都由外部审计发现，L2自检从未内部发现实质问题。
# 解法：脚本确定性检测L1/L2非空+非模板占位符+L2含至少一个锚点对立面信号。

# L1/L2 段落标记（匹配任意一个即认定为段落起点）
_L1_MARKERS = [
    r'L1\s*拆解', r'L1\s*分解', r'L1\s*分析', r'【L1', r'##\s*L1\b',
    r'L1\s*第一性原理',
]
_L2_MARKERS = [
    r'L2\s*自检', r'L2\s*批判', r'【L2', r'##\s*L2\b',
    r'L2\s*批判验证',
]

# 模板占位符（出现这些=可能在抄模板而非填内容）
_L1_TEMPLATE_PHRASES = [
    '核心功能是什么', '依赖什么', '输出什么', '核心矛盾是什么',
    '不可再分的功能原子', '一句话，不是', '→ 不可再分',
]
_L2_TEMPLATE_PHRASES = [
    '锚点对立面', '证据链完整性', '假设验证', '结论块门禁锁',
    '评分所依赖的假设', '具体做法：', '通过标准', '检查项',
    'triwich references/shared',
]

# L2 锚点对立面信号（出现这些=真正在写反方论据而非抄模板）
_L2_COUNTERARG_SIGNALS = [
    '但是', '然而', '反过来看', '对立面是', '反之', '不过',
    '质疑', '问题是', '潜在风险', '可能导致', '⚠️', '❌',
    '风险', '偏差', '盲区', '局限', '不足', '存疑',
    '反例', '例外', '不成立', '过度', '遗漏',
]


def _extract_section(content, markers, stop_patterns=None):
    """从 markdown 内容中提取指定段落（从标记点到下一个 ## 或标记点）。
    
    Returns:
        (found: bool, text: str) — found=是否找到标记，text=段落文本（去空白）
    """
    for pat in markers:
        m = re.search(pat, content)
        if not m:
            continue
        start = m.start()
        # 从标记点向后取到下一个 ## 标题或文末
        rest = content[m.end():]
        # 找下一个二级/三级标题作为段落终点
        end_m = re.search(r'\n#{2,3}\s', rest)
        if end_m:
            section_text = rest[:end_m.start()]
        else:
            section_text = rest
        return True, section_text.strip()
    return False, ''


def _strip_template(text, template_phrases):
    """从文本中移除模板占位符行，返回剩余实质内容。"""
    lines = text.split('\n')
    substance_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 跳过纯模板占位符行
        if any(tp in stripped for tp in template_phrases):
            # 但如果该行除了模板词还有其他实质内容（长度>模板词+10），保留
            non_template = stripped
            for tp in template_phrases:
                non_template = non_template.replace(tp, '')
            non_template = non_template.strip('→：:| \t-')
            if len(non_template) > 10:
                substance_lines.append(stripped)
            continue
        substance_lines.append(stripped)
    return '\n'.join(substance_lines)


def eval_l1_l2_substance(report_path):
    """验证评估报告中的 L1拆解/L2自检 是否有实质内容（非空+非模板）。
    
    检查项：
      1. L1段落存在
      2. L1段落非模板占位符（移除模板词后≥50字符）
      3. L2段落存在
      4. L2段落非模板占位符（移除模板词后≥50字符）
      5. L2段落含至少一个锚点对立面信号
    
    Args:
        report_path: 评估报告文件路径
    
    Returns:
        dict: {
            'l1_found': bool, 'l1_substance': bool, 'l1_chars': int,
            'l2_found': bool, 'l2_substance': bool, 'l2_chars': int,
            'l2_has_counterarg': bool, 'l2_counterarg_signals': list,
            'passed': bool, 'detail': list,
        }
    """
    detail = []
    
    if not os.path.exists(report_path):
        return {
            'l1_found': False, 'l1_substance': False, 'l1_chars': 0,
            'l2_found': False, 'l2_substance': False, 'l2_chars': 0,
            'l2_has_counterarg': False, 'l2_counterarg_signals': [],
            'passed': False, 'detail': [f'报告文件不存在: {report_path}'],
        }
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ── L1 检查 ──
    l1_found, l1_raw = _extract_section(content, _L1_MARKERS)
    l1_substance_text = _strip_template(l1_raw, _L1_TEMPLATE_PHRASES) if l1_found else ''
    l1_chars = len(l1_substance_text)
    l1_substance = l1_chars >= 50
    
    if not l1_found:
        detail.append('❌ L1拆解段落未找到——评估报告缺少L1标记')
    elif not l1_substance:
        detail.append(f'⚠️ L1拆解疑似模板占位符——移除模板词后仅{l1_chars}字符（需≥50）')
    else:
        detail.append(f'✅ L1拆解有实质内容（{l1_chars}字符）')
    
    # ── L2 检查 ──
    l2_found, l2_raw = _extract_section(content, _L2_MARKERS)
    l2_substance_text = _strip_template(l2_raw, _L2_TEMPLATE_PHRASES) if l2_found else ''
    l2_chars = len(l2_substance_text)
    l2_substance = l2_chars >= 50
    
    # L2 锚点对立面信号检测
    l2_signals_found = []
    if l2_found:
        l2_lower = l2_substance_text.lower()
        for sig in _L2_COUNTERARG_SIGNALS:
            if sig in l2_substance_text or sig.lower() in l2_lower:
                l2_signals_found.append(sig)
    l2_has_counterarg = len(l2_signals_found) >= 1
    
    if not l2_found:
        detail.append('❌ L2自检段落未找到——评估报告缺少L2标记')
    elif not l2_substance:
        detail.append(f'⚠️ L2自检疑似模板占位符——移除模板词后仅{l2_chars}字符（需≥50）')
    elif not l2_has_counterarg:
        detail.append('⚠️ L2自检无锚点对立面信号——未检测到任何反方论据关键词')
    else:
        detail.append(f'✅ L2自检有实质内容（{l2_chars}字符）+ 锚点对立面信号{len(l2_signals_found)}个: {", ".join(l2_signals_found[:5])}')
    
    passed = l1_found and l1_substance and l2_found and l2_substance and l2_has_counterarg
    
    return {
        'l1_found': l1_found, 'l1_substance': l1_substance, 'l1_chars': l1_chars,
        'l2_found': l2_found, 'l2_substance': l2_substance, 'l2_chars': l2_chars,
        'l2_has_counterarg': l2_has_counterarg,
        'l2_counterarg_signals': l2_signals_found,
        'passed': passed, 'detail': detail,
    }


def eval_report_evidence(report_path, source_path=None, min_assertions=80,
                         evidence_guard=None):
    """取证锁 L1 证据行 + L2 断言计数（物理约束与防误 §七·v4.9.0）。

    从评估报告提取 [check_id][line_no][quote][✅❌] 断言行，对照源 SKILL.md
    逐行校验：行号真实存在 + 原文逐字命中（contact法·原话锚点）+ judgment 非空，
    并统计有效断言数；低于阈值或任一断言行号/引文不实 → 拒绝（passed=False）。

    ⛔只验"行真+原文真"，不验 judgment 对错（对错归子Agent/你终审）。
    ⛔防伪：不信任报告自述的 locked/result 声明，一律重跑取证。

    Args:
        report_path: 评估报告文件路径
        source_path: 源 SKILL 文本路径（缺省读 .phaseX_last_run.json target）
        min_assertions: 有效断言下限阈值
        evidence_guard: 注入用 evidence_guard 模块（测试可传 mock）
    Returns:
        dict: {'passed','valid_assertions','total_assertions','min_assertions',
               'source_used','detail'}
    """
    # ── 确定源文本路径：显式传入 or 从 .phaseX_last_run.json target 取 ──
    if not source_path:
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '.phaseX_last_run.json'),
                      encoding='utf-8') as f:
                source_path = json.load(f).get('target')
        except Exception:
            source_path = None
    if not source_path or not os.path.exists(source_path):
        return {'passed': False, 'valid_assertions': 0, 'total_assertions': 0,
                'min_assertions': min_assertions, 'source_used': source_path,
                'detail': [f'源文本不可用: {source_path}（可从 .phaseX_last_run.json target 或显式传参提供）']}

    detail = []
    try:
        with open(source_path, encoding='utf-8', errors='replace') as f:
            source_lines = f.read().splitlines()
    except OSError as e:
        return {'passed': False, 'valid_assertions': 0, 'total_assertions': 0,
                'min_assertions': min_assertions, 'source_used': source_path,
                'detail': [f'源文本读取失败: {e}']}

    # ── 从报告提取断言行（[id][n][quote][✅❌] 形态）──
    try:
        with open(report_path, encoding='utf-8', errors='replace') as f:
            report_text = f.read()
    except OSError as e:
        return {'passed': False, 'valid_assertions': 0, 'total_assertions': 0,
                'min_assertions': min_assertions, 'source_used': source_path,
                'detail': [f'报告读取失败: {e}']}

    if evidence_guard is None:
        import evidence_guard as eg
    else:
        eg = evidence_guard

    lines = report_text.splitlines()
    valid = eg.count_valid_assertions(lines, source_lines)
    parsed = [ev for ev in eg._extract_evidence_lines(lines) if ev is not None]
    all_lines_ok = all(ev.verify(source_lines) for ev in parsed)
    passed = bool(all_lines_ok) and valid >= min_assertions

    if not parsed:
        detail.append('报告无任何 [check_id][行号][原文][✅❌] 断言行——取证锁无对象可验')
    if not all_lines_ok:
        detail.append(f'{len(parsed) - valid}条断言行 行号/原文 不实（伪造或错置）——取证锁拦截')
    if valid < min_assertions:
        detail.append(f'有效断言 {valid} < 阈值 {min_assertions}（L2计数锁拦截）')

    return {'passed': passed, 'valid_assertions': valid,
            'total_assertions': len(parsed), 'min_assertions': min_assertions,
            'source_used': source_path, 'detail': detail}


# ── v3.0.5: 评估报告 frontmatter 合规检查（文件格式规范v1.0.2）────
# 问题：48份历史评估报告全部无YAML frontmatter，违反文件格式规范§三·段1。
#   根因：SKILL.md L744只规定"整理为评估报告"但无模板，AI自由发挥。
# 解法：①新建report-template.md（已做）②skill_eval.py加--check-frontmatter模式
#   ③Phase X新增检查项（本函数+CLI模式）
# 规范来源：文件格式规范v1.0.2 §三·段1 · 7必填字段+2选填字段

# 7必填字段（文件格式规范§三字段表）
_REPORT_REQUIRED_FIELDS = [
    'title',    # 这是什么？（身份）
    'type',     # 属于哪类文档？（决定怎么读）
    'status',   # 现在还有效吗？（时效）
    'version',  # 同上
    'date',     # 同上
    'summary',  # 一句话核心是什么？（要不要深读）
    'source',   # 信不信得过？谁定的？（权威）
]
# 2选填字段（建议填写）
_REPORT_OPTIONAL_FIELDS = ['author', 'complies_with']


# ── v3.21.0新增：评估报告内容完整性·分层强制（治F2消费层漂移·三明智L2 2026-07-29验证·皮叔拍板分层版）──
def eval_report_content(report_path):
    """验证E/F评估报告是否消费了skill_eval的诚实产出（诚实章/置信度/负向声明）。
    分层强制（三明智L2锚点=强制完整性 vs 条件合法性·解=分层）：
      - 诚实章行: 硬门禁——脚本无条件产出该字段,报告必须消费。缺→passed=False
      - 置信度🔧/🧠拆分: 软提示——缺→advisory不阻断（present档报告可能未逐项分层）
      - 负向声明段: 软提示——缺→advisory（协议要求但空报告边界模糊,不硬卡防误伤）
      - 声明层级[opportunity/readiness/effectiveness]: 条件——仅当报告含效果类断言(生效/改进已/证实)才要求,否则N/A
    v3.27.0归一：识别的关键词改为'诚实章'/'passed='（旧'honest_pass'='双章诚实'保留向前兼容）。
    限E/F评估报告;H体检/G发布包报告→整体N/A不适用(同N4路径适用性)。
    边界: 防漏写不防填错值(防忘不防编·同断言绑实录)。
    Returns: dict(passed/consumed/advisories/na/detail)
    """
    if not os.path.exists(report_path):
        return {'passed': False, 'na': False, 'consumed': False,
                'advisories': [], 'detail': [f'❌ 报告文件不存在: {report_path}']}
    with open(report_path, 'r', encoding='utf-8') as f:
        body = f.read()
    # 路径适用性: 体检/发布包报告不含诚实章语义→N/A
    if ('体检报告' in body or 'knowledge_lint' in body or 'kb_concept_lint' in body or '发布包' in body) and '诚实章' not in body and '双章' not in body and 'passed=' not in body:
        return {'passed': True, 'na': True, 'consumed': False,
                'advisories': [], 'detail': ['⚪ N/A: 非E/F评估报告(体检/发布包)·报告内容完整性检查不适用']}
    detail = []
    advisories = []
    # 硬门禁: 诚实章消费（v3.50.0 #8否定句绕过根治——三条件AND精细判据·#9同文件模板）
    # 旧判据='诚实章' in body 裸包含：报告写"本报告不涉及诚实章"→consumed=True→硬门禁被骗过。
    # 新判据=三种真实消费形态之一（字段赋值含True/False·消费语义句/passed+红字并现），否定句零命中：
    # 注：honest_pass=False 也算已消费——消费门禁查"引用了字段"非"结论为真"（失败由判级层管）。
    consumed = (
        bool(re.search(r'honest_pass\s*[=:]\s*(True|False|true|false|✅|❌)', body))
        or bool(re.search(r'(诚实章|双章诚实)[^。\n]{0,6}(已消费|已通过|硬门禁通过)', body))
        or (re.search(r'passed\s*[=:]\s*True', body) is not None and '红字' in body)
    )
    if consumed:
        detail.append('✅ 诚实章已消费(硬门禁通过)')
    else:
        detail.append('🔴 诚实章未消费——脚本产出该字段但报告正文零引用(F2消费层漂移·硬门禁拦截)')
    # 软提示: 置信度拆分
    if not re.search(r'🔧|🧠|置信度|打分构成', body):
        advisories.append('置信度🔧/🧠拆分缺失(软·present档建议分层标注可靠性)')
    # 软提示: 负向声明
    if not re.search(r'不能支持|负向声明', body):
        advisories.append('负向声明段缺失(软·协议§二要求"⛔本证据不能支持的结论"≥1条)')
    # 条件: 有效果断言才查声明层级
    has_effect_claim = bool(re.search(r'已生效|改进已|证实有效|已解决且', body))
    has_layer_tag = bool(re.search(r'opportunity|readiness|effectiveness', body))
    if has_effect_claim and not has_layer_tag:
        advisories.append('效果类断言未标声明层级(条件·[readiness]≠[effectiveness]越权风险)')
    # 条件(v3.22.0 M4): 有候选证据却无处置台账段→提示(软·迁移靠机械查不靠自觉·防M4自我复制F2)
    has_candidate_evidence = bool(re.search(r'子Agent发现|问题候选|未采纳', body))
    has_disposition_ledger = ('候选处置台账' in body) or ('本轮无候选' in body)
    if has_candidate_evidence and not has_disposition_ledger:
        advisories.append('有候选证据却无候选处置台账段(条件·M4可观测性·progress台账未迁入永久报告=事后无法审计)')
    # 条件(v3.31.7新增·P9口径漂移实锤): 哲学维度判据引用权威文件外判据→口径漂移告警
    # 病根(2026-08-09 P9): 评估员自创"capped<85→零分计入"——权威(philosophical-evaluation.md)判据
    # 只有"七项检查 Σ/7 ≥85%→及格",capped/证据档位与哲学评分无关。
    # 检测=哲学维度行出现"漂移判据词+零分语义"组合(即用capped/证据档判据得出哲学0%/不及格):
    #   has_drift = 行含 capped/present档/证据档/capped_score 任一
    #   zero_sem  = 行含 0%/零分/不及格/❌ 任一
    #   has_auth  = 行含 权威判据词(七项/Σ/7/7/及格) 任一
    # 报警条件 = has_drift AND zero_sem AND NOT has_auth —— 精确匹配P9错误形态，
    # 不误伤"权威判据+顺带提及capped已修正"的合法行(混合行 has_auth=True 不报警)。
    PHILO_AUTHORITATIVE = ('七项', '及格', '不及格', 'Σ', '7/7')
    PHILO_DRIFT_MARKERS = ('capped', 'present档', '证据档', '证据档位', 'capped_score')
    PHILO_ZERO_SEM = ('0%', '零分', '不及格', '❌')
    philo_lines = re.findall(r'[^\n]*哲学[^\n]*', body)
    for line in philo_lines:
        has_drift = any(k in line for k in PHILO_DRIFT_MARKERS)
        zero_sem = any(k in line for k in PHILO_ZERO_SEM)
        has_auth = any(k in line for k in PHILO_AUTHORITATIVE)
        if has_drift and zero_sem and not has_auth:
            advisories.append(
                f'⚠️ 哲学维度判据疑口径漂移: "{line.strip()[:60]}..."——权威判据只有七项检查≥85%→及格'
                f'(philosophical-evaluation.md)，用capped/证据档判哲学零分=自创规则(P9实锤2026-08-09·人终判)')
    return {'passed': consumed, 'na': False,
            'consumed': consumed,
            'advisories': advisories, 'detail': detail}


def eval_report_frontmatter(report_path):
    """验证评估报告的 YAML frontmatter 合规性（文件格式规范v1.0.2）。
    
    检查项：
      1. YAML frontmatter 存在（文件以 --- 开头，有闭合 ---）
      2. 7必填字段全部存在
      3. YAML 闭合后有空行（Obsidian结构规则）
      4. 字段值非空（防止占位符）
    
    Args:
        report_path: 评估报告文件路径
    
    Returns:
        dict: {
            'has_yaml': bool,
            'required_fields_found': list,   # 找到的必填字段
            'required_fields_missing': list, # 缺失的必填字段
            'optional_fields_found': list,
            'empty_fields': list,            # 值为空的字段
            'has_blank_after_yaml': bool,   # YAML闭合后是否有空行
            'passed': bool,
            'detail': list,
        }
    """
    detail = []
    
    if not os.path.exists(report_path):
        return {
            'has_yaml': False,
            'required_fields_found': [],
            'required_fields_missing': _REPORT_REQUIRED_FIELDS[:],
            'optional_fields_found': [],
            'empty_fields': [],
            'has_blank_after_yaml': False,
            'passed': False,
            'detail': [f'❌ 报告文件不存在: {report_path}'],
        }
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ── 检查1: YAML frontmatter 存在 ──
    has_yaml = content.startswith('---\n')
    if not has_yaml:
        detail.append('❌ YAML frontmatter 不存在——文件未以 ---\\n 开头')
        return {
            'has_yaml': False,
            'required_fields_found': [],
            'required_fields_missing': _REPORT_REQUIRED_FIELDS[:],
            'optional_fields_found': [],
            'empty_fields': [],
            'has_blank_after_yaml': False,
            'passed': False,
            'detail': detail,
        }
    detail.append('✅ YAML frontmatter 存在')
    
    # 提取YAML块
    parts = content.split('---\n', 2)
    if len(parts) < 3:
        detail.append('❌ YAML 块不完整——缺少闭合 ---')
        return {
            'has_yaml': True,
            'required_fields_found': [],
            'required_fields_missing': _REPORT_REQUIRED_FIELDS[:],
            'optional_fields_found': [],
            'empty_fields': [],
            'has_blank_after_yaml': False,
            'passed': False,
            'detail': detail,
        }
    
    yaml_block = parts[1]
    after_yaml = parts[2]
    
    # ── 检查2: 7必填字段 ──
    required_found = []
    required_missing = []
    empty_fields = []
    
    for field in _REPORT_REQUIRED_FIELDS:
        m = re.search(rf'^{field}\s*:\s*(.+?)$', yaml_block, re.MULTILINE)
        if m:
            value = m.group(1).strip().strip('"\'')
            if not value:
                empty_fields.append(field)
                detail.append(f'⚠️ 字段 {field} 值为空')
            else:
                required_found.append(field)
        else:
            required_missing.append(field)
            detail.append(f'❌ 必填字段缺失: {field}')
    
    if not required_missing:
        detail.append(f'✅ 7必填字段全部存在: {", ".join(required_found)}')
    
    # ── 检查3: 选填字段 ──
    optional_found = []
    for field in _REPORT_OPTIONAL_FIELDS:
        if re.search(rf'^{field}\s*:', yaml_block, re.MULTILINE):
            optional_found.append(field)
    if optional_found:
        detail.append(f'✅ 选填字段: {", ".join(optional_found)}')
    
    # ── 检查4: YAML闭合后空行 ──
    has_blank_after = after_yaml.startswith('\n')
    if has_blank_after:
        detail.append('✅ YAML 闭合后有空行')
    else:
        detail.append('⚠️ YAML 闭合后未空行（Obsidian结构规则）')
    
    # ── 综合判定 ──
    passed = (has_yaml and 
              not required_missing and 
              not empty_fields and 
              has_blank_after)
    
    return {
        'has_yaml': has_yaml,
        'required_fields_found': required_found,
        'required_fields_missing': required_missing,
        'optional_fields_found': optional_found,
        'empty_fields': empty_fields,
        'has_blank_after_yaml': has_blank_after,
        'passed': passed,
        'detail': detail,
    }


# ── 2026-09-05设计哲学反哺批A/B/C：诚实边界/伪确定性/交付物理依赖/预留接口 ──
# 四函数均走 advisory 中间态（宪法原则13：机械粗筛+人终判·不计分不进passed·None=静默§7.5）
# 同构先例: eval_removal_advisory / eval_similar_scan_advisory / eval_version_watermark

def eval_honest_boundary_advisory(skill_path, content=None):
    """诚实边界声明粗筛 advisory（2026-09-05·设计哲学反哺批A·#honest_boundary_declaration）。
    背景: 设计哲学原则6「诚实边界」——Skill 应显式声明"哪些落地由脚本确定性保证、
    哪些由 AI 判断/自觉承担"（防把"AI 记得"当"机制保证"）。被评侧通篇无边界声明时，
    存在"把自觉当保险"风险（#288 看板漂移族：声明脚本检查但实际=AI 自检清单）。
    判据（可机械粗筛·人终判）：扫描 SKILL.md 文本，命中边界类声明词 且 同行含语境锚
    （⛔/⚠/边界/确定/终判/除），视为已显式声明；完全无相应结构→advisory 提示补声明。
    产出: advisory 字符串 或 None。advisory 级不计分不进passed（§7.5静默）——
    "是否已诚实声明"可粗筛，"声明是否真的诚实/充分"须人工复核（同 eval_removal_advisory 族）。"""
    if content is None:
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
    boundary_decl = ('诚实边界', '脚本确定性', '确定性分工', 'AI 判断', 'AI判断',
                     'AI 自检', '人工终判', '人类终判', '模型无关', '自觉点',
                     '靠人记得', '机制保证', '边界声明')
    context_words = ('⛔', '⚠', '边界', '确定', '终判', '除')
    for ln in content.splitlines():
        if any(b in ln for b in boundary_decl):
            if any(c in ln for c in context_words):
                return None  # 已显式声明且含语境锚 → 静默
    return ('诚实边界声明粗筛: 通篇未见"脚本确定性/AI判断/终判权"边界声明——'
            '✅DO 显式声明哪些落地由脚本保证、哪些由 AI/人终判（原则6·#288 同族·advisory级不计分）')


def eval_pseudo_determinism_advisory(skill_path):
    """伪确定性占比 advisory（2026-09-05·设计哲学反哺批B·#pseudo_determinism_risk）。
    背景: 确定性分工识别出"伪确定性"=regex 关键词匹配（宣称的"自动检查/机械校验"实际靠
    关键词命中而非结构验证），可同义词绕过/堆砌刷分。本 advisory 粗筛被评侧"检查/校验"类
    声明里关键词计数型占比——过高提示人工复核被评侧机械层真实性。
    判据（可机械粗筛·人终判）：统计 "N项检查/校验/验证/扫描" 型声明数 n_declare，与
    "计数/命中/关键词/出现次数"型检查描述数 n_pseudo；n_declare>0 且 n_pseudo/n_declare>50%→advisory。
    ⛔advisory 级不计分不进passed——"伪确定性占比"是风险信号非质量判决（同 eval_standard_staleness 族）。"""
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return None
    n_declare = len(re.findall(r'[一二三四五六七八九十0-9]+\s*[项处]\s*(?:检查|校验|验证|扫描|核验)', content))
    if n_declare <= 0:
        return None
    n_pseudo = len(re.findall(r'(?:计数|命中|关键词|出现次数)[^。\n]{0,15}(?:检查|校验|验证)', content))
    if n_pseudo / n_declare > 0.5:
        return (f"伪确定性占比 advisory: 声明检查类 {n_declare} 项中 {n_pseudo} 项为关键词/计数型"
                f"（占比{n_pseudo/n_declare:.0%}）——确定性分工伪确定性缓解提示·⛔风险信号非质量判决·advisory级不计分")
    return None


def eval_output_format_physical_advisory(skill_path):
    """交付格式物理依赖 advisory（2026-09-05·设计哲学反哺批B·#output_format_physical_dependency）。
    背景: 确定性分工"能形式化的全丢脚本"终极手段=交付格式物理依赖脚本产物——AI 不调脚本就
    填不出报告字段（从"要不要调"变"不调交不了差"）。被评侧有报告/交付模板但未物理绑定脚本
    产物→存在"靠 AI 记忆生成报告"的自觉点（=#14 output_format_physical_dependency 同族）。
    判据（可机械粗筛·人终判）：扫描交付/报告模板声明；若存在 且 全文无"引用脚本输出/JSON字段/
    一键复制/必须调用脚本"物理依赖信号→advisory。无交付模板声明→静默。
    ⛔advisory 级不计分不进passed——"是否物理依赖"是设计取向，非缺陷计数。"""
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return None
    deliver_signal = ('报告模板', '封口确认', '交付物', '最终输出', '报告格式', '交付格式', '报告输出')
    physical_signal = ('引用脚本输出', 'JSON 字段', '一键复制', '脚本产物', '必须调用脚本',
                       '物理依赖', '不调用脚本', '脚本输出', 'json 输出', '脚本生成',
                       'JSON原样', 'finalize_report.py JSON', 'JSON**原样', '取脚本')  # v4.12.1·F-ADVISORY-FP：自家SKILL含"finalize_report.py JSON原样粘贴"而信号表漏此形态=假阳性犯在自检上
    if not any(s in content for s in deliver_signal):
        return None
    if any(s in content for s in physical_signal):
        return None
    return ('交付格式物理依赖粗筛: 含报告/交付声明但未见"引用脚本输出/JSON/一键复制产物"——'
            '✅DO 让最终交付格式物理依赖脚本产物（不调脚本=填不出字段·确定性分工终极手段·advisory级不计分）')


def eval_unwired_interface_advisory(skill_path):
    """预留接口未接线 advisory（2026-09-05·设计哲学反哺批C·#unwired_interface）。
    背景: 台账已积累 ≥6 例"预留了接口/字段/参数但从不接线"——承诺了机制但不落地
    （=#35"两处定义必漂移"族·静态测试全绿但生产断裂）。被评侧有"预留/待接线/后续接入"声明
    但无实现信号→提示补接线或降级为明示"未实现"。
    判据（可机械粗筛·人终判）：扫描"预留/待接线/后续接入/将来实现"类词；命中且其后续 60 行内
    无"已接线/已实现/已落地"对应→advisory。无预留声明→静默。
    ⛔advisory 级不计分不进passed——"预留是否该接线"是产品决策，非缺陷。"""
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return None
    reserved_signal = ('预留', '待接线', '待接入', '后续接入', '后续版本', '将来实现', '预留扩展')
    done_signal = ('已接线', '已实现', '已接入', '实装', '已挂载', '已落地')
    if not any(w in content for w in reserved_signal):
        return None
    lines = content.splitlines()
    unresolved = 0
    for i, ln in enumerate(lines):
        if any(w in ln for w in reserved_signal):
            window = '\n'.join(lines[i:min(i + 60, len(lines))])
            if not any(d in window for d in done_signal):
                unresolved += 1
    if unresolved == 0:
        return None
    return (f"预留接口未接线粗筛: {unresolved} 处'预留/待接线'声明后 60 行内未见「已接线/已实现/已落地」——"
            f"承诺不落地=#35两处定义必漂移族·✅DO 补接线或降级明示'未实现'（advisory级不计分·#unwired_interface）")


def eval_direction_gate_advisory(skill_path):
    """方向闸接线核验 advisory（2026-10-02·皮叔拍板·direction_gate 机检化）。

    背景：`references/task-standards.json` 顶层 `direction_gate`（v1.0.0）声明了三条方向类
    检查（A1 必要性 / A2 层级校验 / A3 工具适配），SKILL.md §阶段0.5 有指针。
    ⛔**但它在初版是纯声明式**——skill_eval.py 从不读它 ⇒ 与本 Skill「脚本是验收锚点·AI 自觉不是」
    原则存在已知张力（2026-10-02 L2 8要素⑤准确性🔴 的实证）。

    本 advisory 检的是**声明-执行一致性**（不是方向判断本身，那个无机械锚·A1 已标🔵悬置）：
      ① 被评侧 SKILL.md 声明了方向闸指针，但 `task-standards.json` 无 `direction_gate` → 悬空指针
      ② `direction_gate` 存在但**缺 `not_a_governance_tool` 字段** → ⛔降级陷阱防护被摘掉
         （无此字段 = 允许被误读为执行侧治理手段 = 「下次乱套→loop 会抓到」的降级陷阱失守）
      ③ `direction_gate` 存在但**缺 `execution.machine_gap` 诚实边界声明** → 假装已机检
      ④（v4.14.0）`checks` 三项（A1/A2/A3）缺项或**键结构不同构**（任一缺 `source` 条款位指针）
         → 方向检查静默退回纯启发（A1 载体被摘=#9h「假绿比不修更贵」同族）
      ⑤（v4.14.0）`checks[A1].carrier.mechanical_anchor` 缺失 → A1 载体无机械锚声明

    ⛔advisory 级不计分不进 passed——「方向闸该由谁管」是产品决策（分层归位），非缺陷。
    ⛔ **不判定语义**（守卫编写规范 L706：⛔脚本不许校验语义·语义归 AI 验收三问+你终审）——
      本 advisory 永远只问「声明了就有没有、防护被没被摘」，⛔ 不问「方向问得对不对」。
    ⛔ 读不到 task-standards.json → 静默 None（多数 Skill 无此文件·不噪声）。"""
    try:
        sk_md = os.path.join(skill_path, 'SKILL.md')
        if not os.path.exists(sk_md):
            return None
        with open(sk_md, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return None
    # ① 被评侧是否声明了方向闸
    # ⚠️ 声明信号只取**高特异**词——⛔ 不用「阶段0.5」等通用结构编号：
    #   负例实测（2026-10-02）：用「阶段0.5」时·一个只写「# 普通Skill / 阶段0.5」的无关
    #   Skill 也会命中 ⇒ advisory 对全库噪声（狼来了族）。direction_gate/方向闸 为高特异。
    decl_signals = ('direction_gate', '方向闸')
    if not any(w in content for w in decl_signals):
        return None
    std_path = os.path.join(skill_path, 'references', 'task-standards.json')
    if not os.path.exists(std_path):
        return (f"🔺方向闸悬空指针: SKILL.md 声明了方向闸（direction_gate/方向闸/阶段0.5）"
                f"但 `references/task-standards.json` 不存在——声明与执行脱节·✅DO 补标准库或撤声明"
                f"（advisory级不计分·#direction_gate）")
    try:
        import json as _json
        with open(std_path, 'r', encoding='utf-8') as f:
            std = _json.load(f)
    except Exception:
        return (f"🔺方向闸标准库不可解析: `references/task-standards.json` 读取/JSON 解析失败——"
                f"方向闸无法生效·✅DO 修标准库（声明已承诺方向闸）")
    gate = std.get('direction_gate')
    if not isinstance(gate, dict):
        return (f"🔺方向闸悬空指针: SKILL.md 声明了方向闸但 `task-standards.json` 顶层无 "
                f"`direction_gate` 字段——声明-执行 gap·✅DO 补字段或撤声明（#direction_gate）")
    missing = []
    if 'not_a_governance_tool' not in gate:
        missing.append('not_a_governance_tool（防降级陷阱防护）')
    if 'machine_gap' not in (gate.get('execution') or {}):
        missing.append('execution.machine_gap（机检缺口诚实边界声明）')
    # ⑤ v4.14.0·A1 载体化：checks 键结构同构核验
    #    背景：A1 长期是三条里唯一挂散文的（"🔵悬置·无机械锚"）——根因不是遗漏，
    #    是 **A1 在哲学层没有条款位**（A2 顶 #9h / A3 顶 #9g / A1 头顶空）。v4.14.0 起
    #    通用规范新增 #9i，A1 补 source + carrier ⇒ 三条键结构对齐。
    #    本检防的是「载体被摘」：#9i 条款位在标准库这边掉了指针（source 没了），
    #    A1 会静默退回纯启发而无人知晓 = #9h「假绿比不修更贵」同族。
    checks = gate.get('checks')
    if not isinstance(checks, list) or not checks:
        missing.append('checks（三条方向检查本体）')
    else:
        by_id = {}
        for c in checks:
            if isinstance(c, dict):
                by_id[c.get('id')] = c
        for cid in ('A1', 'A2', 'A3'):
            c = by_id.get(cid)
            if c is None:
                missing.append(f'checks[{cid}]（方向检查缺失）')
                continue
            # 三条同构：source=条款位指针（A1 载体化后与 A2/A3 对齐）
            if not str(c.get('source') or '').strip():
                _CLAUSE_HINT = {'A1': '通用规范 #9i', 'A2': '通用规范 #9h',
                                'A3': '通用规范 #9g'}
                missing.append('checks[%s].source（条款位指针·%s）'
                               % (cid, _CLAUSE_HINT.get(cid, '条款位')))
        a1 = by_id.get('A1') or {}
        # ⛔ carrier 缺失也算缺口——本批负例 test_04 自捕：只摘 carrier 留 source 时守卫
        #   静默 ⇒ 载体形态声明（纪律条款+核验·vs 纯启发）可被静默退回，正是本检要防的。
        #   carrier 是 A1 专有字段，故不强制 A2/A3 同字段（避免为对称而对称）。
        if not isinstance(a1.get('carrier'), dict):
            missing.append('checks[A1].carrier（A1 载体形态声明·#9i 纪律条款+核验）')
        elif not str(a1['carrier'].get('mechanical_anchor') or '').strip():
            missing.append('checks[A1].carrier.mechanical_anchor（A1 机械锚声明）')
    if missing:
        return (f"🔺方向闸防护缺失: `direction_gate` 缺 {' + '.join(missing)}——"
                f"无防降级字段=「下次乱套→loop 会抓到」误读陷阱失守·"
                f"无 machine_gap=假装已机检·"
                f"checks 键结构不齐=方向检查静默退回纯启发（A1 载体被摘=#9h 假绿族）·"
                f"✅DO 补回（#direction_gate）")
    return None


# ── L3反哺T1（2026-10-03 皮叔令「做完这个我们再继续LOOP」）：派生态陈旧 advisory ──
DERIVED_STALENESS_NAME_RE = ('snapshot', 'last_run', '_cache', '.cache')  # 派生态载体文件名形态
DERIVED_ANCHOR_RE = re.compile(r'timestamp|collected_at|recomputed|derived_from|generated_at|生成时间|采集时间|重算|20\d{2}-\d{2}-\d{2}', re.I)  # ISO日期键/值同为时间锚（N3复核：daily_quotes_cache 日期键形态 2026-10-03 实测假阳性收编）


def eval_derived_staleness_advisory(skill_path):
    """派生态陈旧性 advisory（v4.15.0 L3反哺T1·不计分·None=静默）。
    扫被评对象树内 snapshot/last_run/cache 类派生文件（.md/.json/.txt/.yaml，≤200KB），
    无任一复验锚（timestamp/collected_at/recomputed/derived_from/生成时间/采集时间/重算）→ ⚠️提示。
    实证病灶：ggs stats快照 rejection_rate=100% vs 官方口径实测0%（消费端把过期快照当现事实）；
    clock-loop __pycache__/last_run 类遗留态误判新污染（10-03 双例）。
    ⛔ 只判「锚字段在不在」的形态存续，⛔不判锚值新鲜度/语义有效（守卫规范 L706：语义归 AI+你终审；
    不做关键词假绿机检——有锚≠不陈旧，陈旧判定另有 staleness 家族，本条防的是「无锚裸奔态」）。"""
    skill_dir = os.path.dirname(skill_path) if skill_path.endswith('.md') else (skill_path or '.')
    if not os.path.isdir(skill_dir):
        return None
    naked = []
    try:
        for root, dirs, files in os.walk(skill_dir):
            dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'node_modules')]
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), skill_dir).lower()
                # 匹配域=相对路径全段（目录名也算：ggs 形态=data_snapshots/2026-09.json 文件名不含关键词、目录名含）
                if not any(p in rel for p in DERIVED_STALENESS_NAME_RE):
                    continue
                if os.path.basename(f).lower() == 'readme.md':
                    continue  # 目录声明文书非派生态实体（N3复核：DB data_snapshots/README 假阳性收编 2026-10-03）
                if not rel.endswith(('.md', '.json', '.txt', '.yaml', '.yml', '.jsonl')):
                    continue
                fp = os.path.join(root, f)
                try:
                    if os.path.getsize(fp) > 200 * 1024 or os.path.getsize(fp) == 0:
                        continue
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                        body = fh.read()
                except Exception:
                    continue
                if not DERIVED_ANCHOR_RE.search(body):
                    naked.append(os.path.relpath(fp, skill_dir))
    except Exception:
        return None
    if naked:
        _lst = ', '.join(sorted(naked)[:6])
        return (f"⚠️ 派生态无锚裸奔 {len(naked)} 个（snapshot/last_run/cache 类文件无 "
                f"timestamp/collected_at/derived_from/生成时间 等复验锚）：{_lst}——"
                f"消费端可能把过期快照当现事实（L3沉淀_2026-10-03 M2·ggs stats实证同族）·"
                f"advisory级不计分·✅DO 补复验锚或声明刷新策略（#derived_staleness）")
    return None


def eval_evidence_tier_verification_advisory(skill_path, content=None):
    """证据档位真伪复核 advisory（2026-09-05·设计哲学反哺批A·P1 evidence_tier_verification·#227）。
    背景: #227 施工单步骤4=证据档位接 ceiling——档位由 evidence_extractor 实算（C01），
    但被评侧自我评估/看板/文档仍可能声称"已达实跑/解锁/证据已注入"级档位，与提取器实算
    不符＝档位吹嘘（把"文档写得好"当"真跑过"——EVIDENCE_LADDER 分档边界即#288诚实边界族）。
    判据（可机械粗筛·人终判）：复用 C01 `_compute_runtime_evidence` 实算被评侧档位作基准；
    另扫描"证据/档位/运行时/实测"语境下的高档声称（exercised/解锁/已注入/outcome-supported/
    已达*档）；实算档位低于声称档位 → advisory 指档位不实。实算已达声称档或无声称→None静默。
    ⛔advisory 级不计分不进passed——"声称是否诚实"须人工复核（同 eval_honest_boundary 族·§7.5静默）。"""
    if content is None:
        try:
            with open(skill_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None
    try:
        ev = _compute_runtime_evidence(skill_path, content)
    except Exception:
        return None
    actual = (ev or {}).get('grade', SKILL_EVAL_EVIDENCE_GRADE)
    order = {'missing/unobserved/na': 0, 'present': 1, 'wired': 2, 'exercised': 3, 'outcome-supported': 4}
    # 仅"证据/档位/运行时/实测"语境下的高档声称才计——防"已实现"等无关完成态词误报
    high_claim = re.compile(
        r'(?:运行时证据已[注入收集验证]|证据已注入|档位解锁|已达\s*exercised|已达[^。\n]{0,6}档|'
        r'exercised|outcome-supported|实跑证据|实测证据)')
    ctx = ('证据', '档位', '运行时', '实测', '实跑', '量化')
    claimed = []
    for ln in content.splitlines():
        if high_claim.search(ln) and any(c in ln for c in ctx):
            claimed.append(ln.strip()[:120])
    if not claimed:
        return None
    if order.get(actual, 0) < order['exercised']:
        return (f"证据档位真伪复核: 实算档位={actual}({EVIDENCE_LADDER.get(actual, '?')}分) 低于被评侧"
                f"自我声称的实跑/解锁级证据（{len(claimed)}处声称·如「{claimed[0]}」）——⛔档位吹嘘/"
                f"虚报证据深度·诚实边界校验警告（提取器实算为准·自动注入档位·人终判·advisory级不计分）")
    return None


def _run_check_only():
    """v2.8.0 --check-only 模式：静态机检（写 .phaseX_last_run.json，不写归档）·P0拆分（v4.8.1）"""
    # v3.30.0: 兼容两种调用形式——`--check-only <target>`（main()原生）与
    # `--target <path> --check-only`（SKILL.md Phase X 声明的写法·E5声明-执行gap修复）
    if '--target' in sys.argv:
        idx = sys.argv.index('--target')
    else:
        idx = sys.argv.index('--check-only')
    target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    if not target or not os.path.exists(target):
        print(json.dumps({'error': f'target not found: {target}', 'passed': False}))
        return 0

    skill_path = target if target.endswith('SKILL.md') else os.path.join(target, 'SKILL.md')
    if not os.path.exists(skill_path):
        print(json.dumps({'error': f'SKILL.md not found under {target}', 'passed': False}))
        return 0

    result = evaluate_skill(skill_path)
    version_result = eval_version_uniform(skill_path)
    grading_advisory = eval_version_grading_advisory(skill_path)
    assertion_advisory = eval_assertion_advisory(skill_path)  # v3.12.0
    removal_advisory = eval_removal_advisory(skill_path)  # v3.36.0 C-A2（L3反哺·数字护栏移除残留扫描）
    staleness_advisory = eval_standard_staleness(skill_path)  # v3.18.0
    exit_collision_advisory = eval_exit_collision_advisory(skill_path)  # v3.41.0 L3反哺②
    selfdesc_advisory = eval_selfdesc_advisory(skill_path)  # v3.41.0 L3反哺③
    hosted_copy_advisory = eval_hosted_copy_advisory(skill_path)  # v3.20.0 L3反哺提案2
    similar_scan_advisory = eval_similar_scan_advisory(skill_path)  # v4.0.2 C05承诺核销制（同类扫描核销闹钟）
    watermark_advisory = eval_version_watermark(skill_path)  # v4.1.0 C07 #184版本水位线（跨会话/并发写入检测）
    lessons_recall_advisory = eval_lessons_recall_advisory(skill_path)  # v4.2.0 C06 #68教训召回（跨周期学习断裂）
    ceiling_advisory = format_ceiling_advisory(result.get('scores'))  # v4.3.0 C12 #198触顶链条（文档侧空间耗尽advisory）
    completeness_advisory = eval_completeness_advisory(skill_path)  # v4.5.0 C14 #178完整性兜底核对机械化（completeness 9项人工核对→粗筛）
    # 2026-09-05设计哲学反哺批A/B/C：四 advisory（诚实边界/伪确定性/交付物理依赖/预留接口）·均不计分·None=静默
    honest_boundary_advisory = eval_honest_boundary_advisory(skill_path)
    pseudo_determinism_advisory = eval_pseudo_determinism_advisory(skill_path)
    output_format_physical_advisory = eval_output_format_physical_advisory(skill_path)
    unwired_interface_advisory = eval_unwired_interface_advisory(skill_path)
    direction_gate_advisory = eval_direction_gate_advisory(skill_path)  # 2026-10-02 你拍板·direction_gate 机检化
    derived_staleness_advisory = eval_derived_staleness_advisory(skill_path)  # v4.15.0 L3反哺T1·派生态无锚裸奔（不计分·None=静默）
    # v4.6.x 批A残留: P1 evidence_tier_verification——复用C01 extractor 复核被评侧高档声称 vs 实算档位
    evidence_tier_verification_advisory = eval_evidence_tier_verification_advisory(skill_path)

    # ── v4.6.0 评估器自我观察（B1/B2/B3/A1·四机制接线）──
    _adv_map = {
        'version_grading_advisory': grading_advisory is not None,
        'assertion_advisory': assertion_advisory is not None,
        'removal_advisory': removal_advisory is not None,
        'staleness_advisory': staleness_advisory is not None,
        'exit_collision_advisory': exit_collision_advisory is not None,
        'selfdesc_advisory': selfdesc_advisory is not None,
        'hosted_copy_advisory': hosted_copy_advisory is not None,
        'similar_scan_advisory': similar_scan_advisory is not None,
        'watermark_advisory': watermark_advisory is not None,
        'lessons_recall_advisory': lessons_recall_advisory is not None,
        # v4.7.0: ceiling_advisory 移出触发率统计——触顶是状态行（非告警）·状态指示不参与 B1 告警频度
        'completeness_advisory': completeness_advisory is not None,
        'honest_boundary_advisory': honest_boundary_advisory is not None,
        'pseudo_determinism_advisory': pseudo_determinism_advisory is not None,
        'output_format_physical_advisory': output_format_physical_advisory is not None,
        'unwired_interface_advisory': unwired_interface_advisory is not None,
        'direction_gate_advisory': direction_gate_advisory is not None,
        'derived_staleness_advisory': derived_staleness_advisory is not None,
        'evidence_tier_verification_advisory': evidence_tier_verification_advisory is not None,
    }
    _record_advisory_history(target, _adv_map)  # B1: 追加触发快照（与 .phaseX_last_run.json 同族写文件）
    advisory_frequency = eval_advisory_frequency()  # B1: 触发率统计（狼来了治理）
    advisory_frequency_advisory = None
    if advisory_frequency and advisory_frequency.get('frequent'):
        _fr = advisory_frequency['frequent']
        advisory_frequency_advisory = (
            f"⚠️ advisory 常响折叠：{len(_fr)}项近{advisory_frequency['window']}次触发率≥80%"
            f"（狼来了·建议转自动/降级/合并）：{'、'.join(_fr)}——明细见 advisory_frequency")
    checker_hygiene = eval_checker_hygiene()  # B2: 检查器卫生（⚪提示级）
    checker_complexity = compute_checker_complexity()  # B3: 复杂度度量（⚪提示级）
    evidence_summary = format_evidence_summary(result.get('evidence'))  # A1: 证据复核入口

    # ── v3.27.0 双章归一（假绿灯聚合根除·三明智L2+迁理之外双验证）──
    # passed=诚实章（红字任一→false），raw_pass=旧口径保留历史可比
    _passed, _flags, _raw_pass = compute_honest_pass(result, version_result, staleness_advisory)

    phaseX_result = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'target': target,
        'passed': _passed,  # v3.27.0归一：诚实章（红字任一→false），替代旧双章制的双字段
        'raw_pass': _raw_pass,  # 旧口径（≥70+gates+version），保历史可比性
        'honest_flags': _flags,  # 红字清单（空=诚实通过）
        'total_score': result.get('total'),
        'grade': compute_grade(result.get('total', 0)),  # v3.31.6等级唯一真相源
        'evidence_tier': f"{compute_grade(result.get('total', 0))}({(result.get('evidence') or {}).get('grade', 'na')})",  # v3.33.4双盲6th P2-3: S(present)/S(exercised)——等级自带证据深度
        'evidence': result.get('evidence'),  # v3.13.0 P1: grade/ceiling/capped/理由码
        't5_score': result.get('t5'),
        'layer': result.get('layer'),
        'd5_band': result.get('d5_band'),
        'token_budget_advisory': result.get('token_budget_advisory'),  # v5.16.0: 行数纯提醒·不扣分
        'attack_level': result.get('attack_level'),
        'required_t5': result.get('required_t5'),
        'mech_type': result.get('mech_sel', {}).get('type'),
        'mech_must_missing': result.get('mech_sel', {}).get('must_missing'),
        'version_uniform': version_result,
        'version_grading_advisory': grading_advisory,  # 不计分·None=无异常（§7.5静默）
        'assertion_advisory': assertion_advisory,
        'removal_advisory': removal_advisory,  # v3.36.0 C-A2（L3反哺·不计分·None=无异常）
        'staleness_advisory': staleness_advisory,  # v3.18.0 考题滞后粗筛·不计分·None=无异常
        'exit_collision_advisory': exit_collision_advisory,  # v3.41.0 L3反哺②·不计分·None=无异常
        'selfdesc_advisory': selfdesc_advisory,  # v3.41.0 L3反哺③·不计分·None=无异常
        'hosted_copy_advisory': hosted_copy_advisory,  # v3.20.0 托管副本软链接核验·不计分·None=无异常
        'similar_scan_advisory': similar_scan_advisory,  # v4.0.2 C05承诺核销制·不计分·None=无异常
        'watermark_advisory': watermark_advisory,  # v4.1.0 C07 #184版本水位线·不计分·None=无异常
        'lessons_recall_advisory': lessons_recall_advisory,  # v4.2.0 C06 #68教训召回·不计分·None=无异常
        'honest_boundary_advisory': honest_boundary_advisory,  # v4.8.0 #50设计哲学§五·不计分·None=无异常（2026-09-09补接线·F1）
        'pseudo_determinism_advisory': pseudo_determinism_advisory,  # v4.8.0 #50·不计分·None=无异常（2026-09-09补接线·F1）
        'output_format_physical_advisory': output_format_physical_advisory,  # v4.8.0 #50·不计分·None=无异常（2026-09-09补接线·F1）
        'unwired_interface_advisory': unwired_interface_advisory,  # v4.8.0 #50·不计分·None=无异常（2026-09-09补接线·F1）
        'direction_gate_advisory': direction_gate_advisory,  # 2026-10-02 你拍板·方向闸声明-执行一致性（不计分·None=一致）
        'derived_staleness_advisory': derived_staleness_advisory,  # v4.15.0 L3反哺T1·派生态无锚裸奔（不计分·None=静默）
        'evidence_tier_verification_advisory': evidence_tier_verification_advisory,  # v4.6.x 批A·不计分·None=无异常（2026-09-09补接线·F1）
        'ceiling_advisory': ceiling_advisory,  # v4.3.0 C12 #198触顶链条·不计分·None=未触顶
        'completeness_advisory': completeness_advisory,  # v4.5.0 C14 #178完整性兜底核对机械化·不计分·None=无异常
        'advisory_frequency': advisory_frequency,  # v4.6.0 B1: advisory触发率统计（狼来了治理·样本不足None）
        'advisory_frequency_advisory': advisory_frequency_advisory,  # v4.6.0 B1: 常响折叠提示·不计分·None=无常响
        'checker_hygiene': checker_hygiene,  # v4.6.0 B2: 检查器卫生（⚪提示级·None=无违规）
        'checker_complexity': checker_complexity,  # v4.6.0 B3: 评估器自身复杂度度量（None=不可解析）
        'evidence_summary': evidence_summary,  # v4.6.0 A1: 证据复核入口一行（exercised 档人可读汇总）
        'poka_depth': result.get('poka_depth'),  # v3.40.0: 防误层深度验证达成率（5项P0检查）
        'poka_depth_detail': result.get('poka_depth_detail'),  # v3.40.0: 防误层深度验证详情
        'poka_base': result.get('poka_base'),  # v3.40.0: 原有三法检查达成率
        'checks': {
            'poka_yoke': '✅' if result.get('scores', {}).get('poka_yoke_layer', 0) >= 10 else '⚠️',
            'poka_depth': ('✅' if result.get('poka_depth', 0) >= 0.8
                           else ('⚠️' if result.get('poka_depth', 0) >= 0.6 else '🔴')),  # v3.40.0: 防误层深度验证
            'eval_gate': '✅' if result.get('eval_set') else '❌',
            'path_safety': '✅' if not result.get('security_violations') else '❌',
            'backup_gate': '✅' if result.get('backup_detail', {}).get('backups', 0) > 0 else '⚠️',
            'version_uniform': '✅' if version_result['passed'] else '❌',
            'fuse_format': '✅' if result.get('scores', {}).get('fuse_mechanism', 0) >= 4
                           else ('⚠️' if result.get('scores', {}).get('fuse_mechanism', 0) >= 3 else '❌'),
            'cross_file': '✅' if result.get('scores', {}).get('cross_file_consistency', 0) >= 3
                          else ('⚠️' if result.get('scores', {}).get('cross_file_consistency', 0) >= 2 else '❌'),
            'single_number': '✅' if result.get('scores', {}).get('single_number_source', 0) >= 2
                             else ('⚠️' if result.get('scores', {}).get('single_number_source', 0) >= 1 else '❌'),
            'gates': '✅' if all(result.get('gate', {}).values()) else '❌',
            'vx_selfhash': '✅' if result.get('vx_selfhash', True) else '🔴',  # v3.27.0问4物理钩
            'layer': result.get('layer', 'L3'),
            'attack_level': result.get('attack_level', '?'),
            'attack_t5': ('✅' if (result.get('required_t5', 0) == 0 or
                                  (result.get('required_t5', 0) == 5 and result.get('t5', 0) >= 10) or
                                  (result.get('required_t5', 0) == 11 and result.get('t5', 0) >= 20))
                          else '⚠️'),
            'mech_sel': ('✅' if not result.get('mech_sel', {}).get('must_missing') else
                         '⚠️' + ','.join(result.get('mech_sel', {}).get('must_missing', []))),
            't5_declarations': f"{result.get('t5', 0)}/{T5_MAX}"
        }
    }

    # 写入 .phaseX_last_run.json
    phasex_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(phasex_dir, '.phaseX_last_run.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(phaseX_result, f, ensure_ascii=False, indent=2)

    print(json.dumps(phaseX_result, ensure_ascii=False, indent=2))
    return 0


def _run_batch_report():
    """全量评估模式：遍历技能→生成Markdown报告→写归档JSON（P0拆分·v4.8.1）"""
    if len(sys.argv) > 1:
        raw = sys.argv[1:]
        # v3.38.7: 无效目标提前判存——无效目标在全量模式曾继续执行并写归档 JSON
        # （副作用声明未覆盖·skill-forge 评估报告 2026-09-02 发现#4）
        valid_raw = [p for p in raw if os.path.exists(p)]
        if not valid_raw and raw:
            print(f"错误: 目标不存在: {', '.join(raw)}", file=sys.stderr)
            print("提示: 用 -h 查看用法；目录会被自动归一为 SKILL.md", file=sys.stderr)
            sys.exit(2)
        raw = valid_raw if valid_raw else raw
    else:
        raw = [p for p in CORE_SKILLS if os.path.exists(p)]
    # 目录参数归一为 SKILL.md（与 --check-only 一致）
    skill_files = []
    for p in raw:
        if os.path.isdir(p):
            sk = os.path.join(p, 'SKILL.md')
            skill_files.append(sk if os.path.exists(sk) else p)
        else:
            skill_files.append(p)

    print(f"# Skill S级合规评估报告\n")
    print(f"> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"> **评估范围**: {len(skill_files)}个Skill")
    print(f"> **评估标准**: {len(WEIGHTS)}维度×{TOTAL_MAX}分制 + 闯关制（G1-G3一票否决）")
    print(f"> **对抗性测试**: T5 独立 {T5_MAX} 分（规范§6.5，不计入主分）")
    print(f"> **评估脚本**: `skill_eval.py` v2.9.12\n")
    print("---\n")

    results = [evaluate_skill(f) for f in skill_files]

    # 总览
    print("## 总览\n")
    print("| Skill | 层级 | 机制类型 | 行数(D5) | 闯关 | 得分 | T5 | 攻击面 | 等级 |")
    print("|:------|:----:|:------:|:--------:|:----:|:----:|:--:|:----:|:----:|")
    for r in results:
        if 'error' in r:
            print(f"| (错误) | - | - | - | ❌ | - | - | - | 错误 |")
            continue
        skill_name = os.path.basename(os.path.dirname(r['file']))
        gate_ok = all(r['gate'].values())
        gate_str = '🟢' if gate_ok else '🔴'
        grade = 'S' if r['total'] >= 90 else 'A' if r['total'] >= 80 else 'B' if r['total'] >= 70 else 'C'
        gemoji = '🟢' if grade in ('S', 'A') else '🟡' if grade == 'B' else '🔴'
        layer = r.get('layer', 'L3')
        mtype = r.get('mech_sel', {}).get('type', '?')
        d5 = r.get('d5_band', '?')
        atk = r.get('attack_level', '?')
        print(f"| {skill_name} | {layer} | {mtype} | {r['lines']}({d5}) | {gate_str} | {r['total']}/{TOTAL_MAX} | {r['t5']}/{T5_MAX} | {atk} | {gemoji} {grade} |")

    print("\n---")
    print("\n## 详细评估\n")
    for r in results:
        if 'error' in r:
            print(f"> ⚠️ {r['error']}\n")
            continue
        skill_name = os.path.basename(os.path.dirname(r['file']))
        print(f"### {skill_name}\n")
        print(f"- **文件**: `{r['file']}`")
        print(f"- **行数**: {r['lines']}行（D5分级：{r.get('d5_band','?')}）")
        if r.get('token_budget_advisory'):
            print(f"- **行数提醒（v5.16.0·不扣分）**: {r['token_budget_advisory']}")
        print(f"- **得分**: {r['total']}/{TOTAL_MAX}\n")

        print("#### 🧬 分层与攻击面（v2.9.0 自动检测）\n")
        layer = r.get('layer', 'L3')
        ld = r.get('layer_detail', {})
        atk = r.get('attack_surface', {})
        dims = atk.get('dims', {})
        req_t5 = r.get('required_t5', 0)
        t5_score = r.get('t5', 0)
        t5_met = (req_t5 == 0) or (req_t5 == 5 and t5_score >= 10) or (req_t5 == 11 and t5_score >= 20)
        print(f"- **推断层级**: `{layer}`（按机制完整度，非行数）")
        l3 = ld.get('L3', {})
        miss3 = [k for k, v in l3.items() if not v]
        if layer != 'L3' and miss3:
            print(f"  - L3未达标项：{'、'.join(miss3)}")
        print(f"- **攻击面评级**: `{r.get('attack_level','?')}` → T5要求 **{req_t5}项** "
              f"（实际 {t5_score}/{T5_MAX}，{'✅达标' if t5_met else '⚠️未达标'}）")
        print(f"- **D1 工具复杂度**: {dims.get('D1','?')}（{atk.get('tool_count',0)}工具：{', '.join(atk.get('tools',[])) or '无'}）")
        print(f"- **D2 写入权限**: {dims.get('D2','?')}")
        print(f"- **D3 交互深度**: {dims.get('D3','?')}")
        src = atk.get('src_types', {})
        src_hit = [k for k, v in src.items() if v]
        print(f"- **D4 外部源数**: {dims.get('D4','?')}（源种类：{', '.join(src_hit) or '无'}）")
        print(f"- **D5 产出影响**: {dims.get('D5','?')}")
        print()

        # ── 机制选配（§2.2）──
        ms = r.get('mech_sel', {})
        if ms:
            mtype = ms.get('type', '?')
            ts = ms.get('type_scores', {})
            ts_str = ' / '.join(f"{k}={ts.get(k, 0)}" for k in MECHANISM_TYPES)
            print(f"- **机制类型(自动判定)**: `{mtype}`（信号分：{ts_str}）")
            must = ms.get('must', [])
            miss = ms.get('must_missing', [])
            print(f"- **MUST机制(✅DO)**: {', '.join(must) if must else '（无）'}")
            if miss:
                print(f"  - ⚠️ **缺口**: {', '.join(miss)}")
            else:
                print(f"  - ✅ 全部满足")
            sn = ms.get('should_not_violations', [])
            if sn:
                print(f"- ⚠️ **⚠SHOULD NOT 违例**: {', '.join(sn)}（该类型应避免却出现）")
            print()

        print("#### ⛔ 闯关检查\n")
        print("| 闯关项 | 状态 |")
        print("|:------|:---:|")
        print(f"| G1 代码围栏闭合 | {'✅' if r['gate']['G1'] else '❌'} |")
        print(f"| G2 内部链接有效 | {'✅' if r['gate']['G2'] else '❌'} |")
        print(f"| G3 YAML字段齐全 | {'✅' if r['gate']['G3'] else '❌'} |")
        print()

        print("#### 分数明细\n")
        print("| 检查项 | 得分 |")
        print("|:-------|:---:|")
        for k, v in r['scores'].items():
            print(f"| {k} | {v}/{WEIGHTS[k]} |")
        print(f"| **合计** | **{r['total']}/{TOTAL_MAX}** |")
        print()

        # 违规提示
        warns = []
        if r.get('sec12_violations'):
            warns.append("§1.2 版本号唯一源：" + "；".join(r['sec12_violations']))
        d = r.get('yaml_req_detail', {})
        if d and not (d.get('author') and d.get('source')):
            miss = [k for k in ('author', 'source') if not d.get(k)]
            warns.append("§1 YAML 缺必填字段：" + "、".join(miss))
        if not r.get('not_for'):
            warns.append("§1 description 缺 NOT for/不适用于 反向触发子句")
        if r.get('eval_set') is None:
            warns.append("§6.1 评估集门禁(P0)：references/eval-set.md 缺失或为空")
        if r.get('security_violations'):
            warns.append("§四 安全：" + "；".join(r['security_violations']))
        backup_detail = r.get('backup_detail', {})
        if backup_detail and backup_detail.get('backups', 0) == 0:
            warns.append("§6.6 备份提醒（非计分）：备份目录未找到该Skill备份——修改前请先备份到记忆琥珀")
        declared_detail = r.get('declared_existence', {})
        if declared_detail and declared_detail.get('missing'):
            miss_list = declared_detail['missing']
            warns.append("§六 声明-事实核对（非计分·2026-08-10 反哺）：{} 个声称路径指向物不存在：{}".format(
                len(miss_list), "、".join(miss_list[:3]) + ("…" if len(miss_list) > 3 else "")))
        cd = r.get('causal_detail', {})
        if cd and cd.get('prohibitions', 0) and (cd.get('reasoned', 0) + cd.get('ext_reasoned', 0)) < cd['prohibitions'] * 0.4:
            warns.append(f"§二 因果链：禁令{cd['prohibitions']}条，同行附原因 {cd['reasoned']}条 + 外置{cd.get('ext_reasoned',0)}条（<40%基准）")
        fd = r.get('fuse_detail', {})
        if fd and fd.get('fuse_count', 0) > 0:
            for fi, f in enumerate(fd.get('per_fuse', []), 1):
                if f['missing']:
                    scope = '全量五字段' if f['is_external'] else '简量三字段'
                    warns.append(f"§4.3 熔断器#{fi} 缺必填字段：{'、'.join(f['missing'])}（应填{scope}）")
                if f['is_external'] and not f['failword_ok']:
                    warns.append(f"§4.3 熔断器#{fi} 失败处理未从[重试|跳过|中止|降级]四选一")
                if not f['fallback_ok']:
                    warns.append(f"§4.3 熔断器#{fi} 降级方案过于笼统（不可仅写跳过/降级）")
                if f['alias_hits']:
                    warns.append(f"§4.3 熔断器#{fi} 字段名用了别名：{'、'.join(f['alias_hits'])}（应改成功条件/失败处理/降级方案等）")
        for w in warns:
            print(f"> ⚠️ **{w}**\n")

        print("#### 🛡️ 对抗性测试 (T5)\n")
        print(f"**得分**: {r['t5']}/{T5_MAX}\n")
        for test_id, found in r['t5_details'].items():
            status = '✅' if found else '⚠️'
            print(f"- {status} {test_id}: {ADVERSARIAL_TESTS[test_id]['name']}")
        print()

    # JSON
    output_dir = os.path.expanduser('[记忆共享中心]/归档/评估报告')
    output_file = os.path.join(output_dir, f"eval_result_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n---\n\n**JSON结果已保存至**: `{output_file}`")


def main():
    # v3.38.7: -h/--help 显式支持（原实现把 sys.argv[1:] 全当 target，--help 被当路径
    # 误触发全量评估并写归档 JSON——skill-forge 评估报告 2026-09-02 发现#4）
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        print("用法: skill_eval.py [模式flag] <SKILL.md路径或skill目录>")
        print("  --check-only            静态机检（写 .phaseX_last_run.json，不写归档）")
        print("  --target <路径>         与位置参数等价")
        print("  --update-watermark <路径>  初始化/更新版本水位线载体（C07 #184·开工同步完成后显式调用）")
        print("  --check-l1l2 <报告>     L1/L2 实质内容检查")
        print("  --check-report-content <报告>  报告内容完整性检查")
        print("  <路径>（无flag）        全量评估（写归档 JSON 到 [记忆共享中心]/归档/评估报告/）")
        sys.exit(0)

    # ── v2.8.0：--check-only 模式（被 clock-loop Phase X 调用）────
    if '--check-only' in sys.argv:
        sys.exit(_run_check_only())
    
    # ── v4.1.0：--update-watermark 模式（C07 #184·开工同步完成后显式初始化/更新版本水位线）──
    if '--update-watermark' in sys.argv:
        idx = sys.argv.index('--update-watermark')
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if not target or not os.path.exists(target):
            print(json.dumps({'error': f'target not found: {target}', 'passed': False}))
            sys.exit(0)
        skill_path = target if target.endswith('SKILL.md') else os.path.join(target, 'SKILL.md')
        if not os.path.exists(skill_path):
            print(json.dumps({'error': f'SKILL.md not found under {target}', 'passed': False}))
            sys.exit(0)
        ok, msg = update_version_watermark(skill_path)
        print(json.dumps({'watermark': ok, 'message': msg}, ensure_ascii=False, indent=2))
        sys.exit(0 if ok else 1)
    
    # ── v3.0.0：--check-l1l2 模式（验证评估报告L1/L2实质内容）────
    if '--check-l1l2' in sys.argv:
        idx = sys.argv.index('--check-l1l2')
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if not target or not os.path.exists(target):
            print(json.dumps({'error': f'报告文件未找到: {target}', 'passed': False}))
            sys.exit(0)
        
        l1l2_result = eval_l1_l2_substance(target)
        output = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'report': target,
            'passed': l1l2_result['passed'],
            'l1_found': l1l2_result['l1_found'],
            'l1_substance': l1l2_result['l1_substance'],
            'l1_chars': l1l2_result['l1_chars'],
            'l2_found': l1l2_result['l2_found'],
            'l2_substance': l1l2_result['l2_substance'],
            'l2_chars': l1l2_result['l2_chars'],
            'l2_has_counterarg': l1l2_result['l2_has_counterarg'],
            'l2_counterarg_signals': l1l2_result['l2_counterarg_signals'],
            'detail': l1l2_result['detail'],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)
    
    # ── v3.0.5：--check-frontmatter 模式（验证评估报告YAML frontmatter合规性）────
    if '--check-frontmatter' in sys.argv:
        idx = sys.argv.index('--check-frontmatter')
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if not target or not os.path.exists(target):
            print(json.dumps({'error': f'报告文件未找到: {target}', 'passed': False}))
            sys.exit(0)
        
        fm_result = eval_report_frontmatter(target)
        output = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'report': target,
            'passed': fm_result['passed'],
            'has_yaml': fm_result['has_yaml'],
            'required_fields_found': fm_result['required_fields_found'],
            'required_fields_missing': fm_result['required_fields_missing'],
            'optional_fields_found': fm_result['optional_fields_found'],
            'empty_fields': fm_result['empty_fields'],
            'has_blank_after_yaml': fm_result['has_blank_after_yaml'],
            'detail': fm_result['detail'],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    # ── v4.9.0：--check-evidence 模式（取证锁 L1证据行 + L2断言计数·物理约束与防误§七）──
    if '--check-evidence' in sys.argv:
        idx = sys.argv.index('--check-evidence')
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if not target or not os.path.exists(target):
            print(json.dumps({'error': f'报告文件未找到: {target}', 'passed': False}))
            sys.exit(0)
        ev = eval_report_evidence(target)
        ev['report'] = target
        ev['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        print(json.dumps(ev, ensure_ascii=False, indent=2))
        sys.exit(0)

    # ── v3.21.0：--check-report-content 模式（报告内容完整性·分层强制·治F2消费层漂移）────
    if '--check-report-content' in sys.argv:
        idx = sys.argv.index('--check-report-content')
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if not target or not os.path.exists(target):
            print(json.dumps({'error': f'报告文件未找到: {target}', 'passed': False}))
            sys.exit(0)
        rc = eval_report_content(target)
        output = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'report': target,
            'passed': rc['passed'],          # 硬门禁: 诚实章未消费→False
            'na': rc['na'],                  # 非E/F报告→N/A不适用
            'consumed': rc['consumed'],
            'advisories': rc['advisories'],  # 软提示/条件项·不阻断
            'detail': rc['detail'],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    # ── 全量评估模式（生成Markdown报告并写归档JSON）──
    _run_batch_report()


if __name__ == '__main__':
    # ── v2.8.8: 启动时维度一致性自检 ──
    _ok, _detail = verify_dimension_consistency()
    if not _ok:
        print('⚠️ 维度一致性自检失败：', file=sys.stderr)
        for d in _detail:
            print(f'  {d}', file=sys.stderr)
        print('脚本终止——请修复WEIGHTS或MACRO_DIMENSIONS后再运行', file=sys.stderr)
        sys.exit(1)
    main()
