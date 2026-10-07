#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""path_overlay.py —— 作者态常量覆盖层（发布包脱敏的统一机制）

## 病灶（实测·不是推测）

`platform_adaptation_check.py` / `content-gate.py` 等把**作者态落点**写成
**模块级常量**：

```python
AUTOCLAW_PATROL = os.path.expanduser("~/脚本中心/route_autoclaw_patrol.sh")
DSH_PLUGIN      = os.path.expanduser("~/脚本中心/five-layer-memory/src/index.js")
SSOT            = os.path.expanduser("~/记忆蓝图/…/04-跨端接入指南.md")
```

拷进包 ⇒ 这些常量在**任何用户机器上都是错的**，且因为是"看起来正常的绝对路径"，
**不报错、不空转警告、只是永远指向不存在的地方**——比抛异常更难查。

## 为什么不用「逐个改 933 行」

| 方案 | 代价 | 失败模式 |
|:---|:---|:---|
| 逐个改源 | 933 行 × 数十处·每次同步都要重做 | 与作者侧真源漂移（⛔ 双源） |
| **覆盖层（本模块）** | 装包时生成一个 `path_override.py`·源文件一行不改 | ⛔ 需保证覆盖发生在常量定义之后 |

**覆盖层选它**：作者侧继续维护**唯一真源**（933 行原样），
包侧靠一个**生成的**文件改值。**无第二份清单 ⇒ 无漂移。**

## 机制

安装器在 `<配置根>/doenglingz/` 下生成 `path_override.py`，内含：

```python
OVERRIDE = {
    "AUTOCLAW_PATROL": "/path/to/or/Skipped",   # 该端未装 ⇒ 指向不存在的哨兵路径
    "DSH_PLUGIN":      None,                     # 该能力不存在 ⇒ None（调用方须处理）
}
```

被改的脚本在**常量定义之后**调一次 `apply_override(globals())`。

⚠️ **两条硬约束**（违反任一 ⇒ 覆盖层是假的）：
1. `apply_override` 必须在**所有常量定义完毕后**调用（⛔ 不能在文件头）
2. 被覆盖成 `None` 的常量，**调用方必须能处理 None**（⛔ 否则 TypeError）
   ——所以本模块**默认不设 None**，只设"哨兵路径"（指向不存在的路径），
   让 `os.path.exists()` 自然返回 False ⇒ **原有防御逻辑原样生效**。

## 为什么默认用「哨兵路径」而不是 None

`platform_adaptation_check` 里所有这些常量后面都跟着 `os.path.exists(PATROL)` 之类的判断。
把路径换成**不存在的哨兵** ⇒ 判断照常跑、结果为"该端未接入" ⇒
**既不崩、也不恒真、还能如实报告"这一端没装"**。

这比 `None` 安全：`None` 会让 `os.path.exists(None)` 抛 TypeError。

## 用法（被改脚本侧·3 行）

```python
DEV = os.path.expanduser("~/脚本中心")     # 作者真源·⛔ 不动
# ... 其余常量 ...
try:                                                  # ← 加在这之后
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass
```

⚠️ 作者侧运行（`开发工具/` 下）时 `path_overlay` 不可达 ⇒ `ImportError` ⇒ 原样运行。
⇒ **同一个文件在作者侧和用户侧都正确**·⛔ 不需要维护两份。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import sys
from typing import Any, Dict, Mapping, MutableMapping, Optional

__version__ = "1.0.0"

# 哨兵路径：⛔ 永不存在（用不可路由的保留名·任何 OS 上都不会被创建）
SENTINEL_NAME = "__BULUOTUO_ABSENT__"


def sentinel(kind: str) -> str:
    """生成"该能力不存在"的哨兵路径。

    ⚠️ 故意构造成**不可被 mkdir 出来**的形态：文件名含 `:`（POSIX 合法但
    实践中无人这么建；Windows 非法）。⇒ `os.path.exists()` 恒 False。
    """
    return os.path.join(
        os.path.sep, "nonexistent", "%s:%s" % (SENTINEL_NAME, kind))


# 覆盖文件查找顺序（⛔ **全部与端无关**）：
#   1. $BULUOTUO_PATH_OVERRIDE  —— 显式指定（测试/多实例）
#   2. $DOENGLINGZ_CONFIG_DIR   —— 运行时配置根
#   3. **本模块同目录**          —— ⭐ 默认（文件自邻）
#
# ⛔ 不内置端家目录默认值（曾硬编码 `~/.hermes/doenglingz`——那是把"当前在做的端"
# 写进公共件，其它端装上必然读不到自己的覆盖文件，覆盖层静默失效）。
#
# ⚠️ **读写必须走同一个 `_target()`**：⛔ 否则安装器写 A 处、运行时读 B 处，
#    覆盖层"看起来在工作、其实一个值都没生效"——这是本机制最阴的死法。
ENV_OVERRIDE = "BULUOTUO_PATH_OVERRIDE"
ENV_CFG_DIR = "DOENGLINGZ_CONFIG_DIR"
OVERRIDE_NAME = "path_override.py"


def _target() -> str:
    """覆盖文件的**唯一**目标路径（读与写共用·⛔ 不许各算各的）。"""
    env = os.environ.get(ENV_OVERRIDE)
    if env:
        return os.path.expanduser(env)
    cfg = os.environ.get(ENV_CFG_DIR)
    if cfg:
        return os.path.join(os.path.expanduser(cfg), OVERRIDE_NAME)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        OVERRIDE_NAME)


def find_override_file() -> Optional[str]:
    """查找覆盖文件（⛔ 找不到返回 None——**不是错误**·作者侧常态）。"""
    p = _target()
    return p if os.path.isfile(p) else None


def load_override() -> Dict[str, Any]:
    """读覆盖表。⛔ 没有覆盖文件 ⇒ 空表（作者侧正常路径）。"""
    path = find_override_file()
    if not path:
        return {}
    ns: Dict[str, Any] = {}
    with open(path, "r", encoding="utf-8") as f:
        exec(compile(f.read(), path, "exec"), ns)   # noqa: S102 - 受控生成物
    table = ns.get("OVERRIDE") or {}
    if not isinstance(table, dict):
        raise ValueError("path_override.py 的 OVERRIDE 必须是 dict：%s" % path)
    return table


def apply_override(g: MutableMapping[str, Any],
                   strict: bool = False) -> Dict[str, Any]:
    """把覆盖值写进模块 globals。返回实际改了哪些（供自检/台账）。

    - 只改**已存在**的键（⛔ 不凭空造常量——那是打错字）
    - `strict=True` 时，键不存在 ⇒ 抛错（用于发布前自检：防常量改名后覆盖失效）
    """
    table = load_override()
    if not table:
        return {}
    changed: Dict[str, Any] = {}
    for k, v in table.items():
        if k not in g:
            if strict:
                raise KeyError(
                    "覆盖键 %r 在目标模块中不存在——常量可能已改名，"
                    "⛔ 覆盖层会静默失效（发布前必须 strict=True 自检）" % k)
            continue
        g[k] = v
        changed[k] = v
    return changed


def write_override(table: Mapping[str, Any], path: Optional[str] = None) -> str:
    """生成覆盖文件（**安装器唯一写入口**）。

    ⚠️ `path=None` 时走 `_target()`——与读路径**同一个函数**（⛔ 不许分叉）。
    """
    target = path or _target()
    os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)
    lines = [
        "# ⛔ 本文件由布洛陀安装器自动生成——⛔ 请勿手改（会被下次安装覆盖）",
        "# 作用：把作者态落点常量改成本机实况（见 path_overlay.py 文档）",
        "",
        "OVERRIDE = {",
    ]
    for k in sorted(table):
        v = table[k]
        lines.append("    %r: %r," % (k, v))
    lines += ["}", ""]
    with open(target, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return target


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="路径覆盖层")
    ap.add_argument("cmd", choices=["show", "sentinel", "selfcheck"])
    ap.add_argument("arg", nargs="?")
    a = ap.parse_args()
    if a.cmd == "sentinel":
        print(sentinel(a.arg or "X"))
        return 0
    if a.cmd == "show":
        t = load_override()
        if not t:
            print("(无覆盖文件·作者侧正常形态)")
            return 0
        for k in sorted(t):
            print("%-28s %s" % (k, t[k]))
        return 0
    # selfcheck：列出会被覆盖但目标模块里不存在的键
    p = a.arg
    if not p:
        print("用法：path_overlay.py selfcheck <目标.py>")
        return 2
    src = open(p, encoding="utf-8", errors="replace").read()
    t = load_override()
    missing = [k for k in t if ("%s =" % k) not in src and ("%s=" % k) not in src]
    if missing:
        print("❌ 覆盖键在目标模块中不存在（会静默失效）：%s" % missing)
        return 1
    print("✅ 覆盖键全部对得上（%d 个）" % len(t))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())