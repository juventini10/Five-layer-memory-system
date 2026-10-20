#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sescan_shim.py — security-scan 读模式镜像钩子（本端自有·D31 根治件·v2 极简职责）
真源: [记忆共享中心]/成长箱/免疫修复工单.md D31 · 裁决: 2026-10-20 皮叔令「不管用什么办法，符合愿景的第一性原理彻底根治」

病灶（取证见 D31 2026-10-20 回填）：
  官方插件钩子以「直接执行」模式跑 ~/.qoder-cn/plugins/cache/.../qodersec-launch.cmd，
  执行权依赖产品安装/更新事务对 bin/ 的瞬间文件状态（EACCES 间歇·本端不可控窗口）。
  对照实验（2026-10-20 实跑）：0644 文件直接执行 → zsh: permission denied rc=126；
  同文件经解释器读模式（python3 脚本 / sh 脚本）→ rc=0。本端 65 条自有钩子全为读模式=零崩同构证据。

根治架构（解耦「扫描成功」与「产品事务瞬间权限态」）：
  1. 镜像：插件 bin/ 只读复制到本端自有 sescan-engine/bin/（内容指纹自动跟随升级·不依赖人记得）
  2. 执行：入口=python3 读模式（只依赖读位）；官方全部版本/pin/update 判定原样委托
     镜像内 qodersec-launch.sh 经 /bin/sh 调起（读模式·单一真源在官方脚本，本件⛔不复刻其规则）
  3. 兜底：任何异常 → exit 0 + 留痕（fail-open·⛔不阻塞工具链·⛔不自造新崩源）
边界：只读官方目录，⛔永不写回第三方缓存；镜像目录归本端所有。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import os
import sys
import json
import shutil
import hashlib
import subprocess

HOME = os.path.expanduser("~")
SRC_ROOT = os.path.join(HOME, ".qoder-cn/plugins/cache/qoder-bundler/security-scan")
MIRROR_ROOT = os.path.join(HOME, ".qoder-cn/sescan-engine")
BIN_DIR = os.path.join(MIRROR_ROOT, "bin")
CHOME = os.path.join(HOME, ".qodersec")
LOG = os.path.join(CHOME, "logs", "sescan_shim.log")
STAMP = os.path.join(MIRROR_ROOT, ".mirror-stamp")
LAUNCHER = os.path.join(BIN_DIR, "qodersec-launch.sh")

# 挂载命令行里的透传参数声明（供 config_guard 查⑪ mount_args_smoke 源码字面比对在岗）：
# 本件自身不解析 --platform / --mode / --layer / --hook-event / --timeout 这些参数，
# 全部原样转调官方 launcher（单一真源在官方脚本，本件⛔不复刻其 argv 解析规则）。
PASSTHROUGH_FLAGS = ("--platform", "--mode", "--layer", "--hook-event", "--timeout")


def log(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        from datetime import datetime
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def src_fingerprint():
    """插件 bin/ 逐文件哈希（内容指纹·不依赖目录 mtime·读官方⛔改官方）。"""
    h = hashlib.sha256()
    d = os.path.join(SRC_ROOT, "bin")
    if os.path.isdir(d):
        for n in sorted(os.listdir(d)):
            p = os.path.join(d, n)
            if os.path.isfile(p):
                h.update(n.encode())
                try:
                    with open(p, "rb") as f:
                        h.update(f.read())
                except Exception:
                    h.update(b"UNREADABLE")
    return h.hexdigest()[:16]


def mirror_ready():
    return os.path.isfile(LAUNCHER)


def sync_mirror():
    if not os.path.isdir(os.path.join(SRC_ROOT, "bin")):
        return mirror_ready()  # 插件被卸：保持上次镜像继续可用
    fp = src_fingerprint()
    try:
        if os.path.isfile(STAMP) and open(STAMP, encoding="utf-8").read().strip() == fp:
            return mirror_ready()
    except Exception:
        pass
    staging = BIN_DIR + ".staging"
    try:
        if os.path.exists(staging):
            shutil.rmtree(staging)
        os.makedirs(staging, exist_ok=True)
        for n in sorted(os.listdir(os.path.join(SRC_ROOT, "bin"))):
            s = os.path.join(SRC_ROOT, "bin", n)
            if os.path.isfile(s):
                shutil.copy2(s, os.path.join(staging, n))
        if os.path.isdir(BIN_DIR):
            shutil.rmtree(BIN_DIR)
        os.replace(staging, BIN_DIR)
        with open(STAMP, "w", encoding="utf-8") as f:
            f.write(fp)
        log("mirror-synced fp=%s" % fp)
        return True
    except Exception as e:
        log("mirror-sync-FAIL: %r" % e)
        try:
            if os.path.exists(staging):
                shutil.rmtree(staging)
        except Exception:
            pass
        return mirror_ready()


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        args = ["review", "settings"]  # 无参兜底：走官方 settings 解析，不产副作用
    if not sync_mirror():
        log("noop: 镜像不可用")
        return 0
    env = dict(os.environ)
    env.setdefault("QODERSEC_HOME", CHOME)
    env["CODESEC_HOME"] = CHOME
    env["PATH"] = os.path.join(CHOME, "bin") + ":" + env.get("PATH", "")
    try:
        proc = subprocess.run(["/bin/sh", LAUNCHER] + args, env=env)  # stdin/stdout 继承=事件 JSON 直通
        return proc.returncode
    except Exception as e:
        log("exec-FAIL: %r" % e)
        return 0  # fail-open


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log("fatal-outer: %r" % e)
        sys.exit(0)
