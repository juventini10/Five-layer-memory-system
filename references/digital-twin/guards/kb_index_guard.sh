#!/usr/bin/env bash
# kb-index-guard.sh v1.4 —— 知识池 INDEX 一致性守卫（changelog-guard 族·登记一致性守卫模式）
#   与 kb_index_sync.py 共用同一判定口径(数据真相优先), 二者必须一致, 否则=文档↔机制漂移(告警贬值)。
# 零第三方依赖(bash+find+awk+grep+sed+comm)。用法: --check(JSON) / --report(明细,供AI补)
# 设计: 比对 05-知识池/ 实际文件(书夹/卡片) 与 INDEX.md 登记(书级表+卡片目录)。
#   漏登记两类——书夹无书级登记(整本漏) / 卡片无卡片目录登记(单卡漏)。治"拆书/迁移后忘更新INDEX"。
#   匹配键: 书级=夹名; 卡片=文件名去.md(INDEX用 [[文件名]] 登记)。
# 依据: 登记一致性守卫模式(2026-08-06你"还能用到哪里"迁移·changelog-guard v1.6契约同源)。
# 边界: INDEX.md/书夹内非卡片文件(精华摘要)不检; 文件缺失而INDEX有登记=反向漂移(卡被删未清INDEX)一并报。
# v1.1 (2026-08-07) 性能修复: 集合预收集+参数替换, 但循环内子进程在沙箱下 ~20-40ms/次, 574+519次仍34s。
# v1.2 (2026-08-07) 性能修复: 卡片检查/反向漂移改 awk 关联数组内存匹配 + comm 集合运算(零循环内子进程),
#   实测 34s→<2s, 根治 Stop 钩子 60s 超时。输出契约(--check JSON / --report markdown)不变。
# v1.3 (2026-08-11) 误报根治(告警=真相): 沉睡4天苏醒后报56处, 脚本反推真相为48处真缺失+8处自身误报。
#   ①「文章卡片」是文章容器目录非书, 书级表不以《》登记它 → 书级检查排除(消 1 处整本漏误报);
#   ② 文章的「<文章名>-精华.md」是精华摘要变体, INDEX 用 () 链接登记不进 [[ ]] 卡片目录表
#      → 卡片集合排除 *-精华(消 7 处单卡漏误报; 原仅排除同名"精华摘要", 漏了该变体)。
#   原则: 守卫报的每一处都必须是真问题, 否则告警贬值成噪音, 人会学会忽略它 = 守卫等于没有。
# v1.4 (2026-08-20) 口径对齐 kb_index_sync.py(根治文档↔机制漂移): 卡片定义=编号卡片(书-卡片\d+)且仅真实书夹(排除文章卡片容器),
#   书级登记识别 4 形态(补 [精华]变体 与 ### 小节标题)。原 v1.3 把 C1穷举清单/文章卡片/书级精华当卡片 + 漏认 [精华]变体
#   → 26 处单卡漏 + 1 处整本漏 全为假阳性; 本版与 sync 一致后真实缺口=0(44 张真卡已由 sync --apply 回填)。
set -uo pipefail
POOL="$HOME/[日记仓库]/2-知识库/05-知识池"
INDEX="$POOL/INDEX.md"

mode="${1:---check}"
[ -f "$INDEX" ] || { echo "知识池 INDEX.md 不存在: $INDEX" >&2; exit 2; }

TMPD="${TMPDIR:-/tmp}/kbguard.$$"; mkdir -p "$TMPD"; trap 'rm -rf "$TMPD"' EXIT

# ---- 一次性集合收集 ----
find "$POOL" -mindepth 2 -maxdepth 2 -name "*.md" | sed "s|^$POOL/||" | sort > "$TMPD/all_full.txt"  # 书夹/卡名.md (仅书夹内一层, 同旧版)
# 书夹路径 (v1.3: 排除「文章卡片」——它是文章容器非书, 书级表按文章名登记, 不以《文章卡片》登记)
find "$POOL" -maxdepth 1 -mindepth 1 -type d ! -name "文章卡片" | sort > "$TMPD/books.txt"
grep -oE '\[\[[^]]+\]\]' "$INDEX" | tr -d '[]' | sort -u > "$TMPD/refs.txt"    # INDEX 全部 [[引用]] 卡名

# 卡片映射: 卡名→书夹 (all_full: 书夹/卡名.md)
# v1.3: 排除精华类文件——书夹用"精华摘要.md", 文章卡片用"<文章名>-精华.md", 二者均以 () 链接登记, 不进 [[ ]] 卡片目录表
# v1.4: 对齐 kb_index_sync.py(数据真相优先)——卡片=编号卡片(书-卡片\d+), 仅真实书夹(排除"文章卡片"容器)。
#   排除 C1穷举清单(元文件非卡)/ 书级精华摘要 / -精华变体。INDEX 1082 条 [[ ]] 引用 100% 符合 卡片\d+,
#   故本判定即真相; 此修消除原 v1.3 把 C1/文章卡片误当卡片导致的 26 处假阳性(告警=真相契约)。
awk '{ n=split($0,a,"/"); book=a[1]; base=a[2]; sub(/\.md$/,"",base);
       if(book=="文章卡片") next;
       if(base ~ /-卡片[0-9]+/) print base "\t" book }' \
  "$TMPD/all_full.txt" > "$TMPD/cards_map.txt"
awk -F'\t' '{print $1}' "$TMPD/cards_map.txt" | sort -u > "$TMPD/cards.txt"

# ---- 卡片漏登记: 卡片集合 - INDEX 引用集合 (comm 一次集合运算) ----
comm -23 "$TMPD/cards.txt" "$TMPD/refs.txt" > "$TMPD/missing.txt"

# ---- 反向漂移: INDEX 引用卡片形态(-卡片) 且 实际文件不存在 ----
sed 's|^[^/]*/||;s|\.md$||' "$TMPD/all_full.txt" | sort -u > "$TMPD/all_base.txt"
grep '\-卡片' "$TMPD/refs.txt" | sort -u > "$TMPD/refs_cards.txt"
comm -23 "$TMPD/refs_cards.txt" "$TMPD/all_base.txt" > "$TMPD/stale.txt"

# ---- 书级检查: 每书夹 INDEX 应有书级登记。v1.4 对齐 kb_index_sync.get_booklevel_registered 的 4 形态:
#   《书》 / [精华摘要](书/精华摘要.md) / [精华](书/ / ### 书(标题可带可不带《》)
#   (原 v1.3 只认前 2 种, 漏认 [精华] 变体与 ### 小节 → 尖叫的数学等假阳性, 已修)
missing_books=""; n_missing_b=0
while IFS= read -r dir; do
  book=$(basename "$dir")
  registered=false
  grep -q "《${book}》" "$INDEX" 2>/dev/null && registered=true
  grep -q "\[精华摘要\](${book}/" "$INDEX" 2>/dev/null && registered=true
  grep -q "\[精华\](${book}/" "$INDEX" 2>/dev/null && registered=true
  grep -q "^### .*${book}" "$INDEX" 2>/dev/null && registered=true
  if ! $registered; then
    missing_books+="| ${book} | 书夹存在但 INDEX 书级表无登记(整本漏) |\n"; n_missing_b=$((n_missing_b+1))
  fi
done < "$TMPD/books.txt"

# ---- 计数 ----
n_books=$(wc -l < "$TMPD/books.txt" | tr -d ' ')
n_cards=$(wc -l < "$TMPD/cards.txt" | tr -d ' ')
n_missing_c=$(wc -l < "$TMPD/missing.txt" | tr -d ' ')
n_stale=$(wc -l < "$TMPD/stale.txt" | tr -d ' ')

if [ "$mode" = "--check" ]; then
  n_bad=$((n_missing_b+n_missing_c+n_stale))
  alarm=$([ "$n_bad" -gt 0 ] && echo true || echo false)
  printf '{"books": %d, "cards": %d, "missing_book": %d, "missing_card": %d, "stale_index": %d, "alarm": %s}\n' "$n_books" "$n_cards" "$n_missing_b" "$n_missing_c" "$n_stale" "$alarm"
  [ "$n_bad" -gt 0 ] && exit 1 || exit 0
elif [ "$mode" = "--report" ]; then
  n_bad=$((n_missing_b+n_missing_c+n_stale))
  if [ "$n_bad" -eq 0 ]; then echo "✅ 知识池全部 ${n_books} 书夹 / ${n_cards} 卡片 已在 INDEX 登记"; exit 0; fi
  echo "## ⚠️ 知识池 INDEX 一致性检测到 ${n_bad} 处问题（${n_books} 书夹 / ${n_cards} 卡片）"
  echo ""
  if [ "$n_missing_b" -gt 0 ]; then
    echo "### 整本漏登记"; echo "| 书 | 问题 |"; echo "|---|------|"
    printf "%b" "$missing_books"; echo ""
  fi
  if [ "$n_missing_c" -gt 0 ]; then
    echo "### 单卡漏登记"; echo "| 书 | 卡片 | 问题 |"; echo "|---|------|------|"
    awk -F'\t' 'NR==FNR { book[$1]=$2; next } $0 in book { print "| " book[$0] " | " $0 " | INDEX 卡片目录无登记(单卡漏) |" }' \
      "$TMPD/cards_map.txt" "$TMPD/missing.txt"
    echo ""
  fi
  if [ "$n_stale" -gt 0 ]; then
    echo "### INDEX 僵尸登记(文件已不存在)"; echo "| 卡片 | 问题 |"; echo "|---|------|"
    awk '{ print "| " $0 " | INDEX 有登记但文件不存在(卡删未清) |" }' "$TMPD/stale.txt"
    echo ""
  fi
  echo "> 机械部分脚本已填;修正动作(补 INDEX 登记行 / 清理僵尸登记)须 AI 执行。"
else echo "用法: kb-index-guard.sh [--check|--report]"; exit 2; fi
