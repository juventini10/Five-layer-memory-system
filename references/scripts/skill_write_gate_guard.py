#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
# skill_write_gate_guard.py — Skill管辖目录写入门卫（铁律-017物理拦截层）
# Disease: PAT-014家族新实例（2026-09-20实证）——AI知道要记成长箱，却直接Bash手写
#   成长箱/drafts/（绕过growth-box Skill）——"用绕过手段记录绕过错误"套娃。
# Verdict (mechanical): PreToolUse拦截——写Skill管辖目录时，检查启动标记文件
#   （~/.cache/skill_gate/{domain}.active·mtime<4h）。无标记→exit 2物理阻断+引导语；
#   有标记→exit 0放行。标记由Skill启动时touch（或AI按阻断引导显式touch=留痕动作）。
# Usage:
#   hook mode (stdin JSON, PreToolUse):
#     ZCode shape:  {"toolName":"Write","input":{"file_path":..}}
#     Bash shape:   {"toolName":"Bash","input":{"command":..}}  (命令串含管辖路径也拦)
#     WB shape:     {"tool_name":"Write","tool_input":{...}}   (extract归一兼容)
#     -> block exit 2 (physical), ok exit 0
# Scope: 成长箱/ 技能配置/ 数字分身/ 发布库/ ~/.workbuddy/ （个人AI档案下前四者）
# Exempt: guard自身 / append_log_entry.py / growth-box scripts/（Skill自有引擎）
# version: v0.10（2026-10-17 Qoder CN端·包面写门禁：写 布洛陀-全平台安装包/ 需锁周期认领·FREE硬拦引导acquire·release目睹清账·--claim-package-lock·负例夹具8/8·LRN-20261017-01机制化）
#   原 v0.9.1（2026-10-10 Qoder CN端·heredoc 假红根治：WRITE_FEATURES 剔 `<<`——
#   `<<` 喂 stdin 不落盘，误列硬拦形⇒只读分析被 exit2；间接写归 unknown 只提示（v0.4 分级同界·不扩大）。
#   原 v0.9（2026-10-05 Qoder CN端·软链根治+hint花括号修+v0.8回归合并收口；v0.2判据绝对前缀/v0.3畸形放行/v0.4动作分级/v0.4.1剔无害重定向/v0.5剥双引号/v0.6评估通道，沿革见下）：
#   v0.2 判据 子串→绝对路径前缀 ｜ v0.3 畸形输入失败放行
#   v0.4 Bash 动作分级：read→放行 ／ write(明确写)→硬拦exit2 ／ unknown→仅提示不打断
#   v0.4.1 剔无害重定向（2>/dev/null、2>&1）再判动作——防只读命令被 `>` 误判为写（WB端实测自锁）
#   v0.5 剥双引号字面量再判 WRITE_FEATURES（2026-09-23 童灵根治：python -c 内比较符/箭头文案误拦）
#   version行 v0.4→v0.5 补记 2026-10-03（E6声明滞后自纠）
#   v0.6 EVAL_CHANNELS 评估修复通道（skillforge←clockloop.active·2026-10-03 三链事故后续接线）
#   v0.7 软链绕过根治（2026-10-05 Qoder CN 实证：Write/cp 经 ~/.qoder-cn/skills 软链写技能配置 exit0 放行）：
#     ① _resolve 与 SCOPES 前缀 normpath→realpath；② hint 花括号 bug 修（引导留痕命令产出真文件名）。
#     与条文45同源病根的读取侧另一面；已知诚实边界不变：python -c 间接写仍 soft 提示（v0.4 力度分级设计）。
#   v0.8（2026-10-05 LobsterAI 端·同文件并发补丁·版本行未抬）：加引号内空格路径切分+相邻重组，修向成立。
#   v0.9（2026-10-05 Qoder CN 端·合并收口）：paths.extend(toks) 修 v0.8 丢裸 token 回归；
#     五组对照复验（真实路径拦/软链Write拦/软链cp拦/只读放行/非管辖放行）全绿为准出。
#   ⚠️ 2026-10-03 三链事故实录：本文件升 v0.4.1/v0.5 后，包内副本与 ~/.qoder-cn/hooks 部署件
#     长期未随源更新（部署件停 v0.4.0 缺两补丁）→ Qoder CN 会话纯读命令被硬拦 exit2。
#     根治=源→包(sync_script_center --only)→hooks(cp)三链重部署+运行态复验；
#     残余风险=已交付件内容哈希无常态对账器（登记待建·见本会话交付报告）
import sys, json, os, re, time

GUARD_NAME = "skill_write_gate_guard.py"
HOME = os.path.expanduser("~")
# 管辖目录判据 = 【绝对路径前缀】（2026-09-19 WB端修正·第一性原理）：
# 原用「子串包含」(`prefix in p`) → 任何含 `.workbuddy/` 的路径都命中，
# 把项目级 `WorkBuddy/开发/.workbuddy/` 误伤（WB 端实测：记忆写入被拦）。
# 判据目标 = 「路径**归属**」非「子串**出现**」→ 改绝对路径前缀匹配。
SCOPES = [
    (os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "成长箱"),  "growthbox"),
    (os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "技能配置"), "skillforge"),
    (os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "数字分身"), "digitaltwin"),
    (os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "发布库"),  "release"),
    (os.path.join(HOME, ".workbuddy"),          "workbuddy"),
]
MARKER_DIR = os.path.expanduser("~/.cache/skill_gate/")
MARKER_TTL = 4 * 3600  # 4h
EXEMPT = ("skill_write_gate_guard.py", "append_log_entry.py",
          "/growth-box/scripts/", "/数字分身/scripts/")

# ── v0.10 包面写门禁（2026-10-17·LRN-20261017-01 机制化·小卡=待完成工作/包面写门禁-session认领机制）──
# 病根：release marker 全局共享（touch 一次 4h 内任何同端窗可写包）——10:44 撞锁案的机制面缺口。
# 判据：写 布洛陀-全平台安装包/ 必须「锁周期认领」——当前 holder ts ∈ claimed 账本。
# 认领=python3 <本件> --claim-package-lock（FREE 拒绝并转述 acquire 引导；同端二次 acquire=REFUSED→闯入窗物理劝退·排队）。
# release 被目睹→清账（锁周期闭合下轮重认领）。acquire/release 命令本身恒放行（⛔不拦锁操作防自锁）。
PKG_ROOT = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "发布库", "五层记忆系统", "布洛陀-全平台安装包")
PKG_HOLDER = os.path.join(PKG_ROOT, ".package-lock", "holder")
PKG_CLAIMED = os.path.join(MARKER_DIR, "pkg_lock_claimed.json")

def _pkg_holder():
    try:
        parts = open(PKG_HOLDER, encoding="utf-8").read().strip().split("\t")
        if len(parts) >= 3 and parts[2].strip().isdigit():
            return parts[0], parts[2].strip()
    except OSError:
        pass
    return None

def _pkg_claimed():
    try:
        v = json.load(open(PKG_CLAIMED, encoding="utf-8"))
        return set(v) if isinstance(v, list) else set()
    except Exception:
        return set()

def _pkg_claim():
    h = _pkg_holder()
    if not h:
        print("FREE（当前无持锁）：先 `bash \"%s/package_lock.sh\" acquire <端名>` 获取锁再认领；"
              "若 REFUSED=他窗持锁（含同端另一窗）——写入需排队，⛔绕行硬写" % PKG_ROOT, file=sys.stderr)
        return 1
    who, ts = h
    try:
        os.makedirs(MARKER_DIR, exist_ok=True)
        cur = _pkg_claimed(); cur.add(ts)
        json.dump(sorted(cur)[-32:], open(PKG_CLAIMED, "w", encoding="utf-8"))
    except OSError as e:
        print("CLAIM FAILED: %r" % e, file=sys.stderr); return 1
    print("CLAIMED: 持锁者=%s ts=%s——本锁周期内包面写入放行（release 后自动失效）" % (who, ts))
    return 0

def extract_event(obj):
    tool = obj.get("toolName") or obj.get("tool_name") or ""
    inp = obj.get("input") or obj.get("tool_input") or {}
    return tool, inp

# ── Bash 动作闸（2026-09-19 WB端·根治"只读命令被误拦"）──
# 病根同"子串 vs 归属"：Bash 侧原只看"命令串里出现管辖路径"→ ls/find/grep 只读也拦。
# 正解=动作×路径：**纯读命令直接放行**（读无害·拦它=纯误伤+告警疲劳）。
# 诚实边界：`python -c "open(p,'w')"` 等间接写不在读白名单→判 unknown：ℹ️提示但不阻断（v0.4 力度分级·⛔不误伤）。"不放过"的兑现形态=提示留痕+人终判，非 exit2 阻断——阻断只留给确定写动作（双盲第11次C-07：原措辞与行为口径差·v0.6.1对齐）。
READ_CMDS = {"ls", "find", "grep", "rg", "cat", "head", "tail", "wc", "stat", "file",
             "du", "df", "diff", "which", "type", "tree", "realpath", "basename",
             "dirname", "echo", "printf", "env", "pwd", "sort", "uniq", "cut", "jq"}
# v0.9.1（2026-10-10）：剔除 `<<` ——heredoc 是喂 stdin 不落盘，原列"明确写"特征致
# 纯只读 `python3 - <<EOF` 分析被 exit2 硬拦（假红·当日实证2次）；间接写面归 unknown 只提示。
WRITE_FEATURES = re.compile(r">>?|-delete\b|-exec\b|\s-i\b|--in-place\b|\|\s*tee\b|truncate")


def _strip_double_quoted(cmd):
    """剥离**双引号内**的字面量（v0.5·2026-09-23 童灵根治假阳性）。

    病根：`WRITE_FEATURES` 的 `>>?` 会命中命令里**任何** `>` 字面——包括 `python3 -c "len(x)>1"`
    里的比较运算符、输出文案里的箭头（如 `<空>`）→ **只读命令被硬拦**（2026-09-23 本轮实测被拦 2 次，
    均为纯 python -c 只读探测）。同族病：判据只看形状不看语义（与当日"守卫格式比对失灵"同源）。

    ⚠️ 刻意的折中边界：**只剥双引号，保留单引号内内容**——`awk` 惯用单引号写重定向
    （`awk '{print > "f"}'`），一并剥离会漏判真写（假阴性比假阳性更伤·§3.4 实锤律）。
    双引号已覆盖 `python -c "..."` 这一主要踩坑面。
    """
    out, inq, prev = [], False, ""
    for ch in cmd:
        if ch == '"' and prev != "\\":
            inq = not inq
            out.append(" ")
            prev = ch
            continue
        out.append(" " if inq else ch)
        prev = ch
    return "".join(out)


WRITE_CMDS = {"cp", "mv", "rm", "rmdir", "touch", "mkdir", "tee", "dd", "truncate",
              "install", "rsync", "ln", "chmod", "chown", "patch", "mkfifo"}


def _bash_action(cmd):
    """判定 Bash 命令的动作语义：'read' | 'write' | 'unknown'（2026-09-19 v0.4·力度分级）。
    分级目的：明确写动作→硬拦；未知命令（判不出）→仅提示不打断（⛔不误伤）。
    v0.4.1 修：先剔无害重定向（`2>/dev/null`/`>/dev/null`/`2>&1`）再判——原版把 `>` 一网打尽，
    致 `ls ... 2>/dev/null` 这类只读命令被误判为"写"（WB 端实测被自锁）。"""
    cmd = re.sub(r"[0-9]?>&[0-9]|[0-9]?>\s*/dev/null", "", cmd)
    if WRITE_FEATURES.search(_strip_double_quoted(cmd)):
        return "write"
    segs = [s.strip() for s in re.split(r"[;&|]{1,2}", cmd) if s.strip()]
    if not segs:
        return "unknown"
    acts = []
    for seg in segs:
        tok = seg.split()[0]
        acts.append("write" if tok in WRITE_CMDS else ("read" if tok in READ_CMDS else "unknown"))
    if "write" in acts:
        return "write"
    if all(a == "read" for a in acts):
        return "read"
    return "unknown"


def extract_paths(tool, inp):
    """抽候选路径：file_path 直取；Bash 抽路径 token（~ 或 / 开头）。
    动作分级（read/write/unknown）由 main() 判定，本函数不再拦截。"""
    paths = []
    fp = inp.get("file_path") or inp.get("path") or ""
    if fp: paths.append(str(fp))
    if tool in ("Bash", "bash"):
        cmd = str(inp.get("command", ""))
        # v0.8·2026-10-05 LobsterAI 端实证·补丁：引号内完整路径优先
        # 病根：原正则 [^\s'\"|;>()]* 遇空格即断 ⇒ 路径含空格（macOS
        # "Library/Application Support/…"）被切成碎片，两片均命不中任何
        # SCOPES ⇒ 经 Bash 的管辖目录写入整体放行（与软链盲区同族·第二洞）。
        # 修：先按引号切段，段内整串作为候选；再对未引号部分走原 token 抽法。
        for seg in re.findall(r'"([^"]*)"|\'([^\']*)\'', cmd):
            q = seg[0] or seg[1] or ""
            if q and (q.startswith("~") or q.startswith("/")):
                paths.append(q.rstrip(",.\\"))
        bare = re.sub(r'"[^"]*"|\'[^\']*\'', " ", cmd)
        toks = [m.group(0).rstrip(",.\\") for m in
                re.finditer(r"(?:~|/)[^\s'\"|;>()]*", bare)]
        # v0.9（2026-10-05 Qoder CN 复验逮到 v0.8 回归）：v0.8 算出 toks 后忘并入
        # paths ⇒ 裸路径 Bash 写管辖目录全部静默放行（实测 cp ~/.qoder-cn/skills/…
        # exit0）——洞比它要修的空格路径洞更大。补：裸 token 一律并入候选。
        paths.extend(toks)
        # v0.8·续：裸路径含空格（未加引号的 "…/Library/Application Support/…"）
        # 仍会被切成碎片 ⇒ 对碎片做「相邻重组」：若某碎片 realpath 落进任一
        # SCOPES 前缀，则与前一碎片拼回完整路径再判（fail-safe·宁多判不漏判）。
        if toks:
            for prefix, _domain in SCOPES:
                for i, frag in enumerate(toks):
                    if not os.path.isabs(frag):
                        continue
                    if not any(prefix.startswith(frag) for prefix in
                               (os.path.normpath(prefix),)):
                        continue
                    for j in range(i):
                        merged = toks[j] + "/" + frag
                        paths.append(merged)
    return paths

def _resolve(p):
    """归一到**文件系统真实归属**的绝对路径（v0.7·2026-10-05 软链绕过根治）：
    病根：原版用 normpath 只折叠字符串形状，不解析软链 →
    `~/.qoder-cn/skills/* → 技能配置/*`、`~/.trae-cn/skills/* → 技能配置/*` 等
    真实存在的软链成为门卫盲区（对照实验：真实路径写 exit2、经软链同目标写 exit0）。
    与条文45同病根的另一面：字符串路径 ≠ 路径真实归属（45管书写侧，本管读取侧）。
    修法：realpath 解析软链后再与 SCOPES 真实前缀比对。⛔不得改回 normpath。
    相对路径→None（⛔不判·防项目级 .workbuddy 误伤）。"""
    p = str(p).replace("\\", "/").strip()
    if not p: return None
    if p.startswith("~"): p = os.path.expanduser(p)
    if not os.path.isabs(p): return None
    return os.path.realpath(p)

def hit_scope(p):
    ap = _resolve(p)
    if not ap: return None
    # 字面路径先判（快路径·零成本·覆盖真实目录写入）
    for prefix, domain in SCOPES:
        pre = os.path.realpath(prefix)  # v0.7：管辖前缀也走真实路径，防 SCOPES 自身含软链段
        if ap == pre or ap.startswith(pre + "/"):
            return domain
    return None

# 评估修复通道（v0.6·2026-10-03 皮叔令「按愿景最优解根治」）：
# clock-loop E路径对技能配置的修复写属合法流程（皮叔 09-27 修复授权令），经 clock-loop
# 阶段0 启动留痕 clockloop.active 代 skillforge 域标记——留痕真实性锚=SKILL.md 阶段0
# 确有此动作（载体=技能配置/clock-loop/SKILL.md），⛔流程未启动时手动 touch=撒谎留痕，
# 责任在 touch 者；本通道仅限 skillforge 域，其余域不扩大。
EVAL_CHANNELS = {"skillforge": "clockloop.active"}


def marker_fresh(domain):
    cands = [domain + ".active"] + [EVAL_CHANNELS[domain]] if domain in EVAL_CHANNELS \
        else [domain + ".active"]
    for f in cands:
        p = os.path.join(MARKER_DIR, f)
        try:
            if (time.time() - os.path.getmtime(p)) < MARKER_TTL:
                return True
        except OSError:
            pass
    return False

def main():
    if os.environ.get("SKILL_GATE_BYPASS") == GUARD_NAME:
        return  # guard自身写入豁免（防自锁）
    if "--claim-package-lock" in sys.argv:
        sys.exit(_pkg_claim())
    try:
        obj = json.load(sys.stdin)
    except Exception:
        return  # 畸形/空输入 → 失败放行（守卫规范·⛔不因守卫自身异常阻断用户操作）
    if not isinstance(obj, dict):
        return
    tool, inp = extract_event(obj)
    if tool not in ("Write", "Edit", "Bash", "MultiEdit", "NotebookEdit"):
        return
    # v0.10：锁操作命令本身恒放行；release 目睹=清认领账（锁周期闭合）
    _cmd0 = str(inp.get("command", ""))
    if tool == "Bash" and "package_lock.sh" in _cmd0:
        if "release" in _cmd0:
            try:
                os.remove(PKG_CLAIMED)
            except OSError:
                pass
        return
    # 豁免检查用完整原文（command/file_path）——match短串查不到豁免件（v0.1 bug修正）
    full_text = str(inp.get("command", "")) + " " + str(inp.get("file_path", ""))
    if any(x in full_text for x in EXEMPT):
        return  # 豁免件（append_log_entry/growth-box引擎/guard自身）→ 放行
    # 动作分级（v0.4）：file_path（Write/Edit）恒为写；Bash 按动作语义判 read/write/unknown
    severity = "hard"
    if tool in ("Bash", "bash"):
        act = _bash_action(str(inp.get("command", "")))
        if act == "read":
            return                                      # 只读命令 → 放行（不误伤）
        severity = "hard" if act == "write" else "soft"  # 未知命令 → 仅提示·不打断
    targets = extract_paths(tool, inp)
    blocked = set()
    for p in targets:
        d = hit_scope(p)
        if d and not marker_fresh(d):
            blocked.add(d)
    # v0.10 包面锁账本判据（严于 release marker·同端窗互盲的补强）：命中安装包路径的写，
    # 当前 holder ts 未被认领 ⇒ 硬拦（soft 仅提示·力度分级沿用）；release marker 旧制对包外发布库件不变。
    pkg_hit = [p for p in targets
               if hit_scope(p) == "release" and os.path.realpath(p).startswith(os.path.realpath(PKG_ROOT))]
    if pkg_hit:
        _h = _pkg_holder()
        if _h is None:
            _pkg_msg = ("包面未持锁（FREE）——写安装包必须先持锁：`bash \"%s/package_lock.sh\" acquire <端名>`，"
                        "获取成功后执行 `python3 \"%s\" --claim-package-lock` 认领留痕" % (PKG_ROOT, os.path.abspath(__file__)))
            if severity == "hard":
                print("⛔ 包面写门禁：" + _pkg_msg, file=sys.stderr); sys.exit(2)
            print("ℹ️ 包面写门禁（提示·不阻断）：" + _pkg_msg, file=sys.stderr)
            return
        if _h[1] not in _pkg_claimed():
            _pkg_msg = ("包面锁现由「%s」持有（ts=%s）——若贵窗正是持锁窗：认领一次全锁期通行 "
                        "`python3 \"%s\" --claim-package-lock`；若贵窗不是持锁窗：`acquire` 会 REFUSED，"
                        "写入必须排队，⛔绕行硬写（本判据=LRN-20261017-01 机制化·release 后认领账自动失效）"
                        % (_h[0], _h[1], os.path.abspath(__file__)))
            if severity == "hard":
                print("⛔ 包面写门禁：" + _pkg_msg, file=sys.stderr); sys.exit(2)
            print("ℹ️ 包面写门禁（提示·不阻断）：" + _pkg_msg, file=sys.stderr)
            return
    if not blocked:
        return
    names = {"growthbox": "growth-box（成长箱）", "skillforge": "相关Skill（skill-forge）",
             "digitaltwin": "数字分身工具链", "release": "发布同步（mirror-sync）",
             "workbuddy": "WorkBuddy系统文件"}
    domains = "、".join(sorted(names.get(d, d) for d in blocked))
    # v0.7 hint 花括号 bug 修：原 f-string `{{{...}}}` 渲染出字面 `{skillforge}.active`，
    # 照抄留痕的人 touch 出的文件名永远对不上 marker_fresh（实锤：盘上 {release}.active 垃圾件）。
    marker_list = " ".join(f"{d}.active" for d in sorted(blocked))
    hint = (f"→ 请先启动对应 Skill（如说'启动成长箱'），走完流程后重试；"
            f"若 Skill 流程确已在本会话走完，执行 "
            f"`mkdir -p ~/.cache/skill_gate && touch ~/.cache/skill_gate/{marker_list}` "
            f"留痕后重试。")
    if severity == "hard":
        print(f"⛔ Skill写入门卫：本次写入命中 Skill 管辖目录（{domains}）。"
              f"对应 Skill 本会话未启动（无有效启动标记）。{hint}", file=sys.stderr)
        sys.exit(2)
    # soft：Bash 命令判不出读写（如 python -c）→ 只提示、不阻断（v0.4·力度分级·防误伤）
    print(f"ℹ️ Skill写入门卫（提示·不阻断）：该命令可能写 Skill 管辖目录（{domains}），"
          f"但无法判定读写，故只提醒不拦截。{hint}", file=sys.stderr)
    return

if __name__ == "__main__":
    if GUARD_NAME in sys.argv[0] and "--selftest" in sys.argv:
        pass
    main()
