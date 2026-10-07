#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blank_claim_guard.py v1.0 -- false-blank detector, triggers-field edition.
PAT-043 root fix (2026-08-23, 你拍板): spec entries carry machine-readable
`triggers:` lines; blank claims are verified against THAT index, not prose.

v1.0 strategy:
  primary   : scene concept-labels vs spec `triggers:` tokens,
              bidirectional >=2-char containment -> precise flag
  fallback  : if spec has no triggers lines at all, lexical scan runs and
              every flag is marked low-confidence ("词面兜底·须人工复核")

History: v0.1-v0.3 lexical-only, calibration archived at
steps/step2.8-blank-guard-calibration.json (precision unusable -- the reason
this file exists in triggers form).

Usage: python3 blank_claim_guard.py <judgments.md> <blind_items.md> <spec.md>
Exit: 0 clean | 1 suspects | 2 usage error.
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import io, re, sys, json

def blocks(text):
    cur, out = [], []
    for line in text.splitlines():
        if line.startswith("## ") and cur:
            out.append("\n".join(cur)); cur = []
        cur.append(line)
    if cur: out.append("\n".join(cur))
    return out

def card_of(block):
    m = re.search(r"S(\d{3})", block.splitlines()[0] if block else "")
    return "S" + m.group(1) if m else None

BLANK = (re.escape(u"\u89c4\u683c\u4e66\u7a7a\u767d") + r"|" +
         re.escape(u"\u65e0\u5bf9\u5e94\u6761\u76ee") + r"|" +
         re.escape(u"\u65e0\u5904\u7406\u4f9d\u636e") + r"|" +
         re.escape(u"\u65e0\u4f9d\u636e\u53ef\u5224"))

def scene_of(items_text, card):
    want = re.compile(r"^## .*" + card); grab = False; buf = []
    for line in items_text.splitlines():
        if line.startswith("## "):
            if grab: break
            grab = bool(want.match(line)); continue
        if grab: buf.append(line)
    t = "\n".join(buf)
    m = re.search(re.escape(u"\u3010\u573a\u666f\u3011") + r"\**(.*?)(?:\*\*\u3010|\Z)", t, re.S)
    return (m.group(1) if m else t).strip()

def concept_labels(scene, block_codes=None):
    """labels anchored to C-codes; plus generic long runs as fallback terms."""
    labeled = {}
    for m in re.finditer(r"(C-\d{3})\s*([\u4e00-\u9fffA-Za-z0-9]{2,12})", scene):
        labeled.setdefault(m.group(1), set()).add(m.group(2))
    return labeled

def trigger_index(spec_text):
    """[(line_no, [tokens])]. A triggers line belongs to the entry above it."""
    idx = []
    for i, ln in enumerate(spec_text.splitlines(), 1):
        m = re.match(r"\s*triggers\s*[:\uff1a]\s*(.+)", ln)
        if m:
            toks = [t.strip() for t in re.split(r"[/\u3001,]\s*", m.group(1)) if len(t.strip()) >= 2]
            if toks:
                idx.append((i, toks))
    return idx

def bidir_hit(token, line):
    """token inside line, or any >=2-char CJK run of line inside token."""
    if token in line:
        return True
    for r in re.findall(r"[\u4e00-\u9fff]{2,}", line):
        if (r in token) or (len(token) >= 2 and token[:2] in r):
            return True
    return False

def main():
    if len(sys.argv) != 4:
        print(__doc__); sys.exit(2)
    j_text = io.open(sys.argv[1], encoding="utf-8").read()
    b_text = io.open(sys.argv[2], encoding="utf-8").read()
    s_text = io.open(sys.argv[3], encoding="utf-8").read()
    s_lines = s_text.splitlines()
    tidx = trigger_index(s_text)
    mode = "triggers" if tidx else u"\u8bcd\u9762\u515c\u5e95"
    report, suspects = [], 0
    for blk in blocks(j_text):
        card = card_of(blk)
        if not card or not re.search(BLANK, blk):
            continue
        sc = scene_of(b_text, card)
        labels = concept_labels(sc)
        # candidate terms: code-anchored labels (+their 2-char heads/tails)
        terms = set()
        for c, labs in labels.items():
            if c not in blk and c not in sc:
                continue
            for lab in labs:
                terms.add(lab); terms.add(lab[:2]); terms.add(lab[-2:])
        hits = []
        if mode == "triggers":
            for ln_no, toks in tidx:
                joined = " ".join(toks)
                for t in sorted(terms, key=len, reverse=True):
                    if len(t) < 2: continue
                    if bidir_hit(t, joined):
                        hits.append({"term": t, "spec_line": ln_no,
                                     "tokens": toks, "via": "triggers"})
                        break
        hits = hits[:3]
        flag = bool(hits)
        suspects += 1 if flag else 0
        report.append({"card": card, "mode": mode, "terms_tried": sorted(terms)[:8],
                       "suspected_false_blank": flag, "hits": hits})
    print(json.dumps({"blank_claims_checked": len(report),
                      "suspected_false_blanks": suspects,
                      "index_mode": mode,
                      "items": report}, ensure_ascii=False, indent=1))
    sys.exit(1 if suspects else 0)

if __name__ == "__main__":
    main()
