# version: v0.5
# 家族：变换（改） ｜ 部署形态：按需
"""dsh_session_repair.py — DSH 会话事件流修复：补 message 事件缺失/错误的 role 字段。

背景（2026-09-10 根因根治）
--------------------------
DSH 会话校验（dsh-session assertMessageEventShape）要求 4 类 message 事件的 role 严格等于：
    system/message → "system" | user/message → "user"
    assistant/message → "assistant" | tool/result → "user"
不满足 → 该会话加载失败：`session event at seq N message must have role "user"`。

根因：DSH 运行写入路径（dsh-agent-loop 把 pre-step 决策消息 append 为 user/message）
对**插件注入消息**不补 role；而 dsh-session-persistence-jsonl 的迁移/规范化路径会补
（normalizeLegacySteering 显式补 role:"user"）→ 于是迁移后新写入的 plugin 注入事件缺 role。

本工具：给这类事件补正确 role（其余字段一字不动），并可选重写 zstd。
契约遵循在插件侧修（注入消息带 role）；本工具负责**存量数据修复**。

用法
----
  python3 dsh_session_repair.py --scan [--root DIR]            # 只扫描报告（默认 ~/.dsh/sessions）
  python3 dsh_session_repair.py --fix --session <uuid|dir>      # 修复单个会话（备份+原子替换）
  python3 dsh_session_repair.py --fix --all                     # 修复全部（逐个备份+原子替换）
  python3 dsh_session_repair.py --verify <file.jsonl.zstd>      # 校验单个文件是否合规
  python3 dsh_session_repair.py --fix --all --dry-run           # 只打印将改什么，不写

安全
----
① 修复前原文件 → `<name>.bak-<YYYYMMDD-HHMMSS>-prerepair`（只增不删）
② 原子替换（同目录临时文件 → os.replace）
③ 只补 role，⛔不改其他字段、不动 seq / 行序 / 行数
④ 修复后自动回扫确认 0 坏事件，否则报错不动
"""
# 2026-09-10：launchd 巡逻以 /usr/bin/python3(3.9) 运行本脚本，PEP 604 注解（`str | None`）
# 在 3.9 下 import 期即抛 TypeError —— 巡逻静默停摆（17:12 实测）。惰性注解使脚本对解释器版本免疫。
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime

ROOT_DEFAULT = os.path.expanduser("~/.dsh/sessions")
# 与 dsh-session MESSAGE_ROLE_BY_TYPE 严格对齐（单一真相源=DSH 源码）
MESSAGE_ROLE_BY_TYPE = {
    "system/message": "system",
    "user/message": "user",
    "assistant/message": "assistant",
    "tool/result": "user",
}


def decompress(path: str) -> bytes:
    r = subprocess.run(["zstd", "-d", "-c", path], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"zstd 解压失败: {r.stderr.decode(errors='replace')[:200]}")
    return r.stdout


# ⚠️ 2026-09-10 二次事故根治 —— 帧契约
# DSH 加载器 dsh-session-persistence-jsonl 的 assertZstdHeaderFrame 要求：
#   **第一个 zstd 帧必须恰好只含 header 那一行**（plaintext.indexOf(10) === plaintext.length-1），
#   事件放后续帧。早期版本这里用 `zstd -q -o` 整文件压成单帧 → 首帧含全部事件
#   → 抛 "first frame is not exactly one header line" → 整个 session/list 失败
#   → 侧栏只剩当前会话（"重启后只剩一条"事故根因）。
# 现改为逐行成帧（对齐 DSH 自身 ~1 行/帧的写法 + XXH64 校验），用 node 的 zstdCompressSync。
_FRAME_JS = (
    "const fs=require('node:fs'),z=require('node:zlib');"
    "const p=fs.readFileSync(process.argv[1]);const ch=[];let s=0;"
    "for(let i=0;i<p.length;i++){if(p[i]===10){ch.push(p.subarray(s,i+1));s=i+1;}}"
    "if(s<p.length)ch.push(p.subarray(s));"
    "fs.writeFileSync(process.argv[2],Buffer.concat(ch.map(c=>z.zstdCompressSync(c,"
    "{params:{[z.constants.ZSTD_c_checksumFlag]:1}}))));"
)

# 批量帧体检（单进程·判据与下面 first_frame_ok/frame_states 一致；输出违规文件 JSON 数组）
_BATCH_FRAME_JS = (
    "const fs=require('node:fs'),z=require('node:zlib');"
    "const files=process.argv.slice(1);const bad=[];"
    "for(const f of files){"
    "try{const b=fs.readFileSync(f);const t=z.zstdDecompressSync(b).toString();"
    "if(!(t.length>0 && t.indexOf(String.fromCharCode(10))===t.length-1)) bad.push(f);}"
    "catch(e){bad.push('ERR '+f);}}"
    "process.stdout.write(JSON.stringify(bad));"
)



# ---------------------------------------------------------------- v0 内容契约门禁
_PACKED_TAGS = ("text-chunks", "reasoning-chunks", "tool-call-chunks")


def v0_contiguity(rows: list):
    """v0 遗留格式的**加载硬契约**：每行 seq === 递增事件计数（packed 行按 payload 长度计）。

    判据来源（⛔非推测·与宿主逐行对齐）：dsh-session-format-v0-to-v1/lib/index.js scanRows()
      · 非 packed：`seq !== eventCount` → 抛 `released Session row N has seq gap (expected X, got Y)`
      · packed（text-chunks/reasoning-chunks/tool-call-chunks）：firstSeq === eventCount，
        eventCount += payload.length（payload = data.texts 或 data.args）
    有效性验证（2026-09-10）：对**已被宿主拒绝**的文件复现出同一处 (row 6, expected 6, got 7)；
    对修复后文件与 15:11 已知可加载基准均全通过 ⇒ 判据与宿主一致。
    rows：不含 header 的事件行 list[dict]。
    """
    exp = 0
    for i, e in enumerate(rows, 1):
        t = e.get("type")
        if t in _PACKED_TAGS:
            s = e.get("seq0")
            d = e.get("data") or {}
            payload = d.get("texts") if isinstance(d.get("texts"), list) else d.get("args")
            n = len(payload) if isinstance(payload, list) else None
            if n is None:
                return False, f"row {i - 1} packed 行缺 payload（无法判定计数）"
        else:
            s = e.get("seq"); n = 1
        if s != exp:
            return False, f"released Session row {i - 1} has seq gap (expected {exp}, got {s})"
        exp += n
    return True, "ok"


def _v0_gate(data: bytes) -> None:
    """写盘前内容契约门禁：文件头 version==0 时强制 seq 连续，违者拒绝落盘。

    为什么焊在这里（2026-09-10 五次事故同族根治）：本函数是**唯一写入口**，
    帧契约自检已在此内建；v0 的加载硬契约同理——⛔不靠各写手记得自查
    （实证：dsh_session_fix_seq.py 删中间 title 行 → 10 个老会话整会话加载失败）。
    """
    text = data.decode("utf-8", "replace")
    first, _, rest = text.partition("\n")
    try:
        header = json.loads(first)
    except Exception:
        return
    if not isinstance(header, dict) or header.get("version") != 0:
        return
    rows = []
    for line in rest.splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            raise RuntimeError("v0 门禁：事件行 JSON 解析失败 → 拒绝落盘")
    ok, detail = v0_contiguity(rows)
    if not ok:
        raise RuntimeError(f"v0 seq 连续性契约不满足（{detail}）→ 拒绝落盘（落盘后宿主将无法加载该会话）")


# ---------------------------------------------------------------- 宿主全链核验（权威判据）
# ⛔与宿主逐字对齐：用 @deepseek-ai/dsh-session-format-catalog 的 createRestore 跑 v0→v3 完整恢复链，
#   和宿主读会话时走的**同一条**代码路径。判据不如"复刻"可信？——这里干脆不复刻：
#   唯一真相源=宿主自身模块（只读引用·⛔不内联规则副本）。
_CHAIN_JS = (
    "const fs=require('node:fs');"
    "const {sessionFormatCatalog}=require('/usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/"
    "@deepseek-ai/dsh-session-format-catalog/lib/index.js');"
    "const lines=fs.readFileSync(process.argv[1],'utf8').split('\\n').filter(l=>l.trim());"
    "try{const h=JSON.parse(lines[0]);"
    "const r=sessionFormatCatalog.createRestore(h,{recovery:'recoverable',validation:'transformed'});"
    "const ctx={emitEvent:()=>{},emitRun:()=>{}};"
    "for(let i=1;i<lines.length;i++){try{r.decodeRow(JSON.parse(lines[i]),ctx);}"
    "catch(e){process.stdout.write('ERR row'+(i-1)+': '+String(e.message).slice(0,110));process.exit(0);}}"
    "r.finish(ctx);process.stdout.write('OK');}"
    "catch(e){process.stdout.write('ERR fatal: '+String(e.message).slice(0,110));}"
)


def chain_restore_ok(path: str):
    """宿主全链核验：返回 (ok, detail)。路径须是**已解压的 jsonl**（避免二次解压开销）。"""
    r = subprocess.run(["node", "-e", _CHAIN_JS, path], capture_output=True)
    out = r.stdout.decode(errors="replace").strip()
    return out == "OK", out or "ERR 核验未输出"


def compress(data: bytes, out_path: str) -> None:
    """写 zstd 会话文件，保持 DSH 帧契约（首帧=header 一行）。

    🔴 2026-09-10 四次事故根治 —— 契约自检**内建**在本函数内（⛔不靠调用方记得调
    assert_frame_contract）。三次复发的共同形状是"新写手只回验内容、没人验帧契约"
    （title_batch 的 `zstd -q -o` 单帧、/tmp/seqfix.py 的同款写法）→ 坏文件静默落盘 →
    整个 session/list 失败 → 侧栏只剩当前会话。写入口自证合规后，任何 import 本函数的
    写路径（含未来新增的）自动被物理门禁覆盖：违规即删临时产物 + 大声抛错，⛔不落盘。
    """
    _v0_gate(data)                       # v0 内容契约门禁（★唯一写入口自证·违者落不了盘）
    plain_tmp = out_path + ".plain"
    with open(plain_tmp, "wb") as fh:
        fh.write(data)
    try:
        r = subprocess.run(["node", "-e", _FRAME_JS, plain_tmp, out_path], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"逐行成帧失败: {r.stderr.decode(errors='replace')[:200]}")
    finally:
        if os.path.exists(plain_tmp):
            os.unlink(plain_tmp)
    ok, state = first_frame_ok(out_path)
    if not ok:
        try:
            os.unlink(out_path)
        except OSError:
            pass
        raise RuntimeError(
            f"帧契约不合规（{state}）：首帧必须恰好只含 header 一行 —— 拒绝落盘（临时产物已删除）"
        )


def first_frame_ok(path: str) -> tuple[bool, str]:
    """帧契约体检：首帧是否恰好只含 header 一行（与 DSH assertZstdHeaderFrame 等价）。

    ⚠️ 判据实现细节：Node 的 zstdDecompressSync **只解压第一帧**，
    故对"整文件压成单帧"的坏文件会返回全部内容 → indexOf(10) ≠ length-1 → 判不合规。
    判据唯一实现在 frame_states()（本函数只是它的单文件壳），⛔不许再写第二份。
    """
    state = frame_states([path]).get(path, "ERR:体检未返回结果")
    return state == "OK", state


def frame_states(paths: list) -> dict:
    """批量帧契约体检（单 node 进程·49 文件 ≈0.2s；逐文件起 node 则 ≈7.5s）。

    返回 {path: "OK" | "BAD" | "ERR:<原因>"}。判据与 DSH assertZstdHeaderFrame 等价：
    Node 的 zstdDecompressSync 只解压**第一帧** → 首帧必须恰好是一行 header。
    提速的意义：体检足够便宜，才能把"检测窗口"从 15 分钟压到 1 分钟（快守卫）。
    """
    out = {p: "OK" for p in paths}
    if not paths:
        return out
    r = subprocess.run(["node", "-e", _BATCH_FRAME_JS] + list(paths), capture_output=True)
    try:
        bad = json.loads(r.stdout.decode(errors="replace") or "[]")
    except Exception:
        return {p: "ERR:批量体检输出无法解析" for p in paths}
    for item in bad:
        if isinstance(item, str) and item.startswith("ERR "):
            out[item[4:]] = "ERR:解压失败"
        else:
            out[item] = "BAD"
    return out


def assert_frame_contract(path: str) -> None:
    """写盘前物理门禁：帧契约不合规即抛错（⛔不允许静默落盘）。

    教训（2026-09-10）：两条写路径都只回验**内容**（role/title），**没人验帧契约**
    → title_batch 的单帧压缩让 48 个会话全部加载失败 → 侧栏只剩当前会话。
    2026-09-10 四次事故后：本断言内建于 compress()（写入口自证），调用方无需再记着调它。
    """
    ok, state = first_frame_ok(path)
    if not ok:
        raise RuntimeError(f"帧契约不合规（{state}）：首帧必须恰好只含 header 一行 —— 拒绝落盘")


def message_slot(ev: dict):
    """返回该事件的 message 字典引用位置：user/message 在 data 顶层，其余在 data.message。"""
    t = ev.get("type")
    if t not in MESSAGE_ROLE_BY_TYPE:
        return None
    d = ev.get("data")
    if not isinstance(d, dict):
        return None
    if t == "user/message":
        return d
    m = d.get("message")
    return m if isinstance(m, dict) else None


def find_bad(events: list) -> list:
    """返回 [(行号, seq, type, 当前role, 应为role)]。"""
    bad = []
    for i, ev in enumerate(events):
        t = ev.get("type")
        if t not in MESSAGE_ROLE_BY_TYPE:
            continue
        msg = message_slot(ev)
        if msg is None:
            continue
        expected = MESSAGE_ROLE_BY_TYPE[t]
        if msg.get("role") != expected:
            bad.append((i, ev.get("seq"), t, msg.get("role"), expected))
    return bad


def load_events(path: str) -> list:
    raw = decompress(path)
    events = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events


def serialize(events: list) -> bytes:
    return ("\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n").encode("utf-8")


def session_files(root: str) -> list:
    return sorted(
        p for p in glob.glob(os.path.join(root, "*", "*", "session*.jsonl.zstd*"))
        if ".bak-" not in p
    )


def cmd_scan(root: str) -> int:
    files, bad_total, bad_files, skipped = 0, 0, 0, 0
    for path in session_files(root):
        files += 1
        try:
            events = load_events(path)
        except Exception as e:
            # ⚠️ skip 必须计数（2026-09-10 假绿根治）：原实现只打印不计数，而汇总与返回码
            #    都只看 bad_total → 缺 zstd/node 时 47 个文件全被跳过仍报「0 个损坏」绿灯。
            #    空测量产出绿灯 = 全绿幻觉（S006）——诊断路径谎报会直接误导排查人。
            skipped += 1
            print(f"  [skip] {path}: {e}")
            continue
        bad = find_bad(events)
        if bad:
            bad_files += 1
            bad_total += len(bad)
            print(f"❌ {os.path.basename(os.path.dirname(path))}  events={len(events)}  坏={len(bad)}")
            for _, seq, t, role, expected in bad[:6]:
                print(f"     seq={seq} type={t} role={role!r} → 应为 {expected!r}")
            if len(bad) > 6:
                print(f"     … 另 {len(bad)-6} 条")
    print(f"\n扫描 {files} 个会话文件：{bad_files} 个损坏 / 坏事件 {bad_total}")
    if skipped:
        print(f"⚠️ {skipped}/{files} 个文件无法解析（zstd/node 不可达或文件损坏）——「0 个损坏」不可信")
    return 1 if (bad_total or skipped) else 0


def repair_one(path: str, dry_run: bool = False) -> bool:
    events = load_events(path)
    bad = find_bad(events)
    if not bad:
        print(f"✅ {os.path.basename(os.path.dirname(path))}: 无需修复")
        return True
    print(f"🔧 {os.path.basename(os.path.dirname(path))}: 补 {len(bad)} 处 role")
    for i, seq, t, role, expected in bad:
        msg = message_slot(events[i])
        msg["role"] = expected
        print(f"     seq={seq} {t}: {role!r} → {expected!r}")
    if dry_run:
        print("     (dry-run·未写盘)")
        return True
    # 修后自校验（物理拦截：不合规不落盘）
    still = find_bad(events)
    if still:
        print(f"     ❌ 修复后仍不合规 {len(still)} 处 → 放弃写盘")
        return False
    data = serialize(events)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{path}.bak-{ts}-prerepair"
    subprocess.run(["cp", path, backup], check=True)
    tmp = f"{path}.tmp-{ts}"
    compress(data, tmp)
    # 回验：临时文件可解压且 0 坏
    verify_payload = load_events(tmp)
    if find_bad(verify_payload):
        os.remove(tmp)
        print("     ❌ 临时文件回验失败 → 放弃替换（原文件与备份均在）")
        return False
    os.replace(tmp, path)
    print(f"     ✅ 已替换（备份 {os.path.basename(backup)}）")
    return True


def cmd_fix(root: str, session: str | None, all_: bool, dry_run: bool) -> int:
    if session:
        cand = [p for p in session_files(root)
                if session in p or session == os.path.basename(os.path.dirname(p))]
        if not cand:
            print(f"未找到会话：{session}")
            return 1
        targets = cand
    elif all_:
        targets = session_files(root)
    else:
        print("需指定 --session 或 --all")
        return 1
    ok = 0
    failed = []
    skipped_v0 = 0
    for p in targets:
        # 🔴 v0 跳过守卫（2026-09-10 第七次事故根治·第二层损坏的真凶关闭）
        #   为什么：本工具的"补 role"输出的是**当前格式语义**；而 v0 迁移器
        #   （dsh-session-format-v0-to-v1）要求 user/message 载荷是 released-v0 形状——
        #   带上 role 后它会按当前格式校验 → 要求 id → 插件注入消息本无 id →
        #   `refuses this format v0 Session: ... lacks required member "id"` → 整个会话历史加载失败。
        #   v0 的 role 由迁移器自行归一（normalizeLegacyMessage），⛔不需要也不许本工具代劳。
        if os.path.basename(p) == "session.jsonl.zstd":
            skipped_v0 += 1
            continue
        # 单文件容错（2026-09-10）：会话文件可能正被宿主写入（zstd 解压/JSON 解析瞬时失败），
        # ⛔不得让单点失败中断整批（否则巡逻/自愈 script exit 1 且无诊断）——记录后继续。
        try:
            if repair_one(p, dry_run):
                ok += 1
            else:
                failed.append(os.path.basename(os.path.dirname(p)))
        except Exception as e:
            failed.append(f"{os.path.basename(os.path.dirname(p))}:{type(e).__name__}")
    print(f"\n处理 {len(targets)} 个文件，成功 {ok}" + (f"（v0 跳过 {skipped_v0}）" if skipped_v0 else ""))
    if failed:
        print(f"⚠️ 失败 {len(failed)}: {', '.join(failed[:6])}")
    return 0 if not failed else 1


def cmd_verify(path: str) -> int:
    events = load_events(path)
    bad = find_bad(events)
    if bad:
        print(f"❌ 不合规 {len(bad)} 处")
        for _, seq, t, role, expected in bad[:10]:
            print(f"   seq={seq} {t} role={role!r} → 应为 {expected!r}")
        return 1
    print(f"✅ 合规（{len(events)} 事件）")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="DSH 会话事件流 role 修复")
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--session")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify")
    a = ap.parse_args()
    if a.verify:
        sys.exit(cmd_verify(a.verify))
    if a.scan:
        sys.exit(cmd_scan(a.root))
    if a.fix:
        sys.exit(cmd_fix(a.root, a.session, a.all, a.dry_run))
    ap.print_help()


if __name__ == "__main__":
    main()
