#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成就系统自动检测脚本
- 读取每日日记，提取番茄数/阅读数/日记数/睡眠数据
- 对比成就文件，检测是否达成新成就
- 达成时发送 macOS 系统通知弹窗
- 更新成就文件中的进度和状态

用法：
  python3 achievement_tracker.py              # 检测今日成就
  python3 achievement_tracker.py --all       # 扫描所有日记（全量统计，正式记录+弹窗）
  python3 achievement_tracker.py --date YYYY-MM-DD  # 按日期触发（截止该日，预览+弹窗，不改写存档）
  python3 achievement_tracker.py --status    # 查看当前成就进度
  python3 achievement_tracker.py --sync-memory # 同步成就数据到 MEMORY.md
"""

import os
import re
import json
import subprocess
import platform
import tempfile
import hashlib
from datetime import datetime, date
from pathlib import Path
from glob import glob

# ─── 路径配置 ────────────────────────────────────────────────
DIARY_DIR = Path.home() / "Local_Obsidian_Vault/1-每日计划/01-日记"
ACHIEVEMENT_DIR = Path.home() / "个人AI档案/成就系统"
DATA_FILE = ACHIEVEMENT_DIR / "scripts" / "achievement_data.json"
READING_NOTES_DIR = Path.home() / "Local_Obsidian_Vault/2-知识库/01-读书笔记"
GREATEST_ME_DIR = Path.home() / "个人AI档案/最伟大的我/成就证据"  # 与最伟大的我联动

# ─── 成就定义 ────────────────────────────────────────────────
ACHIEVEMENTS = {

    # 🍅 番茄成就（累计番茄数）
    "tomato": [
        {"id": "tomato_10",    "name": "🌱 专注萌芽-番茄10个",    "threshold": 10,    "level": "🟢 铜牌"},
        {"id": "tomato_30",    "name": "🌿 小试牛刀-番茄30个",    "threshold": 30,    "level": "🟢 铜牌"},
        {"id": "tomato_50",    "name": "🌳 渐入佳境-番茄50个",    "threshold": 50,    "level": "🟢 铜牌"},
        {"id": "tomato_80",    "name": "🍀 番茄新手-番茄80个",    "threshold": 80,    "level": "🟢 铜牌"},
        {"id": "tomato_100",   "name": "🥈 番茄新星-番茄100个",   "threshold": 100,   "level": "🥈 银牌"},
        {"id": "tomato_200",   "name": "🥈 番茄进阶-番茄200个",   "threshold": 200,   "level": "🥈 银牌"},
        {"id": "tomato_300",   "name": "🥈 番茄达人-番茄300个",   "threshold": 300,   "level": "🥈 银牌"},
        {"id": "tomato_400",   "name": "🥈 番茄高手-番茄400个",   "threshold": 400,   "level": "🥈 银牌"},
        {"id": "tomato_500",   "name": "🥈 番茄大师-番茄500个",   "threshold": 500,   "level": "🥈 银牌"},
        {"id": "tomato_700",   "name": "🥈 番茄传奇-番茄700个",   "threshold": 700,   "level": "🥈 银牌"},
        {"id": "tomato_900",   "name": "🥈 番茄宗师-番茄900个",   "threshold": 900,   "level": "🥈 银牌"},
        {"id": "tomato_1000",  "name": "💎 千番茄王者-番茄1000个","threshold": 1000,  "level": "💎 钻石"},
        {"id": "tomato_2000",  "name": "🥇 两千番茄领主-番茄2000个","threshold": 2000, "level": "🥇 金牌"},
        {"id": "tomato_3000",  "name": "🥇 三千番茄尊者-番茄3000个","threshold": 3000, "level": "🥇 金牌"},
        {"id": "tomato_5000",  "name": "🥇 五千番茄帝皇-番茄5000个","threshold": 5000, "level": "🥇 金牌"},
        {"id": "tomato_7000",  "name": "🥇 七千番茄神话-番茄7000个","threshold": 7000, "level": "🥇 金牌"},
        {"id": "tomato_10000", "name": "💎 万番茄大师-番茄10000个",  "threshold": 10000, "level": "💎 钻石"},
        {"id": "tomato_15000", "name": "💎 万五里程碑-番茄15000个",  "threshold": 15000, "level": "💎 钻石"},
        {"id": "tomato_20000", "name": "💎 二万番茄传奇-番茄20000个","threshold": 20000, "level": "💎 钻石"},
        {"id": "tomato_24000", "name": "💎 二万四千王者-番茄24000个 👑 10000小时定律！", "threshold": 24000, "level": "💎 钻石"},
    ],

    # 📚 阅读成就（累计读书数，从成就系统建立后开始计）
    "reading": [
        {"id": "read_1",    "name": "🌱 阅读萌芽",   "threshold": 1,    "level": "🟢 铜牌"},
        {"id": "read_10",   "name": "🌿 十本学者",   "threshold": 10,   "level": "🟢 铜牌"},
        {"id": "read_20",   "name": "🌳 二十本读者", "threshold": 20,   "level": "🟢 铜牌"},
        {"id": "read_30",   "name": "🍀 三十本博学家","threshold": 30,  "level": "🟢 铜牌"},
        {"id": "read_40",   "name": "🥈 四十本专家", "threshold": 40,   "level": "🥈 银牌"},
        {"id": "read_50",   "name": "🥈 五十本达人", "threshold": 50,   "level": "🥈 银牌"},
        {"id": "read_100",  "name": "🥇 百本大师",   "threshold": 100,  "level": "🥇 金牌"},
        {"id": "read_200",  "name": "🥇 两百本专家", "threshold": 200,  "level": "🥇 金牌"},
        {"id": "read_500",  "name": "🥇 五百本达人", "threshold": 500,  "level": "🥇 金牌"},
        {"id": "read_1000", "name": "💎 千本至尊",   "threshold": 1000, "level": "💎 钻石"},
        {"id": "read_5000", "name": "💎 五千本王者", "threshold": 5000, "level": "💎 钻石"},
    ],

    # 📔 日记打卡成就（累计篇数）
    "diary": [
        {"id": "diary_1",   "name": "📝 开始记录-日记1篇",       "threshold": 1,    "level": "🟢 铜牌"},
        {"id": "diary_10",  "name": "📓 习惯养成-日记10篇",       "threshold": 10,   "level": "🟢 铜牌"},
        {"id": "diary_20",  "name": "📒 执笔不辍-日记20篇",       "threshold": 20,   "level": "🟢 铜牌"},
        {"id": "diary_30",  "name": "📚 月记满月-日记30篇",       "threshold": 30,   "level": "🟢 铜牌"},
        {"id": "diary_50",  "name": "✍️ 半百笔耕-日记50篇",       "threshold": 50,   "level": "🥈 银牌"},
        {"id": "diary_100", "name": "📖 百篇文人-日记100篇",      "threshold": 100,  "level": "🥈 银牌"},
        {"id": "diary_200", "name": "📜 两百春秋-日记200篇",      "threshold": 200,  "level": "🥇 金牌"},
        {"id": "diary_365", "name": "🗓️ 一年365天-日记365篇",    "threshold": 365,  "level": "🥇 金牌"},
        {"id": "diary_500", "name": "🏛️ 五百篇殿堂-日记500篇",   "threshold": 500,  "level": "💎 钻石"},
        {"id": "diary_1000","name": "👑 千篇传奇-日记1000篇",     "threshold": 1000, "level": "💎 钻石"},
    ],

    # 😴 早睡成就（累计23:30前入睡天数）
    "sleep_early": [
        {"id": "sleep_1",   "name": "🌙 第一次早睡-早睡1天",      "threshold": 1,    "level": "🟢 铜牌"},
        {"id": "sleep_3",   "name": "😴 连续3天安眠-早睡3天",     "threshold": 3,    "level": "🟢 铜牌"},
        {"id": "sleep_7",   "name": "🛏️ 一周好眠-早睡7天",       "threshold": 7,    "level": "🟢 铜牌"},
        {"id": "sleep_15",  "name": "🌟 半月安眠达人-早睡15天",   "threshold": 15,   "level": "🟢 铜牌"},
        {"id": "sleep_30",  "name": "🌙 早睡一个月-早睡30天",    "threshold": 30,   "level": "🥈 银牌"},
        {"id": "sleep_60",  "name": "💤 两个月睡神-早睡60天",    "threshold": 60,   "level": "🥈 银牌"},
        {"id": "sleep_90",  "name": "🏆 季度安眠冠军-早睡90天",   "threshold": 90,   "level": "🥈 银牌"},
        {"id": "sleep_180", "name": "👑 半年养生大师-早睡180天", "threshold": 180,  "level": "🥇 金牌"},
        {"id": "sleep_365", "name": "🌟 一年365个好觉-早睡365天", "threshold": 365,  "level": "🥇 金牌"},
        {"id": "sleep_1000","name": "♾️ 千夜安眠传奇-早睡1000天", "threshold": 1000, "level": "💎 钻石"},
    ],

    # 🌙 月亮之子成就-连续熬夜里程碑（单位：1天，共6个解锁点）
    "consecutive_late": [
        {"id": "late_3",   "name": "🦉 夜猫子-连续熬夜3天",    "threshold": 3,   "level": "🟢 铜牌"},
        {"id": "late_5",   "name": "💀 熬夜达人-连续熬夜5天",  "threshold": 5,   "level": "🟢 铜牌"},
        {"id": "late_7",   "name": "🧟 僵尸模式-连续熬夜7天",  "threshold": 7,   "level": "🟢 铜牌"},
        {"id": "late_14",  "name": "🌑 月亮之子-连续熬夜14天", "threshold": 14,  "level": "🥇 金牌"},
        {"id": "late_21",  "name": "☠️ 肝帝-连续熬夜21天",    "threshold": 21,  "level": "🥇 金牌"},
        {"id": "late_30",  "name": "💀 死神眷顾-连续熬夜30天","threshold": 30,  "level": "🥇 金牌"},
    ],

    # 🌙 连续熬夜每日等级表（1-30天全覆盖，每1天一个称号+负面反馈）
    # 用途：日记显示，给用户每天的负面反馈
    # 格式：天数 → (emoji, 称号, 台词警告)
    "consecutive_late_daily": {
        1:  ("🌙", "夜幕初窥", "夜色温柔，但明天会后悔"),
        2:  ("🌘", "月影随行", "两天了，黑眼圈开始蓄力"),
        3:  ("🦉", "夜猫子", "月亮是你的太阳——🦉夜猫子成就解锁！"),
        4:  ("🦇", "蝙蝠候补", "四天没见太阳，你在进化成蝙蝠吗"),
        5:  ("💀", "熬夜达人", "凌晨三点是早晨——💀熬夜达人成就解锁！"),
        6:  ("🕷️", "暗网行者", "六天了，你的肝正在写辞职信"),
        7:  ("🧟", "僵尸模式", "睡眠？不需要的——🧟僵尸模式成就解锁！"),
        8:  ("⚰️", "棺材板压不住了", "八天，再熬下去棺材板快按不住了"),
        9:  ("👻", "幽灵预科", "九天，你走路已经开始飘了"),
        10: ("☁️", "云雾行者", "十天，大脑已经变成浆糊了"),
        11: ("🌫️", "迷雾之灵", "十一天，分不清现实和梦境了吗"),
        12: ("🕳️", "深渊边缘", "十二天，深渊在向你招手"),
        13: ("🔥", "烛火将熄", "十三天，生命之火在摇曳"),
        14: ("🌑", "月亮之子", "黑夜之王——🌑月亮之子成就解锁！致敬杰伦"),
        15: ("🌚", "黑暗支配者", "十五天，你已经完全适应了没有阳光的生活"),
        16: ("💫", "星尘残骸", "十六天，你的肉体正在化为星尘"),
        17: ("❄️", "寒冰尸身", "十七天，体温和情感一起流失"),
        18: ("🌀", "虚空漩涡", "十八天，存在感正在被吞噬"),
        19: ("⛓️", "枷锁加身", "十九天，熬夜已成枷锁"),
        20: ("☠️", "肝帝预备役", "二十天，肝？那是什么东西"),
        21: ("☠️", "肝帝", "肝？已经没有了——☠️肝帝成就解锁！"),
        22: ("🪦", "墓地常客", "二十二天，墓地门口有你专属座位"),
        23: ("🦴", "骨架惊现", "二十三天，照镜子能看到骨头了"),
        24: ("🗿", "石像传说", "二十四天，你已经石化了"),
        25: ("🔮", "亡灵法师", "二十五天，你在用生命力施法"),
        26: ("⚡", "雷劫将至", "二十六天，天道好轮回"),
        27: ("🌊", "沉入深海", "二十七天，彻底沉没"),
        28: ("🎭", "死神mimic", "二十八天，死神开始模仿你的样子"),
        29: ("⏳", "沙漏将尽", "二十九天，倒计时中"),
        30: ("💀", "死神眷顾", "死神在敲门——💀死神眷顾成就解锁！"),
    },
    
    # 🌙 月亮之子成就-累计熬夜（单位：5天）
    "total_late": [
        {"id": "late_5t",   "name": "🌙 熬夜学徒-累计熬夜5天",      "threshold": 5,   "level": "🟢 铜牌"},
        {"id": "late_10t",  "name": "🦇 蝙蝠侠-累计熬夜10天",     "threshold": 10,  "level": "🟢 铜牌"},
        {"id": "late_15t",  "name": "👻 幽灵行者-累计熬夜15天",   "threshold": 15,  "level": "🟢 铜牌"},
        {"id": "late_20t",  "name": "🖤 永夜守护者-累计熬夜20天", "threshold": 20,  "level": "🥈 银牌"},
        {"id": "late_25t",  "name": "🌑 月亮领主-累计熬夜25天",  "threshold": 25,  "level": "🥈 银牌"},
        {"id": "late_30t",  "name": "💀 死神眷顾-累计熬夜30天",  "threshold": 30,  "level": "🥈 银牌"},
        {"id": "late_35t",  "name": "☠️ 不死族-累计熬夜35天",    "threshold": 35,  "level": "🥇 金牌"},
        {"id": "late_40t",  "name": "💀 死神契约-累计熬夜40天",  "threshold": 40,  "level": "🥇 金牌"},
        # ↓ 扩展至 300 天（2026-07-16，5天1碑·反向轨高频负激励·52碑）
        # 段一：暗夜渐深（45–70）
        {"id": "late_45t",  "name": "🦴 白骨露野-累计熬夜45天",     "threshold": 45,  "level": "🥇 金牌"},
        {"id": "late_50t",  "name": "🩸 半百血月-累计熬夜50天",     "threshold": 50,  "level": "🥇 金牌"},
        {"id": "late_55t",  "name": "⛓️ 锁链已成习惯-累计熬夜55天",   "threshold": 55,  "level": "🥇 金牌"},
        {"id": "late_60t",  "name": "👁️ 六十度黑-累计熬夜60天",     "threshold": 60,  "level": "🥇 金牌"},
        {"id": "late_65t",  "name": "⚰️ 棺材铺常客-累计熬夜65天",    "threshold": 65,  "level": "🥇 金牌"},
        {"id": "late_70t",  "name": "🌑 七十永夜-累计熬夜70天",     "threshold": 70,  "level": "🥇 金牌"},
        # 段二：冥灯引路（75–100）
        {"id": "late_75t",  "name": "🪦 冥灯长明-累计熬夜75天",     "threshold": 75,  "level": "🥇 金牌"},
        {"id": "late_80t",  "name": "💀 阎王点名-累计熬夜80天",     "threshold": 80,  "level": "🥇 金牌"},
        {"id": "late_85t",  "name": "🕯️ 烛火将熄-累计熬夜85天",     "threshold": 85,  "level": "🥇 金牌"},
        {"id": "late_90t",  "name": "👻 九十幽冥-累计熬夜90天",     "threshold": 90,  "level": "🥇 金牌"},
        {"id": "late_95t",  "name": "⏳ 倒数破百-累计熬夜95天",     "threshold": 95,  "level": "🥇 金牌"},
        {"id": "late_100t","name": "💯 百夜成魔-累计熬夜100天",    "threshold": 100, "level": "🥇 金牌"},
        # 段三：深渊凝视（105–130）
        {"id": "late_105t","name": "🕳️ 深渊回望-累计熬夜105天",    "threshold": 105, "level": "🥇 金牌"},
        {"id": "late_110t","name": "🕸️ 蛛网覆面-累计熬夜110天",    "threshold": 110, "level": "🥇 金牌"},
        {"id": "late_115t","name": "🎭 面具有裂-累计熬夜115天",    "threshold": 115, "level": "🥇 金牌"},
        {"id": "late_120t","name": "🌘 残月不升-累计熬夜120天",    "threshold": 120, "level": "🥇 金牌"},
        {"id": "late_125t","name": "💉 血条见底-累计熬夜125天",    "threshold": 125, "level": "🥇 金牌"},
        {"id": "late_130t","name": "🕰️ 生物钟已废-累计熬夜130天",  "threshold": 130, "level": "🥇 金牌"},
        # 段四：判官册（135–175）
        {"id": "late_135t","name": "📜 判官落笔-累计熬夜135天",    "threshold": 135, "level": "🥇 金牌"},
        {"id": "late_140t","name": "🩻 骷髅显形-累计熬夜140天",    "threshold": 140, "level": "🥇 金牌"},
        {"id": "late_145t","name": "🪤 陷阱已深-累计熬夜145天",    "threshold": 145, "level": "🥇 金牌"},
        {"id": "late_150t","name": "🧛 半千吸血鬼-累计熬夜150天",  "threshold": 150, "level": "🥇 金牌"},
        {"id": "late_155t","name": "🐺 夜狼化-累计熬夜155天",     "threshold": 155, "level": "🥇 金牌"},
        {"id": "late_160t","name": "🧟 僵尸领主-累计熬夜160天",    "threshold": 160, "level": "🥇 金牌"},
        {"id": "late_165t","name": "🪐 暗星轨道-累计熬夜165天",    "threshold": 165, "level": "🥇 金牌"},
        {"id": "late_170t","name": "📿 念珠断线-累计熬夜170天",    "threshold": 170, "level": "🥇 金牌"},
        {"id": "late_175t","name": "⛩️ 冥界前哨-累计熬夜175天",    "threshold": 175, "level": "🥇 金牌"},
        # 段五：夜王加冕（180–230）
        {"id": "late_180t","name": "👑 夜王初冠-累计熬夜180天",    "threshold": 180, "level": "🥇 金牌"},
        {"id": "late_185t","name": "🕯️ 第185根蜡烛-累计熬夜185天", "threshold": 185, "level": "🥇 金牌"},
        {"id": "late_190t","name": "🎻 安魂曲序章-累计熬夜190天",  "threshold": 190, "level": "🥇 金牌"},
        {"id": "late_195t","name": "🪞 镜已无影-累计熬夜195天",    "threshold": 195, "level": "🥇 金牌"},
        {"id": "late_200t","name": "🌌 双百夜王-累计熬夜200天",    "threshold": 200, "level": "🏆 钻石"},
        {"id": "late_205t","name": "🔪 斩不断的夜-累计熬夜205天",  "threshold": 205, "level": "🏆 钻石"},
        {"id": "late_210t","name": "🩸 日已无温-累计熬夜210天",    "threshold": 210, "level": "🏆 钻石"},
        {"id": "late_215t","name": "🦴 白昼畏光-累计熬夜215天",    "threshold": 215, "level": "🏆 钻石"},
        {"id": "late_220t","name": "🎭 死神微笑-累计熬夜220天",    "threshold": 220, "level": "🏆 钻石"},
        {"id": "late_225t","name": "⚰️ 量身已定-累计熬夜225天",    "threshold": 225, "level": "🏆 钻石"},
        {"id": "late_230t","name": "💀 判词已下-累计熬夜230天",    "threshold": 230, "level": "🏆 钻石"},
        # 段六：永夜尽头（235–300）
        {"id": "late_235t","name": "🌋 夜火山口-累计熬夜235天",    "threshold": 235, "level": "🏆 钻石"},
        {"id": "late_240t","name": "🫀 昼夜倒悬-累计熬夜240天",    "threshold": 240, "level": "🏆 钻石"},
        {"id": "late_245t","name": "🔮 预言应验-累计熬夜245天",    "threshold": 245, "level": "🏆 钻石"},
        {"id": "late_250t","name": "👁️ 全夜无眠-累计熬夜250天",    "threshold": 250, "level": "🏆 钻石"},
        {"id": "late_255t","name": "💀 死神老友-累计熬夜255天",    "threshold": 255, "level": "🏆 钻石"},
        {"id": "late_260t","name": "🪐 永暗行星-累计熬夜260天",    "threshold": 260, "level": "🏆 钻石"},
        {"id": "late_265t","name": "🖤 黑暗已入骨-累计熬夜265天",  "threshold": 265, "level": "🏆 钻石"},
        {"id": "late_270t","name": "🌑 九成暗夜率-累计熬夜270天",  "threshold": 270, "level": "🏆 钻石"},
        {"id": "late_275t","name": "⏳ 倒数永夜-累计熬夜275天",    "threshold": 275, "level": "🏆 钻石"},
        {"id": "late_280t","name": "🦇 昼伏夜出已定型-累计熬夜280天","threshold": 280,"level": "🏆 钻石"},
        {"id": "late_285t","name": "🧬 DNA已改写-累计熬夜285天",   "threshold": 285, "level": "🏆 钻石"},
        {"id": "late_290t","name": "💀 阎王已习惯-累计熬夜290天",  "threshold": 290, "level": "🏆 钻石"},
        {"id": "late_295t","name": "⚰️ 万事俱备-累计熬夜295天",    "threshold": 295, "level": "🏆 钻石"},
        {"id": "late_300t","name": "🖤 夜神本神-累计熬夜300天",    "threshold": 300, "level": "💎 钻石"},
    ],
    
    # 🌅 早起成就（累计07:30前起床天数）
    "wake_early": [
        {"id": "wake_1",   "name": "🌅 第一次早起-早起1天",       "threshold": 1,    "level": "🟢 铜牌"},
        {"id": "wake_3",   "name": "☀️ 连续3天追光-早起3天",      "threshold": 3,    "level": "🟢 铜牌"},
        {"id": "wake_7",   "name": "🌄 一周追光者-早起7天",       "threshold": 7,    "level": "🟢 铜牌"},
        {"id": "wake_15",  "name": "🎯 半月迎光达人-早起15天",    "threshold": 15,   "level": "🟢 铜牌"},
        {"id": "wake_30",  "name": "🌅 一个月追光者-早起30天",    "threshold": 30,   "level": "🥈 银牌"},
        {"id": "wake_60",  "name": "☀️ 两个月日出猎人-早起60天",  "threshold": 60,   "level": "🥈 银牌"},
        {"id": "wake_90",  "name": "🏆 季度迎光冠军-早起90天",    "threshold": 90,   "level": "🥈 银牌"},
        {"id": "wake_180", "name": "👑 半年晨光大师-早起180天",   "threshold": 180,  "level": "🥇 金牌"},
        {"id": "wake_365", "name": "🌟 一年365个晨光-早起365天",  "threshold": 365,  "level": "🥇 金牌"},
        {"id": "wake_1000","name": "♾️ 千晨光传奇-早起1000天",    "threshold": 1000, "level": "💎 钻石"},
    ],
}

# ─── 通知函数 ────────────────────────────────────────────────
def send_notification(title, message, subtitle=None):
    """发送 macOS 系统通知"""
    if platform.system() != "Darwin":
        print(f"[通知] {title}: {message}")
        return
    script = f'display notification "{message}" with title "{title}"'
    if subtitle:
        script += f' subtitle "{subtitle}"'
    script += ' sound name "Glass"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def send_achievement_notification(achievement, value):
    """发送成就解锁对话框弹窗"""
    import subprocess
    print(f"\n{'='*50}")
    print(f"  🎉 成就解锁！")
    print(f"  {achievement['name']}")
    print(f"  {achievement['level']}  |  达成值：{value}")
    print(f"{'='*50}\n")
    if platform.system() == "Darwin":
        # 【2026-04-19】改Popen为run：确保弹框显示，等用户点OK才继续
        subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"])
        ach_name = achievement["name"]
        ach_level = achievement["level"]
        script = f'tell app "System Events" to display dialog "{ach_name}\\n\\n{ach_level} | 达成值：{value}天" with title "🎉 成就解锁！" buttons {{"OK"}} default button "OK" with icon note giving up after 60'
        subprocess.run(["osascript", "-e", script])  # 阻塞等待用户点击
    elif platform.system() == "Windows":
        # 【2026-07-07】Windows 模态弹窗 + 系统提示音（点击式，等价 macOS display dialog）
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"{achievement['name']}\n\n{achievement['level']} | 达成值：{value}天",
                "🎉 成就解锁！",
                0,
            )
        except Exception:
            pass


# ─── 最伟大的我联动 ──────────────────────────────────────────
def sync_to_greatest_me(achievement, value):
    """成就解锁时自动写入 最伟大的我/成就证据/
    
    幂等：同名文件已存在则不重复写入
    格式：{YYYY-MM-DD}-{achievement_id}.md
    """
    today = date.today().strftime("%Y-%m-%d")
    safe_id = achievement["id"].replace("/", "-").replace(" ", "-")
    evidence_file = GREATEST_ME_DIR / f"{today}-{safe_id}.md"
    
    if evidence_file.exists():
        print(f"  ⏭️ 成就证据已存在：{evidence_file.name}")
        return
    
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    
    content = f"""# 成就证据 · {achievement['name']}

- **达成日期**：{today}
- **成就ID**：{achievement['id']}
- **等级**：{achievement['level']}
- **达成值**：{value}
- **来源**：成就系统自动检测

---

{achievement['name']}

> 由 `achievement_tracker.py` 自动写入最伟大的我·成就证据
"""
    evidence_file.write_text(content, encoding="utf-8")
    print(f"  ✅ 已写入最伟大的我/成就证据/{evidence_file.name}")


# ─── 数据读取 ────────────────────────────────────────────────
def _extract_yaml_achievement_data(content):
    """从日记的YAML frontmatter中提取achievement_data块
    
    返回dict：{tomato: X.X, sleep_time: "HH:MM", wake_time: "HH:MM"}
    或None（如果不存在/解析失败）
    """
    import yaml
    # 提取 --- 包裹的frontmatter
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return None
    try:
        frontmatter = yaml.safe_load(m.group(1))
        if isinstance(frontmatter, dict) and "achievement_data" in frontmatter:
            return frontmatter["achievement_data"]
    except (yaml.YAMLError, TypeError):
        pass
    return None


def load_data():
    """读取本地成就数据"""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "tomato_total": 0,
        "reading_total": 3,       # 从成就系统建立后：《咸的玩笑》《卢浮宫的猫》《再见绘梨》
        "diary_total": 0,
        "diary_streak_current": 0,
        "diary_streak_max": 0,
        "sleep_early_total": 0,   # 累计23:30前入睡天数
        "wake_early_total": 0,    # 累计07:30前起床天数
        "unlocked": [],           # 已解锁成就ID列表
        "last_updated": "",
    }


def increment_tomato(count=1):
    """安全累加番茄数（并发安全）
    
    用途：多个龙虾同时完成任务时，避免数据丢失
    策略：
    1. 读取最新数据（而非缓存）
    2. 原子增加番茄数
    3. 记录贡献者
    """
    data = load_data()
    data["tomato_total"] = data.get("tomato_total", 0) + count
    
    # 记录贡献者
    agent_id = os.environ.get("AGENT_NAME", "unknown")
    if "contributors" not in data:
        data["contributors"] = {}
    data["contributors"][agent_id] = data["contributors"].get(agent_id, 0) + count
    
    save_data(data)
    return data["tomato_total"]


def save_data(data):
    """保存成就数据（并发安全版本）
    
    改进点：
    1. 原子写入：临时文件+rename（防止文件损坏）
    2. 版本号：乐观锁机制（检测并发冲突）
    3. 贡献追踪：记录哪个龙虾写入了数据
    """
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取当前版本号（如果存在）
    current_version = 0
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
                current_version = existing.get("version", 0)
        except:
            pass
    
    # 更新版本号和元数据
    data["version"] = current_version + 1
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 记录写入者（从环境变量或默认值获取）
    agent_id = os.environ.get("AGENT_NAME", "unknown")
    data["last_writer"] = agent_id
    
    # 初始化贡献者字典（如果不存在）
    if "contributors" not in data:
        data["contributors"] = {}
    
    # 原子写入：先写临时文件，再rename
    temp_fd, temp_path = tempfile.mkstemp(
        dir=DATA_FILE.parent,
        prefix=".achievement_tmp_",
        suffix=".json"
    )
    
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 原子rename（POSIX保证原子性）
        os.replace(temp_path, DATA_FILE)
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise e


def parse_diary_file(filepath):
    """解析单个日记文件，提取番茄数/睡眠数据/三分维度
    
    读取优先级（2026-04-06升级）：
    1. YAML frontmatter 的 achievement_data 块（结构化，可靠）
    2. 正文正则提取（兼容旧日记无YAML的情况）
    """
    result = {
        "tomato": 0, "sleep_time": None, "wake_time": None, "has_diary": True,
        # v2.0 YAML 12字段新增（2026-06-24）
        "sleep_duration": None, "sleep_quality": None,
        "energy_pred": None, "energy_actual": None,
        "calm_pred": None, "calm_actual": None,
        "satisfaction": None, "physiological": None,
    }
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # ─── 方式1：优先从YAML frontmatter的achievement_data读取 ───
        yaml_data = _extract_yaml_achievement_data(content)
        if yaml_data:
            yaml_tomato = yaml_data.get("tomato")
            yaml_sleep = yaml_data.get("sleep_time")
            yaml_wake = yaml_data.get("wake_time")
            # 老3字段：非零值信任YAML，零值不短路让regex fallback补（回填脚本给旧日记设了0）
            has_trusted_yaml = bool(yaml_tomato and yaml_tomato != 0)
            if has_trusted_yaml:
                result["tomato"] = float(yaml_tomato)
            if yaml_sleep and yaml_sleep != 0:
                result["sleep_time"] = yaml_sleep
            if yaml_wake and yaml_wake != 0:
                result["wake_time"] = yaml_wake
            # 新8字段：回填后必然存在，直接信任YAML
            if yaml_data.get("sleep_duration") is not None and yaml_data["sleep_duration"] != 0:
                result["sleep_duration"] = float(yaml_data["sleep_duration"])
            if yaml_data.get("sleep_quality"):
                result["sleep_quality"] = yaml_data["sleep_quality"]
            if yaml_data.get("energy_pred") is not None and yaml_data["energy_pred"] != 0:
                result["energy_pred"] = int(yaml_data["energy_pred"])
            if yaml_data.get("energy_actual") is not None and yaml_data["energy_actual"] != 0:
                result["energy_actual"] = int(yaml_data["energy_actual"])
            if yaml_data.get("calm_pred") is not None and yaml_data["calm_pred"] != 0:
                result["calm_pred"] = int(yaml_data["calm_pred"])
            if yaml_data.get("calm_actual") is not None and yaml_data["calm_actual"] != 0:
                result["calm_actual"] = int(yaml_data["calm_actual"])
            if yaml_data.get("satisfaction") is not None and yaml_data["satisfaction"] != 0:
                result["satisfaction"] = int(yaml_data["satisfaction"])
            if yaml_data.get("physiological"):
                result["physiological"] = yaml_data["physiological"]
            # 信任YAML番茄→短路；否则fallthrough到regex
            if has_trusted_yaml:
                return result

        # ─── 方式2：Fallback到正文正则提取（仅用于无YAML的旧日记）────

        # ─── 方式2：Fallback到正文正则提取（兼容旧日记）────
        # 提取实际番茄数（多种格式兼容）
        # 0. 优先从"今日番茄累计"行提取（新版日记格式，2026-05起）
        #    兼容：今日番茄：2🍅 / 今日番茄累计：~8🍅 / 今日番茄累计：**14🍅**
        m = re.search(r"-?\s*今日番茄(?:累计)?[：:]\s*~?\*{0,2}(\d+(?:\.\d+)?)\*{0,2}\s*🍅", content)
        if not m:
            # 1. 从"今日实际"行提取
            m = re.search(r"\*{0,2}今日实际\*{0,2}[：:]?\s*(\d+(?:\.\d+)?)\s*🍅", content)
        if not m:
            # 1.5. 从"总实际"行提取（3月日记常用格式）
            m = re.search(r"\*{0,2}总实际\*{0,2}[：:]?\s*(?:约\s*)?(\d+(?:\.\d+)?)\s*🍅", content)
        if not m:
            # 1.6. 从"实际完成番茄总数**：X🍅"提取（优先）
            m = re.search(r"实际完成番茄总数[*]+[：:]\s*(\d+(?:\.\d+)?)\s*🍅", content)
        if not m:
            # 1.7. 从"番茄总数**：X🍅"提取（4月新格式，**在冒号前）
            m = re.search(r"番茄总数[*]+[：:]\s*(\d+(?:\.\d+)?)\s*🍅", content)
        if not m:
            # 1.8. 从"计划番茄总数：X🍅"提取（备用）
            m = re.search(r"计划番茄总数[：:]\s*(\d+(?:\.\d+)?)\s*🍅", content)
        if m:
            result["tomato"] = float(m.group(1))
        else:
            # 2. 从"实际执行"行提取
            m = re.search(r"\*{0,2}实际执行\*{0,2}[：:]\s*(\d+(?:\.\d+)?)\s*🍅", content)
            if m:
                result["tomato"] = float(m.group(1))
            else:
                # 3. 从任务表格提取 ✅ 行的实际番茄数
                # 新格式：| 时间 | 任务类型 | 优先级 | 任务目标 | 预计番茄 | 实际番茄 | 完成状态 |
                tomato_sum = 0
                for row in re.finditer(r"\|\s*[^|]+\s*\|\s*[^|]+\s*\|\s*P\d\s*\|\s*[^|]*\s*\|\s*[^|]*\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*✅", content):
                    tomato_sum += float(row.group(1))
                if tomato_sum > 0:
                    result["tomato"] = tomato_sum

        # 提取入睡时间（从睡眠表格 - 限定在SLEEP SECTION内）
        # 【2026-04-19修复】先定位到SLEEP SECTION，再提取表格第一行的时间
        sleep_section_match = re.search(r"<!-- SECTION: SLEEP -->(.+?)(?=<!-- SECTION:|$)", content, re.DOTALL)
        if sleep_section_match:
            sleep_section = sleep_section_match.group(1)
            # 在睡眠模块内找表格第一行数据（跳过表头）
            # 匹配 | 入睡时间 | 起床时间 | ... | 格式
            m = re.search(r"\|\s*(\d{1,2}:\d{2})\s*\|\s*(\d{1,2}:\d{2})\s*\|", sleep_section)
            if m:
                result["sleep_time"] = m.group(1)
                result["wake_time"] = m.group(2)
        else:
            # Fallback：旧格式无SECTION标记，从任意表格提取（保持兼容）
            m = re.search(r"\|\s*(\d{1,2}:\d{2})\s*\|\s*\d{1,2}:\d{2}\s*\|", content)
            if m:
                result["sleep_time"] = m.group(1)
            m = re.search(r"\|\s*\d{1,2}:\d{2}\s*\|\s*(\d{1,2}:\d{2})\s*\|", content)
            if m:
                result["wake_time"] = m.group(1)

    except Exception as e:
        print(f"解析 {filepath} 失败: {e}")
    return result


def scan_all_diaries(cutoff=None):
    """扫描所有日记，统计全量数据。cutoff='YYYY-MM-DD' 时只统计该日期及之前的日记。"""
    files = sorted(glob(str(DIARY_DIR / "**" / "2026-*.md"), recursive=True))
    if cutoff:
        from datetime import datetime as _dt
        try:
            cutoff_d = _dt.strptime(cutoff, "%Y-%m-%d").date()
        except ValueError:
            print(f"⚠️ 日期格式错误：{cutoff}，应为 YYYY-MM-DD，已忽略日期过滤")
            cutoff = None
    if cutoff:
        filtered = []
        for f in files:
            stem = Path(f).stem
            try:
                fd = _dt.strptime(stem, "%Y-%m-%d").date()
                if fd <= cutoff_d:
                    filtered.append(f)
            except ValueError:
                continue
        files = filtered
    total_tomato = 0
    sleep_early_days = 0
    wake_early_days = 0
    diary_count = 0
    reading_count = 0

    # 逐日累加计算番茄总数（更可靠）
    # 删除直接读取"当前累计"的逻辑，改为逐日累加

    for f in files:
        # 修复：将字符串路径转换为 Path 对象
        f_path = Path(f)
        if "备份" in f_path.name:
            continue
        data = parse_diary_file(f)
        diary_count += 1
        total_tomato += data["tomato"]  # 累加每日番茄

        # 早睡判断：23:30前入睡
        if data["sleep_time"]:
            st = str(data["sleep_time"])
            if ":" in st:
                h, m = map(int, st.split(":"))
            else:
                h, m = int(st) // 60, int(st) % 60
            total_minutes = h * 60 + m
            if total_minutes <= 23 * 60 + 30:
                sleep_early_days += 1

        # 早起判断：07:30前起床
        if data["wake_time"]:
            wt = str(data["wake_time"])
            if ":" in wt:
                h, m = map(int, wt.split(":"))
            else:
                h, m = int(wt) // 60, int(wt) % 60
            total_minutes = h * 60 + m
            if total_minutes <= 7 * 60 + 30:
                wake_early_days += 1

    # 阅读数量：手动维护（从日记中累计）
    # 2026年已读：8本（《卢浮宫的猫》上下集、《再见绘梨》、《咸的玩笑》、《青之芦苇》1-5卷）
    reading_count = 9

    # 暗黑之子成就计算（熬夜判断：入睡时间 > 00:00）
    # 按日期升序排序（3/12 → 4/12），从旧到新遍历
    from datetime import timedelta
    sorted_files = sorted(files)
    consecutive_late_nights = 0
    max_consecutive_late = 0
    total_late_nights = 0
    prev_date = None

    # v2.0 新字段聚合（2026-06-24）
    sleep_quality_counts = {"A": 0, "B": 0, "C": 0}
    energy_pred_actual_pairs = []  # [(pred, actual), ...]
    calm_pred_actual_pairs = []
    satisfaction_values = []
    physiological_counts = {"green": 0, "yellow": 0, "red": 0}

    for f in sorted_files:
        # 修复：将字符串路径转换为 Path 对象
        f_path = Path(f)
        if "备份" in str(f_path):
            continue
        data = parse_diary_file(f)
        
        # v2.0 新字段统计
        if data.get("sleep_quality"):
            sleep_quality_counts[data["sleep_quality"]] = sleep_quality_counts.get(data["sleep_quality"], 0) + 1
        if data.get("energy_pred") is not None and data.get("energy_actual") is not None:
            energy_pred_actual_pairs.append((data["energy_pred"], data["energy_actual"]))
        if data.get("calm_pred") is not None and data.get("calm_actual") is not None:
            calm_pred_actual_pairs.append((data["calm_pred"], data["calm_actual"]))
        if data.get("satisfaction") is not None:
            satisfaction_values.append(data["satisfaction"])
        if data.get("physiological"):
            physiological_counts[data["physiological"]] = physiological_counts.get(data["physiological"], 0) + 1
        
        if data["sleep_time"]:
            st = str(data["sleep_time"])
            if ":" in st:
                h, m = map(int, st.split(":"))
            else:
                h, m = int(st) // 60, int(st) % 60
            # 【2026-04-19修复】熬夜判断：入睡时间在 00:00-06:00 之间算熬夜
            # 23:40(晚上11点)不算熬夜，00:30/01:00/02:30(凌晨)算熬夜
            sleep_minutes = h * 60 + m
            if 0 <= sleep_minutes < 360:  # 00:00 - 06:00
                total_late_nights += 1
                try:
                    import re
                    # 提取文件名中的日期
                    fname = f_path.name if hasattr(f_path, 'name') else str(f_path)
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
                    curr_date = date.fromisoformat(match.group(1)) if match else None
                except:
                    curr_date = None

                if prev_date and curr_date and (curr_date - prev_date) == timedelta(days=1):
                    # 日期差=1天，连续计数+1
                    consecutive_late_nights += 1
                elif not prev_date:
                    consecutive_late_nights = 1
                else:
                    # 中断（间隔>1天），重新开始
                    consecutive_late_nights = 1
                max_consecutive_late = max(max_consecutive_late, consecutive_late_nights)
                prev_date = curr_date
            else:
                # 正常睡眠，打破当前连续段
                consecutive_late_nights = 0
                prev_date = None

    # 连续熬夜取历史最大值（跨多个连续段）
    consecutive_late_nights = max_consecutive_late

    # v2.1 连续日记天数统计（基于文件名日期，真实值非估算）
    import re as _re
    from datetime import date as _date, timedelta as _timedelta
    diary_dates = []
    for f in files:
        f_path = Path(f)
        if "备份" in f_path.name:
            continue
        m = _re.search(r'(\d{4}-\d{2}-\d{2})', f_path.name)
        if m:
            try:
                diary_dates.append(_date.fromisoformat(m.group(1)))
            except ValueError:
                pass
    diary_dates = sorted(set(diary_dates))
    diary_streak_current = 0
    diary_streak_max = 0
    if diary_dates:
        # 计算历史最长连续段
        _streak = 1
        _max = 1
        for i in range(1, len(diary_dates)):
            if (diary_dates[i] - diary_dates[i-1]) == _timedelta(days=1):
                _streak += 1
                _max = max(_max, _streak)
            else:
                _streak = 1
        diary_streak_max = _max
        # 计算当前连续段（从最后一篇往前数）
        today = _date.today()
        last = diary_dates[-1]
        # 如果最后一篇是今天或昨天才算当前连续（允许今天还没写）
        if (today - last).days <= 1:
            _cur = 1
            for i in range(len(diary_dates)-1, 0, -1):
                if (diary_dates[i] - diary_dates[i-1]) == _timedelta(days=1):
                    _cur += 1
                else:
                    break
            diary_streak_current = _cur
        else:
            diary_streak_current = 0

    # v2.0 计算衍生指标
    energy_accuracy = 0.0
    energy_bias = "N/A"
    if energy_pred_actual_pairs:
        correct = sum(1 for p, a in energy_pred_actual_pairs if p == a)
        energy_accuracy = round(correct / len(energy_pred_actual_pairs) * 100, 1)
        over_count = sum(1 for p, a in energy_pred_actual_pairs if p > a)
        under_count = sum(1 for p, a in energy_pred_actual_pairs if p < a)
        if over_count > under_count:
            energy_bias = "高估"
        elif under_count > over_count:
            energy_bias = "低估"
        else:
            energy_bias = "平衡"
    
    calm_accuracy = 0.0
    if calm_pred_actual_pairs:
        correct = sum(1 for p, a in calm_pred_actual_pairs if p == a)
        calm_accuracy = round(correct / len(calm_pred_actual_pairs) * 100, 1)
    
    avg_satisfaction = round(sum(satisfaction_values) / len(satisfaction_values), 1) if satisfaction_values else 0.0

    return {
        "tomato_total": round(total_tomato, 1),
        "diary_total": diary_count,
        "sleep_early_total": sleep_early_days,
        "wake_early_total": wake_early_days,
        "reading_total": reading_count,
        "consecutive_late_nights": consecutive_late_nights,
        "total_late_nights": total_late_nights,
        "diary_streak_current": diary_streak_current,
        "diary_streak_max": diary_streak_max,
        # v2.0 新字段聚合（2026-06-24）
        "sleep_quality_counts": sleep_quality_counts,
        "sleep_quality_data_days": sum(sleep_quality_counts.values()),
        "energy_accuracy": energy_accuracy,
        "energy_bias": energy_bias,
        "energy_data_days": len(energy_pred_actual_pairs),
        "calm_accuracy": calm_accuracy,
        "calm_data_days": len(calm_pred_actual_pairs),
        "avg_satisfaction": avg_satisfaction,
        "satisfaction_data_days": len(satisfaction_values),
        "physiological_counts": physiological_counts,
    }


# ─── 成就检测 ────────────────────────────────────────────────
def check_achievements(data):
    """检测所有成就，返回新解锁的成就列表"""
    newly_unlocked = []
    values = {
        "tomato":      data["tomato_total"],
        "reading":     data["reading_total"],
        "diary":       data["diary_total"],
        "sleep_early": data["sleep_early_total"],
        "wake_early":  data["wake_early_total"],
        "consecutive_late": data.get("consecutive_late_nights", 0),
        "total_late": data.get("total_late_nights", 0),
    }

    skip_keys = {"consecutive_late_daily"}
    for category, achievements in ACHIEVEMENTS.items():
        if category in skip_keys:
            continue
        current_value = values.get(category, 0)
        for ach in achievements:
            if ach["id"] not in data["unlocked"] and current_value >= ach["threshold"]:
                data["unlocked"].append(ach["id"])
                newly_unlocked.append((ach, current_value))

    return newly_unlocked


def get_next_targets(data):
    """获取最近的下一个目标"""
    values = {
        "tomato":      data["tomato_total"],
        "reading":     data["reading_total"],
        "diary":       data["diary_total"],
        "sleep_early": data["sleep_early_total"],
        "wake_early":  data["wake_early_total"],
        "consecutive_late": data.get("consecutive_late_nights", 0),
        "total_late": data.get("total_late_nights", 0),
    }
    # 跳过每日等级表（它是显示用的字典，不是成就列表）
    skip_keys = {"consecutive_late_daily"}
    targets = []
    for category, achievements in ACHIEVEMENTS.items():
        if category in skip_keys:
            continue
        current = values.get(category, 0)
        for ach in achievements:
            if ach["id"] not in data["unlocked"]:
                remaining = ach["threshold"] - current
                pct = int(current / ach["threshold"] * 100)
                targets.append({
                    "name": ach["name"],
                    "level": ach["level"],
                    "threshold": ach["threshold"],
                    "current": current,
                    "remaining": remaining,
                    "pct": pct,
                    "category": category,
                })
                break  # 每个类别只取最近一个
    targets.sort(key=lambda x: x["pct"], reverse=True)
    return targets


# ─── 主流程 ────────────────────────────────────────────────
def update_achievement_markdown():
    """自动更新所有Markdown成就文件"""
    import shutil
    from datetime import datetime
    
    data = load_data()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 1. 更新番茄成就.md
    tomato_file = ACHIEVEMENT_DIR / "番茄成就.md"
    if tomato_file.exists():
        content = tomato_file.read_text(encoding="utf-8")
        # 更新累计番茄
        content = re.sub(r'\| \*\*累计番茄\*\* \| [^|]+ \|', f'| **累计番茄** | {int(data["tomato_total"])}🍅 |', content)
        content = re.sub(r'最后更新[^:]+:', f'最后更新：{timestamp}', content)
        tomato_file.write_text(content, encoding="utf-8")
        print(f"✅ 已更新番茄成就.md")
    
    # 2. 更新通用打卡成就.md
    diary_file = ACHIEVEMENT_DIR / "通用打卡成就.md"
    if diary_file.exists():
        content = diary_file.read_text(encoding="utf-8")
        # 更新日记篇数
        content = re.sub(r'\| \*\*日记篇数\*\* \| [^|]+ \|', f'| **日记篇数** | {data["diary_total"]} 篇 |', content)
        # 更新连续天数（v2.1改用真实统计，不再min(总数,14)估算）
        streak = data.get("diary_streak_current", 0)
        content = re.sub(r'\| \*\*连续日记\*\* \| [^|]+ \|', f'| **连续日记** | {streak} 天 |', content)
        content = re.sub(r'最后更新[^:]+:', f'最后更新：{timestamp}', content)
        diary_file.write_text(content, encoding="utf-8")
        print(f"✅ 已更新通用打卡成就.md（连续日记={streak}天）")
    
    # 3. 更新健康成就.md（如果存在）
    health_file = ACHIEVEMENT_DIR / "健康成就.md"
    if health_file.exists():
        content = health_file.read_text(encoding="utf-8")
        # 更新早睡天数
        content = re.sub(r'\| \*\*早睡天数\*\* \| [^|]+ \|', f'| **早睡天数** | {data["sleep_early_total"]} 天 |', content)
        # 更新早起天数
        content = re.sub(r'\| \*\*早起天数\*\* \| [^|]+ \|', f'| **早起天数** | {data["wake_early_total"]} 天 |', content)
        content = re.sub(r'最后更新[^:]+:', f'最后更新：{timestamp}', content)
        health_file.write_text(content, encoding="utf-8")
        print(f"✅ 已更新健康成就.md")
    
    # 4. 更新月亮之子成就.md
    dark_file = ACHIEVEMENT_DIR / "月亮之子成就.md"
    if dark_file.exists():
        content = dark_file.read_text(encoding="utf-8")
        # 更新连续熬夜
        content = re.sub(r'\|\s*\*\*连续熬夜\*\*\s*\|\s*\d+\s*天\s*\|[^|]*\|', f'| **连续熬夜** | {data.get("consecutive_late_nights", 0)} 天 | {data.get("consecutive_late_desc", "当前连续")}|', content)
        # 更新累计熬夜
        content = re.sub(r'\|\s*\*\*累计熬夜\*\*\s*\|\s*\d+\s*天\s*\|[^|]*\|', f'| **累计熬夜** | {data.get("total_late_nights", 0)} 天 | {data.get("total_late_desc", "累计")}|', content)
        content = re.sub(r'最后更新[^:]+:', f'最后更新：{timestamp}', content)
        dark_file.write_text(content, encoding="utf-8")
        print(f"✅ 已更新月亮之子成就.md")
    
    print(f"\n🎯 Markdown同步完成！")


# 在run_check中调用（在save_data之后）

def run_check(scan_all=False, as_of_date=None):
    """执行成就检测主流程。
    as_of_date 提供时进入"按日期触发"预览模式：扫描截止该日、弹窗解锁，
    但不写回累计存档、不重写 Markdown，避免历史日期把总数冲低。"""
    print("🔍 正在检测成就进度...")

    data = load_data()

    if as_of_date and not scan_all:
        # ── 按日期触发（预览模式）──
        print(f"📅 按日期触发（截止 {as_of_date}），预览模式...")
        stats = scan_all_diaries(cutoff=as_of_date)
        preview_data = dict(data)
        preview_data.update({
            "tomato_total": stats["tomato_total"],
            "diary_total": stats["diary_total"],
            "sleep_early_total": stats["sleep_early_total"],
            "wake_early_total": stats["wake_early_total"],
            "reading_total": stats["reading_total"],
            "consecutive_late_nights": stats.get("consecutive_late_nights", 0),
            "total_late_nights": stats.get("total_late_nights", 0),
            "sleep_quality_counts": stats.get("sleep_quality_counts", {}),
            "sleep_quality_data_days": stats.get("sleep_quality_data_days", 0),
            "energy_accuracy": stats.get("energy_accuracy", 0.0),
            "energy_bias": stats.get("energy_bias", "N/A"),
            "energy_data_days": stats.get("energy_data_days", 0),
            "calm_accuracy": stats.get("calm_accuracy", 0.0),
            "calm_data_days": stats.get("calm_data_days", 0),
            "avg_satisfaction": stats.get("avg_satisfaction", 0.0),
            "satisfaction_data_days": stats.get("satisfaction_data_days", 0),
            "physiological_counts": stats.get("physiological_counts", {}),
        })
        print(f"  番茄总数：{preview_data['tomato_total']}🍅")
        print(f"  日记总数：{preview_data['diary_total']}篇")
        newly_unlocked = check_achievements(preview_data)
        if newly_unlocked:
            print(f"\n🎉 解锁了 {len(newly_unlocked)} 个新成就！")
            for ach, value in newly_unlocked:
                send_achievement_notification(ach, value)
                sync_to_greatest_me(ach, value)
        else:
            print("✅ 暂无新成就解锁")
        print(f"\n📌 预览模式：未修改存档与 Markdown。正式记录请跑 --all")
        return
    elif scan_all:
        print("📊 全量扫描所有日记...")
        stats = scan_all_diaries()
        data["tomato_total"] = stats["tomato_total"]
        data["diary_total"] = stats["diary_total"]
        data["sleep_early_total"] = stats["sleep_early_total"]
        data["wake_early_total"] = stats["wake_early_total"]
        data["reading_total"] = stats["reading_total"]
        data["consecutive_late_nights"] = stats.get("consecutive_late_nights", 0)
        data["total_late_nights"] = stats.get("total_late_nights", 0)
        # v2.0 新字段（2026-06-24）
        data["sleep_quality_counts"] = stats.get("sleep_quality_counts", {})
        data["sleep_quality_data_days"] = stats.get("sleep_quality_data_days", 0)
        data["energy_accuracy"] = stats.get("energy_accuracy", 0.0)
        data["energy_bias"] = stats.get("energy_bias", "N/A")
        data["energy_data_days"] = stats.get("energy_data_days", 0)
        data["calm_accuracy"] = stats.get("calm_accuracy", 0.0)
        data["calm_data_days"] = stats.get("calm_data_days", 0)
        data["avg_satisfaction"] = stats.get("avg_satisfaction", 0.0)
        data["satisfaction_data_days"] = stats.get("satisfaction_data_days", 0)
        data["physiological_counts"] = stats.get("physiological_counts", {})
        print(f"  番茄总数：{data['tomato_total']}🍅")
        print(f"  日记总数：{data['diary_total']}篇")
        print(f"  早睡天数：{data['sleep_early_total']}天")
        print(f"  早起天数：{data['wake_early_total']}天")
        print(f"  阅读总数：{data['reading_total']}本（自动统计）")
        # v2.0 新字段
        if data.get("sleep_quality_data_days"):
            print(f"  睡眠质量：A{data['sleep_quality_counts'].get('A',0)}/B{data['sleep_quality_counts'].get('B',0)}/C{data['sleep_quality_counts'].get('C',0)}（{data['sleep_quality_data_days']}天有数据）")
        if data.get("energy_data_days"):
            print(f"  精力准确率：{data['energy_accuracy']}%（{data['energy_bias']}偏差，{data['energy_data_days']}天）")
        if data.get("calm_data_days"):
            print(f"  平静准确率：{data['calm_accuracy']}%（{data['calm_data_days']}天）")
        if data.get("avg_satisfaction"):
            print(f"  平均满意度：{data['avg_satisfaction']}/5（{data['satisfaction_data_days']}天）")
        if data.get("physiological_counts"):
            pc = data["physiological_counts"]
            print(f"  生理状态：🟢{pc.get('green',0)}/🟡{pc.get('yellow',0)}/🔴{pc.get('red',0)}")
    else:
        # 只扫描今日日记
        today = date.today().strftime("%Y-%m-%d")
        today_file = DIARY_DIR / f"{today}.md"
        if today_file.exists():
            today_data = parse_diary_file(today_file)
            print(f"  今日番茄：{today_data['tomato']}🍅")
        else:
            print(f"  今日日记不存在：{today_file}")

    # 检测新成就
    newly_unlocked = check_achievements(data)

    if newly_unlocked:
        print(f"\n🎉 解锁了 {len(newly_unlocked)} 个新成就！")
        for ach, value in newly_unlocked:
            send_achievement_notification(ach, value)
            sync_to_greatest_me(ach, value)  # ← 联动：写入最伟大的我
    else:
        print("✅ 暂无新成就解锁")

    # 保存数据
    save_data(data)
    
    # 同步更新Markdown文件
    if scan_all:
        update_achievement_markdown()

    # 显示下一个目标
    targets = get_next_targets(data)
    if targets:
        print("\n🎯 最近目标：")
        for t in targets[:5]:
            bar = "█" * (t["pct"] // 10) + "░" * (10 - t["pct"] // 10)
            print(f"  {t['name']}  [{bar}] {t['pct']}%  (还差 {t['remaining']})")

    return newly_unlocked



def force_achievement(achievement_id):
    """手动触发指定成就的弹窗"""
    found = None
    category = None
    for cat, achievements in ACHIEVEMENTS.items():
        if not isinstance(achievements, list):
            continue
        for ach in achievements:
            if ach["id"] == achievement_id:
                found = ach
                category = cat
                break
        if found:
            break
    if not found:
        print(f"❌ 未找到成就 ID: {achievement_id}")
        return
    data = load_data()
    values = {"tomato": data["tomato_total"], "reading": data["reading_total"], "diary": data["diary_total"], "sleep_early": data["sleep_early_total"], "wake_early": data["wake_early_total"], "consecutive_late": data.get("consecutive_late_nights", 0), "total_late": data.get("total_late_nights", 0)}
    current_value = values.get(category, 0)
    print(f"\n🎉 手动触发成就弹窗：{found['name']}")
    print(f"  等级：{found['level']}")
    print(f"  当前值：{current_value}")
    send_achievement_notification(found, current_value)


def auto_notify():
    """自动通知模式：供番茄钟调用"""
    data = load_data()
    stats = scan_all_diaries()
    data["tomato_total"] = stats["tomato_total"]
    data["diary_total"] = stats["diary_total"]
    data["sleep_early_total"] = stats["sleep_early_total"]
    data["wake_early_total"] = stats["wake_early_total"]
    data["reading_total"] = stats.get("reading_total", 9)
    # v2.0 新字段持久化（2026-06-24）
    for k in ["sleep_quality_counts", "sleep_quality_data_days",
              "energy_accuracy", "energy_bias", "energy_data_days",
              "calm_accuracy", "calm_data_days",
              "avg_satisfaction", "satisfaction_data_days",
              "physiological_counts"]:
        if k in stats:
            data[k] = stats[k]
    newly_unlocked = check_achievements(data)
    if newly_unlocked:
        for ach, value in newly_unlocked:
            send_achievement_notification(ach, value)
    save_data(data)
    return len(newly_unlocked)

def show_status():
    """显示当前成就状态"""
    # 强制全量扫描获取最新数据
    stats = scan_all_diaries()
    data = load_data()
    print("\n📊 成就进度总览")
    print("=" * 50)
    print(f"  🍅 番茄总数：{data['tomato_total']}🍅")
    print(f"  📚 阅读总数：{data['reading_total']}本")
    print(f"  📔 日记总数：{data['diary_total']}篇")
    print(f"  😴 早睡天数：{data['sleep_early_total']}天")
    print(f"  🌅 早起天数：{data['wake_early_total']}天")
    print(f"  🏆 已解锁成就：{len(data['unlocked'])}个")
    print(f"  🕐 最后更新：{data['last_updated']}")
    # v2.0 新字段（2026-06-24）
    sq = stats.get("sleep_quality_counts", {})
    if stats.get("sleep_quality_data_days"):
        print(f"  💤 睡眠质量：A{sq.get('A',0)}/B{sq.get('B',0)}/C{sq.get('C',0)}")
    if stats.get("energy_data_days"):
        print(f"  ⚡ 精力准确率：{stats['energy_accuracy']}%（{stats['energy_bias']}偏差）")
    if stats.get("calm_data_days"):
        print(f"  🧘 平静准确率：{stats['calm_accuracy']}%")
    if stats.get("avg_satisfaction"):
        print(f"  😊 平均满意度：{stats['avg_satisfaction']}/5")
    pc = stats.get("physiological_counts", {})
    if any(pc.values()):
        print(f"  💪 生理状态：🟢{pc.get('green',0)}/🟡{pc.get('yellow',0)}/🔴{pc.get('red',0)}")
    print("=" * 50)

    targets = get_next_targets(data)
    print("\n🎯 最近目标：")
    for t in targets[:5]:
        bar = "█" * (t["pct"] // 10) + "░" * (10 - t["pct"] // 10)
        print(f"  {t['name']}  [{bar}] {t['pct']}%  (还差 {t['remaining']})")


# ─── 入口 ────────────────────────────────────────────────────


# ─── MEMORY.md 同步 ─────────────────────────────────────────────
def sync_memory_md():
    """同步成就数据到 workspace MEMORY.md 和 QClaw记忆 MEMORY.md"""
    from datetime import datetime
    data = load_data()
    
    memory_files = [
        Path.home() / ".openclaw" / "workspace" / "MEMORY.md",
        Path.home() / "个人AI档案" / "QClaw记忆" / "MEMORY.md",
    ]
    
    # 计算下一目标
    tomato_total = int(data.get("tomato_total", 0))
    if tomato_total >= 500:
        next_goal = "🥇 番茄宗师（700🍅）"
        next_remaining = 700 - tomato_total
    elif tomato_total >= 400:
        next_goal = "🥈 番茄大师（500🍅）"
        next_remaining = 500 - tomato_total
    else:
        next_goal = "🥈 番茄高手（400🍅）"
        next_remaining = 400 - tomato_total
    
    # 构建新的番茄成就段
    new_section = f"""### 番茄成就（{datetime.now().strftime("%Y-%m-%d")} 数据源：achievement_tracker.py --sync-memory）
- **当前累计**：{tomato_total}🍅
- 达成时间线：
  - 2026-03-22：🥉 番茄新星（100🍅）
  - 2026-03-28：🥈 番茄进阶（200🍅）达成（累计203.5🍅）
  - 2026-04-03：累计269🍅
  - 2026-04-19：累计{tomato_total}🍅（achievement_tracker 全量扫描）
- **下一目标**：{next_goal}，还差{next_remaining}🍅"""
    
    for memory_file in memory_files:
        if not memory_file.exists():
            print(f"⚠️ {memory_file} 不存在，跳过")
            continue
        
        content = memory_file.read_text(encoding="utf-8")
        
        # 使用正则替换番茄成就段（从 "### 番茄成就" 到下一个 "###" 或 "##" 之前）
        pattern = r'(### 番茄成就[^\n]*\n)(.*?)(?=\n### |\n## |$)'
        replacement = new_section + '\n'
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if new_content != content:
            memory_file.write_text(new_content, encoding="utf-8")
            print(f"✅ 已同步 {memory_file.name} 番茄数：{tomato_total}🍅")
        else:
            print(f"⏭️ {memory_file.name} 无变化")
    
    print(f"\n🎯 MEMORY.md 同步完成！")


# ─── 入口 ────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if "--all" in sys.argv:
        run_check(scan_all=True)
    elif "--date" in sys.argv:
        try:
            idx = sys.argv.index("--date")
            dval = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        except Exception:
            dval = None
        if dval:
            run_check(as_of_date=dval)
        else:
            print("用法：python3 achievement_tracker.py --date YYYY-MM-DD")
    elif "--status" in sys.argv:
        show_status()
    elif "--sync-memory" in sys.argv:
        sync_memory_md()
    elif "--force" in sys.argv:
        try:
            idx = sys.argv.index("--force")
            if idx + 1 < len(sys.argv):
                force_achievement(sys.argv[idx + 1])
            else:
                print("用法：python3 achievement_tracker.py --force <achievement_id>")
        except Exception as e:
            print(f"错误：{e}")
    else:
        run_check(scan_all=False)
