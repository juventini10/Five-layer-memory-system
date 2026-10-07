---
name: doenglingz-guard
description: >
  布洛陀·童灵（doenglingz）守护三查（Trae Work 端）。当用户提及"守护、三查、8要素、试金石、机制指针、童灵校验、
  漂移检查、K2、切片新鲜度、规格书同步、童灵接入、童灵完整性"或需要验证童灵接入完整性时使用。
  场景：童灵落点（doenglingz-core.md）更新后校验、规格书变更后检查嵌入同步、会话启动时三查验证、产出交付前守护。
  这是 Trae Work 端专属适配器——对标 TeleAgent/豆包办公端的守卫管道，
  按 Trae Work 真实机制（alwaysApply 规则目录常驻注入·无 Stop 钩子）适配。
compatibility: trae-work, catpaw
allowed-tools: [Read, Write, Bash, Grep, Glob]
dependencies: []
author: 布洛陀体系（Trae Work 端适配 · CatPaw 端适配 2026-09-06）
source: trae-work-adapted · catpaw-adapted-2026-09-06
upstream: [记忆共享中心]/技能配置/（布洛陀 Skill 真源·本端专属不回流）
modifiable: true
version: "1.0.0"
license: Proprietary
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'aea4a1f8-8882-4570-abf2-ca756a007e0f'
  PropagateID: 'aea4a1f8-8882-4570-abf2-ca756a007e0f'
  ReservedCode1: 'b01b2de1-1259-4722-84da-a41d367d48db'
  ReservedCode2: 'b01b2de1-1259-4722-84da-a41d367d48db'
---

# Trae Work 端 · 童灵守护三查

> 🔴 **定位**：本 Skill 是 Trae Work 端童灵的**守护校验层（CHECK）**——承载 3 守卫适配，与「布洛陀-豆包办公规则」/「TeleAgent doenglingz-guard」同构但按 Trae Work 真实机制落地。
> 🔴 **触发**：任何涉及童灵接入/校验/漂移检查的任务前自动加载；会话时三查验证。
> ⛔ **边界**：本 Skill 只做**校验与报告**，⛔不修改规格书/USER_payload/doenglingz-core.md/切片产物（改动作业走 `k2_slice_generator.py` 单向流水线）。

---

## 一、守护三查（Trae Work 端适配）

> Trae Work 无 Stop/UserPromptSubmit 钩子——守护走 **alwaysApply 规则目录常驻注入**（`~/.trae-cn/user_rules/`）+ **Skill 手动触发兜底**，软约束（🟡非机械执行），靠 Skill 触发 + 品格倾向兜底。此为能力面诚实标注，不假装电路级强制。

### 查1：8要素校验（注入态完整性）

**职责**：校验童灵落点 `~/.trae-cn/user_rules/doenglingz-core.md` 是否含 8 要素，防止 K2 切片嵌入残缺或漂移。

**8要素清单**（核心机制逐项检查，位置按 doenglingz-core.md 结构）：

| # | 要素 | doenglingz-core.md 位置 | 通过条件 |
|---|------|----------------------|---------|
| 1 | 运行时注入声明 | 恒驻核 core_slice 首段 | 含愿景四方向/三问判据/红线 |
| 2 | 品格行为底色 | 二·五段 | 含 10 条品格 + 试金石标注 |
| 3 | 非职能域应答纪律 | 三段 | 三步式 + 反漂移条款 |
| 4 | 零问题交付红线 | 四段 | 硬红线 4 条 + 门禁 G1-G4 + 绿灯授权 |
| 5 | 域切片指针 | 文件头 🧭 域切片按需加载 | 含"不常驻" + `doenglingz-slice-nav` 按需 Read 声明（K2 双层结构） |
| 6 | L1 身份骨架 | L1 节 | 系统身份/金句/实事求是/核心身份/品格 10 条 |
| 7 | L6 反向约束 | 恒驻核 L6 节 | 用户行为模式 + 分身自我状态感知 |
| 8 | Trae Work 边界声明 | 文件头实体边界 | 童灵≠本端AI 边界明确 |

> ⚠️ **要素5 口径订正（2026-10-03）**：旧版列「机制登记指针」（`gate_runner.py` + CHANGELOG）——**与生成器设计冲突**：`k2_slice_generator.py::extract_core` 明示**跳过 `## 🔧 机制登记（指针）`**（2026-09-11 恒驻核瘦身：纯导航指针按 trigger 簇按需 Read，不进常驻核）。故 core 内**本就不该有**机制登记 ⇒ 旧检查恒 RED（假红）。改判为「🧭 域切片按需加载」指针——它才是双层结构的功能性锚点（缺它 AI 不知 L2-L5 需按需载）。机制登记本体仍在规格书 §🔧 与 `数字分身/CHANGELOG.md`，按需 Read。

**校验方法**：`grep -c` 逐项计数（含"愿景""四方向""红线""域切片按需加载""品格""反向约束层""实体边界"等锚点行）→ 全 GREEN 才交付；任一 RED 阻断并显式报告。
> ⚠️ 锚点串须与实际标题逐字对齐：L6 标题为 `## L6 · 反向约束层（SHADOW+自我状态感知）`——用 `L6 反向约束层`（空格版）**恒 0 命中（假红）**，须用 `反向约束层`（2026-10-03 实测）。

### 查2：试金石校验（真分身不是应声虫）

**职责**：验证童灵是**真分身**不是应声虫——机制指针/反漂移/路由命中审计。

**试金石清单**：
| 试金石 | 通过条件 |
|--------|---------|
| **真分身试金石** | 童灵敢于温和指出用户言行不一致，不盲从（L1 §1.5 试金石标注在位） |
| **反漂移条款** | 童灵段来自 K2 切片逐字嵌入（src_hash 由下方命令动态读 manifest 校验·⛔不写字面值），⛔禁止手抄增删 |
| **单一真源声明** | doenglingz-core.md 文件头含"重跑生成器后整段替换"声明，禁端侧改写 |
| **门禁控制面** | 零问题门禁 G1-G4 全 GREEN 才交付；任一 RED 显式报告 |
| **机制指针** | 机制说明/判据溯源在 `数字分身/CHANGELOG.md`，不占常驻上下文 |
| **路由命中** | 触发词命中 triwich 走 L1/L2/L3 协议；未命中走三步思考 |

### 查3：切片新鲜度校验（单向流水线未漂移）

**职责**：验证规格书 → 切片 → doenglingz-core.md 嵌入单向流水线未漂移。

**校验方法**（机械可验）：

```bash
# ① 规格书 vs manifest src_hash
env -u PYTHONHOME -u PYTHONPATH python3 -c "import hashlib,json;h=hashlib.sha256(open('[记忆共享中心]/数字分身/童灵·人格规格书.md',encoding='utf-8').read().encode()).hexdigest()[:12];m=json.load(open('[记忆共享中心]/数字分身/K2切片蒸馏/slices/manifest.json'))['src_hash'];print('FRESH' if h==m else 'DRIFT spec='+h+' manifest='+m)"  # 应为 FRESH（无字面 hash·规格书一变不腐烂）
rg src_hash "[记忆共享中心]/数字分身/K2切片蒸馏/slices/manifest.json"

# ② doenglingz-core.md 是否逐字包含 core_slice + L6
env -u PYTHONHOME -u PYTHONPATH python3 - <<'EOF'
import hashlib
with open('$HOME/.trae-cn/user_rules/doenglingz-core.md', encoding='utf-8') as f:
    tgt = f.read()
norm = lambda s: {l.strip() for l in s.splitlines() if l.strip()}
for name in ['core_slice', 'L6_反向约束']:
    with open(f'[记忆共享中心]/数字分身/K2切片蒸馏/slices/{name}.md', encoding='utf-8') as f:
        seg = f.read()
    missing = norm(seg) - norm(tgt)
    print(f'{name}:', '✅ 逐字包含' if not missing else f'❌ 漂移 {len(missing)}行: {list(missing)[:5]}')
EOF
```

**通过条件**：src_hash 一致 + 两段均逐字包含 → GREEN；任一失败 → RED，提醒重跑 `k2_slice_generator.py` 并同步 doenglingz-core.md 嵌入。

---

## 二、执行工作流

1. **识别触发**：任务是否涉及童灵接入/校验/漂移检查 → 是则进入 2
2. **跑三查**：按 查1 → 查2 → 查3 顺序执行（查3 用 Bash 机械校验）
3. **结果汇总**：
   - 全 GREEN → 报告通过（附 src_hash 与各段字节）
   - 任一 RED → 显式报告漂移项 + 建议动作（重跑生成器/重新嵌入/更新边界声明），**不静默修复**
4. **交付**：报告校验结论 + 是否需人工介入

---

## 三、与相关机制的边界

| 机制 | 归属 | 本 Skill 关系 |
|------|------|--------------|
| `k2_slice_generator.py` | 规格书→切片单向流水线 | 校验对象，不替代 |
| `doenglingz_slice_watch.py` | 切片漂移守望（W2 质检·规格书变更自动重部署） | 机械副作用兜底，本 Skill 手动校验互补 |
| `布洛陀-豆包办公规则` | 豆包端守卫 | 同构不同端，不混淆 |
| `TeleAgent doenglingz-guard` | TeleAgent 端守卫 | 同构不同端，落点不同（本端=user_rules/doenglingz-core.md） |
| `童灵·人格规格书.md` | SSOT | 校验真源，不修改 |

---

版本：v1.0.0 | 更新：2026-09-01 | 来源：童灵·人格规格书.md（SSOT）+ K2切片蒸馏 + Trae Work 机制实证（alwaysApply 常驻注入·无 Stop 钩子）