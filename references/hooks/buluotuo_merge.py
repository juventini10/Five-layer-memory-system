#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""buluotuo_merge.py —— 布洛陀断章增量引擎（宪法 §2.0 C1–C7 的唯一执行体）

## 它解决什么

安装器要往**用户已有的文件**里写布洛陀的内容（SOUL.md / USER.md / MEMORY.md /
规则三层 / …）。⛔ 绝不整file覆盖用户已有信息——那是底线（C2）。

本引擎把所有这类写盘收敛到**一个**实现，避免每个落点各写一遍、每遍都可能写错。

## 核心契约

| 条款 | 本引擎如何保证 |
|:--|:---|
| C1 标记段包裹 | `upsert_section()` 只在 `<!-- BULUOTUO:BEGIN id -->` … `<!-- BULUOTUO:END id -->` 之间写 |
| C2 段外零改动 | 段外内容**逐字节**拼接保留；`selfcheck_outside()` 机械验 |
| C3 用户内容保留 | 同 C2（用户段外写的行天然在段外） |
| C4 升级只换段内 | 段已存在 ⇒ 只替换 BEGIN..END 之间，⛔ 不动位置与段外 |
| C5 已存在只追加 | 文件已存在且无段 ⇒ 追加到文末，⛔ 不重写整file |
| C6 写前备份 | `backup()` 强制调用，写前落 `*.bak-<ts>`；失败即中止 |
| C7 段级冲突报告 | `diff_section()` 返回冲突清单，由调用方输出，⛔ 不自动裁决 |

## 为什么用标记段而不是章节对齐

章节对齐（按标题匹配）有个致命问题：**用户的章节标题可能和包的一样**（都叫
「我怎么产出」），那时候分不清谁是谁。标记段是**物理锚点**，不依赖标题，
⛔ 不存在认错的可能。

## 用法

```python
from buluotuo_merge import upsert_section, backup, selfcheck_outside

backup(dst)                                   # C6：任何写之前
ok, status, msg = upsert_section(dst, "soul.persona", body)   # C1-C5 C7
assert ok, msg
viol = selfcheck_outside(dst, "soul.persona")  # C2 机械验
assert viol == [], viol
```

## 状态返回值

| status | 含义 | 调用方该做什么 |
|:--|:---|:---|
| `CREATED` | 首次写入该段 | 正常 |
| `UPDATED` | 段内内容变了 | 正常（包升级） |
| `UNCHANGED` | 段内内容一致 | 正常（幂等·不写盘） |
| `CONFLICT` | 段内被用户手改过且与包模板冲突 | ⛔ 不写，输出冲突报告（C7） |

⚠️ `CONFLICT` 是**默认不写**而非默认覆盖——宁可停下来问，也不要替用户决定。

## 自足性

stdlib only。⛔ 不依赖包内其他模块。Windows 同样可跑（cp1252/cp936 控制台已强制
UTF-8，见文件头）。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import datetime
import os
import re
import shutil
import sys
from typing import List, Optional, Tuple

__version__ = "1.0.0"

# Windows 控制台 cp1252/cp936 会把中文打挂（install_scripts.py 同款处理）
for _stream in (sys.stdout, sys.stderr):
    _reconf = getattr(_stream, "reconfigure", None)
    if callable(_reconf):
        try:
            _reconf(encoding="utf-8")
        except Exception:  # pragma: no cover - 平台差异，失败不阻塞
            pass

BEGIN_TMPL = "<!-- BULUOTUO:BEGIN {sid} -->"
END_TMPL = "<!-- BULUOTUO:END {sid} -->"

# 段 id 白名单：⛔ 防止把 id 拼错写出一个永远匹配不上的死段
_SID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

STATUS_CREATED = "CREATED"
STATUS_UPDATED = "UPDATED"
STATUS_UNCHANGED = "UNCHANGED"
STATUS_CONFLICT = "CONFLICT"


class MergeError(RuntimeError):
    """写盘前的硬失败（备份失败 / 段 id 非法 / 段结构损坏）——调用方必须中止。"""


def _diff_is_injection_only(user_sec: str, tpl_sec: str, rx) -> bool:
    """C14（2026-10-15）：用户段 vs 模板段的差异是否**纯属 step5 注入**。

    判据（逐行对齐·两行均先过 _cmp_norm 口径）：行数相等；每个差异行对上，
    模板行必须命中占位格模式（[Qn·答案待注入]/[Qn·规则待派生]）且用户行不再含占位
    ⇒ 该行差异=注入填充；任何其它差异（表头/行名/缩进外实质行）⇒ False（照报冲突）。
    无差异返回 False（交幂等腿，不消耗豁免）。
    """
    import re as _re
    us = [l.rstrip() for l in (user_sec or "").splitlines() if l.strip()]
    ts = [l.rstrip() for l in (tpl_sec or "").splitlines() if l.strip()]
    if len(us) != len(ts):
        return False
    seen = False
    for u, t in zip(us, ts):
        if u == t:
            continue
        # 收紧（T12b 教训）：不是「模板行含占位+用户行无占位」就放行——
        # 必须用户行=模板行的占位格被非空填充、其余片段逐段原样，否则=真改动照报。
        parts = rx.split(t)
        if len(parts) < 2:
            return False
        import re as _r2
        pat = "^" + "(.+?)".join(_r2.escape(x) for x in parts) + "$"
        if not _r2.match(pat, u):
            return False
        seen = True
    return seen


def _cmp_norm(s: str) -> str:
    """段级比对的归一化（2026-10-04·空行差异不算冲突）

    🔴 病根：旧写法 `.strip("\n")` 只去首尾换行，**段内**多一个空行即判不等
       ⇒ CONFLICT ⇒ 回执 degraded=1（假红·实测铁律版「AI执行铁律」段
       ⛔ 零内容差异·纯 5 处空行差异却被判冲突）。
    ✅ 只归一「空行」：删掉所有**纯空白行**（只含空白/零宽的整行），
       其余行仅去**行尾**空白（⛔ 不动行首缩进）。
       ⛔ **不忽略任何实质字符**（文字/标点/缩进照旧判不等）。
    """
    out = []
    for l in (s or "").split("\n"):
        if not l.strip():          # 纯空白行 ⇒ 整行删除（含段内单个空行）
            continue
        out.append(l.rstrip())     # 只去行尾空白·⛔ 不动行首缩进
    return "\n".join(out)


def _ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _check_sid(sid: str) -> None:
    if not isinstance(sid, str) or not _SID_RE.match(sid or ""):
        raise MergeError("非法段 id: %r（只允许小写字母/数字/.-_，1-64 字符）" % (sid,))


# ── 读取 ────────────────────────────────────────────────────────────

def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def find_section_bounds(text: str, sid: str) -> Optional[Tuple[int, int]]:
    """返回 (段内容起止偏移, 含标记行)。⛔ 无此段返回 None。

    ⚠️ 结构损坏（BEGIN 有 END 无，或反之）⇒ 抛 MergeError，**不回退到覆盖**——
    损坏的段被当成"不存在"再追加一个，会留下两个半截段。
    """
    _check_sid(sid)
    b = BEGIN_TMPL.format(sid=sid)
    e = END_TMPL.format(sid=sid)
    bi, ei = text.find(b), text.find(e)
    if bi < 0 and ei < 0:
        return None
    if bi < 0 or ei < 0:
        raise MergeError(
            "段 %r 标记不成对（BEGIN 有 END 无，或反之）——拒绝自动修复，"
            "请人工确认后处理：%s" % (sid, path_hint(b, e))
        )
    if ei < bi:
        raise MergeError("段 %r 的 END 出现在 BEGIN 之前，拒绝处理" % (sid,))
    return bi, ei + len(e)


def path_hint(b: str, e: str) -> str:
    return "BEGIN@%s / END@%s" % (b, e)


def read_section(text: str, sid: str) -> Optional[str]:
    """读段内正文（不含标记行）。⛔ 无此段返回 None。"""
    bounds = find_section_bounds(text, sid)
    if bounds is None:
        return None
    bi, ei = bounds
    b = BEGIN_TMPL.format(sid=sid)
    body_start = bi + len(b)
    body_end = text.rfind(END_TMPL.format(sid=sid), body_start, ei)
    return text[body_start:body_end].strip("\n")


def read_outside(text: str, sid: str) -> str:
    """读段外全文——这是**必须原样保留**的部分。"""
    bounds = find_section_bounds(text, sid)
    if bounds is None:
        return text
    bi, ei = bounds
    return text[:bi] + text[ei:]


# ── 写入 ────────────────────────────────────────────────────────────

def backup(path: str, backup_dir: Optional[str] = None) -> Optional[str]:
    """C6：写前备份。文件不存在 ⇒ 返回 None（无需备份）。

    ⚠️ 备份失败即抛错——**不允许"备份失败但继续写"**，那是拿用户数据赌。
    """
    if not os.path.isfile(path):
        return None
    d = backup_dir or (os.path.dirname(os.path.abspath(path)) or ".")
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(
        d, "%s.bak-%s" % (os.path.basename(path), _ts())
    )
    try:
        shutil.copy2(path, dst)
    except Exception as exc:
        raise MergeError("备份失败·拒绝写入：%s ← %s（%r）" % (dst, path, exc))
    if os.path.getsize(dst) <= 0:
        raise MergeError("备份产物零字节·拒绝写入：%s" % (dst,))
    return dst


def render_section(sid: str, body: str) -> str:
    """渲染带标记的段文本。"""
    _check_sid(sid)
    body = (body or "").strip("\n")
    return "%s\n%s\n%s" % (BEGIN_TMPL.format(sid=sid), body, END_TMPL.format(sid=sid))


def upsert_section(
    path: str,
    sid: str,
    body: str,
    *,
    template_body: Optional[str] = None,
    do_backup: bool = True,
    backup_dir: Optional[str] = None,
    dry: bool = False,
) -> Tuple[bool, str, str]:
    """把 body 增量写进 path 的 sid 段。返回 (ok, status, msg)。

    `template_body` = 包内模板的段内容。给了才会做 C7 冲突判定：
    段内现内容 ≠ 上次装的模板内容 ⇒ 说明用户手改过 ⇒ CONFLICT，**不写**。
    不给则跳过冲突判定（首次安装场景，合理）。
    """
    _check_sid(sid)
    old = read_text(path)
    has_file = bool(old)
    old_section = read_section(old, sid) if has_file else None
    new_section = (body or "").strip("\n")

    # ── C7 冲突判定（用户手改过 ⇒ 停下报告，不自动裁决）
    if old_section is not None and template_body is not None:
        if _cmp_norm(old_section) != _cmp_norm(template_body):
            return (
                False,
                STATUS_CONFLICT,
                "段 %r 已被用户修改（现内容 ≠ 包模板）·拒绝自动覆盖·"
                "请人工裁决或用 --force-segment" % (sid,),
            )

    # ── 幂等：内容一致则不写盘（不改 mtime，⛔ 不制造"看起来变了"的假象）
    if old_section is not None and _cmp_norm(old_section) == _cmp_norm(new_section):
        return True, STATUS_UNCHANGED, "段 %r 内容一致·未写盘（幂等）" % (sid,)

    new_text, kind = _splice(old, sid, new_section)
    # ── C2 自检：用户的原有字节必须**逐字节原样在位**（⛔ 写盘前拦，不靠事后 diff）
    #    判据按 kind 分两种，⛔ 不混用：
    #      append  → 新文本必须以原文本**原样开头**（用户内容在段前，逐字节不变）
    #      replace → 段前片段必须逐字节等于原段前，且段后片段必须逐字节等于原段后
    viol = _assert_user_bytes_intact(old, new_text, sid, kind)
    if viol:
        raise MergeError("C2 违反：%s·拒绝写入" % viol)

    if do_backup and not dry:
        backup(path, backup_dir)

    if dry:
        return True, STATUS_CREATED if old_section is None else STATUS_UPDATED, "[dry-run]"

    _atomic_write(path, new_text)
    return True, STATUS_CREATED if old_section is None else STATUS_UPDATED, "段 %r 已写入（%s）" % (sid, kind)


def _assert_user_bytes_intact(old: str, new: str, sid: str, kind: str) -> str:
    """C2 机械自检。返回违规描述（空串 = 通过）。

    ⚠️ 判据方向很重要：**新文本 vs 原文本**。
    若拿"段外"这种派生量互相比，派生逻辑和合并逻辑同源 ⇒ 两边一起错时判不出
    （实证：首次建段时该判据恒失败——是判据写错了，不是合并错了）。
    """
    if kind == "create":
        # 全新文件：原文件为空 ⇒ 「用户原有字节原样保留」的判据 = 盘上原为空
        return "" if old == "" else "kind=create 但原文件非空（合并逻辑有 bug）"
    if kind == "append":
        if not new.startswith(old):
            return "用户原有内容未原样保留在段前（append 形态）"
        return ""
    bi_o, ei_o = find_section_bounds(old, sid)
    bi_n, ei_n = find_section_bounds(new, sid)
    if bi_o is None or ei_o is None or bi_n is None or ei_n is None:
        return "replace 形态下段边界丢失（合并逻辑有 bug）"
    if old[:bi_o] != new[:bi_n]:
        return "段前内容被改动（replace 形态）"
    if old[ei_o:] != new[ei_n:]:
        return "段后内容被改动（replace 形态）"
    return ""


def _splice(old: str, sid: str, new_section: str) -> Tuple[str, str]:
    """把新段拼进原文。⛔ 用户原有字节原样保留。

    返回 (新文本, kind)，kind ∈ {"create", "append", "replace"}。
    """
    block = render_section(sid, new_section)
    if not old:
        return block + "\n", "create"
    bounds = find_section_bounds(old, sid)
    if bounds is None:
        # C5：文件已有内容但无本段 ⇒ 追加到文末，⛔ 不重写既有内容
        sep = "" if old.endswith("\n\n") else ("\n" if old.endswith("\n") else "\n\n")
        return old + sep + block + "\n", "append"
    bi, ei = bounds
    return old[:bi] + block + old[ei:], "replace"


def _atomic_write(path: str, text: str) -> None:
    """原子写：同目录临时文件 + os.replace（⛔ 写一半崩了不留残file）。"""
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, ".%s.tmp-%s" % (os.path.basename(path), _ts()))
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


# ── 带 frontmatter 的文件（规则三层/技能卡等）────────────────────────
#
# ⚠️ 为什么单列一节：**YAML frontmatter 必须在文件第 1 行**才被解析。
# 若把整个文件包进标记段，frontmatter 就不再在首位 ⇒ 所有读它的工具
# （frontmatter 取值 / `alwaysApply` 注入 / guard 的 description 计数）全部失效。
# 所以这类文件的形态是「frontmatter 在外·正文在段内」。

def split_frontmatter(text: str) -> Tuple[str, str]:
    """拆成 (frontmatter块含分隔符, 正文)。⛔ 无 frontmatter ⇒ ("", 全文)。

    判据：首行必须是 `---`，且其后有配对的 `---`。⛔ 正文里出现的 `---`
    分隔线不算（只在文件开头才尝试）。
    """
    if not text.startswith("---"):
        return "", text
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return "", text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[: i + 1]) + "\n"
            return fm, "\n".join(lines[i + 1:])
    # 开了头没闭合 ⇒ 当作没有 frontmatter，⛔ 不猜（猜错会让 frontmatter 进正文）
    return "", text


def upsert_file_body(
    path: str,
    sid: str,
    full_text: str,
    *,
    template_full: Optional[str] = None,
    inject_exempt_re: Optional[str] = None,
    do_backup: bool = True,
    backup_dir: Optional[str] = None,
    dry: bool = False,
) -> Tuple[bool, str, str]:
    """带 frontmatter 的整file增量写。返回 (ok, status, msg)。

    `inject_exempt_re`（C14）：step5 注入位占位格的行模式（如摘要版 `[Qn·答案待注入]`）。
    给出时，「纯注入差异」不判用户手改（UNCHANGED 预期态·⛔ 覆盖注入内容）；
    仅在包正文与模板一致（重装无升级）时生效——包升级撞上已注入格=真冲突照报，交人工。

    形态：**frontmatter 留在文件首位（用户已有则保留用户的）· 正文走标记段**。

    ⚠️ frontmatter 归属：用户已有 frontmatter ⇒ **保留用户的**（⛔ 不覆盖，
    因为 description/alwaysApply 是平台行为开关，用户可能故意调过）。
    包内 frontmatter 仅在文件**没有** frontmatter 时才补。
    """
    _check_sid(sid)
    pkg_fm, pkg_body = split_frontmatter(full_text or "")
    # 🔴 2026-10-03 根治「装出的规则文件双份」：
    #   实测装出的 `用户基本规则-摘要版.md` 174 行 / `BULUOTUO:BEGIN` **2 处** / 标题 2 次。
    #   根因：本函数把「frontmatter 之后的**全部**内容」当段正文，
    #   而模板形态是「裸正文 + BEGIN/END 段」⇒ pkg_body = 裸正文+整段（连标记），
    #   `_splice` 再套一层 BEGIN/END ⇒ 用户机上装出来就是两份。
    #   ⛔ 旧假设「模板双份是残留」已被实测否证（模板改单份后装出仍 2 处）——病在取段口径。
    #   ✅ 正解：按段 id 取**段内正文**（不含标记行）；模板无该段才回落全量。
    _sec = read_section(pkg_body, sid)
    if _sec is not None:
        pkg_body = _sec
    old = read_text(path)
    old_fm, old_body = split_frontmatter(old) if old else ("", "")

    # ── C7：正文段冲突判定
    old_section = read_section(old_body, sid) if old_body else None
    if old_section is not None and template_full is not None:
        # 🔴 2026-10-03 与 upsert 取段口径对齐（同根修复）：
        #   旧写法拿「模板 frontmatter 之后的**全部**」跟段内正文比——
        #   模板形态是「裸正文 + BEGIN/END 段」⇒ 两者恒不相等
        #   ⇒ 第二次安装必判 CONFLICT ⇒ 回执 verdict 由 ok 降为 degraded（假降级）。
        #   ✅ 正解：同样按段 id 取段内正文再比，口径与写入侧一致。
        _, _tpl_all = split_frontmatter(template_full)
        _tpl_sec = read_section(_tpl_all, sid)
        _tpl_cmp = _tpl_sec if _tpl_sec is not None else _tpl_all
        if _cmp_norm(old_section) != _cmp_norm(_tpl_cmp):
            # C14 注入预期态豁免：纯占位格填充不算用户手改（重装场景）；包升级照报
            if (inject_exempt_re
                    and _cmp_norm(pkg_body) == _cmp_norm(_tpl_cmp)
                    and _diff_is_injection_only(old_section, _tpl_cmp,
                                                __import__("re").compile(inject_exempt_re))):
                return True, STATUS_UNCHANGED, (
                    "段 %r 为 step5 注入预期态（占位格已填·纯注入差分）·幂等不写·⛔ 覆盖注入内容" % (sid,))
            return (
                False,
                STATUS_CONFLICT,
                "段 %r 已被用户修改（现内容 ≠ 包模板）·拒绝自动覆盖·请人工裁决" % (sid,),
            )

    # ── 幂等
    if old_section is not None and _cmp_norm(old_section) == _cmp_norm(pkg_body):
        return True, STATUS_UNCHANGED, "段 %r 正文一致·未写盘（幂等）" % (sid,)

    new_body, kind = _splice(old_body, sid, pkg_body)
    viol = _assert_user_bytes_intact(old_body, new_body, sid, kind)
    if viol:
        raise MergeError("C2 违反：%s·拒绝写入" % viol)

    # frontmatter：用户有⇒留用户的；没有⇒补包内的（⛔ 绝不覆盖用户的）
    head = old_fm if old_fm.strip() else pkg_fm
    new_text = head + new_body

    if do_backup and not dry:
        backup(path, backup_dir)
    if dry:
        return True, STATUS_CREATED if old_section is None else STATUS_UPDATED, "[dry-run]"
    _atomic_write(path, new_text)
    return True, STATUS_CREATED if old_section is None else STATUS_UPDATED, (
        "段 %r 已写入（%s·frontmatter=%s）"
        % (sid, kind, "保留用户" if old_fm.strip() else "取包内")
    )


# ── 机械自检（验收用·⛔ 别删）────────────────────────────────────────

def selfcheck_outside(path: str, sid: str, original_text: str) -> List[str]:
    """装完校验：用户的**原有字节**是否原样在位。返回违规列表（空 = 过）。

    `original_text` = **安装前**的整file原文（⛔ 不是"段外"，见下）。

    ⚠️ 为什么不用 read_outside 互相比：那是**派生量**，与合并逻辑同源——
    两边一起错时判不出（实证：append 形态下段外会多出一个分隔换行，
    拿派生量互比 ⇒ 恒假红）。判据必须直接比**用户原始字节**。
    """
    now = read_text(path)
    viol: List[str] = []
    bounds = find_section_bounds(now, sid)
    if bounds is None:
        viol.append("装后段 %r 不存在（段被丢了？）" % (sid,))
        return viol
    bi, ei = bounds
    rest = now[:bi] + now[ei:]          # 去掉段块后的剩余全文
    ob = find_section_bounds(original_text, sid)
    if ob is None:
        # 安装前没有本段 ⇒ 必须是「追加」形态：原文件应原样留在前面
        if not rest.startswith(original_text):
            viol.append(
                "C2 违反：用户原有内容未原样保留在段前（append 形态）"
            )
    else:
        oi, oe = ob
        if rest != original_text[:oi] + original_text[oe:]:
            viol.append(
                "C2 违反：段外内容被改动（replace 形态·期望 %d 字符·实得 %d 字符）"
                % (len(original_text[:oi] + original_text[oe:]), len(rest))
            )
    return viol


def selfcheck_single_section(path: str, sid: str) -> List[str]:
    """装完校验：该 sid 段**只出现一次**（防重复段）。"""
    text = read_text(path)
    b = text.count(BEGIN_TMPL.format(sid=sid))
    e = text.count(END_TMPL.format(sid=sid))
    viol = []
    if b != 1:
        viol.append("段 %r 的 BEGIN 出现 %d 次（应为 1）" % (sid, b))
    if e != 1:
        viol.append("段 %r 的 END 出现 %d 次（应为 1）" % (sid, e))
    return viol


def selfcheck_all(path: str, sid: str, original_text: str) -> List[str]:
    """全部自检合并跑一遍（验收主入口）。

    `original_text` = 安装前的整file原文（⛔ 不是 read_outside 的结果）。
    """
    return (
        selfcheck_outside(path, sid, original_text)
        + selfcheck_single_section(path, sid)
    )


# ── CLI（供人工排查用）──────────────────────────────────────────────

def _main(argv: List[str]) -> int:
    if len(argv) >= 3 and argv[1] == "show":
        text = read_text(argv[2])
        bounds = find_section_bounds(text, argv[3]) if len(argv) > 3 else None
        if bounds is None:
            print("（无段）")
        else:
            print(read_section(text, argv[3]))
        return 0
    if len(argv) >= 4 and argv[1] == "verify":
        # verify <file> <sid> <outside-snapshot>
        outside = read_text(argv[4]) if len(argv) > 4 else ""
        viol = selfcheck_all(argv[2], argv[3], outside)
        if viol:
            for v in viol:
                print("❌ " + v)
            return 1
        print("✅ 段外零改动 + 单段唯一")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))