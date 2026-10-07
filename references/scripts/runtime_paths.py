#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runtime_paths.py —— 运行路径解析器（插件/脚本的唯一取路径入口）

## 它解决什么

16 个 Hermes 插件各自硬编码 `[记忆共享中心]/脚本中心` 这类**作者侧目录**
（实测 16/16 插件都写了「个人AI档案」）。包若照抄 ⇒ 其他用户装完
16 个插件**全是静默 fail-open**：不报错、不注入、看起来"装好了"。

正解＝**路径声明 + 单一解析入口**：
- 安装器把本机的真实落点写进 `<配置根>/doenglingz/runtime_paths.json`
- 插件/脚本只调 `rp("devtools")` 取路径，⛔ 不再自己拼目录名
- 键缺 ⇒ **抛 `PathKeyMissing`**（⛔ 不静默回落 `/tmp` 或作者目录）
  ——因为「静默回落」正是恒真判据的制造机。

## 语义键（⛔ 不按目录名·按职责）

| 键 | 职责 | 本机对应 |
|:--|:---|:---|
| `archive_root` | 档案根（所有子目录的父） | `~/个人AI档案` |
| `devtools` | 开发工具脚本面 | `开发工具/` |
| `worklog` | 工作日志 | `工作日志/` |
| `twin` | 数字分身 | `数字分身/` |
| `blueprint` | 记忆蓝图 | `记忆蓝图/` |
| `skills` | 技能配置（真源） | `技能配置/` |
| `kb_engine` | 知识联邦引擎 | `开发工具/知识联邦引擎/` |
| `knowledge` | 知识库 | `知识库/` |
| `k2_slices` | K2 切片 | `数字分身/K2切片蒸馏/` |
| `custom_route` | 路由家族 | `自定义层/路由家族/` |
| `twin_slices` | 分身切片（插件读人格切片） | `数字分身/K2切片蒸馏/slices/` |
| `twin_spec` | 分身规格书 | `数字分身/童灵·人格规格书.md` |

⚠️ **键名故意与目录名解耦**：用户的记忆中心可能叫任何名字；
键表达的是**职责**，落点由安装器填。

## 用法

```python
from runtime_paths import rp, PathKeyMissing, load

rp("devtools")                 # → 绝对路径字符串
rp("devtools", "guard.py")     # → 拼子文件
rp("kb_engine", optional=True) # → 缺键返回 None（⛔ 仅限显式声明可选项）
```

## 为什么缺键要抛错而不是回落

回落会让"路径不对"变成"脚本空转"——而空转**不报错**（守卫的 fail-open 天性）。
抛错让安装/首次运行立刻显形。**这是把静默失效变成可见失败。**
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import sys
from typing import Any, Dict, List, Optional

__version__ = "1.0.0"

for _s in (sys.stdout, sys.stderr):
    _r = getattr(_s, "reconfigure", None)
    if callable(_r):
        try:
            _r(encoding="utf-8")
        except Exception:  # pragma: no cover
            pass


class PathKeyMissing(KeyError):
    """声明里没有这个键。

    ⛔ **故意继承 KeyError**：调用方若写了 `except KeyError` 会一并捕获，
    但本类额外带 `key` / `hint` 属性，便于上层输出可操作的信息。
    """

    def __init__(self, key: str, available: List[str], path_file: str = ""):
        self.key = key
        self.available = available
        self.path_file = path_file
        super().__init__(
            "运行路径声明缺键 %r（声明文件：%s）·可用键：%s\n"
            "  ⇒ 这是**安装不完整**或**该键未声明**，⛔ 不静默回落。"
            % (key, path_file or "<未找到声明文件>", ", ".join(sorted(available)) or "（空）")
        )


class DeclNotFound(RuntimeError):
    """runtime_paths.json 不存在——安装没跑，或跑在别的机器上。"""


# 查找顺序（⛔ **全部与端无关**）：
#   1. $BULUOTUO_RUNTIME_PATHS   —— 安装器/测试显式指定
#   2. $DOENGLINGZ_CONFIG_DIR    —— 运行时配置根（插件可设）
#   3. **本模块同目录的 runtime_paths.json** —— ⭐ 默认
#
# ⛔ **不内置任何端家目录默认值**（曾硬编码 `~/.hermes/doenglingz` ——
# 那是把"当前在做的端"写进公共件，其它端装上必然指错地方）。
# 改为**文件自邻**：安装器把解析器与声明放在同一目录，"解析器在哪 ⇒ 声明在哪"，
# 于是"哪个端"这个问题**根本不需要在这里回答**（端中立）。
ENV_PATHS_FILE = "BULUOTUO_RUNTIME_PATHS"
ENV_CFG_DIR = "DOENGLINGZ_CONFIG_DIR"
ENV_PREFIX = "BULUOTUO_PATH_"
DECL_NAME = "runtime_paths.json"

_CACHE: Optional[Dict[str, str]] = None


def _default_file() -> str:
    if os.environ.get(ENV_PATHS_FILE):
        return os.path.expanduser(os.environ[ENV_PATHS_FILE])
    cfg = os.environ.get(ENV_CFG_DIR)
    if cfg:
        return os.path.join(os.path.expanduser(cfg), DECL_NAME)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DECL_NAME)


def load(force: bool = False) -> Dict[str, str]:
    """读并缓存声明。⛔ 文件不存在 ⇒ 抛 DeclNotFound（⛔ 不返回空 dict）。"""
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE
    path = _default_file()
    if not os.path.isfile(path):
        raise DeclNotFound(
            "未找到运行路径声明：%s\n"
            "  ⇒ 请先运行安装器（它会生成本文件），⛔ 不回落默认值——"
            "回落会让所有脚本静默空转。" % path
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise DeclNotFound("声明文件格式错（应为 JSON 对象）：%s" % path)
    # env 覆盖（BULUOTUO_PATH_<KEY>）——测试缝/多实例用
    for k in list(data.keys()):
        envk = ENV_PREFIX + k.upper()
        if os.environ.get(envk):
            data[k] = os.path.expanduser(os.environ[envk])
    _CACHE = data
    return data


def reset_cache() -> None:
    """清缓存（安装器改写声明后必须调，否则改动不生效）。"""
    global _CACHE
    _CACHE = None


def rp(key: str, *parts: str, optional: bool = False) -> Optional[str]:
    """取路径。`rp("devtools")` → 目录；`rp("devtools","x.py")` → 拼子文件。

    ⛔ 键缺 ⇒ 抛 `PathKeyMissing`（`optional=True` 时返回 None，
    但**调用方必须显式处理 None**，⛔ 不许当空串用）。
    """
    data = load()
    if key not in data:
        if optional:
            return None
        raise PathKeyMissing(key, list(data.keys()), _default_file())
    base = data[key]
    for p in parts:
        base = os.path.join(base, p)
    return base


def has(key: str) -> bool:
    """该键是否已声明（⛔ 不抛错——用于能力探测）。"""
    try:
        return key in load()
    except DeclNotFound:
        return False


def write(paths: Dict[str, str], path: Optional[str] = None, force: bool = False) -> str:
    """写声明文件（**安装器唯一写入口**）。

    -逐键校验绝对路径（⛔ 相对路径会让 cwd 变成隐式依赖）
    - 原子写 + 已有文件先备份（铁律005）
    - 写完 `reset_cache()`（⛔ 否则同进程读到旧缓存）
    """
    target = path or _default_file()
    bad = [k for k, v in paths.items() if not os.path.isabs(os.path.expanduser(v))]
    if bad:
        raise ValueError("路径必须是绝对路径：%s" % ", ".join(sorted(bad)))
    payload = {k: os.path.expanduser(v) for k, v in paths.items()}
    os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)
    if os.path.isfile(target):
        try:
            import shutil
            shutil.copy2(target, target + ".bak")
        except Exception:
            pass
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, target)
    reset_cache()
    return target


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="运行路径声明 读写")
    ap.add_argument("cmd", choices=["show", "keys", "get"])
    ap.add_argument("arg", nargs="?")
    a = ap.parse_args()
    try:
        if a.cmd == "keys":
            for k in sorted(load()):
                print("%-16s %s" % (k, load()[k]))
            return 0
        if a.cmd == "get":
            print(rp(a.arg))
            return 0
        print(json.dumps(load(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (DeclNotFound, PathKeyMissing) as e:
        print("❌ %s" % e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())