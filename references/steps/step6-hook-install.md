# 步骤6·钩子安装（未知未知路由兜底）

📦 **产出物**：`~/.workbuddy/hooks/route_unknown_unknown.py` 已拷贝 + 占位符已替换 + `~/.workbuddy/settings.json` 的 `hooks.Stop` 已追加该钩子（幂等、保留现有钩子）

> 🔴 **本步骤是步骤6（Skill安装）的必然后续，不独立计步序。** 步骤6 完成后、步骤6.5（记忆琥珀）之前自动执行。
> 目的：把「未知未知路由 A+B」真正落到执行机——使 SOUL.md 的 `【🕳️ 我的未知未知】` 段在全新安装后即可被 Stop 钩子兜底自动路由到 `悬置区.md`，而非「说明书写了功能、包裹里没发货」。

---

> **⚡ 步骤锁定协议**
> ① 导航锁：每次回复首行输出 `步骤6-钩子（随步骤6执行）`
> ② 偏离锁：用户问无关问题 → 记到待办列表，继续安装
> ③ 检查点前置依赖：Read `{记忆共享中心}/.install/step6-done.md`（全新）或 `{记忆共享中心}/.install/step5-done.md`（升级，因不走步骤6）— 均不存在则阻塞
> ④ 检查点写入：末尾 Write `{记忆共享中心}/.install/step6-hook-done.md`

## 执行指令

### ⚠️ 平台检测（先决）

执行前判定当前平台：

- **macOS / Linux** → 走下方「macOS / Linux」段
- **Windows** → 走下方「Windows」段

---

### macOS / Linux

#### ⚠️ 禁止行为

| 禁止 | 原因 |
|:----|:-----|
| ❌ NEVER覆盖 `~/.workbuddy/settings.json` 的现有钩子 | 活体已挂 `l3_conclusion_guard.py` 等钩子，整文件重写=误删其他钩子=破坏对话质量 |
| ❌ NEVER用硬编码绝对路径替换占位符 | 必须用步骤3确定的记忆共享中心路径，否则钩子指向错误目录，残差写不进用户的悬置区 |
| ❌ NEVER跳过幂等检查 | 二次安装/升级重跑会重复追加同一条钩子命令 |
| ❌ NEVER在验证通过前说"钩子安装完成" | 钩子未挂上=🕳️段无人兜底，等于功能没交付 |

### 🔌 熔断器

- 成功条件：钩子脚本就位可执行 + settings.json `hooks.Stop` 含该命令 + 占位符已替换为真实路径
- 中断处理：任一步失败 → 输出已完成项 + 标注失败点 → 引导回到对应子步骤修复
- 重试机制：修正后从失败的子步骤继续，不需要重跑整个步骤6
- 降级处理：settings.json 解析异常 → 输出原始内容 + 提示用户手动按下方格式追加，不静默吞错

### 0. 确认记忆共享中心路径（macOS / Linux）

> 本步骤所有路径替换以**步骤3确定的记忆共享中心绝对路径**为准（即 `[记忆共享中心]` 占位符的真实值，例如 `/Users/xxx/个人AI档案`）。
> 若该路径尚未确定（步骤3未完成），先回退步骤3。

记此路径为后续 `MEMORY_CENTER` 变量（末尾不带 `/`）。

### 1. 拷贝钩子脚本 + 赋可执行

```bash
cp references/hooks/route_unknown_unknown.py ~/.workbuddy/hooks/
chmod +x ~/.workbuddy/hooks/route_unknown_unknown.py
```

### 2. 替换占位符为真实路径

```bash
MEMORY_CENTER="<步骤3确定的记忆共享中心绝对路径>"
perl -i -pe "s|\[记忆共享中心\]|$MEMORY_CENTER|g" ~/.workbuddy/hooks/route_unknown_unknown.py
```

> 验证替换结果（应无残留 `[记忆共享中心]`）：
> ```bash
> grep -c "\[记忆共享中心\]" ~/.workbuddy/hooks/route_unknown_unknown.py   # 期望输出 0
> grep "DEFAULT_TARGET" ~/.workbuddy/hooks/route_unknown_unknown.py      # 期望显示真实路径
> ```

### 3. 幂等追加到 settings.json 的 hooks.Stop

> 设计原则：**只 append，不覆盖**。先读现有配置 → 检查是否已有该钩子命令 → 有则跳过，无则追加。保留 `l3_conclusion_guard.py` 等所有现有钩子。

```bash
python3 - <<'PYEOF'
import json, os
p = os.path.expanduser("~/.workbuddy/settings.json")
hook_cmd = "python3 " + os.path.expanduser("~/.workbuddy/hooks/route_unknown_unknown.py")

data = {}
if os.path.isfile(p):
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

hooks = data.setdefault("hooks", {})
stop = hooks.setdefault("Stop", [])

# 幂等：任一现有 Stop 元素已含该钩子命令 → 跳过
already = any(
    "route_unknown_unknown.py" in h.get("command", "")
    for grp in stop if isinstance(grp, dict)
    for h in grp.get("hooks", []) if isinstance(h, dict)
)
if not already:
    stop.append({"hooks": [{"type": "command", "command": hook_cmd}]})
    print("APPENDED: route_unknown_unknown.py 钩子已追加")
else:
    print("SKIPPED: 钩子已存在，幂等跳过")

with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
PYEOF
```

> ⚠️ 该操作会**重新格式化** settings.json（JSON 标准缩进）。这是预期行为——结构不变、仅缩进标准化，不影响 WorkBuddy 加载。若你介意原文件手写格式，可改用手动 patch，但自动追加重格式化是更稳的默认。

### 4. 🔒 门禁验证

```bash
# 4a. 脚本存在且可执行
test -x ~/.workbuddy/hooks/route_unknown_unknown.py && echo "OK_HOOK_FILE"

# 4b. settings.json 含该钩子命令
python3 - <<'PYEOF'
import json, os
p = os.path.expanduser("~/.workbuddy/settings.json")
with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)
stop = data.get("hooks", {}).get("Stop", [])
found = any(
    "route_unknown_unknown.py" in h.get("command", "")
    for grp in stop if isinstance(grp, dict)
    for h in grp.get("hooks", []) if isinstance(h, dict)
)
print("OK_HOOK_REGISTERED" if found else "FAIL_HOOK_MISSING")
PYEOF
```

- 两项均输出 `OK_*` → 写入检查点，进入步骤6.5
- 任一项 `FAIL` → 回到对应子步骤（1 或 3）修复

---

### Windows

> Windows 上 Python 命令为 `python`（非 `python3`），路径用反斜杠，无 `chmod`。

#### 0. 确认记忆共享中心路径（Windows）

同 macOS——以步骤3确定的记忆共享中心路径为准，记作 `MEMORY_CENTER`（末尾不带 `\`）。

#### 1. 拷贝钩子脚本（无需 chmod）

```powershell
New-Item -ItemType Directory -Path $env:USERPROFILE\.workbuddy\hooks -Force
Copy-Item references\hooks\route_unknown_unknown.py $env:USERPROFILE\.workbuddy\hooks\
```

#### 2. 替换占位符为真实路径

```powershell
$MEMORY_CENTER = "<步骤3确定的记忆共享中心路径>"
$f = "$env:USERPROFILE\.workbuddy\hooks\route_unknown_unknown.py"
(Get-Content $f -Raw).Replace('[记忆共享中心]', $MEMORY_CENTER) | Set-Content $f -NoNewline
```

> 验证：
> ```powershell
> Select-String -Path "$env:USERPROFILE\.workbuddy\hooks\route_unknown_unknown.py" -Pattern '\[记忆共享中心\]'   # 期望无输出
> Get-Content "$env:USERPROFILE\.workbuddy\hooks\route_unknown_unknown.py" | Select-String "DEFAULT_TARGET"     # 期望显示真实路径
> ```

#### 3. 幂等追加到 settings.json 的 hooks.Stop

```powershell
python -c @"
import json, os
p = os.path.expanduser('~/.workbuddy/settings.json')
hook_cmd = 'python ' + os.path.expanduser('~/.workbuddy/hooks/route_unknown_unknown.py').replace('\\', '/')

data = {}
if os.path.isfile(p):
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)

hooks = data.setdefault('hooks', {})
stop = hooks.setdefault('Stop', [])

already = any(
    'route_unknown_unknown.py' in h.get('command', '')
    for grp in stop if isinstance(grp, dict)
    for h in grp.get('hooks', []) if isinstance(h, dict)
)
if not already:
    stop.append({'hooks': [{'type': 'command', 'command': hook_cmd}]})
    print('APPENDED: route_unknown_unknown.py hook appended')
else:
    print('SKIPPED: hook already exists, idempotent')

with open(p, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"@
```

> ⚠️ Python 的 `os.path.expanduser('~')` 在 Windows 上正确解析为 `%USERPROFILE%`。

#### 4. 🔒 门禁验证

```powershell
# 4a. 脚本存在
Test-Path "$env:USERPROFILE\.workbuddy\hooks\route_unknown_unknown.py"  # 期望 True

# 4b. settings.json 含该钩子命令
python -c "import json,os;d=json.load(open(os.path.expanduser('~/.workbuddy/settings.json')));print('OK_HOOK_REGISTERED' if any('route_unknown_unknown.py' in h.get('command','') for grp in d.get('hooks',{}).get('Stop',[]) if isinstance(grp,dict) for h in grp.get('hooks',[]) if isinstance(h,dict)) else 'FAIL_HOOK_MISSING')"
```

- 两项均输出 `OK_*` → 写入检查点，进入步骤6.5
- 任一项 `FAIL` → 回到对应子步骤（1 或 3）修复

---

## 写入检查点

验证全部通过后，Write `{记忆共享中心}/.install/step6-hook-done.md`：

```
步骤：步骤6·钩子安装（未知未知路由兜底）
完成时间：<当前时间>
产出物：
- ~/.workbuddy/hooks/route_unknown_unknown.py（已拷贝+占位符替换+可执行）
- ~/.workbuddy/settings.json 的 hooks.Stop 已追加该钩子（幂等，保留现有钩子）
验证：脚本可执行 OK + settings.json 注册 OK
```
