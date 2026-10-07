#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/user_machine_fixture.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""user_machine_fixture.py —— 「用户机」夹具闸门（端到端·防作者机假绿）

## 为什么必须有这道闸

2026-10-02 取证出的两个缺陷，**在作者机上 100% 测不出来**：

| 缺陷 | 作者机 | 用户机 |
|:---|:---|:---|
| `devtools` 键指向 `开发工具`（作者侧目录） | 该目录**存在** ⇒ 声明成立 ⇒ 全绿 | **不存在** ⇒ 缺键 ⇒ 22 处调用抛错 |
| 11 个插件执行体只在 `开发工具/` | **存在** ⇒ 插件跑得通 | **不存在** ⇒ 静默跳过 ⇒ 功能没装上 |

根因：**作者机有用户机没有的东西**（作者侧档案根下的 `脚本中心/` 等目录·具体路径由声明定位）。
⇒ 任何在作者机上跑的验证，对"用户能不能顺利装完"**都不成立**。

## 本闸门做什么

造一个**没有作者侧目录**的临时记忆中心，模拟安装器的真实落点，
然后跑真实验证：

1. 装 `references/scripts/` → `<MC>/脚本中心/`（照 `deploy_script_center` 的 dst_root）
2. 用 `install_scripts.build_runtime_paths` 生成声明
3. **逐项**取 16 个插件里每一个 `rp("键", ...)` 调用
4. **真导入** 16 个插件（`exec_module`）

⛔ **不 mock、不桩**——目录就是没建，让它自己撞。

## 用法

```
python3 user_machine_fixture.py            # 全检
python3 user_machine_fixture.py --keep     # 保留夹具（排查用）
```

退出码：`0`=用户机可装可用 · `1`=有失败（⛔ 不可发包）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import importlib.util as il
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ARCH = os.path.expanduser("~")
PKG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# B17同族根治(2026-10-05·第4支B16同型)：设计运行面=包内 references/scripts/（上溯三层即包根）；
# 作者态/软链入口上溯错位 ⇒ 若无包件则**由声明推包根**（条文47·⛔不引入档案根字面·无声明hard fail）
if not os.path.isfile(os.path.join(PKG, "install_scripts.py")):
    _spec_rp = il.spec_from_file_location("RP_FIX",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtime_paths.py"))
    _rp = il.module_from_spec(_spec_rp)
    _spec_rp.loader.exec_module(_rp)
    PKG = os.path.join(_rp.rp("archive_root"), "发布库/五层记忆系统/布洛陀-全平台安装包")
PLUG = os.path.expanduser("~/.hermes/plugins")


def _install_dirs_from_installer(INS):
    """🔴 **2026-10-03 根治：目录清单不再手抄**（本闸门自己曾是第一本账）。

    **病根（当场实锤）**：本文件原写
        INSTALL_DIRS = ["脚本中心", "脚本中心/知识联邦引擎", ...]
    而安装器 `deploy_script_center` 实际写 `<MC>/知识联邦引擎/`（10-03 从脚本中心下独立）。
    ⇒ 清单漂移 ⇒ `build_runtime_paths` 的存在性过滤跳过 `kb_engine` 键
    ⇒ `buluotuo-stop-hook` / `route-audit-hook` 导入即抛 `PathKeyMissing` ⇒ **2 插件炸**。

    ⚠️ **而这次假红是我自己制造又自己抓的**：清单与安装器同属"落点"这一事实，
    两处各写一份 ⇒ **必漂**。漂了以后，**是夹具报错，不是包报错**——
    根因与指归被颠倒，真洞会被当成误报抹平（§5.7 同族）。

    ⇒ **正解：清单从安装器真源派生**（`RUNTIME_PATH_DIRS` 是模块级常量·可直读）。
    今后安装器改落点 ⇒ 本闸门自动跟随 ⇒ **这本账拆掉，不是补数值**。

    额外补 `技能配置/` 与 `记忆蓝图/`：它们由 `step5/step6`（端 AI 执行路径）落，
    不在 `RUNTIME_PATH_DIRS` 里，但插件会经 `rp("skills")` 取 → 缺了同样假红。
    """
    dirs = {"脚本中心", "数字分身", "数字分身/K2切片蒸馏", "记忆规则",
            "记忆琥珀", "技能配置", "工作日志", "记忆蓝图"}
    for rel in INS.RUNTIME_PATH_DIRS.values():
        dirs.add(rel if isinstance(rel, str) else "/".join(rel))
    return sorted(dirs)
# ⛔ **刻意不建**「开发工具」——那是作者侧目录，端用户机器上没有。
#    建了就等于把这道闸门自己作废（假绿）。

RP_CALL = re.compile(r'\brp\(\s*"([a-z_]+)"(?:\s*,\s*"([^"]+)")?')

# 🔴 **拼接式路径解析**（2026-10-02·封口前补的盲区）
#
# 事实：`route-audit-hook` / `doenglingz-twin` 等插件**不是全都走 rp()**——
# 存在 `_DEVTOOLS = rp("devtools")` 然后 `os.path.join(_DEVTOOLS, "x.py")` 的写法。
# ⛔ 只扫 `rp("键","文件")` 形态 ⇒ 拼接出来的目标**结构性漏检**
#    ⇒ `hermes_tsl_closeout_adapter.py` / `stamp_precheck_guard.py` 两个真缺口
#       在"五闸全绿"下溜了过去（封口前最后一轮实测抓出）。
#
# ✅ 本闸改为：**扫出所有「目录变量 + os.path.join(..., 字面量名)」**，
#    解析出文件名，一并纳入"文件是否真实存在"检查。
#    ⇒ 必需依赖缺失 ⇒ 红；可选(作者侧)缺失 ⇒ ✅
JOIN_PAT = re.compile(r'os\.path\.join\(\s*(_[A-Z_]+|DEVTOOLS)\s*,\s*"([^"]+)"')
# 形如 ("xxx.py", [args]) 的元组表（route-audit-hook 的守卫清单）
TUPLE_PAT = re.compile(r'\(\s*"([A-Za-z0-9_\-]+\.py)"\s*,')

# ⚠️ **可选依赖白名单**（2026-10-02·pruner 越界裁决带出来的判据缺口）
#
# 事实：`platform_adaptation_check / evolution_deviation / route_evolution_suggest /
#      self_optimization_engine / panel_snapshot` 五个**依赖作者侧设施**
#      （开发工具/logs · 知识联邦引擎 · ~/.qoder-cn · 自定义层/待完成工作/）
#      ⇒ 端用户机器上**前提不成立** ⇒ pruner 判它们 out_of_scope（裁决正确）。
#      ⇒ 由 `route-audit-hook` 单点调用，且每处都有 `os.path.isfile()` 保护
#         ⇒ 用户机上**优雅跳过、不崩**——这正是要的降级。
#
# ⛔ 若把它们当"必需依赖"判红，就是逼发布包携带作者设施 = 隐私泄漏。
#    ⇒ 本闸只对**必需依赖**判红；可选依赖缺失 = ✅ 通过。
#
# ⛔ 白名单必须**逐个写明理由**，⛔ 禁止通配。理由不成立 ⇒ 立刻删掉该条目。
OPTIONAL_AUTHOR_SIDE = {
    "platform_adaptation_check.py": "作者多端接入率校验·依赖开发工具/logs",
    "evolution_deviation.py":     "作者侧信号层·依赖开发工具/logs+知识联邦引擎",
    "route_evolution_suggest.py": "作者侧建议生成·依赖开发工具/logs+知识联邦引擎",
    "self_optimization_engine.py":"作者控制环·依赖自定义层/待完成工作/（已出包）",
    "panel_snapshot.py":          "作者面板监视·读 ~/.qoder-cn + 写 开发工具/logs/runtime",
    # Hermes 端专属守卫（2026-10-03 补·夹具 rc=1 定案·⛔ 逐条写明理由·禁通配）：
    #   ① hermes_core_budget_guard —— 守 Hermes 官方契约 `register_system_prompt_section`
    #      的 max_chars=4000 硬上限（超限静默失效·防「恒驻核预算爆掉却没人知道」）。
    #      端用户机**无 Hermes 端**⇒ 该契约不存在 ⇒ 守卫前提不成立。
    #   ② hermes_session_anomaly_guard —— Hermes 会话层异常检测（DSH/lobsterai 同族）。
    #      端用户机无 Hermes 端 ⇒ 无会话层可监测。
    #   ⚠️ 与上 5 件同类：真机上它们在（作者侧/Hermes 端已挂），但**隔离机装完确实没有**
    #      ——夹具直接调 deploy_* 装到临时 MC（⛔ 不手抄拷贝源清单），判「缺失」是**如实**的。
    "hermes_core_budget_guard.py":  "Hermes 端专属·守 register_system_prompt_section 的 max_chars 硬契约（端用户机无该端）",
    "hermes_session_anomaly_guard.py": "Hermes 端专属·会话层异常检测（DSH/lobsterai 同族·端用户机无该端）",
    # ⛔ 数字分身域 + 作者侧设施（pruner 反向对账 ② 的裁决，理由逐条对齐）：
    #    端用户机上「数字分身域结构」不存在 ⇒ 这些守卫**前提不成立**⇒ 优雅跳过。
    #    ⚠️ 与上 5 件同类：插件侧均有 os.path.isfile/isdir 保护 ⇒ 不崩、只静默跳过。
    "doenglingz_inject_prompt.py": "数字分身域·W1上岗行+W3域切片注入·端用户无分身域结构",
    "gate_runner.py":              "数字分身域·读 数字分身/gates + 童灵·人格规格书",
    "guard_registry_check.py":     "作者侧设施·引用 开发工具/logs + 知识联邦引擎",
    "twin_changelog_guard.py":     "数字分身域·童灵规格书↔CHANGELOG 同步守卫",
    "twin_verdict_ledger.py":      "数字分身域·运行期裁决台账",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    T = tempfile.mkdtemp(prefix="userfix_")
    MC = os.path.join(T, "MyVault")            # ⛔ 刻意不叫档案根名（防投影字面泄漏·B修源v2）
    CFG = os.path.join(T, ".hermes")
    SC = os.path.join(MC, "脚本中心")   # 拼接式检查的落点

    # 🔴 **不模拟安装·直接调安装器本体**（2026-10-03 根治·第二本账同拆）
    # 原写 `shutil.copytree(references/scripts → 脚本中心/)` = **手抄安装器的拷贝源清单**
    # ⇒ 安装器加第三源（本次修的分身件）时本闸门不知道 ⇒ 假绿/假红都从这来。
    # ⇒ 现在改成调 `deploy_*` 本体：**安装器装什么，夹具就装什么**（单一真源）。
    spec = il.spec_from_file_location("INS_FIX", os.path.join(PKG, "install_scripts.py"))
    INS = il.module_from_spec(spec)
    spec.loader.exec_module(INS)

    for d in _install_dirs_from_installer(INS):
        os.makedirs(os.path.join(MC, d), exist_ok=True)
    n_files = INS.deploy_script_center(MC) + INS.deploy_digital_twin(MC)
    os.makedirs(os.path.join(CFG, "doenglingz"), exist_ok=True)
    print("=== 用户机夹具 ===\n根：%s" % T)
    print("  记忆中心：MyVault（⛔ 无「开发工具」——模拟真实用户）")
    print("  已调安装器本体部署：%d 件（脚本中心 %d + 分身套件）"
          % (n_files, len(os.listdir(SC))))

    data = INS.build_runtime_paths(MC)
    jf = os.path.join(CFG, "doenglingz", "runtime_paths.json")
    json.dump(data, open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    shutil.copy2(os.path.join(PKG, "references", "scripts", "runtime_paths.py"),
                 os.path.join(CFG, "doenglingz"))
    print("  声明：%d 键 %s" % (len(data), sorted(data)))

    # ⚠️ 必须在 **本进程** 也设：① 段是进程内直接调 RP.rp()，只给子进程设会得到
    #    DeclNotFound（闸门自己假红过一次·2026-10-02）。
    os.environ["BULUOTUO_RUNTIME_PATHS"] = jf
    env = {**os.environ, "BULUOTUO_RUNTIME_PATHS": jf}
    sys.path.insert(0, os.path.join(CFG, "doenglingz"))
    import runtime_paths as RP
    RP.reset_cache()

    # ① 逐项取路径
    n_call = 0
    n_opt = 0
    bad_call = []
    for d in sorted(os.listdir(PLUG)):
        p = os.path.join(PLUG, d, "__init__.py")
        if not os.path.isfile(p):
            continue
        for m in RP_CALL.finditer(open(p, encoding="utf-8",
                                        errors="replace").read()):
            k = m.group(1)
            parts = [x for x in m.groups()[1:] if x]
            n_call += 1
            try:
                v = RP.rp(k, *parts)
                base = os.path.basename(v) if v else ""
                if (base in OPTIONAL_AUTHOR_SIDE):
                    n_opt += 1          # 可选·作者侧设施·缺失即正常态
                    continue
                if (v and v.endswith((".py", ".sh")) and "log" not in v
                        and "日志" not in v and not os.path.exists(v)):
                    bad_call.append((d, k, parts, "路径不存在：%s" % base))
            except Exception as e:
                bad_call.append((d, k, parts, "%s: %s" % (type(e).__name__, str(e)[:60])))
    print("\n=== ① rp() 调用 %d 处（可选·作者侧 %d 处）==="
          % (n_call, n_opt))
    # 🔴 拼接式目标（同批补的盲区）：`os.path.join(_DEVTOOLS, "x.py")` 与
    #    `("x.py", [args])` 元组表 ⇒ 上一轮结构性漏检，封口前实测抓出 2 个真缺口。
    n_join = 0
    bad_join = []
    for d in sorted(os.listdir(PLUG)):
        q = os.path.join(PLUG, d, "__init__.py")
        if not os.path.isfile(q):
            continue
        src = open(q, encoding="utf-8", errors="replace").read()
        names = set(m.group(2) for m in JOIN_PAT.finditer(src))
        names |= set(m.group(1) for m in TUPLE_PAT.finditer(src))
        for nm in names:
            # ⛔ 只查**可执行脚本**：.hermes / plugin.log / <记忆中心> 这类是
            #    路径片段或目录拼接，不是「缺了就崩」的执行体。
            #    ⛔ 目录名命中 ⇒ 误报（上一轮把 .hermes 报成缺失文件）。
            if not nm or not nm.endswith((".py", ".sh")):
                continue
            n_join += 1
            if nm in OPTIONAL_AUTHOR_SIDE:
                continue
            if not os.path.exists(os.path.join(SC, nm)):
                bad_join.append((d, nm))
    print("\n=== ①b 拼接式目标 %d 个（盲区补扫）===" % n_join)
    if not bad_join:
        print("  ✅ 全部可从包内提供")
    else:
        print("  ❌ %d 个缺失" % len(bad_join))
        for d, nm in bad_join:
            print("     %-30s %s" % (d, nm))
    if not bad_call:
        print("  ✅ 全部可取到且文件真实存在")
    else:
        print("  ❌ %d 处失败" % len(bad_call))
        seen = set()
        for d, k, parts, err in bad_call:
            key = (k, tuple(parts), err[:36])
            if key in seen:
                continue
            seen.add(key)
            print("     %-28s rp(%s) → %s"
                  % (d, k + "".join(',"%s"' % x for x in parts), err))

    # ② 真导入 16 插件
    plugins = [os.path.join(PLUG, d, "__init__.py") for d in sorted(os.listdir(PLUG))
               if os.path.isfile(os.path.join(PLUG, d, "plugin.yaml"))]
    bad_imp = []
    for p in plugins:
        r = subprocess.run(
            [sys.executable, "-c",
             "import importlib.util as il,sys;s=il.spec_from_file_location('m',sys.argv[1]);"
             "m=il.module_from_spec(s);s.loader.exec_module(m);print('OK')", p],
            capture_output=True, text=True, timeout=180, env=env)
        if r.stdout.strip() != "OK":
            bad_imp.append((os.path.basename(os.path.dirname(p)),
                            (r.stderr or "").strip().split("\n")[-1][:80]))
    print("\n=== ② 插件真导入 %d 个 ===" % len(plugins))
    if not bad_imp:
        print("  ✅ 全部可导入")
    else:
        print("  ❌ %d 个失败" % len(bad_imp))
        for d, e in bad_imp:
            print("     %-30s %s" % (d, e))

    ok = not (bad_call or bad_join or bad_imp)
    print("\n%s" % ("✅ 用户机可装可用（夹具实证）" if ok
                    else "❌ 用户机装完不可用——⛔ 不可发包"))
    if a.keep:
        print("夹具保留：%s" % T)
    else:
        shutil.rmtree(T, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())