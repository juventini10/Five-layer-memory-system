#!/usr/bin/env python3
"""K2 切片生成器（v0.1·2026-08-24）——规格书 SSOT → 切片产物的单向流水线。

对齐 D3 设计定稿 §6.2/6.3：
  - core_slice: 注入声明+L1（每会话必注·0.96x SOUL）
  - L6 反向切片: priority=high（对抗性重注·每会话必注）
  - L2/L3/L4/L5 域切片: 按 trigger 路由（按需注入）

幂等可重跑：只读规格书→写切片产物目录，重跑输出一致（src_hash 校验）。
对齐引擎验收四问：契约明确（进规格书/出切片 md）/真源唯一（规格书）/幂等/评测挂接。

用法:
  python3 k2_slice_generator.py [--out 产物目录] [--dry-run]
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import hashlib
import os
import re
import sys
import datetime

# 路径相对本目录的上级「数字分身/」（真身 K2切片蒸馏/ 与部署态 k2-slice-generator/ 同构）：
#   规格书在「数字分身/」根（本目录的上级）；切片恒定输出到 <数字分身>/K2切片蒸馏/slices/。
#   ⚠️ 2026-10-05 路径口径收敛（审计报告 P1-1·方案C）：不论真身/部署态，输出恒定落
#      <数字分身>/K2切片蒸馏/slices —— 与安装器检测 / hook 读者 / 端 Skill / 《入门指南-通用版》
#      口径一致（单一真源）。此前落 BASE/slices，部署态脚本在 k2-slice-generator/ 时
#      会错落 k2-slice-generator/slices，致安装器与 ~15 个 hook 找不到切片。
#   不写死任何机器的绝对路径，拷贝到任意端、无参数即可跑。
BASE = os.path.dirname(os.path.abspath(__file__))
SPEC_DEFAULT = os.path.join(os.path.dirname(BASE), "童灵·人格规格书.md")
OUT_DEFAULT = os.path.join(os.path.dirname(BASE), "K2切片蒸馏", "slices")

DOMAIN_TRIGGERS = {
    "L2": ["分析", "为什么", "本质", "底层", "模式", "分类"],
    "L3": ["阻塞", "验证", "让步", "边界", "方案", "裁决", "盘子", "预置", "排序", "优先级", "排期", "吞吐", "预估", "安排"],
    "L4": ["文案", "口播", "表达", "故事", "命名", "变现"],
    "L5": ["盲区", "终审", "裁决归属", "边界"],
    "L6": ["冲动", "疲劳", "睡眠", "偏差", "对质"],
}


def extract_core(spec):
    """注入声明 + L1 全量（恒驻最小核·设计意图）。

    跳过 ## 🔧 机制登记（指针）：其为纯导航指针（零问题门禁/童灵思考），
    按 K2 定案「以 trigger 簇为边界·到处调用非到处注入」应按需 Read 规格书，不进恒驻核。
    2026-09-11 恒驻核瘦身：10973B→9463B≈1.42×SOUL（目标≤1.5×）。
    """
    decl_m = re.search(r"^## ⚡ 运行时注入声明.*?(?=^## 🔧 机制登记|^## 📍 续蒸游标)", spec, re.M | re.S)
    decl = decl_m.group(0).strip() if decl_m else ""
    l1_m = re.search(r"^## L1 · .*?(?=^## L2 · )", spec, re.M | re.S)
    l1 = l1_m.group(0).strip() if l1_m else ""
    return strip_meta(f"{decl}\n\n{l1}").strip()


def extract_layer(spec, num):
    """提取指定层（含标题）。"""
    m = re.search(rf"^## {num} · .*?(?=^## L?[1-6] · |^## 🔁|^## 📍|\Z)", spec, re.M | re.S)
    return strip_meta(m.group(0)).strip() if m else ""


def strip_meta(text):
    """剔除写作期 HTML 注释（骨架模板里的人话引导等元信息），不进切片。
    兜底：即便 AI 据骨架生成规格书时没删干净引导，切片也不会残留。"""
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def slug(num, title):
    t = title.split("（")[0].split("·")[0].strip()
    return f"{num}_{t}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("spec", nargs="?", default=SPEC_DEFAULT)
    args = ap.parse_args()

    # 人话报错（同族 hexaco_slice_generator.fail:263 的姿势·⛔不抛 traceback）：
    #   规格书不是预置文件——装机日它本就不存在，用户/AI 需先把 onboarding 骨架模板
    #   复制到位并改名（口径同 INSTALL.md「首次由 AI 复制骨架模板到 数字分身/ 根、改名」）。
    #   旧行为=裸 FileNotFoundError 栈，对非编程用户是死胡同；此处给出源路径、目标文件名、可复制的两条命令。
    if not os.path.exists(args.spec):
        tpl = os.path.join(os.path.dirname(BASE), "onboarding", "童灵·人格规格书-骨架模板.md")
        print("\n[X] 没找到规格书，生成器没法跑：\n   %s" % args.spec)
        print("   规格书不是预置文件，需要先从骨架模板复制过来并改名：")
        print("     源模板：%s" % tpl)
        print("     复制为：%s" % args.spec)
        print("   复制后照模板开头「给 AI 的总引导」逐层填你自己的资料，再重跑本脚本。")
        print("   嫌麻烦可以直接对你的 AI 说：帮我造数字分身——它会复制模板、改名、陪你逐层蒸。")
        return 2

    with open(args.spec, encoding="utf-8") as f:
        spec = f.read()
    src_hash = hashlib.sha256(spec.encode("utf-8")).hexdigest()[:12]

    # 组装切片
    slices = []
    core = extract_core(spec)
    slices.append(("core_slice", "恒驻最小核（注入声明+L1·每会话必注）", core, "always"))
    l6 = extract_layer(spec, "L6")
    slices.append(("L6_反向约束", "反向约束层（SHADOW+自我状态·对抗性重注）", l6, "always"))
    for num in ["L2", "L3", "L4", "L5"]:
        txt = extract_layer(spec, num)
        title_m = re.search(rf"^## {num} · (.+)$", txt, re.M)
        title = title_m.group(1) if title_m else num
        trig = DOMAIN_TRIGGERS.get(num, [])
        slices.append((f"{num}_{title.split('（')[0].strip()}", title, txt, "|".join(trig)))

    # 输出
    os.makedirs(args.out, exist_ok=True)
    manifest = {"src": args.spec, "src_hash": src_hash, "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "slices": []}
    total = 0
    for name, desc, content, strat in slices:
        bytes_n = len(content.encode("utf-8"))
        total += bytes_n
        manifest["slices"].append({"name": name, "desc": desc, "bytes": bytes_n, "strategy": strat})
        if not args.dry_run:
            path = os.path.join(args.out, f"{name}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✅ 写入 {path} ({bytes_n}B)")
        else:
            print(f"  [dry] {name} ({bytes_n}B) strat={strat}")

    if not args.dry_run:
        # 待填显形（advisory·⛔不阻断）——骨架的既定设计就是「渐进式，不追求一次填满」。
        #   实测触发原因：模板一个字不填也能产出 6 片切片（core 2KB·仅 2 处占位残留），
        #   用户拿到的其实是「通用底壳」，而系统零信号告诉他「分身还不像他」——这比报错更伤体验
        #   （他会以为已经蒸好了）。这里把剩余占位数与所在层显形，让「再蒸一轮」有可查的靶子
        #   （愿景④越用越了解使用者·前提是先能看见"还没懂到哪"）。
        _ph = []
        for name, _desc, content, _strat in slices:   # 四元组（解包姿势对齐 :115 写入循环）
            c = content.count("【")
            if c:
                _ph.append("%s(%d)" % (name, c))
        if _ph:
            _n = sum(int(x.split("(")[1][:-1]) for x in _ph)
            print("  ⚠️ 待填占位仍存 %d 处 → %s" % (_n, "、".join(_ph)))
            print("     切片可用（内置底线已生效），但「分身像不像你」取决于上面这些格子。")
            print("     想更贴自己：把日记/文案/周报喂给 AI，说「蒸馏规格书」增量补，再重跑本脚本。")
        man_path = os.path.join(args.out, "manifest.json")
        with open(man_path, "w", encoding="utf-8") as f:
            import json
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 写入 manifest.json (src_hash={src_hash})")
    print(f"  切片总数 {len(slices)} · 全量字节 {total} · src_hash={src_hash}")


if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)   # 返回值须落到退出码（缺规格书=2）
