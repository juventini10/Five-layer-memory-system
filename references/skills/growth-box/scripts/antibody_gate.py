#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
antibody_gate.py —— 抗体写入端机械门禁 + 标准生成器
Version: 1.8.0（首版 1.0.0·2026-09-15；现行判据 C1~C12·真值取本件 VERSION 常量，v4.12.3 补历史注）

定位：抗体（反哺日志 `🛡 复发检测条件` 字段）的**唯一校验器**——
      写入端（E4/E5）拦截 + 巡检端（growth_box_check / Stop 守卫）复核，三处共用本实现（单一真相源）。

为什么存在（第一性原理）：
  坏抗体的成因 = 「AI 手写 shell 命令 + 靠文本清单自检」。
  已知失败模式是**有限枚举**（4 类实证事故），故设计端无法消除的部分由本门禁物理拦截：
    C1 空/占位      —— 2026-08-24 PAT-014 占位符稀释计数
    C2 多行         —— Schema 要求单行命令
    C3 语法错       —— v1.13.0 已列要求但无脚本执行（文本清单）
    C4 恒真形态     —— 2026-09-06 证据链抗体 `&& exit 0 || exit 0` 恒真刷屏 20+ 次，污染复发记录吞真警报（ERR-20260906-002）
    C5 相对路径     —— 2026-08-21 并行会话 4 条相对路径抗体 → 2 假命中 + 2 假免疫
    C6 重复抗体     —— 同一检测条件反复沉淀，稀释台账信噪比
    C7 恒假形态     —— 取数格式与被检输出不同源（od/xxd 输出双空格 vs 模式单空格）→ 探针永不命中=坑永远报不出来
    C8 命令位不可执行 —— 裸脚本放命令位返回 126，被 `!` 反断言翻成 exit 0=假红（C4/C7 两种形态都检不出）
    C9 检测对象错位 —— detect 问的是「账本里有没有未结案条目提到某词」而非「该行为是否再犯」
                       实证：2026-09-19 免疫终审一次退役 7 条此形态抗体（各累计假命中 26 次上下）；
                       learnings 长期存在 pending 条目 ⇒ 此类 detect **永不免疫**，与恒真同害。
    C10 平台反转形态  —— `grep -L` 放在**决定退出码的末段**：GNU 下 0=有文件被选中（锚缺=坑在），
                       BSD/macOS 下 0=全部文件都含锚（坑已修）——两端恰好相反 ⇒ Mac 端既造假命中
                       （177 条实证）又对真复发永久漏报（方向反了≠恒真·比恒真更隐蔽，C4 看不见它）。
                       实证：8 条「框架缺该专项段=坑在·exit0」型抗体按 GNU 直觉书写，在 macOS 上
                       锚在→rc0 被读作命中、锚缺→rc1 被读作免疫。修法 `! grep -q "锚" <绝对路径>`
                       （两端一致）。范围：仅末段·仅大写 -L（`-l/-rl` 两端一致不拦；-L 落管道中段
                       而退出码来自末段 `grep -q .` 者不拦——防过宽，实测既有 77 条零误伤）。

    C11 否定式提及独占命中 —— 决定段单文件 grep 的模式在目标文件只以"非…"前缀出现=词面假红（S1061 同案·写入端拦）
                       ※ v1.7.0 落地时漏登记本清单，2026-10-12 随 C12 同批补入（预存缺口·非新病）。
    C12 登记态与声明不符（v1.8.0）—— --expect clean|hit：写入端登记时实跑抗体，实测态≠声明态拦。
                       治"方向反抗体"：反断言配坑词（! grep 已被清除的陈旧词）＝坑修好后恒红。
                       实证 2026-10-12 R-20261012-02 初版抗体，语义方向 C1~C11 全检不出；
                       而"本条落地后坑应已干净"是登记侧已知事实，声明与实盘对撞即可机械判定（承 C7 同源思想）。

设计边界（诚实声明）：
  本门禁只做**静态**判定，⛔不执行抗体命令（抗体由不可靠起草者产出，执行=风险；
  且反断言形态在"路径不存在"时天然 exit 0，动态探针会误报——见 tests 负例）。
  动态可证伪性由 growth_box_check.sh 巡检期的"命中/免疫双态留痕"承担。

接口契约（供其他脚本 import）：
  validate_cmd(cmd, label="") -> list[Violation]

用法：
  antibody_gate.py --check-cmd '<cmd>' [--label 标题] [--expect clean|hit]   # 单条校验（写入端·E4 前；--expect=登记态自证 C12）
  antibody_gate.py --scan [文件...]                        # 全量扫描（默认双源）
  antibody_gate.py --gen file-missing <绝对路径> [--label 标题]   # 生成标准抗体
  antibody_gate.py --selftest                              # 门禁自检（负例夹具）
  antibody_gate.py --json                                  # 结构化输出

退出码：0 = 全通过；1 = 存在违规（Fail-Closed）；2 = 用法错误
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import json
import os
import re
import subprocess
import sys

VERSION = "1.8.1"   # v1.8.1（2026-10-12·B-2 承接）：selftest 去生产依赖——C8/C11 用例自建临时夹具（原写死生产绝对路径且两条判据会读文件；换根实测 rc 0→1，夹具化后换根仍 rc=0）
                  # v1.8.0（2026-10-12 方向反抗体根治）：+C12 登记态自证——--check-cmd 配 --expect clean|hit 时实跑抗体对撞声明（实跑态≠声明=拦；坑词用正断言/正词用反断言的方向语义不可机械判，但登记时点期望态是写侧已知事实）   # v1.7.0（2026-10-01 否定假红根治）：+C11 否定式提及独占命中（决定段单文件 grep 的模式在目标文件只以"非…"前缀出现=词面假红·S1061 同案·写入端拦）
                  # v1.6.0（2026-09-23 免疫验真）：+C10 平台反转形态（`grep -L` 作退出码源·GNU=有文件被选中0／BSD·macOS=全部含锚0，两端相反→Mac 端假命中+真复发漏报；8 条抗体已改 `! grep -q` 反断言并 9/9 双向可证伪）
                  # v1.5.0（2026-09-19）：+C9 检测对象错位（抗体问「账本里是否还有未结案条目提到该词」而非「行为是否复发」→永不免疫）
                    #   根治「未命名抗体」刷屏（CAND-20260918-001 重复9次·不可点名＝死数据）；自测 29→30 例

HOME = os.path.expanduser("~")
DEFAULT_SOURCES = [
    os.path.join(os.path.expanduser("[记忆共享中心]"), "成长箱/experience/规范反哺日志.md"),
]
LEARNINGS_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "成长箱/learnings")

FILE_EXT = r"(?:md|sh|py|json|txt|yml|yaml|ps1|log|toml|cfg|conf)"
FILEEXT_RX = re.compile(r"^[\w.\-]+\.%s$" % FILE_EXT)
RELSEG_RX = re.compile(r"^[\w.\-]+/[\w./\-]*%s$" % ("(?:%s)" % FILE_EXT))
TRUTHY_RX = re.compile(r"^(?:true|:|exit\s+0)$")
# C7（v1.2.0）：取数格式不同源——十六进制/对齐生产器 vs 字面量模式
HEX_PROD_RX = re.compile(r"\b(?:od|xxd|hexdump)\b")
HEX_SPACED_RX = re.compile(r"^[0-9a-fA-F]{2}(?: [0-9a-fA-F]{2})+$")
HEX_CONTIG_RX = re.compile(r"^(?:[0-9a-fA-F]{2}){2,}$")
NORM_RX = re.compile(r"\btr\s+-[a-zA-Z]*[sd]")
QUOTED_RX = re.compile(r"'([^']*)'|\"([^\"]*)\"")

PLACEHOLDER_RX = re.compile(r"^(?:\.{2,}|…+|<[^>]*>|\$\{[^}]*\}|TODO|TBD|xxx+|待填|待补|\-)$", re.I)


class Violation(object):
    __slots__ = ("code", "msg", "detail", "line", "label", "cmd")

    def __init__(self, code, msg, detail="", line=0, label="", cmd=""):
        self.code = code
        self.msg = msg
        self.detail = detail
        self.line = line
        self.label = label
        self.cmd = cmd

    def to_dict(self):
        return {
            "code": self.code,
            "msg": self.msg,
            "detail": self.detail,
            "line": self.line,
            "label": self.label,
            "cmd": self.cmd,
        }


# ── 引号感知扫描 ──────────────────────────────────────────────

def _split_quoted(cmd):
    """返回 (引号片段列表, 去掉引号内容的骨架串)；片段为 (起始下标, 结束下标, 内容)。"""
    inside = []
    out = []
    i = 0
    n = len(cmd)
    while i < n:
        ch = cmd[i]
        if ch == "\\" and i + 1 < n:
            out.append(" ")
            i += 2
            continue
        if ch in "'\"":
            quote = ch
            j = i + 1
            buf = []
            while j < n:
                if cmd[j] == "\\" and quote == '"' and j + 1 < n:
                    buf.append(cmd[j + 1])
                    j += 2
                    continue
                if cmd[j] == quote:
                    break
                buf.append(cmd[j])
                j += 1
            inside.append((i, j, "".join(buf)))
            out.append(" ")
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return inside, "".join(out)


def _mask_substitutions(s):
    """把命令替换 $(...) 与 `...` 的内容掩蔽为空格。

    v1.2.0：其退出码**不传播**到整条命令的退出状态，故判定"整条命令恒真"时
    必须先掩蔽——否则 `X=$(cmd && echo 0 || echo 1)` 这类合法写法被误报为恒真。
    """
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "$" and i + 1 < n and s[i + 1] == "(":
            depth = 1
            j = i + 2
            while j < n and depth:
                if s[j] == "(":
                    depth += 1
                elif s[j] == ")":
                    depth -= 1
                j += 1
            out.append(" ")
            i = j
            continue
        if ch == "`":
            j = s.find("`", i + 1)
            out.append(" ")
            i = (j + 1) if j != -1 else (i + 1)
            continue
        out.append(ch)
        i += 1
    return "".join(out)


PATTERN_ARG_RX = re.compile(r"-(?:i?name|path|i?regex|i?wholename)\s*$")


TOK_RE = re.compile("[\"']?([^\\s\"'|&;]+[.](?:py|sh))[\"']?")
INTERPRETERS = ("python3", "python", "bash", "sh", "zsh", "node", "perl", "ruby", "osascript")


LEDGER_STATUS_RX = re.compile(r"Status[^\n]{0,40}?\b(?:pending|active)\b", re.I)


def _ledger_status_probe(s):
    """C9 判据：detect 取数落在成长箱账本（learnings/**）**且**比对 Status 的 pending/active 取值。

    为什么这是错位：它回答的是「账本里是否还有未结案条目提到某个词」，
    而抗体要回答的是「那个行为是否再度发生」。learnings 长期存在 pending 条目
    （PAT 计数与待晋升队列都靠它），所以此类 detect **永远不会免疫**——与恒真形态同害
    （恒真=永远命中，错位=命中与坑无关）。实证：2026-09-19 免疫终审一次退役 7 条。
    窄口径（两个条件 AND）以免误伤「在 learnings 里查某编号/某条文是否落地」这类合法抗体。
    """
    if "learnings" not in s:
        return None
    if not LEDGER_STATUS_RX.search(s):
        return None
    return ("detect 比对的是成长箱账本的 Status 取值（pending/active），不是行为是否复发；"
            "账本里永远有未结案条目 ⇒ 永不免疫。改法：盯真实复发信号（如 免疫复发记录.md 的新增行、"
            "被检产物文件里的具体证据），或由已晋升条文本体承接后删掉这条 detect")



def _list_flag_platform_flip(s):
    """C10（v1.6.0·2026-09-23 免疫验真）：`grep -L` 作退出码来源 = 平台反转形态。

    GNU：exit 0 = 有文件被选中（=锚缺=坑在）；BSD/macOS：exit 0 = 所有文件都含锚（=坑已修）。
    两端**恰好相反**，故抗体在 Mac 端读数与作者意图反向：坑修好报🔴命中（假命中），
    真复发反而报✅已免疫（永久失明）。实证：8 条「框架缺该专项段=坑在」型抗体在 macOS
    已产 177 条假命中（2026-09-23 实测：锚在 rc=0／锚缺 rc=1）。

    判据范围（防误伤·同 C4 的掩蔽思路）：只看**决定退出码的最后一段**（`|`、`||`、`&&`、
    `;`、换行 切分后的末段，可带 `!` 前缀）；`-L` 出现在管道中段（如 `… | xargs grep -L …
    | grep -q .`）时退出码来自末段，不违规。只认大写 `-L`（`-l/-rl` 两端一致，不拦）。
    """
    payloads = [s] + re.findall(r"\b(?:bash|sh)\s+-c\s+'([^']*)'", s)
    for p in payloads:
        seg = re.split(r"\|\||&&|;|\||\n", p.strip())[-1].strip()
        seg = re.sub(r"^(?:!\s*)+", "", seg)
        if not re.match(r"^grep\b", seg):
            continue
        # 短选项簇里含大写 L（-L / -Ll / -e 前置亦可），排除长选项 --line-buffered 等
        for m in re.finditer(r"\s-([A-Za-z][A-Za-z]*)(?=\s|$)", seg):
            if "L" in m.group(1):
                return ("末段 grep 带 -%s：其退出码在 GNU=「有文件被列出(锚缺)」"
                        "、在 BSD/macOS=「全部文件都含锚(坑已修)」，两端相反 → "
                        "Mac 端假命中 + 真复发漏报。改用 `! grep -q \"锚\" <绝对路径>`"
                        % m.group(1))
    return ""


def _negation_only_hit(s):
    """C11（v1.7.0·2026-10-01 否定假红根治）：决定退出码的末段单文件 grep，其模式在目标
    文件中**只以否定式（前缀"非"）出现**＝词面判据打中否定式提及＝结构性假红。

    实证：S1061 立场卡正文「状态：分身已质证·待你抽检（非你已质证·铁律-022③）」——
    抗体 grep "你已质证" 每日命中，而卡本体合规（否定式自我声明）。词面判据分不清
    「说这事」与「说没这事」；与 PAT-016 宽口径自指同构。v1.2 手工修一条是补丁，
    本判据把否定感知前移到**写入端**（产抗体时拦，防下一条手写抗体重犯）。

    判据范围（防误伤·同 C10 掩蔽思路）：只查**决定退出码的末段**单文件 grep（模式与
    路径都带引号的常见 --gen 形态）；管道中段已被下游 `| grep -v "非…"` 过滤的不拦；
    模式长度>=2；只认「非」前缀否定形——"没有/未"等语义否定无法机械枚举，如实不覆盖。
    """
    payloads = [s] + re.findall(r"\b(?:bash|sh)\s+-c\s+'([^']*)'", s)
    for p in payloads:
        seg = re.split(r"\|\||&&|;|\||\n", p.strip())[-1].strip()
        seg = re.sub(r"^(?:!\s*)+", "", seg)
        m = re.match(
            r"^grep\s+(?:-{1,2}[\w-]+\s+)*(['\"])(.+?)\1\s+(['\"])(.+?)\3\s*$", seg)
        if not m:
            continue
        pat = m.group(2)
        path = m.group(4)
        if len(pat) < 2:
            continue
        path = path.replace("$HOME", os.path.expanduser("~"))
        if path.startswith("~/"):
            path = os.path.expanduser(path)
        try:
            if not os.path.isfile(path):
                continue
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except Exception:
            continue
        total = nonneg = 0
        idx = 0
        while True:
            i = text.find(pat, idx)
            if i < 0:
                break
            total += 1
            if i == 0 or text[i - 1] != "非":
                nonneg += 1
            idx = i + len(pat)
        if total > 0 and nonneg == 0:
            return ("模式 %r 在目标文件中只以否定式（前缀\"非\"）出现＝词面假红风险"
                    "（S1061 同案：否定式提及被当正犯）。修法：detect 加 "
                    "`| grep -v \"非%s\"` 排除否定式提及后再判，或改盯非否定证据形态"
                    % (pat[:24], pat[:24]))
    return ""


def _bare_script_noexec(s):
    """C8 判据：脚本文件被放在**命令位**直接调用，但盘上无执行位且前面没有解释器。

    为什么必须查（2026-09-18 实测）：抗体 `! "$HOME/.../antibody_gate.py" --selftest`
    裸执行时 shell 返回 **126（Permission denied）**，而 `!` 反断言把非 0 翻成 0
    ⇒ 巡检读作「坑在」= **结构性假红**；C4/C7 都看不见（既非恒真形态也非取数格式错）。
    为什么必须限「命令位」：正例里 .sh 常出现在**参数位**（grep 读文件），不是执行——
    不限位会集体误拦合规抗体（首版实测即误拦正例，被自家 --selftest 逮住）。
    """
    for m in re.finditer(TOK_RE, s):
        tok = m.group(1)
        path = os.path.expanduser(tok.replace("$HOME", os.path.expanduser("~")))
        if not os.path.isfile(path) or os.access(path, os.X_OK):
            continue
        i = m.start()
        j = i - 1
        while j >= 0 and s[j] in " \t":
            j -= 1
        prev = s[j] if j >= 0 else ""
        if prev and prev not in "!&|; $(": 
            continue  # 参数位：前面是普通 token，不判
        head = s[max(0, i - 24):i]
        if any(w in head for w in INTERPRETERS):
            continue
        return "命令位裸执行且无执行位：%s（shell rc=126 → ! 反断言翻成 0=假命中）" % tok
    return None


def _hex_format_mismatch(s, inside):
    """C7 判据：十六进制/对齐生产器 + 字面量模式 → 取数格式不同源（恒不命中）。

    解引号须**递归**：`sh -c '... grep -q "ef bb bf"'` 是嵌套引号——只解一层会把内层
    模式整段当作命令体，实测 3 条已证实的 BOM 假红抗体因此漏抓。
    """
    if not HEX_PROD_RX.search(s) or "|" not in s:
        return ""
    if NORM_RX.search(s):
        return ""  # 已做空白归一（tr -s ' '/tr -d ' \\n'）→ 格式同源
    lits = []
    queue = [lit or "" for _st, _en, lit in inside]
    while queue:                       # 递归解引号（不限层数）：xargs sh -c '... "..."' = 3 层
        val = queue.pop(0)
        lits.append(val)
        if len(lits) > 200:            # 防御：不因畸形输入爆栈
            break
        inner, _sk = _split_quoted(val)
        queue.extend(x[2] or "" for x in inner)
    for lit in lits:
        t = lit.strip()
        if not t:
            continue
        if HEX_SPACED_RX.match(t):
            return ("模式 `%s` 用单空格分隔字节，但 od/xxd 实际输出为**多空格对齐**"
                    "（如 `ef  bb  bf`）→ 恒不命中；改 `| od -An -tx1 | tr -s ' '` 归一后再匹配" % t)
        if HEX_CONTIG_RX.match(t) and len(t) >= 4:
            return ("模式 `%s` 为连续十六进制（无分隔），但 od/xxd 按字节/字分隔输出"
                    "→ 恒不命中；改 `od -An -v -tx1 | tr -d ' \\n'` 紧凑模式后再匹配" % t)
    return ""


def _relpath_hits(cmd):
    """扫描相对路径。豁免 find/grep 的『模式参数』位（-name/-path 后的 token 是文件名模式，非路径）。"""
    inside, skeleton = _split_quoted(cmd)
    skeleton = re.sub(r"-(?:i?name|path|i?regex|i?wholename)\s+\S+", " ", skeleton)
    hits = []
    for st, _en, s in inside:
        s = s.strip()
        if not s:
            continue
        if PATTERN_ARG_RX.search(cmd[:st].rstrip()):
            continue
        if s.startswith("./") or s.startswith("../"):
            hits.append(s)
        elif FILEEXT_RX.match(s):
            hits.append(s)
    for tok in skeleton.split():
        tok = tok.strip()
        if not tok or tok.startswith("-"):
            continue
        if tok.startswith("./") or tok.startswith("../"):
            hits.append(tok)
        elif FILEEXT_RX.match(tok):
            hits.append(tok)
        elif tok.startswith("$"):
            continue
        elif RELSEG_RX.match(tok):
            hits.append(tok)
    return hits


# ── 六项校验 ─────────────────────────────────────────────────

def polarity_check(cmd, expect, label="", timeout=30.0):
    """C12（v1.8.0）：登记态自证——实跑抗体，把 实测态(hit/clean) 与 声明期望态 对撞。
    不判"命令里 grep 的是正词还是坑词"（语义不可机械判），只判"你以为的现态对不对"。
    rc==0=hit（坑在）／rc!=0=clean（干净）。仅静态判据全过后才被调用（坏命令不跑）。"""
    try:
        r = subprocess.run(["bash", "-c", cmd], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        return [Violation("C12", "抗体实跑超时（>%ss），无法验证现态" % int(timeout),
                          "抗体应为轻量只读命令；先手动跑通再来登记", label=label, cmd=cmd)]
    actual = "hit" if r.returncode == 0 else "clean"
    if actual != expect:
        return [Violation("C12", "抗体实测态=%s，与登记声明 --expect %s 不符" % (actual, expect),
                          "二选一核：①方向写反了——检测『在场=安全』的正词用反断言 `! grep`，检测『在场=坑』的坑词用正断言 `grep`（本条现态若=hit 而你声明 clean，多半是①）；②坑其实还没修好——去目标文件确认后再定期望态",
                          label=label, cmd=cmd)]
    return []


def validate_cmd(cmd, label=""):
    """静态校验单条抗体命令，返回 Violation 列表（空=通过）。"""
    v = []
    raw = cmd if cmd is not None else ""
    s = raw.strip()

    if not s:
        v.append(Violation("C1", "抗体为空", "🔍可机械检测=是 时 🛡 必填（空=阻断 E4 写入）", label=label, cmd=raw))
        return v
    if PLACEHOLDER_RX.match(s):
        v.append(Violation("C1", "抗体是占位符而非命令", "实测值：%s" % s, label=label, cmd=raw))
        return v

    if "\n" in raw or "\r" in raw:
        v.append(Violation("C2", "抗体跨多行", "Schema 要求单行单命令；复杂检测须先写成脚本再引用", label=label, cmd=raw))

    inside, skeleton = _split_quoted(s)
    if re.search(r";\s*(?:true|:)\s*$", skeleton):
        pass
    elif ";" in skeleton and not re.search(r"\b(?:do|done|then|fi|esac)\b", skeleton):
        v.append(Violation("C2", "疑似多条命令并列", "引号外出现 ';' 分隔；单条命令单抗体", label=label, cmd=raw))

    try:
        p = subprocess.run(["bash", "-n", "-c", s], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            err = p.stderr.decode("utf-8", "replace").strip().split("\n")[-1] if p.stderr else ""
            v.append(Violation("C3", "bash -n 语法校验不通过", err[:160], label=label, cmd=raw))
    except FileNotFoundError:
        pass

    # v1.2.0：恒真判定须先在"退出码会传播的范围"内做——命令替换/反引号/分支体外的
    # `|| echo` 不决定整条命令退出码。原实现直接扫原始串，把 `X=$(cmd || echo 1)` 和
    # `if ...; then ...; else ...; fi` 里的合法写法全误报为恒真（实测误报率 3/5）。
    top = _mask_substitutions(s)
    if TRUTHY_RX.match(s):
        v.append(Violation("C4", "恒真形态：命令恒返回 0", "整条命令是 %s（无论检测对象状态如何都命中=假阳性）" % s, label=label, cmd=raw))
    else:
        m = re.search(r"(?:\|\||;|&&)\s*(true|:|exit\s+0)\s*$", top)
        if m:
            op = m.group(0)[:2].strip()
            v.append(Violation(
                "C4", "恒真形态：尾部 %s %s" % (op, m.group(1)),
                "右/末支恒 exit0 → bash -c 恒命中（假阳性源）；正确写法用反断言，如 `! grep -q '坑' <绝对路径>`",
                label=label, cmd=raw))
        # v1.1 扩展：|| echo 兜底（echo 恒 exit 0）；v1.2.0 收紧为**仅末位**才恒真
        # 实证：W6 抗体 `A && B && echo "verified" || echo "missing"` 恒 exit 0
        m2 = re.search(r"\|\|\s*echo\b[^;]*;?\s*$", top)
        if m2:
            v.append(Violation(
                "C4", "恒真形态：末位 || echo 兜底（echo 恒 exit 0）",
                "A && B || echo \"xxx\" 作为**命令末段**时 echo 恒成功 → 整条 exit code 恒 0；"
                "正确写法：去掉 || echo 兜底，改用 ! 反断言"
                "（注：命令替换 $() 内、if 分支内的 || echo 不传播退出码，不判恒真）",
                label=label, cmd=raw))

    # ── C7（v1.2.0·恒假形态）：取数格式与被检输出不同源 ────────────────────
    # 对称补齐：C4 防"恒命中"（不可证伪的假红源），C7 防"恒不命中"（探针语法/取数
    # 格式错→坑永远报不出来）。可机械判定的子类：十六进制/对齐生产器的输出含**可变
    # 空白**，而模式写成单空格或连续十六进制 → 永不匹配。实证：setup.ps1 BOM 抗体
    # `od -An -tx1 | grep -q "ef bb bf"` 实际输出为 `ef  bb  bf`（双空格）→ 53 次假红。
    c7 = _hex_format_mismatch(s, inside)
    if c7:
        v.append(Violation("C7", "恒假形态：取数格式与被检输出不同源", c7, label=label, cmd=raw))

    c8 = _bare_script_noexec(s)
    if c8:
        v.append(Violation("C8", "仪器起不来（反断言会把 126 翻成 0=假红）", c8, label=label, cmd=raw))

    c10 = _list_flag_platform_flip(s)
    if c10:
        v.append(Violation("C10", "平台反转形态：grep -L 作退出码来源", c10, label=label, cmd=raw))

    c9 = _ledger_status_probe(s)
    if c9:
        v.append(Violation("C9", "检测对象错位（账本状态字段≠行为复发）", c9, label=label, cmd=raw))

    c11 = _negation_only_hit(s)
    if c11:
        v.append(Violation("C11", "否定式提及独占命中（词面假红·S1061 同案）", c11, label=label, cmd=raw))

    hits = _relpath_hits(s)
    if hits:
        v.append(Violation(
            "C5", "相对路径 %d 处" % len(hits),
            "须自包含（绝对路径或 $HOME 派生）；实测：%s" % ", ".join(hits[:3]),
            label=label, cmd=raw))

    return v


# ── 抗体提取 ─────────────────────────────────────────────────

FIELD_RX = re.compile(r"复发检测条件\*{0,2}\s*[:：]\s*`([^`]*)`")
TITLE_RX = re.compile(r"`[^`]*`\s*—\s*(.*)$")
# 抗体行自带标题缺失时的取数降级链（2026-09-18·CAND-20260918-001「未命名抗体 重复9次」根因）：
#   E9.2 写入的 🛡 行常不带 ` — 标题` 尾缀 → 复发记录/退役台账/候选全部署「未命名抗体」
#   = 报警不可点名（无人消费的记录是死数据第 N 例）。故：①同行破折号标题 ②同条目 🔖 反哺标题 ③可定位回退。
TITLE_FALLBACK_RX = re.compile(r"🔖\s*\**反哺标题\**[：:]\s*(.+)$")


def extract_antibodies(path):
    """从文件中提取 (行号, cmd, label)。

    解析口径与 growth_box_check.sh 一致：取字段后第一对反引号（⛔非贪婪全行匹配，避免标题内反引号抢位）。
    行号口径显式对齐 grep：按 '\\n' 计数（newline='' 关闭 universal newlines）——否则含 \\r 的文件里
    门禁行号与 grep -n 行号错位，报告定位到别的行（2026-09-15 实测踩中，已根治）。
    """
    out = []
    entry_title = ""   # 每条 🔖 反哺标题 更新；🛡 行自带标题缺失时用它兜名（⛔不得 NameError）
    try:
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
            data = fh.read()
    except (IOError, OSError):
        return out
    for i, line in enumerate(data.split("\n"), 1):
        ft = TITLE_FALLBACK_RX.search(line)
        if ft:
            entry_title = ft.group(1).strip()   # 记住本条目块的标题，供后续 🛡 行降级取名
        if "复发检测条件" not in line:
            continue
        m = FIELD_RX.search(line)
        if not m:
            continue
        cmd = m.group(1)
        tm = TITLE_RX.search(line)
        label = (tm.group(1).strip().rstrip("|").strip() if tm
                 else entry_title or "未命名抗体@%s:L%d" % (os.path.basename(path), i))
        out.append((i, cmd, label))
    return out


def scan_files(paths):
    violations = []
    seen = {}
    scanned = 0
    for p in paths:
        if not os.path.isfile(p):
            continue
        for lineno, cmd, label in extract_antibodies(p):
            scanned += 1
            base = os.path.basename(p)
            for x in validate_cmd(cmd, label):
                x.line = lineno
                x.detail = ("%s · %s" % (base, x.detail)).strip(" ·")
                violations.append(x)
            # C6 去重限定**同文件内**：跨文件重复是设计要求——晋升条目按 SKILL.md E 流程
            # 「配 🛡 抗体」会复制源条目同一条检测条件（v1.5 双源扫描的 learnings 侧数据源），
            # 跨源报违规=假阳性（2026-09-15 实测踩中，已收窄口径）。
            key = (os.path.abspath(p), cmd.strip())
            if key in seen:
                violations.append(Violation(
                    "C6", "同文件内重复抗体",
                    "同一命令已在本文件第 %d 行存在" % seen[key],
                    line=lineno, label=label, cmd=cmd))
            else:
                seen[key] = lineno
    return scanned, violations


def emit_list(paths, stream=None):
    """TSV 导出（\\x1f 分隔）——供 shell 消费者（growth_box_check.sh）读取。

    契约：src_name <US> lineno <US> cmd <US> label <US> codes <US> dup_line
    codes 为空=通过，否则为逗号分隔的违规码（含 C6 同文件重复）。shell 侧一次调用即拿到
    全部抗体 + 门禁判定，⛔消费者不得自行重写校验规则（单一真相源）。
    """
    out = stream or sys.stdout
    for p in paths:
        if not os.path.isfile(p):
            continue
        base = os.path.basename(p)
        seen = {}
        for lineno, cmd, label in extract_antibodies(p):
            codes = [x.code for x in validate_cmd(cmd, label)]
            key = cmd.strip()
            dup = ""
            infos = ""
            if key in seen:
                infos = "C6"
                dup = str(seen[key])
            else:
                seen[key] = lineno
            out.write("\x1f".join([base, str(lineno), cmd, label, ",".join(codes), dup, infos]) + "\n")


def run_antibodies(paths, timeout=30.0, stream=None):
    """逐条实跑抗体，输出 `idx\x1f结果\x1f备注` 行（idx=0 起，与 --list 同序）。

    v1.2.0：**执行**也收进单一真相源。v1.8 只把"提取+判定"委托 gate，而**执行**仍散在
    shell（半单源）——真凶就在此。两个必须：
      ① **stdin 重定向为 DEVNULL**：`grep -rl PATTERN <路径>` 在路径被 glob 掉/无文件参数时
         会**落回读 stdin**，在管道/交互场景下永久等待（实测 2 条抗体挂死，整段巡检不返回）。
      ② **单条超时**：抗体是可证伪性未知的黑盒命令，一条挂死不能拖垮全量巡检
         （原批量 bash 无超时兜底：任何一条挂 = 整段永久挂）。
    超时/异常一律判 M（免疫）而非 H：⛔不把"测不出来"当"命中"（避免制造假红；
    超时条目由健康度分层另标"未复验"）。
    """
    out = stream or sys.stdout
    idx = 0
    for p in paths:
        if not os.path.isfile(p):
            continue
        for _lineno, cmd, _label in extract_antibodies(p):
            res = "M"
            note = ""
            try:
                r = subprocess.run(["bash", "-c", cmd], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=timeout)
                res = "H" if r.returncode == 0 else "M"
            except subprocess.TimeoutExpired:
                res, note = "M", "timeout"
            except (OSError, ValueError) as e:
                res, note = "M", "error:%s" % type(e).__name__
            out.write("\x1f".join([str(idx), res, note]) + "\n")
            idx += 1
    try:
        out.flush()
    except (AttributeError, ValueError):
        pass


def default_sources():
    src = [p for p in DEFAULT_SOURCES if os.path.isfile(p)]
    if os.path.isdir(LEARNINGS_DIR):
        for name in sorted(os.listdir(LEARNINGS_DIR)):
            if not name.endswith(".md"):
                continue
            if re.match(r"^(?:INDEX|FEATURE_REQUESTS|book)_?\.md$", name) or ".bak" in name:
                continue
            src.append(os.path.join(LEARNINGS_DIR, name))
    return src


# ── 生成器（设计端消除常用错误） ──────────────────────────────

GEN_KINDS = {
    "file-missing": "坑=文件丢失（缺→命中0，在→免疫1）",
    "file-exists": "坑=文件存在（在→命中0，缺→免疫1）",
    "text-absent": "坑=文本缺失（缺→命中0，在→免疫1）",
    "text-present": "坑=文本存在（在→命中0，缺→免疫1）",
}


def _need_abs(path):
    if not (path.startswith("/") or path.startswith("$HOME") or path.startswith("~")):
        sys.stderr.write("❌ 生成拒绝：路径须绝对或 $HOME 派生，收到相对路径：%s\n" % path)
        sys.exit(2)
    return path


def generate(kind, args):
    if kind not in GEN_KINDS:
        sys.stderr.write("❌ 未知生成类型：%s（可选：%s）\n" % (kind, ", ".join(sorted(GEN_KINDS))))
        sys.exit(2)
    if kind.startswith("file-"):
        if len(args) != 1:
            sys.stderr.write("❌ %s 需要一个路径参数\n" % kind)
            sys.exit(2)
        path = _need_abs(args[0])
        return 'test ! -f "%s"' % path if kind == "file-missing" else 'test -f "%s"' % path
    if len(args) != 2:
        sys.stderr.write("❌ %s 需要两个参数：<路径> <模式>\n" % kind)
        sys.exit(2)
    path = _need_abs(args[0])
    pattern = args[1]
    if kind == "text-absent":
        return "! grep -q %s \"%s\"" % (_q(pattern), path)
    return "grep -q %s \"%s\"" % (_q(pattern), path)


def _q(pat):
    if "'" in pat and '"' not in pat:
        return '"%s"' % pat
    return "'%s'" % pat.replace("'", "'\\''")


# ── 自检夹具（负例驱动·防"门禁自身退化"） ────────────────────

def selftest():
    # ── v1.8.1 自测去生产依赖（B-2 承接·换根探针实证）───────────────────────────
    #   C8/C11 两条判据会读文件（C8 看存在与执行位、C11 看模式是否只以否定式出现），原用例把目标路径
    #   写死成生产绝对路径 → 换机/换根/卡片改名即假红。实证：把 $HOME/个人AI档案 整体替换为不存在目录
    #   后 selftest 由 rc=0 变 rc=1（2/42 不通过·恰为 C8+C11 两条）。现自建临时夹具，判据本体零改动。
    import tempfile as _tf3
    _box = _tf3.mkdtemp(prefix='antibody_selftest_')
    _bare = os.path.join(_box, "bare_script.py")        # 存在·644 无执行位 → C8 应拦
    with open(_bare, "w", encoding="utf-8") as _bh:
        _bh.write("#!/bin/sh" + chr(10) + "exit 0" + chr(10))
    os.chmod(_bare, 0o644)
    _card_neg = os.path.join(_box, "card_neg_only.md")  # 模式只以「非…」出现 → C11 应拦
    with open(_card_neg, "w", encoding="utf-8") as _ch:
        _ch.write("# 卡" + chr(10) * 2 + "本卡结论非你已质证，系 AI 初判待审。" + chr(10))
    _card_pos = os.path.join(_box, "card_plain.md")     # 肯定式出现 → C11 不拦
    with open(_card_pos, "w", encoding="utf-8") as _ph:
        _ph.write("# 卡" + chr(10) * 2 + "你已质证：结论成立。" + chr(10))
    bad = [
        ("C1", ""),
        ("C1", "..."),
        ("C1", "<待填>"),
        ("C2", "grep -q a \"$HOME/x.md\"\ntest -f \"$HOME/y.md\""),
        ("C2", "test -f \"$HOME/x.md\"; grep -q a \"$HOME/y.md\""),
        ("C3", 'grep -q "unterminated "$HOME/x.md"'),
        ("C4", "&& exit 0 || exit 0"),
        ("C4", "grep -q '坑' \"$HOME/x.md\" || true"),
        ("C4", "grep -q '坑' \"$HOME/x.md\" || exit 0"),
        ("C4", "test -f \"$HOME/x.md\"; true"),
        ("C4", "exit 0"),
        ("C5", "test -f config.json"),
        ("C5", "! grep -q '待拍板' 记忆蓝图/03-进度看板.md"),
        ("C5", "test -f ./scripts/x.sh"),
        ("C4", 'bash -c \'test -f "$HOME/x.md" && grep -q "y" "$HOME/x.md" && echo "verified" || echo "missing"\''),
        ("C4", 'grep -q "a" "$HOME/x.md" || echo "not found"'),
        # C7（v1.2.0·恒假形态）：取数格式不同源——实测 53 次假红的 setup.ps1 BOM 抗体
        ("C7", 'head -c3 "$HOME/x/setup.ps1" | od -An -tx1 | grep -q "ef bb bf"'),
        ("C7", 'xxd -p "$HOME/x/a.ps1" | grep -q "efbbbf"'),
        ("C8", '! "%s" --selftest >/dev/null 2>&1' % _bare),
        ("C7", 'hexdump -C "$HOME/x/a.ps1" | grep -q "ef bb bf"'),
        # C7 嵌套引号（v1.2.0）：`sh -c '... grep -q "ef bb bf"'`——只解一层会漏抓，
        # 实测 3 条已证实的 BOM 假红抗体就是此形。
        ("C7", '! find "$HOME/x" -maxdepth 2 -name setup.ps1 -print0 | xargs -0 -n1 sh -c \'head -c3 "$0" | od -An -tx1 | grep -q "ef bb bf"\''),
        # C9（v1.5.0·检测对象错位）：2026-09-19 免疫终审一次退役的 7 条真形——问账本 Status 不问行为复发
        ("C9", 'bash -c \'grep -rl "删除\\|rm -rf\\|trash" "[记忆共享中心]/成长箱/learnings/*.md" 2>/dev/null '
               '| xargs grep -lE "Status.*(pending|active)" 2>/dev/null | head -1 | grep -q .\''),
        ("C9", 'bash -c \'grep -rl "软链接\\|symlink" "[记忆共享中心]/成长箱/learnings/*.md" | xargs grep -lE "Status.*(pending|active)" | grep -q .\''),
        # C10（v1.6.0·2026-09-23 免疫验真）：grep -L 作退出码 = GNU/BSD 反转
        # 实证：8 条「框架缺该段=坑在」抗体在 macOS 上产 177 条假命中（锚在 rc0／锚缺 rc1）
        ("C10", 'bash -c \'grep -L "写读对同源" "[记忆共享中心]/技能配置/clock-loop/references/evaluation-framework.md"\''),
        ("C10", 'grep -L "a" "$HOME/个人AI档案/x.md"'),
        ("C10", '! grep -L "a" "$HOME/个人AI档案/x.md"'),
        # C11（v1.7.0·否定假红）：S1061 真实文件——"你已质证"只以"非你已质证"出现
        ("C11", '! grep -q "你已质证" "%s"' % _card_neg),

    ]
    good = [
        # 【v1.2.0 移除】原此处含 setup.ps1 BOM 抗体 `od -An -tx1 | grep -q "ef bb bf"`——
        # 它本身即 53 次假红的源头，旧版把假红抗体当"正例"=**测试固化了错误行为**；
        # 现已在 bad 列表以 C7 嵌套引号用例覆盖。
        'test ! -f "[记忆共享中心]/脚本中心/content-gate.py"',
        '! grep -q -- \'/-卡片\\[\' "[记忆共享中心]/脚本中心/changelog-guard/kb_index_guard.sh"',
        "grep -q 'len(int' \"[记忆共享中心]/脚本中心/changelog-guard/kb_index_sync.py\"",
        'bash -c \'for f in $(find "[记忆共享中心]/脚本中心" -maxdepth 1 -name "*.sh"); do bash -n "$f" || exit 0; done; exit 1\'',
        '! diff <(ls "[记忆共享中心]/发布库/A") <(ls "[记忆共享中心]/发布库/B") >/dev/null',
        # C9 的两侧正例（防"见 learnings 就拦"的过宽实现）：
        # ①在 learnings 里查某个具体编号是否落地——合法（不碰 Status 取值）
        'grep -q "QCN-20260918-001" "[记忆共享中心]/成长箱/learnings/LEARNINGS.md"',
        # ②在账本里查 Status 字段本身但不比对 pending/active——合法
        'grep -q "Status" "[记忆共享中心]/成长箱/learnings/INDEX.md"',
        # C10 正例①：修法本体（! grep -q 反断言·两端语义一致）
        'bash -c \'! grep -q "写读对同源" "[记忆共享中心]/技能配置/clock-loop/references/evaluation-framework.md"\'',
        # C10 正例②：-L 落在管道中段、退出码来自末段 grep -q → 不违规（3074 真实形态·防过宽）
        'bash -c \'grep -l "终检清单" ~/x/*.md 2>/dev/null | xargs grep -L "finalize" 2>/dev/null | head -1 | grep -q .\'',
        # C11 正例①（v1.8.1 夹具化）：模式以肯定式出现在自建夹具文件中 → C11 不拦
        '! grep -q "你已质证" "%s"' % _card_pos,
        # C11 正例②：否定式提及已被管道下游排除（决定段=grep -q .，C11 不查中段·同 C10 掩蔽）
        'bash -c \'grep "你已质证" "%s" | grep -v "非你已质证" | grep -q .\'' % _card_neg,

    ]
    fails = 0
    # ── C12 双向夹具（v1.8.0·防 S323 自设自验：正反例互锁，短路判据必红其中一侧）──
    # `false`→rc1=clean；`true`→rc0=hit。声明与实跑相符放、不符拦。
    pol = [("clean", "false", 0), ("hit", "true", 0), ("hit", "false", 1), ("clean", "true", 1)]
    for exp, cmd, want_n in pol:
        got = len(polarity_check(cmd, exp, "selftest-C12"))
        if got != want_n:
            fails += 1
            print("❌ C12 夹具 %s exp=%s 期望violation=%d 实得=%d" % (cmd, exp, want_n, got))
    for want, cmd in bad:
        got = validate_cmd(cmd)
        codes = [x.code for x in got]
        ok = want in codes
        if not ok:
            fails += 1
            print("❌ 负例未拦 %-3s 期望=%s 实得=%s :: %r" % ("", want, codes or "无", cmd[:60]))
    for cmd in good:
        got = validate_cmd(cmd)
        if got:
            fails += 1
            print("❌ 正例误拦 %s :: %r" % ([x.code for x in got], cmd[:60]))
    total = len(bad) + len(good)

    # ── C8 运行时自检（v1.2.0）：执行器必须 stdin=DEVNULL + 单条超时 ──────────
    # 两个互补夹具：
    #   夹具A `cat`：读 stdin 的命令。✅DEVNULL 生效→立即 EOF 返回 H；⛔DEVNULL 缺失→**本自检自己会永久挂死**。
    #   夹具B `sleep 5` + timeout=1：验证单条超时兜底（期望 M/timeout——测不出来不得当命中）。
    import io
    import tempfile
    f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    f.write('- \U0001F6E1 **复发检测条件**：`cat` — 读 stdin 的抗体（验 DEVNULL 生效）\n')
    f.write('- \U0001F6E1 **复发检测条件**：`sleep 5` — 挂死抗体（验单条超时兜底）\n')
    f.close()
    buf = io.StringIO()
    try:
        run_antibodies([f.name], timeout=1.0, stream=buf)
        lines = [x.split("\x1f") for x in buf.getvalue().strip().splitlines()]
        ok_a = len(lines) >= 1 and lines[0][1] == "H" and not lines[0][2]
        ok_b = len(lines) >= 2 and lines[1][1] == "M" and "timeout" in lines[1][2]
        if not ok_a:
            fails += 1
            print("\u274c 执行器自检未过A（DEVNULL 未生效→cat 未立即 EOF）: %r" % (buf.getvalue(),))
        if not ok_b:
            fails += 1
            print("\u274c 执行器自检未过B（单条超时未兜底）: %r" % (buf.getvalue(),))
    except Exception as e:  # noqa: BLE001
        fails += 1
        print("\u274c 执行器自检异常（极可能挂死或缺 DEVNULL）: %s" % type(e).__name__)
    finally:
        os.unlink(f.name)
    total += 2

    # 提取器防误（2026-09-15 实测踩中）：提及字段名的规则叙述⛔不得被当成抗体；
    # 真抗体行必须取到字段后第一对反引号，且行号口径与 grep 一致。
    import tempfile
    sample = (
        "**抗体命令必须可证伪（禁恒真形态）铁律**：任何 `\U0001F6E1 复发检测条件` 命令，"
        "禁止 `&& exit 0 || exit 0` 这类写法。\n"
        "- \U0001F6E1 **复发检测条件**：`test ! -f \"/abs/x.md\"` — 真抗体标题\n"
    )
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    tmp.write(sample)
    tmp.close()
    got = extract_antibodies(tmp.name)
    os.unlink(tmp.name)
    if len(got) != 1 or got[0][0] != 2 or got[0][1] != 'test ! -f "/abs/x.md"' or got[0][2] != "真抗体标题":
        fails += 1
        print("\u274c 提取器防误未过：期望 1 条(L2) 实得 %r" % (got,))
    total += 1

    # 取名降级链防「匿名报警」（2026-09-18·CAND-20260918-001：E9.2 写的 🛡 行不带 ` — 标题` 尾缀
    # → 复发记录/候选全署「未命名抗体」= 不可点名 = 死数据）。三态：自带标题 / 缺标题有条目标题 / 两者皆无。
    sample2 = (
        "- \U0001F6E1 **复发检测条件**：`grep -q \"abc\" \"/abs/x.md\"`\n"          # L1 条目前无标题
        "- \U0001F516 **反哺标题**：条目自带的标题应当被继承\n"                      # L2
        "- \U0001F6E1 **复发检测条件**：`grep -q \"def\" \"/abs/y.md\"`\n"          # L3 继承 L2
        "- \U0001F6E1 **复发检测条件**：`grep -q \"ghi\" \"/abs/z.md\"` — 行内自带标题\n"  # L4
    )
    tmp2 = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    tmp2.write(sample2)
    tmp2.close()
    got2 = extract_antibodies(tmp2.name)
    os.unlink(tmp2.name)
    lab2 = [g[2] for g in got2]
    if (len(got2) != 3 or not lab2[0].startswith("未命名抗体@") or ":L1" not in lab2[0]
            or lab2[1] != "条目自带的标题应当被继承" or lab2[2] != "行内自带标题"):
        fails += 1
        print("\u274c 取名降级链未过（⛔不得再产出不可点名的\"未命名抗体\"）：%r" % (lab2,))
    total += 1

    if fails == 0:
        # §3.9 承接：负例全拦=判据不恒假，正例全过=判据不恒真——两向同时成立才算变异过。
        print("MUT:OK 负例全拦(不恒假)+正例全过(不恒真)·任一失效即 fails>0")
        print("✅ antibody_gate 自检通过：负例 %d/%d 全拦 · 正例 %d/%d 全过（共 %d）"
              % (len(bad), len(bad), len(good), len(good), total))
    else:
        print("🔴 antibody_gate 自检失败：%d/%d 不通过" % (fails, total))
    return 0 if fails == 0 else 1


# ── CLI ──────────────────────────────────────────────────────

def _emit(violations, scanned, as_json, quiet):
    # C6（同文件内同抗体）判定为**提示级**而非违规级：抗体与教训同生共死（守卫编写规范 §3.3），
    # 一条检测条件服务多条教训是**设计使然**（2026-09-15 实锤：LEARNINGS L2684/L2718 分属 QCN-002/003
    # 两条不同教训、共用同一条"改脚本必查语法"抗体）——把它当违规=假阳性=报警疲劳。
    hard = [x for x in violations if x.code != "C6"]
    info = [x for x in violations if x.code == "C6"]
    if as_json:
        print(json.dumps({
            "alarm": bool(hard),
            "version": VERSION,
            "scanned": scanned,
            "total": len(hard),
            "violations": [x.to_dict() for x in hard],
            "info": [x.to_dict() for x in info],
        }, ensure_ascii=False))
        return
    if not hard:
        if not quiet:
            msg = "✅ 抗体门禁全通过 · 已检 %d 条" % scanned
            if info:
                msg += "（提示 %d 条：同抗体多条目复用·命中将多处留痕）" % len(info)
            print(msg)
        return
    print("🔴 抗体门禁拦截 %d 条违规（共检 %d 条）" % (len(hard), scanned))
    for x in hard:
        loc = " L%d" % x.line if x.line else ""
        print("   [%s]%s %s" % (x.code, loc, x.msg))
        print("         Antibody: %s" % (x.label or "未命名抗体"))
        if x.detail:
            print("         Detail: %s" % x.detail)
        print("         Fix: %s" % _FIX.get(x.code, "按 Schema 修正后重跑"))
    print("   ── 门禁 Fail-Closed：违规未清零则禁止写入（E4 阻断）")
    for x in info:
        print("   [C6] L%d 提示：同文件内同抗体多条目复用（命中将多处留痕，非违规）" % x.line)


_FIX = {
    # C7/C9 于 v1.19.0/v1.21.0 落判据时只写了 msg，未进本表 → 消费端看到通用兜底=不可执行改法（2026-09-19 补）
    "C10": "退出码改由 `grep -q` 提供并配 `!` 反断言：`! grep -q \"锚\" \"绝对路径\"`（锚缺=exit0=命中，锚在=exit1=免疫，GNU/BSD 一致）",
    "C7": "取数与匹配同格式：多空白输出（od/ps/diff/stat）先 `| tr -s ' '` 归一再匹配，或改 `tr -d ' \\n'` 后匹配连续串；C7 以**修**为主（判据可改对，不同于 C4 须退役）",
    "C9": "改盯真实复发信号（某产物/某指纹是否再次出现），⛔盯成长箱账本的 Status 取值——待处理态是常态，永不免疫",
    "C8": "命令前加解释器（python3 / bash），或给脚本补执行位——两者择一，⛔不得只删 ! 反断言（那会把判据方向搞反）",
    "C11": "detect 加 `| grep -v \"非<模式>\"` 排除否定式提及后再判（参照 LEARNINGS「你已质证」抗体 v1.2 修法），或改盯非否定证据形态",
    "C1": "填单行 shell 命令；不填=默认不设防，须改为 🔍可机械检测=否 并在📝说明理由",
    "C2": "压成单行；复杂检测先写成检测脚本，抗体里只引用脚本路径",
    "C3": "修语法；本地先跑 `bash -n -c '<cmd>'` 直到通过",
    "C4": "改用反断言或正断言，保证能区分『命中(0)=坑在』与『免疫(非0)=坑补』",
    "C5": "路径改为绝对路径或 $HOME 派生（cwd 不固定，相对路径=假命中/假免疫）",
    "C6": "同一检测条件只留一条；先查 §四 守卫注册表与既有抗体去重",
}


def main(argv=None):
    ap = argparse.ArgumentParser(description="抗体写入端机械门禁 v%s" % VERSION)
    ap.add_argument("--check-cmd", metavar="CMD")
    ap.add_argument("--label", default="")
    ap.add_argument("--scan", nargs="*", metavar="FILE")
    ap.add_argument("--gen", nargs="+", metavar="KIND [ARGS...]")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--expect", choices=["clean", "hit"], default=None,
                    help="C12 登记态自证：与 --check-cmd 连用，声明本抗体在登记时点应有的现态")
    ap.add_argument("--list", nargs="*", metavar="FILE", dest="list_mode",
                    help="TSV 导出（\\x1f 分隔）供 shell 消费者读取·缺省扫双源")
    ap.add_argument("--run", action="store_true",
                    help="实跑全部抗体（stdin=DEVNULL + 单条超时）·输出 idx<US>H/M<US>备注")
    ap.add_argument("--timeout", type=float, default=30.0, metavar="SEC",
                    help="--run 的单条抗体超时秒数（默认 30）")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    if a.list_mode is not None:
        emit_list(a.list_mode or default_sources())
        return 0

    if a.run:
        # -u 等价：shell 侧按行流式消费，不缓冲（否则 idx 与结果错位）
        run_antibodies(default_sources(), timeout=a.timeout)
        return 0

    if a.gen:
        print(generate(a.gen[0], a.gen[1:]))
        return 0

    if a.check_cmd is not None:
        vs = validate_cmd(a.check_cmd, a.label)
        if a.expect and not vs:  # 静态判据全过才实跑（坏命令不执行·防副作用）
            vs = polarity_check(a.check_cmd, a.expect, a.label)
        _emit(vs, 1, a.as_json, a.quiet)
        return 1 if vs else 0

    if a.scan is not None:
        paths = a.scan or default_sources()
        scanned, vs = scan_files(paths)
        _emit(vs, scanned, a.as_json, a.quiet)
        # C6 是提示级（_emit 内已按 hard/info 分流）：退出码必须与**输出结论**同口径。
        # 原 `return 1 if vs` 把 C6 算进红 → 打印「✅ 全通过」却 rc=1，消费端（antibody_guard.sh / Stop）
        # 见 rc 即报＝假红，且与 SKILL.md「--scan 必须 exit 0 且仅允许 C6 存量项」自相矛盾（2026-09-19 实测）。
        return 1 if any(v.code != "C6" for v in vs) else 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
