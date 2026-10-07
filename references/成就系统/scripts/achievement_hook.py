#!/usr/bin/env python3
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from achievement_tracker import auto_notify
if __name__ == "__main__":
    print("🔍 检测成就解锁...")
    count = auto_notify()
    if count > 0:
        print(f"✅ 解锁了 {count} 个新成就！")
    else:
        print("✅ 暂无新成就")
