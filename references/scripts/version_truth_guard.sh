#!/bin/bash
# version_truth_guard.sh v1.4 -- frontmatter version truth gate (pre-commit slot 5)
# v1.4 (2026-08-30): R4 severity fixed -- from "any duplicate in the staged blob" to
#   "duplicate count increased by this commit". Reason: 4 files already carry duplicate
#   entry versions in HEAD, so the absolute test pinned those files for everyone (a gate
#   that blocks unrelated commits gets worked around, which is worse than no gate).
#   Pre-existing collisions now print as 预存 info and are queued to the owning end.
# R3/R4 (v1.3, 2026-08-29): cross-end concurrent version-collision root cure.
#   Live proof 2026-08-29: 06-跨端适配规范.md ended up with TWO v1.20 changelog entries
#   and 01-脚本架构设计通用规范.md double-claimed v1.3.33 -- WorkBuddy and ZCode bumped
#   independently the same day; R1/R2 are blind to "new version already used by someone else"
#   and to "duplicate entry in same file". Anchor: 愿景① detection must not rely on human
#   discipline; 立场卡 S014 机械是药.
# Principle: frontmatter version = addressable identity of content state.
#   Content changed while version unchanged = lying identity; every downstream
#   consumer (changelog_guard ver-diff / recall verify / rollback) builds on a fake address.
# Anchor: S257 "detection must not rely on human discipline". Live proof 2026-08-23:
#   2 files bumped their INTERNAL changelog section but left frontmatter stale.
# Scope: staged .md files differing from HEAD where either side declares 'version:'.
#   Files without frontmatter are outside the version system (exempt);
#   brand-new files exempt (first declaration); deletions exempt.
# Rules:
#   R1 content changed + new version == HEAD version  -> block (bump patch)
#   R2 HEAD had version + new content drops the line -> block (no silent identity erasure)
set -uo pipefail
fail=0
norm() { sed -E 's/^version:[[:space:]]*//; s/["'"'"']?[[:space:]]*$//'; }
# duplist <rev-spec> -- changelog entry versions occurring >1 in that blob, as "v=count"
duplist() {
  git show "$1" 2>/dev/null | grep -E '^- v[0-9]+([.][0-9]+)+[（( ]' \
    | sed -E 's/^- (v[0-9]+([.][0-9]+)+).*/\1/' | sort | uniq -c | awk '$1>1{print $2"="$1}'
}
while IFS= read -r f; do
  case "$f" in *.md) ;; *) continue ;; esac
  # v1.2 ledger-class exemption: append-only ledgers' content IS the log itself;
  #   requiring version bumps per append = double-bookkeeping (TE-20260716 ruling).
  b=$(basename "$f")
  case "$b" in CHANGELOG.md) continue ;; esac
  printf '%s' "$b" | grep -qE '^(变更日志\.md|TTL注册表\.md|免疫复发记录\.md)$' && continue
  git cat-file -e "HEAD:$f" 2>/dev/null || continue
  head_ver=$(git show "HEAD:$f" 2>/dev/null | grep -m1 -E '^version:' | norm || true)
  new_ver=$(git show ":$f" 2>/dev/null | grep -m1 -E '^version:' | norm || true)
  if [ -z "$head_ver" ] && [ -z "$new_ver" ]; then continue; fi
  if [ -n "$head_ver" ] && [ -n "$new_ver" ] && [ "$head_ver" = "$new_ver" ]; then
    echo "[version_truth] BLOCK: $f content changed but frontmatter version still $head_ver -- bump patch and re-commit"
    fail=1
  fi
  if [ -n "$head_ver" ] && [ -z "$new_ver" ]; then
    echo "[version_truth] BLOCK: $f dropped its frontmatter version line (was $head_ver) -- identity must not be silently erased"
    fail=1
  fi
  # R3: history uniqueness -- new version must never reuse a version another write already used
  if [ -n "$new_ver" ] && [ "$new_ver" != "$head_ver" ]; then
    if git log -S"version: $new_ver" --format=%H -- "$f" 2>/dev/null | head -1 | grep -q .; then
      echo "[version_truth] BLOCK: $f new version $new_ver already occupied in git history (cross-end concurrent bump?) -- read current head-of-file, bump to next FREE sequential version"
      fail=1
    fi
  fi
  # R4 (v1.4 corrected): file-internal collision -- block only what THIS commit adds.
  #   Live proof 2026-08-30: HEAD already carries duplicate entry versions in 4 files
  #   (01-脚本架构设计通用规范 x5 / 03-进度看板 x4 / INDEX x1 / 素然启镜-风格讨论 x1),
  #   so "any dup in the staged blob" pinned those files forever — the committer was
  #   blocked by a defect they did not create (mis-attribution; contradicts 预存态透明 G4).
  #   Test = per-version count delta staged vs HEAD, not staged absolute.
  head_dups=$(duplist "HEAD:$f")
  new_dups=$(duplist ":$f")
  added=""; pre=""
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    v=${line%%=*}; c=${line##*=}
    hc=$(printf '%s\n' "$head_dups" | awk -F= -v v="$v" '$1==v{print $2}')
    case "$hc" in ''|*[!0-9]*) hc=1 ;; esac
    if [ "$c" -gt "$hc" ]; then
      added="$added $v(+$(($c - $hc)))"
    elif [ "$hc" -gt 1 ]; then
      pre="$pre $v"
    fi
  done <<EOF
$new_dups
EOF
  if [ -n "$added" ]; then
    echo "[version_truth] BLOCK: $f this commit adds duplicate changelog entry versions:$added -- concurrent-write collision; read current head-of-file, renumber the new entry to next FREE version"
    fail=1
  fi
  if [ -n "$pre" ]; then
    echo "[version_truth] 预存(非本轮引入·不拦): $f already carries duplicate entry versions:$pre in HEAD -- 归位归原登记端，⛔不记在本次提交头上"
  fi
done < <(git -c core.quotepath=false diff --cached --name-only --diff-filter=ACM -- '*.md')
if [ "$fail" -eq 0 ]; then echo "OK version_truth_guard passed"; fi
exit $fail
