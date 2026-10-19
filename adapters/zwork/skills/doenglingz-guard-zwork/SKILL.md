---
name: doenglingz-guard-zwork
description: >
  布洛陀·童灵（doenglingz）守护三查+接入完整性校验（Zwork 端·AutoClaw 新客户端）。
  当用户提及「守护/三查/8要素/试金石/机制指针/童灵校验/漂移检查/K2/切片新鲜度/规格书同步/
  童灵接入完整性」或童灵落点更新后、规格书变更后、交付前守护时使用。
  场景：AGENTS.md 标记区段刷新后校验、manifest src_hash 变更后检查、D3 回合交付前三查。
  这是 Zwork 端专属适配器——对标 Trae Work doenglingz-guard、豆包办公规则 Skill 的守护（CHECK）面，
  按 Zwork 真实机制（无 Stop 钩子·守护为按需 Skill 软约束+exec 机械判据）落地。
compatibility: zwork
allowed-tools: [Read, Bash, Grep, Glob]
dependencies: []
author: 布洛陀体系（Zwork 端适配）
source: zwork-adapted
upstream: 守护判据真源=数字分身设计哲学 06-跨端适配规范（§2.7 三查）+06 §2.2.0 端清单 JSON
modifiable: true
version: "1.0.0"
license: Proprietary
---

# Zwork 端 · 童灵守护三查（CHECK 层）

> 🔴 **定位**：守护校验层——与 doenglingz-slice-nav-zwork 的装载/激活（LOAD/ACTIVATE）互补：
> 本 Skill 只校验，⛔ 改任何产物。无 Stop 钩子⇒守护为**按需触发**（交付前/刷新后/质疑时）
> + 每回合响应内自检行（软约束·平台边界型达标口径同 §2.7.2.1）。

## 一、三查执行（每查一条机械判据·exec 实跑·禁凭印象）

### 查① 恒驻核标记区段完整（8 要素之 K2 载体）
```bash
grep -c "K2 core_slice 开始\|K2 core_slice 结束\|L6 反向约束 开始\|L6 反向约束 结束" \
  ~/个人AI档案/AutoClaw/AGENTS.md
```
判据：4 行全命中=✅；任一缺失=🔴（标记对断裂·禁手工补写——走生成器单向流水线重部署）。

### 查② 切片新鲜度（manifest src_hash vs 规格书现算）
```bash
python3 - << 'PY'
import json, hashlib, os
spec = os.path.expanduser("~/个人AI档案/数字分身/童灵·人格规格书.md")
man = json.load(open(os.path.expanduser("~/个人AI档案/数字分身/K2切片蒸馏/slices/manifest.json")))
now = hashlib.sha256(open(spec, "rb").read()).hexdigest()[:12]
print("FRESH" if now == man.get("src_hash") else f"STALE now={now} manifest={man.get('src_hash')}")
PY
```
判据：FRESH=✅；STALE=🔴（规格书已改而切片未再蒸馏·报告用户并挂蒸馏调度）。

### 查③ 端实体在场+卡号纪律（五系统文件等价物·对账吸收判据）
```bash
test -f ~/个人AI档案/AutoClaw/SOUL.md && grep -c "把沉淀当资产" ~/个人AI档案/AutoClaw/SOUL.md
grep -c "buluotuo:execution-guidelines-v1" ~/个人AI档案/AutoClaw/AGENTS.md
```
判据：SOUL 命中≥1 且标记对 ≥2=✅。

## 二、8 要素试金石（06 规范 §2.7 口径·Zwork 行逐项）

| 要素 | Zwork 承载 | 判 |
|---|---|---|
| 1 恒驻核在位 | AGENTS.md 标记区段（查①） | 机械 |
| 2 Memory 指针卡 | Run 注入·可答「童灵是什么+规格书在哪」 | 行为抽检 |
| 3 W1 契约兑现 | slice-nav-zwork 仪式三件 | 行为抽检 |
| 4 切片新鲜 | manifest src_hash（查②） | 机械 |
| 5 端实体+纪律 | SOUL/AGENTS 锚点（查③） | 机械 |
| 6 W2 同步 | `数字分身/scripts/last_run_doenglingz_slice_watch.ts` 心跳 | 机械 |
| 7 观测层 | route_endpoints Zwork 行 active | 机械 |
| 8 L7 五通道 | 系统日志/TSL/成长箱通道留痕 | 账本 |

## 三、试金石问题（身份完整性·用户可用）

「童灵是什么（一句话）？」「规格书在哪？」「core_slice 和全量规格书什么关系？」——
答不出或答错=恒驻核失效，🔴 上报。

## 四、TSL 机械产树（§八·七 无钩子端脚本化·构造权归脚本）

D3 上岗回合末·调用端专属校验器并**逐行 relay stdout**（⛔自绘/改层状态/只写指针行）：

```bash
python3 ~/个人AI档案/脚本中心/zwork_tsl_verify.py --window 30
```

- 树恒定归**回复末段**（后验对账·正文评估→TSL树→产出签名→署名）。
- ⚪查不了 2 项（L1/L3）= 平台边界型诚实标注，⛔AI 自填 ✅。
- 脚本缺失时如实输出「TSL 脚本不可用·先跑 setup.sh」，⛔自绘。

## 五、输出契约

三查结果按 `✅/🔴 + 判据值` 逐行报；任一 🔴 → 定位（区段/hash/实体）+ 处置建议
（重部署/再蒸馏/修复实体）+ 显式报告用户。⛔ 谎报全绿（S006 红线）。
