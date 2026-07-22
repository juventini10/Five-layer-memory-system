# NSSM（可选·Windows 最稳守护方式）

记忆琥珀 Windows 守护默认走 **Task Scheduler 加固版**（免管理员、免下载、已在 5.1+Restricted 验证可用），开箱即用。

如果你想要**最稳**的托管（由 Windows 服务控制管理器 SCM 管理，与 macOS launchd 对称：无弹窗、崩溃 5 秒自愈），可选装 NSSM：

## 方式一：手动放置（零网络依赖）
1. 从 https://nssm.cc/download 下载 nssm（选与系统匹配的 64/32 位 `nssm.exe`）
2. 放到本目录：`记忆琥珀/engine/nssm/nssm.exe`
3. 以**管理员身份**重新运行安装：`pwsh -ExecutionPolicy Bypass -File 记忆琥珀/engine/amber-install.ps1`
   分发器检测到 nssm 会自动改走 NSSM 服务。

## 方式二：联网自动装（需 winget/choco + 管理员）
```powershell
winget install NSSM.NSSM   # 或  choco install nssm
```
装好后同样以管理员重跑 `amber-install.ps1`。

> 没装 nssm 也没关系——分发器会自动回退到 Task Scheduler 加固版，功能完整。
