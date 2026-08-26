#!/bin/sh
# skills-lab 技能一键安装脚本
#
# 用法:
#   curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi
#   curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi claude
#   curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- --list
#
# 参数(可多个):
#   pi       安装到 ~/.pi/agent/skills
#   claude   安装到 ~/.claude/skills
#   codex    安装到 ~/.codex/skills
#   --list   列出支持的 harness 及默认安装目录
#
# 环境变量:
#   SKILLS_LAB_REPO / SKILLS_LAB_BRANCH   覆盖仓库地址与分支
#   PI_SKILLS_DIR / CLAUDE_SKILLS_DIR / CODEX_SKILLS_DIR   覆盖对应安装目录
#   SKILLS_BACKUP_KEEP   每个目录保留最近几份备份,默认 5,0 不限制

set -eu

REPO_URL="${SKILLS_LAB_REPO:-https://github.com/caikiji/skills-lab.git}"
BRANCH="${SKILLS_LAB_BRANCH:-main}"
KEEP="${SKILLS_BACKUP_KEEP:-5}"

# harness 名称 -> 默认安装目录
target_of() {
    case "$1" in
        pi)      echo "${PI_SKILLS_DIR:-$HOME/.pi/agent/skills}" ;;
        claude)  echo "${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}" ;;
        codex)   echo "${CODEX_SKILLS_DIR:-$HOME/.codex/skills}" ;;
        *)       return 1 ;;
    esac
}

list_harnesses() {
    echo "支持的 harness 及默认安装目录:"
    echo "  pi      -> ~/.pi/agent/skills"
    echo "  claude  -> ~/.claude/skills"
    echo "  codex   -> ~/.codex/skills"
}

# 轮转:只保留最近 KEEP 份备份目录,删除最旧的
prune_backups() {
    [ "$KEEP" -le 0 ] && return 0
    total=$(ls -1 "$1" 2>/dev/null | wc -l)
    too_many=$((total - KEEP))
    [ "$too_many" -le 0 ] && return 0
    ls -1 "$1" | sort | head -n "$too_many" | while read -r d; do
        rm -rf "$1/$d"
        echo "    已清理旧备份 $1/$d"
    done
}

usage() {
    echo "用法: curl -fsSL <url> | sh -s -- <harness> [<harness>...]"
    echo "示例: curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi"
    list_harnesses
}

case "${1:-}" in
    --list|-h|--help) list_harnesses; exit 0 ;;
    "") usage; exit 1 ;;
esac

command -v git >/dev/null 2>&1 || {
    echo "错误:未找到 git,请先安装 git"
    exit 1
}

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT INT TERM

echo "==> 克隆 $REPO_URL ($BRANCH)"
git clone --quiet --depth 1 --branch "$BRANCH" "$REPO_URL" "$tmp_dir/repo"

installed=0
for arg in "$@"; do
    target=$(target_of "$arg") || {
        echo "跳过未知 harness:$arg(用 --list 查看支持项)"
        continue
    }
    mkdir -p "$target"
    stamp=$(date +%Y%m%d%H%M%S)
    backup_dir="$target.backup"
    count=0
    backup_count=0
    for skill_dir in "$tmp_dir/repo"/skills/*/; do
        [ -f "$skill_dir/SKILL.md" ] || continue
        name=$(basename "$skill_dir")
        if [ -e "$target/$name" ]; then
            mkdir -p "$backup_dir/$stamp"
            mv "$target/$name" "$backup_dir/$stamp/$name"
            backup_count=$((backup_count + 1))
        fi
        cp -R "$skill_dir" "$target/"
        count=$((count + 1))
    done
    [ "$backup_count" -gt 0 ] && echo "    已备份 $backup_count 个旧技能 -> $backup_dir/$stamp/"
    prune_backups "$backup_dir"
    echo "==> $arg:安装 $count 个技能 -> $target"
    installed=$((installed + 1))
done

if [ "$installed" -gt 0 ]; then
    echo "完成。重启对应 agent 后用 /skill:<技能名> 验证。"
else
    echo "错误:没有安装任何 harness(用 --list 查看支持项)"
    exit 1
fi
