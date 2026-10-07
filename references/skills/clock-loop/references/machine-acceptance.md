> **来源**：外置自 SKILL.md（2026-09-04 重构·渐进式加载第三级·原文机械搬运未改一字·⛔本处不写版本号·以 SKILL.md frontmatter 为唯一真相源＝#142防漂移）
> **加载时机**：Phase X机检/修改评估器时Read（🔧可机器化验收声明·脚本-管什么-判定三列表）
> **返回导航**：SKILL.md §执行流程骨架 / §references目录索引

---

## 🔧 可机器化验收声明（v3.30.0新增·互审整改P0-2）

> 本表声明哪些操作由脚本确定性完成（🔧 可复现不漂移）、判定锚点是什么——脚本是验收锚点，AI自觉不是锚点。AI 执行项（🧠 语义判断）见各路径细则。

| 脚本 | 管什么 | 判定 |
|:---|:---|:---|
| `scripts/skill_eval.py` | Skill S级合规静态检查（19个微观维度=len(WEIGHTS)·v4.12.1 E6修正·Phase X机检） | `--check-only` 输出 `.phaseX_last_run.json` 非空 + `passed`=诚实章 true |
| `scripts/test_skill_eval.py` | 评测器回归测试（fixtures自动发现·改规则必跑） | `python3 -m unittest test_skill_eval` 0 failure |
| `scripts/append_claim.py` | 断言绑实录追加（Layer2对话冲突检测写入） | 写入成功（退出码0） |
| `scripts/load_claim_index.py` | 断言台账议题名索引加载 | 返回非空索引 |
| `scripts/record_fix.py` | 修复建档/复核（三分权·乐观锁） | `--record/--review` 落盘成功；revision 不符拒写 |
| `scripts/finalize_report.py` | 评估报告归档封口物理锁（阶段4） | 16道检查单通过 + 封口确认块JSON + report_sha8 锚 |
| `scripts/check_cured_snapshot.py` | 依赖Skill固化副本版本对账 | triwich/meta-aletheia·0 stale |
| `scripts/check_selfimprove_gate.py` | 自进步门禁（阶段4收尾） | 文件计数达标 |
| `scripts/privacy_check.py` | 发布包隐私残留检测（Phase X-PKG第4项） | 0 残留 |
| `scripts/pkg_report_check.py` | G路径（发布包检查）报告封口校验（v3.38.0·2026-09-05 A24补列·此前漏检＝#183） | 6项校验全过 exit 0（1=拒绝交付） |
| `scripts/calibration_review.py` | 校准台账聚合器（双盲分歧蒸馏端·v3.38.0·2026-09-05 A24补列） | 读 calibration_ledger.json 输出分歧清单非空 |
| `scripts/check_package_health.sh` | 布洛陀发布前包源质检（9项检查·⑤项已废编号保留不重用·2026-09-05 A24补列） | exit 0 全通；FAIL 项数如实报告 |
| `scripts/skill_eval.py` | Skill S级合规静态检查（19个微观维度=len(WEIGHTS)·v4.12.1 E6修正·Phase X机检） | `--check-only` 输出 `.phaseX_last_run.json` 非空 + `passed`=诚实章 true；`--check-evidence` 取证锁L1/L2 |
| `scripts/evidence_guard.py` | 执行证据链路取证锁 L1证据行锁 + L2断言计数锁（§七·2026-09-06新增） | `python3 evidence_guard.py <断言> <源> [min]` exit 0；伪造行号/错引/纯描述→exit 1 |
| `scripts/test_evidence_guard.py` | 取证锁回归测试（L1/L2 负例：伪造行号/错置引文/缺judgment/纯描述/自述伪锁·2026-09-06新增） | `python3 -m unittest test_evidence_guard` 0 failure |
| 外部 `[记忆共享中心]/脚本中心/知识联邦引擎/scripts/kb_concept_lint.py` | 知识库Lint重档（Phase X-KB机械段） | 退出码 0/1/3（3=时序防抖重跑） |
> 🔻 **降级声明**：上列/本节涉及的知识联邦引擎及其脚本属**发布者工具**，安装包不携带该目录——端用户无此引擎时，相关步骤**跳过·不阻塞**。

> **脚本全集唯一源**：`ls scripts/*.py *.sh`（本表=声明"脚本确定性完成"的验收锚点·2026-09-05 A24补齐3个漏检脚本·**新增脚本时须同步本表**——漏检根因见台账#183）。

---

