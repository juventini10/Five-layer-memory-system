# 评估增强框架 — Clock Loop v2.2.0

> **用途**：SKILL.md阶段2自查环节的增强模块，从"对照用户检查清单"升级为"专业规范矩阵+知识网络+哲学维度"的多维评分
> **加载时机**：阶段2自查环节启动时Read本文件
> **数据源**：`~/个人AI档案/评估知识库/` + `references/triwich-integration.md` + `references/philosophical-evaluation.md`
> **v2.2.0变更**：权重调整（哲学15%↓/逻辑一致性20%↑）+ 哲学及格判定 + 维度去重 + 运行时验证项 + 类型微调 + 触顶判定

---

## Phase 0：知识网络构建（阶段1之后、阶段2之前）

### 对象识别

| 判定条件 | 对象类型 | 评估模式 |
|---------|---------|---------|
| 目录下有SKILL.md | skill | skill_patterns.yaml |
| 目录下有package.json | package | general_evaluation |
| 目录下有README.md + .git | project | general_evaluation |
| 其他 | unknown | general_evaluation（降级） |

### Skill类型检测（v2.2.0新增 P1-2）

```
检测SKILL.md内容特征：
  含"阶段/Phase/步骤流程+执行+自查+审查" → workflow型
  含"对话回合+语境理解+情感响应" → dialog型
  含"加载/注入/初始化" → loader型

类型确定后，从current_weights.yaml读取type_adjustment，对基础权重做±微调
微调后权重归一化（确保总和=100%）
```

### 知识加载流程

```
1. 识别对象类型
2. Read ~/个人AI档案/评估知识库/patterns/{对象类型}_patterns.yaml
   ├─ 文件存在 → 加载对应模式
   └─ 文件不存在 → 降级为 general_evaluation
3. Read ~/个人AI档案/评估知识库/weights/current_weights.yaml
   ├─ 提取 default_weights.{对象类型}
   ├─ v2.2.0: 提取 type_adjustment.{检测到的类型} → 应用微调 → 归一化
   └─ ⛔ adaptive_rules 已废弃（v2.1.2），不再走自适应分支
4. Read ~/个人AI档案/评估知识库/references/second_brain_links.yaml
   ├─ 评估知识库支撑足够 → 跳过
   └─ 支撑不足 → 按references指向加载规范文档
5. 版本检查（固化引用同步验证，4个固化文件）
   ├─ references/triwich-integration.md vs triwich SKILL.md → 不一致⚠️告警
   ├─ references/philosophical-evaluation.md vs meta-aletheia SKILL.md → 不一致⚠️告警
   ├─ references/skill-arch-standard.md vs Skill架构规范.md → 不一致⚠️告警
   └─ references/instruction-standard.md vs 指令编写规范.md → 不一致⚠️告警
   所有版本检查失败=⚠️告警不阻塞，按本地固化版本执行
```

### 🔌 熔断器
- 成功=patterns文件加载返回非空 | 失败=降级为general_evaluation | 重试=0
- 成功=weights文件加载返回非空 | 失败=使用默认权重（等分） | 重试=0
- 版本检查失败=⚠️告警不阻塞，按本地固化版本执行

---

## Phase 1：多维度评分（阶段2自查环节升级）

### 评分流程

```
L1拆解（评分前，Read references/triwich-integration.md） →
  回答四问：核心功能/依赖/输出/核心矛盾
  拆解结果写入评分表前言
  →
逐维度评分 →
  对每个维度：
    1. 读取该维度的 check_items
    2. 逐项核对产出物（不是凭感觉打分）
    3. 每项标注 ✅通过/❌未通过/⚠️部分通过
    4. 维度得分 = 通过项数 / 总项数
  →
加权汇总 →
  总分 = Σ(维度得分 × 归一化后权重)
  →
哲学评估嵌入（对象类型为skill时，Read references/philosophical-evaluation.md） →
  v2.2.0及格判定：总分≥85%→哲学及格(满分计入)；<85%→不及格(零分计入)
  →
L2自检（评分后，Read references/triwich-integration.md） →
  锚点对立面/证据链完整性/假设验证/结论块门禁锁
  →
输出评分表
```

### 评分输出格式

```markdown
### 📊 多维度评分表

### 🔍 L1 拆解（评分前）
- 核心功能：[一句话]
- 依赖：[前置条件列表]
- 输出：[产出物列表]
- 核心矛盾：[一句话]

### 📐 类型检测（v2.2.0新增）
- 检测类型：[workflow/dialog/loader]
- 权重微调：[具体调整项]
- 归一化后权重：[最终权重表]

| 维度 | 权重 | 通过/总数 | 得分 | 依据 |
|------|:---:|:---:|:---:|------|
| 开发规范符合度 | 0.30 | 3/4 | 75% | SKILL.md YAML完整✅ / trigger一致✅ / 产出物锁✅ / 熔断器缺失❌ |
| 指令准确性 | 0.15 | 3/3 | 100% | trigger精确匹配✅ / 五级标注✅ / 语义完整✅ |
| 逻辑一致性 | 0.20 | 4/5 | 80% | 端到端链路✅ / 条件分支✅ / IO定义✅ / 无矛盾✅ / 运行时验证❌ |
| ... | ... | ... | ... | ... |
| 哲学评估 | 0.15 | 及格/不及格 | 100%/0% | 七项检查总分≥85%→及格 |
| **总分** | 1.00 | — | **82%** | — |

### 一致性检查
- 开发规范 vs 指令规范：✅无冲突 / ❌[具体冲突]

### L2自检签名：✅/❌

### 📏 触顶判定（v2.2.0新增）
- 维度饱和度：[N/6] → [触顶/未触顶]
- 剩余可修复空间比率：[X%] → [触顶/未触顶]
- 功能侧vs文档侧空间比：[X:Y] → [建议追分方向]

### 改进建议
1. [高优先] 补充熔断器机制（开发规范符合度-25%）
2. [中优先] ...
```

### 评分门禁

| 总分 | 状态 | 动作 |
|:---:|:---:|------|
| ≥85% | ✅通过 | 自查通过，进入子Agent审查 |
| 70-84% | 🟡部分通过 | 记录未通过项→修正→重评（内部循环） |
| <70% | ❌不通过 | 记录→跳子Agent审查（由子Agent判断是否可接受） |

---

## Phase 2：哲学评估嵌入

> **固化引用**：Read `references/philosophical-evaluation.md`
> **来源**：meta-aletheia v3.2.1
> **引用模式**：固化引用——clock-loop直接读本地references执行，不调用meta-aletheia Skill

### 执行规则（v2.2.0修订）

- ✅DO：哲学评估仅在对象类型为skill时激活
- ✅DO：v2.2.0及格判定——七项哲学检查总分≥85%→该维度按权重满分计入；<85%→按零分计入。不再逐项加分，消除虚假区分度
- ☑SHOULD：非skill对象使用general_evaluation中的简化哲学维度
- ⛔DO NOT：自行定义哲学立场——哲学评估标准来自references/philosophical-evaluation.md固化的meta-aletheia定义

---

## Phase 3：三明智嵌入

> **固化引用**：Read `references/triwich-integration.md`
> **来源**：triwich v3.3.1
> **引用模式**：固化引用——clock-loop直接读本地references执行，不调用triwich Skill

### 三层级嵌入

| 三明智层级 | 嵌入阶段 | 具体作用 | references文件 |
|:----------|:---------|:---------|:--------------|
| L1第一性原理 | 评分前 | 四问拆解（核心功能/依赖/输出/核心矛盾） | triwich-integration.md |
| L2批判验证 | 评分后自检 | 四项自检（锚点/证据链/假设/门禁锁） | triwich-integration.md |
| L3抽象建模 | 跨周期沉淀 | 从多次评估中提取模式（达5的倍数后激活） | triwich-integration.md |

### 执行规则

- ✅DO：L1拆解在Phase 1评分前执行——Read references/triwich-integration.md的L1段
- ✅DO：L2自检在Phase 1评分后执行——Read references/triwich-integration.md的L2段
- 🔴 MUST（交付门禁·见SKILL.md 阶段4「收尾门禁」）：L3沉淀在评估报告数达5的倍数（5/10/15…）时触发
- 🔴 MUST（交付门禁·下游闭环）：L3沉淀生成后**立即执行「反哺派生」**——L1低风险检查项（单一数字源/被引用文件存在性/结构画像防回声）自动写入Phase X验证⑩⑪⑫；L2高风险（动具体Skill）产挂起待办主动列。不靠对话触发，不靠用户提醒（用户2026-07-08指正：沉淀须闭环应用才非死仓库）
- ⛔DO NOT：自行定义三明智方法论——方法论定义来自references/triwich-integration.md固化的triwich v3.3.1定义

---

## 数据沉淀条件

```yaml
persist_conditions:
  confidence_high:
    threshold: 0.8
    condition: "覆盖维度 > 5"
    target: "评估知识库/test_results/"  # 归档评估报告
  confidence_medium:
    threshold: 0.6
    target: "会话缓存"      # 临时存储，7天后清理
  confidence_low:
    target: "丢弃"
```

---

> 版本：v1.3 | 日期：2026-07-04 | 变更：v2.2.0权重同步+哲学及格判定+类型微调+触顶判定+维度去重
