#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""panel_snapshot.py v0.9.7 — 愿景看板 v3（峰终体验版·渲染器）

你的定案（2026-08-21 愿景仪表盘 §10·任务交接）：
  看板从"静态分数清单"重构为"峰终体验 + 闭环流"的活系统呈现。
  - 峰值 = 闭环流（最大区块·检测→修正→免疫→抗体库·趋势图优先喂系统1）
  - 终点 = 一句话总结（峰终收尾·你记住的那句）
  - 中间 = 少而真（四方向原生数据·不合成·分数全去：北极星0.8/自动化率100%是虚荣指标）
  -   刷新即最新：panel_data.js?v={时间戳} cache_bust + fswatch/Stop 钩子重渲染

v0.9.7（2026-09-07·皮叔批准归属约定·补全 v0.9.6 根治的最后一段）：
  - 归属约定入报警文案：自动补登报警文本新增"收到本报警的端须在变更日志补一条归属说明"
    + 可直接复制的 changelog_append.py 补登模板（--tool <你的端名>·--desc 注明变更原因与归属）——
    自动补登只证明"检测到变动"，归属说明才记录"谁改的、为什么"；约定放在报警文案=各端收到
    报警时的唯一必读处，不依赖翻文档。
  - 与 v0.9.6 关系：v0.9.6 解决"变动必须留痕"（检测即留痕·机械兜底）；v0.9.7 解决"留痕必须可归属"。

v0.9.6（2026-09-07·皮叔令"帮我根治"·CatPaw 第17端接入漏登实证）：
  - 治理闸门根治：check_registry_governance 检测到注册表指纹变动且变更日志无「平台注册表」治理记录时，
    自动调 changelog_append.py 补登一条"检测留痕"（--target 透传账本路径·隔离压测同路径）——
    检测即留痕，不依赖端自觉（09-06 CatPaw 批次改 SSOT §二·七 加列却漏登·面板 09-07 才喊）。
    本次仍返回报警（提示相关端可补充变更说明）；下次运行命中记录即更新登记消警。
    根因（第一性原理）：修改注册表的动作与留痕动作无强制绑定→事后检测只喊不记=闭环断血。

v0.9.5（2026-09-02·童灵上岗·皮叔问"免疫为何0/自动化为何降"根因裁定）：
  - ① 全自动化卡去「审计闭环率(returncode==0)」陈旧误标：显示值=auto_rate.actual=hook_auto 触发占比（自动触发调用/总调用），
    而 returncode==0 可靠性=100%(legacy) 被旧标签冒用 → 改诚实标签「hook_auto 触发占比·愿景①=机制自动运转不依赖人记得」+显 returncode 成功=100%
  - ① 降值根因说明：74.7% 较上周 87.8% 下滑=手动调用累积拉低占比（离线守卫默认 manual + 本次调试重跑脚本计入），非自动化退化；机制可靠性仍 100%
  - 免疫环节去"复发拦截"误导框：闭环流 stage 改「免疫 · 复发监测（本周）」+ src 注「0=无复发=抗体生效」；②卡注「免疫命中=历史复发被捕获次数(证明闭环在跑·非未实现)·有效抗体=已建防复发规则」

v0.9.4（2026-09-02·童灵上岗·皮叔令"彻彻底底的解决"）：
  - 闭环流 ≤0 分支去「无未核销差」伪断言：该分支此前暗示"已逐项核销=0"，实情是 detected/fixed 两源独立计数（DRIFT 行 vs 变更日志 WorkBuddy 行），
    从无共同追踪 ID、从未做逐项核销 → 文案改为中性算术描述「检出 ≤ 留痕 · 粗口径」（两源独立计数·非核销）
  - A3（真 per-item 核销）根因裁定：detected 来自 platform_adaptation_check.log [DRIFT] 行、fixed 来自变更日志 WorkBuddy 行，二者无事件级关联键；
    要真核销须重构 checker 日志（每条 DRIFT 发唯一 ID）+ 修正规程（修复须引用该 ID）——属新建可验证基建，非本轮可得，且半吊子重建会造新伪信号
    → 童灵裁决：A3 当前架构不可行，A+B 即终态。差值只作「检出−留痕·粗口径·非核销」真实算术差，绝不作「积压/未闭合」解释

v0.9.3（2026-09-02·童灵上岗·皮叔令"只要符合愿景的最优解"）：
  - 免疫环节去粉饰：闭环流 immune 恒 0 经核为真实（免疫复发记录 26 条命中全落在 08-20~08-25，本周窗口内确无一命中），
    但原 summary「免疫拦截复发 0 次——调节回路在跑」= 拿 0 证成"在跑"·编造结论
    → 改条件化：imm>0 说"拦截复发 N 次"；imm==0 说"免疫本周无触发（末次 YYYY-MM-DD）"，把真实静默时长显出来（可观测）
  - 口径歧义根治：闭环流 immune 标注「（本周）」、四方向②免疫命中标注「（累计）」
    ——26(累计) vs 0(本周) 不再像矛盾读数；引擎侧增 immune_total/immune_last_date（累计口径·不受窗口限制）

v0.9.2（2026-09-02·皮叔令"面板只能有真实有效的数据"）：
  - 闭环流 pill 去「有积压信号」伪断言：差值=detected−fixed 是两不同源计数器的粗口径差（非逐项核销），
    「积压」是假解释 → 保留真实差值数字，改中性灰字「粗口径·非核销」（红 warn→neutral），不编造积压结论（立场卡#S602 看板数字须绑实录）
  - 内联 PANEL_DATA 进 HTML 单文件：去掉外部 panel_data.js + cache_bust，render 时直内联 window.PANEL_DATA
    → 根治「HTML 的 ?v 与 data 不同步→浏览器用旧缓存→你看到过期数」（原你见 10 实际 20）· 打开即最新

v0.8.0（2026-08-23·DSH 三明智 L1 评审整改·皮叔令"做到100分"）：
  - 一句话总结去因果包装："修复N个"→"留痕变更N条"（fixed 源=变更日志全量行，非检出项逐项核销）
    积压 pill 改"差值"语义+悬停标注粗口径——根治 max(0,det-fix)=0 的假阴性闭环宣告
  - ①面孔统一(A v2)：四方向卡「审计闭环 X% · 覆盖 N/M」与 OKR 区同源同读数·覆盖不并入目标线
    （原"自动检测20·免疫拦截14"与冻结口径 returncode==0 占比脱节=三面孔不可复算）
  - ④窗口标注+证据封顶：卡面同显本月/本季累计双窗口；state=过渡时 evidence 机械封顶🟡
    （代理计数不配🟢——记录量≠预测力，防虚荣温床）
  - 零外链化：移除 chart.js/fonts CDN，内联 SVG 趋势图（原生 <title> 悬停读数）——断网可渲染，
    全自动化不依赖外部服务；今日进行中数据不入图（防零值断崖）
  - 平台表列分离：「核验方式」独立文本列（机械/自核/自治），色通道只留给覆盖度——三色混义根治
  - 维护行单轴化：环节Top 与总量显式标注不同轴（原 58+33=91 与 32+25+23+15=95 同行无法对账）
  - PANEL_DATA 加载失败显式横幅（原静默回退快照值=违反"宁可少不要假"）
  - 新增价值层占位卡（北极星产出轴·待量化明示——S451 投资回收轴入口，不装假指标）
  - 配套：SSOT 方案文档 §十二 治理记录回写 + okr_quarter.json 注记去易变数值（注记派生化规则）

v0.7.5（2026-08-22·Hermes 平台专属守卫漏标 +1 修正）：
  - PATROL_EXTRA_SCRIPT 增 Hermes 项（hermes_read_evidence_guard.py·文件存在即 +1）
    ——根因：Hermes 走插件型（无 hook 命令列表可解析），extra_count 落 None → 看板 Hermes 专属守卫漏标 null
    ——但 Hermes 有真实专属守卫（hermes_read_evidence_guard.py·route-audit-hook _READ_EVIDENCE_SCRIPT 实挂）
    →改按"专属守卫脚本文件存在判真"计入，与 AutoClaw/LobsterAI/ZCode patrol 型记法一致
  - mark 三级（🟢机械/🟡自核/🔴需自治核对·解析自 SSOT §二·七 校验覆盖段）保持不变——该语义=校验登记状态，
    接入完备度已由 num/den 独立呈现，色块与数字不混
  - 验证：Hermes extra null→1·Trae Work/其他端不变·exit 0

v0.7（2026-08-22·你点名"季度目标板块漏看"·补上真实空缺·任务交接§五-B）：
  - 新增「🎯 季度 OKR 目标对照层」板块：本季目标线 vs 实际进度·每方向进度条
    （目标≥/当前/完成度+证据档位色·达标🟢/接近🟡≥70%/落后🔴）
  - 目标值←okr_quarter.json（SSOT·自定义层/待完成工作/okr_quarter.json）；当前值←evolution_deviation 机械映射
    （auto=auto_rate.actual / evo=autonomous_evolution.actual / knows=本季 by_month 累计 / better=待量化不上假指标）
  - 剩余天数=end−today 机械算；JS 动态注入（改 okr_quarter.json→重跑→刷新即变·cache_bust 保留）

v0.7.1（2026-08-22·结构性少定义定版落地·网页端同步）：
  - OKR evidence 改为机械判定（current vs target·达标🟢/接近🟡≥70%/落后🔴）·不照抄 okr_quarter.json 静态字段（防过渡冒充定案）
  - 四方向卡③改为「本季进化事件 N · 净采纳率 X%」新口径（旧"本周进化事件69"口径错·与OKR区背离）
  - 四方向卡 badge 与 OKR 区强一致（JS 读 four_dir.state + okr.evidence 更新徽标）+ 状态行「定案/过渡」可视
  - okr_quarter.json 删除死字段 evidence（机械判定接管·单一真相源）

v0.7.4（2026-08-22·诚实降档根治"自动化105%"与"平台缺N"同页打脸）：
  - OKR「全自动化」当前值 = min(审计闭环率 auto_rate.actual, 平台接入完备度)
    （完备度=已接满额且机械核验被审平台占比·⛔任一平台未满额/未机械核验→auto 卡自然降档）
    ——根治 auto_rate(returncode==0 占比 100%)与 Qoder Desktop/Hermes/Trae Work 缺额自相矛盾
  - auto 降档时保留诚实 note（不被 evolution json 的"审计闭环率"note 覆盖）
  - 平台接入标题改「已登记 N 端（🟢机械核验 M）」·⚠️不再用"已核验 N/N"冒充全机械
  - Trae Work 自签 🟢→🟡「自核签名·非机械核验（待补追）」（诚实区分 8 机械 + 1 自签）
  - LobsterAI 升机械校验第 8 端（--src lobsterai·读 openclaw.json/patrol/state-hooks 三源）
    ——推翻"运行时不可见"旧判定·运行时配置在 ~/Library/Application Support/LobsterAI/ 完全可读

数据源（只上线有数据源的指标·宁可少一个不要假指标）：
  closed_loop  ← evolution_deviation v0.3（检测DRIFT/修正WorkBuddy行/免疫命中/抗体🛡+7日趋势）
  四方向       ← evolution_deviation directions（原生数+证据档位🟢🟡🔴）
  维护成本     ← 环节维护台账.py（git log 按环节统计提交数/周·免人工免自评）
  平台接入率   ← 各端 settings.json 实盘直读 + SSOT 兜底
  季度 OKR     ← okr_quarter.json（目标 SSOT·本季框定）+ evolution_deviation（当前值机械映射）
"""
import os, json, glob, re, sys
from datetime import datetime

MC = os.path.expanduser("[记忆共享中心]")
SYSLOG = os.path.join(MC, "开发工具/logs/runtime")
TS_PATH = os.path.join(SYSLOG, "panel_timeseries.jsonl")
LIVE_HTML = os.path.join(MC, "可视化呈现/panel_live.html")
OKR_PATH = os.path.join(MC, "自定义层/待完成工作/okr_quarter.json")   # 季度目标 SSOT（详见愿景看板v3任务交接§五-B）

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

def check_registry_governance(platform_names, changelog_path=None, state_path=None):
    """A v2 治理闸门(机械化·S257 检测不得靠人纪律)：平台注册表变动 ↔ 变更日志治理记录 机械对账。
    返回 None=通过；返回 str=报警文案（主流程打印+注入OKR区红框）。
    对账规则：指纹变动时，变更日志.md 中须存在含「平台注册表」且日期≥上次登记日的行。
    v0.9.6 根治：无治理记录时自动补登"检测留痕"（走 changelog_append.py 唯一合法写入口·
    --target 透传账本路径=隔离压测同路径）——检测即留痕，不依赖端自觉；本次仍返回报警
    提示相关端可补充变更说明，下次运行命中记录即更新登记消警。"""
    import hashlib
    try:
        if changelog_path is None:
            changelog_path = os.path.join(MC, "变更日志.md")
        if state_path is None:
            state_path = os.path.join(MC, "可视化呈现", ".registry_state.json")
        fp = hashlib.sha1("|".join(sorted(platform_names or [])).encode("utf-8")).hexdigest()[:12]
        today = datetime.now().strftime("%Y-%m-%d")
        state = load_json(state_path) or {}
        if not state.get("fp"):
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump({"fp": fp, "since": today}, f, ensure_ascii=False)
            return None
        if state["fp"] == fp:
            return None
        old_fp = state.get("fp", "?")
        hit = False
        try:
            with open(changelog_path, encoding="utf-8") as f:
                for line in f:
                    if "平台注册表" in line and line.strip().startswith("|"):
                        d = line.strip().split("|")[1].strip()
                        if d >= state.get("since", ""):
                            hit = True
                            break
        except Exception:
            hit = False
        if hit:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump({"fp": fp, "since": today}, f, ensure_ascii=False)
            return None
        # v0.9.6 根治：无治理记录 → 自动补登"检测留痕"（不依赖端自觉）
        auto = False
        try:
            import subprocess
            append_py = os.path.join(MC, "开发工具", "changelog_append.py")
            desc = ("平台注册表变动检测留痕（fp {}→{}·{}平台）——panel_snapshot 治理闸门自动补登·"
                    "相关端可另补变更说明或回滚".format(old_fp, fp, len(platform_names or [])))
            r = subprocess.run(
                [sys.executable, append_py, "--tool", "panel_snapshot治理闸门",
                 "--file", "平台注册表", "--version", "—", "--desc", desc,
                 "--target", changelog_path],
                capture_output=True, timeout=60)
            auto = (r.returncode == 0)
        except Exception:
            auto = False
        if auto:
            return ("平台注册表已变动(原登记 {}·fp {}→{})——治理闸门已自动补登检测留痕。\n"
                    "归属约定(2026-09-07 你批准·所有端适用)：收到本报警的端须在变更日志补一条"
                    "归属说明，模板：\npython3 [记忆共享中心]/脚本中心/changelog_append.py "
                    "--tool \"<你的端名>\" --file \"平台注册表（SSOT §二·七）\" "
                    "--version \"<SSOT版本>\" --desc \"归属说明：<变更原因>\"\n"
                    "或回滚注册表改动".format(state.get("since", "?"), old_fp, fp))
        return ("平台注册表已变动(原登记 {}) 但变更日志无对应治理记录——"
                "请用 changelog_append.py 追加一行(--file 含「平台注册表」)，或回滚注册表改动".format(state.get("since", "?")))
    except Exception as e:
        return "治理闸门自身异常(不阻塞面板)：{}".format(e)

def load_kanban_rates():
    """从 SSOT（01-脚本架构设计通用规范.md §二·七 接入率行）机械解析各端接入率。
    根治手敲漂移：SSOT 改一处，面板自动对齐（铁律016·查实盘不查看板）。"""
    path = os.path.join(MC, "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/04-跨端接入指南.md")
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print("[panel_snapshot][WARN] 读取 SSOT 失败: {}".format(e), file=sys.stderr)
        return None
    def _plain(s):
        # 匹配前剥 markdown 装饰：文档给人加粗，不该把机器锚点震断
        # （2026-09-26 实证：SSOT 那行被写成「接入率（**分母=11」→ 字面锚点失配
        #   → 回退手敲兜底值 → 兜底是裸 int → 下游按 (num,den) 解包直接崩）
        return re.sub(r"[*_`]+", "", s)
    header = rate_line = None
    # 只认表格行，且必须在其上方 40 行内找到列头——否则 frontmatter 摘要里
    # 恰好同时含"接入率/分母"的散文行会被误当锚点（2026-09-26 改宽松匹配时实测踩中）
    for i, line in enumerate(lines):
        if not _plain(line).lstrip().startswith("|"):
            continue
        if not ("接入率" in _plain(line) and "分母" in _plain(line)):
            continue
        cand = None
        for j in range(i - 1, max(-1, i - 40), -1):
            if _plain(lines[j]).lstrip().startswith("|") and "Hook 脚本" in _plain(lines[j]):
                cand = lines[j]
                break
        if cand is None:
            continue  # 这行不是那张表的接入率行，继续往下找
        rate_line, header = line, cand
        break
    if not rate_line or not header:
        print("[panel_snapshot][WARN] SSOT 未找到接入率行，回退手敲值", file=sys.stderr)
        return None
    def cells(s):
        return [c.replace("**", "").strip() for c in s.strip().strip("|").split("|")]
    platforms = cells(header)[1:]
    raw_vals = cells(rate_line)[1:]
    out = {}
    for name, raw in zip(platforms, raw_vals):
        m = re.search(r"(\d+)/(\d+)", raw)
        if m:
            out[name] = (int(m.group(1)), int(m.group(2)))
        else:
            out[name] = None
    return out

def parse_kanban_rates():
    """各端接入率——直接派生自 SSOT（见 load_kanban_rates）。不再手敲。"""
    rates = load_kanban_rates()
    if rates:
        return rates
    # 兜底值⛔不得携带具体数字：手敲数字=漂移源（原注释自陈"已过时"），
    # 且其裸 int 形态违反 {平台:(num,den)} 契约。降级=如实标不可判(None)。
    print("[panel_snapshot][WARN] SSOT 接入率锚点未命中→各端接入率标为「不可判」"
          "（不回填手敲值）", file=sys.stderr)
    return {}

def _parse_coverage_from_ssot():
    """从 SSOT §二·七 校验覆盖段自动解析 🟢/🔴 标记（不硬编码）。
    返回 {平台名: (标记, 说明)}。
    """
    out = {}
    ssot_path = os.path.join(MC, "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/04-跨端接入指南.md")
    try:
        with open(ssot_path, encoding="utf-8") as f:
            txt = f.read()
    except Exception:
        return out
    # 找校验覆盖段：🟢机械校验=xxx·🔴需自治核对=xxx
    m = re.search(r"🟢机械校验=([^·]+)", txt)
    green_raw = m.group(1) if m else ""
    m = re.search(r"🔴需自治核对=([^·]+)", txt)
    red_raw = m.group(1) if m else ""
    # 清洗：去 bold 标记、按 / 分割、每段取开头英文平台名（去掉后续中文/括号内容）
    def clean(s):
        s = re.sub(r"\*\*", "", s)
        out = []
        for part in s.split("/"):
            part = part.strip()
            if not part:
                continue
            # 取开头连续的英文字母/数字（平台名），遇到中文/括号/空格停止
            m = re.match(r"^[a-zA-Z0-9\-]+", part)
            if m:
                out.append(m.group(0).lower().replace(" ", "").replace("-", ""))
        return out
    green_names = clean(green_raw)
    red_names = clean(red_raw)
    # 别名映射：SSOT 校验覆盖段中的特殊标识 → 平台名 key（lower+去空格）
    # 例：dsh → deepseekharness（DeepSeek Harness）
    alias_map = {"dsh": "deepseekharness"}
    green_set = set(green_names)
    red_set = set(red_names)
    for alias, mapped in alias_map.items():
        if alias in green_set:
            green_set.add(mapped)
        if alias in red_set:
            red_set.add(mapped)
    # 从 SSOT 表头获取平台名
    rates = load_kanban_rates() or {}
    for name in rates:
        key = name.lower().replace(" ", "").replace("-", "")
        if key in green_set:
            out[name] = ("🟢", "机械校验 · 登记自 SSOT §二·七")
        elif key in red_set:
            out[name] = ("🔴", "需自治核对 · 登记自 SSOT §二·七")
        # fallback: SSOT 表格中 "平台名 自核" 也视为已登记（但非机械核验→🟡 诚实区分）
        elif re.search(re.escape(name) + r"\s*自核", txt):
            out[name] = ("🟡", "自核签名 · 非机械核验（待补追）· 登记自 SSOT §二·七")
    return out

def load_live_rates():
    """实盘接入率：直接读各平台 settings.json hooks 算 11-Hook N/M。
    跳过"人更新 SSOT 文档"环节——配置一改，面板刷新即最新（愿景: 全自动化·减少人工）。
    2026-09-27 童灵根治：分母 12→11 对齐 SSOT §二·七（2026-09-12 裁定 l3_conclusion_guard
    全端永久关闭移出分母）与 platform_adaptation_check.py 现行口径——旧 12-Hook 分母
    给 Qoder CN/WorkBuddy 制造了假"缺 1"（实为 11/11 满额）。"""
    HOOKS11_WITH_CROSSEND = [
        "crossend_guard", "route_inject_prompt", "route_miss_feeder", "kb_inject_prompt",
        "route_unknown_unknown", "audit_search_kb", "route_audit", "route_guard_audit",
        "feedback_detect",
        "rule_three_layer_guard", "card_id_guard",
    ]
    PLATFORMS = [
        ("Qoder Desktop", os.path.expanduser("~/.qoder/settings.json"), True, "settings"),
        ("Qoder CN", os.path.expanduser("~/.qoder-cn/settings.json"), True, "settings"),
        ("WorkBuddy", os.path.expanduser("~/.workbuddy/settings.json"), False, "settings"),
        ("Hermes", os.path.expanduser("~/.hermes/config.yaml"), False, "hermes"),
    ]
    out = {}
    for name, cfg, denom_all, kind in PLATFORMS:
        try:
            if kind == "hermes":
                import yaml
                with open(cfg, encoding="utf-8") as f:
                    d = yaml.safe_load(f)
                enabled = d.get("plugins", {}).get("enabled", []) or []
                mounted = set()
                for h in HOOKS11_WITH_CROSSEND:
                    hook_plugin = {
                        "route_unknown_unknown": "route-audit-hook",
                        "route_audit": "route-audit-hook",
                        "route_guard_audit": "route-audit-hook",
                        "audit_search_kb": "route-audit-hook",
                        "feedback_detect": "route-audit-hook",
                        "rule_three_layer_guard": "route-audit-hook",
                        "card_id_guard": "route-audit-hook",
                    }.get(h)
                    if hook_plugin and hook_plugin in enabled:
                        mounted.add(h)
                # 2026-09-12 SSOT 裁定：统一分母 = 11（l3_conclusion_guard 全端永久关闭移出）
                out[name] = (len(mounted), len(HOOKS11_WITH_CROSSEND))
                continue
            with open(cfg, encoding="utf-8") as f:
                d = json.load(f)
            cmds = []
            for evt in ("SessionStart", "UserPromptSubmit", "Stop"):
                for it in d.get("hooks", {}).get(evt, []):
                    if "hooks" in it:
                        for hh in it["hooks"]:
                            cmds.append(hh.get("command", ""))
                    elif "command" in it:
                        cmds.append(it["command"])
            mounted = set(h for h in HOOKS11_WITH_CROSSEND if any(h in c for c in cmds))
            # 2026-09-12 SSOT 裁定：统一分母 = 11（l3_conclusion_guard 全端永久关闭移出）
            out[name] = (len(mounted), len(HOOKS11_WITH_CROSSEND))
        except Exception:
            out[name] = None
    return out

def load_okr():
    try:
        with open(OKR_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def compute_okr(platform_rates=None):
    """季度 OKR 目标对照层：读 okr_quarter.json（目标/本季框定）+ evolution_deviation（当前值机械映射）。
    铁律：目标值来自 JSON·当前值来自脚本输出·剩余天数=end−today 机械算——三处均不硬编码、不手填。
    platform_rates：{平台名:(num,den)} 或 SSOT 🟢/🔴 标注——auto 当前值据此做诚实降级
    （⛔禁止"审计闭环率 105%"与"平台接入缺 5"同页打脸·2026-08-22 你点名根治）。"""
    okr = load_okr()
    if not okr:
        return None
    # v0.9.8 季度机械轮转（2026-10-07 野根根治轮·Q3 已越界 7 天面板仍挂"剩余 -8 天"）：
    # SSOT 自带 derive 规则「当前季度由 today 的月份机械推导·不手填」——顶层 quarter/start/end
    # 在此按 today 现场推导覆盖手填残值；目标值(target)不动·不触价值层。
    try:
        import calendar as _cal
        _now = datetime.now()
        _qn = (_now.month - 1) // 3 + 1
        _m1 = _qn * 3
        okr["quarter"] = "%d-Q%d" % (_now.year, _qn)
        okr["start"] = "%d-%02d-01" % (_now.year, _qn * 3 - 2)
        okr["end"] = "%d-%02d-%02d" % (_now.year, _m1, _cal.monthrange(_now.year, _m1)[1])
    except Exception:
        pass
    dirs = (load_json(latest_json("evolution_deviation")) or {}).get("directions", {})
    today = datetime.now()
    try:
        end = datetime.strptime(okr["end"], "%Y-%m-%d")
        remaining = (end - today).days
    except Exception:
        remaining = None
    qstart, qend = okr.get("start")[:7], okr.get("end")[:7]  # "2026-07-01"→"2026-07"
    by_month = (dirs.get("knows_user_better", {}) or {}).get("by_month", {}) or {}
    def quarter_sum(bm):
        if not qstart or not qend:
            return None
        lo, hi = (qstart, qend) if qstart <= qend else (qend, qstart)
        return sum(v for k, v in (bm or {}).items() if lo <= k <= hi)

    rows = []
    for obj in okr.get("objectives", []):
        d = obj.get("dir")
        unit = obj.get("unit", "count")
        target = obj.get("target")
        current = None
        note = ""
        extra = {}  # v0.8.0：方向附加读数（仅 auto 使用·每轮重置防残留）
        if d == "auto":
            current = dirs.get("auto_rate", {}).get("actual")
            # 治理史注记：8/22 曾以 min(闭环率,完备度) 防打脸；2026-08-23 L3双Agent裁定 min() 焊死正交两轴
            # 且目标线压复合值可被分母游戏劫持 → A v2 双轴分离（覆盖为独立读数·治理闸门机械化对账）。
            pr = platform_rates or {}
            green_full = 0
            denom_pt = 0
            for _p, _v in pr.items():
                if not (isinstance(_v, (tuple, list)) and len(_v) == 2):
                    continue  # 形态不符=不可判：不进分母、不崩、不拿它冒充读数
                _n, _d = _v
                denom_pt += 1
                if _d and _n == _d:
                    green_full += 1
            platform_done = (green_full / denom_pt) if denom_pt else None
            if unit == "rate":
                auto_trigger_rate = current  # hook_auto触发占比原值（0~1）·2026-09-03童灵口径修正（旧名closure=审计闭环率已废弃）
                # A v2 双轴分离(2026-08-23 L3双Agent裁定·你"go")：目标线=hook_auto触发占比；
                # 平台覆盖 N/M 为独立环境读数，不再 min() 焊入名值——杀分母游戏激励，回归 §11.1 冻结口径。
                note = "A v2 双轴分离 · 目标线=hook_auto 触发占比({:.0%})·愿景①真义=机制自动运转不依赖人记得 · 手动调用累积拉低占比(非退化) · 平台覆盖 {}/{} 为独立读数·不并入目标进度".format(
                    auto_trigger_rate if auto_trigger_rate is not None else 0, green_full, denom_pt)
                if current is not None:
                    current = round(current * 100)
                # A v2 同源暴露：hook_auto触发占比(目标线)/覆盖独立读数随行输出（min下界概念废除）
                extra = {
                    "auto_closure": current,  # 兼容旧消费方·2026-09-03童灵修正：实际是hook_auto触发占比非审计闭环率
                    "auto_trigger_rate": current,  # 2026-09-03童灵新增：正确命名
                    "auto_closure_rate": dirs.get("auto_rate", {}).get("auto_closure_rate"),  # 第二指标：自动闭环率（2026-09-03童灵新增·数据积累中可能为None）
                    "auto_coverage": dirs.get("auto_rate", {}).get("coverage"),  # 覆盖面（2026-09-03童灵实事求是根治：机械计算有埋点的守卫数）
                    "auto_done": round(platform_done * 100) if platform_done is not None else None,
                    "auto_cov": "{}/{}".format(green_full, denom_pt),
                    "auto_breakdown": dirs.get("auto_rate", {}).get("breakdown"),  # 2026-09-03童灵透明度提升：分母构成
                }
            else:
                if platform_done is not None and current is not None:
                    current = round(current * platform_done, 2)
        elif d == "evo":
            # 挑战线=净采纳率(愿景③质量·adoption_rate)：进度条测它；底盘事件数放 note 补充
            ar = dirs.get("autonomous_evolution", {}).get("adoption_rate")
            if ar is not None:
                current = round(ar * 100)
            unit = "rate"
            target = obj.get("challenge_target", target)  # 挑战线覆盖底盘 target
            ev = dirs.get("autonomous_evolution", {}).get("actual")
            note = "本季进化事件 {} · 净采纳率 · 抗刷量/存量无牵引".format(ev if ev is not None else "—")
        elif d == "knows":
            current = quarter_sum(by_month)
            cur_month = dirs.get("knows_user_better", {}).get("count")
            note = "本季 by_month 累计 · 当月 {} 条 · 自然月归当月".format(cur_month if cur_month is not None else "—")
        elif d == "better":
            # 2026-09-27 童灵根治：transition_baseline=免疫命中÷有效抗体（倍数语义·本次抗体 0→39 修复后
            # 首次有值即暴露"基线 2349%"+OKR 假绿 100%——旧代码按百分比乘 100 塞进"高好"进度条，
            # 而该读数是低好方向（目标≤0.8倍=抗体覆盖住复发），方向语义进渲染层前须经你定案。
            # ⛔宁可 N/A 待量化，不上假绿（面板红条幅原话：宁可少，不要假）。
            # 定案口径=漏触发修复率（两池 join·现值 0.078 待治理），届时由脚本接管 current。
            tb = dirs.get("gets_better", {}).get("transition_baseline")
            im = dirs.get("gets_better", {}).get("immune_hits")
            fb = dirs.get("gets_better", {}).get("fanbu_antibodies")
            # 10-07 终审轮：定案口径=漏触发修复率(活跃)——state=定案 且 活跃join有值时脚本接管 current
            if (dirs.get("gets_better", {}).get("state") == "定案"
                    and dirs.get("gets_better", {}).get("join_rate_active") is not None):
                current = min(round(dirs["gets_better"]["join_rate_active"] * 100), 100)
            if im is not None and fb is not None and tb is not None:
                note = "过渡读数=免疫 {}/抗体 {} = {:.1f} 倍（每抗体摊命中·低好方向·待定案不进进度条）· 定案=漏触发修复率(两池join现值{:.3f})".format(
                    im, fb, tb, dirs.get("gets_better", {}).get("join_rate") or 0)
        target_pct = round(target * 100) if (unit == "rate" and target is not None) else target
        if not note:
            note = obj.get("note", "")
        # v0.7.2：note 统一优先读 evolution json（口径单一真相源，含定案/过渡/证据）
        # 根治实测漂移：better 已定案（baseline93%/join92%），面板 note 却还硬编码"过渡基线·待池统一"。
        # 改口径只改 evolution json（脚本生成），面板永不再回落旧档。
        _d2j = {"auto": "auto_rate", "better": "gets_better",
                "evo": "autonomous_evolution", "knows": "knows_user_better"}
        # auto 降档时保留诚实 note（平台完备度口径），⛔不让 evolution json 的"hook_auto触发占比"note 覆盖——
        # 否则 67% 的卡配"hook_auto触发占比105%"的note又重演割裂（2026-08-22 你点名根治·2026-09-03童灵口径修正）。
        if d in _d2j and (d != "auto" or not note.startswith("min(")):
            _jn = dirs.get(_d2j[d], {}).get("note")
            if _jn:
                note = _jn
        # 机械 evidence（v0.7.1·你结构定案·不照抄静态字段防过渡冒充定案）：
        #   count 型：达成🟢 否则🔴（过渡目标同理·不硬标达标）
        #   rate  型：≥100% 达成🟢 · ≥70% 接近🟡 · 否则落后🔴
        mec_ev = "🔴"
        if current is not None and target not in (None, 0):
            if unit == "count":
                mec_ev = "🟢" if current >= target else "🔴"
            else:
                ratio = current / (target * 100)  # current 已是百分比数
                mec_ev = "🟢" if ratio >= 1.0 else ("🟡" if ratio >= 0.7 else "🔴")
        # v0.8.0 证据封顶：state=过渡的方向，代理计数再高也只配🟡（记录量≠预测力·防虚荣温床）
        _st = dirs.get(_d2j.get(d, ""), {}).get("state") if d in _d2j else None
        if _st == "过渡" and mec_ev == "🟢":
            mec_ev = "🟡"
        evidence = mec_ev if current is not None else obj.get("evidence", "🔴")
        row = {
            "dir": d, "name": obj.get("name"), "unit": unit,
            "target": target, "target_pct": target_pct, "current": current,
            "evidence": evidence, "remaining": remaining, "note": note,
            "formula": obj.get("formula", ""),  # v0.8.1 公式随行输出(口径SSOT=okr_quarter.json·静态语义)
            "fidelity": obj.get("fidelity", ""),  # v0.9.1 构念保真度档位(防盲目自信·2026-08-23你质证)
            "measures": obj.get("measures", ""),  # v0.9.1 测什么/不测什么明示
        }
        row.update(extra)
        rows.append(row)
    return {
        "quarter": okr.get("quarter"), "start": okr.get("start"), "end": okr.get("end"),
        "remaining": remaining, "objectives": rows,
    }

def load_knowledge_ladder():
    """L1-L4 知识内化阶梯（2026-08-26 童灵执行·管道打通后入板）
    数据源：INDEX.md（L1-L4 分布·机械解析）+ 引用台账（L4 试金石）
    """
    stats = {"L1": 0, "L2": 0, "L3": 0, "L4": 0}
    idx = os.path.join(MC, "AI学习库/INDEX.md")
    try:
        with open(idx, encoding="utf-8") as f:
            for line in f:
                m = re.search(r"\| 立场卡#S\d+.*?\|\s*(L[1-4])", line)
                if m:
                    stats[m.group(1)] += 1
    except Exception as e:
        print("[panel_snapshot][WARN] INDEX 读取失败: {}".format(e), file=sys.stderr)
    # L4 试金石：引用台账中引用≥3 的卡（含你决策引用数）
    ledger = os.path.join(MC, "AI学习库/引用台账.md")
    counts = {}
    try:
        with open(ledger, encoding="utf-8") as f:
            for line in f:
                if line.startswith("|") and "#S" in line:
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    if len(cells) >= 4 and cells[0].startswith("#S"):
                        cid = cells[0]
                        c = counts.setdefault(cid, {"total": 0, "ge": 0})
                        c["total"] += 1
                        if "你决策" in cells[3]:
                            c["ge"] += 1
    except Exception as e:
        print("[panel_snapshot][WARN] 引用台账读取失败: {}".format(e), file=sys.stderr)
    probe = None
    for cid, c in sorted(counts.items(), key=lambda x: -x[1]["total"]):
        if c["total"] >= 3:
            probe = {"card": cid, "total": c["total"], "ge": c["ge"]}
            break
    # 技能卡候选数量（V0.2·2026-08-26新增·统计候选台账中待确认+提醒中）
    skill_candidates = 0
    cand_ledger = os.path.join(MC, "AI学习库/技能卡候选台账.md")
    try:
        with open(cand_ledger, encoding="utf-8") as f:
            for line in f:
                # 只匹配候选记录表中的行：以|开头+包含日期(YYYY-MM-DD)+状态为待确认或提醒中
                if line.startswith("|") and re.search(r"\d{4}-\d{2}-\d{2}", line) and ("待确认" in line or "提醒中" in line):
                    skill_candidates += 1
    except Exception:
        pass
    return {"stats": stats, "l4_probe": probe, "skill_candidates": skill_candidates, "updated": datetime.now().strftime("%Y-%m-%d")}


def take_snapshot():
    today = datetime.now().strftime("%Y-%m-%d")
    snap = {"date": today, "source": "panel_snapshot.py v0.9.1"}
    evo = load_json(latest_json("evolution_deviation")) or {}
    dirs = evo.get("directions", {})

    # ★ 闭环流（v0.6 峰值数据源）
    cl = evo.get("closed_loop", {}) or {}
    snap["closed_loop"] = {
        "detected": cl.get("detected"),
        "fixed": cl.get("fixed"),
        "immune": cl.get("immune"),
        "immune_total": cl.get("immune_total"),
        "immune_last_date": cl.get("immune_last_date"),
        "antibodies": cl.get("antibodies"),
        "pending": cl.get("pending"),
        "trend": cl.get("trend_7d", []),
        "sources": cl.get("sources", {}),
    }
    snap["cl_detected"] = cl.get("detected")
    snap["cl_fixed"] = cl.get("fixed")
    snap["cl_immune"] = cl.get("immune")
    snap["cl_immune_last"] = cl.get("immune_last_date")

    # 四方向原生数据（v0.6：状态+原生数+证据档位·分数全去）
    snap["auto_rate"] = dirs.get("auto_rate", {}).get("actual")
    snap["regulator_activity"] = dirs.get("regulator_activity", {}).get("actual")
    snap["regulator_last"] = dirs.get("regulator_activity", {}).get("last_week")
    snap["evo_events"] = dirs.get("autonomous_evolution", {}).get("actual")
    snap["evo_evidence"] = dirs.get("autonomous_evolution", {}).get("evidence")
    snap["evo_adoption_rate"] = dirs.get("autonomous_evolution", {}).get("adoption_rate")
    snap["evo_state"] = dirs.get("autonomous_evolution", {}).get("state")
    snap["auto_state"] = dirs.get("auto_rate", {}).get("state")
    snap["auto_closure_rate"] = dirs.get("auto_rate", {}).get("auto_closure_rate")  # 第二指标：自动闭环率（2026-09-03童灵新增·数据积累中可能为None）
    snap["auto_coverage"] = dirs.get("auto_rate", {}).get("coverage")  # 覆盖面（2026-09-03童灵实事求是根治：机械计算有埋点的守卫数）
    snap["auto_breakdown"] = dirs.get("auto_rate", {}).get("breakdown")  # 2026-09-03童灵透明度提升：分母构成（total/hook_auto/manual/other）
    snap["better_state"] = dirs.get("gets_better", {}).get("state")
    snap["better_immune_hits"] = dirs.get("gets_better", {}).get("immune_hits")
    snap["better_antibodies"] = dirs.get("gets_better", {}).get("fanbu_antibodies")
    snap["better_join_active"] = dirs.get("gets_better", {}).get("join_rate_active")
    snap["better_join_all"] = dirs.get("gets_better", {}).get("join_rate")
    snap["better_pool"] = dirs.get("gets_better", {}).get("antibody_pool_dual")
    snap["better_evidence"] = dirs.get("gets_better", {}).get("evidence")
    snap["better_baseline"] = dirs.get("gets_better", {}).get("transition_baseline")
    snap["better_join_rate"] = dirs.get("gets_better", {}).get("join_rate")
    snap["better_note"] = dirs.get("gets_better", {}).get("note")
    snap["knows_state"] = dirs.get("knows_user_better", {}).get("state")
    snap["new_30d"] = dirs.get("knows_user_better", {}).get("actual_new_30d")  # 兼容旧字段=当月数
    snap["knows_current_month"] = dirs.get("knows_user_better", {}).get("current_month")
    snap["knows_count"] = dirs.get("knows_user_better", {}).get("count")
    snap["knows_days_left"] = dirs.get("knows_user_better", {}).get("days_left_in_month")
    snap["knows_evidence"] = dirs.get("knows_user_better", {}).get("evidence")
    sug = load_json(latest_json("route_evolution_suggest")) or {}
    st = sug.get("stats", {})
    snap["uncovered_skills"] = st.get("uncovered_skills")

    # 维护成本（环节台账·git log 派生）
    tai = load_json(latest_json("环节维护台账")) or {}
    snap["maintenance"] = {
        "total_commits": tai.get("total_commits"),
        "segments": [
            {"segment": s.get("segment"), "commits": s.get("commits_7d")}
            for s in (tai.get("segments") or [])[:6]
        ],
    }

    # 实盘优先：workbuddy/qoder-cn/qoder-desktop 直接读配置；其余平台回退 SSOT
    live = load_live_rates() or {}
    ssot = parse_kanban_rates() or {}
    merged = {}
    for name in ssot:
        lv = live.get(name)
        # 实盘直读若返回 None（如 Hermes yaml 分支异常）也回退 SSOT——否则 None 覆盖 SSOT 值 → 假"未解析"
        merged[name] = lv if lv is not None else ssot.get(name)
    for name in live:
        merged.setdefault(name, live[name])
    snap["platform_rates"] = merged
    snap["knowledge_ladder"] = load_knowledge_ladder()   # 知识内化流（L1-L4）
    snap["okr"] = compute_okr(platform_rates=merged)

    # 知识库可视化3模块数据（2026-09-08 童灵根治·合并入panel_snapshot.py）
    kb_metadata_path = os.path.join(MC, "可视化呈现/data/kb_metadata.json")
    try:
        with open(kb_metadata_path, encoding="utf-8") as f:
            snap["knowledge_base"] = json.load(f)
    except Exception as e:
        print("[panel_snapshot][WARN] kb_metadata.json 读取失败: {}".format(e), file=sys.stderr)
        snap["knowledge_base"] = None
   # 季度 OKR 目标对照层（auto 卡含平台完备度诚实边界）
    return snap

def already_has_date(date):
    try:
        with open(TS_PATH, encoding="utf-8") as f:
            for line in f:
                if line.strip() and json.loads(line).get("date") == date:
                    return True
    except Exception:
        pass
    return False

def append_snapshot(snap):
    os.makedirs(os.path.dirname(TS_PATH), exist_ok=True)
    with open(TS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")

def read_timeseries():
    rows = []
    try:
        with open(TS_PATH, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    except Exception:
        pass
    return sorted(rows, key=lambda x: x.get("date", ""))

def build_summary(cl):
    """一句话总结（峰终·终点）——自动生成·数据说话·缺源明说。
    v0.8.0 因果安全措辞：fixed 源=变更日志全量行，≠"对检出项的修复"——⛔不用因果动词暗示管线闭合
    （你最高原则"宁可少一个指标，不要一个假指标"+数学之美卡4 信息熵测试）。"""
    det, fix, imm = cl.get("detected"), cl.get("fixed"), cl.get("immune")
    if det is None or fix is None or imm is None:
        missing = [k for k, v in (("检出", det), ("留痕", fix), ("免疫", imm)) if v is None]
        return "闭环数据采集中——{} 数据源待接入（宁可少一个，不要假指标）".format("、".join(missing))
    imm_last = cl.get("immune_last_date")
    if imm:
        imm_txt = "免疫拦截复发 {} 次".format(imm)
    else:
        imm_txt = "免疫本周无触发" + ("（末次 {}）".format(imm_last) if imm_last else "（无历史命中记录）")
    text = "本周自动检出偏差 {} 次 · 留痕变更 {} 条 · {}".format(det, fix, imm_txt)
    if det > fix:
        text += " · 检出−留痕差值 {}（粗口径·非逐项核销）".format(det - fix)
    return text

def _fmt_okr_val(v, unit):
    if v is None:
        return "—"
    return (str(v) + "%") if unit == "rate" else str(v)

def build_okr_html(snap):
    """季度 OKR 目标对照层（本季目标线 vs 实际进度）。目标值来自 okr_quarter.json·当前值来自脚本·机械算。"""
    okr = snap.get("okr")
    if not okr:
        return '<div class="card wide okr"><h3>🎯 季度 OKR <span style="font-size:11px;color:var(--amber);font-weight:400">数据源缺失（okr_quarter.json 未读到）</span></h3><div class="sub">季度目标线待接入——只上线有数据源的指标</div></div>'
    rows = ""
    for i, o in enumerate(okr.get("objectives", []), 1):
        unit = o.get("unit")
        tgt = o.get("target_pct")
        cur = o.get("current")
        tgt_txt = "目标 ≥" + (_fmt_okr_val(tgt, unit)) if tgt is not None else "目标 —"
        if cur is None:
            cur_lbl, st_lbl, fill_cls, width = "N/A", "待量化", "f-gray", 0
        else:
            denom = tgt or 1
            pct = cur / denom * 100
            disp = min(round(pct), 100)  # A v2: 目标进度封顶100·防"105%✓"观感打脸(当前值标签仍真实)
            if pct >= 100:
                fill_cls, cur_lbl = "f-green", "{}% ✓".format(disp)
            elif pct >= 70:
                fill_cls, cur_lbl = "f-amber", "{}%".format(disp)
            else:
                fill_cls, cur_lbl = "f-red", "{}%".format(disp)
            width = min(pct, 100)
            st_lbl = "当前 " + _fmt_okr_val(cur, unit)
        marks = "".join("<span></span>" for _ in range(10))
        d = o.get("dir", "x")
        rows += (
            '<div class="okr-item">'
            '<div class="okr-idx"><b>{}</b> · {} <span class="e">{}</span></div>'
            '<div><div class="okr-track">'
            '<div class="okr-fill {}" id="o-fill-{}" style="width:{}%"></div>'
            '<div class="okr-marks">{}</div></div>'
            '<div class="okr-note">{}</div>'
            '<div class="okr-formula" title="计算公式 · 口径SSOT: okr_quarter.json">ƒ {}</div>'
            '<div class="okr-measure" title="构念保真度 · 绿灯≠愿景达成(2026-08-23你质证落地)">🧪 {} {}</div></div>'
            '<div class="okr-pct" id="o-pct-{}">{}<span class="st" id="o-st-{}">{}</span></div>'
            '</div>'
        ).format(o.get("name", "—"), tgt_txt, o.get("evidence", ""),
                 fill_cls, d, width, marks, o.get("note", ""), o.get("formula", ""),
                 o.get("fidelity", ""), o.get("measures", ""),
                 d, cur_lbl, d, st_lbl)
    head = (
        '<div class="okr-head">'
        '<h3>🎯 季度 OKR · {} <span style="font-size:11px;color:var(--faint);font-weight:400">本季 {} → {}</span></h3>'
        '<span class="tag" id="okr-remaining">剩余 {} 天 · 目标/当前由 okr_quarter.json + 脚本机械映射 · 自然季度框定</span>'
        '</div>'
    ).format(okr.get("quarter", "—"), okr.get("start", "—"), okr.get("end", "—"),
             okr.get("remaining") if okr.get("remaining") is not None else "—")
    alarm = snap.get("registry_alarm")
    alarm_html = (
        '<div style="background:rgba(220,38,38,.14);border:1px solid var(--red);color:#fca5a5;'
        'padding:6px 10px;border-radius:6px;font-size:11px;margin-bottom:8px">🚨 {}</div>'.format(alarm)
    ) if alarm else ""
    return '<div class="card wide okr">{}{}</div>'.format(alarm_html, head + rows)

# ─────────────────────────────────────────────────────────────
# 渲染 v0.6：峰终布局（峰值=闭环流 / 中间=四方向+维护成本+接入率 / 终点=一句话总结）
# ─────────────────────────────────────────────────────────────

CSS = """
:root{--bg:#0f1115;--card:#181b22;--border:#242832;--text:#e6e8ec;--muted:#7a8090;--faint:#4a4f5c;--green:#22c55e;--amber:#f59e0b;--red:#ef4444;--blue:#3b82f6;--purple:#a78bfa;--mono:"SF Mono",ui-monospace,Menlo,"JetBrains Mono",monospace;--sans:-apple-system,"PingFang SC","Segoe UI",system-ui,sans-serif;}
*{margin:0;padding:0;box-sizing:border-box}
html{color-scheme:dark;-webkit-font-smoothing:antialiased}
body{background:var(--bg);color:var(--text);font-family:var(--sans);padding:24px;min-height:100vh}
.dash{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;max-width:1400px;margin:0 auto}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px 20px}
.card.wide{grid-column:span 4}
.card h3{font-size:13px;font-weight:600;color:var(--text);margin-bottom:2px}
.card .sub{font-size:11px;color:var(--muted);margin-bottom:12px}
/* ── 峰值：闭环流 ── */
.hero{grid-column:span 4;background:linear-gradient(180deg,#1a1e27 0%,var(--card) 100%);border:1px solid #2e3442;border-radius:10px;padding:20px 24px;position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--amber),var(--green),var(--blue),transparent)}
.hero h3{font-size:15px;font-weight:700}
.hero .sub{font-size:11px;color:var(--muted);margin:2px 0 16px}
.flow{display:flex;align-items:stretch;gap:10px;flex-wrap:wrap}
.stage{flex:1;min-width:130px;background:rgba(255,255,255,.02);border:1px solid var(--border);border-radius:8px;padding:14px 16px;text-align:center}
.stage .num{font-size:42px;font-weight:800;line-height:1.05}
.stage .lbl{font-size:12px;font-weight:600;margin-top:6px}
.stage .src{font-size:10px;color:var(--faint);margin-top:3px;font-family:var(--mono)}
.num.c-amber{color:var(--amber)}.num.c-green{color:var(--green)}.num.c-blue{color:var(--blue)}.num.c-purple{color:var(--purple)}
.arrow{align-self:center;font-size:22px;color:var(--faint);font-weight:700}
.pill{margin-left:auto;align-self:center;font-size:12px;font-weight:700;padding:6px 14px;border-radius:99px;white-space:nowrap}
.pill.ok{background:rgba(34,197,94,.12);color:var(--green);border:1px solid rgba(34,197,94,.35)}
.pill.warn{background:rgba(239,68,68,.12);color:var(--red);border:1px solid rgba(239,68,68,.35)}
.pill.neutral{background:rgba(122,128,144,.12);color:var(--muted);border:1px solid rgba(122,128,144,.35)}
.chart-box{position:relative;height:200px;margin-top:16px}
.chart-legend{position:absolute;top:-4px;right:0;display:flex;gap:14px;font-size:10.5px;color:var(--muted);align-items:center}
.chart-legend i{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:5px;vertical-align:middle}
svg#clTrend{width:100%;height:100%;display:block}
.vmethod{color:var(--muted);font-weight:600;font-size:10.5px;letter-spacing:.02em}
.chart-note{font-size:10px;color:var(--faint);font-family:var(--mono);margin-top:8px;text-align:right}
/* ── 四方向（紧凑·少而真） ── */
.fourdir{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.fd{background:rgba(255,255,255,.015);border:1px solid var(--border);border-radius:8px;padding:12px 14px}
.fd .name{font-size:11px;color:var(--muted);font-weight:600;display:flex;justify-content:space-between;align-items:center}
.fd .badge{font-size:11px}
.fd .val{font-size:17px;font-weight:700;margin-top:6px;line-height:1.35}
.fd .note{font-size:10px;color:var(--faint);margin-top:4px}
/* ── 维护成本 / 接入率 ── */
.maint .bar{font-size:12px;line-height:1.9}
.maint .bar b{color:var(--text);font-weight:600}
.maint .bar .seg-item{color:var(--muted)}
/* ── 季度 OKR 目标对照层 ── */
.okr{grid-column:span 4}
.okr-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.okr-head .tag{font-size:11px;font-family:var(--mono);color:var(--blue)}
.okr-item{display:grid;grid-template-columns:200px 1fr 60px;gap:14px;align-items:center;margin-top:10px}
.okr-idx{font-size:11px;color:var(--muted);font-weight:600}
.okr-idx .e{font-size:10px;margin-left:4px}
.okr-track{position:relative;height:18px;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:99px;overflow:hidden}
.okr-fill{position:absolute;top:0;left:0;height:100%;border-radius:99px;transition:width .6s ease}
.okr-marks{position:absolute;inset:0;display:flex;pointer-events:none}
.okr-marks span{flex:1;border-right:1px dashed rgba(255,255,255,.07)}
.okr-fill.f-green{background:linear-gradient(90deg,#16a34a,#22c55e)}
.okr-fill.f-amber{background:linear-gradient(90deg,#d97706,#f59e0b)}
.okr-fill.f-red{background:linear-gradient(90deg,#dc2626,#ef4444)}
.okr-fill.f-gray{background:#374151}
.okr-pct{font-size:15px;font-weight:800;text-align:right;font-variant-numeric:tabular-nums}
.okr-pct .st{font-size:9px;color:var(--faint);font-weight:600;display:block}
.okr-note{font-size:10px;color:var(--faint);margin-top:3px}
.okr-formula{font-family:var(--mono);font-size:9.5px;color:var(--faint);margin-top:4px;padding-top:4px;border-top:1px dashed rgba(255,255,255,.06)}
.okr-measure{font-size:9.5px;color:var(--muted);margin-top:3px}
details.rates{grid-column:span 4}
details.rates summary{cursor:pointer;font-size:13px;font-weight:600;list-style:none;display:flex;justify-content:space-between;align-items:center}
details.rates summary::-webkit-details-marker{display:none}
details.rates summary .hint{font-size:11px;color:var(--faint);font-family:var(--mono)}
details.rates[open] summary{margin-bottom:12px}
table{border-collapse:collapse;width:100%;font-size:12px;font-family:var(--sans)}
th{text-align:left;color:var(--faint);font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
td{padding:6px 8px;border-bottom:1px solid var(--border)}
td:first-child{color:var(--muted);font-weight:600}
td:nth-child(2){font-weight:700}
/* ── 终点：一句话总结 ── */
.summary{grid-column:span 4;background:linear-gradient(135deg,#1c2029 0%,#181b22 70%);border:1px solid #2e3442;border-radius:10px;padding:22px 26px;display:flex;gap:16px;align-items:flex-start}
.summary .bolt{font-size:28px;line-height:1}
.summary .text{font-size:19px;font-weight:700;line-height:1.5}
.summary .text .em{color:var(--green)}
.summary .meta{font-size:10px;color:var(--faint);font-family:var(--mono);margin-top:8px}
.footer{max-width:1400px;margin:16px auto 0;padding:0 4px;display:flex;justify-content:space-between;font-size:10px;color:var(--faint);font-family:var(--mono)}

/* ── 知识库可视化3模块（2026-09-08 童灵根治·合并入panel_snapshot.py） ── */
.kb-federation{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.kb-federation .kb-cell{background:rgba(255,255,255,.015);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-align:center}
.kb-federation .kb-cell .label{font-size:10px;color:var(--muted);font-weight:600;margin-bottom:4px}
.kb-federation .kb-cell .val{font-size:22px;font-weight:800;line-height:1.2}
.kb-federation .kb-cell .val.c-amber{color:var(--amber)}.kb-federation .kb-cell .val.c-green{color:var(--green)}.kb-federation .kb-cell .val.c-blue{color:var(--blue)}.kb-federation .kb-cell .val.c-purple{color:var(--purple)}
.kb-federation .kb-cell .src{font-size:9px;color:var(--faint);margin-top:3px;font-family:var(--mono)}
.kb-cards{margin-top:12px}
.kb-card-row{display:grid;grid-template-columns:90px 1fr 60px;gap:10px;align-items:center;margin-bottom:8px}
.kb-card-row .name{font-size:11px;color:var(--muted);font-weight:600}
.kb-card-row .bar-track{position:relative;height:16px;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:99px;overflow:hidden}
.kb-card-row .bar-fill{position:absolute;top:0;left:0;height:100%;border-radius:99px;transition:width .6s ease}
.kb-card-row .bar-fill.f-green{background:linear-gradient(90deg,#16a34a,#22c55e)}
.kb-card-row .bar-fill.f-amber{background:linear-gradient(90deg,#d97706,#f59e0b)}
.kb-card-row .bar-fill.f-blue{background:linear-gradient(90deg,#2563eb,#3b82f6)}
.kb-card-row .bar-fill.f-purple{background:linear-gradient(90deg,#7c3aed,#a78bfa)}
.kb-card-row .bar-fill.f-red{background:linear-gradient(90deg,#dc2626,#ef4444)}
.kb-card-row .count{font-size:13px;font-weight:700;text-align:right;font-variant-numeric:tabular-nums}
.kb-progress{margin-top:12px}
.kb-progress-track{position:relative;height:24px;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:99px;overflow:hidden}
.kb-progress-fill{position:absolute;top:0;left:0;height:100%;background:linear-gradient(90deg,#2563eb,#3b82f6,#a78bfa);border-radius:99px;transition:width .8s ease}
.kb-progress-text{position:absolute;top:0;left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:var(--text);text-shadow:0 1px 2px rgba(0,0,0,.5)}
.kb-progress-meta{display:flex;justify-content:space-between;margin-top:6px;font-size:10px;color:var(--faint);font-family:var(--mono)}
.kb-method{margin-top:10px;padding:8px 12px;background:rgba(59,130,246,.06);border:1px solid rgba(59,130,246,.2);border-radius:6px;font-size:10px;color:var(--muted);line-height:1.6}
.kb-method b{color:var(--blue)}
"""

HEAD_JS = """
// v0.8.0 零外链：内联 SVG 趋势图（原生 <title> 悬停读数·断网可渲染·无 Chart.js/字体 CDN）
(function(){
  var MUTED="#7a8090",GRID="#242832";
  var SERIES=[["detected","#f59e0b","检出"],["fixed","#22c55e","留痕"],["immune","#3b82f6","免疫"]];
  window.renderTrend=function(trend){
    var svg=document.getElementById("clTrend");
    if(!svg||!trend||!trend.length)return;
    var W=720,H=200,L=38,R=16,T=16,B=24,n=trend.length;
    var vals=[];trend.forEach(function(r){SERIES.forEach(function(s){if(typeof r[s[0]]==="number")vals.push(r[s[0]]);});});
    if(!vals.length)return;
    var rawMax=Math.max.apply(null,vals);
    var step=rawMax<=8?2:rawMax<=30?5:rawMax<=60?10:20;
    var ymax=Math.max(step,Math.ceil(rawMax/step)*step);
    function xp(i){return L+(W-L-R)*(n===1?0:i/(n-1));}
    function yp(v){return T+(H-T-B)*(1-v/ymax);}
    var out="";
    for(var g=0;g<=ymax;g+=step){
      var y=yp(g);
      out+='<line x1="'+L+'" y1="'+y.toFixed(1)+'" x2="'+(W-R)+'" y2="'+y.toFixed(1)+'" stroke="'+GRID+'" stroke-opacity=".55" stroke-width="1"/>';
      out+='<text x="'+(L-7)+'" y="'+(y+3).toFixed(1)+'" text-anchor="end" font-size="9.5" fill="'+MUTED+'">'+g+'</text>';
    }
    trend.forEach(function(r,i){
      out+='<text x="'+xp(i).toFixed(1)+'" y="'+(H-8)+'" text-anchor="middle" font-size="9.5" fill="'+MUTED+'">'+r.date+'</text>';
    });
    SERIES.forEach(function(s){
      var key=s[0],col=s[1],name=s[2],pts=[];
      trend.forEach(function(r,i){pts.push([xp(i),yp(r[key]||0)]);});
      var d="";
      pts.forEach(function(p,i){d+=(i?" L":"M")+p[0].toFixed(1)+" "+p[1].toFixed(1);});
      out+='<path d="'+d+' L'+pts[n-1][0].toFixed(1)+' '+yp(0).toFixed(1)+' L'+pts[0][0].toFixed(1)+' '+yp(0).toFixed(1)+' Z" fill="'+col+'" opacity="0.08"/>';
      out+='<path d="'+d+'" fill="none" stroke="'+col+'" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>';
      pts.forEach(function(p,i){
        out+='<circle cx="'+p[0].toFixed(1)+'" cy="'+p[1].toFixed(1)+'" r="2.6" fill="'+col+'"><title>'+trend[i].date+' · '+name+' '+(trend[i][key]||0)+'</title></circle>';
      });
      var lp=pts[n-1],lv=(trend[n-1][key]||0);
      out+='<text x="'+(lp[0]-7).toFixed(1)+'" y="'+(lp[1]-7).toFixed(1)+'" text-anchor="end" font-size="10" font-weight="700" fill="'+col+'">'+lv+'</text>';
    });
    svg.setAttribute("viewBox","0 0 "+W+" "+H);
    svg.setAttribute("preserveAspectRatio","xMidYMid meet");
    svg.innerHTML=out;
    var lg=document.getElementById("clLegend");
    if(lg)lg.innerHTML=SERIES.map(function(s){return '<span><i style="background:'+s[1]+'"></i>'+s[2]+'</span>';}).join("");
  };
})();
"""

LIVE_JS = """
(function(){
  var d = window.PANEL_DATA;
  if (!d) {
    var b = document.createElement('div');
    b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99;background:#ef4444;color:#fff;font:600 12px/1.6 system-ui;padding:8px 14px';
    b.textContent = '⚠️ panel_data.js 加载失败——下方数字为上次生成的快照，非实时（宁可少，不要假）';
    document.body.appendChild(b);
    return;
  }
  function set(id, v){ var el = document.getElementById(id); if(el && v !== undefined && v !== null) el.textContent = v; }
  var cl = d.closed_loop || {};
  set("cl-detected", cl.detected); set("cl-fixed", cl.fixed);
  set("cl-immune", cl.immune); set("cl-antibodies", cl.antibodies);
  var pill = document.getElementById("cl-pending");
  if (pill) {
    if (cl.pending > 0) { pill.className = "pill neutral"; pill.title = "粗口径=检出−留痕·非逐项核销·不代表积压"; pill.textContent = "差值 " + cl.pending + " · 粗口径·非核销"; }
    else if (cl.detected !== null && cl.detected !== undefined) { pill.className = "pill ok"; pill.title = "粗口径=检出−留痕·两源独立计数·非核销"; pill.textContent = "检出 ≤ 留痕 · 粗口径"; }
  }
  var st = document.getElementById("summary-text");
  if (st && d.summary) { st.innerHTML = d.summary; }
  // 知识内化流动态注入（2026-08-26 根治硬编码快照·数据来自knowledge_ladder）
  var kl = d.knowledge_ladder;
  if (kl && kl.stats) {
    set("kf-l1", kl.stats.L1); set("kf-l2", kl.stats.L2);
    set("kf-l3", kl.stats.L3); set("kf-l4", kl.stats.L4);
    var kc = document.getElementById("kf-cand");
    if (kc && kl.skill_candidates !== undefined) {
      kc.textContent = "🔧 技能卡候选 " + kl.skill_candidates;
      kc.style.color = kl.skill_candidates > 0 ? "var(--amber)" : "var(--faint)";
    }
    var kp = document.getElementById("kf-pill");
    if (kp && kl.l4_probe) {
      kp.textContent = "管道已通 · L4 待首例 · 试金石 " + kl.l4_probe.card + " 引用" + kl.l4_probe.total + "含你决策" + kl.l4_probe.ge;
    }
  }
  var fd = d.four_dir || {};
  if (fd.auto) set("fd-auto", fd.auto);
  if (fd.better) set("fd-better", fd.better);
  if (fd.evo) set("fd-evo", fd.evo);
  if (fd.knows) set("fd-knows", fd.knows);
  if (fd.knows_note) set("fd-knows-note", fd.knows_note);
  // 四方向卡 badge 与 OKR 区强一致：从 four_dir 的 state/evidence 更新徽标（过渡不冒充定案·定案显示机械 evidence）
  var stateMap = {auto: fd.auto_state, better: fd.better_state, evo: fd.evo_state, knows: fd.knows_state};
  var okrObjs = (d.okr && d.okr.objectives) || [];
  ['auto','better','evo','knows'].forEach(function(k){
    var oi = okrObjs.filter(function(o){return o.dir===k;})[0];
    // 通过卡片容器定位该方向徽标
    var fdCard = document.querySelector('#fd-'+k);
    var cardEl = fdCard ? fdCard.closest('.fd') : null;
    if (cardEl) {
      var bd = cardEl.querySelector('.badge');
      var evRaw = (oi && oi.evidence) || '—';
      var stRaw = stateMap[k] || '';
      if (bd) bd.textContent = evRaw;
      var nm = cardEl.querySelector('.name');
      if (nm && stRaw) {
        var existing = nm.querySelector('.st-badge'); if (existing) existing.remove();
        var sb = document.createElement('span'); sb.className = 'st-badge'; sb.textContent = '· ' + stRaw; sb.style.cssText = 'font-weight:400;font-size:10px;opacity:.6;margin-left:4px;'; nm.appendChild(sb);
      }
    }
  });
  if (d.maintenance_line) set("maint-line", d.maintenance_line);
  if (cl.trend && cl.trend.length && window.renderTrend) { window.renderTrend(cl.trend); }
  // 接入率表
  if (!d.platform_rates) return;
  var html = '';
  d.platform_rates.forEach(function(r){
    var gapHtml = (r.gap !== undefined && r.gap !== null)
      ? '<span style="color:' + (r.gap>0?'#ef4444':'#22c55e') + '">缺 ' + r.gap + '</span>'
      : '—';
    var numHtml = (r.num !== undefined && r.num !== null)
      ? '<span style="color:' + r.color + ';font-weight:700">' + r.num + '/' + r.den + '</span>'
      : '—';
    var extraHtml = (r.extra > 0)
      ? ' <span title="平台附加守卫(非共享清单)" style="color:#3b82f6;font-weight:600">+' + r.extra + '</span>'
      : '';
    html += '<tr><td>' + r.name + '</td>' +
            '<td><span class="vmethod" title="' + r.note + '">' + (r.method || r.mark || '—') + '</span></td>' +
            '<td>' + numHtml + extraHtml + '</td><td>' + gapHtml + '</td></tr>';
  });
  var table = document.getElementById("rates-table");
  if (table) {
    table.innerHTML = '<tr><th>平台</th><th>核验</th><th>已接</th><th>缺口</th></tr>' + html;
    var upd = document.createElement("div");
    upd.style.cssText = 'font-size:11px;color:#4a4f5c;font-family:var(--mono);margin-top:8px;text-align:right';
    upd.textContent = '数据更新: ' + (d.updated || '—');
    table.parentElement.appendChild(upd);
  }
  // 季度 OKR 目标对照层（目标线 vs 实际进度·动态注入，改 okr_quarter.json→重跑脚本→刷新即变）
  var okr = d.okr;
  if (okr) {
    var rem = document.getElementById("okr-remaining");
    if (rem && okr.remaining !== undefined && okr.remaining !== null) rem.textContent = "剩余 " + okr.remaining + " 天 · 目标/当前由 okr_quarter.json + 脚本机械映射 · 自然季度框定";
    (okr.objectives || []).forEach(function(o){
      var pctEl = document.getElementById("o-pct-" + o.dir);
      var fillEl = document.getElementById("o-fill-" + o.dir);
      var stEl = document.getElementById("o-st-" + o.dir);
      if (!pctEl || !fillEl) return;
      if (o.current === null || o.current === undefined) {
        pctEl.textContent = "N/A";
        if (stEl) stEl.textContent = "待量化";
        fillEl.className = "okr-fill f-gray"; fillEl.style.width = "0%";
        return;
      }
      var tgt = o.target_pct || 1, p = o.current / tgt * 100, disp = Math.min(Math.round(p), 100); // A v2 封顶100
      var cls = p >= 100 ? "f-green" : p >= 70 ? "f-amber" : "f-red";
      pctEl.textContent = cls === "f-green" ? disp + "% ✓" : disp + "%";
      if (stEl) stEl.textContent = "当前 " + o.current + (o.unit === "rate" ? "%" : "");
      fillEl.className = "okr-fill " + cls;
      fillEl.style.width = Math.min(p, 100) + "%";
    });
  }

  // 知识库可视化3模块数据加载（2026-09-08 童灵根治·合并入panel_snapshot.py）
  var kb = d.knowledge_base;
  if (kb) {
    if (kb.ai_lib) set("kb-ai-lib", kb.ai_lib.total);
    if (kb.obsidian_kb) set("kb-obsidian", kb.obsidian_kb.total_md);
    if (kb.blueprint) set("kb-blueprint", kb.blueprint.total_md);
    if (kb.federation) set("kb-total", kb.federation.total);
    var fc = kb.federated_cards || {};
    set("kb-stance", fc.stance); set("kb-concept", fc.concept);
    set("kb-knowledge", fc.knowledge); set("kb-skill", fc.skill);
    var maxCard = Math.max(fc.knowledge||0, fc.stance||0, fc.concept||0, fc.index||0, fc.skill||0, 1);
    var cardBars = [
      {id:"kb-bar-knowledge", count:"kb-count-knowledge", val:fc.knowledge},
      {id:"kb-bar-stance", count:"kb-count-stance", val:fc.stance},
      {id:"kb-bar-concept", count:"kb-count-concept", val:fc.concept},
      {id:"kb-bar-index", count:"kb-count-index", val:kb.index_cards?kb.index_cards.generated:0},
      {id:"kb-bar-skill", count:"kb-count-skill", val:fc.skill}
    ];
    cardBars.forEach(function(c){
      var bar = document.getElementById(c.id);
      var cnt = document.getElementById(c.count);
      if (bar && c.val !== undefined) { bar.style.width = Math.max(c.val/maxCard*100, 0.5) + "%"; }
      if (cnt && c.val !== undefined) { cnt.textContent = c.val; }
    });
    var ic = kb.index_cards;
    if (ic) {
      var fill = document.getElementById("kb-progress-fill");
      var text = document.getElementById("kb-progress-text");
      if (fill) fill.style.width = ic.progress_pct + "%";
      if (text) text.textContent = ic.generated + " / " + ic.total_needed + " · " + ic.progress_pct + "%";
    }
  }
})();
"""

def _stage(num, color, lbl, src, num_id):
    return ('<div class="stage"><div class="num {c}" id="{i}">{n}</div>'
            '<div class="lbl">{l}</div><div class="src">{s}</div></div>').format(
        c=color, i=num_id, n=("—" if num is None else num), l=lbl, s=src)

def render_html(snap):
    cl = snap.get("closed_loop", {}) or {}
    det, fix, imm = cl.get("detected"), cl.get("fixed"), cl.get("immune")
    anti, pending = cl.get("antibodies"), cl.get("pending") or 0
    trend = cl.get("trend") or []
    today_md = (snap.get("date") or "")[5:]   # "MM-DD"
    trend_plot = [r for r in trend if r.get("date") != today_md]  # v0.8.0 今日进行中不入图·防零值断崖

    # 峰值：闭环流
    flow_html = (
        _stage(det, "c-amber", "检测 · DRIFT 检出", "platform_adaptation_check.log", "cl-detected") +
        '<div class="arrow">→</div>' +
        _stage(fix, "c-green", "修正 · 变更留痕", "变更日志 WorkBuddy 行", "cl-fixed") +
        '<div class="arrow">→</div>' +
        _stage(imm, "c-blue", "免疫 · 复发监测", "免疫复发记录「命中」（本周·0=无复发=抗体生效）", "cl-immune") +
        '<div class="arrow">→</div>' +
        _stage(anti, "c-purple", "抗体库 · 累计", "规范反哺日志「🛡」", "cl-antibodies")
    )
    if det is not None and fix is not None and det > fix:
        pill = '<div class="pill neutral" id="cl-pending" title="粗口径=检出−留痕·非逐项核销·不代表积压">差值 {} · 粗口径·非核销</div>'.format(det - fix)
    elif det is not None:
        pill = '<div class="pill ok" id="cl-pending" title="粗口径=检出−留痕·两源独立计数·非核销">检出 ≤ 留痕 · 粗口径</div>'
    else:
        pill = '<div class="pill neutral" id="cl-pending">数据采集中</div>'

    hero = (
        '<div class="hero">'
        '<h3>🔄 闭环流 <span style="font-size:11px;color:var(--faint);font-weight:400">检测 → 修正 → 免疫 → 抗体库 ↺ 自主进化回路</span></h3>'
        '<div class="sub">本周流量 · 全自动检出与拦截 · 修正自动留痕（图优先：回路在动吗，一眼看出）</div>'
        '<div class="flow">{}{}</div>'
        '<div class="chart-box"><div class="chart-legend" id="clLegend"></div><svg id="clTrend" role="img" aria-label="近7日闭环流趋势"></svg></div>'
        '<div class="chart-note">近7日逐日流量 · 今日进行中不入图（防零值断崖） · 结构性基线从 2026-08-21 起自动积累（缺数日=0·不编造）</div>'
        '</div>'
    ).format(flow_html, pill)

    # 知识内化流（2026-08-26 新增·L1-L4 管道打通后入板·与闭环流同构）
    kl = snap.get("knowledge_ladder") or {}
    kl_stats = kl.get("stats") or {}
    kl_probe = kl.get("l4_probe")
    def _klv(k):
        v = kl_stats.get(k)
        return v if v is not None else "—"
    probe_txt = ""
    if kl_probe:
        probe_txt = " · 试金石 {} 引用{}含你决策{}".format(kl_probe["card"], kl_probe["total"], kl_probe["ge"])
    if _klv("L4") == 0 and _klv("L4") != "—":
        kl_pill = '<div class="pill ok" id="kf-pill" title="引用登记已自动化·L4 首例待你决策引用触发">管道已通 · L4 待首例{}</div>'.format(probe_txt)
    else:
        kl_pill = '<div class="pill ok" id="kf-pill">L4 已破冰</div>'
    ladder_html = (
        '<div class="hero">'
        '<h3>🧠 知识内化流 <span style="font-size:11px;color:var(--faint);font-weight:400">L1 提炼 → L2 质证 → L3 应用 → L4 内化 ↺ 引用自动登记</span> <span id="kf-cand" style="font-size:11px;color:var(--amber);font-weight:600;margin-left:8px">🔧 技能卡候选 {}</span></h3>'
        '<div class="sub">立场卡+技能卡内化阶梯 · 引用自动登记（2026-08-26 管道打通）· 数据源=INDEX.md/引用台账 机械解析（无人工填报）</div>'
        '<div class="flow">'
        '<div class="stage"><div class="num c-amber" id="kf-l1">{}</div><div class="lbl">L1 · 提炼</div><div class="src">AI学习库 · 待质证</div></div>'
        '<div class="arrow">→</div>'
        '<div class="stage"><div class="num c-green" id="kf-l2">{}</div><div class="lbl">L2 · 质证</div><div class="src">分身初审 / 你锤事件</div></div>'
        '<div class="arrow">→</div>'
        '<div class="stage"><div class="num c-blue" id="kf-l3">{}</div><div class="lbl">L3 · 应用</div><div class="src">引用台账 · 自动登记</div></div>'
        '<div class="arrow">→</div>'
        '<div class="stage"><div class="num c-purple" id="kf-l4">{}</div><div class="lbl">L4 · 内化</div><div class="src">引用≥3 含你决策</div></div>'
        '{}</div>'
        '<div class="chart-note">知识内化回路（2026-08-26 童灵打通）· 更新于 {} · 每批碰撞/你确认自动登记引用</div>'
        '</div>'
    ).format(kl.get("skill_candidates", 0), _klv("L1"), _klv("L2"), _klv("L3"), _klv("L4"), kl_pill, kl.get("updated", "—"))

    # 知识库可视化3模块（2026-09-08 童灵根治·合并入panel_snapshot.py）
    kb = snap.get("knowledge_base") or {}
    fc = kb.get("federated_cards", {}) or {}
    ic = kb.get("index_cards", {}) or {}
    ai_lib = kb.get("ai_lib", {}) or {}
    obs_kb = kb.get("obsidian_kb", {}) or {}
    bp = kb.get("blueprint", {}) or {}
    fed = kb.get("federation", {}) or {}
    def _kbv(d, k, default="—"):
        v = d.get(k)
        return v if v is not None else default
    max_card = max(_kbv(fc, "knowledge", 0), _kbv(fc, "stance", 0), _kbv(fc, "concept", 0), _kbv(ic, "generated", 0), _kbv(fc, "skill", 0), 1)
    def _bar_w(val):
        return max(val / max_card * 100, 0.5) if max_card > 0 else 0.5
    kb_html = (
        '<div class="card wide"><h3>📚 知识库联邦总览 <span style="font-size:10px;color:var(--faint);font-weight:400">AI学习库 + Obsidian知识库 + 记忆蓝图 · 联邦多路径统计 · 三维度联合识别</span></h3><div class="sub">数据源=kb_metadata_extract.py 机械采集（无人工填报）· 立场卡/概念卡/知识卡跨库联邦统计 · 每日 07:30 机械采集</div>'
        '<div class="kb-federation">'
        '<div class="kb-cell"><div class="label">AI学习库</div><div class="val c-amber" id="kb-ai-lib">{}</div><div class="src">立场卡+技能卡+其他</div></div>'
        '<div class="kb-cell"><div class="label">Obsidian知识库</div><div class="val c-green" id="kb-obsidian">{}</div><div class="src">10子目录 · 知识池/概念层/读书笔记</div></div>'
        '<div class="kb-cell"><div class="label">记忆蓝图</div><div class="val c-blue" id="kb-blueprint">{}</div><div class="src">6顶层目录 · 设计哲学/开发规范</div></div>'
        '<div class="kb-cell"><div class="label">联邦总规模</div><div class="val c-purple" id="kb-total">{}</div><div class="src">AI学习库+Obsidian+蓝图</div></div>'
        '<div class="kb-cell"><div class="label">立场卡</div><div class="val c-amber" id="kb-stance">{}</div><div class="src">AI学习库 · 决策判据</div></div>'
        '<div class="kb-cell"><div class="label">概念卡</div><div class="val c-green" id="kb-concept">{}</div><div class="src">Obsidian 08-概念层</div></div>'
        '<div class="kb-cell"><div class="label">知识卡</div><div class="val c-blue" id="kb-knowledge">{}</div><div class="src">Obsidian 05-知识池</div></div>'
        '<div class="kb-cell"><div class="label">技能卡</div><div class="val c-purple" id="kb-skill">{}</div><div class="src">AI学习库 · Skill用法卡</div></div>'
        '</div>'
        '<div class="kb-method"><b>三维度联合识别方法</b>：文件名前缀 + YAML type字段 + 目录位置，不强制改名，联邦多路径统计。立场卡=AI学习库立场卡#前缀，概念卡=Obsidian 08-概念层目录，知识卡=Obsidian 05-知识池目录，技能卡=AI学习库技能卡#前缀。</div>'
        '</div>'
        '<div class="card wide"><h3>📊 卡片分布与蓝图索引卡进度 <span style="font-size:10px;color:var(--faint);font-weight:400">五类卡片分布条形图 + 蓝图索引卡生成进度</span></h3><div class="sub">条形图按数量比例渲染 · 蓝图索引卡=记忆蓝图文件的索引卡（核心原则+摘要+路径指针），进知识库可被语义检索</div>'
        '<div class="kb-cards" id="kb-cards-container">'
        '<div class="kb-card-row"><div class="name">知识卡</div><div class="bar-track"><div class="bar-fill f-blue" id="kb-bar-knowledge" style="width:{}%"></div></div><div class="count" id="kb-count-knowledge">{}</div></div>'
        '<div class="kb-card-row"><div class="name">立场卡</div><div class="bar-track"><div class="bar-fill f-amber" id="kb-bar-stance" style="width:{}%"></div></div><div class="count" id="kb-count-stance">{}</div></div>'
        '<div class="kb-card-row"><div class="name">概念卡</div><div class="bar-track"><div class="bar-fill f-green" id="kb-bar-concept" style="width:{}%"></div></div><div class="count" id="kb-count-concept">{}</div></div>'
        '<div class="kb-card-row"><div class="name">蓝图索引卡</div><div class="bar-track"><div class="bar-fill f-purple" id="kb-bar-index" style="width:{}%"></div></div><div class="count" id="kb-count-index">{}</div></div>'
        '<div class="kb-card-row"><div class="name">技能卡</div><div class="bar-track"><div class="bar-fill f-red" id="kb-bar-skill" style="width:{}%"></div></div><div class="count" id="kb-count-skill">{}</div></div>'
        '</div>'
        '<div class="kb-progress">'
        '<div class="kb-progress-track"><div class="kb-progress-fill" id="kb-progress-fill" style="width:{}%"></div><div class="kb-progress-text" id="kb-progress-text">{} / {} · {}%</div></div>'
        '<div class="kb-progress-meta"><span>已生成 {} 张</span><span>待生成 {} 张</span>{}</div>'
        '</div></div>'
        '<div class="card wide"><h3>🔍 知识库运作机制 <span style="font-size:10px;color:var(--faint);font-weight:400">卡片碰撞机制 + 检索路径 + 增量更新闭环</span></h3><div class="sub">童灵全系统导航协议：检索→路径指针→蓝图原文→综合回答 · 卡片碰撞=概念卡+知识卡+立场卡三向碰撞产生新洞察</div>'
        '<div class="kb-federation">'
        '<div class="kb-cell"><div class="label">检索引擎</div><div class="val c-amber" style="font-size:16px">search_kb.py</div><div class="src">5源联邦检索 · 三路融合</div></div>'
        '<div class="kb-cell"><div class="label">蓝图索引卡</div><div class="val c-green" style="font-size:16px">路径指针</div><div class="src">检索到→Read完整蓝图</div></div>'
        '<div class="kb-cell"><div class="label">卡片碰撞</div><div class="val c-blue" style="font-size:16px">三向碰撞</div><div class="src">概念+知识+立场→新洞察</div></div>'
        '<div class="kb-cell"><div class="label">增量更新</div><div class="val c-purple" style="font-size:16px">launchd</div><div class="src">每日 07:30 自动校验</div></div>'
        '</div>'
        '<div class="kb-method"><b>童灵全系统导航协议（K2 W1第12条）</b>：蓝图结构（6顶层目录）+ 映射表（蓝图文件→索引卡路径）+ 渐进式加载4步（L0恒驻核→L1条目索引→L2域切片→L3单条目）+ 7大域导航路径。通过童灵就知道整个系统的"为何做、如何做、做的目的和效果"。</div>'
        '</div>'
    ).format(
        _kbv(ai_lib, "total"), _kbv(obs_kb, "total_md"), _kbv(bp, "total_md"), _kbv(fed, "total"),
        _kbv(fc, "stance"), _kbv(fc, "concept"), _kbv(fc, "knowledge"), _kbv(fc, "skill"),
        _bar_w(_kbv(fc, "knowledge", 0)), _kbv(fc, "knowledge"),
        _bar_w(_kbv(fc, "stance", 0)), _kbv(fc, "stance"),
        _bar_w(_kbv(fc, "concept", 0)), _kbv(fc, "concept"),
        _bar_w(_kbv(ic, "generated", 0)), _kbv(ic, "generated"),
        _bar_w(_kbv(fc, "skill", 0)), _kbv(fc, "skill"),
        _kbv(ic, "progress_pct", 0), _kbv(ic, "generated"), _kbv(ic, "total_needed"), _kbv(ic, "progress_pct"),
        _kbv(ic, "generated"), _kbv(ic, "pending", 0),
        # 2026-09-27 童灵根治：守卫状态改读数据字段（watch_active），⛔不再硬编码✅——假绿=反模式
        ('<span>防漂移校验 ✅</span><span>launchd增量监控 ✅</span>'
         if _kbv(ic, "watch_active", False)
         else '<span style="color:var(--amber)">⚠️ 防漂移守卫未挂载（com.buluotuo.kb-index-guard.plist 缺位）</span>')
    )


    # 四方向原生数据（紧凑行·少而真·零分数）
    # v0.8.0 三面孔同源：①/④ 卡直接复用 OKR 机械映射行读数（auto_closure/auto_done/auto_cov/evidence）
    _okr_map = {}
    for _o in ((snap.get("okr") or {}).get("objectives") or []):
        _okr_map[_o.get("dir")] = _o
    def _pf(v):  # percent-or-dash
        return ("{}%".format(v) if isinstance(v, (int, float)) else "—")
    _oa = _okr_map.get("auto") or {}
    auto_txt = "自动触发占比 {} · 覆盖 {}".format(
        _pf(_oa.get("auto_closure")), _oa.get("auto_cov") or "—")
    auto_badge = _oa.get("evidence") or "🔴"
    imm_h = snap.get("better_immune_hits")
    anti_e = snap.get("better_antibodies")
    better_base = snap.get("better_baseline")
    if snap.get("better_state") == "定案" and snap.get("better_join_active") is not None:
        better_txt = "漏触发修复率(近14天活跃) {:.0%} · 全史对照 {:.0%} · 双载体池 {} 条".format(
            snap["better_join_active"], (snap.get("better_join_all") or 0),
            snap.get("better_pool") or "—")
    else:
        better_txt = "免疫命中 {}（累计） · 有效抗体 {}".format(imm_h if imm_h is not None else "—", anti_e if anti_e is not None else "—")
    better_ev = snap.get("better_evidence") or "🟢"
    evo_v = snap.get("evo_events")
    evo_txt = "本季进化事件 {} · 净采纳率 {}".format(
        evo_v if evo_v is not None else "—",
        ("{:.0f}%".format(snap.get("evo_adoption_rate") * 100) if snap.get("evo_adoption_rate") is not None else "待量"))
    evo_badge = snap.get("evo_evidence") or "🔴"
    knows_v = snap.get("knows_count")
    knows_dl = snap.get("knows_days_left")
    _ok = _okr_map.get("knows") or {}
    knows_txt = "本月 {} 条 · 本季累计 {}/{} · 剩 {} 天".format(
        knows_v if knows_v is not None else "—",
        _ok.get("current") if _ok.get("current") is not None else "—",
        _ok.get("target_pct") if _ok.get("target_pct") is not None else "—",
        knows_dl if knows_dl is not None else "—")
    knows_badge = _ok.get("evidence") or snap.get("knows_evidence") or "🟡"
    fourdir = (
        '<div class="card wide fourdir">'
        '<div class="fd"><div class="name">① 全自动化 <span class="badge" title="愿景①真义=机制自动运转不依赖人记得·值为hook_auto触发占比(自动触发调用/总调用)·手动调用累积会拉低占比(非自动化退化)">{}</span></div>'
        '<div class="val" id="fd-auto">{}</div><div class="note">值为 hook_auto 触发占比(愿景①=机制自动运转不依赖人记得) · 手动调用累积拉低占比≠自动化退化 · returncode 成功=100%(可靠性) · 覆盖N/M独立读数 · 🧪🟡过程代理</div></div>'
        '<div class="fd"><div class="name">② 越用越好用 <span class="badge" title="定案(v0.5)=漏触发修复率·两池join≥90%门槛实过">{}</span></div>'
        '<div class="val" id="fd-better">{}</div><div class="note">免疫命中=历史复发被捕获次数(证明闭环在跑·非未实现) · 有效抗体=已建防复发规则 · 基线 {} · 🧪{}</div></div>'
        '<div class="fd"><div class="name">③ 自主进化 <span class="badge" title="净采纳率=本季新增采纳/总提案">{}</span></div>'
        '<div class="val" id="fd-evo">{}</div><div class="note">挑战线=净采纳率≥60% · 愿景③真义=机制被真内化 · 🧪🟢行为锚</div></div>'
        '<div class="fd"><div class="name">④ 越懂你 <span class="badge" title="过渡方向·代理计数证据封顶🟡">{}</span></div>'
        '<div class="val" id="fd-knows">{}</div><div class="note" id="fd-knows-note">过渡=认知发现数·自然月归当月 · 定案=预测准确率（需先建「预测vs实际」成对标签） · 🧪🔴产量代理</div></div>'
        '</div>'
    ).format(auto_badge, auto_txt, better_ev, better_txt,
             ("{:.0%}".format(better_base) if better_base is not None else "—"),
             ("🟢定案(活跃口径)" if snap.get("better_state") == "定案" else "🟡过程代理"),
             evo_badge, evo_txt, knows_badge, knows_txt)

    # 维护成本（git 派生·免自评）
    mt = snap.get("maintenance", {}) or {}
    if mt.get("total_commits") is not None:
        segs = " · ".join("{} {}".format(s["segment"], s["commits"]) for s in mt.get("segments", []) if s.get("commits") is not None)
        maint_line = "近7天共 {} 次提交 · 环节Top：{}（环节口径≠总量口径·示集中度）".format(mt["total_commits"], segs)
    else:
        maint_line = "数据采集中（环节维护台账.py 待产出）"
    maint = (
        '<div class="card wide maint">'
        '<h3>🧰 维护成本 <span style="font-size:10px;color:var(--faint);font-weight:400">git log 按环节统计提交数/周 · 免人工 · 免自评</span></h3>'
        '<div class="bar" id="maint-line" style="margin-top:8px">{}</div>'
        '</div>'
    ).format(maint_line)

    # v0.8.0 价值层占位卡：北极星产出轴入口（S451 投资回收轴）——诚实待量化，不装假指标
    value_card = (
        '<div class="card wide maint">'
        '<h3>🎯 价值层（北极星产出轴） <span style="font-size:10px;color:var(--faint);font-weight:400">S451 投资回收轴 · 建/停决策依据</span></h3>'
        '<div class="bar" style="margin-top:8px;color:var(--muted)">待量化（定义中：本周「系统帮你产出」事件数——视频发布 / 文案产出 / 账号数据） · 无数据源不上假指标（你最高原则）</div>'
        '</div>'
    )

    okr_html = build_okr_html(snap)   # 季度 OKR 目标对照层（本季目标线 vs 实际进度）

    # 平台接入率（按需展开·保留 N/M + 校验覆盖标记）
    # 校验覆盖标记自动解析自 SSOT §二·七 校验覆盖段（不硬编码·防漂移）
    ssot_cov = _parse_coverage_from_ssot()
    rates = snap.get("platform_rates", {})
    def rate_key(item):
        v = item[1]
        return (v[0] / v[1]) if v and v[1] else -1
    rate_rows = ""
    verified = 0
    known = 0
    METHOD_TXT = {"🟢": "机械", "🟡": "自核", "🔴": "自治"}
    for name, v in sorted(rates.items(), key=rate_key, reverse=True):
        if v is None:
            rate_rows += '<tr><td>{}</td><td><span class="vmethod">未登记</span></td><td>—</td><td>—</td></tr>\n'.format(name)
            continue
        num, den = v
        known += 1
        mark, note = ssot_cov.get(name, ("❔", "未登记"))
        if mark == "🟢":
            verified += 1
        pct = round(num / den * 100) if den else 0
        color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 50 else "#ef4444"
        gap = den - num
        rate_rows += ('<tr><td>{}</td>'
                      '<td><span class="vmethod" title="{}">{}</span></td>'
                      '<td style="color:{};font-weight:700">{}/{}</td>'
                      '<td style="color:{}">缺 {}</td></tr>\n').format(
            name, note, METHOD_TXT.get(mark, "未登记"), color, num, den,
            "#ef4444" if gap > 0 else "#22c55e", gap)
    rates_card = (
        '<details class="card rates">'
        '<summary>📡 平台接入率 · 已登记 {known} 端（🟢机械核验 {verified}）<span class="hint">N/M 实际数量 · 🟢机械/🟡自签/🔴自治 · 点击展开明细 ▾</span></summary>'
        '<table id="rates-table"><tr><th>平台</th><th>核验</th><th>已接</th><th>缺口</th></tr>{rows}</table>'
        '</details>'
    ).format(known=known, verified=verified, rows=rate_rows)

    # 终点：一句话总结
    summary = build_summary(cl)
    summary_card = (
        '<div class="summary">'
        '<div class="bolt">⚡</div>'
        '<div><div class="text" id="summary-text">{}</div>'
        '<div class="meta">一句话总结 · 自动生成于 {} · 源: platform_adaptation_check / 变更日志 / 免疫复发记录 / 规范反哺日志</div></div>'
        '</div>'
    ).format(summary, snap.get("date", "—"))

    today_str = snap.get("date", "—")
    html = (
        '<!doctype html>\n<html lang="zh">\n<head>\n<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1"/>\n'
        '<title>系统活面板 · 峰终体验 v3</title>\n'
        '<!-- v0.8.0 零外链：无 Chart.js/字体 CDN · 断网可渲染 -->\n'
        '<style>' + CSS + '</style>\n'
        '<script>' + HEAD_JS + '</script>\n'
        '</head>\n<body>\n<div class="dash">\n'
        + hero + "\n" + ladder_html + "\n" + fourdir + "\n" + okr_html + "\n" + maint + "\n" + value_card + "\n" + rates_card + "\n" + kb_html + "\n" + summary_card + '\n'
        '</div>\n'
        '<div class="footer">'
        '<span>最后更新: ' + today_str + ' · 峰终体验 v3：峰值=闭环流 · 终点=一句话 · 中间少而真（零分数）</span>'
        '<span>数据源: evolution_deviation / 环节维护台账 / 各端 settings.json · 刷新即最新 · 零外链(v0.8.0)</span>'
        '</div>\n'
        '<script>window.PANEL_DATA = ' + json.dumps(write_panel_data_js(snap), ensure_ascii=False) + ';</script>\n'
        '<script>window.renderTrend(' + json.dumps(trend_plot, ensure_ascii=False) + ');</script>\n'
        '<script>' + LIVE_JS + '</script>\n'
        '</body>\n</html>\n'
    )
    return html

def write_live_html(html):
    os.makedirs(os.path.dirname(LIVE_HTML), exist_ok=True)
    with open(LIVE_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("[panel_snapshot] 已渲染 {}".format(LIVE_HTML))

def write_panel_data_js(snap):
    """生成 panel_data.js（刷新即最新核心）。

    HTML 用 <script src="panel_data.js"> 加载（script 不受 file:// CORS 限制），
    页面每次加载/刷新都会重新读取本文件 → 数据与 HTML 渲染解耦：
    fswatch/Stop 钩子更新本文件 → 你刷新网页 = 读到最新数据（v0.6：闭环流/四方向/维护成本/总结全量覆盖）。
    """
    cl = snap.get("closed_loop", {}) or {}
    rates = snap.get("platform_rates", {})
    # 自动解析 SSOT（与 render_html 用同一个函数·数据同源）
    coverage = _parse_coverage_from_ssot()
    # 保底：auto-parse 缺失的平台按 SSOT 自核签名补
    for name in rates:
        if name not in coverage:
            ssot_path = os.path.join(MC, "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/04-跨端接入指南.md")
            try:
                with open(ssot_path, encoding="utf-8") as f:
                    txt = f.read()
            except Exception:
                txt = ""
            if re.search(re.escape(name) + r"\s*自核", txt):
                coverage[name] = ("🟢", "自核签名 · 登记自 SSOT §二·七")
    SHARED13 = ["crossend_guard","route_inject_prompt","route_miss_feeder","kb_inject_prompt",
        "route_unknown_unknown","audit_search_kb","route_audit","route_guard_audit",
        "reply_format_guard","l3_conclusion_guard","feedback_detect",
        "rule_three_layer_guard","card_id_guard"]
    PLATFORM_CFG = {
        "WorkBuddy": os.path.expanduser("~/.workbuddy/settings.json"),
        "Qoder CN": os.path.expanduser("~/.qoder-cn/settings.json"),
        "Qoder Desktop": os.path.expanduser("~/.qoder/settings.json"),
    }
    DSH_PLUGIN = os.path.expanduser(
        "[记忆共享中心]/脚本中心/five-layer-memory/src/index.js")
    # 平台专属守卫实盘映射（SSOT §二·七 + 守卫家族实例登记·脚本文件存在即计入 +N·对齐 DSH/LobsterAI 记法）
    # 这 4 平台走 patrol 拉模式（无 CC 式 hooks），extra 只能从专属守卫脚本文件判真——不存在则 0，极端不存盘不计数
    # Hermes 走插件型（无 hook 命令列表可解析·专属守卫 hermes_read_evidence_guard.py 由 route-audit-hook
    # _READ_EVIDENCE_SCRIPT 实挂）——同样按"专属守卫脚本文件存在判真"计入，与 AutoClaw/LobsterAI/ZCode 记法一致
    PATROL_EXTRA_SCRIPT = {
        "AutoClaw": os.path.expanduser("[记忆共享中心]/脚本中心/autoclaw_gateway_guard.py"),
        "LobsterAI": os.path.expanduser("[记忆共享中心]/脚本中心/lobsterai_session_anomaly_guard.py"),
        "Trae Work": os.path.expanduser("[记忆共享中心]/脚本中心/session_memory_quality_guard.py"),
        "ZCode": os.path.expanduser("[记忆共享中心]/脚本中心/zcode_config_guard.py"),
        "Hermes": os.path.expanduser("[记忆共享中心]/脚本中心/hermes_read_evidence_guard.py"),
    }
    # 非守卫命令（挂在 hooks 里但不是"专属守卫"：渲染器/机械校验器）——统计专属守卫时剔除，防 +N 虚高
    NON_GUARD_CMDS = ("panel_snapshot.py", "platform_adaptation_check.py")
    def extra_count(name):
        if name in PATROL_EXTRA_SCRIPT:
            return 1 if os.path.exists(PATROL_EXTRA_SCRIPT[name]) else 0
        cfg = PLATFORM_CFG.get(name)
        if name == "DeepSeek Harness":
            try:
                with open(DSH_PLUGIN, encoding="utf-8") as f:
                    src = f.read()
                # 行级解析到独立 "]" 行为止——args 内联 "]" 会提前截断（实测 bug）
                seg_lines = []
                for line in src.split("STOP_GUARDS", 1)[1].splitlines():
                    if line.strip().startswith("]") and "script:" not in line:
                        break
                    seg_lines.append(line)
                seg = "\n".join(seg_lines)
                total = seg.count("script:")
                in_shared = sum(1 for s in SHARED13 if s in seg)
                return max(total - in_shared, 0)
            except Exception:
                return None
        if not cfg:
            return None
        try:
            with open(cfg, encoding="utf-8") as f:
                d = json.load(f)
            cmds = []
            for evt in ("SessionStart", "UserPromptSubmit", "Stop"):
                for it in d.get("hooks", {}).get(evt, []):
                    if "hooks" in it:
                        for hh in it["hooks"]:
                            cmds.append(hh.get("command", ""))
                    elif "command" in it:
                        cmds.append(it["command"])
            in_shared = sum(1 for c in cmds if any(s in c for s in SHARED13))
            non_guard = sum(1 for c in cmds if any(s in c for s in NON_GUARD_CMDS))
            return max(len(cmds) - in_shared - non_guard, 0)
        except Exception:
            return None
    rows = []
    def rk(item):
        v = item[1]
        return (v[0] / v[1]) if v and v[1] else -1
    METHOD_TXT = {"🟢": "机械", "🟡": "自核", "🔴": "自治"}
    for name, v in sorted(rates.items(), key=rk, reverse=True):
        if v is None:
            rows.append({"name": name, "num": None, "den": None, "mark": "❔", "method": "未登记", "note": "未解析", "extra": None})
            continue
        num, den = v
        gap = den - num
        pct = round(num / den * 100) if den else 0
        color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 50 else "#ef4444"
        mark, note = coverage.get(name, ("❔", "未登记"))
        rows.append({"name": name, "num": num, "den": den, "gap": gap,
                     "mark": mark, "method": METHOD_TXT.get(mark, "未登记"),
                     "note": note, "color": color,
                     "extra": extra_count(name)})

    # 四方向文本（与 render_html 同口径·单一来源由同一函数生成）
    det, fix, imm = cl.get("detected"), cl.get("fixed"), cl.get("immune")
    anti = cl.get("antibodies")
    mt = snap.get("maintenance", {}) or {}
    # 免疫命中 / 有效抗体（过渡基线·与 closed_loop.antibodies 同口径——免疫拦截效果·单一事实源）
    imm_h = snap.get("better_immune_hits")
    anti_e = snap.get("better_antibodies")
    if mt.get("total_commits") is not None:
        segs = " · ".join("{} {}".format(s["segment"], s["commits"]) for s in mt.get("segments", []) if s.get("commits") is not None)
        maint_line = "近7天共 {} 次提交 · 环节Top：{}（环节口径≠总量口径·示集中度）".format(mt["total_commits"], segs)
    else:
        maint_line = None

    # v0.8.0 三面孔同源：①/④ 卡复用 OKR 机械映射行（与 OKR 区同一读数·根治口径脱节）
    _okr_rows_js = (snap.get("okr") or {}).get("objectives") or []
    _oa = next((o for o in _okr_rows_js if o.get("dir") == "auto"), {})
    _ok = next((o for o in _okr_rows_js if o.get("dir") == "knows"), {})
    def _pf(v):
        return ("{}%".format(v) if isinstance(v, (int, float)) else "—")

    data = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "closed_loop": {
            "detected": det, "fixed": fix, "immune": imm,
            "immune_total": cl.get("immune_total"), "immune_last_date": cl.get("immune_last_date"),
            "antibodies": anti, "pending": cl.get("pending"),
            "trend": cl.get("trend", []),
        },
        "summary": build_summary(cl),
        "four_dir": {
            "auto": "自动触发占比 {} · 覆盖 {}".format(
                _pf(_oa.get("auto_closure")), _oa.get("auto_cov") or "—"),
            # 2026-09-27 童灵根治：基线是倍数语义（免疫命中÷抗体），⛔按百分比渲染出过"2349%"
            # 10-07 终审轮：state=定案 时四方向②卡同步切定案读数（活跃口径+全史对照，⛔不再挂过渡文案）
            "better": ("漏触发修复率(近14天活跃) {:.0%} · 全史对照 {:.0%} · 双载体池 {} 条".format(
                snap["better_join_active"], (snap.get("better_join_all") or 0),
                snap.get("better_pool") or "—")
                if (snap.get("better_state") == "定案" and snap.get("better_join_active") is not None)
                else "免疫命中 {}（累计） · 有效抗体 {} · {}".format(
                    imm_h if imm_h is not None else "—",
                    anti_e if anti_e is not None else "—",
                    ("命中/抗体 {:.1f} 倍".format(snap.get("better_baseline"))
                     if isinstance(snap.get("better_baseline"), (int, float)) else "基线 —"))),
            "evo": "本季进化事件 {} · 净采纳率 {}".format(
                snap.get("evo_events") if snap.get("evo_events") is not None else "—",
                (("{:.0f}%".format( snap.get("evo_adoption_rate")*100)) if snap.get("evo_adoption_rate") is not None else "待量")),
            "knows": "本月 {} 条 · 本季累计 {}/{} · 剩 {} 天".format(
                snap.get("knows_count") if snap.get("knows_count") is not None else "—",
                _ok.get("current") if _ok.get("current") is not None else "—",
                _ok.get("target_pct") if _ok.get("target_pct") is not None else "—",
                snap.get("knows_days_left") if snap.get("knows_days_left") is not None else "—"),
            "auto_state": snap.get("auto_state") or "定案",
            "better_state": snap.get("better_state") or "过渡",
            "evo_state": snap.get("evo_state") or "定案",
            "knows_state": snap.get("knows_state") or "过渡",
            "knows_note": "过渡=认知发现数·自然月归当月 · 定案=预测准确率（需先建「预测vs实际」成对标签）",
        },
        "maintenance_line": maint_line,
        "platform_rates": rows,
        "knowledge_ladder": snap.get("knowledge_ladder"),
        "knowledge_base": snap.get("knowledge_base"),  # 2026-09-08 童灵根治：知识库可视化3模块数据
        "hermes_kpi": snap.get("hermes_kpi"),
        "okr": snap.get("okr"),
        # 2026-09-03 童灵新增：全自动化指标扩展字段（snap层面，与okr层面同源）
        "auto_coverage": snap.get("auto_coverage"),  # 覆盖面：有埋点的守卫数（机械计算）
        "auto_closure_rate": snap.get("auto_closure_rate"),  # 第二指标：自动闭环率（数据积累中可能为None）
        "auto_breakdown": snap.get("auto_breakdown"),  # 分母构成：total/hook_auto/manual/other
        "auto_state": snap.get("auto_state"),  # 状态：过程代理/定案
    }
    js_path = os.path.join(os.path.dirname(LIVE_HTML), "panel_data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("// 面板实时数据（panel_snapshot v0.9.2 生成·勿手改）\n")
        f.write("window.PANEL_DATA = {};\n".format(json.dumps(data, ensure_ascii=False)))
    print("[panel_snapshot] 已更新 {}".format(js_path))
    return data

if __name__ == "__main__":
    snap = take_snapshot()
    # 总是用最新数据覆盖当日快照（避免陈旧数据残留）
    if already_has_date(snap["date"]):
        rows = read_timeseries()
        rows = [r for r in rows if r.get("date") != snap["date"]]
        rows.append(snap)
        os.makedirs(os.path.dirname(TS_PATH), exist_ok=True)
        with open(TS_PATH, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("[panel_snapshot] 已更新 {} 快照".format(snap["date"]))
    else:
        append_snapshot(snap)
        print("[panel_snapshot] 已追加 {} 快照".format(snap["date"]))
    # A v2 治理闸门（机械化对账）：注册表变动未留治理记录 → 大声报错+OKR区红框
    try:
        _alarm = check_registry_governance(list((snap.get("platform_rates") or {}).keys()))
    except Exception:
        _alarm = None
    if _alarm:
        print("[REGISTRY-GOVERNANCE] " + _alarm)
        snap["registry_alarm"] = _alarm
    html = render_html(snap)
    write_live_html(html)

# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"~/个人AI档案/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass