#!/usr/bin/env python3
"""
Skill S级合规评估脚本 v2.9.5
基于《皮叔·Skill架构规范 v5.15》+《指令编写规范 v4.2》

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
  T5 对抗性测试是独立 20 分维度（规范§6.5），不计入主分。
  v2.9.0 变更（v5.15配套）：① eval_token_budget 增 layer 参数，D5行数阈值按
    L1/L2/L3分层（规范§2.3：L1≤600/L2≤500/L3≤400安全，之上逐级警告/危险/不可接受）；
    ② 新增 eval_layering 按机制完整度推断 L1/L2/L3（规范§1.5/§1.7，非行数）；
    ③ 新增 eval_attack_surface 计算 §二附B 攻击面5维度 D1-D5（确定性信号检测，
    全自动零人工干预），任意维度=高→T5要求11项。以上均不触碰锁死的100分与T5独立20分。
  v2.9.1 变更：新增 eval_mechanism_selection（规范§2.2 机制选配矩阵核查）——信号打分
    自动判Skill类型（流程执行/生成/查询/转换/交互/分析）× 关键词检6机制，输出该类型
     MUST(✅DO)缺口与⚠SHOULD NOT违例。独立报告块（与攻击面同），不进锁死100分。
  v2.9.4 变更（补记·v2.9.0 注释遗漏）：密度系数加权（规范§2.3 v5.15）——密度≥0.90安全线上浮25%/≥0.85上浮15%/≥0.80上浮5%/<0.80不调整。
  v2.9.5 变更（v5.16配套）：D5 角色维度解耦——engine/host 类评分豁免(1.0)+独立 d5_advisory(不计入分)+band「预期·引擎类」；新增 ENGINE_ROLES/_extract_role/_build_d5_advisory。leaf/methodology 逻辑不变。满分100与T5独立20分不动。
    类型判定信号已校准：分析型须具体词（思考检查点/结论块/多Agent/哲学）不用泛词"分析/批判/推理"，
    流程执行型含"步骤/流程"泛词——修正初版把awaken/system-logger/growth-box误判为分析/转换型。
"""
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
from pathlib import Path
from datetime import datetime

# ── 8个核心Skill路径 ──────────────────────────────────────────────
CORE_SKILLS = [
    os.path.expanduser("~/.workbuddy/skills/shall-we-talk/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/triwich/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/awaken-memory-system/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/daily-buddy/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/system-logger/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/growth-box/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/meta-aletheia/SKILL.md"),
    os.path.expanduser("~/.workbuddy/skills/reading-assistant/SKILL.md"),
]

# ── 备份目录（§6.6 备份门禁检测用）────────────────────────────────
BACKUP_DIR = os.path.expanduser("~/个人AI档案/记忆琥珀/技能升级备份")

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
    'poka_yoke_layer':               15,   # 指令§5.7 三方法设计端防错【v2.4 关键词刚性修复+权重↑】
    'fuse_mechanism':                 5,   # 标准§4.3 熔断器
    'deliverable_definition':         5,   # 标准§4.1 产出物锁
    # —— 触发与结构 ——
    'trigger_conditions':             7,   # 标准§7.1 触发条件段
    'token_budget':                   7,   # 标准§2 行数预算【v2.8.5: 8→7，转移1分至single_number_source】
    'position_risk':                  4,   # 指令§8.2 关键指令前置
    'cross_file_consistency':         4,   # 标准§2 跨文件一致
    'single_number_source':           3,   # 标准§2 验证⑩单一数字源【v2.8.5新增】
    'file_clutter':                   3,   # 标准§2 无README/无杂乱【v2.8.5: 4→3】
    # —— 门禁类（P0/安全）——
    'eval_set_gate':                  6,   # 标准§6.1 评估集门禁(P0)【v2.8.5: 7→6】
    'security_hardcode':              5,   # 指令§四/§4.3 无绝对路径+XML【v2.3新增】
    # 注：backup_gate（§6.6 修改前备份）v2.4 起降为非计分提醒（见下方说明）
}
# ⛔ Poka-Yoke 定值法：满分必须=100，任何权重改动后此断言物理拦截溢出
assert sum(WEIGHTS.values()) == 100, \
    f"权重总和必须=100，当前={sum(WEIGHTS.values())}——修改 WEIGHTS 后请重新配平"

TOTAL_MAX = sum(WEIGHTS.values())  # =100

# ── 共享正则常量（避免重复定义）────────────────────────────────
# 版本号提取模式：匹配 `**版本**：v1.2.3` / `版本：v1.2.3` / `version: 1.2.3`
RE_VERSION_BOLD = re.compile(r'\*\*版本\*\*\s*[：:]\s*(v?\d[\w.]*)')
RE_VERSION_COLON = re.compile(r'版本[：:]\s*(v?\d[\w.]*)')
RE_VERSION_YAML = re.compile(r'^version:\s*["\']?(v?\d[\w.]+)["\']?', re.MULTILINE)

# ── 允许的Skill目录文件/目录（eval_file_clutter用）─────────────
ALLOWED_SKILL_FILES = {
    'SKILL.md', 'references', '_user_meta.json', '.DS_Store',
    'scripts', 'assets', 'tests',
}


def pts(key, ratio):
    """把 [0,1] 达成率换算为该维度实际得分（四舍五入到整数）"""
    return round(max(0.0, min(1.0, ratio)) * WEIGHTS[key])


# ══════════════════════════════════════════════════════════════════
#  宏观维度映射表（v2.8.8新增）
#  SKILL.md阶段2声明的6个宏观维度 → skill_eval.py的19个微观检查项
#  每个微观维度必须追溯到唯一一个宏观维度。
#  verify_dimension_consistency()启动时自检，保证两层权重一致。
# ══════════════════════════════════════════════════════════════════
MACRO_DIMENSIONS = {
    # 宏观维度名: (声明权重%, [下属微观维度key列表])
    # v2.8.8: 声明权重=下属微观维度WEIGHTS之和/100，由verify_dimension_consistency()自检
    '开发规范':     (19, ['yaml_frontmatter', 'yaml_required_fields', 'description_not_for',
                            'sec_1_2_version_single_source', 'file_clutter']),
    '指令准确性':   (18, ['trigger_conditions', 'security_hardcode', 'eval_set_gate']),
    '逻辑一致性':   (27, ['causal_chain', 'poka_yoke_layer', 'cross_file_consistency',
                            'single_number_source']),
    '文档完整性':   (14, ['five_level_annotations', 'no_binary_annotations',
                            'deliverable_definition']),
    '测试覆盖':     (12, ['fuse_mechanism', 'token_budget']),
    '哲学评估':     (10, ['alternatives_considered', 'position_risk']),
}


def verify_dimension_consistency():
    """启动时自检：宏观维度与微观维度权重一致性。

    检查项（4项全过才允许运行）：
      1. 每个微观维度key在WEIGHTS中存在
      2. 每个微观维度只属于一个宏观维度（无重复归属）
      3. 宏观维度声明权重% == 其下属微观维度WEIGHTS之和 / 100 * TOTAL_MAX
         （容差±1分，因四舍五入）
      4. 宏观维度声明权重总和 = 100%
      5. 所有WEIGHTS中的微观维度都被MACRO_DIMENSIONS覆盖（无遗漏）

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
                ref_text = open(ref_path, encoding='utf-8').read()
                # 外置文件中含原因标记的行即计为外部化原因（上限=禁令数，避免超额）
                ext_reasoned = min(sum(1 for l in ref_text.splitlines() if reason_pat.search(l)),
                                    prohibitions)
    total_reasoned = min(reasoned + ext_reasoned, prohibitions)
    # 达标基准=禁令数的40%附原因即满分
    ratio = min(total_reasoned / (prohibitions * 0.4), 1.0)
    return ratio, {'prohibitions': prohibitions, 'reasoned': reasoned, 'ext_reasoned': ext_reasoned}

def eval_alternatives(content):
    """指令§5.8 Alternatives Considered 段存在"""
    return 1.0 if re.search(r'Alternatives\s*Considered|替代方案|权衡', content) else 0.0

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

    # ── 检查1：用例数一致 ──
    # SKILL.md中常见声明模式："eval-set.md ... N条用例" 或 "N条用例"
    checks_total += 1
    eval_count_mismatch = None
    # 从SKILL.md提取声明的用例数
    declared_counts = re.findall(r'(\d+)\s*条(?:用例|测试用例|case)', main_content)
    eval_set_path = os.path.join(refs_dir, 'eval-set.md')
    if os.path.isfile(eval_set_path) and declared_counts:
        with open(eval_set_path, 'r', encoding='utf-8') as f:
            eval_content = f.read()
        # 从eval-set.md头部提取声明数
        head_declared = re.search(r'用例总数[：:]\s*(\d+)\s*条', eval_content)
        # 从eval-set.md实际用例行数提取（| N | 开头的行）
        actual_rows = len(re.findall(r'^\|\s*\d+\s', eval_content, re.MULTILINE))
        for dc_str in declared_counts:
            dc = int(dc_str)
            if head_declared and int(head_declared.group(1)) != dc:
                eval_count_mismatch = (
                    f'SKILL.md声明{dc}条用例，但eval-set.md头部声明{head_declared.group(1)}条'
                )
                break
            if actual_rows > 0 and actual_rows != dc:
                eval_count_mismatch = (
                    f'SKILL.md声明{dc}条用例，但eval-set.md实际只有{actual_rows}条用例行'
                )
                break
    if eval_count_mismatch:
        detail['mismatches'].append(eval_count_mismatch)
    else:
        checks_passed += 1
    detail['checks'].append({
        'name': 'eval_set_count',
        'passed': eval_count_mismatch is None,
        'detail': eval_count_mismatch or '用例数声明与实际一致'
    })

    # ── 检查2：签名格式一致 ──
    # SKILL.md中声明的签名格式 vs signature.md中的示例
    checks_total += 1
    sig_mismatch = None
    sig_path = os.path.join(refs_dir, 'shared', 'signature.md')
    if not os.path.isfile(sig_path):
        # 尝试直接在references下找signature.md
        sig_path = os.path.join(refs_dir, 'signature.md')
    if os.path.isfile(sig_path):
        with open(sig_path, 'r', encoding='utf-8') as f:
            sig_content = f.read()
        # 提取signature.md中所有签名示例（反引号内的内容）
        sig_examples = re.findall(r'`\[🧠[^`]+\]`', sig_content)
        # 提取SKILL.md中声明的签名格式
        skill_sig_formats = re.findall(r'格式[：:]\s*`\[🧠[^`]+\]`', main_content)
        if sig_examples and skill_sig_formats:
            # 归一化比较：去掉具体内容，只比结构（L1/L2/L3标识 + 分隔符数量）
            def normalize_sig(s):
                # 提取L1/L2/L3 + ✅/❌ + 分隔符|的数量
                level = re.search(r'L[123]', s)
                bars = s.count('|')
                has_date = bool(re.search(r'\d{4}-\d{2}-\d{2}|日期', s))
                return (level.group(0) if level else '?', bars, has_date)
            sig_norms = set(normalize_sig(s) for s in sig_examples)
            skill_norms = set(normalize_sig(s.split('`')[1] if '`' in s else s)
                             for s in skill_sig_formats)
            # 检查每个SKILL.md声明的签名层级在signature.md中有对应
            for sn in skill_norms:
                if sn not in sig_norms:
                    sig_mismatch = (
                        f'SKILL.md签名格式{sn}在signature.md中无对应示例'
                    )
                    break
    if sig_mismatch:
        detail['mismatches'].append(sig_mismatch)
    else:
        checks_passed += 1
    detail['checks'].append({
        'name': 'signature_format',
        'passed': sig_mismatch is None,
        'detail': sig_mismatch or '签名格式声明与示例一致'
    })

    # ── 检查3：License一致 ──
    # YAML frontmatter的license字段 vs 文末协议声明
    checks_total += 1
    lic_mismatch = None
    yaml_lic = re.search(r'^license\s*:\s*["\']?(\w+)["\']?', main_content, re.MULTILINE)
    # 文末协议声明（最后20行内）
    last_lines = '\n'.join(main_content.splitlines()[-20:])
    tail_lic = re.search(r'(?:开源协议|协议|License)[：:]\s*(MIT|Proprietary|Apache[\s-]+2\.0|GPL)', last_lines, re.IGNORECASE)
    if yaml_lic and tail_lic:
        yaml_l = yaml_lic.group(1).lower()
        tail_l = tail_lic.group(1).lower().replace(' ', '-')
        # 归一化比较
        lic_map = {'apache-2.0': 'apache', 'apache2.0': 'apache'}
        yaml_l = lic_map.get(yaml_l, yaml_l)
        tail_l = lic_map.get(tail_l, tail_l)
        if yaml_l != tail_l:
            lic_mismatch = (
                f'YAML license={yaml_lic.group(1)} vs 文末协议={tail_lic.group(1)}'
            )
    if lic_mismatch:
        detail['mismatches'].append(lic_mismatch)
    else:
        checks_passed += 1
    detail['checks'].append({
        'name': 'license_consistency',
        'passed': lic_mismatch is None,
        'detail': lic_mismatch or 'License声明一致'
    })

    # ── 检查4：索引表引用文件存在性 ──
    # SKILL.md中引用了 references/xxx.md 的文件必须存在
    # 只匹配明确的文件路径引用（references/后直接跟文件名.md），排除自然语言描述
    checks_total += 1
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
        # 尝试在references目录下找（含子目录）
        found = False
        for root, _, files in os.walk(refs_dir):
            if ref_name in files:
                found = True
                break
        if not found:
            missing_refs.append(ref_name)
    if missing_refs:
        detail['mismatches'].append(f'索引表引用的文件不存在: {missing_refs}')
    else:
        checks_passed += 1
    detail['checks'].append({
        'name': 'indexed_files_exist',
        'passed': not missing_refs,
        'detail': f'缺失文件: {missing_refs}' if missing_refs else '索引表引用文件均存在'
    })

    # ── 检查5：关键数字交叉比对 ──
    # SKILL.md中声明的步数 vs references文件中实际Step数
    checks_total += 1
    step_mismatch = None
    # 提取SKILL.md中"N步"声明（如"4步""8步""11步"）
    step_decls = re.findall(r'(\d+)\s*步', main_content)
    # 检查references文件中实际Step标题数
    for ref_fname in ref_files:
        ref_fpath = os.path.join(refs_dir, ref_fname)
        try:
            with open(ref_fpath, 'r', encoding='utf-8') as f:
                ref_content = f.read()
        except Exception as e:
            detail.setdefault('warnings', []).append(f'读取{ref_fname}失败: {e}')
            continue
        # 文件头部声明的步数（如"> 步骤：4步"或"> 步骤：...（8步）"）
        head_step = re.search(r'步骤[：:][^\n]*?(\d+)\s*步', ref_content)
        # 实际Step标题数（## Step1 / ## Step2 等）
        actual_steps = len(re.findall(r'^##\s*Step\d+', ref_content, re.MULTILINE))
        if head_step and actual_steps > 0:
            declared = int(head_step.group(1))
            if declared != actual_steps:
                step_mismatch = (
                    f'{ref_fname}: 头部声明{declared}步，实际{actual_steps}个Step标题'
                )
                break
    if step_mismatch:
        detail['mismatches'].append(step_mismatch)
    else:
        checks_passed += 1
    detail['checks'].append({
        'name': 'step_count_consistency',
        'passed': step_mismatch is None,
        'detail': step_mismatch or '步数声明与实际一致'
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

    # ── 检查2：G系列编号连续性 ──
    # 提取所有G编号（G1, G2, G3...），检查是否连续无跳号
    checks_total += 1
    g_nums = [int(m) for m in re.findall(r'\bG(\d+)\b', content)]
    if g_nums:
        unique_g = sorted(set(g_nums))
        expected = list(range(1, max(unique_g) + 1))
        missing = [g for g in expected if g not in unique_g]
        if missing:
            mismatch = f'G系列编号跳号：缺失G{missing}（存在{unique_g}）'
            detail['mismatches'].append(mismatch)
            detail['checks'].append({
                'name': 'g_series_continuous',
                'passed': False,
                'detail': mismatch
            })
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
    """标准§2 文件杂乱 + ⛔无 README.md"""
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
    try:
        matches = [f for f in os.listdir(BACKUP_DIR)
                   if skill_name.lower() in f.lower()]
    except Exception as e:
        return 0.0, {'skill': skill_name, 'backups': 0, 'warning': f'备份目录读取失败: {e}'}
    return (1.0 if matches else 0.0), {
        'skill': skill_name, 'backups': len(matches)}


# ── v2.8.0新增：全文件版本统一校验 ────────────────────────────────
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
    
    # 2. CHANGELOG latest version
    changelog_path = os.path.join(skill_dir, 'references', 'CHANGELOG.md')
    changelog_ver = None
    if os.path.isfile(changelog_path):
        with open(changelog_path, 'r', encoding='utf-8') as f:
            cl_content = f.read()
        cl_m = re.search(r'^### (v[\w.]+)', cl_content, re.MULTILINE)
        if cl_m:
            changelog_ver = cl_m.group(1)
            result['versions']['CHANGELOG.md'] = changelog_ver
    
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
    
    # 5. 附加文件版本扫描（仅供参考，不产生FAIL——固化引用/模板有自己的版本号体系）
    #    只记录到 versions 供排查，不加入 mismatches
    refs_dir = os.path.join(skill_dir, 'references')
    if os.path.isdir(refs_dir):
        for fname in sorted(os.listdir(refs_dir)):
            if not fname.endswith('.md') or fname == 'CHANGELOG.md':
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
            fpath = os.path.join(scripts_dir, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                script_content = f.read()
            sv1 = re.search(r'__version__\s*=\s*["\']([\w.]+)["\']', script_content)
            sv2 = RE_VERSION_COLON.search(script_content)
            sv = None
            if sv1:
                sv = sv1.group(1)
            elif sv2:
                sv = sv2.group(1)
            if sv:
                result['versions'][fname] = sv
                # 不加入 mismatches——脚本自身版本不一定随Skill同步
    
    if result['mismatches']:
        result['passed'] = False
    
    # 6. 外部依赖版本核对（dependencies 声明 vs 源文件 vs 固化引用）
    result['dependencies'] = []
    dep_pattern = re.compile(
        r'-\s*name:\s*(\S+)\s*\n\s*version:\s*["\']?([\w.]+)["\']?\s*\n\s*path:\s*(\S+)',
        re.MULTILINE
    )
    for m in dep_pattern.finditer(main_content):
        dep_name = m.group(1)
        declared_ver = m.group(2)
        dep_path = m.group(3)
        dep_path = dep_path.replace('~', os.path.expanduser('~'))
        
        dep_info = {
            'name': dep_name,
            'declared': declared_ver,
            'source_ver': None,
            'ref_ver': None,
            'status': 'unknown'
        }
        
        # Check source file
        source_skill = os.path.join(dep_path, 'SKILL.md')
        if not os.path.isfile(source_skill):
            # 非 Skill 源（如规范文件）：在目录里找文件名含 name 关键词的文件
            name_keys = {'instruction-standard': '指令编写', 'skill-arch-standard': '架构规范'}
            if os.path.isdir(dep_path):
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
        if r and r != s:
            issues.append(f'固化引用版本{dep_info["ref_ver"]} ≠ 源文件版本{dep_info["source_ver"]}')
        if r and r != d and s and r == s:
            issues.append(f'dependencies声明版本{dep_info["declared"]} ≠ 固化引用版本{dep_info["ref_ver"]}')
        
        if issues:
            dep_info['status'] = '🔴 drift'
            result['warnings'].extend(f'依赖 {dep_name}: {i}' for i in issues)
        else:
            dep_info['status'] = '✅ sync'
        
        result['dependencies'].append(dep_info)
    
    return result


# ── T5 对抗性测试（独立20分，不计入主分 · 规范§6.5）─────────────────
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
T5_MAX = 20  # 独立维度，不计入主分

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
    alt_present = eval_alternatives(content) > 0

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


def _count_evalset(es_text):
    """评估集条目数（跨格式鲁棒统计，规范§1.5 L3要求≥10）。

    优先级：①显式总数声明（用例总数/共N条/总计）②分节（N条）求和
    ③表格 | N | 行数。返回整数条目数。"""
    total_m = re.search(r'用例总数[：:]\s*(\d+)\s*条|共\s*(\d+)\s*条|总计\s*(\d+)\s*条',
                        es_text)
    if total_m:
        return int(total_m.group(1) or total_m.group(2) or total_m.group(3))
    secs = re.findall(r'（[^）]*?(\d+)\s*条', es_text)
    if secs:
        return sum(int(x) for x in secs)
    return len(re.findall(r'^\|\s*\d+\s', es_text, re.MULTILINE))


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
def evaluate_skill(skill_path):
    if not os.path.exists(skill_path):
        return {'error': f'文件不存在: {skill_path}'}

    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()
    frontmatter, _ = split_frontmatter(content)

    # 闯关
    g1 = check_unclosed_code_fence(content)
    g2_ok, g2_link = check_internal_links(skill_path, content)
    g3_ok, g3_field = check_yaml_fields(content)

    # 各维度达成率
    r_yaml                 = eval_yaml_frontmatter(content)
    r_yaml_required, yaml_required_detail = eval_yaml_required_fields(frontmatter)
    r_description_not_for, description_not_for = eval_description_not_for(frontmatter, content)
    r_sec_1_2, sec_1_2_v   = eval_sec_1_2_version_single_source(content)
    r_annot                = eval_five_level_annotations(content)
    r_nobin                = eval_no_binary_annotations(content)
    r_causal, causal_detail = eval_causal_chain(content, skill_path)
    r_alt                  = eval_alternatives(content)
    r_poka                 = eval_poka_yoke(content)
    r_fuse, fuse_detail    = eval_fuse_mechanism(content)
    r_deliver              = eval_deliverable_definition(content)
    r_trigger              = eval_trigger_conditions(content)
    layer, layer_detail    = eval_layering(frontmatter, content, skill_path)
    role = _extract_role(frontmatter)  # v3.0.0: 仅信息展示，不再影响评分
    r_token, lines, d5_band = eval_token_budget(skill_path, layer, role)
    attack, attack_level, required_t5 = eval_attack_surface(content, skill_path, layer)
    mech_sel = eval_mechanism_selection(content, skill_path)
    r_pos                  = eval_position_risk(content)
    r_cross, ref_cnt       = eval_cross_file_consistency(skill_path)
    r_single, single_detail = eval_single_number_source(content)
    r_clutter, clutter_detail = eval_file_clutter(skill_path)
    r_evalset, evalset_detail = eval_eval_set_gate(skill_path)
    r_security, security_detail = eval_security_hardcode(content)
    r_backup, backup_detail = eval_backup_gate(skill_path)

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
        'poka_yoke_layer':               pts('poka_yoke_layer', r_poka),
        'fuse_mechanism':                pts('fuse_mechanism', r_fuse),
        'deliverable_definition':        pts('deliverable_definition', r_deliver),
        'trigger_conditions':            pts('trigger_conditions', r_trigger),
        'token_budget':                  pts('token_budget', r_token),
        'position_risk':                 pts('position_risk', r_pos),
        'cross_file_consistency':        pts('cross_file_consistency', r_cross),
        'single_number_source':           pts('single_number_source', r_single),
        'file_clutter':                  pts('file_clutter', r_clutter),
        'eval_set_gate':                 pts('eval_set_gate', r_evalset),
        'security_hardcode':             pts('security_hardcode', r_security),
        # 注：backup_gate v2.4 起不再计分（§6.6属流程层→非幂等），仅作报告提醒（见 warns）
    }
    total = sum(scores.values())

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
        'fuse_detail': fuse_detail,
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


def main():
    # ── v2.8.0：--check-only 模式（被 clock-loop Phase X 调用）────
    if '--check-only' in sys.argv:
        idx = sys.argv.index('--check-only')
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if not target or not os.path.exists(target):
            print(json.dumps({'error': f'target not found: {target}', 'passed': False}))
            sys.exit(0)
        
        skill_path = target if target.endswith('SKILL.md') else os.path.join(target, 'SKILL.md')
        if not os.path.exists(skill_path):
            print(json.dumps({'error': f'SKILL.md not found under {target}', 'passed': False}))
            sys.exit(0)
        
        result = evaluate_skill(skill_path)
        version_result = eval_version_uniform(skill_path)
        
        phaseX_result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'target': target,
            'passed': (result.get('total', 0) >= 70 and
                       all(result.get('gate', {}).values()) and
                       version_result['passed']),
            'total_score': result.get('total'),
            't5_score': result.get('t5'),
            'layer': result.get('layer'),
            'd5_band': result.get('d5_band'),
            'attack_level': result.get('attack_level'),
            'required_t5': result.get('required_t5'),
            'mech_type': result.get('mech_sel', {}).get('type'),
            'mech_must_missing': result.get('mech_sel', {}).get('must_missing'),
            'version_uniform': version_result,
            'checks': {
                'poka_yoke': '✅' if result.get('scores', {}).get('poka_yoke_layer', 0) >= 10 else '⚠️',
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
                'layer': result.get('layer', 'L3'),
                'attack_level': result.get('attack_level', '?'),
                'attack_t5': ('✅' if (result.get('required_t5', 0) == 0 or
                                      (result.get('required_t5', 0) == 5 and result.get('t5', 0) >= 10) or
                                      (result.get('required_t5', 0) == 11 and result.get('t5', 0) >= 20))
                              else '⚠️'),
                'mech_sel': ('✅' if not result.get('mech_sel', {}).get('must_missing') else
                             '⚠️' + ','.join(result.get('mech_sel', {}).get('must_missing', []))),
                't5_declarations': f"{result.get('t5', 0)}/20"
            }
        }
        
        # 写入 .phaseX_last_run.json
        phasex_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(phasex_dir, '.phaseX_last_run.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(phaseX_result, f, ensure_ascii=False, indent=2)
        
        print(json.dumps(phaseX_result, ensure_ascii=False, indent=2))
        sys.exit(0)
    
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
    
    if len(sys.argv) > 1:
        raw = sys.argv[1:]
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
    print(f"> **评估脚本**: `skill_eval.py` v2.9.1\n")
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
    output_dir = os.path.expanduser('~/个人AI档案/归档/评估报告')
    output_file = os.path.join(output_dir, f"eval_result_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n---\n\n**JSON结果已保存至**: `{output_file}`")


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
