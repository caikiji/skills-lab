#!/bin/sh
# skills-lab 技能与配置一键安装脚本
#
# 用法:
#   curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi
#   curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi configs
#   curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- --list
#
# 参数(可多个):
#   pi / claude / codex   安装技能到对应 harness 目录
#   configs               按 deploy.yaml 部署 configs/ 内容
#   --list                列出支持的 harness 及默认安装目录
#
# 环境变量:
#   SKILLS_LAB_REPO / SKILLS_LAB_BRANCH   覆盖仓库地址与分支
#   PI_SKILLS_DIR / CLAUDE_SKILLS_DIR / CODEX_SKILLS_DIR   覆盖对应安装目录
#   SKILLS_BACKUP_KEEP   每个目标保留最近几份备份,默认 5,0 不限制
#
# configs 部署依赖 python3/python(py launcher) + PyYAML

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

# 探测带 PyYAML 的 python:python3 -> python -> py -3
find_python() {
    for c in python3 python; do
        if command -v "$c" >/dev/null 2>&1 && "$c" -c "import yaml" >/dev/null 2>&1; then
            echo "$c"
            return 0
        fi
    done
    if command -v py >/dev/null 2>&1 && py -3 -c "import yaml" >/dev/null 2>&1; then
        echo "py -3"
        return 0
    fi
    return 1
}

list_harnesses() {
    echo "支持的 harness 及默认安装目录:"
    echo "  pi       -> ~/.pi/agent/skills"
    echo "  claude   -> ~/.claude/skills"
    echo "  codex    -> ~/.codex/skills"
    echo "  configs  -> 按 deploy.yaml 部署 configs/ 内容"
}

usage() {
    echo "用法: curl -fsSL <url> | sh -s -- <harness> [<harness>...]"
    echo "示例: curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi configs"
    list_harnesses
}

case "${1:-}" in
    --list|-h|--help) list_harnesses; exit 0 ;;
    "") usage; exit 1 ;;
esac

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

# 部署 configs:解析 deploy.yaml,src -> dest(copy + 备份)
deploy_configs() {
    repo_dir="$1"
    prefix="$2"
    work="$3"
    deploy_yaml="$repo_dir/deploy.yaml"
    configs_dir="$repo_dir/configs"
    [ -f "$deploy_yaml" ] || { echo "跳过:仓库未包含 deploy.yaml"; return 1; }
    [ -z "$prefix" ] && { echo "警告:需要 python3 + PyYAML 解析 deploy.yaml,跳过 configs 部署"; return 1; }

    entries="$work/deploy.tsv"
    errs="$work/deploy.err"
    $prefix - "$deploy_yaml" > "$entries" 2> "$errs" <<'PYEOF' || true
import os, sys, yaml

try:
    sys.stdout.reconfigure(newline="\n")
except AttributeError:
    pass

path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    data = yaml.safe_load(f)

items = (data or {}).get("deployments", [])
if not isinstance(items, list):
    sys.stderr.write("警告:deployments 必须是列表\n")
    sys.exit(1)

for item in items:
    if not isinstance(item, dict):
        continue
    src = str(item.get("src") or "").strip()
    dest = str(item.get("dest") or "").strip()
    mode = str(item.get("mode") or "copy").strip()
    if not src or not dest:
        sys.stderr.write("警告:条目缺少 src/dest\n")
        continue
    if mode != "copy":
        sys.stderr.write("警告:mode '%s' 暂不支持,跳过 %s\n" % (mode, src))
        continue
    dest = os.path.abspath(os.path.expandvars(os.path.expanduser(dest)))
    print("%s\t%s" % (src, dest))
PYEOF
    [ -s "$errs" ] && cat "$errs" >&2

    stamp=$(date +%Y%m%d%H%M%S)
    deployed=0
    skipped=0
    while IFS="$(printf '\t')" read -r src dest; do
        [ -n "$src" ] || continue
        dest=$(printf '%s' "$dest" | tr -d '\r')
        if [ ! -e "$configs_dir/$src" ]; then
            echo "    跳过:configs/$src 不存在"
            skipped=$((skipped + 1))
            continue
        fi
        mkdir -p "$(dirname "$dest")"
        if [ -e "$dest" ]; then
            mkdir -p "$dest.backup/$stamp"
            mv "$dest" "$dest.backup/$stamp/"
            echo "    已备份旧 $src -> $dest.backup/$stamp/$(basename "$dest")"
        fi
        cp -R "$configs_dir/$src" "$dest"
        echo "    已部署 $src -> $dest"
        deployed=$((deployed + 1))
    done < "$entries"
    echo "==> configs:部署 $deployed 项,跳过 $skipped 项"
}

command -v git >/dev/null 2>&1 || {
    echo "错误:未找到 git,请先安装 git"
    exit 1
}

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT INT TERM

echo "==> 克隆 $REPO_URL ($BRANCH)"
git clone --quiet --depth 1 --branch "$BRANCH" "$REPO_URL" "$tmp_dir/repo"

PY_BIN=$(find_python || true)

installed=0
for arg in "$@"; do
    if [ "$arg" = "configs" ]; then
        if deploy_configs "$tmp_dir/repo" "$PY_BIN" "$tmp_dir"; then
            installed=$((installed + 1))
        fi
        continue
    fi
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
