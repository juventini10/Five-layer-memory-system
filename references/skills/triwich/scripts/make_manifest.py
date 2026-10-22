#!/usr/bin/env python3
# REG: skip triwich Skill 包内页表工程件（非脚本中心守卫族）·版本纪律走本 Skill CHANGELOG·先例=triwich_scan.py 同口径
# -*- coding: utf-8 -*-
"""
make_manifest.py — 页表指纹生成器（M2·2026-10-21·⛔手维护=漂移必发的机械兑现）
病根：page_fingerprint 若靠人抄写，页改版即漂（H3 硬条款：声明值/实盘分叉新载体）。
真源算法（本文件唯一定义处）：
  页体 = 第二个 '---' 行之后到 EOF 的全部字节（含换行，UTF-8）
  指纹 = sha256(页体).hexdigest()[:8]
  ——指纹只盖页体，frontmatter 自指不递归（改指纹行不动页体，天然稳定）。
用法：
  build  [--root <skill目录>]   重算全部页指纹 → 同步写回页 frontmatter + pages/manifest.json
  check  [--root <skill目录>]   只验不写：manifest 表内 == 页 frontmatter 声明 == 重算，三方一致才绿
退出码：0=一致/建表成功；1=漂移（逐页列出）；2=页缺失/manifest 缺失。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, json, hashlib, argparse, datetime

def skill_pages(root):
    """页清单 = pages/ 下全部 .md（含 pr-reference/ 子目录）"""
    pages_dir = os.path.join(root, "pages")
    out = []
    for dirpath, dirnames, filenames in os.walk(pages_dir):
        for fn in sorted(filenames):
            if fn.endswith(".md"):
                p = os.path.join(dirpath, fn)
                out.append(os.path.relpath(p, root).replace(os.sep, "/"))
    return sorted(out)

def body_of(text):
    lines = text.splitlines(keepends=True)
    idx = [i for i, l in enumerate(lines) if l.strip() == "---"]
    if len(idx) < 2:
        return text  # 无 frontmatter：全文即页体
    return "".join(lines[idx[1] + 1:])

def fingerprint(path):
    with open(path, encoding="utf-8") as f:
        return hashlib.sha256(body_of(f.read()).encode("utf-8")).hexdigest()[:8]

def declared_fp(path):
    m = re.search(r"^page_fingerprint:\s*([0-9a-f]{8})\s*$",
                  open(path, encoding="utf-8").read(), re.M)
    return m.group(1) if m else None

def set_declared_fp(path, fp):
    t = open(path, encoding="utf-8").read()
    if re.search(r"^page_fingerprint:", t, re.M):
        t2 = re.sub(r"^page_fingerprint:\s*.*$", "page_fingerprint: %s" % fp, t, count=1, flags=re.M)
    else:
        t2 = re.sub(r"^(---\n(?:.*?\n)*?)(version:.*?$)",
                    r"\1\2\npage_fingerprint: %s" % fp, t, count=1, flags=re.M)
    if t2 == t and "page_fingerprint: %s" % fp not in t:
        raise RuntimeError("无法写入指纹行: %s" % path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(t2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "check"])
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    mf_path = os.path.join(root, "pages", "manifest.json")
    pages = skill_pages(root)
    if not pages:
        print("MANIFEST:FAIL 找不到任何页（%s/pages/）" % root, file=sys.stderr)
        return 2

    drift = []
    entries = []
    for rel in pages:
        p = os.path.join(root, rel)
        fp = fingerprint(p)
        dcl = declared_fp(p)
        if dcl != fp:
            drift.append((rel, dcl, fp))
        entries.append({"path": rel, "fingerprint": fp,
                        "bytes": os.path.getsize(p)})

    if a.mode == "build":
        for rel, dcl, fp in drift:  # 声明==重算：以重算为准写回（单向，指纹永不手改）
            set_declared_fp(os.path.join(root, rel), fp)
            entries[pages.index(rel)]["fingerprint"] = fingerprint(os.path.join(root, rel))
        manifest = {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "algorithm": "sha256(body-after-frontmatter)[:8] (真源=make_manifest.py)",
                    "pages": entries}
        with open(mf_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("MANIFEST:OK %d 页建表（漂移同步 %d 处）→ pages/manifest.json" % (len(entries), len(drift)))
        for rel, dcl, fp in drift:
            print("   synced %s: %s → %s" % (rel, dcl or "(缺)", fp))
        return 0

    # check：三方一致 = manifest 表内 == 页声明 == 重算
    if not os.path.isfile(mf_path):
        print("MANIFEST:FAIL manifest 缺失——先跑 make_manifest.py build", file=sys.stderr)
        return 2
    mf = json.load(open(mf_path, encoding="utf-8"))
    tab = {e["path"]: e["fingerprint"] for e in mf.get("pages", [])}
    bad = []
    for rel, dcl, fp in drift:
        bad.append("声明漂移 %s: frontmatter=%s 重算=%s" % (rel, dcl or "(缺)", fp))
    for e in mf.get("pages", []):
        cur = fingerprint(os.path.join(root, e["path"])) if os.path.isfile(os.path.join(root, e["path"])) else None
        if cur is None:
            bad.append("页丢失 %s" % e["path"])
        elif tab.get(e["path"]) != cur:
            bad.append("表内≠重算 %s: manifest=%s 重算=%s" % (e["path"], tab.get(e["path"]), cur))
    extra = set(skill_pages(root)) - set(tab)
    for x in sorted(extra):
        bad.append("新页未入表 %s" % x)
    if bad:
        print("MANIFEST:FAIL %d 处漂移（跑 make_manifest.py build 重算）：" % len(bad), file=sys.stderr)
        for b in bad:
            print("   " + b, file=sys.stderr)
        return 1
    print("MANIFEST:OK 三方一致（表内==声明==重算·%d 页）" % len(tab))
    return 0

if __name__ == "__main__":
    sys.exit(main())
