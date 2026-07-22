#!/usr/bin/env python3
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
