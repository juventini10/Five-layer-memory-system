#!/bin/bash
# git_commit_wrapper.sh — 透明 git wrapper：所有 `git commit` 自动经 git_commit_safe.sh 安全门禁（零人工采纳·愿景①）
#
# 真源在本文件（[记忆共享中心]/脚本中心/·git 跟踪 → 容灾三通道自动覆盖）。
# 部署点 = 指向本文件的软链（⛔DO NOT 复制实体文件·复制=双实现漂移且实体落 tracked 目录外→容灾全盲）：
#   ~/bin/git            软链至此（会 source profile 的端）
#   ~/.local/bin/git     软链至此（App 注入 PATH·稳定排在 /usr/bin 之前）
# 异机/新端部署动作：ln -sf "[记忆共享中心]/脚本中心/git_commit_wrapper.sh" <PATH目录>/git
# 其余子命令原样透传到真实 git（GCS_GIT 全路径，避免 wrapper 自递归）。
REAL_GIT="$(PATH=/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin command -v git)"
export GCS_GIT="$REAL_GIT"
SCRIPT="[记忆共享中心]/脚本中心/git_commit_safe.sh"

if [ "$1" = "commit" ]; then
  exec bash "$SCRIPT" "$@"
else
  exec "$REAL_GIT" "$@"
fi
