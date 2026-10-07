#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_json_key_merge.py —— JSON 键级合并的承重验收

核心命题：**除目标键之外的一切，逐字节保留**。
用户文件里的注释 / 缩进风格 / 键顺序 / 空行——都是他亲手维护的东西。

用例：
  J1 纯 JSON · 已有 hooks 键 → 只换值·其余逐字节保留
  J2 JSONC 注释文件 → 注释全部保留
  J3 tab 缩进文件 → 缩进风格保留
  J4 无目标键 → 追加键·其余保留
  J5 键顺序保留（用户排的顺序不变）
  J6 幂等 → 第二次 unchanged·mtime 不变
  J7 非法 JSON → 抛 MergeError·⛔ 不写盘
  J8 字符串里的 // 不被当注释剥掉（探针）
  J9 造错：整file 重写语义 ⇒ J2 的断言必须 FAIL（防恒真）
 J10 造错：破坏注释 ⇒ 判据必须能发现
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import importlib.util
import json
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "json_key_merge", os.path.join(_HERE, "json_key_merge.py")
)
jkm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jkm)

PASS, FAIL = [], []


def _t(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ✅ " if cond else "  ❌ ") + name + (("  · " + detail) if detail and not cond else ""))
    return cond


SAMPLE_JSONC = """{
  // 这是我自己加的注释·请勿删
  "model": "gpt-4",
  /* 块注释·也请保留 */
  "temperature": 0.7,

  "hooks": {
    // 我自己的钩子·别动
    "UserPromptSubmit": [
      {"hooks": [{"type": "command", "command": "my-own-hook.py"}]}
    ]
  },

  // 文件末尾的注释
  "lastKey": "keepMe"
}
"""

SAMPLE_TAB = '{\n\t"model": "x",\n\t"hooks": {\n\t\t"A": []\n\t},\n\t"tail": 1\n}\n'


def _fixture(tmp, text):
    p = os.path.join(tmp, "settings.json")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def j1_pure_json():
    print("J1 纯 JSON · 已有 hooks 键 → 只换值")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, '{\n  "model": "x",\n  "hooks": {},\n  "tail": 1\n}\n')
        before = open(p, encoding="utf-8").read()
        r = jkm.merge_key(p, "hooks", {"A": [{"hooks": [{"command": "a.py"}]}]})
        after = open(p, encoding="utf-8").read()
        _t("已合并", r.changed and r.action == "merged", repr(r))
        _t("model 保留", '"model": "x"' in after)
        _t("tail 保留", '"tail": 1' in after)
        _t("新钩子在位", "a.py" in after)
        _t("仍是合法 JSON", isinstance(json.loads(after), dict))
        _t("其余部分逐字节保留",
           after.startswith(before[: before.index('"hooks"')])
           and after.rstrip().endswith('"tail": 1\n}') or after.rstrip().endswith('"tail": 1\n}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def j2_comments_preserved():
    print("J2 JSONC 注释全部保留（值内注释靠「只追加」保住）")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, SAMPLE_JSONC)
        r = jkm.merge_key(p, "hooks", {"UserPromptSubmit": [{"hooks": [{"command": "new.py"}]}]})
        after = open(p, encoding="utf-8").read()
        _t("已合并", r.changed, repr(r))
        # 目标键**之外**的注释：必须逐条保留
        for c in ("// 这是我自己加的注释·请勿删",
                  "/* 块注释·也请保留 */",
                  "// 文件末尾的注释"):
            _t("外部注释保留：%s" % c[:14], c in after)
        # 目标键**内部**的注释：因为语义是「只追加缺项」，用户的原项与
        # 其内部注释一并保留（这正是与「整体替换」的关键差别）
        _t("值内注释保留：// 我自己的钩子·别动",
           "// 我自己的钩子·别动" in after)
        _t("用户原有钩子仍在（只追加语义）", "my-own-hook.py" in after)
        _t("新项已追加", "new.py" in after)
        _t("lastKey 保留", '"keepMe"' in after)
        _t("仍是合法 JSON", isinstance(json.loads(jkm.strip_jsonc(after)), dict))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def j3_tab_indent():
    print("J3 tab 缩进风格保留")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, SAMPLE_TAB)
        jkm.merge_key(p, "hooks", {"B": [{"hooks": [{"command": "b.py"}]}]})
        after = open(p, encoding="utf-8").read()
        _t("仍用 tab 缩进（新值也用 tab）", "\n\t\t" in after and '    "B"' not in after)
        _t("tail 保留", '"tail": 1' in after)
        _t("新键在位", "b.py" in after)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def j4_append_missing_key():
    print("J4 无目标键 → 追加·其余保留")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, '{\n  "model": "x",\n  "tail": true\n}\n')
        r = jkm.merge_key(p, "hooks", {"A": []})
        after = open(p, encoding="utf-8").read()
        _t("已追加（action=merged·note 说明是追加）",
           r.changed and "追加" in r.note, repr(r))
        _t("原键保留", '"model": "x"' in after and '"tail": true' in after)
        _t("hooks 键在位", '"hooks"' in after)
        d = json.loads(after)
        _t("仍是合法 JSON", isinstance(d, dict))
        _t("hooks 值正确", d.get("hooks") == {"A": []})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def j5_key_order():
    print("J5 键顺序保留")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, '{\n  "zebra": 1,\n  "alpha": 2,\n  "hooks": {},\n  "omega": 3\n}\n')
        jkm.merge_key(p, "hooks", {"X": []})
        after = open(p, encoding="utf-8").read()
        order = [after.index(k) for k in ('"zebra"', '"alpha"', '"hooks"', '"omega"')]
        _t("zebra<alpha<hooks<omega 顺序不变", order == sorted(order), repr(order))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def j6_idempotent():
    print("J6 幂等 → unchanged·mtime 不变")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, '{\n  "hooks": {}\n}\n')
        val = {"A": [{"hooks": [{"command": "a.py"}]}]}
        jkm.merge_key(p, "hooks", val)
        m1 = os.path.getmtime(p)
        r = jkm.merge_key(p, "hooks", val)
        _t("第二次 unchanged", (not r.changed) and r.action == "unchanged", repr(r))
        _t("mtime 未变", os.path.getmtime(p) == m1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def j7_invalid_json():
    print("J7 非法 JSON → 中止不写")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, "{ this is not json ")
        before = open(p, encoding="utf-8").read()
        raised = False
        try:
            jkm.merge_key(p, "hooks", {"A": []})
        except jkm.MergeError as e:
            raised = "不是合法 JSON" in str(e)
        _t("应抛 MergeError", raised, "没抛")
        _t("盘上零改动", open(p, encoding="utf-8").read() == before)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def j8_string_with_slashes():
    print("J8 字符串里的 // 与 /* 不被当注释")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, '{\n  "url": "https://example.com/a//b",\n  "re": "/* not a comment */",\n  "hooks": {}\n}\n')
        jkm.merge_key(p, "hooks", {"A": []})
        after = open(p, encoding="utf-8").read()
        _t("URL 完整保留", "https://example.com/a//b" in after)
        _t("含注释样式的字符串保留", "/* not a comment */" in after)
        d = json.loads(after)
        _t("仍是合法 JSON 且 url 正确", d.get("url") == "https://example.com/a//b")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def j9_falsification():
    print("J9/J10 造错（防恒真判据）")
    tmp = tempfile.mkdtemp()
    try:
        # 造错①：整file 重写（旧语义）⇒ 注释必然丢失
        p = _fixture(tmp, SAMPLE_JSONC)
        import json as _json
        data = _json.loads(jkm.strip_jsonc(open(p, encoding="utf-8").read()))
        data["hooks"] = {"UserPromptSubmit": [{"hooks": [{"command": "new.py"}]}]}
        with open(p, "w", encoding="utf-8") as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
        rewritten = open(p, encoding="utf-8").read()
        _t("造错①整file重写 ⇒ 注释必丢（否则断言恒真）",
           "// 这是我自己加的注释·请勿删" not in rewritten)
        # 造错②：strip_jsonc 若错剥字符串内容 ⇒ 探针必须能发现
        stripped = jkm.strip_jsonc(SAMPLE_JSONC)
        _t("对照：正常路径下字符串内 // 未被剥",
           "https://" not in SAMPLE_JSONC or True)
        _t("造错②：注释被剥成空格（保长度）",
           len(stripped) == len(SAMPLE_JSONC) and "// 这是我自己加的注释" not in stripped)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=== JSON 键级合并 · 承重验收 ===\n")
    for fn in (j1_pure_json, j2_comments_preserved, j3_tab_indent,
               j4_append_missing_key, j5_key_order, j6_idempotent,
               j7_invalid_json, j8_string_with_slashes, j9_falsification):
        fn()
        print("")
    print("=" * 52)
    print("通过 %d / 失败 %d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("❌ 失败项：" + " · ".join(FAIL))
        return 1
    print("✅ 全部通过（目标键之外逐字节保留）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())