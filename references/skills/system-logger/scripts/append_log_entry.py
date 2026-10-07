#!/usr/bin/env python3
"""Append a system-log entry with a mechanically-captured timestamp.

Root-cause fix (system-logger v3.10.5): the `完成` timestamp used to be an
AI-declared free-text value, which could be wrong (L442 wrote 20:46 while the
file mtime was 14:35). The only correct value is the moment of the write,
which only the OS clock at append time knows. This script captures `date`
internally, fills the `完成` field, and appends — AI never touches the time
value, so it is physically impossible to write a fabricated timestamp.

Usage:
  printf '%s' "$ENTRY_BODY" | python3 append_log_entry.py --tool WorkBuddy [--logdir DIR] [--reflection]
  python3 append_log_entry.py --guard-line [--logdir DIR]   # 独立产出 changelog_guard 检测行（v3.10.24）

ENTRY_BODY must contain a line `- **完成**：<NOW>` (placeholder) OR omit the
`完成` field entirely (the script inserts it). A literal HH:MM in the 完成
line = bypass of the physical anchor -> exit 1 (refuse to write).

--guard-line (v3.10.24·2026-09-01·你"系统日志写半天"架构解耦): 默认写入路径
  不再同步内嵌 changelog_guard --check（全树扫描 ~7s 绑定每次写入=主凶）。
  改为独立模式：AI 在输出验证块前跑一次本模式，机械产出 guard_line 回显——
  填值权仍归脚本（AI 接触不到填值权·防假阴性疲劳设计不变），只改调用时机。
  输出: GUARD_LINE <值>

--reflection: 童灵思考标记（v3.10.15 新增·2026-08-26·脚本旧标 v3.10.8 系笔误·2026-09-01 Loop评估#7对齐CHANGELOG·v1.2 2026-09-05 反思→思考更名）
  当指定此参数时，在条目标题前添加 `[童灵思考]` 前缀。
  蒸馏管道会扫描此标记，按内容分流到 L2/L3/L6。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import os
import time
import re
import subprocess
import sys
from datetime import datetime

LOGDIR_DEFAULT = os.path.expanduser("[记忆共享中心]/工作日志/系统日志")

# v3.12.0(2026-09-02·愿景①根治回复呈现层漂移): `--guard-line` 把 changelog_guard
# 检测值写入此缓存，写入路径的验证块读取它填 `📋 变更日志检测` 行——避免每次写入
# 重跑 7s 全树扫描（v3.10.24 解耦的代价），又让验证块 100% 脚本产出、AI 零构造权。
# v3.14.3(2026-09-18·QClaw·缓存新鲜度=年龄代理→被检对象身份验证·第一性根治):
#   病灶：v3.14.2 用"缓存年龄<10分钟"代理"缓存内容仍有效"——与 triwich_closeout_guard v1.2.0（mtime 时间差代理"本轮登记有没有"）
#   属**同一族缺陷**（拿代理信号冒充直接证据）。实证：08:36 算出"7 条候选未记"，08:45 写入时已修至 0，
#   但缓存年龄 9min<10min → 旧值被放行进验证块 → 系统日志固化了早已不成立的警告。
#   修法：缓存写入时**同时记录 changelog_guard.sh 与 变更日志.md 的 mtime+size 指纹**（即"检测所看过的东西"的身份），
#   读取时指纹不一即重算——年龄只做上限兵，指纹做新鲜度本体。解态：只有强制重算才拿得到旧值。
GUARD_CACHE = os.path.expanduser("~/.cache/systemlogger/guard_line.txt")


def _guard_fingerprint():
    """签名=检测所依赖的两个输入的身份（guard 脚本 + 被检账本）。
    ⛔ 不用缓存自身年龄作新鲜度——那只是"多久前算的"，不回答"所算的东西变了没"。"""
    parts = []
    for p in (
        os.path.expanduser("[记忆共享中心]/脚本中心/changelog_guard.sh"),
        os.path.expanduser("[记忆共享中心]/变更日志.md"),
    ):
        try:
            st = os.stat(p)
            parts.append("%s:%d:%d" % (os.path.basename(p), st.st_mtime_ns, st.st_size))
        except OSError:
            parts.append("%s:missing" % os.path.basename(p))
    return "|".join(parts)


def _write_guard_cache(val):
    try:
        d = os.path.dirname(GUARD_CACHE)
        os.makedirs(d, exist_ok=True)
        with open(GUARD_CACHE, "w", encoding="utf-8") as f:
            f.write(val.rstrip("\n") + "\n" + _guard_fingerprint() + "\n")
    except Exception:
        pass


def _read_guard_cache():
    """v3.14.3 第一性根治（2026-09-18·QClaw）：指纹验证优先于年龄。
    病灶：旧版只问"缓存多久前算的"（年龄代理），不问"所算的东西变了没"（直接证据）——
    与 triwich_closeout_guard v1.2.0（mtime 代理登记）同一族。实证：08:36 的"7 条"在已修至 0 后
    仍被年龄 TTL 放行进验证块（9min<10min）。
    新序：①读缓存行 ②指纹不一致（含旧格式无指纹行）→立即重算 ③指纹一致→年龄仅作上限兜底。"""
    try:
        if os.path.exists(GUARD_CACHE):
            with open(GUARD_CACHE, encoding="utf-8") as f:
                raw = f.read().strip().split("\n")
            val = raw[0].strip() if raw else ""
            cached_fp = raw[1].strip() if len(raw) > 1 else ""
            if cached_fp != _guard_fingerprint():
                fresh = run_guard_line()
                if fresh:
                    _write_guard_cache(fresh)
                    return fresh
                return "⚠️ guard_line 自动重算失败（输入已变·审查F2升级）——手动跑 `append_log_entry.py --guard-line` 核实"
            age = time.time() - os.path.getmtime(GUARD_CACHE)
            if age > 600:
                v2 = run_guard_line()
                if v2:
                    _write_guard_cache(v2)
                    return v2
                return "⚠️ guard_line 自动重算失败（原缓存>%d分钟·审查F2升级）——手动跑 `append_log_entry.py --guard-line` 核实" % (600 // 60)
            return val
    except Exception:
        pass
    return None


def run_guard_line():
    """机械产出 changelog_guard 检测行（v3.10.24 从写入路径独立出来）。

    AI 只能回显本函数返回值，不能自填——v3.10.7 防假阴性疲劳设计保留，
    仅调用时机从"每次写入"改为"验证块输出前（每会话 1 次）"。
    """
    guard_line = ""
    guard_script = os.path.expanduser("[记忆共享中心]/脚本中心/changelog_guard.sh")
    if os.path.exists(guard_script):
        out = err = ""
        try:
            try:
                cp = subprocess.run(
                    ["bash", guard_script, "--check"], capture_output=True, timeout=90
                )
                out = cp.stdout.decode("utf-8", "replace").strip()
                err = cp.stderr.decode("utf-8", "replace").strip()
            except subprocess.TimeoutExpired:
                guard_line = "⚠️ changelog_guard --check 超时 90s 未返回（AI 需手动跑 --check 核实）"
            if not guard_line:
                import json as _json
                j = _json.loads(out)
                n = int(j.get("candidates", 0))
                guard_line = "✅ 全部已记" if n == 0 else "⚠️ %d 条候选未记录（整行红框高亮）" % n
        except Exception as e:
            reason = "%s: %s" % (type(e).__name__, str(e)[:120])
            if err:
                reason += " | stderr: %s" % err.splitlines()[0][:160]
            guard_line = "⚠️ changelog_guard 执行失败（原因=%s·AI 需手动跑 --check 核实）" % reason
    else:
        guard_line = "N/A（个人工具·未安装）"
    return guard_line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", required=False, help="tool name (normalized allowlist value)")
    ap.add_argument("--logdir", default=LOGDIR_DEFAULT)
    ap.add_argument("--reflection", action="store_true",
                    help="添加 [童灵思考] 前缀（童灵→童灵心智活动汇报·蒸馏管道扫描标记）")
    ap.add_argument("--guard-line", action="store_true",
                    help="v3.10.24: 独立产出 changelog_guard 检测行（不写条目）——验证块输出前调用")
    ap.add_argument("--verify-reply", metavar="REPLY_FILE",
                    help="v3.13.0: 检测 AI 回复是否包含流程完成令牌（🔖 流程完成令牌：{hash}）。"
                         "传入回复文本文件路径，或用 - 从 stdin 读取。exit 0=包含令牌（流程完成），"
                         "exit 1=不包含令牌（流程未完成，需重新 relay 验证块）。")
    args = ap.parse_args()

    if args.guard_line:
        val = run_guard_line()
        _write_guard_cache(val)
        print("GUARD_LINE %s" % val)
        return 0

    if args.verify_reply:
        return verify_reply_token(args.verify_reply)
    if not args.tool:
        print("error: --tool 必填（--guard-line 模式除外）", file=sys.stderr)
        return 2

    # 输入面物理校验（v3.10.9·2026-08-27）：--tool 决定 `## <Tool>` 组头与概览行键，
    # 此前零校验=任意字符串直接进结构层（概览脏行的输入面缺口）。唯一真源=normalize_tool。
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import normalize_tool as nt
    if args.tool not in nt.ALLOWLIST:
        key = nt.norm_key(args.tool)
        cand = {nt.VARIANTS.get(key, key)} | {a for a in nt.ALLOWLIST if nt.norm_key(a) == key}
        canon = next(iter(cand & nt.ALLOWLIST), None)
        if not canon:
            print(f"error: --tool {args.tool!r} 不在 {len(nt.ALLOWLIST)} 规范名 allowlist 且无法归一"
                  f"——按 SKILL.md「工具名规范」节归一后重跑（拒写，不生成脏行）", file=sys.stderr)
            return 1
        args.tool = canon

    dt = datetime.now()
    now_hm = dt.strftime("%H:%M")
    today = dt.strftime("%Y-%m-%d")

    body = sys.stdin.buffer.read().decode('utf-8', errors='replace')
    if not body.strip():
        print("error: empty entry body on stdin", file=sys.stderr)
        return 2

    # 童灵思考标记（v3.10.15 新增·v1.2 2026-09-05 更名：反思→思考·你裁定认错偏置）
    if args.reflection:
        # 在第一个 ### 标题后添加 [童灵思考] 前缀
        body = re.sub(r"(^###\s+)", r"\1[童灵思考] ", body, count=1, flags=re.M)
        # 如果没有 ### 标题，在第一个 ## 标题后添加
        if not re.search(r"^###\s+", body, re.M):
            # ⚠️ 2026-10-02 段名归一（你指正）：兜底标题原写「童灵认知深化」，与 2026-09-05
            #   你裁定的唯一段名「童灵思考」不一致 → 同一份系统日志里出现两套段名。
            #   判据：蒸馏按前缀 [童灵思考] 扫描（L96·标题内容不参与判据），故改标题不改功能，
            #   但段名统一是规范要求——「名字即货币」（§二·十七同源判据）。
            body = re.sub(r"(^##\s+.*\n)", r"\1\n### [童灵思考] 童灵思考（本日）\n", body, count=1, flags=re.M)
        # 审查F13修复：两个标题都没有时标记无效——必须显式警告而非静默（防标记与内容不符）
        if not re.search(r"^###\s+|^##\s+", body, re.M):
            # v3.16.0（2026-09-11·第18端接入漏网根治）：原实现仅告警 → 改**机械兜底自动补标题**。
            # 漏网实证：AI 传裸文本（无任何标题）→ [童灵思考] 未注入 → 蒸馏分流静默不命中（假绿式漏网）。
            # 全自动化方向（愿景①）：脚本自己补标题，不依赖 AI 记得写 ###。
            body = "### [童灵思考] 童灵思考（%s）\n\n%s" % (today, body.lstrip("\n"))
            print("ℹ️ --reflection：条目体无标题 → 已机械补「### [童灵思考] 童灵思考」标题（防漏网兜底·段名与 2026-09-05 裁定一致）", file=sys.stderr)

    # Bypass guard: a literal time in the 完成 line instead of <NOW>.
    comp = re.search(r"^\s*-\s*\*\*完成\*\*\s*[:：]\s*(.+)$", body, re.M)  # v3.16.0 r1-C6：全/半角冒号并拒（原只拦全角=半角伪造时间可落盘成双行）
    if comp and comp.group(1).strip() != "<NOW>":
        print(
            "error: 完成 field contains literal time '%s' — must use <NOW> "
            "(the script owns the timestamp; a literal value bypasses the physical anchor)"
            % comp.group(1).strip(),
            file=sys.stderr,
        )
        return 1

    # Fill the placeholder (if AI wrote <NOW>) or insert if omitted.
    body = body.replace("<NOW>", now_hm)
    # v3.15.1(2026-09-10·跨组错位根治)：条目须携带 `- **工具**：<规范名>`——下游
    # reconcile_overview.py 的组位归一以此为**唯一归属真源**（缺字段=归不了位·不猜）。
    # 机制与「完成」完全一致：缺则补、有则不动；⛔不改任何既有行内容，⛔不动追加姿势。
    _has_tool = bool(re.search(r"^\s*-\s*\*\*工具\*\*\s*[:：]", body, re.M))  # 批4 r3-K2 [:：]统一
    _has_done = bool(re.search(r"^\s*-\s*\*\*完成\*\*\s*[:：]", body, re.M))  # v3.16.0批3 r2-C6：[:：]统一（原只认全角=半角<NOW>过L211后在此漏判成双行）
    _new = []
    if not _has_tool:
        _new.append("- **工具**：%s" % args.tool)
    if not _has_done:
        _new.append("- **完成**：%s" % now_hm)
    if _new:
        _ins = "".join(s + "\n" for s in _new)
        # 插入点=**首个既有字段行之前**（而非紧跟标题）——避免标题下的空行被留在字段中间，
        # 同时让「工具→完成→其余」贴近单条记录模板顺序。
        _anchor = re.search(r"^- \*\*[^*]+\*\*[:：]", body, re.M)  # 同上 [:：] 统一
        if _anchor:
            body = body[:_anchor.start()] + _ins + body[_anchor.start():]
        else:
            body = re.sub(r"(^###\s+.*\n)", lambda m: m.group(1) + _ins, body, count=1)

    logfile = os.path.join(args.logdir, "系统日志_%s.md" % today)

    # Grouping: tool group header must be unique in the whole file (v3.10.6 根治:
    # tail-window 判定缺陷——组头在文件中部时末尾窗口看不到，误加重复组头，8/12 连犯两次).
    # 判定基准=全文扫描该工具组头是否已存在：存在→并入（不加组头）；不存在→新建组头。
    header = ""
    if os.path.exists(logfile):
        with open(logfile, encoding="utf-8") as f:
            text = f.read()
        group_exists = bool(re.search(rf"^## {re.escape(args.tool)}\s*$", text, re.M))
        if not group_exists:
            header = "## %s\n\n" % args.tool
    else:
        header = (
            "# 系统日志 %s\n\n"
            "## 今日概览\n\n"
            "| 工具 | 任务数 | 关键成果 |\n"
            "|------|--------|---------|\n"
            "| %s | 0 |  |\n\n"
            "## %s\n\n"
        ) % (today, args.tool, args.tool)

    # v3.14.0(2026-09-21·皮叔令「数字分身信誉度最高级别任务」): 令牌内嵌进条目本体——
    #   修 v3.13.0 两缺陷：①签发值只落 last_token.txt 一枚，下次写入即被覆盖 → 历史令牌
    #   全部不可事后验签（2026-09-21 实测：当日 6 枚令牌 grep 日志 0 命中·签发值已被覆盖）；
    #   ②令牌不进日志文件 → 只能证明「某次脚本运行发生过」，不能证明「哪轮·哪条」。
    #   现在：每条条目自带 seal 行（落盘·逐条独立·可事后审计）；签发账本 seal_ledger.log
    #   改为 append-only 追加（保留历史）。
    import hashlib as _hl, secrets as _sk
    _seed = "%s%s%s%s" % (today, now_hm, args.tool, _sk.token_hex(8))
    token_hash = _hl.sha256(_seed.encode("utf-8")).hexdigest()[:8]
    content = header + body.rstrip("\n") + "\n" + "- **seal**：%s\n" % token_hash
    try:
        _cache_dir = os.path.dirname(GUARD_CACHE)
        os.makedirs(_cache_dir, exist_ok=True)
        with open(os.path.join(_cache_dir, "last_token.txt"), "w", encoding="utf-8") as _tf:
            _tf.write(token_hash)
        with open(os.path.join(_cache_dir, "seal_ledger.log"), "a", encoding="utf-8") as _lf:
            _lf.write("%s\t%sT%s\t%s\t%s\n" % (token_hash, today, now_hm, os.path.basename(logfile), args.tool))
    except Exception:
        pass  # 落盘失败不阻塞写入主流程；verify 时按"无签发记录"降级处理

    # O_APPEND atomic append — concurrent writers never overwrite each other.
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(content)

    # Mechanical overview reconcile (best effort; never blocks the append).
    # stdout 静默——避免子进程诊断行污染 AI 捕获的 stdout（stdout 只应为验证块）。
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "reconcile_overview.py"), logfile],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        if r.returncode != 0:
            # 审查F14修复：不阻塞主流程，但失败信号必须可见（不再静默吞）
            print("⚠️ reconcile 未收敛（exit %d）——概览计数可能滞后，建议手动跑 reconcile_overview.py 查看详情" % r.returncode, file=sys.stderr)
    except Exception as e:
        print("⚠️ reconcile 调用异常：%s（概览计数可能滞后）" % e, file=sys.stderr)

    # v3.10.24(2026-09-01·你"系统日志写半天"架构解耦): changelog_guard 检测行
    # 不再在写入路径同步内嵌（全树扫描 ~7s×每次写入=主凶）——改由 AI 在验证块
    # 输出前跑 `--guard-line` 独立模式（每会话 1 次）机械产出。填值权仍归脚本。
    # 见 run_guard_line()。

    # 调试行写 stderr（机器消费者用），stdout 只出验证块供 AI 逐字 relay
    sys.stderr.write("APPENDED %s\n" % logfile)
    sys.stderr.write("TIME %s %s\n" % (today, now_hm))
    if args.reflection:
        sys.stderr.write("REFLECTION true\n")
    sys.stderr.write("---ENTRY---\n")
    sys.stderr.write(content + "\n")

    # v3.12.0 回复验证块：脚本机械产出，AI 只许逐字 relay（防误·设计消除错误）。
    # 漂移在架构上不可能——AI 接触不到任何格式构造权。
    emit_verify_block(logfile, today, now_hm, args.tool, body, token_hash)
    return 0


def emit_verify_block(logfile, today, now_hm, tool, body, token_hash):
    """机械产出回复验证块（diff 块）。AI 只许逐字 relay，接触不到构造权。

    段2 的全部行（📍文件/⏰时间/🔧工具/📋校验/📋变更日志检测/🔖流程完成令牌）均由脚本算值填，
    与 SKILL.md 步骤5 模板逐字一致。设计消除错误：AI 无法改写/表格化/增删任何行。

    v3.13.0(2026-09-02·回复完整性令牌机制): 验证块末尾新增「🔖 流程完成令牌」——
    唯一 hash（sha256(time+random)前8位），AI 不能伪造。SKILL.md 声明：系统日志流程完成的
    唯一标志是回复末尾包含此令牌。没有令牌=流程未完成=AI 必须重新 relay 验证块。
    --verify-reply 模式检测回复是否包含此令牌。
    """
    import hashlib
    import secrets
    fname = os.path.basename(logfile)
    # 数据一致性：重读文件确认刚写入的条目存在
    consistency = "✅ 数据一致性：通过"
    try:
        with open(logfile, encoding="utf-8") as f:
            txt = f.read()
        if not re.search(rf"^- \*\*完成\*\*[:：]\s*{re.escape(now_hm)}$", txt, re.M):  # 批4 r3-K2 回读同型+\s*（冒号后带空格值曾假红·全角同修）
            consistency = "⚠️ 数据一致性：写入后回读未命中（请人工核对）"
    except Exception:
        consistency = "⚠️ 数据一致性：回读失败（请人工核对）"
    # 格式完整性：统计字段行数（期望 8）
    n_fields = len(re.findall(r"^- \*\*[^*]+\*\*[:：]", body, re.M))  # 批4 r3-K2 计数字段同型
    if n_fields >= 8:
        fmt = "✅ 格式完整性：%d 字段齐全（≥8 基础门槛·含扩展）" % n_fields
    else:
        fmt = "⚠️ 格式完整性：%d/8 基础字段不足（必备字段缺失·与扩展字段无关）" % n_fields
    # 变更日志检测：读 --guard-line 写入的缓存
    gv = _read_guard_cache()
    if gv is None:
        changelog = "⚠️ guard_line 未跑（先跑 `append_log_entry.py --guard-line` 填值）"
    else:
        changelog = gv
    # v3.14.0：令牌已在写入前生成，并已内嵌进条目（- **seal**：行）+ 记入 seal_ledger.log
    #   （append-only）。此处只负责把同一枚值打进验证块——保证「条目内 seal ≡ 回复令牌」。
    print("📝 系统日志已写入")
    print("━━━━━━━━━━━━━━━")
    print()
    print("📍 文件：%s" % fname)
    print()
    print("⏰ 时间：%s %s" % (today, now_hm))
    print()
    print("🔧 工具：%s" % tool)
    print()
    print("📋 校验状态：")
    print(consistency)
    print(fmt)
    print("✅ 机械校验：完成行回读一致 + 字段结构检查（假设验证=AI步骤4.3自检项·脚本未代验·审查F3如实化）")
    print()
    print("📋 变更日志检测：%s" % changelog)
    print()
    print("🔖 流程完成令牌：%s" % token_hash)


def verify_reply_token(reply_path):
    """v3.13.0: 检测 AI 回复是否包含流程完成令牌。

    流程完成令牌格式：`🔖 流程完成令牌：{8位hash}`
    - 包含令牌 → exit 0（流程完成）
    - 不包含令牌 → exit 1（流程未完成，需重新 relay 验证块）

    这是防错层兜底（事后检测），不是防误层根治（事前消除）。
    防误层根治是：SKILL.md 声明「系统日志流程完成的唯一标志是回复末尾包含此令牌」，
    把 relay 验证块从「行为要求」升级为「流程完成的必要条件」。

    诚实边界：纯 AI 环境不存在「绝对物理杜绝」——AI 仍然可以选择不 relay 验证块，
    只是这样流程就不算完成。--verify-reply 需要 AI 自觉跑，AI 可以不跑。
    可达的最优形态：绕过成本 > 遵守成本 + 绕过留痕。
    """
    if reply_path == "-":
        text = sys.stdin.buffer.read().decode('utf-8', errors='replace')
    else:
        try:
            with open(os.path.expanduser(reply_path), encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print("error: 无法读取回复文件 %s: %s" % (reply_path, e), file=sys.stderr)
            return 2

    # 检测流程完成令牌：🔖 流程完成令牌：{8位十六进制hash}
    token_pattern = r"🔖\s*流程完成令牌[：:]\s*([0-9a-f]{8})"
    m = re.search(token_pattern, text)
    if m:
        token = m.group(1)
        # 审查F1：与最近签发值比对（格式合法 ≠ 本会话签发）
        issued = None
        try:
            token_store = os.path.join(os.path.dirname(GUARD_CACHE), "last_token.txt")
            if os.path.exists(token_store):
                with open(token_store, encoding="utf-8") as tf:
                    issued = tf.read().strip()
        except Exception:
            issued = None
        _ledger_hit = None
        try:
            _lp = os.path.join(os.path.dirname(GUARD_CACHE), "seal_ledger.log")
            if os.path.exists(_lp):
                for _line in open(_lp, encoding="utf-8"):
                    if _line.split("\t", 1)[0].strip() == token:
                        _ledger_hit = _line.rstrip("\n")
                        break
        except Exception:
            _ledger_hit = None
        if issued == token:
            print("✅ 回复完整性：通过（令牌=%s·与本会话签发值一致·验签✓）" % token)
            print("📋 系统日志流程完成。")
            return 0
        if _ledger_hit:
            print("✅ 回复完整性：通过（令牌=%s·命中签发账本 seal_ledger·v3.14.0 历史可验）" % token)
            print("   账本行：%s" % _ledger_hit)
            print("📋 系统日志流程完成。")
            return 0
        elif issued is None:
            print("⚠️ 回复完整性：无本会话签发记录（签发值落盘缺失或系统异常）——无法验签，请人工核对日志文件·审查F1", file=sys.stderr)
            return 1
        else:
            print("⚠️ 回复完整性：令牌格式合法但与本会话最近签发值不符（伪造或跨会话）·审查F1验签", file=sys.stderr)
            print("📌 处置：确认是否本会话产出——是则人工核对日志文件后放行，否则重新 relay 验证块。", file=sys.stderr)
            return 1
    else:
        print("❌ 回复完整性：未通过（缺少流程完成令牌）", file=sys.stderr)
        print("⚠️ 系统日志流程未完成——AI 回复中未检测到「🔖 流程完成令牌：{hash}」。", file=sys.stderr)
        print("📌 可能原因：", file=sys.stderr)
        print("  1. AI 自创了回复格式，跳过了验证块的逐字 relay", file=sys.stderr)
        print("  2. 验证块被表格化/改写/增删了行", file=sys.stderr)
        print("  3. append_log_entry.py 版本过旧（< v3.13.0），未产出令牌", file=sys.stderr)
        print("📌 修复：重新逐字 relay append_log_entry.py stdout 末尾的验证块（含🔖流程完成令牌行）。", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
