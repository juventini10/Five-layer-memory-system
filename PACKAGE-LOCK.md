# PACKAGE-LOCK.md — 安装包写入串行协议

> 立制背景：2026-09-23 晨，多端并行改包发生真实覆盖事故——Hermes 端将 `adapters/execution-guidelines-脱敏评估.md` 移至包根时用旧副本覆盖，LobsterAI 端 06:41 写入的修订节丢失（git 无基线无法恢复，靠事后重建）。作者 08:03 令"没人在动了，启动童灵根治所有"，本协议为该根治的机制层。

## 三层防线

| 层 | 机制 | 防什么 |
|:---|:---|:---|
| ① 编辑锁 | `package_lock.sh acquire/release <端名>` | 文件级并发读写覆盖 |
| ② 提交锁 | git `index.lock`（天然原子） | commit 并发竞态 |  
> ℹ️ 2026-10-05 读档注（S-f误判的真相）：脚本 usage 仅列 acquire/release/status，执行者当时未读全文即判「文档虚写 commit 腿」——实查本文 L16 早已写明 git 提交为原生动作、两步锁设计无误。**文档没错，错在只读三行就下结论**。持锁端注意：commit 用包仓原生 git，非 lock 脚本子命令。
| ③ 版本基线 | 包内容入 git（个人AI档案仓库） | 覆盖后不可恢复——事故从"丢失"降级为"diff 可见可回滚" |

## 写侧协议（各端 AI 必守·三步）

1. 动包内任何文件前：`bash package_lock.sh acquire {端名}` —— REFUSED 即排队，⛔DO NOT 绕行硬写。
2. 完成全部编辑+自验（verify/data_contamination_check）后：`git add 布洛陀-全平台安装包 && git commit -m "{端名}: {摘要}"`（先 commit 后 release，锁保护覆盖到提交）。
3. `bash package_lock.sh release {端名}`。异常中断由持锁端负责；锁龄 >6h 视为僵尸锁，任何端可 `release <僵尸端名> --force` 并在系统日志留痕。

> v2.0 自愈注记（2026-10-07·Qoder CN·半残僵尸锁案）：acquire 中断于 mkdir 与 holder 写入之间会留下"lock.dir 在而 holder 无"的结构性死锁（status 假报 FREE、后续 acquire 全 REFUSED）。现 acquire 内置自愈——lock.dir 存在 ∧ holder 缺失/损坏 ∧ 龄>60s ⇒ 打印 `AUTO-REPAIR` 留痕清理后获取；holder 完好的真僵尸锁（>6h）仍按本文人工 `--force` 协议（可能对应仍在编辑的活端）。`status` 对半残态显形 `INCONSISTENT`。

## 读侧

只读（检索/校验/巡检）⛔不需要锁。

## 锁态目录

`.package-lock/`（已入 .gitignore·非发布产物）。
