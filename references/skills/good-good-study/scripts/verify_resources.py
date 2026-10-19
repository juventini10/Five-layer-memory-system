#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
good-good-study 资源字段校验脚本（v1.1.8 · 出图必跑·创建v0.8.7）
=====================================================
治"资料出错"三关中的第①关（机器拦截）+ 第③关（留痕检查）：
  - ISBN-10/13 校验位算法（拦随机编造/抄错）
  - 可定位标识检查（ISBN / DOI / 官方域名 / 具名案例，四选一）
  - 违规字眼检查（"任一篇" / "搜" / "百度" / "Google" 等操作指令式）
  - 留痕检查（"已核验" 或 ⚠️ 至少其一，无留痕=未核验）
用法：
  python3 verify_resources.py <路径图.md 或 .html>
退出码：0=全部通过  1=存在缺陷（列出清单）  2=用法/输入异常（路径缺失或不可读·视为未跑，⛔不当作通过）
注意：本脚本是第①关机器拦截。第②关"字段同源核验"（ISBN与书名/出版社/年份
必须来自同一条检索结果）无法纯脚本化，仍需出图时逐条 WebSearch + 留痕——
v0.8.6 三层契约的第②层。脚本防的是"明显编造"，防不了"张冠李戴"。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import re
import sys
from pathlib import Path


# ---------- ISBN 校验位 ----------

def isbn13_check(digits: str) -> bool:
    """ISBN-13 校验位：前12位 奇数位×1 偶数位×3，校验位=(10 - sum%10)%10"""
    if len(digits) != 13:
        return False
    s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:12]))
    return int(digits[12]) == (10 - s % 10) % 10


def isbn10_check(digits: str) -> bool:
    """ISBN-10 校验位：前9位×(10-i)，校验位=sum mod 11（10→X）"""
    if len(digits) != 10:
        return False
    s = sum(int(d) * (10 - i) for i, d in enumerate(digits[:9]))
    # 审查P1-1修复：check ≡ -s (mod 11)——原 `c = s % 11` 判的是 +s（合法0306406152被拒/伪照0306406159放行·双向失准实测）
    c = (11 - s % 11) % 11
    c = 'X' if c == 10 else str(c)
    return digits[9] == c


def check_isbn(raw: str) -> bool | None:
    """返回 True=合法 / False=非法 / None=未含ISBN"""
    # 审查P2-7修复：按连续数字段提取（原全串去分隔符合并——ISBN旁有页数等数字时合并超长→静默None跳过校验）
    # 审查N1修复v2（复核抓到v1连字None仍fail-open）：空格=硬边界、连字符=ISBN内部——
    # 段=数字X与连字符的连续组合，清洗后恰10/13位才检验（其他长度忽略=非ISBN数字串·日期/页数安全）
    candidates = re.findall(r'[\dXx][\dXx-]{8,18}[\dXx]', raw)
    results = []
    for seg in candidates:
        d = re.sub(r'[^0-9X]', '', seg.upper())
        if len(d) not in (10, 13):
            continue
        if len(d) == 13:
            results.append(isbn13_check(d))
        elif len(d) == 10:
            results.append(isbn10_check(d))
    if not results:
        return None
    return all(results)  # v1.1.1 fail-closed：同行任一非法ISBN即判非法（旧any()被合法值掩盖非法值=fail-open·审查P8实证）


# ---------- 可定位标识 / 违规字眼 / 留痕 ----------

# 可定位四选一（v0.8.6）：ISBN / DOI / 官方域名 / 具名企业+案例名
HAS_LOCATOR = [
    r'\d{9}[\dX]',            # ISBN-10/13（裸数字或带连字符）
    r'doi\.org',
    r'https?://',
    r'www\.',
]
# 具名方法论豁免（v0.8.7）：无ISBN的知名框架/模型（如"麦肯锡7S"）——本身即知识对象，
# 豁免"可定位"检查，但仍需留痕交代来源；⛔禁止用宽泛词（"一个模型"）冒充具名方法论
NAMED_METHODOLOGY = r'[\u4e00-\u9fa5A-Za-z0-9]{2,30}(模型|框架|方法论|体系|SOP)'
# 违规字眼（v0.8.1 保留项 + v0.8.6 反例）
BANNED = ['任一篇', '搜', '百度', 'Google一下', 'google一下', '搜一下', '去搜']
# 留痕标记（v0.8.6 第②层/第③层）：已核验 or 明确标⚠️
HAS_TRACE = [r'已核验', r'⚠️', r'【英文原版', r'【影印版']


def extract_resource_lines(text: str):
    """从 md 的 resources: [...] 或 html 的 res: "..." 提取资源条目"""
    lines = []
    # md YAML: resources: ["a", "b"]
    for m in re.finditer(r'resources:\s*\[(.*?)\]', text, re.S):
        inner = m.group(1)
        for item in re.findall(r'"([^"]+)"', inner):
            lines.append(item)
    # html: res: "a + b + c"（书名《...》内的 + 需保护：先替换为占位符再切分）
    for m in re.finditer(r'\bres:\s*"([^"]+)"', text):
        seg = m.group(1)
        # 保护书名号内容
        protected = re.sub(r'《[^》]*》', lambda x: x.group(0).replace('+', '␟'), seg)
        for part in re.split(r'\s\+\s', protected):
            lines.append(part.replace('␟', '+'))
    return [l.strip() for l in lines if l.strip()]


# ---------- 主流程 ----------

def main():
    if len(sys.argv) < 2:
        print('用法: python3 verify_resources.py <路径图.md 或 .html>')
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f'❌ 文件不存在: {path}')
        sys.exit(2)
    text = path.read_text(encoding='utf-8')

    items = extract_resource_lines(text)
    if not items:
        print('⚠️ 未提取到资源条目——v0.13.2 收紧：快速层与深度层均须≥1条资源（见 learning-map-schema resources 字段）；若应填而未提取则检查文件格式（md: resources:[...] / html: res:"..."）')
        sys.exit(1)

    problems = []
    for i, item in enumerate(items, 1):
        # 1. ISBN 校验位
        isbn_status = check_isbn(item)
        if isbn_status is False:
            problems.append(f'[条目{i}] ISBN 校验位非法: {item}')
        # 2. 可定位标识（至少命中一种；具名方法论如"麦肯锡7S模型"可豁免——本身即知识对象）
        has_loc = any(re.search(p, item) for p in HAS_LOCATOR)
        has_book = '《' in item  # 书名号也算可定位锚点（配合第②关同源核验）
        is_named_meth = bool(re.search(NAMED_METHODOLOGY, item))
        if not (has_loc or has_book or is_named_meth):
            problems.append(f'[条目{i}] 无可定位标识（ISBN/DOI/域名/案例名/书名/具名方法论都无）: {item}')
        # 3. 违规字眼
        for b in BANNED:
            if b in item:
                problems.append(f'[条目{i}] 违规字眼「{b}」: {item}')
                break
        # 4. 留痕（v0.8.6：有"已核验"或⚠️或【英文原版/影印版标注 才算有交代）
        has_trace = any(re.search(p, item) for p in HAS_TRACE)
        if not has_trace:
            problems.append(f'[条目{i}] 无核验留痕（缺"已核验"/⚠️/版次标注）: {item}')

    print(f'共扫描资源条目: {len(items)}')
    if problems:
        print(f'❌ 发现 {len(problems)} 处问题:')
        for p in problems:
            print('  ' + p)
        sys.exit(1)
    else:
        print('✅ 全部通过（ISBN校验位/可定位标识/无违规字眼/核验留痕）')
        sys.exit(0)


if __name__ == '__main__':
    main()
