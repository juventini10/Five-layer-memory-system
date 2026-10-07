#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
systemlog_normalize_fix.py — 系统日志结构自修复（根治 emoji/描述式 ## 头 + 误归组）
设计依据: system-logger SKILL.md「结构健康门禁」治理步「按条目工具字段重组」
          + 「工具名规范」节（## 头必须是裸 allowlist 规范名，禁止 emoji/括号/描述后缀）
职责:
  幂等修复单文件——①任何非规范名 ## 头（被错当组头的任务标题）→ 按条目 - **工具**： 字段归组
            并降为 ### 清洗标题；②按条目 - **工具**： 字段把 entry 重排到对应 ## {工具} 组。
  这是「检测-only」normalize_tool.py 的互补「修复」通道：检测层拦异常，本脚本让异常物理上自我消解。
安全:
  先备份（.bak-<时间戳>）再写；仅移动/重命名标题行，绝不删内容；无变化则不写。
  本脚本是一次性整文件治理工具（对应门禁治理步「按条目工具字段重组」），非日写入路径，
  因此不受「整体读回写禁令」约束（该禁令作用于条目追加姿势，防 2^n 重复；本脚本幂等+备份，无重复风险）。
用法:
  python3 systemlog_normalize_fix.py [日志文件路径]   # 修复指定文件
  python3 systemlog_normalize_fix.py                  # 无参=今日日志（自动定位）
  python3 systemlog_normalize_fix.py --dry            # 只打印将发生的改动，不写盘
退出码: 0=已修复或无变化  1=通用错误
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, shutil
from datetime import date, datetime

HOME = os.path.expanduser("~")
SYSLOG_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "工作日志", "系统日志")

# ── 备份落点=记忆琥珀 + 留存封顶（2026-10-06 皮叔令「统一放记忆琥珀·不要在原文件备份」）──
# 旧认知已作废：原实现 bak = "<原路径>.bak-<时间戳>"，即备份写在**原文件旁边**。
# 病根实证：写时守护反复触发 → 日志目录一度攒到 41193 件 .bak / 1.89GB（09-27 单日 21306 件），
#   且备份与正文同目录 = 噪声进证据面（任何全树扫描被拖慢，guard_doc_consistency 全树扫描被 SIGKILL）。
# 铁律-005④ 明文要求「备份先 cp 到记忆琥珀路径」，原实现直接违反。
# 新契约：① 备份一律落 记忆琥珀/<用途>/<日期>/，⛔ 原文件旁零 .bak
#        ② 同一文件同一日期桶内最多留 AMBER_KEEP_PER_DAY 份，超出=废弃件 → trash（⛔不 rm）
#        ③ 废弃件不是备份，不进琥珀（琥珀只装值得追溯的快照）
AMBER_ROOT = os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆琥珀", "系统日志备份")
AMBER_KEEP_PER_DAY = 3
# 跨天上限：与记忆琥珀引擎的 `amber-backup.sh` RETENTION_DAYS=7 **同口径**（2026-10-06 补）。
# 病根实证：①记忆琥珀引擎的 7 天清理走 `find 全目录 -name "*.bak"` 但只清文件名匹配
#   `..._YYYYMMDD-HHMMSS_hash6.bak` 的（`amber-backup.sh` L135），同日去重只扫顶层（L164）
#   ⇒ **本脚本的 `.bak-HHMMSS_hash` 命名 + 日期子目录两层都不在它射程内**；
# ②⇒ 跨天清理**只有本脚本自己负责**，而按日分桶若不设跨天上限 ⇒ 一年 365 个桶永久堆积。
# 口径统一（=7 天，引擎同值）而非另立一套：两套上限并存 = 上限失效（谁大谁说了算）。
AMBER_KEEP_DAYS = 7


def _prune_old_buckets(root=None):
    """删除早于 AMBER_KEEP_DAYS 的日期桶（目录名 YYYY-MM-DD）。返回删除数。
    ⛔ 只删本脚本自己建的日期桶（`YYYY-MM-DD` 形态），⛔ 不碰桶内任何其他文件。"""
    base = root or AMBER_ROOT
    if not os.path.isdir(base):
        return 0
    import time as _t
    import re as _r
    cutoff = _t.time() - AMBER_KEEP_DAYS * 86400
    n = 0
    for name in os.listdir(base):
        d = os.path.join(base, name)
        if not os.path.isdir(d) or not _r.fullmatch(r"\d{4}-\d{2}-\d{2}", name):
            continue
        try:
            mt = os.path.getmtime(d)
        except OSError:
            continue
        if mt < cutoff:
            try:
                shutil.rmtree(d)
                n += 1
            except OSError:
                pass
    return n


def backup_to_amber(path, tag=""):
    """备份落记忆琥珀·按日期分桶·桶内限量。⛔绝不在原文件旁写 .bak。
    返回备份绝对路径；失败抛异常由调用方处理（⛔不静默吞掉备份失败）。"""
    now = datetime.now()
    bucket = os.path.join(AMBER_ROOT, now.strftime("%Y-%m-%d"))
    os.makedirs(bucket, exist_ok=True)
    base = os.path.basename(path)
    dst = os.path.join(bucket, "%s.bak-%s%s" % (base, now.strftime("%H%M%S_%f"), tag))
    shutil.copy2(path, dst)
    _dropped = _prune_old_buckets()   # 跨天上限（与引擎 7 天同口径）
    # 桶内限量：超出部分属废弃件 → trash
    same = sorted([f for f in os.listdir(bucket) if f.startswith(base + ".bak-")],
                  key=lambda f: os.path.getmtime(os.path.join(bucket, f)))
    stale = same[:max(0, len(same) - AMBER_KEEP_PER_DAY)]
    if stale:
        try:
            os.makedirs(TRASH_DIR, exist_ok=True)
        except OSError:
            pass
        for f in stale:
            try:
                os.replace(os.path.join(bucket, f), os.path.join(TRASH_DIR, f))
            except OSError:
                pass
    if _dropped:
        sys.stderr.write("[normalize_fix] 备份跨天清理：删除 %d 个超 %d 天的日期桶\n" % (_dropped, AMBER_KEEP_DAYS))
    return dst


# 历史存量清运用：把 target 旁的 .bak 裁到最近 keep 份（⛔仅清原位存量，新流程已不再产原位备份）
RETAIN_BAK = 5
TRASH_DIR = os.path.join(HOME, ".Trash", "bak轮转")


def prune_baks(target, keep=RETAIN_BAK):
    """把 target 的 .bak 裁到最近 keep 份，其余移入 trash。返回 (总数, 移出数)。"""
    d = os.path.dirname(os.path.abspath(target))
    base = os.path.basename(target)
    try:
        baks = [f for f in os.listdir(d) if f.startswith(base + ".bak-")]
    except OSError:
        return 0, 0
    baks.sort(key=lambda f: os.path.getmtime(os.path.join(d, f)))
    stale = baks[:max(0, len(baks) - keep)]
    if not stale:
        return len(baks), 0
    moved = 0
    try:
        os.makedirs(TRASH_DIR, exist_ok=True)
        for f in stale:
            try:
                os.replace(os.path.join(d, f), os.path.join(TRASH_DIR, f))
                moved += 1
            except OSError:
                pass
    except OSError:
        pass
    return len(baks), moved

# 工具表单一事实源（守卫编写规范§二原则1：真相有且只有一个物理住所，守卫只 import 不内联）
# 真源=normalize_tool.py 的 ALLOWLIST/VARIANTS；⛔DO NOT 在本文件恢复内联副本——内联即分叉，漂移是数学必然
# （实证：2026-08-25 本文件副本缺 Hermes → 守护把 ## Hermes 组头当异常拆掉归并，条目被误归组）
import importlib.util as _ilu

def _load_tool_table():
    _p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "normalize_tool.py")
    _spec = _ilu.spec_from_file_location("_normalize_tool_table", _p)
    if _spec is None or _spec.loader is None:
        raise ImportError("无法加载工具表真源 normalize_tool.py: %s" % _p)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod.ALLOWLIST, _mod.VARIANTS

ALLOWLIST, VARIANTS = _load_tool_table()
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF\U0000FE00-\U0000FE0F"
    "\U0001F900-\U0001F9FF\U0001FA70-\U0001FAFF\u20e3\ufe0f]"
)

def norm_key(name: str) -> str:
    return re.sub(r"[\W_]", "", name).lower()

def resolve_tool(text: str):
    """从一段文本（条目体或头部）解析所属工具名：优先变体/allowlist 子串精确匹配。"""
    # 1) 显式 - **工具**： 字段
    m = re.search(r"^\s*-\s*\*\*工具\*\*\s*：\s*(.+)$", text, re.M)
    if m:
        raw = m.group(1).strip()
        if raw in ALLOWLIST:
            return raw
        k = norm_key(raw)
        if k in VARIANTS:
            return VARIANTS[k]
        if k in ALLOWLIST:
            return k
    # 2) allowlist 名作为子串出现在文本中（大小写/emoji 归一后）
    norm = norm_key(text)
    for a in ALLOWLIST:
        if norm_key(a) in norm:
            return a
    for v, a in VARIANTS.items():
        if v in norm:
            return a
    return None

def resolve_tool_field(body: str):
    """归组专用：仅认条目体显式 - **工具**： 字段，绝不扫正文子串。
    正文偶提某工具名（如部署目标）≠ 该条目属于该工具，避免误归组。"""
    m = re.search(r"^\s*-\s*\*\*工具\*\*\s*：\s*(.+)$", body, re.M)
    if not m:
        return None
    raw = m.group(1).strip()
    if raw in ALLOWLIST:
        return raw
    k = norm_key(raw)
    if k in VARIANTS:
        return VARIANTS[k]
    if k in ALLOWLIST:
        return k
    return None

def clean_title(header_text: str):
    """把任务标题式 ## 头清洗为干净的 ### 标题：剥 emoji + allowlist 工具名 + 残留标点。"""
    t = _EMOJI_RE.sub("", header_text)
    # 剥 allowlist 名 / 变体名（大小写不敏感）
    for name in sorted(ALLOWLIST | set(VARIANTS.keys()), key=len, reverse=True):
        t = re.sub(re.escape(name), "", t, flags=re.IGNORECASE)
    # 剥残留连接符与空括号
    t = t.replace("·", " ").replace("•", " ")
    t = re.sub(r"\(\s*\)", "", t)          # 空括号
    t = re.sub(r"[（]\s*[）]", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    t = t.strip(" -··")
    return t if t else "未命名任务"

def parse(path):
    """返回 (h1_line, overview_lines, groups: list of (tool, [entries]))
       entries: list of (title_or_None, [body_lines])"""
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    h1 = lines[0] if lines and lines[0].startswith("# ") else "# 系统日志"
    # 找概览块
    overview = []
    rest_start = 0
    for i, ln in enumerate(lines):
        if ln.strip().startswith("## 今日概览"):
            j = i + 1
            while j < len(lines) and not (lines[j].startswith("## ") and "今日概览" not in lines[j]):
                overview.append(lines[j])
                j += 1
            rest_start = j
            break
    rest = lines[rest_start:]
    groups = []          # (tool_or_None, [(title, body_lines)])
    cur_tool = None
    cur_entry = None     # (title, body_lines)
    def flush_entry():
        nonlocal cur_entry
        if cur_entry is not None:
            groups.append((cur_tool, [cur_entry]))
            cur_entry = None
    def flush_group():
        nonlocal cur_tool
        flush_entry()
        if cur_tool is not None:
            pass  # group 已 append（entries 带 tool）
    for ln in rest:
        if ln.startswith("## "):
            head = ln[3:].strip()
            if "今日概览" in head:
                continue
            flush_entry()
            if head in ALLOWLIST:
                cur_tool = head
                cur_entry = None
            else:
                # 被错当组头的任务标题：解析所属工具，降为 ### entry
                tool = resolve_tool(head)
                title = clean_title(head)
                # 归入解析出的工具组；若解析不出工具，暂挂 None（末尾兜底）
                cur_tool = tool
                cur_entry = (title, [])
        elif ln.startswith("### "):
            flush_entry()
            title = ln[4:].strip()
            # 合法 ### 子标题原样保留（不清洗，避免误删 · 等合法标点）；
            # 仅当标题自身含 allowlist 工具名/emoji 时才清洗（罕见污染）。
            tool = resolve_tool(title)
            if tool is not None and cur_tool is None:
                cur_tool = tool
            cur_entry = (title, [])
        else:
            if ln.strip() == "":
                # 空行：不在任何 entry 内则跳过——避免 ## 头后/EOF 前尾随空行生成 phantom 空 entry（空组头）
                if cur_entry is not None:
                    cur_entry[1].append(ln)
                continue
            if cur_entry is None:
                # 组下首个 entry 无 ### 子标题（直接以 - **任务**： 开头）
                cur_entry = (None, [])
            cur_entry[1].append(ln)
    flush_entry()
    # 归组：每条 entry 仅按其自身 body 的显式 - **工具**： 字段重判归属（根治误归组），
    # 无显式字段则保留解析时的组归属（cur_tool）；两者皆无则兜底 WorkBuddy。
    # ⛔ 绝不扫正文子串——正文偶提工具名（如部署目标"悟空/云端"）≠ 该条目归属该工具。
    agg = {}   # tool -> [entries]
    order = []
    for tool, entries in groups:
        for (title, body) in entries:
            rt = resolve_tool_field("\n".join(body))   # 仅显式 - **工具**： 字段
            if rt is None:
                rt = tool or "WorkBuddy"
            agg.setdefault(rt, []).append((title, body))
            if rt not in order:
                order.append(rt)
    return h1, overview, agg, order

def emit(h1, overview, agg, order):
    out = [h1, ""]
    out.append("## 今日概览")
    out.append("")
    out.extend([l for l in overview if l.strip() != ""])
    out.append("")
    for tool in order:
        out.append("## %s" % tool)
        out.append("")
        for (title, body) in agg[tool]:
            b = list(body)
            while b and b[0].strip() == "":
                b.pop(0)
            while b and b[-1].strip() == "":
                b.pop()
            if not b:
                continue
            if title:
                out.append("### %s" % title)
                out.append("")
            out.extend(b)
            out.append("")
        # 组间空行已由 entry 末尾空行提供
    # 去掉尾部多余空行
    while out and out[-1] == "":
        out.pop()
    out.append("")
    return "\n".join(out)

def main():
    dry = "--dry" in sys.argv
    if len(sys.argv) > 1 and not dry:
        path = sys.argv[1]
    else:
        d = date.today().isoformat()
        path = os.path.join(SYSLOG_DIR, "系统日志_%s.md" % d)
    if not os.path.exists(path):
        print("❌ 日志文件不存在: %s" % path)
        return 1
    h1, overview, agg, order = parse(path)
    new_text = emit(h1, overview, agg, order)
    old_text = open(path, encoding="utf-8").read()
    if new_text == old_text:
        print("✅ 无需修复（已合规）: %s" % path)
        return 0
    if dry:
        print("🔍 将发生改动（--dry，未写盘）:")
        import difflib
        for line in difflib.unified_diff(old_text.splitlines(), new_text.splitlines(),
                                         lineterm="", n=1):
            print(line)
        return 0
    # v3.16.0批3 r2-C1：撤批1所插重复幂等块（L232既有早退已覆盖）；本项实际修复=微秒bak。
    #   r1 S8"每轮写盘"归因订正：早退在位仍每轮写 ⇒ emit/读回字节差振荡，根因未定位，记待查⛔不谎称已修。
    # 备份（2026-10-06 改：落记忆琥珀·⛔原文件旁零 .bak——旧实现即 41193 件堆积的源头）
    bak = backup_to_amber(path)
    # 审查F6修复：原子替换（tmp+os.replace·对齐 reconcile v3.11.0 方案）——
    # 二次读与写之间落下的他端 O_APPEND 条目不再被截断写吞掉；并发读者不再见半成品。
    tmp = "%s.tmp-%s" % (path, datetime.now().strftime("%Y%m%d%H%M%S"))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new_text)
    cur = open(path, encoding="utf-8").read()
    if cur != old_text:
        os.replace(tmp, "%s.aborted-%s" % (path, datetime.now().strftime("%Y%m%d%H%M%S")))  # 审查N3：带时间戳防二次放弃覆盖首次现场
        print("⚠️ 检测到写入前文件已被并发修改——本次 normalize 放弃（现场存 %s.aborted-<时间戳>），请重跑" % path)
        return 3
    os.replace(tmp, path)
    print("✅ 已修复并原子写盘: %s" % path)
    # 备份保留窗口（2026-10-06 新增）：写盘即裁 .bak，防止无界堆积复发
    _n, _moved = prune_baks(path)
    if _moved:
        print("🧹 备份轮转：原有 %d 份 → 留 %d 份（最近），移出 %d 份至 %s"
              % (_n, RETAIN_BAK, _moved, TRASH_DIR))
    # 诚实边界（审查N3·对齐兄弟脚本F7）：tmp写与replace之间微秒残窗仍存（缩窗非根治）·彻底解=fcntl锁·pending你授权
    print("📦 备份: %s" % bak)
    # 机械派生概览 + 门禁回验
    d0 = os.path.dirname(os.path.abspath(__file__))
    try:
        subprocess = __import__("subprocess")
        subprocess.run([sys.executable, os.path.join(d0, "reconcile_overview.py"), path], check=False)
        r = subprocess.run([sys.executable, os.path.join(d0, "systemlog_gate_check.py"), path],
                           capture_output=True, text=True)
        print(r.stdout, end="")
    except Exception as e:
        print("⚠️ 后处理异常（概览/门禁）: %s" % e)
    return 0

if __name__ == "__main__":
    sys.exit(main())
