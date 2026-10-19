#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""json_key_merge.py —— JSON **键级增量合并**（保注释 / 保缩进 / 保键序）

## 它解决什么

安装器要在用户的 `settings.json` 里注册钩子。旧写法是
`json.load(整file)` → 改 `hooks` → `json.dump(整file 写回)`。

⛔ 那会毁掉用户文件里的一切格式信息：注释（JSONC）、缩进风格（tab/空格）、
键顺序、**值内部的注释**、空行分段。这些都不是「数据」，但都是用户亲手维护的东西。

## 核心设计：**只做「确保存在」，不做「整体替换」**

| 两侧类型 | 处置 |
|:---|:---|
| dict ↔ dict | 逐键递归：已有键递归处理（值缺失才替换），新键追加到末尾 |
| list ↔ list | **只追加缺项**：已有项逐字节保留（含其内部注释） |
| 标量 ↔ 标量 | 相同 ⇒ noop；**不同 ⇒ 抛 MergeError**（⛔ 不替用户裁决） |
| 类型不一致 | 抛 MergeError（⛔ 不静默替换） |

⇒ 语义是「**union-add**」而非「replace」。这正是注册钩子需要的语义。

## 保证

| 项 | 做法 |
|:--|:---|
| 非目标内容逐字节保留 | 文本级拼接，⛔ 不做序列化往返 |
| 注释保留 | 同上（值内部注释靠「只追加」保住） |
| 缩进风格保留 | 从原文件推断单位（tab 亦可），新片段用同款 |
| 键顺序保留 | 已有键位置不动；新键追加到末尾 |
| 幂等 | 已是目标态 ⇒ `changed=False`，⛔ 不写盘 |
| 写前备份 | 备份失败即中止 |
| 原子写 | 同目录临时文件 + os.replace |

## 用法

```python
from json_key_merge import merge_key
r = merge_key(path, "hooks", {"Stop": ["cmd.py"]})
# r.changed / r.action ∈ created|merged|unchanged ; MergeError=冲突
```

CLI：`python3 json_key_merge.py keys <file>` · `show <file> <key>`
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import datetime
import json
import os
import re
import shutil
import sys
from typing import Any, Dict, List, Optional, Tuple

__version__ = "2.0.0"

for _stream in (sys.stdout, sys.stderr):
    _reconf = getattr(_stream, "reconfigure", None)
    if callable(_reconf):
        try:
            _reconf(encoding="utf-8")
        except Exception:  # pragma: no cover
            pass


class MergeError(RuntimeError):
    """合并前的硬失败/冲突——调用方必须中止，⛔ 不回退到覆盖。"""


class Result:
    __slots__ = ("changed", "action", "note")

    def __init__(self, changed: bool, action: str, note: str = ""):
        self.changed = changed
        self.action = action        # created / merged / unchanged
        self.note = note

    def __repr__(self) -> str:  # pragma: no cover
        return "Result(changed=%r, action=%r, note=%r)" % (
            self.changed, self.action, self.note)


def _ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


# ── JSONC → 纯 JSON（剥注释但**保长度**，偏移才可复用）────────────────

_STR_RE = re.compile(r'"(?:\\.|[^"\\])*"')


def strip_jsonc(text: str) -> str:
    """剥注释，注释位置换成**等长空格**（换行保留）。

    ⚠️ 必须保长度——本模块靠字符偏移定位；改长度会让偏移全部错位。
    ⚠️ 必须不碰字符串字面量里的 `//` 与 `/*`（URL、正则、文案里都有）。
    """
    out = list(text)
    i, n = 0, len(text)
    in_str = False
    while i < n:
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            i += 1
            continue
        if ch == "/" and i + 1 < n:
            nxt = text[i + 1]
            if nxt == "/":
                j = text.find("\n", i)
                j = n if j < 0 else j
                for k in range(i, j):
                    out[k] = " "
                i = j
                continue
            if nxt == "*":
                j = text.find("*/", i + 2)
                j = n if j < 0 else j + 2
                for k in range(i, j):
                    if out[k] != "\n":
                        out[k] = " "
                i = j
                continue
        i += 1
    return "".join(out)


# ── 区间定位 ─────────────────────────────────────────────────────────

def _skip_ws(s: str, i: int) -> int:
    n = len(s)
    while i < n and s[i] in " \t\r\n":
        i += 1
    return i


def _scan_string(s: str, i: int) -> int:
    """s[i] 必须是 `"`；返回字符串结束后的下标。"""
    m = _STR_RE.match(s, i)
    if not m:
        raise MergeError("字符串字面量未闭合（文件截断？）·⛔ 中止")
    return m.end()


def _value_end(s: str, start: int) -> int:
    """返回 s[start:] 起一个完整值的**结束下标后一位**。

    ⚠️⛔ **必须用栈式配对**，⛔ 不能只数深度：`}` 与 `]` 混算深度时，
    `{"hooks": [{...}]}` 里的内层 `]` 会把深度减到 0 ⇒ 提前返回 ⇒
    `_iter_list_items` 拿到错位偏移后 cur 不前进 ⇒ **死循环**（实测 J2 挂死）。
    """
    n = len(s)
    if start >= n:
        raise MergeError("值起始越界（文件截断？）·⛔ 中止")
    if s[start] in "{[":
        stack = [s[start]]
        i = start + 1
        while i < n:
            c = s[i]
            if c == '"':
                i = _scan_string(s, i)
                continue
            if c == "{":
                stack.append(c)
            elif c == "[":
                stack.append(c)
            elif c in "}]":
                if not stack:
                    raise MergeError("多出闭合符 %r·⛔ 中止" % c)
                op = stack.pop()
                if (op == "{" and c != "}") or (op == "[" and c != "]"):
                    raise MergeError("括号错配：%r 对 %r·⛔ 中止" % (op, c))
                if not stack:
                    return i + 1
            i += 1
        raise MergeError("括号不配对·⛔ 中止")
    i = start
    while i < n and s[i] not in ",}] \t\r\n":
        i += 1
    return i


def find_key_span(s: str, lo: int, hi: int, key: str) -> Optional[Tuple[int, int]]:
    """在 s[lo:hi] 这段**对象**内找 `key`，返回 (值起, 值止)。⛔ 无则 None。"""
    i = _skip_ws(s, lo)
    if i >= hi or s[i] != "{":
        return None
    i += 1
    depth = 1
    while i < hi:
        c = s[i]
        if c == '"':
            j = _scan_string(s, i)
            if depth == 1:
                k = _skip_ws(s, j)
                if k < hi and s[k] == ":" and json.loads(s[i:j]) == key:
                    vs = _skip_ws(s, k + 1)
                    return vs, _value_end(s, vs)
            i = j
            continue
        if c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
            if depth == 0:
                return None
        i += 1
    return None


# ── 缩进 ─────────────────────────────────────────────────────────────

_INDENT_RE = re.compile(r"\n([ \t]+)\S")


def infer_indent(text: str) -> str:
    m = _INDENT_RE.search(text)
    return m.group(1) if m else "  "


def render_inline(val: Any, indent: str, base: str = "") -> str:
    """渲染成多行 JSON，缩进风格跟随 `indent` 单位（tab 亦可）。

    ⚠️ `json.dumps(indent=N)` 只吐空格 ⇒ 原文件是 tab 时会被静默换成空格
    （实测 J3 假红时暴露）。故按单位重铺每行前导缩进。
    ⚠️ `base` = **续行前缀**（dumps 缩进之前的额外缩进）。
    ⚠️ 首行不加任何前缀——它紧跟在 `"key": ` 后面，缩进由调用方的
    `"%s: %s"` 拼接决定（加了就会把首行推歪，实测输出成 `"A":       [`）。
    """
    body = json.dumps(val, ensure_ascii=False, indent=max(len(indent), 1))
    if indent.strip() != "":
        raise MergeError("缩进单位异常（含非空白字符）：%r" % (indent,))
    unit = max(len(indent), 1)
    lines = body.split("\n")
    out = [lines[0]]
    for ln in lines[1:]:
        ws = len(ln) - len(ln.lstrip(" "))
        out.append(base + indent * (ws // unit) + ln.lstrip(" "))
    return "\n".join(out)


# ── 递归键级合并 ─────────────────────────────────────────────────────

def _iter_dict_entries(s: str, vs: int, ve: int):
    """遍历对象内每个 (键, 值起, 值止, 下一个条目的起始偏移, 尾部留白)。

    ⚠️ 每轮必须跳过空白——否则遇到 `"key": value` 的 `:` 后的空格时
    `_value_end` 原地返回 ⇒ cur 不前进 ⇒ **死循环**（实测 J2 挂死 120s）。
    """
    cur = vs + 1
    while cur < ve:
        j = _skip_ws(s, cur)
        if j >= ve or s[j] == "}":
            return
        if s[j] == ",":
            cur = j + 1
            continue
        if s[j] != '"':
            raise MergeError("对象内出现非键内容（偏移错位？）·⛔ 中止")
        ke = _scan_string(s, j)
        key = json.loads(s[j:ke])
        colon = _skip_ws(s, ke)
        if colon >= ve or s[colon] != ":":
            raise MergeError("键 %r 后缺 `:`（偏移错位？）·⛔ 中止" % key)
        vstart = _skip_ws(s, colon + 1)
        vend = _value_end(s, vstart)
        nxt = _skip_ws(s, vend)
        if nxt < ve and s[nxt] == ",":
            nxt = nxt + 1
        yield key, vstart, vend, nxt
        cur = vend


def _iter_list_items(s: str, vs: int, ve: int):
    """遍历数组内每个 (项文本起, 项文本止, 下一项起始)。

    ⚠️ **零长度项必须硬停**：`_value_end` 在「当前字符是闭合符」时返回
    原位（不前进）。若不检查 `en > st`，游标永远卡在同一偏移 ⇒ **死循环**
    （实测：项尾是 `}` 而数组闭合是 `]` 时必现）。
    """
    cur = _skip_ws(s, vs + 1)
    while cur < ve:
        c = s[cur]
        if c in ",]}" or c in " \t\r\n":
            if c == ",":
                cur = _skip_ws(s, cur + 1)
                continue
            return                                # 到达数组/对象闭合符
        st = cur
        en = _scan_string(s, cur) if c == '"' else _value_end(s, cur)
        if en <= st:                              # ⛔ 零进展 ⇒ 停止（防死循环）
            return
        nxt = _skip_ws(s, en)
        if nxt < ve and s[nxt] == ",":
            nxt = nxt + 1
        yield st, en, nxt
        cur = en


def _merge_into(s: str, vs: int, ve: int, new_val: Any,
                indent: str, path: str = "", src: Optional[str] = None):
    """把 `new_val` 合并进 s[vs:ve] 这段值，返回 (新片段, 是否改动)。

    ⚠️ **`s` 与 `src` 的分工**（实测 J2 值内注释丢失时暴露）：
    - `s`   = 剥掉注释后的文本，**只用于扫描/定位**（偏移与 `src` 恒等，
              因为 `strip_jsonc` 保长度）
    - `src` = **原始文本**，用于**取原片段拼回去**
    ⛔ 若从 `s` 取片段拼回去 ⇒ 该片段的注释被空格替换 ⇒ 用户注释静默消失。
    """
    src = s if src is None else src
    old_txt = s[vs:ve]
    if not old_txt.strip():
        return render_inline(new_val, indent), True
    old_val = json.loads(s[vs:_value_end(s, vs)])
    ko, kn = type(old_val), type(new_val)

    if kn is not dict and kn is not list:                     # 标量
        if old_val == new_val:
            return src[vs:ve], False
        raise MergeError("标量冲突 %s：盘上 %r vs 包 %r·⛔ 拒绝自动覆盖"
                         % (path or "<root>", old_val, new_val))
    if ko is not kn:
        raise MergeError("类型冲突 %s：盘上 %s vs 包 %s·⛔ 拒绝替换"
                         % (path or "<root>", ko.__name__, kn.__name__))
    if kn is dict:
        return _merge_dict(s, vs, _value_end(s, vs), new_val, indent, path, src)
    return _merge_list(s, vs, _value_end(s, vs), new_val, indent, path, src)


def _indent_of(s: str, pos: int) -> Tuple[str, str, bool]:
    """求 pos 处值/键的缩进信息。

    返回 (行首缩进, 本层键/项缩进, 值是否独占一行)。

    ⚠️ **踩过的坑**（J1 实测输出被污染成 `"hooks": "A": ...`）：
    直接用 `pos - line_start` 当缩进，会把**同一行前面的 `"key": ` 也算进去**——
    因为值常常不是行首（`  "A": [` 里的 `[` 就不在行首）。
    正解：先取**行首连续空白**；值若紧跟其后（独占一行）⇒ 本层缩进=行首缩进；
    否则（值在同一行跟在键后面）⇒ 本层缩进 = 行首缩进 + 一级。
    """
    line_start = s.rfind("\n", 0, pos) + 1
    j = line_start
    while j < len(s) and s[j] in " \t":
        j += 1
    line_indent = s[line_start:j]
    alone = (j == pos)
    return line_indent, (line_indent if alone else None), alone


def _merge_dict(s: str, vs: int, ve: int, new_val: Dict[str, Any],
                indent: str, path: str, src: Optional[str] = None) -> Tuple[str, bool]:
    """逐键递归。

    ⚠️ **只重建「键值区」**：`s[kstart:colon+1] + gap + 值`。键与键之间的
    注释/空行落在 seg 之外，原样保留（实证：早期版本重建整段 ⇒ 值内注释
    `// 我自己的钩子·别动` 消失——键保住了，键前那段没了）。
    """
    src = s if src is None else src
    line_indent, alone_indent, alone = _indent_of(s, vs)
    key_indent = alone_indent if alone else line_indent + indent
    close_indent = key_indent[: len(key_indent) - len(indent)] if len(key_indent) >= len(indent) else ""
    changed = False
    pieces: List[str] = []
    seen: List[str] = []
    prev = vs + 1
    for key, vstart, vend, nxt in _iter_dict_entries(s, vs, ve):
        seen.append(key)
        # seg = [键前留白/注释] + `"key":` + [键后空白 gap]  （s[prev:vstart]）
        colon = _key_colon(s, prev, vstart)
        gap = s[colon + 1:vstart]
        head = src[prev:colon + 1] + src[colon + 1:vstart]
        if key in new_val:
            sub, ch = _merge_into(s, vstart, vend, new_val[key],
                                  indent, "%s.%s" % (path, key), src)
            changed = changed or ch
            pieces.append(head + sub)
        else:
            pieces.append(head + src[vstart:vend])
        prev = vend
    # ⚠️ ve 是 `_value_end` 的返回值＝**闭合符之后**一位 ⇒ 尾部切片必须
    #    去掉最后一个字符，否则会把 `}` 也带进来（实测输出多出一个 `}`）。
    tail_lead = src[prev:ve - 1]      # 末键值之后的留白/注释，原样保留
    missing = [k for k in new_val if k not in seen]
    if not missing:
        return "{" + "".join(pieces) + tail_lead + "}", changed
    body = (",\n" + key_indent).join(
        "%s: %s" % (json.dumps(k, ensure_ascii=False),
                    render_inline(new_val[k], indent, key_indent))
        for k in missing
    )
    if pieces:
        return ("{" + "".join(pieces) + tail_lead + ",\n" + key_indent + body
                + "\n" + close_indent + "}"), True
    return "{\n" + key_indent + body + "\n" + close_indent + "}", True


def _key_colon(s: str, seg_start: int, seg_end: int) -> int:
    """找 seg 区间内「键名后的那个冒号」偏移。

    ⚠️ ⛔ 不能用 `s.index(":", seg_start)`：注释里可能有冒号
    （`// 时间: 12:00`），会命中错位置。必须**跳过注释与字符串**再找。
    """
    i = seg_start
    while i < seg_end:
        c = s[i]
        if c == '"':
            i = _scan_string(s, i)
            continue
        if c == "/" and i + 1 < seg_end and s[i + 1] == "/":
            j = s.find("\n", i)
            i = seg_end if j < 0 else min(j + 1, seg_end)
            continue
        if c == "/" and i + 1 < seg_end and s[i + 1] == "*":
            j = s.find("*/", i + 2)
            i = seg_end if j < 0 else min(j + 2, seg_end)
            continue
        if c == ":":
            return i
        i += 1
    raise MergeError("键名后未找到 `:`（偏移错位？）·⛔ 中止")


def _merge_list(s: str, vs: int, ve: int, new_val: List[Any],
                indent: str, path: str, src: Optional[str] = None) -> Tuple[str, bool]:
    """只追加缺项；已有项逐字节保留（含其内部注释）。"""
    src = s if src is None else src
    line_indent, alone_indent, alone = _indent_of(s, vs)
    item_indent = (alone_indent if alone else line_indent + indent) + indent
    close_indent = alone_indent if alone else line_indent
    items = list(_iter_list_items(s, vs, ve))
    have = set()
    for st, en, _nxt in items:
        try:
            have.add(json.dumps(json.loads(s[st:en]), ensure_ascii=False, sort_keys=True))
        except ValueError:
            pass
    missing = [v for v in new_val
               if json.dumps(v, ensure_ascii=False, sort_keys=True) not in have]
    if not missing:
        return src[vs:ve], False
    add = ",\n" + ",\n".join(item_indent + render_inline(v, indent, item_indent)
                            for v in missing)
    if not items:
        return "[\n" + add.lstrip(",\n") + "\n" + close_indent + "]", True
    # 末项之后到闭合符之间（含留白/注释）原样保留；新项插在它**之前**
    last_nxt = items[-1][2]
    tail = src[last_nxt:ve - 1]        # 末项后的留白/注释（不含 `]`）
    head = src[_skip_ws(s, vs):last_nxt].rstrip()
    return head + add + tail + "\n" + close_indent + "]", True


# ── 顶层入口 ─────────────────────────────────────────────────────────

def merge_key(path: str, key: str, new_value: Any, *, dry: bool = False) -> Result:
    """把 `path` 的顶层 `key` 与 `new_value` 做**增量合并**（确保存在，不覆盖）。"""
    if not os.path.isfile(path):
        if dry:
            return Result(True, "created", "[dry-run] 将新建")
        d = os.path.dirname(os.path.abspath(path)) or "."
        os.makedirs(d, exist_ok=True)
        _atomic_write(path, json.dumps({key: new_value}, ensure_ascii=False, indent=2) + "\n")
        return Result(True, "created", "新建 %s" % os.path.basename(path))

    raw = open(path, "r", encoding="utf-8").read()
    s = strip_jsonc(raw)
    # ⚠️ **合法性硬校验**：必须先确认整个文件是合法 JSON，才允许动手。
    #    实证 J7：非法 JSON 因「不以 } 结尾」而绕过了原本的检查 ⇒ 落到
    #    「追加键」分支 ⇒ `rfind("}")`=-1 ⇒ **TypeError 而非清晰的 MergeError**
    #    ⇒ 报错完全指错方向，维护者会去查错地方。
    try:
        json.loads(s)
    except ValueError as e:
        raise MergeError(
            "%s 不是合法 JSON/JSONC（%s）·⛔ 中止：宁可停下，"
            "也不替用户改他改不动的文件" % (os.path.basename(path), e)
        )
    indent = infer_indent(s)
    span = find_key_span(s, 0, len(s), key)

    if span is None:                                   # 顶层无此键 ⇒ 追加
        close = s.rstrip().rfind("}")
        m = re.search(r'\n([ \t]+)"', s)
        key_indent = m.group(1) if m else indent
        entry = "%s: %s" % (json.dumps(key, ensure_ascii=False),
                            render_inline(new_value, indent))
        has_keys = '"' in s
        joiner = ",\n" if has_keys else "\n"
        new_text = s[:close].rstrip() + joiner + key_indent + entry + "\n}\n"
        if dry:
            return Result(True, "merged", "[dry-run] 将追加顶层键 %s" % key)
        _backup(path)
        _atomic_write(path, new_text)
        return Result(True, "merged", "已追加顶层键 %s（其余逐字节保留）" % key)

    vs, ve = span
    merged, changed = _merge_into(s, vs, ve, new_value, indent, key, raw)
    if not changed:
        return Result(False, "unchanged", "已是目标态·未写盘（幂等）")
    new_text = raw[:vs] + merged + raw[ve:]
    if new_text == raw:
        return Result(False, "unchanged", "合并后与原文件一致·未写盘")
    if dry:
        return Result(True, "merged", "[dry-run] 将合并键 %s" % key)
    _backup(path)
    _atomic_write(path, new_text)
    return Result(True, "merged", "已增量合并键 %s（其余逐字节保留）" % key)


def _backup(path: str) -> str:
    dst = "%s.bak-%s" % (path, _ts())
    try:
        shutil.copy2(path, dst)
    except Exception as exc:
        raise MergeError("备份失败·拒绝写入：%s（%r）" % (dst, exc))
    if os.path.getsize(dst) <= 0:
        raise MergeError("备份产物零字节·拒绝写入：%s" % dst)
    return dst


def _atomic_write(path: str, text: str) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
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


def _main(argv: List[str]) -> int:
    if len(argv) >= 3 and argv[1] in ("show", "keys"):
        p = argv[2]
        if not os.path.isfile(p):
            print("（文件不存在）")
            return 0
        s = strip_jsonc(open(p, encoding="utf-8").read())
        data = json.loads(s)
        if argv[1] == "keys":
            print("顶层键：" + ", ".join(data.keys()))
            return 0
        for k in argv[3:]:
            data = data.get(k, {}) if isinstance(data, dict) else {}
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))