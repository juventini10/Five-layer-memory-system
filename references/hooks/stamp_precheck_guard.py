#!/usr/bin/env python3
# REG: family=守卫 | registry=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md§四 | board=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md
# -*- coding: utf-8 -*-
"""stamp_precheck_guard.py v1.1 — 「变更记录时间戳」事前钩子（PreToolUse·落笔那一刻就拦）。

v1.1（2026-09-19 08:40·Qoder CN 童灵·皮叔令「根治这个风险」）：加「携带既有行」豁免——判据只作用在**新落笔**的行上。真机误伤实证：07:04 写成的合规变更行在 08:33 被再次提交（修订/移动/连带重写都会）时判"估算/旧值"→rc=2，等于禁止对当天记录做任何二次编辑。修法＝读取目标文件现有行，逐行原样命中者放行；新文件按全判（FileNotFoundError→known 空集），既有内容读不到才 fail-open。夹具 P8/P9 成对自证（豁免删掉 P8 红、写成一律放行 P9 红）→ 9/9·MUT:OK。

为什么要有它（PAT-045 第 4 次同型后判别）：事后闸已存在（guard_doc_consistency 件⑦ 检 `HH:Mx` 估算形态），
但**落笔时没有任何东西提醒我先 `date`**——2026-09-19 亲历：写"不许凭感觉记时间"这条规则的同一小时里，
`date` 打出 06:51，我仍按感觉写成 06:52。⇒ 缺的不是规则，是**事前**机制（愿景①机制自动运转·⛔不靠人记得）。

判据（只判一件事·宁可漏报不误伤）：
  变更记录行**行首**的落笔时间（`- v1.2.3（2026-09-19 06:43·…` 或 `### v4.0.7 · 2026-09-19 07:58`），
  当且仅当它写的是**今天**（或省略日期）时与系统当前时间比对：
    · 偏差 > TOLERANCE_MIN(12) 分钟 → 拦（估算/旧值）
    · 未来时间（> NOW+2 分钟）      → 拦（预写·铁律同源旧案 2026-08-03 QCN-20260803-001）
  ⛔不判正文中间引用的历史时刻（"05:48 落地"这类是取证不是落笔），⛔不判昨天的行（补记合法）。

退出码：0=放行 / 2=拦截（stderr 说明+改法）/ 非 .md·非 JSON·取不到时间 → fail-open 0（回落律·闸不自爆）。
挂法：`~/.qoder-cn/settings.json` → PreToolUse（本端实证 exit 2 拦得住工具调用；机器本地，⛔不宣称跨端覆盖）。
用法：stdin 收 payload；`--self-test` 跑夹具；`--check-time TEXT` 把同一判据用在非钩子场合（自测/巡检复用）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import datetime
import json
import os
import re
import sys

TOLERANCE_MIN = 12
FUTURE_GRACE_MIN = 2
LOG = os.path.expanduser("[记忆共享中心]/脚本中心/logs/stamp_precheck.jsonl")
# 行首 = 可选列表/标题符号 + 版本号 + 开括号 + 可选日期 + HH:MM
ROW_RE = re.compile(
    r"^[ \t]*(?:[-*#>|]|\d+\.)*[ \t]*v?[0-9][0-9.]*[^0-9\n]{0,6}[（(]\s*(?:(\d{4}-\d{2}-\d{2})[ Tt])?(\d{1,2}):(\d{2})",
    re.M)
# 标题式行：`### vX · 2026-09-19 07:58`（开括号不是必需）
HEAD_RE = re.compile(r"^[ \t]*#{1,6}[ \t]+[^#\n]*?[（(]?[ \t]*(\d{4}-\d{2}-\d{2})[ \t]*·?[ \t]+(\d{1,2}):(\d{2})", re.M)


def _now():
    return datetime.datetime.now()


def judge(text, now=None, known=None):
    """返回 [(行号, 写下的时间, 偏差分钟, 类别)]。只判"今天"的落笔时间。

    `known`=目标文件**现有行**（strip 后集合）：其中的行属于"携带"而非"新落笔"，
    一律放行。⛔不做这项区分的后果是实测的——修订/移动/连带重写一条今天早些写下的
    合规记录（如 07:04 的变更行在 08:33 被再次提交）会被判"估算/旧值"而拦截，
    即"把正确历史当错误当前"，误伤面覆盖所有对当天记录的二次编辑。
    """
    now = now or _now()
    known = known or set()
    lines = (text or "").split("\n")
    bad = []
    for rx in (ROW_RE, HEAD_RE):
        for m in rx.finditer(text or ""):
            d = m.group(1)
            if d and d != now.strftime("%Y-%m-%d"):
                continue                      # 非今天的行＝补记/历史，合法
            ln = text[:m.start()].count("\n")
            if ln < len(lines) and lines[ln].strip() in known:
                continue                      # 携带既有行，不是新落笔
            hh, mm = int(m.group(2)), int(m.group(3))
            try:
                wrote = now.replace(hour=hh, minute=mm)
            except ValueError:
                continue                      # 25:00 之类不判（防崩）
            delta = (wrote - now).total_seconds() / 60.0
            if delta > FUTURE_GRACE_MIN:
                bad.append((ln + 1, f"{hh:02d}:{mm:02d}", delta, "预写未来时间"))
            elif abs(delta) > TOLERANCE_MIN:
                bad.append((ln + 1, f"{hh:02d}:{mm:02d}", delta, "估算/旧值"))
    return sorted(set(bad))


def _msg(items):
    lines = ["⛔ [stamp_precheck] 变更记录行的落笔时间不是实取值（PAT-045 事前钩子）："]
    for ln, wrote, delta, kind in items:
        lines.append(f"   · 第 {ln} 行写 {wrote}，现在 {_now().strftime('%H:%M')}（偏差 {delta:+.0f} 分钟·{kind}）")
    lines.append('   改法：跑 `date "+%Y-%m-%d %H:%M"` 取当前值再写；确需补记历史时刻→把日期显式写成昨天或更早。')
    lines.append("   ⛔不要静默卸载本钩子；要改口径请改脚本并在 守卫编写规范 §3.4 留痕。")
    return "\n".join(lines)


def _log(payload_kind, verdict, detail):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now().strftime("%Y-%m-%d %H:%M:%S"), "kind": payload_kind,
                                 "verdict": verdict, "detail": detail}, ensure_ascii=False) + "\n")
    except OSError:
        pass                                   # 留痕失败不改变放行判定（闸不为记账自毁）


def extract(payload):
    """从 PreToolUse payload 里取 (文件路径, 待写文本)。形状不匹配→(None, "")。"""
    if not isinstance(payload, dict):
        return None, ""
    ti = payload.get("tool_input") or payload.get("args") or {}
    if isinstance(ti, str):
        try:
            ti = json.loads(ti)
        except ValueError:
            return None, ""
    path = ti.get("file_path") or ti.get("path") or ti.get("target_file") or ""
    body = ""
    for key in ("content", "new_string", "newText", "text"):
        if isinstance(ti.get(key), str):
            body += ti[key] + "\n"
    return path, body


def main(argv):
    if "--self-test" in argv:
        return self_test()
    if "--check-time" in argv:
        i = argv.index("--check-time")
        if hasattr(sys.stdin, "reconfigure"): sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        txt = argv[i + 1] if i + 1 < len(argv) else sys.stdin.read()
        bad = judge(txt)
        print(_msg(bad) if bad else "✅ 时间戳实取无异常")
        return 2 if bad else 0
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        print("stamp_precheck: payload 非 JSON → fail-open 放行（⛔不制造假红）", file=sys.stderr)
        return 0
    path, body = extract(payload)
    if not path or not str(path).endswith(".md"):
        return 0
    if not body.strip():
        return 0
    try:
        with open(os.path.expanduser(str(path)), encoding="utf-8") as fh:
            known = {ln.strip() for ln in fh}
    except FileNotFoundError:
        known = set()                         # 新文件：全部按新落笔判
    except (OSError, UnicodeDecodeError):
        # 读不到既有内容 ⇒ 无从区分"携带"与"新写"，按回落律 fail-open（⛔不制造误伤）
        print("stamp_precheck: 目标文件读不到既有内容 → fail-open 放行", file=sys.stderr)
        return 0
    bad = judge(body, known=known)
    if bad:
        print(_msg(bad), file=sys.stderr)
        _log("pretooluse", "BLOCK", {"path": str(path), "items": bad})
        return 2
    _log("pretooluse", "PASS", {"path": str(path)})
    return 0


def self_test():
    """夹具测线上本体 judge()（§3.0·5）。含两向探针 + **真变异**（把容差置大＝判据死亡，正例必转红）。"""
    now = datetime.datetime(2026, 9, 19, 6, 40)
    cases = [
        ("P1 实取当前分钟 → 放行", judge("- v1.0（2026-09-19 06:40·甲端）x", now) == [], "pass"),
        ("P2 偏差 55 分钟（凭感觉）→ 拦", len(judge("- v1.0（2026-09-19 05:45）x", now)) == 1, "block"),
        ("P3 未来时间 → 拦", len(judge("- v1.0（2026-09-19 07:30）x", now)) == 1, "block"),
        ("P4 正文引用历史时刻 → 放行", judge("- 关联：昨天 05:48 已落地，见系统日志", now) == [], "pass"),
        ("P5 昨天的行（补记合法）→ 放行", judge("- v1.0（2026-09-18 23:30）补记", now) == [], "pass"),
        ("P6 省略日期·当前分钟 → 放行", judge("- v1.0（06:41）x", now) == [], "pass"),
        ("P7 payload 非 JSON → fail-open 放行", extract("{" if False else "not-json") == (None, ""), "pass"),
        # P8/P9 成对＝「携带既有行」豁免的双向自证（等价变异测试）：
        #   同一条 05:45 旧时间戳行，在 known 内→放行，不在 known→必拦。
        #   若豁免分支被写死成"一律放行"，P9 必红；若被删除，P8 必红。
        ("P8 携带目标文件既有行（今天更早的合规记录）→ 放行",
         judge("- v1.0（2026-09-19 05:45）x", now, known={"- v1.0（2026-09-19 05:45）x"}) == [], "pass"),
        ("P9 同形但不在既有内容里（=新落笔的旧值）→ 拦",
         len(judge("- v1.0（2026-09-19 05:45）x", now, known={"别的行"})) == 1, "block"),
    ]
    bad = 0
    for name, ok, _ in cases:
        print(("  ✅ " if ok else "  ❌ ") + name)
        bad += 0 if ok else 1
    global TOLERANCE_MIN
    live = TOLERANCE_MIN
    TOLERANCE_MIN = 10 ** 9                     # 变异：把比对短路成"永不超时"
    try:
        mut = judge("- v1.0（2026-09-19 05:45）x", now)
    finally:
        TOLERANCE_MIN = live
    print(f"  变异体 容差置大 → 偏差 55 分钟用例 {'转绿 ✅ 判据活着' if mut == [] else '仍红 ❌ 变异未命中'}")
    pair = next(o for nm, o, _ in cases if nm.startswith("P8")) and \
        next(o for nm, o, _ in cases if nm.startswith("P9"))
    print("MUT:" + ("OK" if (mut == [] and bad == 0 and pair) else "FAIL") +
          f" 夹具 {len(cases) - bad}/{len(cases)}｜变异自证 2 例（容差短路→P2 必绿·携带豁免对偶→P8/P9 必一放一拦）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
