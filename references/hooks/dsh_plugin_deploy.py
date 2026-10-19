#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dsh_plugin_deploy.py v1.0 — five-layer-memory 上游源 → DSH 活体 唯一上线通道（抗更新根治·2026-08-25）

背景：插件活体在 ~/.dsh/profiles/web/node_modules/five-layer-memory/，DSH 升级/重装会整体覆盖它；
上游唯一真源在 [记忆共享中心]/脚本中心/five-layer-memory/。此前双头演化曾致"登记✅实盘无"勘误
（T0 twin 只改源未部署）与 5 项修复滞留源端。本脚本收敛为单通道：
    --deploy   备份活体 → 复制 src/index.js + resources/navigator.md → 占位符按机替换 → 机械验证
    --verify   仅机械验证（升级后漂移检测；也可被 twin_distill_watch 巡检联动调用）
验证口径=行为终态（node 动态 import 实跑：模块加载/段注册/twin 在位/切片文件存在），非文件存在性。
退出码：0=PASS，1=FAIL，2=前置缺失。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import json
import shutil
import subprocess
import sys
import os
from datetime import datetime

SRC_DIR = os.path.expanduser("[记忆共享中心]/脚本中心/five-layer-memory")
SRC_JS = os.path.join(SRC_DIR, "src", "index.js")
SRC_NAV = os.path.join(SRC_DIR, "resources", "navigator.md")
DST_DIR = os.path.expanduser("~/.dsh/profiles/web/node_modules/five-layer-memory")
DST_JS = os.path.join(DST_DIR, "src", "index.js")
DST_NAV = os.path.join(DST_DIR, "resources", "navigator.md")
ROOT = os.path.expanduser("~")
# 本机画像文件（setup.sh 探测结果的固化；换机/画像更新时改这一行）
PROFILE_FILE = "2026-07-28-AI观察-你的六画像与四弱点.md"

VERIFY_JS_TEMPLATE = """
import { DEFAULT_SECTIONS } from 'file://%(dst)s';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
const root = %(root)s;
const names = DEFAULT_SECTIONS.map(s => s.name);
const mustHave = ['five-layer-dsh-const', 'five-layer-core', 'five-layer-twin', 'five-layer-twin-l6'];
const missing = mustHave.filter(n => !names.includes(n));
const fileFail = DEFAULT_SECTIONS.filter(s => s.name !== 'five-layer-user' && !existsSync(join(root, s.path))).map(s => s.name);
const userSec = DEFAULT_SECTIONS.find(s => s.name === 'five-layer-user');
const userOk = userSec && !userSec.path.includes('{用户画像文件}') && existsSync(join(root, userSec.path));
if (missing.length || fileFail.length || !userOk) {
  console.log('FAIL missing=' + JSON.stringify(missing) + ' fileFail=' + JSON.stringify(fileFail) + ' userOk=' + userOk);
  process.exit(1);
}
console.log('TWIN-OK sections=' + DEFAULT_SECTIONS.length);
"""


def verify() -> tuple:
    js = VERIFY_JS_TEMPLATE % {"dst": DST_JS, "root": json.dumps(ROOT)}
    p = subprocess.run(["node", "--input-type=module", "-e", js],
                       capture_output=True, text=True, timeout=60)
    out = (p.stdout or "").strip()
    ok = p.returncode == 0 and "TWIN-OK" in out
    return ok, out or (p.stderr or "").strip()[:300]


def main():
    mode = "--verify" if "--verify" in sys.argv else ("--deploy" if "--deploy" in sys.argv else "")
    if mode == "":
        print(__doc__)
        return 2
    if not os.path.isfile(SRC_JS):
        print(f"[FAIL] 上游源缺失: {SRC_JS}")
        return 2

    if mode == "--deploy":
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        for src, dst in [(SRC_JS, DST_JS), (SRC_NAV, DST_NAV)]:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.isfile(dst):
                bak = f"{dst}.bak-{ts}"
                shutil.copy2(dst, bak)
                print(f"[backup] {bak}")
            shutil.copy2(src, dst)
        # 占位符按机替换（镜像 setup.sh sed 语义）
        text = open(DST_JS, encoding="utf-8").read()
        if "{用户画像文件}" in text:
            text = text.replace("{用户画像文件}", PROFILE_FILE)
            open(DST_JS, "w", encoding="utf-8").write(text)
            print(f"[subst] {{用户画像文件}} -> {PROFILE_FILE}")

    ok, detail = verify()
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {mode} @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
