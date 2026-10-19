# 步骤8：数字分身（童灵）部署与逐环节验证链
> 🔊 收口播报（P31/P22）：本站收口 MUST 播 INSTALL.md〈段间播报表〉对应行（8/8 口径）；非 T9 终点站⛔禁说"完成/装好了"，只说"这站就位"；进度数字读 .install/stepN-done.md。

- **状态**：v2.0（2026-10-13 全量调查后重写·替代 v1.0 的 25 行 TODO 骨架）
- **依据**：INSTALL.md §数字分身完整版单装（三阶段+养成链）· 条文7（注册≠派发·装机验证须有运行态腿）· 条文17（五腿判据）· 条文61（双平台对等）· 既有检查器 `twin_chain_check.py`（verify.sh §3.7）与 `slice_chain_check.py`（§3.7b）
- **病灶**（本步骤治什么）：数字分身是上版安装被追问最多的环节（"分身装哪/语义模型在哪"）——Phase A/B/C+养成链装在 INSTALL.md 单装章节，**每段只有"文件在不在"级自检，没有"跑起来 work 不 work"级验证闸**。本步骤把每段落成「动作+机械自检命令+通过判据」三件套，上一段不过不进下一段。

## 0. 前置依赖与入口（检查点链·条文39）

1. Read `[记忆共享中心]/.install/step7-done.md`（升级态为 step6-done）——不存在则**阻塞**，回退对应步骤。
2. **主流程挂接**（治"老用户升级不自动补齐"）：step7 验收通过后，AI 必须检测分身在位情况并提示——
   - `install_scripts.py` 安装末尾（`main():2580` `_detect_existing_twin`）已自带：有分身→"跳过造芯·只做接入"；无分身→三步造芯引导。step7 文档侧同步该口径：安装器已打印引导≠流程已走完，AI 须把用户带到本步骤或明示"分身可后装"。
   - 提示话术（固定）：「数字分身未装（或未造芯）——现在走步骤8部署，或随时说『装数字分身』走单装流程。」
3. 记忆共享中心路径从 `step3-done.md` 头部 CONFIG_ROOT/MEMORY_CENTER 读取（重启会话自恢复）。

## 1. 实现层现状（2026-10-13 实跑订正·⛔ 勿照抄旧 TODO）

| 件 | 现状 | 证据 |
|:--|:--|:--|
| 分身三钩子 | **已在 ROSTER** | `install_scripts.py:122-124`（doenglingz_inject_prompt.py / twin_verdict_ledger.py / twin_changelog_guard.py）；`--list --platform <端>` 末尾三行实证 |
| 守卫件 | **已在 DT_SUITE devtools** | `install_scripts.py:170-181`（doenglingz_guard.py / gate_runner.py / tsl_verify.py 等）·随脚本体系自动部署 |
| 造芯引导 | **已在安装器内** | `main():2573-2603`（有分身检测+三步引导+入门指南路径） |
| 卡链路/切片链检查器 | **已在包内** | `references/scripts/twin_chain_check.py` · `slice_chain_check.py`（verify.sh §3.7/§3.7b 已接线） |

⇒ 旧版缺口 1「守卫执行自动入口未入 ROSTER」**已不成立**（2026-09-30 后已补齐）。本步骤真缺口 = **逐环节验证闸**（下四节）。

## 2. Phase A · 分身基座（零下载·即装即用）

**动作**（对齐 INSTALL.md §数字分身完整版单装 Phase A）：
1. A1 前置检查：脚本体系已装？（`install_scripts.py --list` 含分身三钩子·见上表）——未装 → 先走「脚本体系单装」再回来。
2. A2 部署 `[记忆共享中心]/数字分身/` 目录骨架：devtools 钩子件 + gates + hexaco 答题件 + k2 造芯三件 + onboarding 引导三件（人格向量空模板 + 规格书骨架 + 入门指南）。
3. A3 就绪检查：骨架在位。

**机械自检**（上一段不过不进下一段）：

```bash
# Mac/Linux（Windows 见 §6 对照·python→python.exe）
MC="[记忆共享中心]"   # 从 step3-done.md 取
# A2 判据：三件套在位
for f in "数字分身/onboarding/童灵·人格向量-空模板.json" \
         "数字分身/onboarding/童灵·人格规格书-骨架模板.md" \
         "数字分身/onboarding/入门指南-通用版.md"; do
  [ -f "$MC/$f" ] && echo "✅ $f" || { echo "❌ 缺 $f → 阻塞"; exit 1; }
done
# A3 判据：造芯件在位（生成器只读正式件·⛔不认模板名）
[ -f "$MC/数字分身/k2-slice-generator/hexaco_slice_generator.py" ] && echo "✅ 造芯件在位" || { echo "❌ 缺造芯件 → 阻塞"; exit 1; }
```

**通过判据**：全部 ✅ 才进 Phase B。任一条 ❌ → 停下报告缺失件，⛔不继续（防"骨架没装齐就往下跑"的静默漏装）。

## 3. Phase B · 卡生产链路（最小件·无模型·核心增量）

**动作**：引擎最小件 9 件随脚本体系自动装配（`install_scripts.py` 的 `deploy_script_center`→`[记忆共享中心]/知识联邦引擎/scripts/`）——本段只做**验证**，无需手工拷贝（⛔不要照 INSTALL.md 手工 cp 段·那是安装器不可用时的兜底）。

**机械自检**：

```bash
# B3 判据（对齐 INSTALL.md Phase B 终检）：extract_concepts.py prepare 输出 PREPARED 或 SKIP-LOGGED（C23：无进料首装留痕态同判过）
python3 "$MC/知识联邦引擎/scripts/extract_concepts.py" prepare 2>&1 | grep -q -e PREPARED -e 'SKIP-LOGGED' \
  && echo "✅ 卡生产链路就绪" || { echo "❌ 卡链路未就绪（看上方输出·多为路径/依赖）→ 阻塞"; exit 1; }
# 引擎件完整性（缺件=装了也断）
for f in extract_concepts.py regen_ailib_index.py derive_reading_status.py \
         sync_card_frontmatter.py collision_scan.py build_kb_vectors.py \
         _engine_env.py _paths.py source_hash.py; do
  [ -f "$MC/知识联邦引擎/scripts/$f" ] || { echo "❌ 缺 $f → 阻塞"; exit 1; }
done && echo "✅ 引擎九件齐"
```

**通过判据**：PREPARED 或 SKIP-LOGGED（无进料源已留痕=首装正常态，脚本 131 行分支实证在位；晚间复盘可重扫）+ 九件齐。语义增强**未装不阻塞**（降级不阻塞·条文16：collision_scan 无模型时明确退出不静默）。

## 4. Phase C · 语义增强（可选·知情同意后自选·默认跳过）

**动作**：C1 知情同意卡（**先展示后选择·⛔ AI 不得替用户决定/默认下载**·话术全文以 INSTALL〈模型安装文案（C1 展示稿全文）〉节为唯一真源逐字宣读，⛔本节不复制要素表——P25 根治双本账截胡）；选「装」→ C2 下载引导（hf-mirror 镜像·BAAI/bge-base-zh-v1.5·本机缓存全程离线）；选「不装」或下载失败 → 回 Phase B 态，如实标注"语义增强未装"。

**机械自检**（仅当选了「装」）：

```bash
# C3 判据：build_kb_vectors.py 输出向量库已更新（JSON+npy 双写）
python3 "$MC/知识联邦引擎/scripts/build_kb_vectors.py" 2>&1 | grep -q "向量库已更新" \
  && echo "✅ 语义层点亮（同义问法可命中立场卡）" || { echo "❌ 向量库未建成（多为模型未落盘/内存不足·自动降级无模型态·⛔不阻塞）"; }
```

**通过判据**：选「不装」= 本段通过（如实标注）；选「装」= C3 绿或显式降级声明。**任何情况不阻塞 Phase 后续**——语义层是增强不是必需（条文16 降级不阻塞）。

## 5. 养成链 · 两步入职（D1-D4·AI 对话执行·⛔不许 shell 自动化·条文39 §3）

**动作**（对齐 INSTALL.md 养成链）：D1 答题（浏览器打开 `[记忆共享中心]/数字分身/hexaco/自建100题-答题页-v1.html`——P28 单源裁决：包面仅此一张答题页，⛔按题材名另找页面；全程本地计算不联网）→ D2 计分（把答题页导出的 JSON 存盘，**跑随包脚本机械计分**：`python3 "$MC/数字分身/hexaco/hexaco_selfbuild_scorer.py" "<答卷.json>"`——反向计分/六维均分/效度闸/直线作答检测全在脚本里，⛔AI 不心算 96 个数（E2E 实测首轮手抄即错 2 题）；`rc=0` 才进 D3，`rc=1` 按提示重答该段（用户确认暂不重答而继续时，**D3 开场第一句必须先宣读告知**：取计分输出的 `runs`（连片同分段）/`zero_dims`（零信号维度）/`share_flag`（单一分值占比）字段逐条转述——哪些维本次无信号、建议重答哪段；无信号维度在人格向量对应域加 `__本次无信号__` 标注后才可写入，⛔ 不得拿中性值冒充读数进造芯，⛔ 未宣读不得进 D3——告知内容绑脚本字段非 AI 记忆，S064），`rc=2` 作答作废须重测）→ D3 偏移+基调协商（**AI 只能建议·逐条确认或拒绝才写入**·表达基调七候选你定）→ D4 上线（跑两个生成器+接线）。

**机械自检**（D 段每步的落盘判据）：

```bash
# D4 判据①：正式件在位（复制模板改名后·⛔模板原件不算）
[ -f "$MC/数字分身/童灵·人格向量.json" ] && echo "✅ 人格向量已落" || echo "⏳ 未造芯（D2 未完成）"
[ -f "$MC/数字分身/童灵·人格规格书.md" ] && echo "✅ 规格书已落" || echo "⏳ 未蒸馏（第二步入职未做）"
# D4 判据②：切片产物存在（生成器确定性产出）
ls "$MC/数字分身/K2切片蒸馏/slices/"*.md >/dev/null 2>&1 && echo "✅ 切片已生成" || echo "⏳ 切片未生成（跑两个生成器后复检）"
# 蒸馏完成自检一问（INSTALL.md 硬前置）：挑规格书 L1 一段·有没有只有你才说得出的具体内容？
# 没有＝没蒸完·别跑生成器（拿空骨架生成＝切片全是模板套话）
```

**通过判据**：第一步入职完成 = D1-D3 有人格向量正式件；D4 跑完生成器切片存在。

**D5 终验收口（P33·2026-10-19 硬步骤·不靠 AI 记得）**：D4 通过后 ✅DO 重出 INSTALL〈M6 三层验收〉屏——分身状态行按实况三态判定：`已入职` / `文件在·值守未生效` / `未入职`；全绿才播〈T9 全线完成播报〉固定稿（唯一终点）。任一项红 → 播〈T9 降级态宣告〉**第三分支**（P32缺口1）：「底座完成，分身自动值守未生效。原因：[红项逐条]；修复路径：[对应站回补口令]；期间分身手动三档（代行/预筛/守护）照常可用。」⛔ 禁止"全绿稿或烂尾"二选一；⛔ T9 播完不回屏就收场。数据源=verify/装机回执实况，⛔ 复制上次输出。第二步入职（规格书蒸馏）随用随蒸——**不存在"等养成"门槛**，但跑生成器前必须过"蒸馏完成自检一问"。

## 6. 终检（装后统一·挂 verify 已有检查器）

**不另造检查器**——复用包内既有两条（条文4 双写链共用·⛔防双本账）：

| 检查器 | 命令（Mac） | 判据 |
|:--|:--|:--|
| 分身链路（抽卡→落卡→碰撞） | `python3 references/scripts/twin_chain_check.py --pkg-root <安装包> --memory-center "$MC" --quiet` | rc=0 三步全绿（隔离沙箱·零触真实卡库） |
| 切片链（规格书→生成器→六片） | `python3 references/scripts/slice_chain_check.py --pkg-root <安装包>` | rc=0 五断言全绿（包骨架沙箱·零触真实档案） |
| 派发心跳（注册≠派发·条文7） | `python3 <MC>/脚本中心/guard_heartbeat_check.py --report` | 三钩子在岗（⚪无记录=刚装完正常·🔴停摆嫌疑需排查） |

**双平台对照**（条文61·⛔不许"有 Git Bash 所以 bash 能跑"推断）：

| 本文件命令 | Mac/Linux | Windows |
|:--|:--|:--|
| python3 | `python3` | `python.exe`（WB 自带绝对路径·非 WB 端 PATH 上的 python）或 `py` |
| 终检跑法 | `bash verify.sh --platform <端ID>` | `powershell -File verify.ps1 -Platform <端ID>`（win-verify.ps1 走安装腿真跑） |
| 心跳报告 | 同上 | 同上（ps1 侧已镜像 §3.6） |

Windows 侧特有注意：① 中文路径+PowerShell 编码（管道非 UTF-8 locale 必崩·条文5 平台维度）；② 语义模型下载腿走 pwsh（Phase C 可选腿）。

## 7. 检查点写入（条文39）

本步骤完成（或显式声明"分身后装"）→ Write `[记忆共享中心]/.install/step8-done.md`，内容**必须是实查结果**（⛔不是"已完成"三字）：

```markdown
# step8-done
日期：YYYY-MM-DD HH:MM
Phase A：✅/❌（依据：三件套+造芯件在位检查输出）
Phase B：✅/❌（依据：PREPARED 或 SKIP-LOGGED＋九件齐）
Phase C：已装/未装（知情同意结果）
养成链：D1-D4 进度（人格向量/规格书/切片 存在性实查）
终检：twin_chain_check rc=? · slice_chain_check rc=? · 心跳三态=?
声明：分身完整部署 / 分身后装（用户选择·已告知走单装路径）
```

## 8. 历史

- v1.0（2026-09-30）：25 行 TODO 骨架（缺口 4 处·含"守卫未入 ROSTER"——2026-10-13 实跑证实该缺口已不成立）
- v2.0（2026-10-13）：全量调查后重写为真执行链——四段三件套（动作+机械自检+通过判据）+ 实现层现状订正表 + 终检挂既有检查器 + 双平台对照 + 检查点实查结果模板
