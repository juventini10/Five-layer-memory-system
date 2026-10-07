#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# version: v1.0.0
"""ZCode 端 Skill 生态健康度守卫（端薄适配器·判据 import 公共原语 skill_health_common）。
## 存在理由（T0 方案 B3·G0 裁决「接」·吸收 WB v1.0.0 先例协议）
族内四端各有 skill_health_guard·ZCode 缺席而 40+ Skill 生态=当日操作面（S813 断链=操作面死）。
## 与 symlink_guard 的边界（§二·十二 防重复观测·裁定）
symlink_guard=跨端 ENDS 清单断链面（已岗·ENDS 含 ~/.zcode/skills）；本件=本端生态深度面：
断链逐 skill 深查（他端资产端隔离）+ SKILL.md/frontmatter 完整性 + **重名遮蔽**（.zcode 胜 .agents 的
发现序遮蔽·官方 configuration-guide 判据）——两镜互补· ⛔语义不复制 symlink_guard。
## ZCode 形态差异（对齐 WB 差异声明）
~/.zcode/skills 允许实目录（ZCode 无「消费面必须软链」铁律）⇒ 实目录不判红只统计。
检测项：1 断链 RED / 2 SKILL.md 缺 WARN / 3 frontmatter 缺 name WARN / 4 重名遮蔽 WARN（.agents 同名被 .zcode 遮蔽）。
挂载：Stop 报告制·恒 exit 0（--strict 有 RED 才 1）。
"""
import sys, os, json, ast, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from skill_health_common import classify, fm_name, new_report, add, finalize  # noqa: E402

VERSION = "v1.0.0"
HOME = os.path.expanduser("~")
ZSKILLS_DEFAULT = os.path.join(HOME, ".zcode", "skills")
ASKILLS_DEFAULT = os.path.join(HOME, ".agents", "skills")


def _zskills():
    """动态读 env——模块级冻结废自测夹具（T2 先例·本件首版第四次犯·教训固化：env 可覆盖路径⛔模块级求值）。"""
    return os.environ.get("SKILL_HEALTH_ZCODE") or ZSKILLS_DEFAULT


def _askills():
    return os.environ.get("SKILL_HEALTH_AGENTS") or ASKILLS_DEFAULT


def _iter_skills(root):
    if not os.path.isdir(root):
        return
    for name in sorted(os.listdir(root)):
        yield name, os.path.join(root, name)


def check():
    rep = new_report(_zskills(), VERSION)
    znames = {}
    for name, path in _iter_skills(_zskills()):
        znames[name] = path
        if os.path.islink(path) and not os.path.exists(path):
            add(rep, "RED", "broken_link", f"{name} → {os.readlink(path)}（目标不存在）")
            continue
        real = os.path.realpath(path)
        cls = classify(real)  # 原语 classify 不解析软链·先 realpath（v1.0.1 首跑 17 项全误 non_skill_dir 实证）
        if cls != "skill":
            # 消费面语义：skill/category 之外的形态=残缺安装（原语 classify 对无 SKILL.md 目录归 resource/empty
            #   ——「skillmd_missing」独立分支为死代码·v1.0.2 删·教训=判据须在读原语语义之后写）
            add(rep, "WARN", "non_skill_dir", f"{name}: 形态 {cls}（缺 SKILL.md 或残缺安装）")
            continue
        if not fm_name(os.path.join(real, "SKILL.md")):
            add(rep, "WARN", "frontmatter_no_name", f"{name}: frontmatter 缺 name")
    # 重名遮蔽：.agents 同名会被 .zcode 发现序遮蔽（configuration-guide：first same-named wins）
    for name, path in _iter_skills(_askills()):
        if name in znames:
            add(rep, "WARN", "shadowed_by_zcode",
                f"{name}: ~/.agents/skills 与 ~/.zcode/skills 同名——后者遮蔽前者（agents 版永不加载）")
        elif os.path.isdir(path):
            smd = os.path.join(path, "SKILL.md")
            if os.path.isfile(smd) and not fm_name(smd):
                add(rep, "WARN", "agents_frontmatter_no_name", f"agents/{name}: frontmatter 缺 name")
    return finalize(rep)


def _self_test():
    import tempfile
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td) if (Path := __import__("pathlib").Path) else None
        z = td / "z"; a = td / "a"
        (z / "good").mkdir(parents=True)
        (z / "good" / "SKILL.md").write_text("---\nname: good\n---\nx", encoding="utf-8")
        os.symlink(str(td / "ghost_target"), str(z / "nolink"))  # 断链夹具（条目本身=断链软链）
        (z / "noskill").mkdir(); (z / "noskill" / "junk.txt").write_text("x")  # 残缺安装夹具（有内容无SKILL.md）
        (z / "noname").mkdir(parents=True)
        (z / "noname" / "SKILL.md").write_text("---\ntitle: x\n---\n", encoding="utf-8")
        (a / "good").mkdir(parents=True)                         # 遮蔽对
        os.environ["SKILL_HEALTH_ZCODE"] = str(z)
        os.environ["SKILL_HEALTH_AGENTS"] = str(a)
        rep = check()
        kinds = {f["kind"] for f in rep["findings"]}
        assert any(f["level"] == "RED" and f["kind"] == "broken_link" for f in rep["findings"]), "T2"
        ok += 1; print("✅ T2 断链 RED")
        assert "non_skill_dir" in kinds, "T3"
        ok += 1; print("✅ T3 残缺安装（non_skill_dir）")
        assert "frontmatter_no_name" in kinds, "T4"
        ok += 1; print("✅ T4 缺 name")
        assert "shadowed_by_zcode" in kinds, "T5"
        ok += 1; print("✅ T5 重名遮蔽")
        # T1 干净夹具→零 findings（放最后·污染 env 前重置）
        z2 = td / "z2"; (z2 / "clean").mkdir(parents=True)
        (z2 / "clean" / "SKILL.md").write_text("---\nname: clean\n---\nx", encoding="utf-8")
        os.environ["SKILL_HEALTH_ZCODE"] = str(z2)
        os.environ["SKILL_HEALTH_AGENTS"] = str(td / "a_empty")
        rep2 = check()
        assert not rep2["findings"], "T1"
        ok += 1; print("✅ T1 干净生态零告警")
    for k in ("SKILL_HEALTH_ZCODE", "SKILL_HEALTH_AGENTS"):
        os.environ.pop(k, None)
    print(f"自测结果: {ok}/5 通过")
    return 0 if ok == 5 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="有 RED 时 exit 1（默认恒 0·报告制）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    rep = check()
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"ZCode Skill 生态健康 · {rep['ts']} · {VERSION}")
        for f in rep["findings"]:
            print(f"  [{f['level']}] {f['kind']}: {f['detail']}")
        print(f"  Skill {rep['total']} · RED {rep['red']} / WARN {rep['warn']}")
    return 1 if (a.strict and rep["red"]) else 0


if __name__ == "__main__":
    sys.exit(main())
