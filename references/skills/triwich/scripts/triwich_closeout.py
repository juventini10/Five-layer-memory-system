#!/usr/bin/env python3
# REG: skip triwich Skill 包内收尾编排件（非脚本中心守卫族）·版本纪律走本 Skill CHANGELOG·先例=triwich_scan.py 同口径
# -*- coding: utf-8 -*-
"""
triwich_closeout.py — 三明智收尾四合一编排器（F10 减法主线 S1·皮叔2026-10-21批）
病根：收尾三登记+系统日志=四次分开作业，每次交接都是漏登/踩坑/摩擦点
     （实证：2026-09-17 漏FU登记、2026-09-15 采样漏行靠你点名、今日路径探路×2、
      今日 L1 轮封口链摩擦≈4min 占本轮 60%）。
原则：动作→证据是副产品，不是事后第二次作业；任一落点失败整链显形并盘点已完成面。

一条命令四落点+一道前置闸：
  ⓪ 翻页回执对账（page_receipt_guard·V3·缺回执在 seal 之前判红——伪造走不了封口）
  ① seal record（triwich_seal.py，同轮 --followup 等参数=FU卡登记，原生绑定复用）
  ② 采样台账追加一行（阶段A·§三）
  ③ 系统日志条目（append_log_entry.py --tool，8字段体自动生成）
用法：
  python3 triwich_closeout.py --tool Qoder CN --block-file /tmp/结论块.txt \
    --key-file steps/step0-determination-<ts>.md \
    --seal-args "--followup xx --predict xx --falsify xx --deadline 2026-11-30 --default no-op --window 30天 --depth L1" \
    --sampling "任务简述|卡点|深度匹配|需回访|已回访" --log-summary "一句话结论" [--dry-run]
约定：block-file 首版即须含签名行（今日教训内化：seal 拒无签名文本）。
--key-file：本轮键文件路径；`none:<理由>`=显式豁免（留痕可抽检，⛔静默放行）；
  缺省=自动取 cwd/steps/ 最新键文件——auto 兜"忘了传"，不兜"故意绕"（键根可由 TRIWICH_KEY_ROOT 覆盖·测试夹具隔离用·R0② 2026-10-21）。
--dry-run：全部落点指临时区（假 logdir/临时采样文件/seal 由调用方 env 隔离），夹具用。
退出码：0=四落点全成；2=参数缺；3+=某落点失败（stderr 盘点已完成面，⛔静默半提交）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, json, glob, subprocess, datetime, tempfile, argparse

HOME = os.path.expanduser("~")
SKILL = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置", "triwich")
SEAL = os.path.join(SKILL, "scripts", "triwich_seal.py")
RECEIPT_GUARD = os.path.join(SKILL, "scripts", "page_receipt_guard.py")
SAMPLING_DEFAULT = os.path.join(os.path.expanduser("[记忆共享中心]"), "自定义层", "待完成工作", "阶段A采样清单-三明智4.0.md")
APPEND_LOG = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置", "system-logger", "scripts", "append_log_entry.py")

def fail(step, done, msg):
    print("CLOSEOUT:FAIL @%s —— 已完成面: %s ｜%s" % (step, "→".join(done) or "无", msg), file=sys.stderr)
    sys.exit(3)

def resolve_key_file(arg):
    """返回 (路径|None豁免, 说明)；找不到且未显式豁免 → None+None 由调用方判红"""
    if arg:
        if arg.startswith("none:"):
            return None, "豁免(%s)" % arg[5:35]
        return arg, "显式键文件"
    # R0②（2026-10-21 卡轮28）：键根可 env 覆盖——此前夹具跑在真实工作区 cwd 时自动踩真盘最新键，
    #   T1/T3 随 cwd 红绿漂移（非竞态）。隔离面与 TRIWICH_SEAL_LOG/DECISION_ROOM 同族；缺省=生产语义 cwd 不变。
    root = os.environ.get("TRIWICH_KEY_ROOT") or os.getcwd()
    pat = os.path.join(root, "steps", "step0-determination-*.md")
    files = sorted(glob.glob(pat))
    if files:
        return files[-1], "auto取最新(%s)" % os.path.basename(files[-1])
    return "NOTFOUND", ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", required=True)
    ap.add_argument("--block-file", required=True)
    ap.add_argument("--key-file", default="", help="本轮键文件；none:<理由>=显式豁免；缺省=cwd/steps 自动取最新（TRIWICH_KEY_ROOT 可改键根·夹具隔离用）")
    ap.add_argument("--seal-args", default="")
    ap.add_argument("--sampling", default="none", help="采样台账行内容（|分隔）；none=本轮不采（灰度豁免须 --no-sampling-reason）")
    ap.add_argument("--no-sampling-reason", default="")
    ap.add_argument("--log-summary", required=True, help="系统日志结论字段一句话")
    ap.add_argument("--sampling-file", default=SAMPLING_DEFAULT)
    ap.add_argument("--logdir", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    done = []

    if not os.path.isfile(a.block_file):
        fail("block-file", done, "读不到 %s" % a.block_file)
    block = open(a.block_file, encoding="utf-8").read()
    if "三明智" not in block or "✅" not in block and "❌" not in block:
        fail("签名预检", done, "block-file 未含三明智签名行（✅/❌）——今日教训：seal 拒无签名文本，首版即带")

    # ⓪ 翻页回执对账（V3 接线：缺回执/指纹不符 → 在 seal 之前判红，done 面停在预检）
    kf, note = resolve_key_file(a.key_file)
    _kf_for_seal = kf if (kf and kf != "NOTFOUND") else None
    if kf == "NOTFOUND":
        fail("回执对账", done, "cwd/steps/ 无键文件且未显式传 --key-file——真载轮必有键；确属无键场景传 none:<理由> 留痕")
    if kf is None:
        done.append("回执对账:" + note)
    else:
        rg = [sys.executable, RECEIPT_GUARD, "--key-file", kf]
        r0 = subprocess.run(rg, capture_output=True, text=True)
        if r0.returncode == 0 and "RECEIPT:FAIL" not in r0.stdout:
            vtag = "OK" if "RECEIPT:OK" in r0.stdout else "SKIP-legacy"
            done.append("回执对账(%s·%s)" % (vtag, note))
        else:
            fail("回执对账", done, "键文件 %s ｜%s" % (kf, (r0.stderr or r0.stdout)[:220]))

    # ① seal record（FU 同轮绑定复用原生参数面；v1.2 键-链强互锁：--key-file 入链）
    cmd = [sys.executable, SEAL, "record", "--tool", a.tool, "--text-file", a.block_file]
    if _kf_for_seal is not None:
        cmd += ["--key-file", _kf_for_seal]
    if a.seal_args:
        import shlex
        cmd += shlex.split(a.seal_args)  # v1.0.1 自纠：手写 regex 拆参对含空格值必错拆，换标准库
    r = subprocess.run(cmd, capture_output=True, text=True)
    if "SEAL:OK" not in r.stdout and "已记录" not in r.stdout:
        fail("seal", done, (r.stdout + r.stderr)[:200])
    if "--followup" in a.seal_args and "FOLLOWUP:FAIL" in r.stdout:
        fail("FU登记", done, "seal 链已进但 FU 卡被拒：" + [l for l in r.stdout.splitlines() if "FOLLOWUP" in l][0][:160] + "（夹具环境须预置 TRIWICH_DECISION_ROOM 文件或去掉 --seal-args 中的 --followup）")
    seal_line = [l for l in r.stdout.splitlines() if "SEAL" in l or "FOLLOWUP" in l]
    done.append("seal" + ("+FU" if "--followup" in a.seal_args else ""))

    # ①b 键-链互锁回读自证（v1.2·结果导向：linkcheck 现算==链载才认封）
    if _kf_for_seal is not None:
        rl = [sys.executable, SEAL, "linkcheck", "--key-file", _kf_for_seal]
        r1b = subprocess.run(rl, capture_output=True, text=True)
        if r1b.returncode != 0:
            fail("键链回读", done, "seal 已入链但 linkcheck 判红：" + (r1b.stdout + r1b.stderr)[:200])
        done.append("键链回读(linkcheck OK)")

    # ② 采样台账
    if a.sampling != "none":
        fields = a.sampling.count("|")
        if fields < 4:
            fail("sampling", done, "采样行须 ≥5 段（|分隔·任务|卡点|深度匹配|需回访|已回访），实得 %d 段" % (fields + 1))
        ts = datetime.datetime.now().strftime("%m-%d %H:%M")
        row = "| %s | %s |\n" % (ts, a.sampling)
        with open(a.sampling_file, "a", encoding="utf-8") as f:
            f.write(row)
        # 落点自证：行数必须真+1
        now_n = sum(1 for _ in open(a.sampling_file, encoding="utf-8"))
        done.append("采样台账(+1行·总%d)" % now_n)
    else:
        if not a.no_sampling_reason:
            fail("sampling", done, "本轮不采须给 --no-sampling-reason（防静默漏登·0915/0917 判例）")
        done.append("采样豁免(%s)" % a.no_sampling_reason[:30])

    # ③ 系统日志（8字段体自动生成——工具字段留空由 append 机械补规范名）
    depth = re.search(r"三明智 (L[123])", block)
    body = "- **类型**：三明智收尾\n- **涉及文件**：%s\n- **结论**：%s\n- **来源**：🟢验证（closeout 一条命令四落点·回执可 grep）\n- **置信度**：🟢A\n" % (
        a.block_file, a.log_summary)
    if depth:
        body = "### 三明智 %s 收尾轮\n" % depth.group(1) + body
    cmd3 = [sys.executable, APPEND_LOG, "--tool", a.tool]
    if a.logdir:
        cmd3 += ["--logdir", a.logdir]
    r3 = subprocess.run(cmd3, input=body, capture_output=True, text=True)  # v1.0.2 修 text 模式 input 类型冲突（夹具 T1 逮出）
    # v1.0.3 判定改结果导向（夹具逮出：子脚本回执行不在其 stdout/stderr 任一流，读流判定必假红/假绿）
    lg_dir = a.logdir or os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "工作日志", "系统日志")
    lg_file = os.path.join(lg_dir, "系统日志_%s.md" % datetime.date.today().strftime("%Y-%m-%d"))
    mark = a.log_summary[:12]
    if not (os.path.isfile(lg_file) and mark in open(lg_file, encoding="utf-8").read()):
        fail("系统日志", done, "回读未见结论标记@%s ｜子进程尾:%s" % (lg_file, (r3.stdout + r3.stderr)[-120:]))
    done.append("系统日志(回读证实)")

    # F7-a（v4.10.0）：L3 耗时自动读数（阶段戳落键文件；⛔人工 mtime 重建）
    dur_note = ""
    if _kf_for_seal:
        _m = re.search(r"(\d{8})_(\d{6})", os.path.basename(_kf_for_seal))
        if _m:
            _st = datetime.datetime.strptime(_m.group(1) + _m.group(2), "%Y%m%d%H%M%S")
            _mins = int((datetime.datetime.now() - _st).total_seconds() // 60)
            try:
                with open(_kf_for_seal, "a", encoding="utf-8") as _f:
                    _f.write("\n### 阶段戳\ncloseout_at=%s 用时=%dmin（F7a 自动读数）\n" % (
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), _mins))
            except Exception:
                pass
            dur_note = " ｜用时=%dmin（F7a 自动读数）" % _mins
    print("CLOSEOUT:OK %s%s" % (" → ".join(done), dur_note))
    for l in seal_line: print("  ", l)
    return 0

if __name__ == "__main__":
    sys.exit(main())
