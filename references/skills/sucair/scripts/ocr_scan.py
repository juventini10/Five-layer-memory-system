#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""素裁 · 扫描件 OCR 扫描器 v1.1.0（2026-10-17 新增）

用途：把扫描版 PDF 批量转成带 [页 N] 标记的纯文本，并出「结构闸」体检表。

设计要点（全部来自 2026-10-17 实测，不是拍脑袋）：
1. **必须 use_cls=False** —— 这是真凶，不是 DPI。p22 那张「白崇禧…」小字注释行：
   use_cls=True 漏掉（26 框），use_cls=False 读到（27 框），**同一张 200dpi 图**。
   最初误判成"200dpi 漏行"，是 cls 阶段的干扰被算到了 DPI 头上（v1.0.0 错误结论，已纠正）。
2. **DPI 200 与 300 在 use_cls=False 下效果相当** —— 7 页实测 CER：200dpi 1.45% / 300dpi 1.51%。
   默认仍取 300（给其他书的更小字号留余量），`--dpi 200` 可省约 30% 磁盘。
3. 引擎探测优先 —— 不强依赖 RapidOCR：装了就快跑，没装报 OCR_ENGINE=none，
   由素裁 SKILL.md 0.1.0 改走视觉转写兜底。分享给他人时不装也能用。
4. 结构闸只阻断硬信号（空页/双跑差异），缺页码/缺页眉/几何少行只作 △ 提示——
   本书半页（章节尾）天然缺页码，当阻断项会误杀（v1.0.0 实测 6/7 页误报）。
5. **闸表抓不到单字识别错误** —— 「陈赓」被读成「陈赛」，同一模型两次跑都错一样，双跑无差异。
   那类靠纠错表 + 抽检 3 页硬项，别指望闸表。

用法：
  python3 scripts/ocr_scan.py --probe
  python3 scripts/ocr_scan.py --pdf <源.pdf> --out <输出.txt> [--pages 1-30] [--dpi 300] [--cross-check]
  python3 scripts/ocr_scan.py --img <单页.png>

环境变量：
  SUCAIR_OCR_PYTHON  可选。指向已装 rapidocr-onnxruntime 的解释器
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import statistics
import subprocess
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass  # Windows cp1252 控制台防非ASCII print 崩（F2 根治·2026-10-17）

import tempfile
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CORR_FILE = SKILL_DIR / "references" / "ocr-corrections.json"
DEFAULT_DPI = 300
CROSS_DPI = 200          # 双跑对照用的低清档（实测 200 与 300 错法不同，正好互补）
PITCH_TOLERANCE = 2.0    # 几何提示：行数比容量估计少超过这么多行才 △

# 年份形态检查：本书排印用「一九五○年」，RapidOCR 会把「○」整字吞掉 → 「一九五年」
# （2026-10-17 目录页 p6/p8 实测）。年份是硬项，吞字必须显形，⛔不做自动修复（哪个位置缺
# 零无法确定，猜着补=制造新错误）。只检出，交人工/视觉复核。
YEAR_BAD_RE = re.compile(r"(?<![〇○0-9一二三四五六七八九])[一二][〇○0-9一二三四五六七八九]{1,2}年")

# ---------------------------------------------------------------- 引擎探测


def _importable() -> bool:
    try:
        import rapidocr_onnxruntime  # noqa: F401
        return True
    except Exception:
        return False


def find_engine() -> tuple[str, str | None]:
    """返回 (engine_name, python_executable)。engine_name ∈ {rapidocr, none}"""
    if _importable():
        return "rapidocr", sys.executable
    alt = os.environ.get("SUCAIR_OCR_PYTHON")
    if alt and Path(alt).exists():
        try:
            r = subprocess.run(
                [alt, "-c", "import rapidocr_onnxruntime"],
                capture_output=True, timeout=180,
            )
            if r.returncode == 0:
                return "rapidocr", alt
        except Exception:
            pass
    return "none", None


# ---------------------------------------------------------------- 后处理归一

_MARKER_RE = re.compile(r"^[ \t]*[【\[（(]\s*(\d{1,2})\s*[】\]）)]?[ \t]*")   # 右括号可缺：实测有「[6」「【1）」等残形
_DASH_RE = re.compile(r"[-－—]{2,}|一-|一一(?=[九○〇\d])")


def normalize(text: str) -> str:
    out = []
    for line in text.split("\n"):
        line = _MARKER_RE.sub(lambda m: "〔%s〕" % m.group(1), line)
        line = _DASH_RE.sub("——", line)
        line = re.sub(r"\(([^()]{1,20})\)", r"（\1）", line)
        # 半角逗号 → 全角（仅 CJK 上下文，避免误伤数字/英文）
        line = re.sub(r"(?<=[\u4e00-\u9fff]),", "，", line)
        # 年份里的 ASCII 0 → ○：本书排印用「一九○五」，OCR 输出「一九0五」
        line = re.sub(r"(?<=[一二三四五六七八九])0(?=[一二三四五六七八九)）])", "○", line)
        out.append(line.rstrip())
    return "\n".join(out)


def load_corrections() -> list[tuple[str, str]]:
    if not CORR_FILE.exists():
        return []
    try:
        data = json.loads(CORR_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"WARN: 纠错表解析失败 {CORR_FILE}: {e}", file=sys.stderr)
        return []
    return [
        (it["wrong"], it["right"])
        for it in data.get("contextual", [])
        if it.get("wrong") and it.get("right") and it["wrong"] != it["right"]
    ]


def apply_corrections(text: str, pairs: list[tuple[str, str]]) -> tuple[str, list[str]]:
    hits = []
    for wrong, right in pairs:
        n = text.count(wrong)
        if n:
            text = text.replace(wrong, right)
            hits.append(f"{wrong}→{right}×{n}")
    return text, hits


# ---------------------------------------------------------------- OCR 主体


def ocr_page(engine, png: str) -> tuple[str, list[dict]]:
    """单页 OCR + 行序还原。返回 (文本, 行元信息[{y,h,text}])"""
    res, _ = engine(png, use_cls=False)
    if not res:
        return "", []
    items = []
    for box, text, _score in res:
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        items.append({
            "y": sum(ys) / 4, "x": min(xs),
            "h": max(ys) - min(ys), "t": text,
        })
    items.sort(key=lambda d: d["y"])
    lines, cur = [], [items[0]]
    for it in items[1:]:
        tol = max(10.0, min(it["h"], cur[-1]["h"]) * 0.55)
        if abs(it["y"] - cur[-1]["y"]) <= tol:
            cur.append(it)
        else:
            lines.append(cur)
            cur = [it]
    lines.append(cur)

    meta, texts = [], []
    for ln in lines:
        ln.sort(key=lambda d: d["x"])
        meta.append({
            "y": sum(d["y"] for d in ln) / len(ln),
            "h": max(d["h"] for d in ln),
            "text": "".join(d["t"] for d in ln),
        })
        texts.append("".join(d["t"] for d in ln))
    return "\n".join(texts), meta


def render(pdf: str, outdir: str, dpi: int, first: int, last: int) -> None:
    subprocess.run(
        ["pdftoppm", "-r", str(dpi), "-png", "-f", str(first), "-l", str(last),
         pdf, os.path.join(outdir, "p")],
        check=True,
    )


def pdf_pagecount(pdf: str) -> int:
    try:
        r = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, timeout=60)
        m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 0


# ---------------------------------------------------------------- 结构闸


def gate_row(pno: int, text: str, meta: list[dict]) -> dict:
    lines = [ln for ln in text.split("\n") if ln.strip()]

    # 页码位置随奇偶页翻转（本书实测）：
    #   偶数页（印刷页）在行首 —— 「8毛泽东文集第六卷」
    #   奇数页在行尾 —— 「解放西南地区的作战方针7」
    #   偶有独占一行 —— 「6」
    # v1.0.0 只认第三种 → 7 页里误判 6 页缺页码。
    pagenum = ""
    head = ""
    for idx, ln in enumerate(lines[:3]):
        s = ln.strip()
        core = s
        if idx == 0:
            m = re.search(r"(\d{1,4})\s*$", s)
            if m and s[:m.start()].strip():
                pagenum = pagenum or m.group(1)
                core = s[:m.start()]
            elif s.isdigit() and len(s) <= 4:
                pagenum = pagenum or s
                core = ""
        if not pagenum:
            m2 = re.match(r"\s*(\d{1,4})(?=\D)", s)
            if m2:
                pagenum = m2.group(1)
                core = s[m2.end():]
        core = core.strip()
        if not head and len(core) >= 2:
            head = core[:18]

    # 几何容量估计：用最紧的行距当"一行的高度"，估这一块文本最多能放几行
    cap = 0
    if len(meta) >= 3:
        gaps = [meta[i]["y"] - meta[i - 1]["y"] for i in range(1, len(meta))]
        pos = [g for g in gaps if g > 0]
        pitch = min(pos) if pos else 0
        extent = meta[-1]["y"] - meta[0]["y"]
        if pitch > 0:
            cap = int(extent / pitch) + 1

    return {
        "页": pno,
        "行数": len(lines),
        "字数": len(re.sub(r"\s", "", text)),
        "页眉": head,
        "印刷页码": pagenum,
        "容量": cap,
        "疑似漏行": (cap - len(lines)) if cap else 0,
        "年份异常": [m.group(0) for m in YEAR_BAD_RE.finditer(text)],
        "双跑差异": "",
        "⚠️": "",
    }


def text_diff(a: str, b: str) -> str:
    """a=300dpi 文本, b=200dpi 文本。返回差异摘要（空串=无差异）"""
    na = re.sub(r"[.·…\s\u3000]", "", a)
    nb = re.sub(r"[.·…\s\u3000]", "", b)
    sm = difflib.SequenceMatcher(None, na, nb, autojunk=False)
    parts = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        seg_a, seg_b = na[i1:i2], nb[j1:j2]
        if max(len(seg_a), len(seg_b)) >= 6:   # 只报成段差异，忽略标点级噪声
            parts.append(f"300dpi<{seg_a[:24]}> / 200dpi<{seg_b[:24]}>")
    return " ； ".join(parts[:3])


def finalize_gate(rows: list[dict], cross: bool) -> list[dict]:
    """阻断项只留硬信号。缺页码/缺页眉降为 △ 提示——本书有半页（章节尾）天然缺，
    当阻断项会把正常页判死（v1.0.0 实测 6/7 页误报）。"""
    for r in rows:
        flags = []
        if r["行数"] == 0:
            flags.append("空页")
        if cross and r["双跑差异"]:
            flags.append("双跑差异")
        r["⚠️"] = "+".join(flags)
        hints = []
        if not r["印刷页码"]:
            hints.append("缺页码")
        if not r["页眉"]:
            hints.append("缺页眉")
        if r["疑似漏行"] > PITCH_TOLERANCE:
            hints.append(f"几何少{r['疑似漏行']}行")
        if r.get("年份异常"):
            hints.append(f"年份存疑{len(r['年份异常'])}处")
        r["△"] = " ".join(hints)
    return rows


def render_gate_md(rows: list[dict], src: str, cross: bool) -> str:
    bad = [r for r in rows if r["⚠️"]]
    hint = [r for r in rows if not r["⚠️"] and r["△"]]
    med_lines = statistics.median([r["行数"] for r in rows]) if rows else 0
    out = [
        f"# 结构闸报告 · {Path(src).name}",
        "",
        f"- 总页数：{len(rows)}",
        f"- 阻断页：{len(bad)}（{len(bad)/max(1,len(rows))*100:.1f}%）",
        f"- 提示页（不阻断）：{len(hint)}",
        f"- 行数中位数：{med_lines:g}",
        f"- 双跑交叉：{'已启用' if cross else '未启用'}",
        "",
        "> **阻断判据**（必须复核后才入 C1）：空页 / 双跑差异非空。",
        "> **△ 提示**（看一眼即可）：缺页码 / 缺页眉 / 几何少行。"
        "篇首页（如 p24「同绥远〔1〕负责人的谈话」）和章节尾半页天然不排页码，不是错；"
        "几何少行多由段落间距造成，也不是错。",
        "> **闸表抓不到什么**（如实标注）：单字识别错误（如「陈赓」被读成「陈赛」）——"
        "同一模型两次跑都错一样，双跑抓不到。那类靠 `references/ocr-corrections.json` 纠错表 + 抽检 3 页硬项。",
        "",
        "| 页 | 行数 | 字数 | 页码 | ⚠️ | △ |",
        "|:--|:--|:--|:--|:--|:--|",
    ]
    for r in rows:
        if r["⚠️"] or r["△"]:
            out.append(
                f"| {r['页']} | {r['行数']} | {r['字数']} | {r['印刷页码'] or '—'} | "
                f"{r['⚠️'] or '—'} | {r['△'] or '—'} |"
            )
    if not bad and not hint:
        out.append("| — | — | — | — | 无异常 | — |")

    years = [(r["页"], y) for r in rows for y in r.get("年份异常", [])]
    if years:
        out += ["", "## 年份存疑明细", "",
                "> 判据：`年` 前不足 4 个数字字符（正常应为「一九五○年」）。"
                "本书排印用「○」，RapidOCR 会把「○」整字吞掉。⛔不自动修复——"
                "缺的零在哪个位置无法确定，猜着补=制造新错误。须回原图/视觉转写确认。", ""]
        for pno, y in years:
            out.append(f"- p{pno}：`{y}`")

    if any(r["双跑差异"] for r in rows):
        out += ["", "## 双跑差异明细", ""]
        for r in rows:
            if r["双跑差异"]:
                out.append(f"- **p{r['页']}**：{r['双跑差异']}")
        out += ["", "> 差异行不代表哪边对——必须回原图裁决（PIL 裁剪放大，避开 Read 图片去重）。"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 入口


def main() -> int:
    ap = argparse.ArgumentParser(description="素裁 · 扫描件 OCR 扫描器")
    ap.add_argument("--probe", action="store_true", help="探测本机 OCR 引擎")
    ap.add_argument("--pdf")
    ap.add_argument("--img")
    ap.add_argument("--out")
    ap.add_argument("--pages", help="页码范围，如 1-30；缺省=全书")
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    ap.add_argument("--cross-check", action="store_true",
                    help="双跑交叉：额外用 200dpi 读一遍并逐页比对（耗时约翻倍；抓检测层不稳定/漏框，抓不到单字识别错误）")
    ap.add_argument("--no-corrections", action="store_true")
    args = ap.parse_args()

    t_start = time.time()
    engine_name, engine_py = find_engine()

    if args.probe:
        print(f"OCR_ENGINE={engine_name}")
        if engine_name == "rapidocr":
            print(f"OCR_PYTHON={engine_py}")
            print(f"OCR_DPI={args.dpi}")
        else:
            print("HINT=未探测到 RapidOCR。走视觉转写兜底；"
                  "想快就装：pip install rapidocr-onnxruntime"
                  "（或设 SUCAIR_OCR_PYTHON 指向已装的解释器）")
        return 0

    if engine_name == "none":
        print("OCR_ENGINE=none —— 本机无 OCR 引擎，请改走视觉转写分支。", file=sys.stderr)
        return 3

    if engine_py and os.path.realpath(engine_py) != os.path.realpath(sys.executable):
        os.execv(engine_py, [engine_py, os.path.abspath(__file__)] + sys.argv[1:])

    from rapidocr_onnxruntime import RapidOCR  # noqa: E402
    engine = RapidOCR()

    if args.img:
        text, _ = ocr_page(engine, args.img)
        print(normalize(text))
        return 0

    if not args.pdf:
        ap.print_help()
        return 2

    total = pdf_pagecount(args.pdf)
    first, last = 1, total or 10 ** 6
    if args.pages:
        m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", args.pages)
        if not m:
            print("--pages 格式应为 1-30", file=sys.stderr)
            return 2
        first, last = int(m.group(1)), int(m.group(2))
        if total:
            last = min(last, total)

    out_path = Path(args.out) if args.out else Path(f"{Path(args.pdf).stem}-OCR全文.txt")
    gate_path = out_path.with_name(out_path.stem + "-结构闸.md")
    pairs = [] if args.no_corrections else load_corrections()

    rows: list[dict] = []
    texts: dict[int, str] = {}
    all_hits: list[str] = []

    with tempfile.TemporaryDirectory(prefix="sucair_ocr_") as tmp:
        hi = os.path.join(tmp, "hi")
        os.makedirs(hi, exist_ok=True)
        t0 = time.time()
        render(args.pdf, hi, args.dpi, first, last)
        pngs = sorted(Path(hi).glob("p-*.png"))
        if not pngs:
            print("转图失败：pdftoppm 无输出", file=sys.stderr)
            return 4
        t_render = time.time() - t0

        t0 = time.time()
        for i, png in enumerate(pngs, start=1):
            pno = first + i - 1
            text, meta = ocr_page(engine, str(png))
            text = normalize(text)
            if pairs:
                text, hits = apply_corrections(text, pairs)
                all_hits.extend(hits)
            texts[pno] = text
            rows.append(gate_row(pno, text, meta))
            print(f"\rOCR {pno}/{last}", end="", file=sys.stderr, flush=True)
        t_ocr = time.time() - t0
        print("", file=sys.stderr)

        t_cross = 0.0
        if args.cross_check:
            t0 = time.time()
            lo = os.path.join(tmp, "lo")
            os.makedirs(lo, exist_ok=True)
            render(args.pdf, lo, CROSS_DPI, first, last)
            lo_pngs = sorted(Path(lo).glob("p-*.png"))
            by_pno = {r["页"]: r for r in rows}
            for i, png in enumerate(lo_pngs, start=1):
                pno = first + i - 1
                if pno not in by_pno:
                    continue
                t2, _ = ocr_page(engine, str(png))
                by_pno[pno]["双跑差异"] = text_diff(texts[pno], normalize(t2))
                print(f"\rCROSS {pno}/{last}", end="", file=sys.stderr, flush=True)
            print("", file=sys.stderr)
            t_cross = time.time() - t0

    rows = finalize_gate(rows, args.cross_check)

    body = "\n".join(f"[页 {r['页']}]\n{texts[r['页']]}\n" for r in rows)
    out_path.write_text(body, encoding="utf-8")
    gate_path.write_text(render_gate_md(rows, args.pdf, args.cross_check), encoding="utf-8")

    bad = [r for r in rows if r["⚠️"]]
    print(f"OK 文本 → {out_path}（{len(rows)} 页 / {len(body)} 字）")
    print(f"OK 闸表 → {gate_path}（阻断异常 {len(bad)} 页）")
    print(f"耗时：转图 {t_render:.0f}s / OCR {t_ocr:.0f}s"
          + (f" / 双跑 {t_cross:.0f}s" if args.cross_check else "")
          + f" / 合计 {time.time()-t_start:.0f}s")
    if all_hits:
        print("纠错命中：" + "；".join(sorted(set(all_hits))))
    if bad:
        print("⚠️ 阻断页：" + ", ".join(str(r["页"]) for r in bad))
        print("   → 这些页必须用视觉转写复核后再入 C1")
    if not args.cross_check:
        print("提示：未开 --cross-check。该开关抓检测层漏框，不抓单字识别错误（那靠纠错表+抽检）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
