#!/usr/bin/env python3
# REG: family=哲学读侧注入钩子 | registry=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md§四 | board=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md
# -*- coding: utf-8 -*-
"""
philosophy_radar_inject.py v0.1 — 哲学读侧完整性专项 · P0 到达腿（UserPromptSubmit 注入钩子）

设计定位（哲学读侧完整性专项-S级方案 §三 P0.2 + §二「到达=注入而非文件」判据）：
- 到达面断链根治：加待读文件＝没人读（循环），唯有"注入"才让 AI 每次会话第一眼就看见近 72h 在动的哲学。
- 形态复用 kb_inject_prompt 家族：stdin JSON 协议 → 委托 hook_protocol.emit 单真源出 json
  （⛔裸文本会被本端产品判 winner=none 整轮丢弃·宿主收讫律）。
- 阈值闸防噪声（Hermes「接了制造噪声」判例）：① 雷达空 → 静默零开销；② 仅"会话首轮"注入
  （按 payload.session_id 去重，同会话后续轮不再刷）；③ 注入 ≤5 行。
- 快照可能隔天才跑 → 按条目 mtime 现值再筛一次 72h 窗口，⛔不注入陈旧项。

失败默认放行（Hook 三纪律）：任何异常一律不注入、exit 0，绝不阻断对话。

用法：
  echo '{"session_id":"s1","prompt":"...","cwd":"/x"}' | python3 philosophy_radar_inject.py UserPromptSubmit --hook-protocol=json
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import json
from datetime import datetime

BASE = os.path.expanduser("[记忆共享中心]/脚本中心")
sys.path.insert(0, BASE)
try:
    import hook_protocol as _hp
except Exception:
    _hp = None

RADAR = os.path.join(BASE, "logs", "philosophy_radar.jsonl")
STATE = os.path.join(BASE, "logs", ".philosophy_inject_seen.json")
DEGRADE_LOG = os.path.join(BASE, "logs", "philosophy_inject_degrade.jsonl")
WINDOW_H = 72
MAX_LINES = 5
STATE_CAP = 500
MARK = "【哲学近72h变动·变更雷达】"

_PAYLOAD = {}


def _load_radar(window_h=WINDOW_H):
    """读雷达快照，按 mtime 现值再筛 72h，最新在前。快照缺失/坏 → 空（静默）。"""
    out = []
    now = datetime.now().timestamp()
    try:
        with open(RADAR, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                ms = d.get("mtime_s")
                if ms is None:
                    continue
                try:
                    if now - float(ms) > window_h * 3600:
                        continue
                except (TypeError, ValueError):
                    continue
                out.append(d)
    except FileNotFoundError:
        return []
    except Exception:
        return []
    out.sort(key=lambda r: float(r.get("mtime_s", 0)), reverse=True)
    return out


def _load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _save_state(data):
    try:
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data[-STATE_CAP:], f, ensure_ascii=False)
        os.replace(tmp, STATE)
    except Exception:
        pass


def _emit(ctx):
    """委托 hook_protocol 单真源判端发形态；真源缺失 → 降级裸文本并留痕（⛔不静默）。"""
    if _hp is not None:
        return _hp.emit(ctx, payload=_PAYLOAD, argv=sys.argv[1:],
                        event="UserPromptSubmit", script=os.path.basename(__file__))
    try:
        with open(DEGRADE_LOG, "a", encoding="utf-8") as f:
            f.write('{"reason":"hook_protocol import failed","script":"philosophy_radar_inject.py"}\n')
    except Exception:
        pass
    if ctx:
        sys.stdout.write(ctx)
    return "text"


def build_ctx(entries):
    lines = ["%s 近72h有 %d 个哲学文件在动——先扫最新几个再开口（读侧完整性雷达·治「读脚本夹就以为读完」）："
             % (MARK, len(entries))]
    for r in entries[:MAX_LINES]:
        flag = "🆕新建" if r.get("new") else "改"
        lines.append("  %s %s ｜域 %s ｜版本 %s"
                     % (flag, r.get("file", "?"), r.get("domain", "?"), r.get("version", "?")))
    lines.append("📌 全量见 开发工具/logs/philosophy_radar.jsonl；读完请记阅读台账（P1）。")
    return "\n".join(lines)


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    global _PAYLOAD
    if raw and raw.strip():
        try:
            p = json.loads(raw)
            if isinstance(p, dict):
                _PAYLOAD = p
        except ValueError:
            _PAYLOAD = {}
    sid = str(_PAYLOAD.get("session_id", "")).strip() if isinstance(_PAYLOAD, dict) else ""

    entries = _load_radar()
    if not entries:
        return 0                                  # 雷达空 → 静默零开销
    if sid and sid in _load_state():
        return 0                                  # 非会话首轮 → 静默
    ctx = build_ctx(entries)
    if sid:
        st = _load_state()
        if sid not in st:
            st.append(sid)
        _save_state(st)
    _emit(ctx)
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as e:                          # 失败默认放行·不阻断对话
        sys.stderr.write("philosophy_radar_inject 异常（放行）：%s\n" % e)
        rc = 0
    sys.exit(rc if rc in (2,) else 0)  # 步2:检红/软失败归0,rc=2透传保留(若有拦截语义)
