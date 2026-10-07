> **来源**：外置自 SKILL.md（2026-09-04 重构·渐进式加载第三级·原文机械搬运未改一字·⛔本处不写版本号·以 SKILL.md frontmatter 为唯一真相源＝#142防漂移）
> **加载时机**：阶段1标准确认后Read（知识网络构建+版本核对）
> **返回导航**：SKILL.md §执行流程骨架 / §references目录索引

---

### 阶段1.5:知识网络构建(v2.0新增, v2.6.0新增版本核对)

📦 产出物:对象类型 + 评估模式 + 权重配置 + 知识网络加载确认 + 固化引用版本核对结果

**详细流程见** `references/evaluation-framework.md`(Phase 0段)

```
1. 识别对象类型(skill/package/project/unknown)
   ├─ 目录下有SKILL.md → skill → skill_patterns.yaml
   └─ 其他 → general_evaluation(降级)

2. 加载评估知识库
   ├─ Read references/eval-knowledge/patterns/{对象类型}_patterns.yaml
   ├─ Read references/eval-knowledge/weights/current_weights.yaml
   └─ 支撑不足 → Read references/eval-knowledge/second_brain_links.yaml 按指向加载规范文档

3. 固化引用版本核对(v2.6.0新增·防滞后机制·v2.8.3源侧闭环)
   ├─ 逐个读references/下带source_skill/source字段的固化引用文件
   ├─ 对比: 固化引用头部version vs 源头文件 version（SKILL.md 读 YAML version 字段；规范 md 读其头部版本声明行（`> 版本：vX` 格式）。源头部已声明 cured_snapshot 依赖）
   ├─ 一致 → ✅继续
   ├─ 不一致 → ⚠️告警"{文件名}版本滞后:固化v{旧} vs 源v{新}" → 执行重固化(不阻塞,但交付评估前须消除滞后):
   │   ├─ 读源文件头部 cured_snapshot.reference 定位固化文件 + sync_rule 取动作
   │   ├─ 将固化文件从源重新提取评估相关段落 → 升其头部 version 至源版本（**⛔升version前须内容比对（diff/哈希）·2026-09-05批6d＝#131制度性根源封堵：旧捷径"仅版本号滞后可直接升version"使版本对齐但内容漂移合法化（#131 instruction-standard L215实锤）·AI判断"评估本体未变"不算比对**）
   │   └─ 重固化后复跑本步确认 ✅
   └─ 源文件不存在 → 🔴标注"依赖Skill缺失"→ 不阻塞

4. 输出知识网络加载确认
   "📚 评估知识网络已加载:[对象类型] + [N个维度] + [权重配置版本] + 固化引用版本状态"

4.5 细则加载确认(v3.34.0新增·治"没读细则=打折"):关键条款已内联主流程(自爆判据/candidate门禁/审查轮次·3项)+签名两轴定义见 triwich-integration.md 第106行（2026-09-05批6d＝#191：原声明"已内联"但实盘无该段·改为如实指针）——evaluation-framework.md/triwich-integration.md 为扩展参考,⛔DO NOT以"未读细则"为打折借口;内联条款是强制,细则文件是参考。输出一行"细则内联已生效"声明即可。
```

🔌 熔断器（patterns加载）
├─ 成功条件：Read patterns/{对象类型}_patterns.yaml 返回非空内容
├─ 失败处理：降级
├─ 可修正参数：对象类型 → 检查阶段1.5识别的对象类型是否正确（skill/package/project/unknown）
├─ 重试次数：1
└─ 降级方案：patterns文件缺失/为空→降级为 general_evaluation（通用评估模式），继续流程

🔌 熔断器（weights加载）
├─ 成功条件：Read weights/current_weights.yaml 返回非空内容
├─ 失败处理：降级
├─ 可修正参数：权重文件路径 → 检查 references/eval-knowledge/weights/ 下文件是否存在
├─ 重试次数：1
└─ 降级方案：weights文件缺失/为空→使用默认权重(各维度等分)，继续流程

🔌 熔断器（固化引用版本核对）
├─ 成功条件：固化引用版本核对完成且**无未消除告警**（2026-09-05批6d＝#187④矛盾修正：旧文"含告警也视为成功"与本文件第27行"交付评估前须消除滞后"直接矛盾·按27行口径为准——含告警→须重固化后才算成功）
├─ 失败处理：跳过
└─ 降级方案：跳过核对继续，不阻塞

---

