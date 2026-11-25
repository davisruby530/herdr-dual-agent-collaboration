#!/usr/bin/env bash
# 把本仓库组装成可被各类 agent 调用的 herdr-dual-agent 技能。
# 骨架与指南只在仓库里维护一份，更新后重跑本脚本即可。
#
# 用法：skills/install.sh [--force]
#   安装到 ~/.agents/skills/herdr-dual-agent，并为已存在的各 agent 技能目录建软链接。
#   目标已存在时须加 --force 才会替换。
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
dest="$HOME/.agents/skills/herdr-dual-agent"

if [ -e "$dest" ]; then
  [ "${1:-}" = "--force" ] || { echo "已存在: $dest（加 --force 替换）" >&2; exit 1; }
  rm -rf "$dest"
fi
mkdir -p "$dest/assets/project" "$dest/references"

cp "$repo/skills/herdr-dual-agent/SKILL.md" "$dest/"
cp -R "$repo/templates/project/." "$dest/assets/project/"
find "$dest" -name '__pycache__' -prune -exec rm -rf {} +
chmod +x "$dest/assets/project/scripts/wait-for-verdict.sh"
cp "$repo/templates/academic_paper_workflow.md" "$repo/templates/ticket-index.md" "$dest/references/"
{ cat "$repo/GLOSSARY.md"; echo; cat "$repo"/docs/adr/*.md; } > "$dest/references/glossary-and-adr.md"

# 指南与操作说明里的仓库路径改为技能内路径
sed -e 's#^> \*\*术语\*\*：见仓库根目录.*$#> **术语与设计缘由**：见本技能的 `references/glossary-and-adr.md`。#' \
    -e 's#\[`templates/project/AGENTS.md`\](../../templates/project/AGENTS.md)#`assets/project/AGENTS.md`#' \
    -e 's#\[`templates/academic_paper_workflow.md`\](../../templates/academic_paper_workflow.md)#`references/academic_paper_workflow.md`#' \
    -e 's#](../../templates/project/tools/#](../assets/project/tools/#g' \
    -e 's#templates/project/\.#<本技能目录>/assets/project/.#g' \
    -e 's#templates/project/#assets/project/#g' \
    -e 's#templates/ticket-index\.md#references/ticket-index.md#g' \
    "$repo/docs/agents/coder-reviewer-herdr-collaboration-guide.md" > "$dest/references/guide.md"
quickstart="$dest/assets/project/docs/agents/collaboration-quickstart.md"
sed -e 's#^框架来源与完整指南：.*$#框架来源与完整指南：`herdr-dual-agent` 技能的 `references/guide.md`。#' \
    -e 's#框架仓库里 `templates/academic_paper_workflow.md`#`herdr-dual-agent` 技能里 `references/academic_paper_workflow.md`#' \
    "$quickstart" > "$quickstart.tmp" && mv "$quickstart.tmp" "$quickstart"

for dir in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.gemini/config/skills" "$HOME/.pi/agent/skills"; do
  [ -d "$dir" ] || continue
  link="$dir/herdr-dual-agent"
  if [ -L "$link" ] || [ ! -e "$link" ]; then
    ln -sfn "$dest" "$link"
    echo "已链接: $link"
  else
    echo "跳过（同名目录已存在）: $link" >&2
  fi
done
echo "已安装: $dest"
