#!/bin/sh
# skills-lab 技能一键安装脚本
#
# 用法:
#   curl -fsSL https://raw.githubusercontent.com/Cai-ki/skills-lab/main/install.sh | sh
#
# 自定义(环境变量覆盖):
#   SKILLS_LAB_REPO=<git地址>   要安装的仓库,默认 https://github.com/Cai-ki/skills-lab.git
#   SKILLS_LAB_BRANCH=<分支>    仓库分支,默认 main
#   PI_SKILLS_DIR=<目录>        安装目标,默认 ~/.pi/agent/skills

set -eu

REPO_URL="${SKILLS_LAB_REPO:-https://github.com/Cai-ki/skills-lab.git}"
BRANCH="${SKILLS_LAB_BRANCH:-main}"
TARGET="${PI_SKILLS_DIR:-$HOME/.pi/agent/skills}"
BACKUP="${PI_SKILLS_BACKUP:-$TARGET.backup}"

command -v git >/dev/null 2>&1 || {
    echo "错误:未找到 git,请先安装 git"
    exit 1
}

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT INT TERM

echo "==> 克隆 $REPO_URL ($BRANCH)"
git clone --quiet --depth 1 --branch "$BRANCH" "$REPO_URL" "$tmp_dir/repo"

mkdir -p "$TARGET"

count=0
for skill_dir in "$tmp_dir/repo"/skills/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    name=$(basename "$skill_dir")
    if [ -e "$TARGET/$name" ]; then
        stamp=$(date +%Y%m%d%H%M%S)
        mkdir -p "$BACKUP/$stamp"
        mv "$TARGET/$name" "$BACKUP/$stamp/$name"
        echo "    已备份旧技能 $name -> $BACKUP/$stamp/$name"
    fi
    cp -R "$skill_dir" "$TARGET/"
    count=$((count + 1))
done

echo "==> 安装完成:$count 个技能 -> $TARGET"
echo "    重启 pi 后可用 /skill:<技能名> 验证"
