#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""buluotuo_panel.py v0.1 — 布洛陀神经态可视化聚合器（引擎类·stats·跨工具中立）

把已存在的真实信号源聚合成「壮族铜鼓活面板」单文件 HTML：
  - evolution_deviation_<日期>.json  → 愿景四方向误差量化（鼓心太阳纹亮度）
  - route_evolution_suggest_<日期>.json → 路由自进化漏触发（羽人信号流）
  - 守卫编写规范.md 注册表 → 守卫/引擎家族规模（蛙·守护）
  - 进度看板.md 各端接入率 → 链路覆盖缺口（第二仪表·诚实并排）

设计原则（守布洛陀宪法）：
  - 填值权归脚本：所有数字来自真实文件，AI 不编。
  - 真实性>丰富度：健康度100% 与 接入率55% 两仪表并排，不藏缺口。
  - 跨工具中立：产物=本地单文件 HTML，不绑任何工具，离线可看。
  - 壮族语呈现：铜鼓(goengqreng)/太阳纹/蛙(守护)/羽人(布洛陀鸟首人身·路由)/米洛甲(镜像生成)。
  - 失败放行：任一源读不到 → 该块标「信号静默」(N/A由脚本产出)，exit 0。

用法：python3 buluotuo_panel.py  → 输出 HTML 到 可视化呈现/铜鼓活面板.html
"""
import os
import sys
import json
import re
import glob
from datetime import datetime

MC = os.path.expanduser("[记忆共享中心]")
SYSLOG = os.path.join(MC, "开发工具/logs/runtime")
DEV = os.path.join(MC, "开发工具")
GUARD_SPEC = os.path.join(MC, "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md")
KANBAN = os.path.join(MC, "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md")
OUT_DIR = os.path.join(MC, "可视化呈现")
OUT = os.path.join(OUT_DIR, "铜鼓活面板.html")


def latest_json(prefix):
    try:
        fs = sorted(glob.glob(os.path.join(SYSLOG, prefix + "_*.json")))
        return fs[-1] if fs else None
    except Exception:
        return None


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def parse_guard_counts():
    """从守卫编写规范.md 取家族规模（真相源=注册表总数行）。"""
    try:
        txt = open(GUARD_SPEC, encoding="utf-8").read()
        m = re.search(r"守卫类\s*(\d+)\s*\+\s*引擎类\s*(\d+)", txt)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return None, None


def parse_platform_rates():
    """从进度看板.md 取各端接入率（真相源=§一·五 表）。"""
    out = {}
    try:
        txt = open(KANBAN, encoding="utf-8").read()
        for m in re.finditer(r"\|\s*\*\*(.+?)\*\*\s*\|\s*\*\*(\d+)/11\s*\((\d+)%\)", txt):
            out[m.group(1)] = {"rate": int(m.group(2)), "pct": int(m.group(3))}
    except Exception:
        pass
    return out


def build_svg(dirs, health, guard_n, engine_n, radar_hits, route_total, suggest_top):
    """壮族铜鼓 SVG。鼓心太阳纹亮度=overall_health；蛙=守卫；羽人=路由信号。"""
    # 太阳纹亮度：health(0~1) → 金光强度
    glow = int(120 + 135 * (health if health is not None else 0.0))
    glow_hex = "#%02X%02X%02X" % (glow, glow, int(glow * 0.7))
    rays = ""
    for i in range(12):
        ang = i * 30
        rays += (f'<line x1="400" y1="400" x2="400" y2="250" '
                 f'transform="rotate({ang} 400 400)" '
                 f'stroke="{glow_hex}" stroke-width="6" stroke-linecap="round" opacity="0.9"/>')
    # 四方向节点（鼓面内环）
    labels = [
        ("全自动化", dirs.get("auto_rate", {}).get("actual")),
        ("越用越好用", dirs.get("gets_better", {}).get("route_audit_total")),
        ("自主进化", dirs.get("autonomous_evolution", {}).get("actual")),
        ("越懂使用者", dirs.get("knows_user_better", {}).get("actual_new_30d")),
    ]
    nodes = ""
    for i, (name, val) in enumerate(labels):
        ang = i * 90 + 45
        import math
        r = 150
        x = 400 + r * math.cos(math.radians(ang - 90))
        y = 400 + r * math.sin(math.radians(ang - 90))
        val_s = "—" if val is None else str(val)
        nodes += (f'<g transform="translate({x:.0f},{y:.0f})">'
                  f'<circle r="34" fill="#3a2a12" stroke="#caa15a" stroke-width="2"/>'
                  f'<text y="-6" text-anchor="middle" fill="#e8d3a0" font-size="13">{name}</text>'
                  f'<text y="16" text-anchor="middle" fill="{glow_hex}" font-size="20" font-weight="bold">{val_s}</text>'
                  f'</g>')
    # 蛙（守护）环：画 12 只简化蛙 + 计数徽标
    frogs = ""
    for i in range(12):
        ang = i * 30
        frogs += (f'<circle cx="400" cy="120" r="9" fill="#7a5a22" '
                  f'transform="rotate({ang} 400 400)"/>')
    frog_badge = f"守卫 {guard_n}" if guard_n else "守卫 —"
    engine_badge = f"引擎 {engine_n}" if engine_n else "引擎 —"
    # 羽人路由信号（外环旋转的虚点，数量=雷达命中，封顶可视化）
    spin = (f'<animateTransform attributeName="transform" type="rotate" '
            f'from="0 400 400" to="360 400 400" dur="40s" repeatCount="indefinite"/>')
    signals = (f'<g opacity="0.8">{spin}'
               f'<circle cx="400" cy="95" r="4" fill="#9fe0ff"/>'
               f'<circle cx="400" cy="95" r="4" fill="#9fe0ff" transform="rotate(72 400 400)"/>'
               f'<circle cx="400" cy="95" r="4" fill="#9fe0ff" transform="rotate(144 400 400)"/>'
               f'<circle cx="400" cy="95" r="4" fill="#9fe0ff" transform="rotate(216 400 400)"/>'
               f'<circle cx="400" cy="95" r="4" fill="#9fe0ff" transform="rotate(288 400 400)"/>'
               f'</g>')
    return f'''
    <svg viewBox="0 0 800 800" width="100%" style="max-width:520px">
      <defs>
        <radialGradient id="drum" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="{glow_hex}"/>
          <stop offset="35%" stop-color="#b5832f"/>
          <stop offset="100%" stop-color="#5a3d12"/>
        </radialGradient>
      </defs>
      <circle cx="400" cy="400" r="385" fill="url(#drum)" stroke="#caa15a" stroke-width="6"/>
      <circle cx="400" cy="400" r="340" fill="none" stroke="#8a6a2a" stroke-width="2" opacity="0.6"/>
      {rays}
      <circle cx="400" cy="400" r="60" fill="#2a1c08" stroke="{glow_hex}" stroke-width="3"/>
      <text x="400" y="395" text-anchor="middle" fill="#e8d3a0" font-size="15">布洛陀</text>
      <text x="400" y="418" text-anchor="middle" fill="{glow_hex}" font-size="13">Baeuqloegdoz</text>
      {nodes}
      {frogs}
      <text x="400" y="150" text-anchor="middle" fill="#e8d3a0" font-size="14">🐸 {frog_badge}</text>
      <text x="400" y="660" text-anchor="middle" fill="#cfe8ff" font-size="13">羽人路由信号 · 雷达命中 {radar_hits}</text>
      <text x="400" y="685" text-anchor="middle" fill="#cfe8ff" font-size="12">米洛甲(镜像生成) · {engine_badge}</text>
      {signals}
    </svg>'''


def build_html():
    evo = load_json(latest_json("evolution_deviation")) or {}
    sug = load_json(latest_json("route_evolution_suggest")) or {}
    dirs = evo.get("directions", {})
    health = evo.get("overall_health")
    guard_n, engine_n = parse_guard_counts()
    rates = parse_platform_rates()
    radar_hits = sug.get("stats", {}).get("total_radar_hits_30d")
    route_total = dirs.get("gets_better", {}).get("route_audit_total")
    suggest_top = sug.get("suggestions", [])[:6]

    # 诚实双仪表
    auto = dirs.get("auto_rate", {})
    hermes_rate = rates.get("Hermes", {}).get("pct")
    health_disp = "—" if health is None else f"{health:.2f}"
    auto_disp = "—" if auto.get("actual") is None else f"{auto.get('actual'):.2f}"
    hermes_disp = "—" if hermes_rate is None else f"{hermes_rate}%"

    tips = "".join(
        f"<li><b>{s['skill']}</b> · 雷达命中 {s['radar_hits_30d']} 次 · 未入硬路由</li>"
        for s in suggest_top
    ) or "<li>信号静默（radar 数据未达）</li>"

    rate_rows = "".join(
        f"<tr><td>{k}</td><td>{v['rate']}/11</td><td>{v['pct']}%</td></tr>"
        for k, v in rates.items()
    ) or "<tr><td colspan='3'>信号静默</td></tr>"

    svg = build_svg(dirs, health, guard_n, engine_n, radar_hits, route_total, suggest_top)

    html = f'''<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>布洛陀铜鼓活面板</title>
<style>
:root{{
  --void-900:#07050a; --void-700:#140d04; --void-500:#1a1206; --void-300:#241808;
  --bronze:#caa15a; --bronze-dim:#8a6a2a; --bronze-deep:#5a3d12;
  --cyan:#00f0ff; --green:#05ffa1; --magenta:#ff2a6d; --gold:#fcee0a;
  --text:#e8d3a0; --text-dim:#a98f5a; --text-mute:#7a663a;
  --glow-bronze:0 0 12px rgba(202,161,90,.55),0 0 28px rgba(202,161,90,.28);
  --glow-cyan:0 0 10px rgba(0,240,255,.6),0 0 24px rgba(0,240,255,.3);
  --glow-green:0 0 10px rgba(5,255,161,.6),0 0 24px rgba(5,255,161,.3);
  --glow-mag:0 0 10px rgba(255,42,109,.6),0 0 24px rgba(255,42,109,.3);
  --mono:'JetBrains Mono','SF Mono',ui-monospace,monospace;
  --disp:'Rajdhani','PingFang SC',system-ui,sans-serif;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{color-scheme:dark;-webkit-font-smoothing:antialiased}}
body{{background:var(--void-500);color:var(--text);font-family:var(--disp);
  min-height:100dvh;padding:28px;overflow-x:hidden;line-height:1.5}}
body::after{{content:'';position:fixed;inset:0;pointer-events:none;z-index:9998;opacity:.045;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.5) 2px,rgba(0,0,0,.5) 4px);}}
h1{{font-family:var(--disp);font-size:clamp(1.4rem,1.1rem+1vw,2.1rem);font-weight:700;
  letter-spacing:.04em;color:var(--bronze);text-shadow:var(--glow-bronze);text-transform:uppercase}}
.wrap{{display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start;margin-top:20px}}
.panel{{background:linear-gradient(160deg,var(--void-300),var(--void-700));
  border:1px solid var(--bronze-deep);border-radius:4px 14px 4px 14px;
  padding:20px;min-width:300px;box-shadow:inset 0 0 30px rgba(0,0,0,.5),0 0 18px rgba(202,161,90,.08)}}
.panel h3{{font-size:clamp(.95rem,1.3vw,1.15rem);color:var(--bronze);letter-spacing:.03em;
  text-transform:uppercase;margin-bottom:14px;border-bottom:1px solid var(--bronze-deep);padding-bottom:8px}}
.meter{{margin:14px 0}}
.meter small{{display:block;font-family:var(--mono);font-size:11px;color:var(--text-dim);
  letter-spacing:.05em;margin-bottom:5px;text-transform:uppercase}}
.bar{{height:16px;background:var(--void-900);border:1px solid var(--bronze-deep);border-radius:3px;overflow:hidden}}
.fill{{height:100%;background:linear-gradient(90deg,var(--bronze-dim),var(--bronze));box-shadow:var(--glow-bronze)}}
.fill.green{{background:linear-gradient(90deg,#03a969,var(--green));box-shadow:var(--glow-green)}}
.fill.cyan{{background:linear-gradient(90deg,#0097a7,var(--cyan));box-shadow:var(--glow-cyan)}}
.fill.mag{{background:linear-gradient(90deg,#b31248,var(--magenta));box-shadow:var(--glow-mag)}}
.val{{font-family:var(--mono);font-size:13px;color:var(--text);margin-top:4px}}
table{{border-collapse:collapse;width:100%;font-size:13px;font-family:var(--mono)}}
td,th{{border:1px solid var(--bronze-deep);padding:6px 9px;text-align:left;color:var(--text)}}
th{{color:var(--bronze);font-weight:600}}
ul{{list-style:none;font-size:13px}}
ul li{{padding:5px 0;border-bottom:1px dashed var(--bronze-deep);color:var(--text)}}
ul li b{{color:var(--cyan);text-shadow:var(--glow-cyan);font-family:var(--mono)}}
.legend{{font-size:12px;color:var(--text-dim);margin-top:18px;line-height:1.9;
  border-top:1px solid var(--bronze-deep);padding-top:12px}}
.note{{font-size:11px;color:var(--text-mute);margin-top:12px;font-family:var(--mono);line-height:1.6}}
.tag{{display:inline-block;font-family:var(--mono);font-size:10px;color:var(--void-500);
  background:var(--bronze);padding:2px 7px;border-radius:2px;letter-spacing:.05em}}
</style></head><body>
<h1>🥁 布洛陀铜鼓活面板 · 神经态聚合</h1>
<div class="wrap">
  <div class="panel">{svg}</div>
  <div class="panel">
    <h3>诚实双仪表 <span class="tag">真实性 &gt; 丰富度</span></h3>
    <div class="meter"><small>①误差量化健康度（鼓心亮度）</small>
      <div class="bar"><div class="fill green" style="width:{float(health_disp)*100 if health else 0}%"></div></div>
      <div class="val">{health_disp}</div></div>
    <div class="meter"><small>①全自动化率（已接链路通不通）</small>
      <div class="bar"><div class="fill cyan" style="width:{float(auto_disp)*100 if auto.get('actual') else 0}%"></div></div>
      <div class="val">{auto_disp}</div></div>
    <div class="meter"><small>②Hermes 端接入率（该接的接没接·缺口）</small>
      <div class="bar"><div class="fill mag" style="width:{hermes_rate or 0}%"></div></div>
      <div class="val">{hermes_disp} · 缺口 {100-(hermes_rate or 0)}%</div></div>
    <h3 style="margin-top:22px">各端接入率</h3>
    <table><tr><th>平台</th><th>已接</th><th>%</th></tr>{rate_rows}</table>
  </div>
  <div class="panel">
    <h3>🪶羽人路由自进化信号（漏触发 Top6）</h3>
    <ul>{tips}</ul>
    <div class="val" style="margin-top:12px;color:var(--text-dim)">雷达近30天总命中：{radar_hits or '—'} · route_audit 累计：{route_total or '—'}</div>
    <div class="val" style="color:var(--text-dim)">🐸守卫 {guard_n or '—'} · 🌾米洛甲引擎 {engine_n or '—'}</div>
  </div>
</div>
<div class="legend">
  🥁 铜鼓(goengqreng)=整个活系统 · ☀️太阳纹十二芒=愿景四方向误差量化 · 🐸蛙=守卫家族(守护) ·
  🪶羽人(布洛陀鸟首人身)=路由信号流 · 🌾米洛甲(创世女神)=镜像/生成层 · ⚡雷=反馈/未知未知路由
</div>
<div class="note">数据真相源：evolution_deviation / route_evolution_suggest（{evo.get('date','—')}）· 守卫编写规范注册表 · 进度看板§一·五。
填值权归脚本，AI 只回显。本面板不编任何数。设计源文件：自定义层/待完成工作/布洛陀铜鼓活面板设计哲学.md</div>
</body></html>'''
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[buluotuo_panel] 已生成 {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(build_html())
