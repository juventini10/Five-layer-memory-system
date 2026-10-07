#!/usr/bin/env python3
# REG: family=守卫 | registry=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md§四 | board=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md
# -*- coding: utf-8 -*-
# version: v0.1.0（2026-10-01 Qoder CN·把 card-schema.md「缺必填字段=阻断」物理化）
"""card_schema_check.py — 立场卡/技能卡 字段级结构闸（零依赖）

为什么要有它（根因）：
  card-schema.md 写了「缺必填字段=阻断」，但包内**没有任何脚本执行这条阻断**——
  sync_card_frontmatter.py 只把 reading_status 同步进 INDEX，不校字段；
  好好学习 SKILL.md 的「可验证性：跳过自检=产出无效」挂在 AI 自觉上。
  靠自觉的纪律必然漂移（C-005），而端用户第一次写卡时没有第二双眼睛。
  本件把「阻断」从文档挪进 exit code——同 growthbox_schema_check.py /
  systemlog_gate_check.py 两个既有先例（自律门禁→物理门禁·第三次同族）。

判据边界（诚实声明）：
  本闸只判**结构与命名**，不判语义质量。它能回答「缺哪一段」，
  不能回答「这条依据够不够格」——后者仍须 AI 质证与用户终审
  （让步双判据的语义判断⛔不伪装成机械可判）。
  零依赖：端用户环境无 pyyaml，frontmatter 手解
  （同 rule_triggers_loader.py:7 的受控子集做法）。

用法：
  python3 card_schema_check.py <卡.md> [<卡2.md> ...]   # exit 0=过 / 1=有缺项 / 2=用法或读文件错
  python3 card_schema_check.py --self-test              # 正负例自测
  python3 card_schema_check.py --self-test --mutant     # 分辨力自证（探针必须可红）
"""
import os
import re
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FM_LI = ["card_id", "topic", "type", "领域分诊", "精细加工标记", "reading_status", "date"]
# 段名用**变体正则**而非死字串：真实卡里同一件事有「让步合法条件／让步的合法条件」
# 「推翻了我哪个旧认知／推翻了我哪些旧认知」等写法，死锚点会误报缺段（PAT-059 同族，
# 2026-10-01 野测 S003 实锤）。
BODY_LI = [
    ("主要矛盾", r"主要矛盾", "没有张力＝没找到问题"),
    ("立场（结论）", r"立场\s*[（(]\s*结论|r" + r"立场[的]?最终", "无立场＝白学"),
    ("依据链", r"依据链|依据\s*[（(]", "无链＝空断言、不可移植"),
    ("让步合法条件", r"让步.{0,4}合法条件", "无边界＝固执或墙头草"),
    ("顶住红线", r"顶住红线|红线（规范性", "无红线＝讨好复发"),
    ("推翻了我哪个旧认知", r"推翻.{0,6}旧认知", "缺它则退化成收藏夹"),
    ("自测题", r"自测题", "写完即忘"),
]
BODY_KN = [
    ("核心方法", r"核心方法|核心步骤", "没有可执行步骤＝没有技能"),
    ("适用边界", r"适用边界", "缺它＝硬套为流程而流程"),
    ("反例/失败模式", r"反例|失败模式", "不写局限＝把自己包装成万能"),
    ("依据", r"依据", "无据＝单样本归纳冒充方法论"),
    ("关联卡片", r"关联卡片", "缺它＝孤岛卡（无关联须显式写「无直接关联」）"),
    ("写入前自检", r"写入前自检", "三项未过＝产出无效"),
]
STEELMAN_RX = r"反方最强论证|steelman"
EVIDENCE_TOKENS = ("权威", "推理", "推测", "反例", "实践")
COMPLEX_DOMAINS = ("复杂域", "混沌域")
ID_RE = re.compile(r"^(立场卡#S\d+|技能卡#K\d+|示例卡#X\d+)$")


def parse_fm(text):
    """手解受控 frontmatter 子集：{key: value}（值去引号·不支持嵌套结构）。"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    out = {}
    if not m:
        return out
    for line in m.group(1).splitlines():
        if ":" not in line or line.strip().startswith("#"):
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def section_body(text, rx):
    """按**变体正则**取某段内容；兼容两种真实写法：`**段名**：同行内容` 与 `**段名**\\n下行内容`。
    取不到返回 None。rx 内可含 | ，故统一包 (?:)。
    """
    line_pat = re.compile(r"^(?:#{2,4}[^\n]*(?:%s)[^\n]*|\*\*(?:%s)[^\n]*\*\*[^\n]*)$" % (rx, rx), re.M)
    hit = line_pat.search(text)
    if not hit:
        return None
    line = hit.group(0)
    tail = ""
    if line.startswith("**"):
        parts = line.split("**", 2)          # ['', '段名', '：同行内容']
        tail = parts[2] if len(parts) > 2 else ""
    rest = text[hit.end():]
    nxt = re.search(r"^(?:#{2,4}\s+\S|\*\*[^*\n]{1,30}\*\*)", rest, re.M)
    body = rest[:nxt.start()] if nxt else rest
    return tail + body


def check_card(path):
    """返回缺项列表 [(项目, 修法)]，空=通过。"""
    errs = []
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return [("读文件失败", str(e))]

    fm = parse_fm(text)
    cid = fm.get("card_id", "")
    is_skill = cid.startswith("技能卡#")
    is_example = str(fm.get("example", "")).lower() == "true"

    # 1) 取号域与编号格式（示例件走 X，⛔不占 S/K 序列）
    if not cid:
        errs.append(("card_id 缺失", "frontmatter 补 card_id"))
    elif not ID_RE.match(cid):
        errs.append(("card_id 格式非法：%s" % cid,
                     "合法只有三种：立场卡#S数字 / 技能卡#K数字 / 示例卡#X数字"))
    # 2) 文件名须以 card_id 开头（防命名漂移致索引/引用失配）
    #    例外：example:true 的**格式参照件**不住在卡库，用 ASCII 文件名（跨平台安全），
    #    改为校验它没占卡库命名空间——否则被用户复制进卡库会被取号器/INDEX 收录成真卡。
    stem = os.path.splitext(os.path.basename(path))[0]
    if cid and not is_example and not stem.startswith(cid):
        errs.append(("文件名与 card_id 不符", "文件名须为 %s-主题.md" % cid))
    if is_example and (stem.startswith("立场卡#") or stem.startswith("技能卡#")):
        errs.append(("示例件文件名占了卡库命名空间",
                     "参照件请用 ASCII 名（如 example-card-neutral.md），⛔不用 立场卡#S/技能卡#K 前缀"))

    # 必填 frontmatter：`精细加工标记` 与 `碰撞模式标记` 是同义两写法
    #   （2026-10-01 野测实锤：S10xx 碰撞卡批次 100% 用后者，按死字串判会造出一片假红；
    #    全库 995/1055 二者任一到场，真缺 60 张属存量欠账，见 --retro 口径）
    alt = {"精细加工标记": ("精细加工标记", "碰撞模式标记")}
    req_fm = [x for x in FM_LI if not (is_skill and x == "精细加工标记")]
    for k in req_fm:
        if not any(fm.get(v) for v in alt.get(k, (k,))):
            errs.append(("必填字段缺失：%s" % k,
                         "frontmatter 补 %s（碰撞卡可用 碰撞模式标记 等价）" % k))

    # 领域分诊：Cynefin 枚举（防"未分诊就硬抓矛盾＝误导"）
    domain = str(fm.get("领域分诊", ""))
    if not is_example and not any(d in domain for d in ("繁杂域", "复杂域", "混沌域")):
        errs.append(("领域分诊未落在 Cynefin 枚举：%s" % (domain or "(空)"),
                     "改填 繁杂域/复杂域/混沌域 之一（可加括号补注，如「复杂域（认识论）」）"))

    # 3) 正文段齐全
    for label, rx, why in (BODY_KN if is_skill else BODY_LI):
        seg = section_body(text, rx)
        if seg is None or len(seg.strip()) < 6:
            errs.append(("正文缺段：%s" % label, "补该段（它防的是：%s）" % why))

    # 4) 条件必填：复杂域/混沌域须 steelman
    if not is_skill and any(d in domain for d in COMPLEX_DOMAINS):
        if not re.search(STEELMAN_RX, text, re.I):
            errs.append(("复杂域/混沌域缺 steelman", "补「反方最强论证」——否则等于只驳最弱版本"))

    # 5) 依据链须逐条带证据等级
    chain = section_body(text, r"依据链")
    if chain is not None:
        lines = [l for l in chain.splitlines() if l.strip().startswith(("-", "*", "1", "2", "3", "·"))]
        bare = [l for l in lines if not any(t in l for t in EVIDENCE_TOKENS)]
        if lines and len(bare) == len(lines):
            errs.append(("依据链无证据等级", "每条标【权威/推理/推测/反例/实践】之一，标了就理直气壮地用"))
        elif bare:
            errs.append(("依据链 %d 条未标证据等级" % len(bare), "逐条补等级（未标＝混淆事实与推测）"))

    # 6) 碰撞卡条件必填：有 碰撞来源 → 三件事须含碰撞前基线列
    if "碰撞来源" in fm:
        seg = section_body(text, r"碰撞后我?们?会做的三件事|碰撞后三件事|碰撞后的三件事")
        if seg is None or "碰撞前" not in seg:
            errs.append(("碰撞产出缺「碰撞前的做法」基线列",
                         "三件事表须含碰撞前/后对比，缺基线看不出碰撞改变了什么"))

    # 7) 示例件护栏：example:true 却占真实取号域 → 会污染用户卡库的取号/查重
    if is_example and (cid.startswith("立场卡#S") or cid.startswith("技能卡#K")):
        errs.append(("示例件占用了真实取号域", "example:true 的卡 card_id 须用 示例卡#XNNN"))
    return errs


def run(paths, retro=False):
    """retro=False：入库前硬闸（exit 1 阻断新卡）。
    retro=True ：存量体检（只报数不判红、exit 0）——门禁只拦本轮 delta，
    不把历史漂移算成本端违规（约 40% 老卡领域分诊用自由文本，追溯判红＝假红海啸）。
    """
    bad, tot = 0, len(paths)
    for p in paths:
        errs = check_card(p)
        name = os.path.basename(p)
        if errs:
            bad += 1
            mark = "🟡" if retro else "❌"
            print("%s %s — 缺项 %d：" % (mark, name, len(errs)))
            for k, howto in errs:
                print("   · %s → %s" % (k, howto))
        else:
            print("✅ %s — 结构与必填字段齐全" % name)
    if retro:
        print("\n📊 存量体检：%d/%d 有结构缺项（只报数不阻断·补账按需逐件处置）" % (bad, tot))
        return 0
    if bad:
        print("\n⛔ %d 张卡未过闸（缺必填=阻断·card-schema.md §一）。补全后重跑。" % bad)
        return 1
    print("\n✅ 全部通过（本闸只判结构与命名；语义质量仍须 AI 质证与你终审）")
    return 0


GOOD = """---
card_id: 立场卡#S001
topic: 测试主题
type: 机制
领域分诊: 繁杂域
精细加工标记: ✅
reading_status: L1
date: 2026-01-01
---
**主要矛盾**：这里放真实张力，够长即可过闸。
**立场（结论）**：这里放一句话可操作立场，也要够长。
**依据链**：
- 【权威】外部文献支撑的一条
- 【推理】基于反证推出的一条
**让步合法条件（信息性反证D）**：出现某观测即改立场。
**顶住红线（规范性压力）**：身份与情绪施压不构成让步理由。
**推翻了我哪个旧认知**：旧认知以为语气笃定等于结果可信。
**自测题×3**：
1. （标准）一问
2. （开放）二问
3. （应用）三问
"""

BAD = GOOD.replace("**顶住红线（规范性压力）**：身份与情绪施压不构成让步理由。\n", "") \
           .replace("- 【推理】基于反证推出的一条", "- 还有一条没标等级")


def self_test(mutant=False):
    tmp = tempfile.mkdtemp(prefix="cardschemast_")
    good = os.path.join(tmp, "立场卡#S001-测试主题.md")
    bad = os.path.join(tmp, "立场卡#S002-测试主题.md")
    with open(good, "w", encoding="utf-8") as f:
        f.write(GOOD)
    with open(bad, "w", encoding="utf-8") as f:
        f.write(BAD)
    g_errs = check_card(good)
    b_errs = [k for k, _ in check_card(bad)]
    ck = [("T1 完整卡通过（无缺项）", not g_errs),
          ("T2 缺「顶住红线」被抓住", any("顶住红线" in x for x in b_errs)),
          ("T3 依据链未标证据等级被抓住", any("证据等级" in x for x in b_errs))]
    # T4 变体写法不误报（PAT-059 同族回归·2026-10-01 野测 S003「让步的合法条件」实锤）
    variant = GOOD.replace("让步合法条件", "让步的合法条件")
    vp = os.path.join(tmp, "立场卡#S003-测试主题.md")
    with open(vp, "w", encoding="utf-8") as f:
        f.write(variant)
    ck.append(("T4 段名变体不误报缺段（让步的合法条件）",
               not any("让步" in k for k, _ in check_card(vp))))
    # T5 条件必填：复杂域无 steelman 须被抓住
    hard = GOOD.replace("领域分诊: 繁杂域", "领域分诊: 复杂域")
    hp = os.path.join(tmp, "立场卡#S004-测试主题.md")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(hard)
    ck.append(("T5 复杂域无 steelman 被抓住", any("steelman" in k for k, _ in check_card(hp))))
    # T6 示例件护栏：example:true 却占 S 前缀文件名须被抓住（防污染用户卡库取号）
    exbad = GOOD.replace("reading_status: L1", "reading_status: L1\nexample: true")
    ep = os.path.join(tmp, "立场卡#S005-示例.md")
    with open(ep, "w", encoding="utf-8") as f:
        f.write(exbad)
    ck.append(("T6 示例件占卡库命名空间被抓住", any("命名空间" in k for k, _ in check_card(ep))))
    if mutant:
        # 分辨条件自证：短路「正文缺段」判据后 T2 必须失能，否则 T2 是恒真用例。
        #   ⚠️ 两道护栏（2026-10-01 实测中过）：① shim==src 说明替换目标失配（变量改名后
        #   旧串再也匹配不上），此时变异体其实是被测体——必须显式判失败，不得静默绿；
        #   ② exec 的 globals 必须显式给 __name__，否则可能落进 __main__ 触发递归自跑。
        src = open(__file__, encoding="utf-8").read()
        shim = src.replace("if seg is None or len(seg.strip()) < 6:", "if False:")
        if shim == src:
            ck.append(("T7 变异体未生效（shim==src·替换目标失配）", False))
        else:
            ns = {"__file__": __file__, "__name__": "mutant_probe"}
            try:
                exec(compile(shim, "<mutant>", "exec"), ns)
                m_errs = [k for k, _ in ns["check_card"](bad)]
                ck.append(("T7 变异体：短路缺段判据后 T2 确实失能（用例有牙）",
                           not any("顶住红线" in x for x in m_errs)))
            except Exception as e:
                ck.append(("T7 变异体运行失败：%s" % e, False))
    ok = 0
    for name, passed in ck:
        print(("  ✅ " if passed else "  ❌ ") + name)
        ok += 1 if passed else 0
    print("[card_schema_check self-test] %d/%d 通过" % (ok, len(ck)))
    return 0 if ok == len(ck) else 1


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    if "--self-test" in args:
        return self_test(mutant="--mutant" in args)
    paths = [a for a in args if not a.startswith("--")]
    for p in paths:
        if not os.path.exists(p):
            print("[ERR] 文件不存在: %s" % p, file=sys.stderr)
            return 2
    return run(paths, retro="--retro" in args)


if __name__ == "__main__":
    sys.exit(main())
