#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/tsl_closeout_guard.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""tsl_closeout_guard.py — TSL 收尾守卫（腿3·观察层·2026-09-21·v1.1 2026-10-09 Qoder 任务卡六改点⑥联动 tree_hook 当回合真跑证据）

判据（你三问根治）：回合回复输出了 TSL 验证清单（树状特征 `├─ L0`/`TSL会话评级`）
却**没有跑 tsl_verify.py**（~/.cache/tsl_verify/last_run.txt 缺失或早于本回合起点）
→ 违规留痕 w1_not_honored（不阻断·观察层，对齐 tsl_hits 口径）。

为什么是"必须跑校验器"而不是"必须全 GO"：TSL 的可信度来自**脚本说了算**，
AI 只许 relay——全 GO 不是义务，跑校验器才是义务。

诚实边界：纯 AI 环境无绝对杜绝——AI 可以不跑校验器，但绕过必留痕（本守卫的职责）。
输入：Stop hook JSON（stdin）·需 transcript_path；输出：stdout 仅在违规时告警。
退出码：恒 0（观察层·不阻塞 Stop）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import sys,os,json
for _p in (os.path.dirname(os.path.abspath(__file__)),  # 同目录自推导（用户侧=脚本中心·transcript_reader 同部署面·2026-09-30 by ZCode）
           os.path.expanduser("[记忆共享中心]/脚本中心"), os.path.expanduser("[记忆共享中心]/脚本中心")):  # 2026-10-04 修脱敏残留：原两项均为开发工具(重复)，第二项应为脚本中心(端用户部署面兜底)
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
import transcript_reader as _tr  # 跨端解析·单一真源（2026-09-23 童灵根治）
# v1.0 档位判据（2026-10-05 童灵代行·根治 TSL 禁令失效四犯）：
#   档位函数复用 tsl_tree_hook 同名实现（⛔不复制粘贴——复制=第二本账=混合态根因）。
#   导入失败→降级为无门控（保守侧：不假红，也不假装覆盖）。
try:
    from tsl_tree_hook import session_d_tier as _session_d_tier
except Exception:
    _session_d_tier = None
FRESH_WINDOW_SEC = 600  # stamp 时间戳落在此窗口内 = 本回合产物（非 D3 档树义务为零 ⇒ 只可能是 AI 自跑）
CACHE = os.environ.get("TSL_VERIFY_CACHE") or os.path.expanduser("~/.cache/tsl_verify")
   # ^ 2026-09-26 补测试缝：自测/探针须可整根重定向缓存根，否则夹具会往真 stamps.log/eight_check.log 里写条目（本轮实测污染过 1 条假 stamp，已删）。
__version__ = "v1.1"   # 版本机械载体（2026-09-26 与注入器同律：⛔版本只活在文档手写号里）· v1.0 腿1 档位门控（2026-10-05 童灵代行）· v1.1 change⑥联动 tree_hook 当回合真跑证据（2026-10-09 Qoder 任务卡：⛔把 hook 代跑判成假红）
def _narration_vs_tree(text, tree_text):
    """v0.7 口径来源判据（2026-09-26 皮叔令「我一定要根治」）。

    抓的不是"话说得绿"，而是**引用了脚本没给过的口径**：
      ① 回复出现"累计…✅"而树内该层没有 `[累计✅做到]` 标记 → 口径系 AI 自造；
      ② 回复出现"两项均 ✅/均 ✅/全 ✅"式总括，而树内仍有 🔴没做 → 叙述与树不一致。
    观察期只留痕不阻断（§3.4 呈现格式禁拦律：判据对象是文本表面形态的件不得拦链）。
    """
    import re
    v = []
    lay = {}
    for l in tree_text.splitlines():
        m = re.match(r"^[├└─│\s]*(L\d(?:-\d)?)[^\n]*?\s(✅做到|🔴没做|🟡存疑|⚪查[^ ]*)", l)
        if m:
            lay[m.group(1)] = (m.group(2), "[累计✅做到]" in l, l)
    for m in re.finditer(r"(L\d(?:-\d)?)[^\n]{0,28}?(累计[^\n]{0,14}✅|均 ✅|两项均 ✅|全部 ✅)", text):
        lid, frag = m.group(1), m.group(2)
        if lid not in lay:
            continue
        st, has_cum, _ = lay[lid]
        if "累计" in frag and not has_cum:
            v.append("叙述自造累计口径：%s 树内=%s 无[累计✅做到]标记，回复片段=%r" % (lid, st, frag))
        elif frag.startswith(("均 ", "两项均", "全部")) and st == "🔴没做":
            v.append("叙述翻绿：%s 树内🔴没做，回复却称 %r" % (lid, frag))
    return v


def _tree_binding(text, cache=None):
    """v0.8 章树绑定（2026-09-26 皮叔令「TSL 不能再出错」·补 v0.2 自陈"绑验暂缺"）。

    抓三件事：①抄真章改某行（回复层状态与存档不符）②拿另一棵更绿的树配这枚章
    ③选择性呈现（回复缺层）。比对容忍空白差异，只比"层名↔状态词"。
    观察期只留痕不阻断（§3.4 呈现格式禁拦律：判据对象是文本表面形态的件不得拦链）。
    """
    import re, os, io
    v = []
    cache = cache or os.path.expanduser("~/.cache/tsl_verify")
    tdir = os.path.join(cache, "trees")
    def _rows(txt):
        out = {}
        for l in txt.splitlines():
            l = re.sub(r"\[[^\]]*\]", "", l)          # 剥掉 [累计…] 附注，防把括号里的状态当主状态
            m = re.search(r"(L\d(?:-\d)?)", l)
            if not m:
                continue
            st = re.search("(✅做到|🔴没做|🟡存疑|⚪查)", l[m.end():])
            if st:
                out[m.group(1)] = st.group(1)
        return out
    for stamp in dict.fromkeys(re.findall(r"TSL-stamp\s+([0-9a-f]{8})", text)):
        p = os.path.join(tdir, stamp + ".txt")
        if not os.path.isfile(p):
            # 老章豁免：v0.6 之前 stamps.log 只有两栏（时间+章），无行数/树指纹 ⇒ 本判据对它无对象
            _lg = os.path.join(cache, "stamps.log")
            _legacy = False
            if os.path.isfile(_lg):
                for _l in io.open(_lg, encoding='utf-8', errors='replace'):
                    _f = _l.rstrip("\n").split("\t")
                    if len(_f) > 1 and _stamp_of(_f) == stamp:
                        _legacy = len(_f) < 4
                        break
            if not _legacy:
                v.append("stamp %s 无存档树体（v0.6 起应有）＝章树不可核对" % stamp)
            continue
        stored = _rows(io.open(p, encoding='utf-8', errors='replace').read())
        order = list(stored.keys())
        seen = _rows(text)
        for lid, st in seen.items():
            if lid in stored and stored[lid] != st:
                v.append("层状态与存档不符：%s 存档=%s 回复=%s（stamp %s）" % (lid, stored[lid], st, stamp))
        miss = [k for k in order if k not in seen]
        if miss:
            v.append("选择性呈现：回复缺层 %s（stamp %s 树体共 %d 层）" % (",".join(miss), stamp, len(order)))
        # ── v1.1 全文 diff 腿（2026-10-07 童灵落·relay 候选2）────────────────────
        #   病根：上行只比「层名↔状态词」，_rows() 把判定依据文字整段丢弃 ⇒
        #   「改依据文字但保留 ✅/🔴 符号」这类改写全部漏网（比状态列更隐蔽的洗绿）。
        #   本腿比「层名 + 归一化后的整行正文」：状态词之外的任何改写都抓。
        #   ⛔ 容忍项：行首树形字符（├─│└─）与空白差异——那属呈现层不算改写（§3.4）。
        def _norm_line(l):
            l = re.sub(r"^[│├└─\s]+", "", l)          # 剥树形前缀+空白
            l = re.sub(r"\s+", " ", l).strip()          # 归一空白
            return l
        def _bodies(txt):
            out = {}
            for l in txt.splitlines():
                m = re.search(r"(L\d(?:-\d)?)", l)
                if not m:
                    continue
                out[m.group(1)] = _norm_line(l)
            return out
        sb, tb = _bodies(io.open(p, encoding='utf-8', errors='replace').read()), _bodies(text)
        for lid, sline in tb.items():
            if lid in sb and sb[lid] != sline:
                v.append("层正文被改写（状态词之外）：%s（stamp %s）｜存档=%r 回复=%r"
                         % (lid, stamp, sb[lid], sline))
    return v


def _stamp_of(parts):
    """从 stamps.log 的一行解析出 stamp 栏（v0.11.6·2026-10-07 候选1 兼容层）。

    ⛔ 禁假设固定列序：历史行无 src 栏（时间\\tstamp\\t…），新行有（时间\\tsrc=xxx\\tstamp\\t…）。
    若按固定下标 parts[1] 取，新行的 "src=workbuddy" 会被当成 stamp ⇒「伪造凭证」假红
    （v0.8 章树绑定全线报废）。

    ⚠️ 定位法（2026-10-07 实测修正）：⛔ 不可用「首个不以 src= 开头的非空栏」——
    那是**第0栏的时间戳**（时间戳不带 src= 前缀，必先命中）⇒ 解析出时间戳当 stamp。
    正解：**从 src= 栏的下一栏开始**取第一个非空栏（那才是 stamp）。
    """
    pp = [x.strip() for x in parts]
    for i, x in enumerate(pp):
        if x.startswith("src="):
            for y in pp[i + 1:]:
                if y:
                    return y
            return ""
    return pp[1] if len(pp) > 1 else ""


def _stamp_fresh(stamp, window=FRESH_WINDOW_SEC):
    """stamp 在 stamps.log 中的时间戳是否落在最近 window 秒内。

    ⛔ 口径：只答"这枚 stamp 是不是刚产出的"，不答"它是不是钩子产的"——后者
    在 stamps.log 无产出者字段时不可判（2026-10-05 实盘核实：五栏无 PID/事件）。
    但在非 D3 档二者等价：tree_hook 对非 D3 不产树 ⇒ 本回合出现的新 stamp 只可能来自 AI 自跑。
    """
    import datetime as _dt
    _sl = os.path.join(CACHE, "stamps.log")
    if not os.path.isfile(_sl):
        return False
    try:
        for _l in open(_sl, encoding="utf-8", errors="replace"):
            _p = _l.split("\t")
            if len(_p) >= 2 and _stamp_of(_p) == stamp:
                _ts = _dt.datetime.strptime(_p[0].strip()[:19], "%Y-%m-%d %H:%M:%S")
                return (_dt.datetime.now() - _ts).total_seconds() <= window
    except Exception:
        return False
    return False


def _hook_ran_evidence():
    """v1.1（2026-10-09 Qoder 任务卡·六改点⑥）：tree_hook 当回合是否真跑过 tsl_verify。
    tree_hook 跑通即写 tsl_tree_hook_ran.json（ts 新鲜＝本回合产物）。
    ⛔ 不把「hook 代跑·AI 被踹回前未自跑」判成红（假红违三纪律3保守判定）。
    注：证据落独立文件而非 stamps.log——stamps.log 格式归 tsl_verify 所有，跨写
    src=tree_hook 行会破坏 tsl_verify 自有解析（更糟的复发），故用隔离证据通道。"""
    import datetime as _dt
    try:
        from tsl_tree_hook import HOOK_RAN as _HR
    except Exception:
        _HR = os.path.join(os.path.expanduser("~"), ".workbuddy", "tsl_tree_hook_ran.json")
    if not os.path.isfile(_HR):
        return False
    try:
        d = json.load(open(_HR, encoding="utf-8"))
        _ts = _dt.datetime.strptime(d.get("ts", ""), "%Y-%m-%d %H:%M:%S")
        return (_dt.datetime.now() - _ts).total_seconds() <= FRESH_WINDOW_SEC
    except Exception:
        return False


TSL_SHAPE_MARKERS = ("├─ L0", "TSL会话评级", "TSL-stamp", "🧾 TSL 机械核验", "├─ L7-")


def has_tsl_shape(text):
    """回复是否含 TSL 形态（与 main() v0.4b 识别词同源·单一真源·⛔不与 main 各写一套）"""
    return any(_mk in text for _mk in TSL_SHAPE_MARKERS) if text else False


def _non_d3_overreach(text, _has_tsl=None):
    """腿1 · 非 D3 档 TSL 越界判据。返回留痕原因串；空串 = 无越界（静默）。

    ① 回复出现 TSL 形态却无脚本 stamp（8 位十六进制）→ 手绘 stamp / 自画树；
    ② 引用的 stamp 时间戳在 FRESH_WINDOW_SEC 内 → 本回合刚产出（AI 自跑 tsl_verify）；
    ③ 引用的是历史 stamp → 属"引用/讨论 TSL 机制"，豁免静默——
       ⛔ 不把分析会话打成红：那正是 10-04 噪声涨到 2146 条/天的成因之一。

    ⛔ 判据自足：形态判定在本函数内完成（不依赖调用方先判 has_tsl）——
       T1 变异体实测：函数被单独调用时原实现把"无 TSL 形"误报成"手绘 stamp"。
    """
    if not text:
        return ""
    _has = has_tsl_shape(text) if _has_tsl is None else _has_tsl
    if not _has:
        return ""
    import re as _re2
    _stamps = _re2.findall(r"TSL-stamp\s+([0-9a-f]{8})", text)
    if not _stamps:
        return "无脚本 stamp（手绘 stamp / 自画树）"
    _fresh = [s for s in _stamps if _stamp_fresh(s)]
    if _fresh:
        return "本回合新产 stamp=" + ",".join(_fresh)
    return ""


def _selftest():
    import re, os, io  # noqa: F401（与判据函数同源，防模块级未导入）
    tree = ("\u251c\u2500 L7-1 错误→成长箱 🔴没做 [累计✅做到] 窗口内新立记录=0\n"
            "\u251c\u2500 L7-5 反思沉淀 🔴没做 窗口内[童灵思考]=0\n")
    cases = [
        ("N1 脚本给了累计口径→不报", "L7-1 当日累计两项 ✅", True),
        ("N2 树内无累计却称累计→必报", "L7-5 当日累计 ✅", False),
        ("N3 树内🔴却总括均✅→必报", "L7-5 均 ✅", False),
        ("N4 不提口径→静默", "L7-5 窗口内 0 条", True),
    ]
    ok = 0
    for name, frag, quiet in cases:
        r = _narration_vs_tree(frag, tree)
        good = (not r) if quiet else bool(r)
        ok += good
        print("  %s %s%s" % ("✅" if good else "❌", name, ("" if good else " 实际=%r" % (r,))))
    mut = _narration_vs_tree("L7-5 均 ✅", "")          # 判据置假（无树=无对照）→ 必归零
    print("  %s MUT:%s 判据置假（空树）→ 检出 %d（应为 0）" % ("✅" if mut == [] else "❌", "OK" if mut == [] else "FAIL", len(mut)))
    ok += (mut == [])
    import tempfile
    td = tempfile.mkdtemp()
    os.makedirs(os.path.join(td, "trees"))
    io.open(os.path.join(td, "trees", "abcd1234.txt"), "w", encoding="utf-8").write(
        "\u251c\u2500 L7-1 错误→成长箱 \U0001f534没做 [累计\u2705做到] 窗口内0\n"
        "\u251c\u2500 L7-5 反思沉淀 \U0001f534没做 窗口内0\n\U0001f50f TSL-stamp abcd1234\n")
    # v1.1（2026-10-07 候选2·全文 diff 腿）：B1 夹具改为**忠实 relay**（判据文字与存档逐字一致）。
    #   原夹具回复侧写 "x"/"y" 而存档侧是 "窗口内0" —— 老逻辑只比状态词所以能过；
    #   全文 diff 腿上线后这在语义上就是「判据文字被改写」，B1 遂红。
    #   ⛔ 但真实 relay 就是逐行照抄（判据文字必然一致）⇒ 改夹具，不放宽判据。
    #   「呈现层差异该容忍」单列 B5（树形/空白·§3.4），防误报面被误伤。
    _t_faithful = ("├─ L7-1 错误→成长箱 🔴没做 [累计✅做到] 窗口内0\n"
                   "├─ L7-5 反思沉淀 🔴没做 窗口内0\n")
    b1 = _tree_binding("🔏 TSL-stamp abcd1234\n" + _t_faithful, td) == []
    _t_fmt = ("├─  L7-1 错误→成长箱  🔴没做 [累计✅做到]  窗口内0\n"
              "├─  L7-5 反思沉淀 🔴没做  窗口内0\n")
    b5 = _tree_binding("🔏 TSL-stamp abcd1234\n" + _t_fmt, td) == []
    b2 = bool(_tree_binding("├─ L7-1 错误→成长箱 ✅做到 偷改成绿\n🔏 TSL-stamp abcd1234", td))
    b3 = bool(_tree_binding("├─ L7-1 错误→成长箱 🔴没做 [累计✅做到] 窗口内0\n🔏 TSL-stamp abcd1234", td))          # 缺 L7-5=选择性呈现
    b4 = bool(_tree_binding(_t_faithful + "🔏 TSL-stamp deadbeef", td))  # 无存档章
    os.makedirs(os.path.join(td, "empty", "trees"))
    io.open(os.path.join(td, "empty", "trees", "abcd1234.txt"), "w", encoding="utf-8").write("├─ 表头无层行\n")
    mut = _tree_binding("├─ L7-1 错误→成长箱 ✅做到\n🔏 TSL-stamp abcd1234", os.path.join(td, "empty")) == []
    for name, good in [("B1 逐行忠实relay→不报", b1), ("B2 抄真章改层状态→必报", b2),
                       ("B3 缺层（选择性呈现）→必报", b3), ("B4 新章无存档树体→必报", b4),
                       ("B5 呈现层差异（树形/空白）→容忍", b5),
                       ("MUT 判据置假（无存档根）→归零", mut)]:
        ok += bool(good)
        total_b = True
        print("  %s %s" % ("✅" if good else "❌", name))
    n_cases = len(cases) + 1 + 6   # v1.1：B 组新增 B5（呈现层差异容忍）⇒ 5→6
    # v1.0 腿1 档位门控变异体（T1-T4）：判据必须能分辨「越界自产」与「引用/讨论 TSL」——
    #   分辨不了 = 要么漏掉 10-03 四犯，要么把分析会话打成红（后者正是 2146 条/天噪声的成因）。
    import tempfile as _tf2, datetime as _dt2, shutil as _sh2
    _td2 = _tf2.mkdtemp()
    _old_cache = globals().get("CACHE")
    _now_s = _dt2.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _old_s = (_dt2.datetime.now() - _dt2.timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    io.open(os.path.join(_td2, "stamps.log"), "w", encoding="utf-8").write(
        "%s\t1111aaaa\t14\tfingerprint\n%s\t2222bbbb\t14\tfingerprint\n" % (_old_s, _now_s))
    try:
        globals()["CACHE"] = _td2
        t1 = _non_d3_overreach("普通回复，不含任何 TSL 形态") == ""            # 压噪主路径
        t2 = bool(_non_d3_overreach("TSL-stamp（本回合树见下方 relay）"))       # 手绘 stamp·10-03 第三犯形态 → 必报
        t3 = _non_d3_overreach("复盘引用历史章：TSL-stamp 1111aaaa") == ""      # 历史 stamp=引用讨论 → 静默
        t4 = bool(_non_d3_overreach("TSL-stamp 2222bbbb"))                     # 本回合新产 → 必报
    finally:
        globals()["CACHE"] = _old_cache
        _sh2.rmtree(_td2, ignore_errors=True)
    for name, good in [("T1 非D3无TSL形→静默(压噪)", t1), ("T2 手绘stamp无hash→必报", t2),
                       ("T3 引用历史stamp→静默", t3), ("T4 本回合新产stamp→必报", t4)]:
        ok += bool(good)
        n_cases += 1
        print("  %s %s" % ("✅" if good else "❌", name))
    # v0.9 端到端回归：自测原样只调判定函数，**从不进 main()**——于是 main() 里的
    #   UnboundLocalError 让守卫每次 Stop 都 rc=1，而自测照样 10/10 全绿（判据没被任何用例走一遍）。
    #   本例用真实子进程跑 main()（隔离 WORKBUDDY_CONFIG_DIR·喂无 TSL 的最小载荷），
    #   断言 rc==0 且无 traceback——只测"能不能跑完"，不测内容判定。
    try:
        import subprocess
        env = dict(os.environ)
        env["WORKBUDDY_CONFIG_DIR"] = td
        env["TSL_VERIFY_CACHE"] = os.path.join(td, "tslcache")
        os.makedirs(env["TSL_VERIFY_CACHE"], exist_ok=True)
        r = subprocess.run([sys.executable, os.path.abspath(__file__)],
                           input='{"last_assistant_message": "普通回复无TSL树", "session_id": "selftest"}',
                           capture_output=True, text=True, env=env, timeout=30)
        e2e_ok = (r.returncode == 0) and ("Traceback" not in (r.stderr or ""))
        ok += 1 if e2e_ok else 0
        n_cases += 1
        print("  %s E2E main() 端到端 rc=%s 无traceback=%s"
              % ("✅" if e2e_ok else "❌", r.returncode, "Traceback" not in (r.stderr or "")))
        if not e2e_ok:
            print("     stderr:", (r.stderr or "")[-300:].replace("\n", " / "))
    except Exception as _e:
        n_cases += 1
        print("  ❌ E2E main() 端到端 自检自身异常：%s: %s" % (type(_e).__name__, _e))
    print("自测 %d/%d %s" % (ok, n_cases, "全绿" if ok == n_cases else "有红"))
    import shutil as _sh
    _sh.rmtree(td, ignore_errors=True)
    return 0 if ok == n_cases else 1
    print("自测 %d/%d %s" % (ok, len(cases) + 1, "全绿" if ok == len(cases) + 1 else "有红"))
    return 0 if ok == len(cases) + 1 else 1


def main():
    import sys as _s
    if "--self-test" in _s.argv:
        return _selftest()
    try: data=json.load(sys.stdin)
    except Exception: return 0
    tp=data.get("transcript_path") or ""
    sid=data.get("session_id") or ""   # v1.0：档位判据按本会话过滤（⛔不读全局最新行=串台源）
    # 跨端解析走单一真源（2026-09-23 童灵根治）：
    # 原实现先按 '"type":"assistant"' 预过滤行，而 WB 端该行 type 是 "message"
    # → 一行都进不来（预过滤失明）；即便进来 content 也在顶层（取值失明）＝双重失明。
    text="\n".join(_tr.assistant_texts(tp))
    if not text: return 0  # 取不到回复=不判定（诚实·不瞎报）
    # v0.4b 判定面修正（夹具实证：截断树无"├─ L0"行致 has_tsl=False=守卫整个没进判定——
    #   洞比预想深：不止"半棵树放行"，是"半棵树让守卫根本不认识它是树"。识别词扩三形态：）
    has_tsl=has_tsl_shape(text)   # v1.0：形态识别收敛到单一真源（原内联五选一·与本类 TSL_SHAPE_MARKERS 重复=双本账）
    if not has_tsl: return 0
    # v0.3 八要素机械痕（2026-09-23 三问拆穿"分级放权"：判权给有逃逸动机者=012预演；
    #   立法改向：档位只分形态（评估类全量表/其余一行简版），⛔不分做不做——每轮必输出
    #   `🧪 8要素|①..⑧|结论` 固定前缀行，缺痕=留痕。）
    #   ↑ v1.0 位置上移：本判据属"TSL 轮必做"，不随档位免除，故置于档位门控之前。
    if "🧪 8要素" not in text and "🧪8要素" not in text:
        _v("TSL轮缺🧪8要素痕（每轮必做·档位只分形态不分做不做·08 L5-1 v1.4.2）")
        _oklog("MISS")
    else:
        _oklog("OK")  # v0.5 痕账本：正常也记（verify L5 读最近一行→⚪欠装转有颜色的判定源）
    # v1.0 腿1 · 档位门控（根治 2026-10-03 禁令失效四犯 · 四犯全发生在非 D3 档）：
    #   树义务仅 D3（08 §七·与 tsl_tree_hook 产树门控 / tsl_echo_hook 注入门控同源判据）。
    #   非 D3 档出现任何 TSL 形态 = AI 越界（自跑 tsl_verify / 手绘 stamp / 越界树文）；
    #   同时非 D3 档**不再走后续章树绑定/口径腿**——那些腿的对象是"本回合该 relay 的树"，
    #   非 D3 档无此对象，照旧判定＝把"引用历史树讨论 TSL"打成红
    #   （实证：噪声 10-03 212 条/天 → 10-04 2146 条/天，有效信号被淹没）。
    if _session_d_tier is not None:
        _tier = _session_d_tier(sid)
        if _tier != "D3":
            if not has_tsl:
                return 0   # 非 D3 且无 TSL 形 → 全腿跳过（压假红主路径）
            _why = _non_d3_overreach(text)
            if _why:
                _v("非D3档TSL越界（树义务仅D3·%s）" % _why)
                print("🔴 TSL 收尾违规：本会话非 D3（tier=%s），回复出现 TSL 树/stamp —— "
                      "树义务仅 D3，AI ⛔ 不得自跑校验器/手绘 stamp/自画树。已留痕 w1_not_honored。"
                      % (_tier or "无档位"))
            return 0
    lr=os.path.join(CACHE,"last_run.txt")
    ran=False
    if os.path.isfile(lr):
        try:
            import datetime
            ts=open(lr,encoding='utf-8').read().split("\t")[0]
            datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")
            ran=True
        except Exception:
            ran=False
    # v1.1（2026-10-09 Qoder 任务卡·六改点⑥）：closeout 判据联动——认「tree_hook 当回合真跑」
    #   tree_hook 跑通即写 tsl_tree_hook_ran.json（_hook_ran_evidence 验 ts 新鲜）。
    #   ⛔ 把「hook 代跑·AI 被踹回前未自跑」判成红（假红违三纪律3保守判定）。
    if not ran and _hook_ran_evidence():
        ran=True
    if not ran:
        _v("输出了TSL清单但tsl_verify未跑（last_run缺失或不可解析）")
        print("🔴 TSL 收尾违规：回复输出了 TSL 验证清单，但 tsl_verify.py 未跑——"
              "TSL 必须由脚本产出（AI 只许 relay）。已留痕 w1_not_honored。")
        return 0
    # v0.2 stamp 验真（2026-09-23 皮叔令「TSL 0出错显示·机械保底·禁美化」构造权扩面配套）：
    #   抓回复中的 🔏 TSL-stamp：缺=手绘树（绕过脚本自画）；有但不在 stamps.log=伪造凭证。
    #   边界更新（v0.8·2026-09-26）：原自陈"逐行 hash 绑验暂缺"已补——`_tree_binding()` 按章取存档树体
    #   逐层比对状态词＋缺层检测，"抄真章偷改一行/配更绿树/选择性缺层"三态实测可逮（自测 B1-B4＋MUT）。
    import re as _re
    # v0.4 截断树判据（2026-09-23 你实锤：relay 用 tail -6 传了半棵树+真stamp=现机制放行=洞）：
    #   FULL 树合法形状=≥12条 ├─ 行；出现树且 stamp 真但 ├─行数<12 → 截断relay 留痕。
    _tlines=[l for l in text.splitlines() if l.strip().startswith("├─") and ("L0" in l or "L1" in l or "L7-" in l or "接" in l)]
    if _tlines:
        _allt=sum(1 for l in text.splitlines() if l.strip().startswith("├─"))
        if _allt < 12:
            _v("TSL树截断relay（├─行数%d<12·半棵树+真章=绕完整义务·§三·九律一复发案QCN-016）" % _allt)
    # v0.6 签名时间机检（PAT-045晋升·仪表：产出签名时间须date实取非预写）：
    #   回复尾 `| HH:MM]` 的 HH 与 transcript mtime 小时差>2 → 留痕。观察期只留痕不阻断，一周按误伤率定去留。
    try:
        import datetime as _dd
        _mt=_dd.datetime.fromtimestamp(os.path.getmtime(tp)) if tp and os.path.isfile(tp) else _dd.datetime.now()
        _sig=_re.findall(r'(?<!\d)(\d{1,2}):(\d{2})\]\s*$', text.strip())
        if _sig:
            _d=abs(int(_sig[-1][0])-_mt.hour)
            if _d>2 and _d<22:
                _v('PAT-045仪表：签名时间'+_sig[-1][0]+':'+_sig[-1][1]+'与运行时刻差>'+str(_d)+'h（预写嫌疑·观察窗仅留痕）')
    except Exception:
        pass
    stamps=_re.findall(r'TSL-stamp\s+([0-9a-f]{8})', text)
    if not stamps:
        _v("TSL树无🔏stamp行=手绘树（v0.3构造权扩面后禁止AI自画）")
        print("🔴 TSL 收尾违规：回复里的 TSL 树无脚本 stamp 行——树须由 tsl_verify --full 产出并 relay 原文。已留痕。")
        return 0
    known=set()
    _sl=os.path.join(CACHE,"stamps.log")
    if os.path.isfile(_sl):
        for l in open(_sl,encoding='utf-8',errors='replace'):
            parts=l.split("\t")
            if len(parts)>=2:
                _s = _stamp_of(parts)
                if _s: known.add(_s)
    bad=[x for x in stamps if x not in known]
    if bad:
        _v("TSL stamp 不在签发账本=凭证伪造嫌疑:%s" % ",".join(bad))
    # v0.7 口径来源判据（叙述 vs 树·观察期只留痕）
    # v0.9 修正一：本块原用局部名 `_tr` 承载树体文本，与模块级 `import transcript_reader as _tr`
    #   同名 → Python 把 `_tr` 判为 main() 局部名 → L153 的 `_tr.assistant_texts(tp)` 直接
    #   UnboundLocalError，守卫每次 Stop 都 rc=1（＝本腿实际从未产出过判定）。改局部名 `_tree_txt`。
    _tree_txt = ""
    _tp = os.path.join(CACHE, "last_tree.txt")
    try:
        if os.path.isfile(_tp):
            _tree_txt = open(_tp, encoding="utf-8", errors="replace").read()
        if _tree_txt:
            for _m in _narration_vs_tree(text, _tree_txt):
                _v("v0.7 口径来源：" + _m)
        for _m in _tree_binding(text):
            _v("v0.8 章树绑定：" + _m)
    except Exception as _e:
        # v0.9 修正二：原 `except: pass` 后紧跟"伪造凭证"print＝异常被喊成指控、真伪造却不喊，
        #   事实与指控反接。现：异常只显形为判据自身故障（Fail-Loud·⛔不冒充内容违规）。
        _v("v0.7/v0.8 判据执行异常=守卫自身故障(非内容指控): %s: %s" % (type(_e).__name__, str(_e)[:120]))
        print("⚠️ TSL 收尾守卫内部异常（判据未产出，⛔不作为对回复的指控）：%s: %s"
              % (type(_e).__name__, str(_e)[:120]))
    if bad:
        # 真·凭证异常才对外喊话（原来这一句被错放在 except 分支里）
        print("🔴 TSL 收尾违规：回复 stamp %s 不在 stamps.log——伪造凭证级，重点核查。" % ",".join(bad))
    return 0

def _oklog(state):
    try:
        os.makedirs(CACHE,exist_ok=True)
        import datetime
        with open(os.path.join(CACHE,"eight_check.log"),"a",encoding="utf-8") as f:
            f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"\t"+state+"\n")
    except Exception:
        pass

def _v(msg):
    os.makedirs(CACHE,exist_ok=True)
    import datetime
    now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(CACHE,"violations.log"),"a",encoding="utf-8") as f:
        f.write(f"{now}\tw1_not_honored\t{msg}\n")


if __name__=="__main__": sys.exit(main())
