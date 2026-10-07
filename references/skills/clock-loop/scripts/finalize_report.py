#!/usr/bin/env python3
"""finalize_report.py — 评估报告归档封口物理锁（v3.23.0建·v3.24.0加纯净度门禁·clock-loop 阶段4）

v1.7.0 变更（2026-09-04 · 幂等性活故障修复 · 你授权"按符合愿景的最优解根治"）：
  病（实测实锤·9/9 归档报告 sha8 对不上·100%复现）：v1.6.0 自动回贴段以 `\n\n---\n\n## 🔒…`
    开头，而 report_sha8 剔离正则从 `## 🔒` 起剔、**漏剔前置孤立 `---`** → 贴块后哈希变值。
    静态测试未逮住的原因：幂等测试**手写**段格式（无 `---` 前缀）→ 测的是想象形态非生产形态。
  解（三层·对应愿景三问）：
    ① 单一真相源：SEAL_HEADER 常量 + build_seal_section() 为回贴段唯一出口，剔离正则
      **从 SEAL_HEADER 派生**（⛔不得两处各写格式）→ 漂移在结构上不可能。
    ② 正则补可选前置 `---`（兼容存量已贴块报告）。
    ③ 启动幂等性自检 _selfcheck_idempotency()：走**生产同一代码路径**造段→贴→重算，
      失败即 exit 2 拒绝封口（让漂移在封口前被逮出·绕过成本>遵守成本+留痕·C-090）→ 强化闭环 + 减少人工（不靠人记得验）。
  存量处置：9 份已贴块报告的重算回填走 --reseal-sha8（见 main）。

设计依据（00-遗留问题与交接.md §0 已验证待落地·三明智L2过关2026-07-29冻结）：
  病：门禁④⑤(--check-l1l2/--check-report-content)是收尾门禁步·靠AI记得跑
      → AI跳过收尾门禁则F2/M4漏检又回来。规范§Poka-Yoke定死"防误>防错"。
  解：本脚本统一封口——AI完成归档必调它，内部跑
      check-only(硬门禁) + check-l1l2(硬门禁) + check-report-content(硬门禁·na放行)
      + 归档路径校验 + 文件存在性，任一硬门禁不过 → exit非零拒绝封口。

认知诚实边界（架构规范§一1.1 防误层诚实边界·v5.22）：
  纯AI环境无"绝对物理杜绝"——链条尽头仍有"AI调不调本脚本"的自觉点。
  本脚本的真实效果 = 把绕过点从"忘跑门禁④⑤"挪到"伪造整个封口确认块+算对报告哈希
  +骗过双盲复现"，绕过成本大增且全程留痕（.finalize_last_run.json + report_sha8）。
  ⛔措辞禁用"杜绝/根治"。

honest_pass 透传不阻断（设计决策·与v3.19.0双章制自洽）：
  双章制本意是"红字显形"非"堵死交付"——若honest_pass=False硬拒封口，
  clock-loop自评(d5红字长期账·皮叔07-27裁"不为指标动热路径")将永远无法归档报告，
  与双盲3rd报告已归档的事实矛盾。False时确认块内置⛔警示行，
  报告消费纪律由 check-report-content 硬门禁卡。

用法：
  python3 finalize_report.py --skill <被评估SKILL.md或目录> --report <评估报告绝对路径>
  exit 0 = 封口成功（stdout输出封口确认块JSON·报告须原样粘贴）
  exit 1 = 拒绝封口（缺陷清单在JSON detail）
  exit 2 = 参数/环境错误
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import hashlib
import json
import sys
import os
import re
import subprocess
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_EVAL = os.path.join(SCRIPT_DIR, 'skill_eval.py')
LAST_RUN_PATH = os.path.join(SCRIPT_DIR, '.finalize_last_run.json')
# 归档根（与SKILL.md阶段4"写入前路径阻断"同一真相源）
DEFAULT_ARCHIVE_ROOT = os.path.expanduser('[记忆共享中心]/评估知识库/test_results/')

# 版本单一真相源（v1.6.1）：封口块 seal 字段与版本对账均取此。
# ⛔DO NOT 在别处硬编码版本号——原因是 v1.6.0 曾把 'v1.6.0' 写死在 seal 字段（元数据靠人维护必漂移）；
# 且 skill_eval.eval_version_uniform 扫 scripts/*.py 的 __version__，定义于此才能被对账视野逮到。
__version__ = '1.8.0'

# ── 封口确认块格式·单一真相源（v1.7.0：剔离正则与回贴段同源派生→两处定义合一，漂移在结构上无处发生）──────
SEAL_HEADER = '## 🔒 归档封口确认块'
# 剔离正则从 SEAL_HEADER 派生（空格→\s* 保留容错）+ 可选前置 `---` 分隔线。
# ⛔DO NOT 另写一份剔离正则——原因是两处定义必漂移（v1.6.0 实锤：9/9 报告 sha8 失效）。
_SEAL_HDR_PAT = r'\s*'.join(re.escape(p) for p in SEAL_HEADER.split(' '))
SEAL_STRIP_RE = re.compile(r'\n*(?:---[ \t]*\n+)?' + _SEAL_HDR_PAT + r'.*?(?=\n##\s|\n---\n|\Z)',
                           re.DOTALL)


def build_seal_section(block):
    """生成回贴用封口确认块段——**生产唯一出口**。

    ⛔DO NOT 在别处（含测试）手写本段字符串——原因是手写格式与实际回贴格式一旦不一致，
    幂等测试会测"想象中的格式"而报绿，生产却静默失效（v1.6.0 实锤·2026-09-04）。
    测试须调本函数取段。
    """
    paste = {
        'seal': block['seal'],
        'timestamp': block['timestamp'],
        'skill': block['skill'],
        'report': block['report'],
        'report_sha8': block['report_sha8'],
        'sealed': block['sealed'],
        'passed': block.get('passed'),
        'honest_flags': block.get('honest_flags'),
        'human_check': block.get('human_check', {}).get('note'),
    }
    return ('\n\n---\n\n' + SEAL_HEADER + '（finalize_report.py 自动回贴·机械生成·'
            'report_sha8 幂等哈希已剔离本段）\n\n```json\n'
            + json.dumps(paste, ensure_ascii=False, indent=2) + '\n```\n')


def check_archive_path(report_path, root=DEFAULT_ARCHIVE_ROOT):
    """归档路径校验（纯函数·root可注入供unittest·照daily-buddy validate_diary先例）。
    Returns (ok: bool, reason: str)"""
    real = os.path.realpath(os.path.expanduser(report_path))
    root_real = os.path.realpath(os.path.expanduser(root))
    if not real.startswith(root_real + os.sep):
        return False, f'路径不在归档根下: {real} (要求前缀 {root_real}/)'
    if not real.endswith('.md'):
        return False, f'非markdown报告文件: {real}'
    return True, 'ok'


def report_sha8(report_path):
    r"""报告内容sha1前8位——防伪锚点。
    幂等哈希：计算前剔离"归档封口确认块"段（若已粘贴）——否则确认块粘进报告后内容变化，
    双盲复现重跑永远对不上（哈希自指悖论）。复现方式=直接重跑本脚本比对sha8。

    v1.6.1：剔离改用 SEAL_STRIP_RE（从 SEAL_HEADER 派生 + 含可选前置 `---`）。
    ⚠️ 历史缺陷（v1.6.0·已修）：旧正则 `\n*##\s*🔒\s*归档封口确认块.*?` 漏剔回贴段的
    前置 `\n\n---\n\n` → 残留孤立 `---` 使哈希变值 → 9/9 自动回贴报告 sha8 对不上（实测100%复现）。
    """
    with open(report_path, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    # 剔离封口确认块段（含前置空行与可选 --- 分隔线）：至下一个同级标题/---分隔/文件尾
    text = SEAL_STRIP_RE.sub('', text)
    # 尾部空白归一化——剔离后残留换行不得影响哈希（幂等保证）
    return hashlib.sha1(text.rstrip().encode('utf-8')).hexdigest()[:8]


def _selfcheck_idempotency():
    """启动自检：幂等性物理验证（让漂移在封口前被逮出·C-090）。

    用**生产同一份** build_seal_section() 造段 → 贴 → 重算 sha8 必须不变。
    失败 = 剔离正则与回贴格式再次漂移 → main() 直接 exit 2 拒绝封口。
    为什么必要：v1.6.0 的教训是"静态测试手写格式报绿、生产实际格式失效"——
    只有让自检走生产同一代码路径，才能保证测的就是跑的（消除想象形态 vs 生产形态的缝）。
    Returns (ok: bool, detail: str)
    """
    import tempfile
    d = tempfile.mkdtemp(prefix='seal_selfcheck_')
    p = os.path.join(d, 'selfcheck_评估报告.md')
    try:
        with open(p, 'w', encoding='utf-8') as f:
            f.write('# 自检报告\n正文内容\n')
        h1 = report_sha8(p)
        fake = {'seal': f'finalize_report.py v{__version__}', 'timestamp': 'selfcheck',
                'skill': 'selfcheck', 'report': p, 'report_sha8': h1, 'sealed': True,
                'passed': True, 'honest_flags': [], 'human_check': {'note': 'selfcheck'}}
        with open(p, 'a', encoding='utf-8') as f:
            f.write(build_seal_section(fake))
        h2 = report_sha8(p)
        return h1 == h2, f'贴块前 sha8={h1} / 贴块后重算 sha8={h2}'
    except Exception as e:  # 自检本身异常 = 不可信 = 不放行（fail-closed）
        return False, f'自检执行异常: {e}'
    finally:
        try:
            os.remove(p)
            os.rmdir(d)
        except OSError:
            pass


def check_single_report(report_path):
    """单报告单文件纯净度检查（纯函数·v3.24.0建·v3.26.0双盲4th修漏检误伤）。
    检测文件中部再现YAML frontmatter块（双报告污染信号）。
    第一性特征：frontmatter=非文件开头的闭合 --- 块 + 块内含frontmatter键(title/type/status等)。
    v3.26.0修（双盲4th实锤）：①漏检修——不再只认首行title，改认块内任一frontmatter键（首行是type/status也逮）
    ②误伤修——先剔fenced code防代码块内YAML示例被误杀 + 要求闭合---块防正文单条分隔线误伤。
    负例实锤=growth-box_v1.9.3报告混入triwich副本（AutoClaw批量append错目标）。
    Returns (ok: bool, reason: str)"""
    with open(os.path.expanduser(report_path), 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    # ②先剔 fenced code block（以等长占位保偏移）——防代码块内YAML示例误伤
    text_nc = re.sub(r'```.*?```', lambda m: '\n' * m.group(0).count('\n'), text, flags=re.DOTALL)
    # 找所有闭合 frontmatter 块：非贪婪匹配 ^---$ ... ^---$
    FM_KEY = re.compile(r'^\s*(title|type|status|version|date|summary|source|author|complies_with|normative_vocab)\s*:', re.MULTILINE)
    extra = []
    for m in re.finditer(r'(?:^|\n)---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)', text_nc, flags=re.DOTALL):
        if m.start() == 0:
            continue  # 文件开头(位置0)的frontmatter合法
        if FM_KEY.search(m.group(1)):  # 块内含frontmatter键=真双报告（非正文分隔线）
            extra.append(m.start())
    if extra:
        return False, f'双报告污染：文件中部再现闭合frontmatter块(偏移{extra})——单报告单文件约束被破坏'
    return True, 'ok'


def run_check(mode, target):
    """subprocess调skill_eval既有CLI（JSON接口稳定·不import防副作用）。
    Returns dict（解析失败→{'passed': False, 'error': ...}）"""
    try:
        proc = subprocess.run(
            [sys.executable, SKILL_EVAL, mode, target],
            capture_output=True, text=True, timeout=120)
        return json.loads(proc.stdout)
    except Exception as e:  # 解析失败/超时=检查不可用=不放行（fail-closed）
        return {'passed': False, 'error': f'{mode} 执行/解析失败: {e}'}


def check_report_grade(report_path, mech_grade):
    """等级一致性校验（v3.31.6新增·等级口径根治门禁·皮叔 2026-08-09 拍板）。
    报告声明的等级（**X级·** 或 | 等级 | **X级）必须 == skill_eval 机械 grade（compute_grade 唯一真相源）。
    不一致=等级口径漂移（AI 自创加权映射）→ 拒封口。识别全部等级声明（防漏检）。"""
    try:
        with open(report_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError:
        return False, f'报告读取失败: {report_path}'
    # 抓取报告中的最终等级声明（兼容 "**S级·通过**" / "**S级**" / "**S 级 · 通过**" 等形态）
    # ⛔只认"最终等级行"（等级/综合/最终评级/结论行的 **X级），初评/首评/复评对照（如"初评 C级→复评 S级"）不计入——
    # 历史对照是事实记录，非等级声明（2026-08-09 修正：shall-we-talk/sucair 修复闭环报告含 C/B 对照被误伤）。
    grades_found = set()
    # 行首锚定的等级/综合/最终评级/结论块行
    for m in re.finditer(r'^\|\s*(?:等级|\*\*综合\*\*|最终评级|综合等级)\s*\|\s*\*\*?([SABC])\s*级', text, re.MULTILINE):
        grades_found.add(m.group(1))
    if not grades_found:
        # 兜底：结论块 "**X级·通过/不通过**"（无表格行时）
        for m in re.finditer(r'\*\*([SABC])\s*级\s*·\s*(?:通过|不通过)', text):
            grades_found.add(m.group(1))
    if not grades_found:
        return False, '报告无最终等级声明（须写"等级 | **X级**"或"**X级·通过**"）——等级缺失拒封口'
    bad = [g for g in grades_found if g != mech_grade]
    if bad:
        return False, (f"报告等级口径漂移: 最终等级声明{bad} ≠ 机械grade {mech_grade}"
                       f"——等级唯一真相源=skill_eval compute_grade，⛔DO NOT自创加权映射（2026-08-09你定）")
    return True, f'报告等级 {mech_grade} == 机械grade（单一真相源）'


def check_overdue_freeze(skill_path):
    """双盲欠账冻结门禁（v3.33.4新增·P2-1·QClaw双盲6th实锤：overdue_n≥2硬门禁原为prose级自觉）。
    仅对被评对象=clock-loop 自身生效（SKILL.md门禁③语义：clock-loop 自升级交付前须清双盲欠账）——
    其他 Skill 的评估封口不受 clock-loop 体系欠账牵连。overdue_n≥2 → 拒封口（物理阻断·非自觉）。"""
    if 'clock-loop' not in os.path.basename(os.path.dirname(os.path.abspath(skill_path))) and \
       'clock-loop' not in os.path.abspath(skill_path):
        return True, '非clock-loop自身评估——overdue冻结不适用'
    try:
        gate_script = os.path.join(SCRIPT_DIR, 'check_selfimprove_gate.py')
        proc = subprocess.run([sys.executable, gate_script], capture_output=True, text=True, timeout=60)
        data = json.loads(proc.stdout)
        # v3.50.1（#40 fail-open根治）：gate异常退出/带gate_error → 拒放行（异常≠欠账清零）
        if proc.returncode != 0 or data.get('gate_error'):
            return False, (f'overdue_gate 执行异常（exit={proc.returncode}·gate_error={data.get("gate_error")}）'
                           f'——fail-closed：无法确认欠账状态=不放行')
        overdue = int(data.get('double_blind_overdue_n', 0))
        if overdue >= 2:
            return False, (f'🔴 双盲欠账{overdue}次≥2——clock-loop自身版本升级交付冻结：'
                           f'须先清双盲欠账（SKILL.md门禁③·v3.33.4物理化）')
        return True, f'双盲欠账{overdue}次（<2·未触发冻结）'
    except Exception as e:
        return False, f'overdue_gate执行失败: {e}（fail-closed·不误放行）'


def check_promise_overdue(skill_path):
    """承诺欠账核销门禁（v1.8.0新增·C05承诺核销制·#129"挂了挡没接变速箱"）。
    读 steps/counter_conditional_promises.md 的 overdue_promises 计数——条件式承诺台账（A20建·零脚本消费实锤）：
    ≥2 → 拒封口（台账闹钟阈值：阻断"✅交付完成"声明）· =1 → 汇报不阻断（你待裁决项·机器不代决）· 0 → 通过。
    仅对被评对象=clock-loop 自身生效（同 overdue_freeze_guard 语义）。文件不存在→0（台账幂等规则）；
    存在但解析失败→fail-closed 拒放行（异常≠清零·v3.50.1 先例）。"""
    if 'clock-loop' not in os.path.basename(os.path.dirname(os.path.abspath(skill_path))) and \
       'clock-loop' not in os.path.abspath(skill_path):
        return True, '非clock-loop自身评估——承诺欠账门禁不适用'
    counter_path = os.path.join(SCRIPT_DIR, '..', 'steps', 'counter_conditional_promises.md')
    if not os.path.isfile(counter_path):
        return True, 'counter_conditional_promises.md 不存在——overdue_promises=0（台账幂等）'
    try:
        with open(counter_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError as e:
        return False, f'counter台账读取失败: {e}（fail-closed·不误放行）'
    m = re.search(r'^overdue_promises\s*:\s*(\d+)', text, re.M)
    if not m:
        return False, 'counter台账缺 overdue_promises 计数行（格式异常·fail-closed·需人工核查）'
    overdue = int(m.group(1))
    if overdue >= 2:
        return False, (f'🔴 条件式承诺欠账{overdue}条≥2——阻断"✅交付完成"声明：'
                       f'须先核销条件式承诺（C05承诺核销制·台账闹钟阈值）')
    if overdue == 1:
        return True, f'条件式承诺欠账1条（<2·未阻断）——⚠收尾门禁逐条汇报（你待裁决·机器不代决）'
    return True, '条件式承诺欠账0条（全部核销）'


def check_verdict_presentation(report_path):
    """双轨呈现校验（v3.33.0新增·皮叔拍板：采纳者只看等级+验证深度，raw/capped/总分%数字进台账区不端给用户）。
    ①结论区必须含「验证深度」行且值为人话标签（静态文档级/实测通过/部分实测）
    ②结论区（排除双章诚实行）+最终评级区出现 raw/capped/`N/100` 数字 → 拒封口。
    设计端消除为主（模板v1.3.0已改），本检查为防错层兜底（§一1.1：绕过成本>遵守成本+全程留痕）。"""
    try:
        with open(report_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError:
        return False, f'报告读取失败: {report_path}'
    # 区A：评估结论表（## 评估结论 到 下一个 ## 段）
    m = re.search(r'## 评估结论\s*(.*?)(?=\n## )', text, re.S)
    concl = m.group(1) if m else ''
    if not concl:
        return False, '报告缺"## 评估结论"区'
    if not re.search(r'\|\s*验证深度\s*\|', concl):
        return False, '结论区缺"验证深度"行（v3.33.0双轨呈现：等级+验证深度）——拒封口'
    if not re.search(r'(静态文档级|实测通过|部分实测)', concl):
        return False, '验证深度行值非人话标签（须:静态文档级·未实测/实测通过/部分实测）——拒封口'
    # 结论区数字检查（排除双章诚实行——内部诚实章台账行，不属用户区）
    # v3.33.1：允许等级行单一机检分（如"机检 95/100"可追问差在哪·皮叔拍板）；raw/capped 无条件禁；N/100 ≥2次=三数并列回潮→拒
    concl_no_honest = '\n'.join(l for l in concl.splitlines() if not l.strip().startswith('| 双章诚实'))
    bad_codes = re.findall(r'raw\s*\d+|capped\s*\d+', concl_no_honest)
    if bad_codes:
        return False, f'结论区出现内部账本编码{bad_codes[:3]}（v3.33.0/1双轨呈现：⛔raw/capped不进结论区）——拒封口'
    num_occur = len(re.findall(r'\d+\.?\d*\s*/\s*100', concl_no_honest))
    if num_occur > 1:
        return False, f'结论区出现{num_occur}个 /100 分数（v3.33.1只许等级行单一机检分——三数并列回潮）——拒封口'
    # 区B：最终评级表（## 最终评级 到 下一个 ## 段）
    m2 = re.search(r'## 最终评级\s*(.*?)(?=\n## |\Z)', text, re.S)
    final_sec = m2.group(1) if m2 else ''
    if final_sec:
        bad_nums2 = re.findall(r'raw\s*\d+|capped\s*\d+', final_sec)
        if bad_nums2:
            return False, f'最终评级表出现内部账本编码{bad_nums2[:3]}（v3.33.0/1双轨呈现）——拒封口'
    return True, '双轨呈现合规（等级+单一机检分+验证深度·无内部账本编码进用户区）'


def check_smoke_evidence(report_path):
    """门禁16判据（v4.12.3·独立可测函数）：报告宣称「实测通过」→ 必携 `冒烟证据:` 行且绝对路径磁盘实存。
    非"实测通过"标签（静态文档级/部分实测/未实测）为本门合法终态不强制。fail-closed：读取异常=红。"""
    import re as _re
    if not report_path or not os.path.isfile(report_path):
        return True, '报告缺失由existence守卫·本门跳过'
    try:
        with open(report_path, encoding='utf-8', errors='replace') as f:
            _rp = f.read()
    except Exception as _e:
        return False, f'smoke_evidence_guard 读取失败: {_e}'
    if '实测通过' not in _rp:
        return True, '未宣称"实测通过"→不强制证据（静态文档级/部分实测为合法终态）'
    _ms = _re.findall(r'冒烟证据[:：]\s*([^\n]+)', _rp)
    _paths = [p.strip() for seg in _ms for p in _re.split(r'[,、]', seg) if p.strip().startswith('/')]
    if not _paths:
        return False, '报告宣称"实测通过"但无 `冒烟证据:` 行（标签无产物绑定=不可防伪·v4.12.3）'
    _missing = [p for p in _paths if not os.path.exists(p)]
    if _missing:
        return False, f'冒烟证据路径不存在: {_missing[:3]}（宣称与实物不符）'
    # v4.12.4·R4-F-A：自指证据无效（报告给自己当"冒烟证据"=零信息）
    _rp_abs = os.path.abspath(report_path)
    if any(os.path.abspath(p) == _rp_abs for p in _paths):
        return False, '冒烟证据含报告自身路径（自指证据=零信息·v4.12.4）'
    return True, (f'冒烟证据 {len(_paths)} 条磁盘实存且非自指（本门只证"存在性"不证"产物归属相关性"'
                   '——相关性属机械域外·见 known-limitations ·v4.12.4 措辞如实化）')


def check_candidate_verdict(skill_path, report_path):
    """candidate 裁决记录检查（v3.34.0新增·治"带 candidate 交付"）。
    .phaseX_last_run.json 的 per_check_reason 中 candidate-found 项，报告候选处置台账必须逐项裁决。"""
    run_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.phaseX_last_run.json')
    if not os.path.isfile(run_json):
        return True, 'skip: 无 .phaseX_last_run.json（未跑机检）'
    try:
        with open(run_json, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return False, f'.phaseX_last_run.json 解析失败: {e}'
    # 机检 target 必须匹配被评估对象（防读错对象的机检数据）
    target = data.get('target', '')
    skill_file = skill_path if not os.path.isdir(skill_path) else os.path.join(skill_path, 'SKILL.md')
    # v4.12.2·R2-N-03：旧绑定只比 basename——两侧恒等"SKILL.md"，任意他Skill机检产物可冒充（文件名级身份=纸锁）
    _t_norm = os.path.normcase(os.path.abspath(target if target.lower().endswith('skill.md')
                                                else os.path.join(target, 'SKILL.md'))) if target else ''
    _s_norm = os.path.normcase(os.path.abspath(skill_file))
    if not target or _t_norm != _s_norm:
        return False, (f'机检 target({target or "空"}) ≠ 被评估对象({skill_file})（全路径比对·v4.12.2）'
                       f'——机检数据不是本对象的，重跑 skill_eval --check-only 再封口')
    pcr = data.get('evidence', {}).get('per_check_reason', {})
    candidates = [k for k, v in pcr.items() if v == 'candidate-found']
    if not candidates:
        return True, '无 candidate-found 项（全部 checked-clean）'
    try:
        with open(report_path, encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError:
        return False, f'报告读取失败: {report_path}'
    if '候选处置台账' not in text:
        return False, f'candidate-found {len(candidates)} 项({candidates})但报告无"候选处置台账"段——须逐项裁决（清零证据或显式说明）'
    verdict_words = ['采纳', '降级', '合并', '挂起', '证据不支持', '路由']
    count = sum(text.count(w) for w in verdict_words)
    if count < len(candidates):
        return False, f'台账处置记录({count}处) < candidate 数({len(candidates)})——须逐项裁决'
    # ── v3.49.0（#108逆向论证锁机械校验）：降级/证据不支持/挂起必须附逆向论证 ──
    # 判据源：review-protocol L82"如果这个判定错了，会怎样？——写不出具体后果=不许降级，回退为采纳"
    # 病根（#108）：旧校验只数关键词，写"降级"两字就过＝纸锁；同节挂起态二要素有 delivery_summary_guard 管，
    # 逆向论证却没有——同一节一个有脚本管一个没有。
    sec = re.split(r'^#+.*候选处置台账.*$', text, maxsplit=1, flags=re.M)
    ledger_text = ''
    if len(sec) > 1:
        tail = sec[1]
        stop = re.search(r'^#+\s', tail, flags=re.M)
        ledger_text = tail[:stop.start()] if stop else tail
    scope = ledger_text if ledger_text.strip() else text
    # 排除否定行（"本轮无挂起项/无降级"不是处置记录）
    scope_lines = [ln for ln in scope.splitlines()
                   if not re.search(r'无(候选|挂起|降级|处置)|本轮无', ln)]
    scope_pos = '\n'.join(scope_lines)
    if any(w in scope_pos for w in ('降级', '证据不支持', '挂起')):
        has_reverse = ('逆向论证' in scope_pos) and bool(
            re.search(r'如果[^。\n]{0,50}(错|不成立|误判)', scope_pos))
        if not has_reverse:
            return False, ('台账含 降级/证据不支持/挂起 处置但缺逆向论证'
                           '（须写明"如果这个判定错了，会怎样"的具体后果）'
                           '——写不出具体后果=不许降级，回退为采纳（review-protocol 逆向论证锁·#108·v3.49.0）')
        return True, (f'台账处置记录({count}处) ≥ candidate 数({len(candidates)})'
                      '·降级类处置逆向论证校验通过')
    return True, f'台账处置记录({count}处) ≥ candidate 数({len(candidates)})·无降级类处置'


def check_review_trail(report_path):
    """审查轮次记录存在性（v3.34.0新增·治"修完未审交付"）: 报告须含审查结果段。"""
    try:
        with open(report_path, encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError:
        return False, f'报告读取失败: {report_path}'
    for marker in ('子 Agent 审查', '子Agent审查', '审查结果', '审查轮次'):
        if marker in text:
            return True, f'报告含审查记录段（{marker}）'
    return False, '报告缺审查轮次记录段（子 Agent 审查结果）——修复未审不可封口'


def check_delivery_summary(report_path):
    """📢 交付摘要存在性（v3.34.2新增·对话框结论单一真相源）: 报告必含双轨段+CTA。
    v3.34.3扩展: 挂起分层——有挂起须呈现（你待决区或CTA可延后行），无挂起须显式声明"本轮无挂起项"。"""
    try:
        with open(report_path, encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError:
        return False, f'报告读取失败: {report_path}'
    checks = {
        '📢 评估结论': '📢 评估结论' in text,
        '✅ 结果': '✅ 结果' in text,
        '验证深度': '验证深度' in text,
        '一句话': '一句话' in text,
        '📢 接下来你可以': '📢 接下来你可以' in text,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        return False, f'📢 交付摘要缺项: {missing}——对话框结论必须从报告搬运，缺失=拒封口'
    # v3.34.3: 挂起分层校验——有挂起须呈现，无挂起须显式声明
    has_pending = '挂起' in text or '待决' in text or '待你定' in text
    has_pending_section = ('🧭 你待决' in text) or ('🟢 可延后决策' in text)
    has_no_pending_decl = '本轮无挂起项' in text
    if has_pending and not has_pending_section:
        return False, '报告含挂起项但无挂起呈现区（🧭 你待决/🟢 可延后决策）——挂起须按阻塞性分层呈现，缺失=拒封口'
    if not has_pending and not has_no_pending_decl:
        # 无挂起时需显式声明（防静默）；但历史报告无此声明时放宽（向后兼容）
        if '归档封口确认块' in text:
            return True, '📢 交付摘要齐全（双轨+CTA）；无挂起项（历史格式，未含显式声明）'
        return False, '报告无挂起项声明（须写"本轮无挂起项"或呈现挂起区）——防静默，缺失=拒封口'
    return True, '📢 交付摘要齐全（双轨+CTA+挂起分层）——对话框搬运源就绪'


def finalize(skill, report, archive_root=DEFAULT_ARCHIVE_ROOT):
    """16道检查 → 封口确认块dict。（v4.12.3 门禁15共享record_fix实装+位次=编号对齐；门禁16=冒烟证据产物绑定；test#7 看护 编号↔声明↔append 三线一致）sealed=True 当且仅当全部硬门禁通过。"""
    detail = []
    # ── 硬门禁1：报告文件存在性（门禁⓪等价·确定性os.path.exists） ──
    exists = os.path.exists(os.path.expanduser(report))
    detail.append(('existence', exists, report if exists else f'报告不存在: {report}'))
    # ── 硬门禁2：归档路径校验（阶段4"写入前路径阻断"同源） ──
    path_ok, path_reason = check_archive_path(report, archive_root)
    detail.append(('path_guard', path_ok, path_reason))
    # ── 硬门禁3：单报告纯净度（v3.24.0·L3沉淀模式J·双报告污染拒封） ──
    if exists:
        purity_ok, purity_reason = check_single_report(report)
    else:
        purity_ok, purity_reason = False, 'skipped: report missing'
    detail.append(('purity_guard', purity_ok, purity_reason))
    # ── 硬门禁4：check-only（Phase X机检·封口时重跑取实录·防.phaseX缓存伪造） ──
    co = run_check('--check-only', skill) if exists else {'passed': False, 'error': 'skipped: report missing'}
    # v3.31.2修复(P1-1·皮叔确认): honest_pass 透传不阻断——d5尺寸红字(框架自指账·皮叔07-27裁"不为指标动热路径")
    # 仅显形不堵死交付；其他真红字(固化引用漂移/capped<70/基础raw_pass未过)仍拦截封口。
    _co_flags = co.get('honest_flags') or []
    _co_nond5 = [f for f in _co_flags if not str(f).startswith('d5')]  # v3.33.3: 前缀匹配替代精确字符串（双盲6th P2-4·防d5描述变更误判）
    _check_only_ok = bool(co.get('passed')) or (bool(_co_flags) and not _co_nond5)
    detail.append(('check_only', _check_only_ok, co.get('error') or f"score={co.get('total_score')}·honest_flags={_co_flags}"))
    # ── 硬门禁5：check-l1l2（门禁④·L1/L2实质内容） ──
    l1l2 = run_check('--check-l1l2', report) if exists else {'passed': False}
    detail.append(('check_l1l2', bool(l1l2.get('passed')), l1l2.get('error') or f"l1={l1l2.get('l1_substance')} l2={l1l2.get('l2_substance')}"))
    # ── 硬门禁6：check-report-content（门禁⑤·honest_pass消费·na=非E/F放行） ──
    rc = run_check('--check-report-content', report) if exists else {'passed': False, 'na': False}
    rc_ok = bool(rc.get('passed')) or bool(rc.get('na'))
    detail.append(('check_report_content', rc_ok, rc.get('error') or f"na={rc.get('na')} honest_consumed={rc.get('honest_pass_consumed')}"))
    # ── 硬门禁7：grade_guard（v3.31.6新增·等级判定唯一真相源·皮叔拍板根治等级口径混乱） ──
    mech_grade = co.get('grade')  # check-only 输出的机械 grade（compute_grade 唯一真相源）
    if exists and mech_grade:
        grade_ok, grade_reason = check_report_grade(report, mech_grade)
    elif exists:
        grade_ok, grade_reason = False, 'skill_eval 未输出 grade 字段（--check-only 需 v2.9.8+）'
    else:
        grade_ok, grade_reason = False, 'skipped: report missing'
    detail.append(('grade_guard', grade_ok, grade_reason))
    # ── 硬门禁8：verdict_guard（v3.33.0新增·双轨呈现·皮叔拍板：用户只看等级+验证深度） ──
    if exists:
        vd_ok, vd_reason = check_verdict_presentation(report)
    else:
        vd_ok, vd_reason = False, 'skipped: report missing'
    detail.append(('verdict_guard', vd_ok, vd_reason))
    # ── 硬门禁9：overdue_freeze_guard（v3.33.4新增·双盲6th P2-1·overdue_n≥2物理冻结clock-loop自升级） ──
    if exists:
        of_ok, of_reason = check_overdue_freeze(skill)
    else:
        of_ok, of_reason = False, 'skipped: report missing'
    detail.append(('overdue_freeze_guard', of_ok, of_reason))
    # ── 硬门禁10：candidate_verdict_guard（v3.34.0新增·candidate-found 须有裁决记录） ──
    if exists:
        cv_ok, cv_reason = check_candidate_verdict(skill, report)
    else:
        cv_ok, cv_reason = False, 'skipped: report missing'
    detail.append(('candidate_verdict_guard', cv_ok, cv_reason))
    # ── 硬门禁11：review_trail_guard（v3.34.0新增·修复未审不可封口） ──
    if exists:
        rt_ok, rt_reason = check_review_trail(report)
    else:
        rt_ok, rt_reason = False, 'skipped: report missing'
    detail.append(('review_trail_guard', rt_ok, rt_reason))
    # ── 硬门禁12：delivery_summary_guard（v3.34.2新增·对话框结论单一真相源） ──
    if exists:
        ds_ok, ds_reason = check_delivery_summary(report)
    else:
        ds_ok, ds_reason = False, 'skipped: report missing'
    detail.append(('delivery_summary_guard', ds_ok, ds_reason))
    # ── 硬门禁13：promise_overdue_guard（v1.8.0新增·C05承诺核销制·条件式承诺台账零脚本消费实锤→装机械触发器） ──
    if exists:
        po_ok, po_reason = check_promise_overdue(skill)
    else:
        po_ok, po_reason = False, 'skipped: report missing'
    detail.append(('promise_overdue_guard', po_ok, po_reason))
    # ── 硬门禁14：evidence_precondition（v4.9.0新增·取证锁 L1证据行+L2断言计数·物理约束与防误§七） ──
    # 证：最终判据=所有原生真相断言须能在源找得到；AI 自述取证的 locked 声明一律不采信（重跑取证）。
    # 存量兼容：报告无任何断言行（旧格式）→ N/A 放行（防卡死历史报告）；有断言行才强制校验。
    if exists:
        ev = run_check('--check-evidence', report)
        for d in (ev.get('detail') or []):
            if '无任何' in d:  # 无断言行=该报告未带断言证据（旧格式）→ N/A
                ev = {'passed': True, 'na': True, 'detail': [d]}
                break
        ev_ok = bool(ev.get('passed'))
    else:
        ev_ok, ev = False, {'passed': False, 'detail': ['skipped: report missing']}
    detail.append(('evidence_precondition', ev_ok, ev.get('detail') or '取证锁通过'))

    # ── 硬门禁15：pending_review_guard（v4.12.3 共享实装·R3攻3根治：finalize自带算法与record_fix对同台账给相反结论=双实现必漂移；物理位次=编号对齐） ──
    try:
        import importlib.util as _ilu
        _rf_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'record_fix.py')
        _spec = _ilu.spec_from_file_location('record_fix_g15', _rf_p)
        _rfm = _ilu.module_from_spec(_spec)
        _obw = sys.dont_write_bytecode; sys.dont_write_bytecode = True  # importlib写pyc会污染scripts/触发同竞态(v4.12.4b)
        try:
            _spec.loader.exec_module(_rfm)
        finally:
            sys.dont_write_bytecode = _obw
        _g15_days, _g15_oldest, _g15_n, _g15_msg = _rfm.check_pending_review_overdue()
        if _g15_days is None:
            g15_ok, g15_note = False, f'pending_review fail-closed：{_g15_msg}'
        elif _g15_days >= getattr(_rfm, 'BLOCK_DAYS', 14):
            g15_ok, g15_note = False, f'🔴 {_g15_msg}'
        else:
            g15_ok, g15_note = True, _g15_msg
    except Exception as _e:
        g15_ok, g15_note = False, f'pending_review_guard 运行失败: {_e}（fail-closed）'
    detail.append(('pending_review_guard', g15_ok, g15_note))

    # ── 硬门禁16：smoke_evidence_guard（v4.12.3新增·R3-N-06："实测通过"标签无产物绑定=从未实测也能宣称实测） ──
    g16_ok, g16_note = check_smoke_evidence(report)
    detail.append(('smoke_evidence_guard', g16_ok, g16_note))

    sealed = all(ok for _, ok, _ in detail)
    # v3.27.0归一：co['passed']=诚实章（唯一结论），raw_pass=旧口径历史可比
    block = {
        'seal': f'finalize_report.py v{__version__}',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'skill': skill,
        'report': report,
        'report_sha8': report_sha8(os.path.expanduser(report)) if exists else None,
        'sealed': sealed,
        'checks': {name: ('✅' if ok else '🔴') for name, ok, _ in detail},
        'passed': co.get('passed'),  # v3.27.0归一：诚实章（唯一结论）
        'honest_flags': co.get('honest_flags'),  # 红字清单
        'raw_pass': co.get('raw_pass'),  # 旧口径历史可比通道
        'advisories': rc.get('advisories'),
        'detail': [f"{'✅' if ok else '🔴'} {name}: {msg}" for name, ok, msg in detail],
    }
    if not co.get('passed'):
        block['warning'] = '⛔ 诚实章未过——红字清单见honest_flags（v3.27.0双章归一·passed=诚实章唯一结论）'
    # v3.34.0 人类终审环节：封口确认块输出你抽查点建议（终审权在你，AI 不代签）
    block['human_check'] = {
        'note': '🛡️ 你抽查点（终审权在你）：建议核对 ①本封口块 report_sha8 与报告实际 sha8 一致 ②check_only passed 值与 .phaseX_last_run.json 一致 ③任选 1 项数字断言回源核验',
        'owner': '你',
    }
    return block


def reseal_sha8(report_path):
    """v1.6.1 存量修复：重算已贴块报告的 report_sha8 并回填（幂等·原子写·留痕）。

    背景：v1.6.0 剔离正则漏剔前置 `---` → 9/9 自动回贴报告的声明sha8 与重算值不符（实测100%复现）。
    本函数用修好的 SEAL_STRIP_RE 重算并回填，使防伪锚恢复有效（双盲复现/你抽查不再误判"造假"）。
    ⛔不改报告正文任何内容，只改封口块 JSON 内的 report_sha8 与 seal 两字段。
    Returns exit code: 0=成功（含已一致无需改）| 1=无封口块/读写失败 | 2=参数错
    """
    rp = os.path.expanduser(report_path)
    if not os.path.isfile(rp):
        print(json.dumps({'ok': False, 'error': f'报告不存在: {rp}'}, ensure_ascii=False))
        return 1
    with open(rp, 'r', encoding='utf-8', errors='replace') as f:
        body = f.read()
    if SEAL_HEADER not in body:
        print(json.dumps({'ok': False, 'changed': False,
                          'error': '报告无封口确认块——无需回填（未走过自动回贴）'}, ensure_ascii=False))
        return 1
    new_sha = report_sha8(rp)          # 剔离封口块后重算（幂等）
    pat = re.compile(r'("report_sha8"\s*:\s*")([0-9a-f]{8})(")')
    m = pat.search(body)
    if not m:
        print(json.dumps({'ok': False, 'error': '封口块内未找到 report_sha8 字段（格式异常·需人工核查）'},
                         ensure_ascii=False))
        return 1
    old_sha = m.group(2)
    if old_sha == new_sha:
        print(json.dumps({'ok': True, 'changed': False, 'report_sha8': new_sha,
                          'note': '声明值与重算值已一致——无需回填（幂等）'}, ensure_ascii=False))
        return 0
    fixed = pat.sub(lambda mm: mm.group(1) + new_sha + mm.group(3), body, count=1)
    # seal 字段同步标注修复来源（版本取 __version__ 单一真相源）
    fixed = re.sub(r'("seal"\s*:\s*")([^"]*)(")',
                   lambda mm: mm.group(1) + f'finalize_report.py v{__version__}' + mm.group(3),
                   fixed, count=1)
    tmp = rp + '.reseal.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(fixed)
        os.replace(tmp, rp)            # 原子写（照 record_fix.save 先例）
    except OSError as e:
        print(json.dumps({'ok': False, 'error': f'回填写入失败: {e}'}, ensure_ascii=False))
        return 1
    # 回填后再算一次——必须仍等于 new_sha（否则回填自身破坏了幂等）
    verify = report_sha8(rp)
    print(json.dumps({'ok': True, 'changed': True, 'old_sha8': old_sha, 'new_sha8': new_sha,
                      'post_write_verify': verify, 'idempotent': verify == new_sha,
                      'note': f'sha8 由 v{__version__} 重算回填（治 v1.6.0 剔离正则漏剔前置---的幂等缺陷）·正文零改动'},
                     ensure_ascii=False))
    return 0 if verify == new_sha else 1


def main():
    # ── v1.7.0：启动幂等性自检（让漂移在封口前被逮出·C-090）──
    # 剔离正则与回贴格式一旦再次漂移，⛔不允许带着坏防伪锚去封口任何报告。
    _sc_ok, _sc_detail = _selfcheck_idempotency()
    if not _sc_ok:
        print(json.dumps({
            'sealed': False,
            'error': f'幂等性自检失败（SEAL_STRIP_RE 与 build_seal_section 格式漂移）: {_sc_detail}',
            'hint': '⛔不得绕过本自检封口——先修剔离正则或回贴格式使两者同源，再重跑',
        }, ensure_ascii=False))
        sys.exit(2)

    ap = argparse.ArgumentParser(description='评估报告归档封口物理锁')
    ap.add_argument('--skill', required=False, help='被评估SKILL.md或其目录')
    ap.add_argument('--report', required=False, help='评估报告绝对路径（须在test_results/下）')
    # v1.6.1 存量修复通道：重算已贴块报告的 report_sha8 并回填（幂等·可重跑）
    ap.add_argument('--reseal-sha8', action='store_true',
                    help='重算 --report 指定报告的 report_sha8 并回填到已贴封口块（治 v1.6.0 存量失效）')
    args = ap.parse_args()

    if args.reseal_sha8:
        if not args.report:
            print(json.dumps({'ok': False, 'error': '--reseal-sha8 需搭配 --report <报告路径>'}, ensure_ascii=False))
            sys.exit(2)
        sys.exit(reseal_sha8(args.report))

    if not args.skill or not args.report:
        print(json.dumps({'ok': False, 'error': '封口模式需 --skill 与 --report 两个参数'}, ensure_ascii=False))
        sys.exit(2)

    if not os.path.exists(SKILL_EVAL):
        print(json.dumps({'sealed': False, 'error': f'skill_eval.py不存在: {SKILL_EVAL}'}, ensure_ascii=False))
        sys.exit(2)

    block = finalize(args.skill, args.report)

    # v1.6.0 (2026-09-02): 封口确认块自动回贴报告正文——双盲第9次实锤"0/12报告粘贴缺位"
    # 且童灵监理2026-09-02实锤本轮复发0/4。根治=机制代意志：sealed=true 即机械回贴，
    # 不再依赖 AI 记得执行"原样粘贴"环节。幂等性由 report_sha8() 的确认块剔离保证。
    if block.get('sealed') and block.get('report') and block.get('report_sha8'):
        rp = os.path.expanduser(block['report'])
        try:
            with open(rp, 'r', encoding='utf-8', errors='replace') as f:
                body = f.read()
            if SEAL_HEADER not in body:
                # v1.6.1：改调 build_seal_section()（生产唯一出口）——⛔不得在此手写段格式，
                # 原因是手写与实际格式不一致时幂等测试会报绿而生产静默失效（v1.6.0 实锤）。
                with open(rp, 'a', encoding='utf-8') as f:
                    f.write(build_seal_section(block))
                block['auto_pasted'] = True
            else:
                block['auto_pasted'] = 'already_present'
        except OSError as e:
            block['auto_pasted'] = False
            block['auto_paste_error'] = str(e)

    # 留痕：无论成败都写.finalize_last_run.json（绕过留痕锚点之一）
    with open(LAST_RUN_PATH, 'w', encoding='utf-8') as f:
        json.dump(block, f, ensure_ascii=False, indent=2)
    print(json.dumps(block, ensure_ascii=False, indent=2))
    sys.exit(0 if block['sealed'] else 1)


if __name__ == '__main__':
    main()
