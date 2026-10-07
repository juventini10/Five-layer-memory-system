#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mount_plugins.py —— 把已部署的插件挂进端配置的 `plugins.enabled`

## 为什么单独一个文件（⛔ 不在 shell 里硬拼 YAML）

`config.yaml` 的 `plugins.enabled` 是**带注释的块列表**：

```yaml
plugins:
  enabled:
    - route-audit-hook
    # 童灵（Doenglingz）数字分身接入 · 端自主适配 v1.0.0（2026-10-01）
    - doenglingz-twin
```

⇒ 任何"读出来→改→序列化回去"的做法都会**吞掉注释、重排键、改缩进**
（台账 §4.7「回滚/改配置的完整性判据是逐字节」）。
⇒ 本脚本**只做文本插入**：定位 `enabled:` 块，把缺失项**追加到块尾**，
   **已有内容一个字节不动**。

## 三条硬约束

1. **只增不删**：⛔ 不移除用户已启用但包里没有的插件（那是用户主权）
2. **幂等**：已在列表里的不重复加
3. **写前备份 + 原子写**（铁律005）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import os
import re
import shutil
import sys

# `plugins:` → `  enabled:` → 缩进的 `- name` 列表，直到 dedent 或新顶级键
PLUG_BLOCK = re.compile(
    r"^(?P<indent>[ \t]*)plugins[ \t]*:[ \t]*\n"
    r"(?P<body>(?:(?:[ \t]+[^\n]*)?\n)*)", re.M)
ENABLED = re.compile(r"^(?P<ei>[ \t]+)enabled[ \t]*:[ \t]*(?P<inline>\[[^\]]*\])?[ \t]*$",
                     re.M)
ITEM = re.compile(r"^[ \t]*-[ \t]+(?P<name>[\w.\-]+)[ \t]*$")


def find_enabled_lines(lines):
    """返回 (enabled 行的 idx, 条目行的 idx 列表, 缩进)。找不到返 (None, [], "")。"""
    for i, ln in enumerate(lines):
        m = ENABLED.match(ln)
        if not m:
            continue
        # 必须落在 `plugins:` 块内（⛔ 不碰其它键下的 enabled）
        prev = "\n".join(lines[max(0, i - 6):i])
        if not re.search(r"^plugins[ \t]*:", prev, re.M):
            continue
        ei = len(m.group("ei"))
        items = []
        for j in range(i + 1, len(lines)):
            ln2 = lines[j]
            if ln2.strip() and not ln2.startswith(" " * (ei + 1)) \
                    and not ln2.startswith("\t"):
                break                       # dedent ⇒ 块结束
            im = ITEM.match(ln2)
            if im:
                items.append((j, im.group("name")))
            elif ln2.strip() and not ln2.strip().startswith("#"):
                # 块内有非条目非注释内容（如嵌套键）⇒ 保守停手
                if not ln2.startswith(" " * (ei + 1)):
                    break
        # ⚠️ 条目缩进**从已有条目取**，⛔ 不从 `enabled:` 键推。
        #    `  enabled:` 是 2 空格而条目是 4 空格——按键推会插成 2 空格
        #    ⇒ YAML 层级错 ⇒ `safe_load` 直接抛 "expected <block end>"。
        if items:
            m2 = re.match(r"^([ \t]+)-", lines[items[0][0]])
            ind = m2.group(1) if m2 else " " * (ei + 2)
        else:
            ind = " " * (ei + 2)
        return i, items, ind
    return None, [], ""


def mount(cfg_path: str, names, dry=False):
    if not os.path.isfile(cfg_path):
        raise SystemExit("❌ 配置不存在：%s" % cfg_path)
    src = open(cfg_path, encoding="utf-8").read()
    lines = src.split("\n")
    idx, items, indent = find_enabled_lines(lines)
    if idx is None:
        print("❌ 未找到 plugins.enabled（⛔ 不猜结构·请先确认端配置格式）")
        return 2
    have = {n for _i, n in items}
    missing = [n for n in names if n not in have]
    print("当前已启用 %d 个 · 本包 %d 个 · 缺 %d 个"
          % (len(have), len(names), len(missing)))
    if not missing:
        print("✅ 全部已挂载（幂等·未改任何字节）")
        return 0
    if dry:
        print("[dry] 将追加：%s" % ", ".join(missing))
        return 0
    # 插到块末（enabled 最后一个条目之后）
    insert_at = items[-1][0] + 1 if items else idx + 1
    new = lines[:insert_at] + ["%s- %s" % (indent, n) for n in missing] \
        + lines[insert_at:]
    out = "\n".join(new)
    # 写前备份（铁律005）
    shutil.copy2(cfg_path, cfg_path + ".bak-premount")
    tmp = cfg_path + ".tmp"
    open(tmp, "w", encoding="utf-8").write(out)
    os.replace(tmp, cfg_path)
    print("✅ 已追加 %d 个：%s" % (len(missing), ", ".join(missing)))
    print("   备份：%s.bak-premount" % os.path.basename(cfg_path))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--plugins-dir", required=True,
                    help="已部署插件目录（扫其中的 plugin.yaml 取名）")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    names = sorted(
        d for d in os.listdir(a.plugins_dir)
        if os.path.isfile(os.path.join(a.plugins_dir, d, "plugin.yaml")))
    if not names:
        print("❌ %s 下无 plugin.yaml——⛔ 不挂空" % a.plugins_dir)
        return 2
    return mount(a.config, names, a.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())