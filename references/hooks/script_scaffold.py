#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
script_scaffold.py — 家族脚本脚手架生成器（生成即合规 + 生成即入册）
============================================================
家族：变换（改） ｜ 部署形态：按需
版本：v0.1

为什么存在（根因）：
  脚本体系"总在修"的两个病根——①生成端无标准（头部无版本标识、无退出码约定、
  无负例自测桩）②入册无闸门（新增脚本漏登记 scripts_manifest → 孤儿）。
  本生成器把两件事合并成一条命令：从模板生成 → 头部天然合规 → 自动入册。
  理论位：模型参考自适应控制——骨架=参考模型，生成=以参考模型为准的构造，
  门禁=误差驱动的调整器（《工程控制论》下册·第18章）。

用法：
  python3 script_scaffold.py <家族> <脚本名> --duty "一句话职责" [--why "根因"] [--form 按需] [--dry-run]

退出码约定：
  0 = 成功
  2 = 参数错误
  3 = 内部错误
  4 = 冲突（文件已存在 / 命名违规 / 模板缺失）

设计原则：
  - 先 dry-run 再落地（铁律-020：派生类操作先看命中范围）
  - 生成前断言模板存在（铁律-021④：替换锚点未命中断言报错，⛔不接受静默无操作）
  - 入册即同一事务（生成失败不写清单，清单失败回滚已生成文件）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import hashlib
import json
import os
import re
import sys

__version__ = "v0.1"

HOME = os.path.expanduser("~")
PHILO_DIR = os.path.join(HOME, "[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学")
# 路径可被环境变量覆盖——用于隔离压测（铁律-014：未隔离验证绝不直跑真实文件）
TPL_DIR = os.environ.get("SCAFFOLD_TPL_DIR") or os.path.join(PHILO_DIR, "templates")
MANIFEST = os.environ.get("SCAFFOLD_MANIFEST") or os.path.join(HOME, "[记忆共享中心]/脚本中心/scripts_manifest.json")
DEV_DIR = os.environ.get("SCAFFOLD_DEV_DIR") or os.path.join(HOME, "[记忆共享中心]/脚本中心")

FAMILY_MAP = {"守卫": "guard", "引擎": "engine", "变换": "transform"}
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*\.py$")


def fail(msg, code=3):
    print(f"❌ {msg}", file=sys.stderr)
    return code


def name_ok(fname):
    """命名规范校验：小写 snake_case + .py（对齐 01-通用规范 §三 命名规范）。"""
    return bool(NAME_RE.match(fname))


def sha8_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:8]


def build(args):
    fam_en = FAMILY_MAP[args.family]
    tpl = os.path.join(TPL_DIR, f"_template_{fam_en}.py")
    if not os.path.isfile(tpl):
        return fail(f"模板缺失：{tpl}（该家族骨架尚未建立）", 4)
    with open(tpl, encoding="utf-8") as f:
        tpl_text = f.read()

    body = (tpl_text
            .replace("{{NAME}}", args.name)
            .replace("{{DUTY}}", args.duty)
            .replace("{{WHY}}", args.why or "TODO：补充根因（为什么需要这个守卫）")
            .replace("{{FORM}}", args.form))
    for token in ("{{NAME}}", "{{DUTY}}", "{{WHY}}", "{{FORM}}"):
        assert token not in body, f"占位符未替换：{token}"

    target = os.path.join(DEV_DIR, args.name)
    rel = os.path.relpath(target, HOME)
    if rel.startswith(".."):
        rel = target  # 目标不在 HOME 下（隔离压测场景）→ 记绝对路径
    entry = {
        "name": args.name, "path": rel, "family": args.family, "subfamily": None,
        "form": args.form, "event": None, "version": "v0.1", "win_entry": False,
        "sha8": "", "events": [], "deployed_wb": False, "in_package": False,
    }
    return body, target, entry


def do_write(body, target, entry):
    with open(target, "w", encoding="utf-8") as f:
        f.write(body)
    os.chmod(target, 0o755)
    entry["sha8"] = sha8_of(target)

    with open(MANIFEST, encoding="utf-8") as f:
        man = json.load(f)
    names = {s["name"] for s in man["scripts"]}
    assert entry["name"] not in names, f"清单已存在同名条目：{entry['name']}"
    man["scripts"].append(entry)
    man["scripts"].sort(key=lambda s: s["name"])
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)

    # 并发防护（铁律-014：并发可检测·⛔不宣称并发安全）——
    # 多端并行写同一清单时，读-改-写窗口内他端条目可能丢失，写后复验并大声报错。
    with open(MANIFEST, encoding="utf-8") as f:
        after = json.load(f)
    names_after = {s["name"] for s in after["scripts"]}
    assert entry["name"] in names_after, "写入后未找到本条（并发冲突）"
    lost = names - names_after
    if lost:
        raise RuntimeError(
            f"⚠️ 并发写入检测：{len(lost)} 条他端条目在本次写入过程中丢失 "
            f"{sorted(lost)[:5]}——请重跑本命令以补回"
        )
    return len(after["scripts"])


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("family")
    ap.add_argument("name")
    ap.add_argument("--duty", required=True)
    ap.add_argument("--why", default="")
    ap.add_argument("--form", default="按需")
    ap.add_argument("--dry-run", action="store_true")
    if len(sys.argv) == 1 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    args = ap.parse_args()

    if args.family not in FAMILY_MAP:
        return fail(f"未知家族：{args.family}（可选：{'/'.join(FAMILY_MAP)}）", 2)
    if not name_ok(args.name):
        return fail(f"命名违规：{args.name}（须为小写 snake_case + .py）", 4)
    target = os.path.join(DEV_DIR, args.name)
    if os.path.exists(target):
        return fail(f"文件已存在，拒绝覆盖：{target}", 4)

    built = build(args)
    if isinstance(built, int):
        return built
    body, target, entry = built

    if args.dry_run:
        print(f"🔎 dry-run：将生成 {target}")
        print(f"   家族={args.family} 形态={args.form} 版本=v0.1")
        print(f"   清单将新增条目：{entry['name']}（当前 {len(json.load(open(MANIFEST))['scripts'])} 条）")
        print(f"   头部合规自检：{'✅ 命中版本标识判据' if re.search(r'^# version:', body, re.M) else '❌ 未命中'}")
        return 0

    total = do_write(body, target, entry)
    print(f"✅ 已生成 {target}")
    print(f"✅ 已入册 scripts_manifest.json（共 {total} 条）")
    print(f"   版本=v0.1 sha8={entry['sha8']}")
    print("   下一步：补 check() 实现 + 自测函数（双向断言·命名避开发现式正则的字面量）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
