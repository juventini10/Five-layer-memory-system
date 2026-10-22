#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/tsl_verify.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""tsl_verify.py — TSL 验证清单机械核验器（v0.3·2026-09-23 全层化·皮叔令「TSL必须0出错显示·机械保底·禁美化」）

v0.3 变更（构造权移交扩面 L7→L0-L7）：
  · v0.2 只覆盖 L7 五项，L0-L6 仍由 AI 手绘自评——你实证指出这是"美化通道"（树是手画的，
    状态是自己评的，连"8要素没走"都能编个豁免注脚 QCN-012）。
  · v0.3：--full 渲染全层树，每层只认**机械锚**（文件/台账/launchd/日志），拿不到锚=⚪如实
    显示"无机械证据"，⛔永不因 AI 声称而升 ✅（可信≠全绿：报告与实盘一致才叫可信）。
  · 输出末行 stamp；整树+stamp 落 cache/last_tree.txt → tsl_closeout_guard 逐行比对回复中的树，
    改任一状态行=留痕（美化在机制层被封）。
诚实边界：L4(W3无留痕)/L5(8要素·试金无锚) 本端暂无机械源=⚪，扩展需载体先建（不是假装能验）。
用法：python3 tsl_verify.py --since "YYYY-MM-DD HH:MM" [--full]
退出码：0=NO-GO 为 0；1=有 NO-GO；2=参数错误
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import os, sys, argparse, datetime, re, subprocess, hashlib
BASE = os.environ.get("BULUOTU_BASE") or os.path.expanduser("[记忆共享中心]")
#   ^ 2026-09-27 测试缝（D35 缺口补齐）：锚点根可整根重定向，自测夹具⛔不得写进真档案
QCN_RULES = os.path.expanduser("~/.qoder-cn/rules")
SLICES = os.path.join(BASE, "数字分身/K2切片蒸馏/slices")
SSOT = os.path.join(BASE, "数字分身/童灵·人格规格书.md")
DECLARE_STATE = os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"),
                             "doenglingz_level_declare_state.json")
# v0.11.6 2026-10-09 L3读面根治（Qoder CN 童灵D3·同 W3 L28"写读分根即假红"先例）：
#   根因＝guard 各端按 DOENGLINGZ_CONFIG_DIR 写本端 state（本端192行含当日记录），tsl 读面只盯 ~/.workbuddy
#   （WB 台账末行停昨日）⇒ 本端每轮 L3 恒🟡＝双向失明（声明真在·台账看不见）。修法＝读面跟随写面聚合。
import glob as _glob
def _declare_files():
    home = os.path.expanduser("~")
    cands = [DECLARE_STATE]
    cands += _glob.glob(os.path.join(home, ".*", "doenglingz_level_declare_state.json"))
    cands += _glob.glob(os.path.join(os.path.expanduser("[记忆共享中心]"), ".*", "doenglingz_level_declare_state.json"))
    out = []
    for c in cands:
        if c not in out:
            out.append(c)
    return out

def _declare_src_match(path, src):
    if not src or src == "unknown":
        return True
    import re as _re
    tag = _re.sub(r"[._\-]", "", os.path.basename(os.path.dirname(path))).lower()
    return tag == _re.sub(r"[_\-]", "", src.lower())
GUARD_STATE = os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"),
                           "doenglingz_guard_state.json")
CACHE = os.environ.get("TSL_VERIFY_CACHE") or os.path.expanduser("~/.cache/tsl_verify")   # env=测试隔离缝（对齐 closeout 同名先例·守卫规范 §3.9）
W3_LEDGER = os.path.join(BASE, "脚本中心/logs/runtime/w3_inject_ledger.jsonl")  # 2026-10-07 W3根治：读侧对齐写侧(doenglingz_inject_prompt L489)——写读分根即假红
__version__ = "v0.11.9"
#   v0.11.9（2026-10-11·ZCode 童灵·L7-3 serve 账认账·任务卡队列③挂账清偿）：
#     _kb_trail_since 原只认 source=cli → CLI 快通道（kb_serve 常驻引擎·2026-10-11 上线）
#     落的 source=serve 账被 L7-3 判据过滤 = 归属断（当日两度实证 L7-3 红）。
#     修法：cli∪serve 同权——两者动作主体同为「童灵本端主动实跑 search_kb」（serve 只是
#     执行引擎为常驻 daemon·trail 落同一本 kb_query_trail.jsonl）；source=inject（注入流）
#     仍排除。⛔不改 search_kb 侧记账（追加第二账=双本账）。
#   v0.11.8（2026-10-10·Qoder CN 童灵·L7-2 假红根治·皮叔令「符合愿景根治处理」）：
#     判据面补第三出口——08 §L7-2 早允许「本次会话无铁律盲区需反哺」，但机械判据只认两本账
#     （扫描 log ∪ 反哺日志）＝合法出口无处落账 → 无素材回合必红（同族第三次：v0.11.3 缺第二账本
#     ／v0.11.4 账本行形状脱钩／本次缺第三出口）。修法＝读 growth-box E0 扫描动作台账
#     （drain-backlog --check 每次成功运行落一行·backlog 由脚本自算·⛔不由 AI 报数）：
#     本窗口跑过 E0 且 backlog=0 → GO；backlog>0 而反哺未动 → 仍 🔴（⛔不被本增量洗白）。
#     ⛔不用 ⚪ 表示"无对象"：08 v1.4.3 定死 ⚪＝平台物理无机制，"本轮无候选"是合法完成态。
#     ⛔不替换原两本账（防退化）；fail-open：无台账件/解析失败 → 回落原判据·⚪不误标。
#   v0.11.7（2026-10-10·Hermes 童灵·L7-3 假红根治·皮叔令「符合愿景彻底根治」）：   # 版本机械载体（2026-09-26 与注入器同律：⛔版本只活在输出串/文档手写号里）
#   v0.11.7（2026-10-10·Hermes 童灵·L7-3 假红根治·皮叔令「符合愿景彻底根治」）：
#     L7-3 判据增读 kb_query_trail 动作台账（与日志#S 判据取或·符合愿景①动作即凭证）。
#     病根：原判据只认「系统日志 立场卡#S 行」=凭证层，「跑 search_kb」=动作层，两层靠
#     AI 自觉写日志串联 ⇒ 跑了没写日志=判红=「两层记账」结构缺口（D3 回合连判🔴实证）。
#     search_kb 实跑已由 _log_cli_trail→kb_query_trail.append_trail(source=cli) 落台账
#     ⇒ 判据增读该台账·动作自动转凭证·不靠记日志。⛔不替换原判据（防退化）；fail-open
#     回落纯原判据（不破坏他端/无引擎端）；source 只认 cli（注入流不算「自己跑」）。
#     验证：selftest 14/14+MUT 变异被抓；真机 L7-3 ✅做到·检索台账1(10-10 06:47)。
#   v0.11.6（2026-10-07·Hermes 童灵·你令 relay 候选1·src= 生产者字段同步面）：stamps.log
#     第1栏时间戳后插入 src= 生产者字段（relay 归因基础·⛔历史行无此字段·解析侧按 tab 位取用）。
#   v0.11.5（2026-10-06·WorkBuddy 童灵·L5 MISS 根治·皮叔令「查为何MISS：时序/字段/口径，修到连续两轮✅」·Qoder CN 方案执行）：
#     L5 对账口径切换＝doenglingz_guard_state.json **当轮行**（本会话+ts>=since 的最新行·tsl_hits 含
#     ts_l5_selfcheck=守护三查痕）。根因三查实锤：①口径——原读全局 eight_check.log 尾行，账本无
#     session 字段=跨会话串台源；②字段——守卫台账行自带 session_id+tsl_hits，是唯一「当轮可归因」
#     载体；③时序——Stop 链并行（实证 15:43 守卫行 ts 晚于树渲染 2s）→ 当轮行可能未落，加 12s 有界
#     等待，等不到降级痕账本旧口径（⛔不假红也不假绿）。配套：tsl_tree_hook 透传 --session；
#     doenglingz_guard.sh 观察层剥树行自指污染（relay 树行含「守护三查」词面=树给自己作证，必须先修
#     否则口径一切换就永久假绿）。eight_check.log 降级为无会话/无行时的 fallback（旧路径保留不删）。
#   v0.11.4（2026-10-05·Qoder CN 童灵·双源治理四期顺手根治·L7-2 第二账本形态脱钩）：
#     原正则只认 `📅 日期 | YYYY-MM-DD HH:MM`（竖线＋必带时分），而流程E 真机条目行是
#     `- 📅 日期：YYYY-MM-DD`（冒号·时分常缺）⇒ 当日真实反哺条目**永远读不到**，L7-2 连
#     "今日他方=N笔"都数不出来（表现为"今日零扫描（没写=没扫）"=把已写的账读成没写）。
#     根因不是符号选错，是**夹具照抄了解析器而不是真机**（§3.0·5「夹具须照抄真机行形状」复现）。
#     修法=分隔符两形都收（：或|）＋时分可选，无时分按 00:00 保守归他方（⛔不冒充本窗口·与扫描 log 同律）；
#     夹具补真机形态腿 S8d（冒号带时分→窗内）/S8e（冒号无时分→他方不顶账），双向对立。
#   v0.11.3（2026-09-30·皮叔令「必须根治」·L7-2 判据面缺）：原锚只有 成长箱/铁律盲区扫描.log——
#     该账本生产者=各端童灵手写（Qoder CN/ZCode·WB 端 0 写入者）且 09-27 后零更新＝死账本锚；
#     WB 端实际反哺走成长箱流程E 写 规范反哺日志.md（当日 2 条新增·判据看不见）＝面缺实锤。
#     现扩为双账本：扫描 log ∪ 反哺日志详细条目「📅 日期 | YYYY-MM-DD HH:MM」行（带时分可归因
#     窗口）——任一窗口内命中即 GO；归因三态（本窗口/他方不顶账/零）保持。自测 S8a/S8b/S8c 扩。
#   v0.11（2026-09-27 皮叔令「没做的也要有几个字说明原因·分享出去读者才不紧张」·NO-GO 机械短因）：
#   v0.10 的归因全在 detail 全文，但树行只显前26字＝外部读者只看到光秃秃"=0"。修法＝
#   NO-GO 行短因前置（机械推导·构造权仍在脚本）：「本回合未扫（他方N笔）」等事实短因进前26字，
#   全数据进明细文件。短因=事实陈述非粉饰——正是 08 v1.4.3「指名缺哪本账」立法的显形化。

def _tidy(detail, limit=26):
    """把长证据压成树行短式（呈现层），全文另存明细文件（机制层）——⛔不是删证据。

    规则确定可复算：①`[累计X] ` 前缀原样保留（tsl_closeout_guard 的口径判据靠这个标记）；
    ②先切「（」，再切「＝」，再切「·」，切到 ≤limit 就停；③还长就硬截加 …（明细文件里仍是全文）。
    """
    pre = ""
    body = detail
    if detail.startswith("[累计"):
        i = detail.find("] ")
        if i > 0:
            pre, body = detail[:i + 2], detail[i + 2:]
    for cut in ("（", "＝", "=", "·"):
        if len(body) > limit and cut in body:
            body = body.split(cut)[0].strip()
            break
    if len(body) > limit:
        body = body[:limit] + "…"
    return (pre + body) if pre else body


def _read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""

def _mtime(p):
    try:
        return os.path.getmtime(p)
    except Exception:
        return None

# ── L7 五项（v0.2 逻辑保留 + v0.3 修编号前缀盲区：LRN|TE|QD|ERR 漏了 QCN 等新端前缀，
#     致本端当日 5 条落袋被报 0=仪器假红·待入册）：正则改通用大写前缀 ──
def _log_docs(day):
    """锚点日志文件集＝day 起至今日（2026-09-26 皮叔令「做完所有工作」自查捕获 D38）。

    原实现只读 `系统日志_<since 当日>.md`：窗口跨零点后，前一晚写的条目落在另一只文件里，
    同一轮 `tsl_verify` 会报「窗口内条目=0」把真做过的事判成没做（=假红，方向与造假相反
    但同样是仪器说谎）。返 [(日期, 文本)]，缺文件跳过；⛔不猜未来日。
    """
    out = []
    d = datetime.datetime.strptime(day, "%Y-%m-%d")
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    while d <= today:
        ds = d.strftime("%Y-%m-%d")
        out.append((ds, _read(os.path.join(BASE, "工作日志/系统日志", "系统日志_%s.md" % ds))))
        d += datetime.timedelta(days=1)
    return [(ds, t) for ds, t in out if t]


# ── v0.11.8 L7-2 动作凭证源：growth-box E0 扫描台账（drain-backlog 落账）──
def _e0_trail_since(since):
    """返回 (本窗口 E0 扫描次数, 最后一次 backlog)；无台账/解析失败 → (0, None)＝fail-open 回落原判据。

    ⛔不信任 AI 自报"我扫过了"——凭证只来自脚本自己落的那行（backlog 由 drain-backlog 计算）。
    """
    p = os.environ.get("DOENGLINGZ_E0_TRAIL") or os.path.join(
        BASE, "技能配置", "growth-box", "logs", "e0_scan_trail.jsonl")
    if not os.path.isfile(p):
        return (0, None)
    try:
        import json as _json
        n, last = 0, None
        for line in open(p, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                d = _json.loads(line)
            except Exception:
                continue
            ts = str(d.get("ts", ""))[:19].replace("T", " ")
            try:
                t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except Exception:
                t = datetime.datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
            if t >= since:
                n += 1
                last = d.get("backlog")
        return (n, last)
    except Exception:
        return (0, None)


# ── v0.11.7 L7-3 动作凭证源：kb_query_trail（2026-10-10 童灵根治·符合愿景①全自动化）──
# 病根（D3 回合 TSL 连判 L7-3 🔴「今日日志无立场卡引用」·但 search_kb 明明实跑过）：
#   原判据只认「系统日志里 `立场卡…#S数字` 行」= **凭证层**。而「跑 search_kb」是**动作层**，
#   两者中间靠 AI 自觉写日志串联 ⇒ 跑了但没写日志 = 判红 = 「两层记账」结构缺口。
#   后果：① 误伤真检索（本回合实跑被红）；② 钩子已注入锚点时 AI 易以为「有卡了不用跑」更不记。
# 修法（三选里最符合愿景①的「动作即凭证」·⛔不靠我记得记账）：
#   search_kb 每次实跑已由 `_log_cli_trail`→`kb_query_trail.append_trail(source="cli")`
#   落台账（事实：本机 3641 条·末条即本回合 06:47 那次）⇒ 判据**增读该台账**，
#   与日志 #S 判据**取或**：任一命中即 GO。
#   ⚠️ 保留原判据（不替换）——防退化：若 trail 落盘坏了，日志引用仍是独立证据源；
#      两者都无才判 🔴（红着不圆·符合 TSL 纪律）。
#   ⚠️ fail-open：找不到引擎/trail ⇒ 回落纯原判据（⛔不因本增量破坏他端/无引擎端）。
def _kb_trail_path():
    """定位 kb_query_trail.jsonl（与 search_kb._pick_engine_dir 同判据·route_table.json）。"""
    for sub in ("脚本中心/知识联邦引擎", "开发工具/知识联邦引擎"):
        eng = os.path.join(BASE, sub)
        if os.path.isfile(os.path.join(eng, "route_table.json")):
            p = os.path.join(eng, "logs", "kb_query_trail.jsonl")
            if os.path.isfile(p):
                return p
    # 兜底：常见落点直查（不依赖 route_table 判据·防引擎结构差异漏读）
    for sub in ("开发工具/知识联邦引擎", "脚本中心/知识联邦引擎"):
        p = os.path.join(BASE, sub, "logs", "kb_query_trail.jsonl")
        if os.path.isfile(p):
            return p
    return ""


def _kb_trail_since(since):
    """返回本窗口(source=cli) trail 时刻列表；缺台账返回 []（fail-open 回落原判据）。"""
    p = _kb_trail_path()
    if not p:
        return []
    try:
        import json as _json
        out = []
        for line in open(p, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                d = _json.loads(line)
            except Exception:
                continue
            if d.get("source") not in ("cli", "serve"):
                continue        # 只看本端主动实跑（cli=冷路径/serve=快通道·v0.11.9 同权；inject 注入流不算「童灵自己跑」）
            try:
                t = datetime.datetime.strptime(
                    str(d.get("ts", "")), "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            if t >= since:
                out.append(t.strftime("%m-%d %H:%M"))
        return out
    except Exception:
        return []


def l7_rows(since, day, logf):
    rows = []
    ld = os.path.join(BASE, "成长箱/learnings")
    hits = []   # v0.10 归因显形：(完成时刻, 编号)——⛔只计数不显时刻=他方产出可冒充本回合产出
    if os.path.isdir(ld):
        # v0.8 D38：ID 只作锚点，是否入窗统一由 Logged 时间戳 >= since 把关。
        pat = re.compile(r'\b[A-Z]{2,5}-(\d{8})-\d{3}')
        for f in os.listdir(ld):
            fp = os.path.join(ld, f)
            if not os.path.isfile(fp):
                continue
            t = _read(fp)
            ids = set(pat.findall(t))
            if not ids:
                continue
            Lf = t.splitlines()
            for i, l in enumerate(Lf):
                if not any(x in l for x in ids):
                    continue
                # v0.3b：Logged 行在 ID 标题行**下方**（形状假设须绑实盘——v0.2 只向上搜8行致 QCN 五案全漏报）
                for j in range(max(0, i - 2), min(len(Lf), i + 10)):
                    mm = re.search(r'Logged\**\s*[:：]\s*(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})', Lf[j])
                    if mm:
                        try:
                            if datetime.datetime.strptime(mm.group(1) + " " + mm.group(2), "%Y-%m-%d %H:%M") >= since:
                                _id = next((x for x in ids if x in l), "?")
                                hits.append((mm.group(2), _id))
                        except Exception:
                            pass
                        break
    hits.sort()
    if hits:
        _d1 = "本窗口新立=%d（%s%s）" % (len(hits), "；".join("%s %s" % (t, i) for t, i in hits[:4]),
                                        "等" if len(hits) > 4 else "")
    else:
        _d1 = "本回合无新增（无新错误记录）"
    rows.append(("L7-1", "错误→成长箱", "GO" if hits else "NO-GO", _d1))
    n4 = n5 = nseal = 0
    oth4 = oth5 = 0   # v0.11：窗口外他方计数（短因素材）
    t4, t5 = [], []   # v0.10：时刻归因列表
    for day2, logt in _log_docs(day):
        L = logt.splitlines()
        blocks, cur = [], None
        for l in L:
            if re.match(r'^- \*\*完成\*\*：\d{2}:\d{2}', l.strip()):
                if cur: blocks.append(cur)
                cur = [l]
            elif cur is not None:
                cur.append(l)
        if cur: blocks.append(cur)
        for b in blocks:
            mm = re.match(r'^- \*\*完成\*\*：(\d{2}:\d{2})', b[0].strip())
            m = None
            if mm:
                try:
                    m = datetime.datetime.strptime(f"{day2} {mm.group(1)}", "%Y-%m-%d %H:%M")
                except Exception:
                    m = None
            if m and m >= since:
                n4 += 1
                t4.append(day2[-5:] + " " + mm.group(1))
                for x in b:
                    if x.startswith("- **seal**："):
                        nseal += 1
                        break
            elif m:
                oth4 += 1   # v0.11：窗口外他方条目（短因素材·显形不顶账）
        # v0.4c L7-5 行级配对：标题[童灵思考]→其后12行内首个「完成：HH:MM」>=since 才计
        for i2, l2 in enumerate(L):
            if "[童灵思考]" in l2 and l2.strip().startswith("### "):
                for l3 in L[i2 + 1:i2 + 13]:
                    mm3 = re.match(r'^- \*\*完成\*\*：(\d{2}):(\d{2})', l3.strip())
                    if mm3:
                        try:
                            m3 = datetime.datetime.strptime(f"{day2} {mm3.group(1)}:{mm3.group(2)}", "%Y-%m-%d %H:%M")
                            if m3 >= since:
                                n5 += 1
                                t5.append(day2[-5:] + " " + mm3.group(1))
                            else:
                                oth5 += 1
                        except Exception:
                            pass
                        break
    # v0.11 NO-GO 机械短因前置（≤26字内显形·全数据在 detail 后段+明细文件）：
    if n4:
        _d4 = "本窗口条目=%d·seal=%d·时刻 %s" % (n4, nseal, "/".join(t4[:5]) or "—")
    elif oth4:
        _d4 = "本回合未写（他方%d条在账·不顶账）" % oth4
    else:
        _d4 = "今日日志零条目（没写=没记·无账可查）"
    rows.append(("L7-4", "系统日志", "GO" if n4 else "NO-GO", _d4))
    if n5:
        _d5 = "本窗口[童灵思考]=%d·时刻 %s" % (n5, "/".join(t5[:5]) or "—")
    elif oth5:
        _d5 = "本回合未写反思（他方%d条·不顶账）" % oth5
    else:
        _d5 = "今日零反思条目（没写=没沉淀）"
    rows.append(("L7-5", "反思沉淀", "GO" if n5 else "NO-GO", _d5))
    # ── v0.10 L7-2 归因显形：原锚"当日有行即GO"=晨巡产出顶本回合账（当日实证）。
    #   行带时分（| YYYY-MM-DD HH:MM |…）才可判窗口；旧行只带日期=按00:00保守归"他方"。
    #   状态=本窗口口径（会话义务）；他方产出只显形不顶账（累计口径由 v0.5 双口径树接住）。
    scan = [l for l in _read(os.path.join(BASE, "成长箱/铁律盲区扫描.log")).splitlines()
            if l.startswith("| " + day)]
    in2, oth2 = [], []
    for l in scan:
        mm = re.match(r"\|\s*(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?\s*\|", l)
        if not mm:
            continue
        lbl = mm.group(2) or "无时分"
        try:
            t = datetime.datetime.strptime(day + " " + (mm.group(2) or "00:00"), "%Y-%m-%d %H:%M")
        except Exception:
            continue
        (in2 if t >= since else oth2).append(lbl)
    # ── v0.11.3 第二账本：规范反哺日志（成长箱流程E 产出·条目「📅 日期」行带时分可归因）。
    #   义务同轴：L7-2「铁律盲区反哺」的合法产出形态=跨端扫描 log ∪ 流程E 反哺条目，二者并列。
    #   窗口判定与 L7-4 同律（D38 跨零点）：t>=since 即窗内（⛔不按 day 过滤——跨零点窗含今日晨条目，
    #   实测 S8a 红抓出）；当日且窗外的计他方；历史条目（非当日且窗外）不计入防轰历史账。
    inF, othF = [], []
    for l in _read(os.path.join(BASE, "成长箱/experience/规范反哺日志.md")).splitlines():
        # v0.11.4 判据面缺根治：真账本条目行形态是 `- 📅 日期：YYYY-MM-DD`（流程E 手写·冒号·
        #   多数无时分），而原判据只认 `📅 日期 | … HH:MM`（竖线＋必带时分）＝**夹具自造形状**——
        #   夹具照抄了解析器而不是真机（§3.0·5「夹具须照抄真机行形状」的同型复现），
        #   后果=当日真实反哺条目永远 invisible，L7-2 连"他方N笔"都数不出来。
        #   修法=分隔符两形都收（：或|），时分可选；无时分按 00:00 保守归他方（⛔不顶账·与扫描 log 同律）。
        mm = re.search(r"📅\s*日期\s*[：|]\s*(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?", l)
        if not mm:
            continue
        if mm.group(2):
            try:
                t = datetime.datetime.strptime(mm.group(1) + " " + mm.group(2), "%Y-%m-%d %H:%M")
            except Exception:
                continue
        else:
            try:
                t = datetime.datetime.strptime(mm.group(1) + " 00:00", "%Y-%m-%d %H:%M")
            except Exception:
                continue
        lbl = mm.group(2) or "无时分"
        if t >= since:
            inF.append(lbl)
        elif mm.group(1) == day:
            othF.append(lbl)
    st2 = "GO" if (in2 or inF) else "NO-GO"
    if in2 or inF:
        _d2 = "本窗口扫描=%d·反哺=%d · 今日他方=扫描%d/反哺%d（不顶账）" % (
            len(in2), len(inF), len(oth2), len(othF))
    elif oth2 or othF:
        _d2 = "本回合未扫未反哺（他方：扫描%d笔/反哺%d笔·不顶账）" % (len(oth2), len(othF))
    else:
        _d2 = "今日零扫描（没写=没扫）"
    # ── v0.11.8 第三出口：E0 扫描动作凭证（⛔不替换上两本账，仅在其均为空时补位）──
    if st2 == "NO-GO":
        _n0, _b0 = _e0_trail_since(since)
        if _n0 and _b0 == 0:
            st2 = "GO"
            _d2 = "E0扫描=%d次·积压=0（无候选可反哺·动作即凭证 v0.11.8）·他方：扫描%d/反哺%d" % (
                _n0, len(oth2), len(othF))
    rows.append(("L7-2", "铁律盲区反哺", st2, _d2))
    # ── v0.10 L7-3 归因显形：原锚"当日日志含引用即GO"=他会话产出顶账。引用行归属其上方最近的
    #   「完成：HH:MM」（条目完成时刻）；遍历 _log_docs 全日文件（对齐 D38 跨零点判据·原只看当日文件）。
    in3, oth3 = [], []
    for day2, logt2 in _log_docs(day):
        last_t = None
        for l2 in logt2.splitlines():
            mm0 = re.match(r'^\s*-\s*\*\*完成\*\*：(\d{2}:\d{2})', l2.strip())
            if mm0:
                last_t = mm0.group(1)
                continue
            if last_t and re.search(r'立场卡[^\n]{0,12}?#?\s*S\d+', l2):
                try:
                    t3 = datetime.datetime.strptime(f"{day2} {last_t}", "%Y-%m-%d %H:%M")
                except Exception:
                    continue
                (in3 if t3 >= since else oth3).append(day2[-5:] + " " + last_t)
    # v0.11.7：L7-3 判据 = 日志#S引用（凭证层） ∪ kb_query_trail动作台账（动作层）·取或。
    #   ⚠️ 不替换原判据·防退化（trail 落盘坏了日志引用仍是独立源）；两者都无才 NO-GO。
    trail3 = _kb_trail_since(since)
    # v0.11.10 文案归真（2026-10-13·Qoder CN）：原 else 分支写「今日无检索凭证」，
    #   但窗口外今日实有 trail 动作时也走到该分支 ⇒ 措辞与事实不符，会误导归因
    #   （把「本回合没跑」读成「今天没人跑」）。补一个今日全量口径供分支判定。
    _trail_today = _kb_trail_since(datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
    st3 = "GO" if (in3 or trail3) else "NO-GO"
    _src3 = []
    if in3:
        _src3.append("日志引用%d" % len(in3))
    if trail3:
        _src3.append("检索台账%d(%s)" % (len(trail3), "/".join(trail3[:2])))
    if in3 or trail3:
        _d3 = ("本窗口：%s · 今日他方=%d（%s·不顶账）"
               % ("+".join(_src3), len(oth3), "/".join(oth3[:2]) or "—"))
    elif oth3 or _trail_today:
        _d3 = ("本回合未实跑（今日窗口外：日志%d处·台账%d次·⛔不顶账）"
               % (len(oth3), len(_trail_today)))
    else:
        _d3 = "今日全天零检索凭证（日志与台账双无·没跑=没检索）"
    rows.append(("L7-3", "立场卡检索", st3, _d3))
    return rows

# ── L0-L6（v0.3 新增·每层一个机械锚，无锚=⚪） ──
_SESSION = ""            # v0.11.5：main() 按 --session 置入（自测/手动无 session=空→痕账本旧口径）
_GUARD_ROW_CACHE = {}   # v0.11.5：按 (session, day) 记忆化——l0_l6_rows 被窗口/累计两口径各调一次，
                        # 守卫行只查一次（两口径的最新当轮行是同一行），⛔重复 12s 等待

def _norm_sid(sid):
    """会话号归一（对齐共脚本/守卫 v1.2 同款：触发侧带 .session.execution 后缀·Stop 侧不带）"""
    return str(sid or "").replace(".session.execution", "")

def _guard_row_l5(session, since_dt):
    """v0.11.5 L5 对账口径＝守卫台账当轮行（2026-10-06 你令·详见 __version__ 注）。

    返回 (status, detail) 或 None（无会话/无台账文件→调用方走痕账本降级路径）。
    """
    if not session:
        return None
    if not os.path.isfile(GUARD_STATE):
        return None
    import json as _json2, time as _time2
    day = since_dt.strftime("%Y-%m-%d")
    ck = (_norm_sid(session), day)
    if ck in _GUARD_ROW_CACHE:
        return _GUARD_ROW_CACHE[ck]
    deadline = datetime.datetime.now() + datetime.timedelta(seconds=12)
    rows = []
    while True:
        rows = []
        for line in _read(GUARD_STATE).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = _json2.loads(line)
            except Exception:
                continue
            if _norm_sid(d.get("session_id")) != ck[0]:
                continue
            try:
                ts = datetime.datetime.strptime(str(d.get("ts", "")), "%Y-%m-%dT%H:%M:%S")
            except Exception:
                continue
            if ts >= since_dt:
                rows.append((ts, d))
        if rows or datetime.datetime.now() >= deadline:
            break
        _time2.sleep(2)   # Stop 链并行：守卫当轮行常晚于树渲染数秒（15:43 实证 +2s）→ 有界等待
    if not rows:
        _GUARD_ROW_CACHE[ck] = None
        return None
    rows.sort(key=lambda x: x[0])
    ts, row = rows[-1]
    hits = str(row.get("tsl_hits", "") or "")
    hit = "ts_l5_selfcheck" in [h for h in hits.split(",") if h]
    _t = ts.strftime("%H:%M:%S")
    if hit:
        res = ("GO", "守卫当轮行(%s)含守护三查痕·对账口径=guard_state当轮行" % _t)
    else:
        res = ("NO-GO", "守卫当轮行(%s)无守护三查痕·收口前补🧪 8要素行" % _t)
    _GUARD_ROW_CACHE[ck] = res
    return res


def l0_l6_rows(since, src="unknown"):
    rows = []
    core_rules = _read(os.path.join(QCN_RULES, "doenglingz-core.md"))
    go0 = bool(core_rules) and any(os.path.isfile(os.path.join(BASE, d, "doenglingz_inject_prompt.py")) for d in ("开发工具", "脚本中心/分身", "脚本中心"))  # B3中心直址双看·旧单径判据必假(L0假红) 2026-10-16
    rows.append(("L0", "接入态", "GO" if go0 else "NO-GO", "锚=rules/doenglingz-core.md非空+W1注入脚本在位（文件级）"))
    go1 = all(os.path.isfile(os.path.join(QCN_RULES, f)) for f in ("core-identity.md", "core-soul.md", "core-user.md"))
    rows.append(("L1", "身份感知", "GO" if go1 else "NO-GO", "锚=三恒驻身份文件存在（文件级·注入生效归inject_chain_guard另腿）"))
    go2 = ("身份骨架" in core_rules) and ("L6" in core_rules)
    rows.append(("L2", "规则加载", "GO" if go2 else "NO-GO", "锚=doenglingz-core含「身份骨架」+「L6」段标题（内容级）"))
    _dfiles = [f for f in _declare_files() if _declare_src_match(f, src)]
    _dst = "".join(_read(f) for f in _dfiles)
    today = since.strftime("%Y-%m-%d")
    _srcref = "" if (not src or src == "unknown") else f"·端={src}"
    if not any(_read(f) for f in _dfiles):
        l3, d3 = "⚪", "声明台账均不可读（无机械证据·非通过）"
    elif today in _dst:
        l3, d3 = "GO", f"锚=declare台账当日在（读面{len(_dfiles)}端聚合{_srcref}·仅档位标签可机检·仪式全文未覆盖如实声明）"
    else:
        l3, d3 = "🟡", f"锚=declare台账当日无记录（聚合{len(_dfiles)}端{_srcref}·待核·不判过）"
    rows.append(("L3", "上岗仪式", l3, d3))
    # v0.4 L4 上色（皮叔令「欠装的两台检查机造出来」2026-09-23）：W3 留痕台账在位，⚪ 退役
    lw3all = [l for l in _read(W3_LEDGER).strip().splitlines() if since.strftime("%Y-%m-%d") in l]
    # v0.7 L4 分口径（2026-09-26 自查：本日 L4 显示 180 笔，实为我的 dryrun/探针灌出来的——
    #   判据"注入器在跑"被自测污染成虚高绿＝PAT-058 同型）。只有带会话号的行才算真回合证据，
    #   无号行单列显形，⛔不静默丢弃（丢了就看不出曾经被灌过）。
    import json as _json
    _real = _probe = _legacy = _bad = 0
    # 测试标签集：这些 host/src 是本日手工跑 `--prompt` 留下的，不是端上回合（新增测试标签须同步这里，
    # ⛔不靠"无号即探针"猜——字段上线前的真实回合行同样无号，混为一谈＝把历史真行说成假数据）
    _TEST_HOSTS = {"dryrun", "probe-only", "x", "len-probe", "selftest"}  # ⛔不放端名（未来某端可能合法传 --src qoder-cn，宁可少认探针也不误判真行）
    for _l in lw3all:
        try:
            _d = _json.loads(_l)
        except Exception:
            _bad += 1
            continue
        _h = str(_d.get("host") or _d.get("src") or "")
        if str(_d.get("session_id") or ""):
            _real += 1
        elif _h in _TEST_HOSTS:          # 自测/探针灌入（可指名）
            _probe += 1
        else:                             # 无号且非测试标签＝字段上线前的历史行，⛔不冒充"自测灌的"也不冒充真回合
            _legacy += 1
    if not lw3all:
        rows.append(("L4", "域切片", "NO-GO", "W3留痕台账今日零笔=注入器没在记账（机器已装·账本空=没跑，不是没装）"))
    elif _real == 0:
        rows.append(("L4", "域切片", "NO-GO", f"W3今日{len(lw3all)}笔无一带会话号（探针{len(lw3all) and _probe}·字段上线前行{_legacy}＝均不作真回合证据）"))
    else:
        _tail = ("·另探针%d/上线前行%d/坏行%d笔不计" % (_probe, _legacy, _bad)) if (_probe + _legacy + _bad) else ""
        rows.append(("L4", "域切片", "GO", f"W3台账今日真回合{_real}笔{_tail}·注入器在跑（AI自报不再是唯一证据源）"))
    sm = [_mtime(os.path.join(SLICES, f)) for f in os.listdir(SLICES)] if os.path.isdir(SLICES) else []
    sm = [x for x in sm if x]
    xm = _mtime(SSOT)
    if sm and xm:
        fresh = max(sm) >= xm
        # v0.4 L5 上色：🧪痕账本（closeout v0.5 eight_check.log 每轮 OK/MISS）
        # v0.11.5 主判据改守卫当轮行（--session 在场时）；痕账本降级为 fallback
        ec = [l for l in _read(os.path.join(CACHE, "eight_check.log")).strip().splitlines() if since.strftime("%Y-%m-%d") in l]
        if not fresh:
            l5, d5 = "NO-GO", "切片落后于规格书（重跑k2生成器）"
        else:
            _g = _guard_row_l5(_SESSION, since)
            if _g is not None:
                l5, d5 = _g
            elif not ec:
                l5, d5 = "NO-GO", "🧪痕账本今日零笔=痕检查器没跑过（今晚Stop链首响后应有账·新装机制观察窗）"
            elif "MISS" in ec[-1]:
                l5, d5 = "NO-GO", "痕账本最近=MISS·收口前补🧪 8要素行（缺痕轮见violations.log）"
            else:
                l5, d5 = "GO", f"新鲜度OK+痕账本今日{len(ec)}笔·最近={ec[-1].split(chr(9))[-1]}"
    else:
        l5, d5 = "⚪", "切片/规格书 mtime 不可得"
    rows.append(("L5", "守护三查", l5, d5))
    # ── L6 分身同步（v0.11.10·2026-10-19 你「就这样改吧」）────────────────────
    # 判据源换成端账本 state_bus.json（watcher 每轮写回），⛔ 不再问 launchctl：
    #   那是 mac 专属的「进程活着吗」，而本层要答的是「我的分身在各工具新不新、要不要你动手」。
    #   换源附带根除跨平台缺口，JSON 谁都能读，⛔ 无需平台分支（旧「launchctl 不可达」即缺该分支的病）。
    # 状态词刻意不走 SYM0（「✅做到/🔴没做」＝把机器干的活记成 AI 的成绩·立场卡 S925 截断线）。
    # 合格线（08 §五·v1.7.7）：3 秒内答出「新不新」「要不要动手」；取证细节下沉明细文件。
    import json as _json
    _BUS = os.path.join(BASE, "数字分身", "state_bus.json")
    _err = ""
    _bus_doc = {}
    try:
        _bus_doc = _json.load(open(_BUS, encoding="utf-8")) or {}
        _ends = _bus_doc.get("ends", {})
    except Exception as _e:
        _ends = None
        _err = type(_e).__name__
    # 账本超龄阈值单源化（2026-10-19 Q3·方案①）：读账本 l6_policy.stale_days（写者=state_bus_sync
    # --update·真源 BASELINE_MAX_AGE_DAYS）；账本未含该块时 fallback=3 与旧值等价，⛔勿在此调值。
    _STALE_DAYS = (_bus_doc.get("l6_policy") or {}).get("stale_days", 3)
    if not _ends:
        rows.append(("L6", "分身同步", "⚪", "本机未启用自动同步（改完分身说一句「更新分身切片」即可）"
                     + (("·%s" % _err) if _ends is None else "")))
    else:
        import datetime as _dt
        _bad = [v.get("name") or k for k, v in _ends.items() if v.get("status") == "out_of_sync"]
        _ok = sum(1 for v in _ends.values() if v.get("status") == "in_sync")
        _idle = sum(1 for v in _ends.values() if v.get("status") in ("pending", "ignored"))
        _when = max([v.get("last_verified") or "" for v in _ends.values()])
        try:
            _age = (_dt.datetime.now() - _dt.datetime.strptime(_when, "%Y-%m-%d %H:%M")).days
        except Exception:
            _age = None
        if _bad:
            _d1 = "%d 个工具还是旧版：%s" % (len(_bad), "、".join(_bad[:4]))
            _d1 += "｜说一句「更新分身切片」即可修"
        elif _age is not None and _age > _STALE_DAYS:
            _d1 = "账本 %d 天没更新（守望可能停摆）→ 查 数字分身/scripts/doenglingz_slice_watch.log" % _age
        else:
            _d1 = "%d 个工具都是最新版" % _ok
            if _idle:
                _d1 += "（另有 %d 个未接入/不纳管，不计）" % _idle
        _st = "🔴" if _bad else ("🟡" if (_age is not None and _age > _STALE_DAYS) else "✅")
        rows.append(("L6", "分身同步", _st, _d1 + "｜末核 %s" % (_when or "?")))
    return rows

SYM0 = {"GO": "✅做到", "NO-GO": "🔴没做", "🟡": "🟡存疑", "⚪": "⚪查不了"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--full", action="store_true", help="渲染 L0-L7 全层树（v0.3）")
    ap.add_argument("--session", default="", help="本会话 session_id（v0.11.5·L5 对账口径=守卫当轮行；缺省走痕账本旧口径）")
    ap.add_argument("--self-test", action="store_true",
                  help="锚点回归自测（D38 跨零点·2026-09-27 补装·夹具整根重定向）")
    ap.add_argument("--mutant", action="store_true", help="配合 --self-test：短路判据验探针可证伪")
    # v0.11.6（2026-10-07 童灵落·relay 层失守候选1）：生产者字段——多端共写 stamps.log 此前无 src，
    #  肇事端归属判不了（脚本 L114 注释自承盲区）。加字段后「谁产的树」可机械归因，
    #  为候选2（哈希全文 diff）/候选3（去 relay 化）铺路。缺省=unknown（⛔不猜端名，宁可显式未知）。
    ap.add_argument("--src", default="unknown", help="生产者端名（如 workbuddy/qodercn/traework）·写入 stamps.log 归因字段")
    # 自测先于 parse：--since 是必填项，自测不需要它（⛔不为了跑测试编一个假 since）
    if "--self-test" in sys.argv:
        return _self_test()
    a = ap.parse_args()
    if "--self-test" in sys.argv:
        return _self_test()
    try:
        since = datetime.datetime.strptime(a.since, "%Y-%m-%d %H:%M")
    except ValueError:
        print("参数错误：--since 须 'YYYY-MM-DD HH:MM'")
        return 2
    day = since.strftime("%Y-%m-%d")
    logf = os.path.join(BASE, "工作日志/系统日志", "系统日志_%s.md" % day)
    # ── v0.5 双口径树（2026-09-26 皮叔令「我一定要根治」·根治面=口径定义权）──
    #   病根：v0.2-v0.4 把「树的构造权」交给了脚本，但「口径」仍留在 AI 手里——
    #   --since 由 AI 自填、且脚本只出一个口径 ⇒ AI 可以在树外自己补一句「当日累计口径两项均 ✅」
    #   把脚本给的🔴在叙述里翻成✅。stamp 虽含 since，但 guard 不做逐行比对（其注释自陈"绑验暂缺"），
    #   所以换窗口/加叙述这两条路全程无判据覆盖。
    #   根治＝把两个口径都变成脚本的行：会话窗口 + 当日累计同时在场、同绑进一个 stamp，
    #   AI 不再需要"自己声明累计口径"——需求消失比检测话术可靠（文本判据挡不住换一种说法）。
    since_day = datetime.datetime.strptime(day + " 00:00", "%Y-%m-%d %H:%M")
    global _SESSION
    _SESSION = _norm_sid(a.session)   # v0.11.5：L5 守卫当轮行对账的会话锚（l0_l6_rows 内消费）
    def _build(sc):
        return (l0_l6_rows(sc, getattr(a, "src", "unknown")) + l7_rows(sc, day, logf)) if a.full else l7_rows(sc, day, logf)
    rows_s, rows_d = _build(since), _build(since_day)
    dmap = {n: (st, dt) for n, _nm, st, dt in rows_d}
    merged, same = [], 0
    # B21修复(2026-10-06 你两问树跳号): L7-x按编号序渲染·其余保持插入序·只动渲染序不动判据
    rows_s = [r for r in rows_s if not r[0].startswith('L7-')] + sorted([r for r in rows_s if r[0].startswith('L7-')], key=lambda x: x[0])
    for n, name, st, detail in rows_s:
        st2 = dmap.get(n, ("?", ""))[0]
        if st == st2:
            same += 1
            merged.append((n, name, st, detail))
        else:
            merged.append((n, name, st, "[累计%s] %s" % (SYM0.get(st2, st2), detail)))
    rows = merged
    ng = sum(1 for _, _, st, _ in rows if st == "NO-GO")
    nz = sum(1 for _, _, st, _ in rows if st in ("⚪", "🟡"))
    # v0.3c 显示修正（你指正：GO/NO-GO 纯文字违反 08 §七 跨端固定视觉「✅状态」正典——
    #   修仪器不等于可以换刻度盘，状态一律渲染正典符号：✅GO/🔴NO-GO/🟡待核/⚪无锚）
    # v0.4 文案定稿（你两条拍板 2026-09-23：①"没做"保留🔴不换❌ ②"没查"禁"没长眼"式残疾话术——
    #   能做未做=欠条归因为🔴；只有平台物理无机制才许⚪查不了且须附边界依据。语义判定不动，只换刻度盘字样）
    SYM = {"GO": "✅做到", "NO-GO": "🔴没做", "🟡": "🟡存疑", "⚪": "⚪查不了"}   # "须附平台边界依据"进明细，⛔不占树行
    # v0.5 调整（2026-09-26 读 §七/§九 后自纠）：口径信息原先占一行 ├─ ，犯两处——
    #   ①破坏 08 §七「跨端固定视觉标准（2026-09-13 锁定）」的树形（模板里没有这一行）；
    #   ②垫高 tsl_closeout_guard「├─ 行数<12 判截断」的计数基准——多占一行＝真漏一层也能凑够 12 行。
    #   改法：口径并入 🧾 首行（非树体），树体行数恢复与模板一致。
    tree = ["├─ 层 状态 判定依据（AI说的不算，账本里的才算）"]
    _details = []
    # B21修复(2026-10-06 你两问树跳号): L7-x按编号序渲染·其余保持插入序·只动渲染序不动判据
    rows = [r for r in rows if not r[0].startswith('L7-')] + sorted([r for r in rows if r[0].startswith('L7-')], key=lambda x: x[0])
    for n, name, st, detail in rows:
        short = _tidy(detail)
        tree.append("├─ %s %s %s %s" % (n, name, SYM.get(st, st), short))
        if short != detail:
            _details.append("%s %s｜%s｜%s" % (n, name, SYM.get(st, st), detail))
    tree.append("└─ 结论：🔴没做%d件 · ⚪查不了%d件 · 其余✅各自有账（红着不圆）" % (ng, nz))
    stamp = hashlib.sha256(("\n".join(tree) + since.strftime("%Y%m%d%H%M")).encode()).hexdigest()[:8]
    head = ["🧾 TSL 机械核验 %s · since=%s%s" % (__version__, a.since, " · FULL" if a.full else ""),
            # v0.11.2（2026-09-27 皮叔令「大白话·一堆数看着迷糊」）：🧮行去数字化——机器细节
            # （窗口/累计时间戳、N/12 分数）退出树头；since 仍在 🧾 行与 stamps.log 第5栏（机器锚无损），
            # [累计] 前缀仍在树体（AI/绑验消费无损）。人只看人话，机器照旧对账。
            "🧮 口径（脚本产出·AI ⛔不得自造）：树里每行都按两把尺子各量了一遍——「眼前这回合做了吗」和「今天全天有没有人做」；"
            "两把尺子答案不同的共 %d 行（就是树里带[累计]标签的那几行）·正常分工·谁都不用处理"
            % (len(rows) - same)]
    out = head + tree + ["🔏 TSL-stamp %s" % stamp]
    print("\n".join(out))
    # v0.10 第六腿·人话总结行（树外·不进 last_tree.txt 绑验体）：你看一眼即知"本回合真做了什么"，
    # 他方产出显形"不顶账"——质证动作由机制前置回答，不再依赖你逐条问。
    done = [n for n, _nm, st, _dt in rows if st == "GO"]
    oth = []
    for n, _nm, st, _dt in rows:
        # v0.11：短因措辞有"他方N条/处"两种形态（无等号）——正则去掉等号兼容
        _m = re.search(r"他方(\d+)", _dt or "")
        if st != "GO" and _m and int(_m.group(1)) > 0:
            oth.append("%s他方%s" % (n, _m.group(1)))
    _sum = "📌 归因总览：本窗口✅=%s · 他方产出不顶账=%s · ⚪无锚=%d" % (
        ",".join(done) or "无", ";".join(oth) or "无", nz)
    out.append(_sum)
    print(_sum)
    try:
        os.makedirs(CACHE, exist_ok=True)
        open(os.path.join(CACHE, "last_tree.txt"), "w", encoding="utf-8").write("\n".join(tree) + "\n🔏 TSL-stamp %s\n" % stamp)
        # v0.6 章树绑定（2026-09-26 皮叔令「TSL 不能再出错」）：
        #   v0.2 注释自陈「树 body 与 stamp 的逐行 hash 绑验暂缺」⇒ 只验章真不验树同，
        #   留有两条活路：抄真章改某行、拿另一棵更绿的树配这枚章。此处补齐：
        #   stamps.log 第3栏起记「行数\t树体指纹」，并把该 stamp 的树体单独存档供守卫比对。
        tsha = hashlib.sha256("\n".join(tree).encode("utf-8")).hexdigest()[:8]
        tdir = os.path.join(CACHE, "trees")
        os.makedirs(tdir, exist_ok=True)
        open(os.path.join(tdir, "%s.txt" % stamp), "w", encoding="utf-8").write("\n".join(tree))
        # v0.8 明细：树行被短式化的层，其完整判据原文按章号存档（⛔好看不得吃证据）
        if _details:
            open(os.path.join(tdir, "%s.detail.txt" % stamp), "w", encoding="utf-8").write(
                "\n".join(_details) + "\n")
            out.append("📄 明细（长判据全文·不在树里）：%s"
                       % os.path.join(tdir, "%s.detail.txt" % stamp))
            print(out[-1])   # 只补一行指针；整棵树已在前面 print 过，⛔不重复打第二遍
        with open(os.path.join(CACHE, "stamps.log"), "a", encoding="utf-8") as _f:
            # v0.11.6：第1栏时间戳后插入 src= 生产者字段（候选1·relay 归因基础）。
            # ⛔ 历史行无此字段，解析侧须容忍（按 tab 位取用，勿假设固定列序）。
            _f.write("%s\tsrc=%s\t%s\t%d\t%s\twindow=%s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                              a.src, stamp, len(tree), tsha, a.since))
    except Exception:
        pass
    return 1 if ng else 0

def _self_test():
    """回归用例（2026-09-27·皮叔令「做完所有工作」轮补装·D35 缺口）。

    夹具整根重定向（BULUOTU_BASE 语义·不写真档案）；变异模式见 --self-test --mutant。
    """
    import shutil
    import tempfile
    global BASE
    td = tempfile.mkdtemp(prefix="tslverify_st_")
    real_base = BASE
    d1 = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    d2 = datetime.datetime.now().strftime("%Y-%m-%d")
    logdir = os.path.join(td, "工作日志/系统日志")
    os.makedirs(logdir)
    # 前一日 22:30 一条 + 当日 02:10 一条 = 跨零点窗口应计 2 条；各带一条立场卡引用（L7-3 归因夹具）
    open(os.path.join(logdir, "系统日志_%s.md" % d1), "w", encoding="utf-8").write(
        "### 昨夜条目\n- **完成**：22:30\n- **结论**：引用 立场卡#S042 判据\n- **seal**：aaa\n")
    open(os.path.join(logdir, "系统日志_%s.md" % d2), "w", encoding="utf-8").write(
        "### 今晨条目A\n- **完成**：00:05\n- **结论**：引用 立场卡#S034 判据\n- **seal**：ccc\n"
        "### 今晨条目B\n- **完成**：02:10\n- **结论**：引用 立场卡#S993 判据\n- **seal**：bbb\n")
    # 夹具目录先建再写（首跑两次失败：NameError io → 上级目录不存在·当场暴露当场修）
    os.makedirs(os.path.join(td, "成长箱/learnings"), exist_ok=True)
    # 扫描 log 夹具：d1 旧行（无时分·按00:00=他方）+ d2 新行 07:00（可判窗口）
    open(os.path.join(td, "成长箱/铁律盲区扫描.log"), "w", encoding="utf-8").write(
        "| %s | WB | 1 | 旧行无时分\n| %s 07:00 | WB | 1 | 新行带时分\n" % (d1, d2))
    BASE = td
    orig_docs = _log_docs

    def run(sc_day, sc_hm, day):
        since = datetime.datetime.strptime(sc_day + " " + sc_hm, "%Y-%m-%d %H:%M")
        rows = l7_rows(since, day, os.path.join(logdir, "系统日志_%s.md" % day))
        return {n: (st, _dt) for n, _nm, st, _dt in rows}
        return d

    try:
        r_cross = run(d1, "22:05", d1)      # 窗口跨零点
        r_same = run(d2, "00:30", d2)       # 窗口全在今日
        l2_pre = r_cross["L7-2"]            # v0.11.3：反哺日志写入前的 L7-2 前态（纯扫描单源）
        # v0.11.3 第二账本夹具（流程E 形态·📅 日期行带时分）：d1 12:00 窗外 + d2 07:00 窗内
        os.makedirs(os.path.join(td, "成长箱/experience"), exist_ok=True)
        open(os.path.join(td, "成长箱/experience/规范反哺日志.md"), "w", encoding="utf-8").write(
            "| 📅 日期 | %s 12:00 |\n| 📅 日期 | %s 07:00 |\n" % (d1, d2))
        r_cross = run(d1, "22:05", d1)      # 反哺入账后重跑（双源态）
        r_same = run(d2, "00:30", d2)
        # v0.11.4 真机形态腿：流程E 手写条目实际长这样（**冒号**·时分常缺）——
        #   ⛔ 夹具照抄解析器造的形状（竖线必带时分）会让"真账本读不到"这件事永不被测。
        open(os.path.join(td, "成长箱/experience/规范反哺日志.md"), "w", encoding="utf-8").write(
            "- 📅 日期：%s 23:30\n- 📅 日期：%s\n" % (d2, d2))
        r_shape = run(d2, "00:30", d2)      # 带时分行=窗内；无时分行=按00:00归今日他方（不顶账）
        def cnt(note):   # 从"窗口内条目=N"里取 N，按精确条数断言（⛔只断 GO/NO-GO 会漏掉少算）
            i = note.find("条目=")
            return note[i + 3:].split("·")[0] if i >= 0 else "?"
        # v0.11.8 第三出口用例：先把两本账都清成"本窗口皆无"，再单独加 E0 凭证
        #   （早前夹具往扫描 log 写过窗内行·⛔不清就顶掉 S9b/S9c 的 NO-GO 预期＝夹具污染用例）
        open(os.path.join(td, "成长箱/铁律盲区扫描.log"), "w", encoding="utf-8").write(
            "| %s 00:04 | 夹具 | 0 | 窗外旧扫描行（他方·不顶账） |\n" % d1)
        open(os.path.join(td, "成长箱/experience/规范反哺日志.md"), "w", encoding="utf-8").write(
            "- 📅 日期：%s 00:05\n" % d1)          # 窗外旧条目（他方·不顶账）
        _tp = os.path.join(td, "e0_trail.jsonl")
        os.environ["DOENGLINGZ_E0_TRAIL"] = _tp
        open(_tp, "w", encoding="utf-8").write(
            '{"ts": "%s 00:31", "backlog": 0, "alarm": false, "src": "qodercn"}\n' % d2)
        r_e0 = run(d2, "00:30", d2)                # 窗内凭证·backlog=0 → 应 GO
        open(_tp, "w", encoding="utf-8").write(
            '{"ts": "%s 00:31", "backlog": 3, "alarm": true, "src": "qodercn"}\n' % d2)
        r_e0b = run(d2, "00:30", d2)               # 有积压未反哺 → 必仍 🔴（⛔洗白）
        _tp2 = os.path.join(td, "e0_none.jsonl")
        os.environ["DOENGLINGZ_E0_TRAIL"] = _tp2   # 无凭证文件 → 回落原判据（防恒真）
        r_e0c = run(d2, "00:30", d2)
        os.environ.pop("DOENGLINGZ_E0_TRAIL", None)
        cases = [
            ("S9a L7-2 E0凭证窗内且backlog=0 → GO(第三出口)", r_e0["L7-2"][0], "GO", r_e0["L7-2"][1]),
            ("S9b L7-2 E0凭证backlog>0未反哺 → 必仍NO-GO(不洗白)", r_e0b["L7-2"][0], "NO-GO", r_e0b["L7-2"][1]),
            ("S9c L7-2 无E0凭证 → 回落原判据NO-GO(防恒真)", r_e0c["L7-2"][0], "NO-GO", r_e0c["L7-2"][1]),
            ("S1 跨零点窗口计三日", cnt(r_cross["L7-4"][1]), "3", r_cross["L7-4"][1]),
            ("S2 窗口只在今日计一条", cnt(r_same["L7-4"][1]), "1", r_same["L7-4"][1]),
            ("S3 L7-4 状态随条目存在为 GO", r_cross["L7-4"][0], "GO", r_cross["L7-4"][1]),
            # v0.10 第六腿归因用例：
            ("S4a L7-2 窗口外扫描不顶账(跨零点窗·前态)", l2_pre[0], "NO-GO", l2_pre[1]),
            ("S4b L7-2 窗口内带时分扫描算产出", "本窗口扫描=1" in r_same["L7-2"][1], True, r_same["L7-2"][1]),
            ("S8a L7-2 反哺日志窗口内命中即GO(双源)", r_cross["L7-2"][0] == "GO" and "反哺=1" in r_cross["L7-2"][1], True, r_cross["L7-2"][1]),
            ("S8b L7-2 双账本同窗各自计数", "本窗口扫描=1·反哺=1" in r_same["L7-2"][1], True, r_same["L7-2"][1]),
            ("S8c L7-2 窗外反哺他方不顶账", "今日他方=扫描1/反哺1" in r_cross["L7-2"][1], True, r_cross["L7-2"][1]),
            ("S8d L7-2 真机冒号带时分=窗内命中", r_shape["L7-2"][0] == "GO" and "本窗口扫描=1·反哺=1" in r_shape["L7-2"][1], True, r_shape["L7-2"][1]),
            ("S8e L7-2 真机冒号无时分=保守归他方(不冒充本窗口)", "今日他方=扫描0/反哺1" in r_shape["L7-2"][1], True, r_shape["L7-2"][1]),
            # v0.11.7：_d3 格式改「本窗口：日志引用N+检索台账M(...) · 他方=K」⇒ 断言同步
            ("S5a L7-3 跨日三引用都入窗", "日志引用3" in r_cross["L7-3"][1], True, r_cross["L7-3"][1]),
            ("S5b L7-3 窗外引用显形他方不顶账", "他方=1" in r_same["L7-3"][1] and "日志引用1" in r_same["L7-3"][1], True, r_same["L7-3"][1]),
            ("S6 L7-4 时刻归因显形", "22:30" in r_cross["L7-4"][1], True, r_cross["L7-4"][1]),
            ("S7 NO-GO 机械短因前置", l2_pre[1].startswith("本回合未扫"), True, l2_pre[1]),
        ]
        bad = 0
        print("=== tsl_verify 锚点回归（D38 跨零点）===")
        for name, got, want, note in cases:
            ok = (got == want)
            bad += 0 if ok else 1
            print("  %s %-22s 期望=%s 实得=%s（%s）" % ("✅" if ok else "❌", name, want, got, note))
        # v0.11.4 变异段**默认执行**（§3.9 红线：出厂第一个跑的是变异测试，不是自测）——
        #   旧写法把探针藏在 --mutant 之后，而聚合器只跑 `--self-test` ⇒ "变异跑过"永远无痕迹，
        #   本件因此长期挂 🔴「新守卫缺变异自检」（该红按设计正确：无标记＝无证据）。
        #   --mutant 保留为兼容别名（行为与默认一致·⛔不新增开关面）。
        if True:
            # 变异1：_log_docs 退回"只读 since 当日文件"（即 D38 修前的行为）→ S1 必须转红
            def mutant(day):
                return [(day, _read(os.path.join(logdir, "系统日志_%s.md" % day)))]
            globals()['_log_docs'] = mutant
            rm = run(d1, "22:05", d1)
            # 变异体应把昨夜那条漏掉（少算 1 条＝假红方向），实跑得"条目=1"才算抓到
            caught = cnt(rm["L7-4"][1]) == "1"
            globals()['_log_docs'] = orig_docs
            print("  %s MUT1 退回单文件 → 昨夜条目被漏计（实得=%s）" % ("✅" if caught else "❌", rm["L7-4"][1]))
            # 变异2（v0.10）：_log_docs 返回空 → 全 L7 日志锚必须转 🔴（证伪"GO 恒真"）
            globals()['_log_docs'] = lambda day: []
            rm2 = run(d2, "00:30", d2)
            caught2 = (rm2["L7-4"][0] == "NO-GO") and (rm2["L7-3"][0] == "NO-GO")
            globals()['_log_docs'] = orig_docs
            print("  %s MUT2 空日志 → L7-3/L7-4 转🔴（实得=%s/%s）" % (
                "✅" if caught2 else "❌", rm2["L7-4"][0], rm2["L7-3"][0]))
            print("变异判定：%s（未抓到＝本探针恒真·作废）" % ("被抓" if (caught and caught2) else "未抓"))
            _mut = bool(caught and caught2)
        else:
            _mut = True                      # 显式跑过变异才可能为 False（本分支不可达·留作回落声明）
        print("合计 %d/%d 过（分母由 len(cases) 实算）＋变异%s" % (
            len(cases) - bad, len(cases), "被抓" if _mut else "未抓·探针作废"))
        # §3.9 承接标记（guard_selftest_check classify_mut 消费）：⛔留在 try 内——
        #   中途抛异常则标记不落＝聚合器按"未承接"归因本件（Fail-Closed·不自证式假绿）
        print("  %s MUT:%s 两枚探针（MUT1 退回单文件漏计／MUT2 空日志转🔴）均翻转"
              % ("✅" if _mut else "❌", "OK" if _mut else "FAIL"))
        print("判定：%s" % ("✅ 全过（变异自检已在默认路径内跑完）"
                          if (bad == 0 and _mut) else "❌ 有红或探针不响·⛔不得落地"))
        return 0 if (bad == 0 and _mut) else 1
    finally:
        BASE = real_base
        globals()['_log_docs'] = orig_docs
        shutil.rmtree(td, ignore_errors=True)


if __name__ == "__main__":
    _rc = main()
    try:
        os.makedirs(CACHE, exist_ok=True)
        open(os.path.join(CACHE, "last_run.txt"), "w", encoding="utf-8").write(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\t" + " ".join(sys.argv[1:]) + "\texit=%d" % _rc + "\n")
    except Exception:
        pass
    sys.exit(_rc)
