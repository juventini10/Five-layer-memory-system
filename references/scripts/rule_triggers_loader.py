#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
rule_triggers_loader.py — 共享：解析 rule_triggers.yaml + rule_conflict_signals.yaml + 提取铁律版索引表 id（v0.2 泛化 key）

零依赖设计：环境无 pyyaml，故先试 import yaml，缺失则手解我们受控的简单 YAML 子集
（2 空格缩进：顶层 key / triggers 列表(level2 item) / item 内 key(level4) / match 列表(level6)）。
两个消费方（rule_fragment_inject.py / rule_three_layer_guard.py ⑥）共用本模块，单一解析逻辑。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re

HOME = os.path.expanduser("~")
RULES_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆规则")
TIELU_FILE = os.path.join(RULES_DIR, "用户基本规则-铁律版.md")
TRIGGERS_YAML = os.path.join(RULES_DIR, "rule_triggers.yaml")


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _coerce(v):
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        v = v[1:-1]
    elif v.startswith("'") and v.endswith("'"):
        v = v[1:-1]
    # YAML 双引号转义还原（子集解析器无 yaml 模块，须手动处理）。
    # 仅 `\\` -> `\` 一种：YAML 中反斜杠只此一种合法转义，安全。
    # 修复前：`"\\.json"` 被裸剥离成 `\\.json`（双反斜杠），正则误读为
    # "字面前导反斜杠+任意字符"，导致 001 扩展名模式永远漏命中。
    v = v.replace("\\\\", "\\")
    if v == "true":
        return True
    if v == "false":
        return False
    return v


def _parse_subset(text, key="triggers"):
    """手解受控 YAML 子集 → {"version":.., "source":.., "triggers":[ {...}, ... ]}。

    结构约定（本文件作者控制，勿超此形状）：
        version: 1
        source: "..."
        triggers:
          - id: "001"
            name: ...
            resident: false
            source_file: ...
            source_anchor: "..."
            match:
              - "p1"
              - "p2"
    """
    data = {"version": None, "source": None, key: []}
    triggers = data[key]
    cur = None          # 当前 item dict
    in_match = False    # 是否处于某 item 的 match 列表内
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            in_match = False
            if line == key + ":":
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = _coerce(v)
            continue
        if indent == 2 and line.startswith("- "):
            in_match = False
            cur = {}
            triggers.append(cur)
            rest = line[2:].strip()
            if ":" in rest:
                k, v = rest.split(":", 1)
                cur[k.strip()] = _coerce(v)
            continue
        if indent == 4 and cur is not None:
            if line.startswith("match:"):
                in_match = True
                cur["match"] = []
                rest = line[len("match:"):].strip()
                if rest and rest != "[]":  # 同行内联（本文件不用，但容错）；"[]"=空列表
                    cur["match"].append(_coerce(rest))
                continue
            in_match = False
            if ":" in line:
                k, v = line.split(":", 1)
                cur[k.strip()] = _coerce(v)
            continue
        if indent == 6 and in_match and line.startswith("- "):
            cur["match"].append(_coerce(line[2:]))
            continue
    return data


def load_triggers(path=TRIGGERS_YAML):
    """返回 triggers 列表（list[dict]）。优先 pyyaml，缺失走子集解析。"""
    text = _read(path)
    try:
        import yaml  # 环境若无则 ImportError → 子集解析
        return yaml.safe_load(text).get("triggers", [])
    except ImportError:
        return _parse_subset(text).get("triggers", [])


CONFLICT_SIGNALS_YAML = os.path.join(RULES_DIR, "rule_conflict_signals.yaml")


def load_conflict_signals(path=CONFLICT_SIGNALS_YAML):
    """返回冲突/边缘信号列表（list[dict]·v0.2 新增）。

    真源=rule_conflict_signals.yaml（独立于 rule_triggers.yaml——后者受 guard⑥ 22==22 校验辖区）。
    文件缺失/解析失败返回 []（调用方 fallback 内置默认组）。
    """
    text = _read(path)
    try:
        import yaml  # 环境若无则 ImportError → 子集解析
        return yaml.safe_load(text).get("signals", [])
    except ImportError:
        return _parse_subset(text, key="signals").get("signals", [])


def extract_tielu_index_ids(tielu_text):
    """从铁律版「加载时机索引表」提取编号集合（001-019）。

    索引表行形如：| 001 | 先看清，再动手 | ... |
    仅取该表内（标题『加载时机索引表』之后、『AI执行铁律』之前）的 | NNN | 行。
    """
    start = tielu_text.find("加载时机索引表")
    end = tielu_text.find("AI执行铁律", start)
    if start < 0 or end < 0:
        # 退化：全文件扫
        seg = tielu_text
    else:
        seg = tielu_text[start:end]
    ids = re.findall(r"^\|\s*(\d{3})\s*\|", seg, re.M)
    return sorted(set(ids))


def extract_tielu_section(tielu_text, anchor):
    """提取铁律版中 anchor 小节正文（到下一个 ### 或 ## 或 EOF 为止）。"""
    idx = tielu_text.find(anchor)
    if idx < 0:
        return None
    rest = tielu_text[idx:]
    m = re.search(r"\n### |\n## ", rest[1:])
    if m:
        return rest[:m.start() + 1].strip()
    return rest.strip()


if __name__ == "__main__":
    ts = load_triggers()
    print(f"triggers 解析条数: {len(ts)}")
    for t in ts:
        print(f"  {t.get('id')} resident={t.get('resident')} match={len(t.get('match') or [])} "
              f"anchor={t.get('source_anchor')}")
    ids = extract_tielu_index_ids(_read(TIELU_FILE))
    print(f"铁律版索引表 id 集合: {ids}")
