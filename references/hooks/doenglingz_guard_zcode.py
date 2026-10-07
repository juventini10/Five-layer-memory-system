#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# TRUTH_OF: 脚本中心/doenglingz_guard_zcode.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""doenglingz_guard_zcode.py —— Stop 钩子·童灵守护三查（数字分身常驻守卫·ZCode 端）
设计定位：童灵"守护"职能（02-治理与灰度设计规范§五）在 ZCode 运行时刻的机械落点。
  依据：宪法愿景「分身让规则在每次执行中被真正执行」+ 02规范守护三查(合规/价值/漂移)。
挂载：~/.zcode/cli/config.json → hooks.events.Stop（配置文件钩子·hooks.enabled=true 已开）。
执行对象：Stop 钩子传入的最终回复文本（stdin JSON 宽容键序 text/prompt/content/…），
  并把观测到的 stdin 顶层键名写入台账——载荷 schema 不靠猜，首跑后自证。
契约：--check(JSON,含 alarm) / --report(markdown明细) / --selfcheck(挂载自检) /
  --self-test(六用例·供 guard_selftest_check.py 聚合器发现)。
机械边界（02规范§五.3 守护自限）：只扫成文硬红线(红区六类+铁律版关键词·模式源=02规范§二)，
  价值/漂移类软信号不静默裁决→仅提示"建议你质证"，alarm 不置 true（防误拦·自主≠黑箱）。
报告制守卫三纪律：失败默认放行（任何异常 exit 0·绝不阻塞对话）·只检测不修改·台账可观测。
台账：写 /tmp/doenglingz_guard_state_zcode.json（单行 JSON 追加·tail -n1=末条；
  每端独立文件先例对齐 qodercn 后缀方案）。
跨端适配：06-跨端适配规范§二（内核不分端·装载分态·本端适配器·各端自行实施）。
"""
import os
import re
import json
import sys
from datetime import datetime

CONFIG_DEFAULT = os.path.expanduser("~/.zcode/cli/config.json")
_WB_ROOT = os.environ.get("DOENGLINGZ_CONFIG_DIR") or os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy")  # 台账统一根·三段对齐共脚本 DOENGLINGZ>WORKBUDDY>~/.workbuddy（2026-10-06 PAT-081 验证卡·读写同根防串他端旧账）
STATE_DEFAULT = os.path.join(_WB_ROOT, "doenglingz_guard_state_zcode.json")
INJECT_STATE = os.path.join(_WB_ROOT, "doenglingz_inject_state.json")   # 与 doenglingz_inject_prompt.py 实盘落点对齐（W1 触发台账）
W1_WATERMARK = "/tmp/doenglingz_guard_w1_watermark.txt"  # 已检查的 w1 触发水位线
W1_PROOF = "童灵上岗"  # 行为契约自证词（v1.3 契约注入要求回复含此行）

# ── 红区六类硬关键词（02规范§二·不可逆+影响身份；与 doenglingz_guard.py QoderCN 同源）──
# 仅"提示性扫描"：机械命中代表"此回复可能涉及红区动作"，须你/AI 复核，不直接拦。
RED_ZONE_PATTERNS = [
    r"删除记忆", r"清空调", r"rm\s+-rf",
    r"跨根迁移", r"对外发布", r"发布视频", r"发布文章", r"发布安装包",
    r"变更\s*SOUL", r"改铁律", r"信用授权", r"新授权", r"收回授权",
    r"记忆架构根变更",
]

# ── 铁律/记忆规则硬触线（不可逆删除类·可机械判定）──
HARD_VIOLATION_PATTERNS = [
    r"rm\s+-rf\s+~", r"rm\s+-rf\s+/Users", r"rm\s+-rf\s+\$HOME",
    r"直接\s+rm\s", r"直接删除.*(Desktop|Downloads|Documents)",
]

# ── 认知深化信号关键词（童灵第五入口沉淀机制·对齐 QoderCN v0.2）──
REFLECTION_SIGNAL_PATTERNS = [
    r"今天.*收获", r"今天.*学到", r"今天.*发现",
    r"我.*发现", r"我.*意识到", r"我.*认识到",
    r"认知深化", r"经验沉淀", r"童灵.*沉淀",
    r"分母统一", r"口径统一", r"标准统一",
    r"自动化优先", r"SSOT", r"唯一真源",
]

# ── 隐私红线扫描（童灵规格书 §四 硬红线④·密钥/Token/密码绝不外传）──
# 提示性扫描（同红区模式·非阻断）：机械命中代表"此输出可能泄露凭据"，须你/AI 复核。
# 仅匹配具体凭据形态，避免正文提及"密码/密钥"等词误报。
PRIVACY_PATTERNS = [
    r"sk-[a-zA-Z0-9]{20,}",          # OpenAI/通用 sk- 密钥
    r"AKIA[0-9A-Z]{16}",             # AWS Access Key
    r"ghp_[a-zA-Z0-9]{36}",          # GitHub PAT
    r"xox[baprs]-[a-zA-Z0-9-]{10,}", # Slack Token
    r"api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}",
    r"token\s*[:=]\s*['\"]?[a-zA-Z0-9_\-\.]{16,}",
    r"password\s*[:=]\s*['\"]?\S{8,}",
    r"secret\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}",
]

RED_ZONE_RE = re.compile("|".join(RED_ZONE_PATTERNS))
HARD_VIOLATION_RE = re.compile("|".join(HARD_VIOLATION_PATTERNS))
REFLECTION_SIGNAL_RE = re.compile("|".join(REFLECTION_SIGNAL_PATTERNS))
PRIVACY_RE = re.compile("|".join(PRIVACY_PATTERNS))

# Stop 载荷文本候选键（宽容读取·命中第一个非空字符串即止）
# responseText/last_assistant_message = ZCode 运行时 Stop 载荷实测键名（2026-08-29 台账
# stdin_keys 18 键实证；缺这两个键则守卫空转扫空文本·text_len=0 同构 WB 端病灶）。
TEXT_KEYS = ["text", "prompt", "content", "responseText", "response",
             "message", "last_assistant_message", "last_message",
             "responsePreview", "output", "assistant_message"]


def _config_path():
    return os.environ.get("ZCODE_CONFIG", CONFIG_DEFAULT)


def _state_file():
    return os.environ.get("DOENGLINGZ_GUARD_STATE_FILE", STATE_DEFAULT)


def get_text_from_stdin():
    """读 stdin JSON，返回 (text, observed_keys)：宽容提取回复文本并记录载荷结构。"""
    try:
        raw = sys.stdin.read() or "{}"
        d = json.loads(raw)
    except Exception:
        return "", []
    if not isinstance(d, dict):
        return str(d)[:2000], []
    observed = sorted(d.keys())
    for k in TEXT_KEYS:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v, observed
    return "", observed


def _findall(rex, text):
    """findall 在组合正则含捕获组时会退化为返回组内容而非整段匹配（t_hard 用例实证），
    统一走 finditer.group(0)。"""
    seen, out = set(), []
    for m in rex.finditer(text):
        s = m.group(0)
        if s not in seen:
            seen.add(s)
            out.append(s)
    return sorted(out)


def scan(text):
    """扫描文本，返回 (red_hits, hard_hits, reflection_signals, privacy_hits, alarm)"""
    red_hits = _findall(RED_ZONE_RE, text)
    hard_hits = _findall(HARD_VIOLATION_RE, text)
    reflection_signals = _findall(REFLECTION_SIGNAL_RE, text)
    privacy_hits = _findall(PRIVACY_RE, text)
    alarm = len(hard_hits) > 0
    return red_hits, hard_hits, reflection_signals, privacy_hits, alarm


def write_state(text_len, red_hits, hard_hits, reflection_signals,
                privacy_hits, alarm, observed_keys=None, w1_not_honored=False):
    """台账：单行 JSON 追加（tail -n 1 = 最后一条记录）"""
    record = {
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "host": "zcode",
        "w1_not_honored": bool(w1_not_honored),
        "text_len": text_len,
        "red_zone_hits": ",".join(red_hits),
        "hard_violation_hits": ",".join(hard_hits),
        "reflection_signals": ",".join(reflection_signals),
        "privacy_hits": ",".join(privacy_hits),
        "alarm": alarm,
    }
    if observed_keys is not None:
        record["stdin_keys"] = ",".join(observed_keys)
    try:
        with open(_state_file(), "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def last_record():
    sf = _state_file()
    if not os.path.exists(sf):
        return None
    try:
        with open(sf) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        return lines[-1] if lines else None
    except Exception:
        return None


def mode_selfcheck():
    """挂载自检（06§2.1 三要素）：①是否被发现 ②是否可执行 ③最近实际调用台账"""
    in_config = "❌ 否"
    try:
        with open(_config_path()) as f:
            content = f.read()
        if "doenglingz_guard_zcode" in content:
            # enabled 门是配置文件钩子的总开关（pitfall#1）
            m = re.search(r'"enabled"\s*:\s*(true|false)', content)
            gate = m.group(1) if m else "?"
            in_config = f"✅ 是（hooks.enabled={gate}）"
    except Exception as e:
        in_config = f"⚠️ 无法读取 config.json（{type(e).__name__}）"
    exec_ok = "✅ 是" if os.access(os.path.abspath(__file__), os.X_OK) else "❌ 否(chmod +x 缺失)"
    rec = last_record()
    ledger = rec if rec else "（无调用台账·尚未被 Stop 链实际调用）"
    print("## 🔍 童灵守卫挂载自检 (doenglingz_guard_zcode.py · ZCode)")
    print()
    print("| 检查项 | 结果 |")
    print("|---|---|")
    print(f"| 在 config.json Stop 链中 | {in_config} |")
    print(f"| 脚本可执行 | {exec_ok} |")
    print(f"| 最近一次实际调用台账 | {ledger} |")
    print()
    print("> 三项均正常=童灵守护已在 ZCode 运行时刻生效；任一异常=机制静默失效（须修）。")


def mode_check(text):
    red_hits, hard_hits, refl, privacy_hits, alarm = scan(text)
    write_state(len(text), red_hits, hard_hits, refl, privacy_hits, alarm)
    print(json.dumps({
        "text_len": len(text),
        "red_zone_hits": ",".join(red_hits),
        "hard_violation_hits": ",".join(hard_hits),
        "reflection_signals": ",".join(refl),
        "privacy_hits": ",".join(privacy_hits),
        "alarm": alarm,
    }, ensure_ascii=False))


def mode_report(text):
    red_hits, hard_hits, refl, privacy_hits, alarm = scan(text)
    write_state(len(text), red_hits, hard_hits, refl, privacy_hits, alarm)
    if not alarm and not red_hits and not refl and not privacy_hits:
        print("✅ 童灵守护三查：未检出硬红线触线，红区提示性扫描无命中，无认知深化信号，无隐私泄露特征")
        return
    print("## ⚠️ 童灵守护三查扫描结果（ZCode）")
    print()
    if hard_hits:
        print(f"- 🔴 **硬触线（已报警）**：{', '.join(hard_hits)} —— 可能涉及不可逆删除·须确认走 trash 而非 rm")
    if red_hits:
        print(f"- 🟡 **红区提示（建议你质证·非静默裁决）**：{', '.join(red_hits)} —— 红区六类之一·分身不代批")
    if refl:
        print(f"- 🔵 **认知深化信号**：{', '.join(refl)} —— 建议用 system-logger --reflection 记 [童灵思考]")
    if privacy_hits:
        print(f"- 🟡 **隐私泄露特征（建议你质证·非静默裁决）**：{', '.join(privacy_hits)} —— 童灵规格书§四红线④·密钥/Token/密码绝不外传")
    print()
    print("> 价值/漂移类软信号不在此静默裁决（02规范§五.3 守护自限），须你/AI 复核。")


def run_self_test():
    """六用例自测（零副作用：临时状态文件+显式清理）→ 全过返回 0，否则打印明细返 1。"""
    import tempfile
    old_state = os.environ.get("DOENGLINGZ_GUARD_STATE_FILE")
    fd, tmp = tempfile.mkstemp(prefix="doenglingz_guard_zcode_test_")
    os.close(fd)
    try:
        os.environ["DOENGLINGZ_GUARD_STATE_FILE"] = tmp
        cases = []

        def case(name, fn):
            try:
                fn()
                cases.append((name, True, ""))
            except AssertionError as e:
                cases.append((name, False, str(e)))
            except Exception as e:  # 自测框架自身不得崩
                cases.append((name, False, f"{type(e).__name__}: {e}"))

        def t_clean():
            hits, hard, _, _, alarm = scan("正常回复：已完成代码审查，未改动守卫。")
            assert (hits, hard, alarm) == ([], [], False), (hits, hard, alarm)

        def t_red_zone():
            hits, _, _, _, alarm = scan("建议把记忆架构根变更一起做了。")
            assert "记忆架构根变更" in hits and not alarm, (hits, alarm)

        def t_hard():
            _, hard, _, _, alarm = scan("可以直接 rm -rf ~/个人AI档案 清理。")
            assert alarm and len(hard) >= 1, (hard, alarm)

        def t_state_write():
            assert last_record() is None, "临时台账应从空开始"
            write_state(10, [], [], [], [], False)
            rec = last_record()
            assert rec and '"host":"zcode"' in rec or rec and '"host": "zcode"' in rec, rec

        def t_reflection():
            _, _, refl, _, _ = scan("今天发现一个模式：唯一真源收敛减少了重复维护。")
            assert any("唯一真源" in x for x in refl), refl

        def t_always_pass_exit():
            # 报告制纪律：mode_check/mode_report 对任何输入都不得 raise
            for txt in ["", "rm -rf ~ 全部删除"]:
                red, hard, refl, privacy_hits, alarm = scan(txt)
                write_state(len(txt), red, hard, refl, privacy_hits, alarm)
                assert isinstance(alarm, bool)

        case("clean_scan无命中", t_clean)
        case("red_zone识别且不置alarm", t_red_zone)
        case("hard触线置alarm", t_hard)
        case("state台账单行追加", t_state_write)
        case("reflection信号识别", t_reflection)
        case("报告制任意输入可跑", t_always_pass_exit)

        failed = [c for c in cases if not c[1]]
        print(json.dumps({"total": len(cases),
                          "failed": len(failed),
                          "detail": [{"case": n, "err": e} for n, ok, e in cases if not ok]},
                         ensure_ascii=False))
        return 0 if not failed else 1
    finally:
        if old_state is None:
            os.environ.pop("DOENGLINGZ_GUARD_STATE_FILE", None)
        else:
            os.environ["DOENGLINGZ_GUARD_STATE_FILE"] = old_state
        try:
            os.unlink(tmp)
        except Exception:
            pass


def check_w1_honor(text):
    """v1.3 启动兑现检测：本回合前若有未消费的 W1 触发，回复须含自证词。
    返回 True=兑现/无触发；False=缺位；None=无法判定（失败放行语义）。
    水位线文件记录已检查的 w1 触发 ts——同一触发只检一次。"""
    try:
        if not os.path.exists(INJECT_STATE):
            return None
        last_w1 = None
        with open(INJECT_STATE, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if d.get("w1") is True:
                        last_w1 = d.get("ts")
                except Exception:
                    pass
        if not last_w1:
            return None
        seen = ""
        if os.path.exists(W1_WATERMARK):
            with open(W1_WATERMARK, encoding="utf-8") as f:
                seen = f.read().strip()
        if last_w1 == seen:
            return None  # 已检查过
        with open(W1_WATERMARK, "w", encoding="utf-8") as f:
            f.write(last_w1)
        return W1_PROOF in (text or "")
    except Exception:
        return None


def main():
    args = sys.argv[1:]

    if "--selfcheck" in args:
        mode_selfcheck()
        return
    if "--self-test" in args:
        sys.exit(run_self_test())

    if "--report" in args:
        text, keys = get_text_from_stdin()
        red, hard, refl, privacy_hits, alarm = scan(text)
        write_state(len(text), red, hard, refl, privacy_hits, alarm, keys)
        mode_report(text)
        return

    # hook 默认模式（--check 或裸调）：扫描→台账→有命中才输出告警文本，全程 exit 0 放行
    try:
        text, keys = get_text_from_stdin()
        red, hard, refl, privacy_hits, alarm = scan(text)
        w1_honored = check_w1_honor(text)
        write_state(len(text), red, hard, refl, privacy_hits, alarm, keys,
                    w1_not_honored=w1_honored is False)
        if alarm:
            mode_report(text)  # 仅硬触线报警时输出（避免每轮噪音）
        if w1_honored is False:
            # W1 契约未兑现：报告制提示（注入下轮对话·岗位3 判据②可扫台账汇总）
            print("⚠️ 童灵执行侧缺位：本回合 W1 已触发（'启动童灵'类）但回复未含童灵上岗自证"
                  "——已登记 w1_not_honored，下回合须以童灵身份补位。")
    except Exception:
        pass  # 失败默认放行
    sys.exit(0)


if __name__ == "__main__":
    main()
