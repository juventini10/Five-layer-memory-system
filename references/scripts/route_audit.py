#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route_audit.py v0.3 — Stop 钩子审计：观测硬路由命中 Skill 的漏判率（P2 第②步·只记录不注入）
v0.3（2026-08-27）：审计器自身四处失明根治——①Qoder CN transcript 的 role 在顶层 `type`/`message.role`，旧代码只读 `d["role"]` ⇒ 本端 0 记录（含我自己的两次绕过全未留痕）；②`task_of` 收到的是**注入后**的 prompt 全文（17/20 条机器块），新增 strip_injected() 只留人话，并识别 `humanInput` 字段（无该字段的 user 行=系统代发，不作审计对象）；③覆盖判定窗口无界 ⇒ 后续一次真实调用会洗掉先前的绕过，改为场景终点=下一条 user 消息；④EVIDENCE_WORDS["triwich"] 9 词→2 词（triwich/三明智），清除第一性原理/靠谱吗/确定吗等泛词——泛词作证据词违背本脚本自述的硬信号原则，且 4 条记录是路由引擎自己打的「【路由引擎硬匹配】」提示被再次审计=自命中。旧 v0.2 行保留作历史。
v0.2（2026-08-24）：新增 predicted_skill_id/predicted_bucket 显式标签字段 + actual_skill_id/actual_bucket（initially null，待 deviation 仪表盘两账对账后回填）；旧 skills/triggers 字段保留向后兼容。

挂为 Qoder CN 原生 Stop 钩子（~/.qoder-cn/settings.json）。
每次主代理结束响应时，通过 stdin 传入 JSON，含 transcript_path（完整对话 JSONL）。
本脚本解析对话：

  - 判定"硬路由命中场景"：最后一则 user 任务经 router.route() 命中 ≥1 个 Skill；
    不含触发词的延续任务（"继续""按建议推进"）向前回溯最多 3 则 user 消息
    找最近的命中场景（回溯范围内找不到 → exit 0 不记）。
  - 判定"是否覆盖"：场景任务之后全部文本（含工具调用渲染）搜该 Skill 的证据词
    （name 字段 + 中文名/别名）——含 → 视为可能已触发（讨论/调用均不记）；
    不含 → 追加 1 条审计日志 {ts, task, skills, triggers, potential_miss:true}。
  - 其余一切情况 → 退出码 0 = 放行（绝不拦截、绝不误写）。

设计原则（失败默认放行，绝不破坏对话）：
  - 解析异常 / 无 transcript_path / 行损坏 → 直接 exit 0
  - 无命中场景 → exit 0（不写）
  - 判定保守：宁可漏记不可误记（误记=审计噪音污染 miss 率）
  - 任何未捕获异常 → exit 0

⚠️ 已知边界：模型执行 Skill 时不一定提名字 → potential_miss 是"疑似漏判"线索，
  最终对账看系统日志（两账比对：路由日志"应该命中" vs 系统日志"实际做了"）。
  消费端：--stats 子命令统计（两周基线后人工对账）。

用法：
  echo '{"transcript_path": "..."}' | python3 route_audit.py        # Stop 钩子模式
  echo '{"transcript_path": "..."}' | python3 route_audit.py --src qodercn  # 标注来源工具（分源对账）
  python3 route_audit.py --stats                                     # 统计
  python3 route_audit.py --self-test                                 # 内置自测

--src 参数（2026-08-13）：多工具接入同一账本后，src 区分触发来源（qodercn/workbuddy/openclaw-cron），
  8/22 两账对账按工具维度统计；缺省默认 stop-audit（向后兼容旧挂载点）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import re
import json
try:
    import fcntl
except ImportError:
    fcntl = None  # Windows 无 fcntl → 跳过文件锁（降级无锁追加，不崩）
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from router import route, SKILLS  # 单一真源：路由核心改一处，审计跟着走

DEFAULT_LOG = os.path.expanduser("[记忆共享中心]/脚本中心/logs/route_audit.jsonl")
LOG_PATH = os.environ.get("ROUTE_AUDIT_LOG", DEFAULT_LOG)  # 测试可重定向
MAX_BACKTRACK = 3  # 延续任务回溯深度

# 证据词：Skill 的 name 字段 + 中文正式名（场景后文本搜到即视为覆盖）
# 原则：只取硬信号（Skill 名/正式名/执行标志），不用触发词/泛词——否则回复提词即覆盖=审计空转
EVIDENCE_WORDS = {
    "awaken-memory-system": ["awaken-memory-system", "awaken", "小美", "我美吗"],
    "chrold": ["chrold", "色界"],
    "excavator": ["excavator", "挖掘机", "需求挖掘", "客户报告"],
    "clock-loop": ["clock-loop", "反方向的钟", "闭环"],
    "daily-buddy": ["daily-buddy", "每日伙伴"],
    "good-good-study": ["good-good-study", "好好学习"],
    "growth-box": ["growth-box", "成长箱"],
    "meta-aletheia": ["meta-aletheia", "迁理之外"],
    "scriyore": ["scriyore", "手写的从前"],
    "shall-we-talk": ["shall-we-talk"],
    "skill-forge": ["skill-forge"],
    "sucair": ["sucair", "读书助手", "知识包"],
    "system-logger": ["system-logger", "系统日志"],
    "triwich": ["triwich", "三明智"],
    "热点捕手": ["热点捕手"],
    "素然启镜": ["suran-qijing", "素然启镜"],
    "win-ps1-python-resolution": ["win-ps1-python-resolution", "setup.ps1", "Find-Python", "Windows 安装包静默失败", "Get-Command 畸形前缀"],
}


INJECTED_BLOCKS = (
    "<system-reminder>",
    "【知识库激活",
    "【路由引擎硬匹配】",
    "【SSOT 格式契约",
    "[Attached file:",
    "[cron:",
)


def strip_injected(text):
    """剔掉平台/钩子注入的提示块——审计只对人说的话负责。

    2026-08-27 实测：账本 20 条 triwich 漏判中 17 条 task 首部是注入文本
    （其中 4 条是路由引擎自己打的「【路由引擎硬匹配】」提示被再次审计=自命中）。
    """
    out = []
    for seg in re.split(r"(?=<system-reminder>)", text):
        for block in INJECTED_BLOCKS:
            idx = seg.find(block)
            if idx >= 0:
                seg = seg[:idx]
        out.append(seg)
    return "\n".join(out).strip()


def task_of(msg_text):
    """提取 user 消息中的任务描述（<user_query> 标签优先，无标签用全文）"""
    m = re.search(r"<user_query>(.*?)</user_query>", msg_text, re.S)
    return strip_injected((m.group(1) if m else msg_text).strip())


def read_transcript(path):
    """读 JSONL transcript → 返回 [(role, text)]，行损坏跳过。

    人话判定：能区分 humanInput 的端（Qoder CN 新版）只把带 humanInput 的
    user 行当任务——其余 user 行是压缩续接文本/Skill 正文回显/工具结果，
    实测本端 403 条 user 行仅 ~16 条为皮叔真实发言。
    """
    raw = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = d.get("message", {}).get("content")
            role = d.get("role") or (d.get("message") or {}).get("role") or d.get("type") or ""
            text = ""
            human = d.get("humanInput")
            has_human = isinstance(human, dict) and bool(human.get("text"))
            if has_human:
                text = human["text"]
            elif isinstance(content, list):
                parts = []
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    if c.get("text"):
                        parts.append(c["text"])
                    elif c.get("type") == "tool_use":
                        parts.append(c.get("name") or "")
                        inp = c.get("input") or {}
                        if isinstance(inp, dict):
                            for k in ("skill", "skill_name", "skill_id"):
                                if inp.get(k):
                                    parts.append(str(inp[k]))
                text = " ".join(p for p in parts if p)
            elif isinstance(content, str):
                text = content
            raw.append((role, text, has_human))

    human_capable = any(r == "user" and h for r, _, h in raw)
    msgs = []
    for role, text, has_human in raw:
        if human_capable and role == "user" and not has_human:
            role = "system"  # 系统代发的 user 行，不作人话审计
        msgs.append((role, text))
    return msgs


def find_last_hit_task(msgs):
    """找最后一则硬路由命中场景。返回 (任务, [(skill, 触发词)]) 或 (None, None)"""
    user_tasks = []
    for role, text in msgs:
        if role == "user":
            task = task_of(text)
            if task:
                user_tasks.append(task)
    if not user_tasks:
        return None, None
    for task in reversed(user_tasks[-MAX_BACKTRACK:]):
        hits = get_hits(task)
        if hits:
            return task, hits
    return None, None


def get_hits(task):
    """返回 [(skill, 命中触发词)]"""
    import router
    out = []
    for s in SKILLS:
        ok, hw, _ = router.hit(s, task)
        if ok and hw:
            out.append((s, hw))
    return out


def covered(after_text, skills):
    """场景后文本是否含任一命中 Skill 的证据词"""
    for s in skills:
        for w in EVIDENCE_WORDS.get(s, [s]):
            if w and w in after_text:
                return True
    return False


def append_log(entry):
    path = LOG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_UN)


def audit(transcript_path, src="stop-audit"):
    if not transcript_path or not os.path.isfile(transcript_path):
        return 0
    msgs = read_transcript(transcript_path)
    if not msgs:
        return 0
    task, hits = find_last_hit_task(msgs)
    if not task:
        return 0
    scene_start = None
    for i, (role, text) in enumerate(msgs):
        if role == "user" and task_of(text) == task:
            scene_start = i
            break
    if scene_start is None:
        return 0
    # 覆盖判定只搜「本轮助手回复」——用户原消息含触发词（如"系统日志"）不能算"已执行"；
    # 窗口必须止于下一条 user 行，否则后续轮次的真调用会洗白本轮绕过（2026-08-27 实测：
    # 21:23 绕过 triwich，因 21:26 真调用被无界窗口判为已覆盖）。
    scene_end = len(msgs)
    for j in range(scene_start + 1, len(msgs)):
        if msgs[j][0] == "user":
            scene_end = j
            break
    after_text = " ".join(t for role, t in msgs[scene_start:scene_end] if role == "assistant")
    skills = [s for s, _ in hits]
    if covered(after_text, skills):
        return 0  # 可能已触发（调用/讨论均视为覆盖），不记
    # predicted_skill_id = 主预测 Skill（skills[0] 为最高优先级）
    # predicted_bucket = 预测任务桶（skills[0]，与 Skill 同粒度的分类）
    # actual_skill_id / actual_bucket = 实际执行 Skill 与桶（initially null，待 deviation 仪表盘两账对账后回填）
    # potential_miss=True 时 actual_* 必为 null（执行未发生）
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "task": task[:100],
        "predicted_skill_id": skills[0] if skills else None,
        "predicted_bucket": skills[0] if skills else None,
        "actual_skill_id": None,  # 待 deviation 仪表盘两账对账后回填
        "actual_bucket": None,    # 同上
        "skills": skills,
        "triggers": {s: w[:6] for s, w in hits},
        "potential_miss": True,
        "src": src,
    }
    append_log(entry)
    return 0


def stats():
    path = LOG_PATH
    if not os.path.isfile(path):
        print("路由审计日志为空"); return 0
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    by_skill = {}
    for r in rows:
        for s in r.get("skills", []):
            by_skill[s] = by_skill.get(s, 0) + 1
    print(f"路由审计日志共 {len(rows)} 条疑似漏判")
    for s, n in sorted(by_skill.items(), key=lambda x: -x[1]):
        print(f"  {s}: {n}")
    print("提示：疑似漏判需与系统日志对账确认（两账比对：路由'应该命中' vs 日志'实际做了'）")
    return 0


def self_test():
    import tempfile
    import subprocess
    os.environ["ROUTE_AUDIT_LOG"] = tempfile.mktemp(suffix=".jsonl")
    # 用例1：任务命中 system-logger，回复含"系统日志" → 覆盖不记
    t1 = tempfile.mktemp(suffix=".jsonl")
    with open(t1, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>记入系统日志</user_query>"}]}}) + "\n")
        f.write(json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": "📝 系统日志已写入"}]}}) + "\n")
    # 用例2：任务命中 daily-buddy，回复无证据 → 记 potential_miss
    t2 = tempfile.mktemp(suffix=".jsonl")
    with open(t2, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>写今天的日记</user_query>"}]}}) + "\n")
        f.write(json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": "好的，已记录。"}]}}) + "\n")
    msgs1 = read_transcript(t1)
    t1_, h1 = find_last_hit_task(msgs1)
    ok1 = t1_ == "记入系统日志" and "system-logger" in [s for s, _ in h1]
    msgs2 = read_transcript(t2)
    t2_, h2 = find_last_hit_task(msgs2)
    ok2 = t2_ == "写今天的日记" and "daily-buddy" in [s for s, _ in h2]
    # 覆盖判定
    after1 = " ".join(t for _, t in msgs1[1:])
    ok3 = covered(after1, ["system-logger"]) is True
    # 坏输入
    p = subprocess.run([sys.executable, __file__], input="not json", capture_output=True, text=True)
    ok4 = p.returncode == 0
    print(f"用例1 命中判定（系统日志）: {'✅' if ok1 else '❌'}")
    print(f"用例2 命中判定（每日伙伴）: {'✅' if ok2 else '❌'}")
    print(f"用例3 覆盖判定: {'✅' if ok3 else '❌'}")
    print(f"用例4 坏输入 exit 0: {'✅' if ok4 else '❌'}")
    return 0 if all([ok1, ok2, ok3, ok4]) else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        sys.exit(stats())
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    src = "stop-audit"
    if len(sys.argv) > 2 and sys.argv[1] == "--src":
        src = sys.argv[2]
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    try:
        sys.exit(audit(payload.get("transcript_path"), src))
    except Exception:
        sys.exit(0)
