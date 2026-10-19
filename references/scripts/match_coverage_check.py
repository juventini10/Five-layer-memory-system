#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""匹配面完备性检查（缺尺检测·v1.2 2026-10-10·Qoder CN 童灵·R3 根治）

**它治的病**：铁律晋升时只写条文的"法条面"，不写 rule_triggers.yaml 的 match（预注入腿）
与 rule_fragment_eval.py 的语料（尺）——结果是"有法无尺"：新铁律能否被正确加载全靠
人记得，且没人知道它能不能命中（实证：2026-10-10 全量扫描 37 条铁律中 17 条无语料）。

**判据**：某铁律"有尺" = ①yaml triggers 里有对应条目（按 source_anchor 的 ### 铁律-NNN 认）
②该条目 match 非空 ③rule_fragment_eval.py CORPUS 里有该 NNN 键。三者缺一 = 缺尺。

**存量豁免 + 增量必绿**（承 antibody_gate STOCK 范式）：
    --write  生成/刷新 baseline（当前缺尺清单快照）
    --check  当前缺尺 − baseline 非空 → exit 1（新立的必须自带尺；历史欠账不阻断他人施工）
    exit 0 = 无新增缺尺；exit 1 = 有新增；exit 2 = 路径/解析不可用（fail-closed，⛔不当"没问题"）

--self-test 用临时目录造三例（正例全尺→0／反例新法无尺→1／变异补尺后→0），⛔不碰真账。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import io
import json
import os
import re
import sys

MC = os.path.expanduser("[记忆共享中心]")
DEF_RULE = os.path.join(MC, "记忆规则", "用户基本规则-铁律版.md")
DEF_YAML = os.path.join(MC, "记忆规则", "rule_triggers.yaml")
DEF_CORPUS = os.path.join(MC, "脚本中心", "记忆蒸馏", "rule_fragment_eval.py")
DEF_BASE = os.path.join(MC, "记忆规则", "match_coverage_baseline.json")

ID_RE = re.compile(r"^### 铁律-(\d{3})", re.M)
CORPUS_KEY_RE = re.compile(r'^\s{4}"(\d{3})":\s*\{', re.M)


PLACEHOLDER_RE = re.compile(r"已合并入|保留占位|编号保留|内容已合并")


def _resident_ids(yamlp):
    """恒驻条目（resident: true）＝**尺无消费者**态：评测器只跑非恒驻集
    （`eval_ids = [t for t in triggers if not t.get("resident")]`），
    给它们报"缺尺"＝假红（本器第二次因同一族缺态被真账逮出——008 本轮即为一例）。
    与占位态分开显形（两种豁免理由不同，⛔合并成一个数）。
    """
    import yaml
    try:
        d = yaml.safe_load(io.open(yamlp, encoding="utf-8"))
    except Exception:
        return set()
    out = set()
    for e in (d.get("triggers") or []):
        m = re.search(r"铁律-(\d{3})", str(e.get("source_anchor") or ""))
        if m and e.get("resident"):
            out.add(m.group(1))
    return out


def _bad_yaml_escape(s):
    """返回 s 中第一个「反斜杠 + 非 YAML 合法转义字符」的下标；无则 None。

    YAML 双引号标量里，反斜杠后只许跟固定几个字符；正则方言里常见的空格类/数字类
    都带反斜杠，直接抄进 YAML 串就是未知 escape（本会话 15:0x／15:5x 两次实炸皆此形）。
    本件一律用 chr(92) 取反斜杠字面量，⛔不再写转义形式。
    """
    BS = chr(92)
    legal = set("0adbtvnfre_" + chr(34) + chr(47) + BS + "NLPUxu")
    k = 0
    while k < len(s):
        if s[k] == BS:
            nxt = s[k + 1] if k + 1 < len(s) else ""
            if nxt not in legal:
                return k
            k += 2
        else:
            k += 1
    return None


def _bad_yaml_escape(s):
    """返回 s 中第一个「反斜杠 + 非 YAML 合法转义字符」的下标；无则 None。

    YAML 双引号标量里，反斜杠后只许跟固定几个字符；正则方言里常见的空格类/数字类
    都带反斜杠，直接抄进 YAML 串就是未知 escape（本会话 15:0x／15:5x 两次实炸皆此形）。
    本件一律用 chr(92) 取反斜杠字面量，⛔不再写转义形式。
    """
    BS = chr(92)
    legal = set("0adbtvnfre_" + chr(34) + chr(47) + BS + "NLPUxu")
    k = 0
    while k < len(s):
        if s[k] == BS:
            nxt = s[k + 1] if k + 1 < len(s) else ""
            if nxt not in legal:
                return k
            k += 2
        else:
            k += 1
    return None


def _bad_yaml_escape(s):
    """返回 s 中第一个「反斜杠 + 非 YAML 合法转义字符」的下标；无则 None。

    YAML 双引号标量里，反斜杠后只许跟固定几个字符；正则方言里常见的空格类/数字类
    都带反斜杠，直接抄进 YAML 串就是未知 escape（本会话 15:0x／15:5x 两次实炸皆此形）。
    本件一律用 chr(92) 取反斜杠字面量，⛔不再写转义形式。
    """
    BS = chr(92)
    legal = set("0adbtvnfre_" + chr(34) + chr(47) + BS + "NLPUxu")
    k = 0
    while k < len(s):
        if s[k] == BS:
            nxt = s[k + 1] if k + 1 < len(s) else ""
            if nxt not in legal:
                return k
            k += 2
        else:
            k += 1
    return None


def lint_yaml(yamlp):
    """写侧闸（v1.2·PAT-086 三连犯的机械承接）：改完 rule_triggers.yaml 立即跑。

    唯一真判据＝整份可否 safe_load：不可解析＝预注入腿失能（本会话 15:0x／15:5x 两次实炸都是这一层抓的）。
    ⛔不判「值里含不含反斜杠」：真账实测 001/029 的单引号/明文标量里反斜杠是合法正则转义，
      加了这条扫描＝给闸自己装假红（本日同族第三次，见 QCN-20261010-019）。
    位置意义大于判据复杂度：读侧的 safe_load 只在有人查时响，本闸挂在**写完那一刻**。
    """
    import yaml
    try:
        d = yaml.safe_load(io.open(yamlp, encoding="utf-8"))
    except Exception as e:
        print("🔴 写侧闸：yaml 不可解析（预注入腿失能）")
        print("   " + str(e)[:130])
        return 1
    frs = d.get("triggers") or []
    bs = sorted({str(e.get("id")) for e in frs for m in (e.get("match") or []) if chr(92) in m})
    print("✅ 写侧闸：可解析 triggers=%d（含反斜杠的条目：%s·该形态在单引号/明文标量下合法，仅提示）" % (len(frs), " ".join(bs) or "无"))
    return 0

def _placeholders(rule_text):
    """识别**占位条目**（编号保留但内容已合并/退役）——它们不该有触发器，也不该被要求有尺。

    病根（2026-10-10·本器 v1.0 上线 40 分钟即被真账逮出）：009 条文本体是「（已合并入008·v8.8）」
    的占位声明，却被算进缺尺 15 条 ⇒ 新仪器自己产了一个假红，犯的正是已晋升的 PAT-079
    「状态枚举缺零历史态/判据未随对象演化」。修尺纪律＝**判据必须覆盖对象的全部存在态**，
    占位态是态，不是"条目不存在"。真源取条文本体的占位声明，⛔靠编号猜。
    窗口划法：本条标题 → 下一条目标题（⛔定长字窗——会读入邻条正文而连上一条一起豁免）。
    """
    ph = set()
    ms = list(re.finditer(r"^### 铁律-(\d{3})[^\n]*\n", rule_text, re.M))
    for i, m in enumerate(ms):
        # 窗口止于**下一条目标题**（⛔固定 200 字窗——自测实测：固定窗会读进下一条目的正文，
        #   把上一条（008）误判成占位＝把假红改成假绿，比原病更糟）
        nxt = ms[i + 1].start() if i + 1 < len(ms) else len(rule_text)
        seg = rule_text[m.start():nxt][:400]
        if PLACEHOLDER_RE.search(seg):
            ph.add(m.group(1))
    return ph


def deficit(rule, yamlp, corp):
    """返回 (在册id集合, 缺尺id列表, 占位id集合)。yaml 解析失败 → 抛异常由调用方 fail-closed。"""
    import yaml
    rule_text = io.open(rule, encoding="utf-8").read()
    ids = sorted(set(ID_RE.findall(rule_text)))
    ph = _placeholders(rule_text)
    res = _resident_ids(yamlp)
    d = yaml.safe_load(io.open(yamlp, encoding="utf-8"))
    frs = d.get("triggers") or d.get("fragments") or []
    by_id, empty_match = {}, set()
    for e in frs:
        m = re.search(r"铁律-(\d{3})", str(e.get("source_anchor") or e.get("id") or ""))
        if not m:
            continue
        by_id[m.group(1)] = e
        if not (e.get("match") or []):
            empty_match.add(m.group(1))
    have_corpus = set(CORPUS_KEY_RE.findall(io.open(corp, encoding="utf-8").read()))
    miss = [i for i in ids if i not in ph and i not in res and (i not in by_id or i in empty_match or i not in have_corpus)]
    return ids, miss, ph | res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", default=DEF_RULE)
    ap.add_argument("--yaml", dest="yamlp", default=DEF_YAML)
    ap.add_argument("--corpus", default=DEF_CORPUS)
    ap.add_argument("--baseline", default=DEF_BASE)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--lint", action="store_true", help="写侧闸：yaml 可解析+match 无非法转义（改完 yaml 必跑）")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.lint:
        return lint_yaml(a.yamlp)
    try:
        ids, miss, ph = deficit(a.rule, a.yamlp, a.corpus)
    except Exception as e:
        print("❌ 匹配面检查不可用（fail-closed，⛔不等于通过）：%s" % str(e)[:100])
        return 2
    if a.write:
        json.dump({"generated_by": "match_coverage_check.py v1.1", "total": len(ids),
                   "deficit": miss, "placeholder_exempt": sorted(ph)},
                  io.open(a.baseline, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("✅ baseline 已写：在册 %d 条，缺尺存量 %d 条，豁免 %d 条（%s）——豁免含占位态与恒驻态" % (
            len(ids), len(miss), len(ph), " ".join(sorted(ph)) or "无"))
        return 0
    if a.check:
        base = set()
        if os.path.isfile(a.baseline):
            try:
                base = set(json.load(io.open(a.baseline, encoding="utf-8")).get("deficit", []))
            except Exception:
                base = set()
        new = [i for i in miss if i not in base]
        print("在册 %d ｜缺尺 %d（存量豁免 %d）｜新增缺尺 %d｜豁免态 %d(%s·占位+恒驻·尺无消费者或不该有尺)" % (
            len(ids), len(miss), len(miss) - len(new), len(new), len(ph), " ".join(sorted(ph)) or "无"))
        if new:
            print("🔴 新立铁律缺尺：%s → 依 01规范「匹配面三件套」补 match+语料+dry-run" % ",".join(new))
            return 1
        print("✅ 无新增缺尺（历史欠账见 baseline 快照，收敛由挂账卡推进）")
        return 0
    ap.print_help()
    return 2


def self_test():
    import tempfile
    t = tempfile.mkdtemp(prefix="mcchk-")
    rule = os.path.join(t, "rule.md")
    yamlp = os.path.join(t, "rt.yaml")
    corp = os.path.join(t, "eval.py")
    base = os.path.join(t, "base.json")

    def emit(ids_with_scale):
        io.open(rule, "w", encoding="utf-8").write(
            "".join("### 铁律-%s · 条%s\n" % (i, i) for i in ids_with_scale))
        frs = []
        for i in ids_with_scale:
            e = {"source_anchor": "### 铁律-%s" % i}
            e["match"] = [] if i == "099" else ["(%s).{0,8}(测试)" % i]
            frs.append(e)
        io.open(yamlp, "w", encoding="utf-8").write(
            "version: 1\ntriggers:\n" + "".join(
                "  - source_anchor: \"### 铁律-%s\"\n    match:%s\n" % (
                    i, " []" if i == "099" else "\n      - \"%s-test\"" % i) for i in ids_with_scale))
        io.open(corp, "w", encoding="utf-8").write(
            "CORPUS = {\n" + "".join(
                '    "%s": {\n        "pos": ["x"],\n        "neg": ["y"]\n    },\n' % i
                for i in ids_with_scale if i != "099") + "}\n")

    emit(["098", "099"])
    rc = main(["--check", "--rule", rule, "--yaml", yamlp, "--corpus", corp, "--baseline", base])
    ok1 = (rc == 1)
    print("  %s 反例：新法 099 无尺 → 必 rc=1（实得 rc=%s）" % ("✅" if ok1 else "❌", rc))
    json.dump({"deficit": ["099"]}, io.open(base, "w", encoding="utf-8"))
    rc2 = main(["--check", "--rule", rule, "--yaml", yamlp, "--corpus", corp, "--baseline", base])
    ok2 = (rc2 == 0)
    print("  %s 存量豁免：099 进 baseline → rc=0（实得 %s）" % ("✅" if ok2 else "❌", rc2))
    emit(["098", "099"])
    # ⚠️ 先 read 到变量再 open("w")——同表达式里 open(w) 会先截断，read 得到空串＝把夹具写没
    _y = io.open(yamlp, encoding="utf-8").read().replace(
        "  - source_anchor: \"### 铁律-099\"\n    match: []",
        "  - source_anchor: \"### 铁律-099\"\n    match:\n      - \"099-test\"")
    io.open(yamlp, "w", encoding="utf-8").write(_y)
    _c = io.open(corp, encoding="utf-8").read().replace(
        "}\n", '    "099": {\n        "pos": ["x"],\n        "neg": ["y"]\n    },\n}\n')
    io.open(corp, "w", encoding="utf-8").write(_c)
    ids, miss, ph = deficit(rule, yamlp, corp)
    ok3 = ("099" not in miss)
    print("  %s 变异(反向)：补齐 match+语料 → 099 脱缺尺（实得 miss=%s）" % ("✅" if ok3 else "❌", miss))
    io.open(rule, "w", encoding="utf-8").write(
        "".join("### 铁律-%s · 条%s\n" % (i, i) for i in ["098", "099"])
        .replace("### 铁律-099 · 条099", "### 铁律-099：（已合并入098·占位）\n本编号保留占位。"))
    ids_p, miss_p, ph_p = deficit(rule, yamlp, corp)
    ok5 = ("099" in ph_p and "099" not in miss_p)
    print("  %s S5 占位条目 → 豁免不计缺尺（实得 ph=%s miss=%s）" % ("✅" if ok5 else "❌", sorted(ph_p), miss_p))
    _rp = io.open(rule, encoding="utf-8").read().replace(
        "（已合并入098·占位）\n本编号保留占位。", "·实条\n本编号已启用。")
    io.open(rule, "w", encoding="utf-8").write(_rp)
    # 变异要同时撤掉"已补的语料"——否则 099 本来就不缺尺，断言会假过（首版即栽在此）
    io.open(corp, "w", encoding="utf-8").write(
        'CORPUS = {\n    "098": {\n        "pos": ["x"],\n        "neg": ["y"]\n    },\n}\n')
    _i2, miss_v, ph_v = deficit(rule, yamlp, corp)
    ok6 = (not ph_v and "099" in miss_v)
    print("  %s MUT-占位: 占位声明摘掉 → 099 必进缺尺（实得 ph=%s）" % ("✅" if ok6 else "❌", sorted(ph_v)))
    rc4 = main(["--yaml", yamlp, "--rule", "/nonexistent/rule.md", "--check", "--baseline", base])
    ok4 = (rc4 == 2)
    print("  %s fail-closed：规则文件不可读 → rc=2（不当通过·实得 %s）" % ("✅" if ok4 else "❌", rc4))
    good = ok1 and ok2 and ok3 and ok4 and ok5 and ok6
    print("自测 %d/6 %s" % (sum([ok1, ok2, ok3, ok4, ok5, ok6]), "过" if good else "未全过"))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
