#!/bin/sh
# fetch-zip：从任意 http(s) 直链下载 zip 分发的技能包，解压进仓库指定目录
#
# 与 git-fetch-file 同级的内容同步工具：zip 内容落入工作区后由 git 管版本，
# 后续安装仍走 install.sh；溯源信息登记在清单 .git-remote-zips（随仓库提交）
#
# 用法:
#   ./fetch-zip.sh <url> <target> [--strip] [--force]   添加/更新单条并写清单
#   ./fetch-zip.sh pull [--force]                        重放清单全部条目
#   ./fetch-zip.sh list                                  查看已登记条目
#
# 参数:
#   --strip   剥掉 zip 内唯一的顶层包装目录（如 my-skill-1.0/SKILL.md -> SKILL.md）；
#             不传则保留原始结构。顶层结构不满足时该包同步报错
#   --force   目标目录存在未提交改动时仍强制覆盖
#
# 环境变量:
#   GIT_REMOTE_ZIPS   清单路径，默认仓库根下 .git-remote-zips（测试用）
#
# 更新语义: 先清空目标再放入，上游删除的文件不会残留；改动在 git diff 可见

set -eu

# 固定切入脚本所在目录（仓库根），保证相对路径行为一致
SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

ABS_ROOT=$PWD
MANIFEST="${GIT_REMOTE_ZIPS:-.git-remote-zips}"
TMP_BASE=".temp/fetch-zip"
PKG_ZIP="$TMP_BASE/pkg.zip"
STAGE_DIR="$TMP_BASE/stage"

# 下载产物与解压暂存的全局变量
DOWNLOAD_SHA=''

die() { printf 'fetch-zip: %s\n' "$1" >&2; exit "${2:-1}"; }

# 过程性消息走 stderr，stdout 留给数据输出
msg() { printf 'fetch-zip: %s\n' "$1" >&2; }

usage() {
cat <<'EOF'
用法:
  ./fetch-zip.sh <url> <target> [--strip] [--force]
      下载 zip 并解压到 <target>，成功后写入/更新清单记录
  ./fetch-zip.sh pull [--force]
      重放清单所有条目：sha256 无变化跳过，有变化替换
  ./fetch-zip.sh list
      列出清单中的 url / target / strip / sha256 / 日期
EOF
}

ensure_tools() {
    # 前置依赖检查，缺哪个报哪个
    for t in curl unzip sha256sum; do
        command -v "$t" >/dev/null 2>&1 || die "缺少依赖命令：$t"
    done
}

# 校验目标路径：拒绝空值、绝对路径、反斜杠与 '..' 上跳组件
is_safe_target() {
    case "$1" in ''|/*|*\\*) return 1 ;; esac
    _saved_ifs=$IFS
    IFS='/'
    for _seg in $1; do
        if [ "$_seg" = '..' ]; then
            IFS=$_saved_ifs
            return 1
        fi
    done
    IFS=$_saved_ifs
    return 0
}

# 目标在 git 工作区有未提交改动时返回 1；--force 放行并告警
check_clean_target() {
    _tgt=$1
    _force=$2
    [ -d "$_tgt" ] || return 0
    [ -n "$(git status --porcelain -- "$_tgt" 2>/dev/null)" ] || return 0
    if [ "$_force" -eq 1 ]; then
        msg "! $_tgt 有未提交改动，已按 --force 强制继续"
        return 0
    fi
    msg "$_tgt 存在未提交改动：先提交或 stash，或加 --force 重试"
    return 1
}

reset_stage() {
    rm -rf "$STAGE_DIR"
    mkdir -p "$STAGE_DIR"
}

# 下载到固定缓存路径并设置全局 DOWNLOAD_SHA；失败返回非 0（不直接退出）
download_pkg() {
    mkdir -p "$TMP_BASE"
    if ! curl -fsSL --retry 2 -o "$PKG_ZIP" "$1"; then
        msg "下载失败：$1"
        return 1
    fi
    DOWNLOAD_SHA=$(sha256sum "$PKG_ZIP" | awk '{print $1}')
}

# 完整性校验后在子 shell 内解压到暂存目录，限制恶意相对路径的影响范围
extract_pkg() {
    if ! unzip -tqq "$2" >/dev/null 2>&1; then
        msg 'zip 完整性校验失败'
        return 1
    fi
    ( cd "$1" && unzip -qo "$2" >/dev/null )
}

# 把唯一的顶层目录内容提升到暂存区根目录；结构不符时报错终止本次同步
apply_strip() {
    _stage=$1
    _top_num=$(find "$_stage" -mindepth 1 -maxdepth 1 | awk 'END{print NR}')
    if [ "$_top_num" -ne 1 ]; then
        msg "--strip 要求 zip 顶层只有一个条目，实际 $_top_num 个：$(ls -A "$_stage" | tr '\n' ' ')"
        return 1
    fi
    _wrap_dir=$(find "$_stage" -mindepth 1 -maxdepth 1 -type d)
    if [ -z "$_wrap_dir" ]; then
        msg '--strip 要求顶层唯一条目是目录，实际是文件'
        return 1
    fi
    find "$_wrap_dir" -mindepth 1 -maxdepth 1 -exec mv {} "$_stage/" \;
    rmdir "$_wrap_dir"
}

# 先清空目标再放入新内容，保证目录状态与 zip 完全一致
install_to_target() {
    mkdir -p "$2"
    find "$2" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    cp -R "$1/." "$2/"
}

# 解析清单为 TSV 一行一条：url / target / strip / sha256 / updated
manifest_to_tsv() {
    : > "$1"
    [ -f "$MANIFEST" ] || return 0
    awk '
        function flush_block() {
            if (cur_url != "")
                print cur_url "\t" cur_target "\t" cur_strip "\t" cur_sha "\t" cur_date
            cur_url = ""
        }
        /^\[zip "/ {
            flush_block()
            u = $0
            sub(/^\[zip "/, "", u)
            sub(/"\]$/, "", u)
            cur_url = u; cur_target = ""; cur_strip = "0"
            cur_sha = ""; cur_date = ""
            next
        }
        /^target *=/ { sub(/^target *= */, ""); cur_target = $0; next }
        /^strip *=/  { sub(/^strip */, "", $0); sub(/^= */, "", $0); cur_strip = $0; next }
        /^sha256 *=/ { sub(/^sha256 */, "", $0); sub(/^= */, "", $0); cur_sha = $0; next }
        /^updated *=/{ sub(/^updated */, "", $0); sub(/^= */, "", $0); cur_date = $0; next }
        END { flush_block() }
    ' "$MANIFEST" >> "$1"
}

# 以新记录替换同 URL 的旧块（不存在则追加），临时文件原子改名
upsert_manifest() {
    _tmp="$MANIFEST.tmp"
    if [ -f "$MANIFEST" ]; then
        awk -v del="$1" '
            /^\[zip "/ {
                line = $0
                sub(/^\[zip "/, "", line)
                sub(/"\]$/, "", line)
                inactive = (line == del)
                if (!inactive) print
                next
            }
            !inactive { print }
        ' "$MANIFEST" > "$_tmp"
    else
        : > "$_tmp"
    fi
    printf '[zip "%s"]\ntarget = %s\nstrip = %s\nsha256 = %s\nupdated = %s\n' \
        "$1" "$2" "$3" "$4" "$5" >> "$_tmp"
    mv "$_tmp" "$MANIFEST"
}

# 把一个 url+target 同步到位（下载之后的阶段）；返回非 0 表示失败
sync_payload() {
    _target=$1
    _strip=$2
    reset_stage
    if ! extract_pkg "$STAGE_DIR" "$ABS_ROOT/$PKG_ZIP"; then
        return 1
    fi
    if [ "$_strip" -eq 1 ]; then
        if ! apply_strip "$STAGE_DIR"; then
            return 1
        fi
    fi
    install_to_target "$STAGE_DIR" "$_target"
}

cmd_add() {
    # add 用法：url 与 target 为位置参数，其后只接受标志位
    if [ $# -lt 2 ]; then
        usage
        exit 1
    fi
    _url=$1
    _target=${2%/}
    shift 2
    _strip=0
    _force=0
    while [ $# -gt 0 ]; do
        case $1 in
            --strip) _strip=1 ;;
            --force) _force=1 ;;
            *) die "未知参数：$1（add 支持 --strip / --force）" ;;
        esac
        shift
    done
    case $_url in
        https://*|http://*) ;;
        *) die 'url 仅支持 http(s) 直链' ;;
    esac
    case $_url in *'"'*) die 'url 不能包含双引号' ;; esac
    is_safe_target "$_target" || die "非法目标路径：$_target"
    if ! check_clean_target "$_target" "$_force"; then
        exit 1
    fi
    download_pkg "$_url" || exit 1
    if ! sync_payload "$_target" "$_strip"; then
        exit 1
    fi
    _file_cnt=$(find "$_target" -type f | awk 'END{print NR}')
    upsert_manifest "$_url" "$_target" "$_strip" "$DOWNLOAD_SHA" "$(date +%F)"
    msg "完成：$_target <- $_url（$_file_cnt 个文件）"
    msg "sha256: $DOWNLOAD_SHA"
    if [ ! -f "$_target/SKILL.md" ]; then
        msg "提示：$_target 下未见 SKILL.md，请确认包结构与技能目录约定一致"
    fi
    msg "下一步：审查 git diff 并提交；以后用 ./fetch-zip.sh pull 更新此包"
}

cmd_pull() {
    # 重放清单：逐条下载比对 hash，变化才重新解压落位并回写登记
    _force=0
    while [ $# -gt 0 ]; do
        case $1 in
            --force) _force=1 ;;
            *) die "未知参数：$1（pull 仅支持 --force）" ;;
        esac
        shift
    done
    if [ ! -f "$MANIFEST" ]; then
        msg "清单不存在（$MANIFEST），先执行一次 ./fetch-zip.sh <url> <target>"
        return 0
    fi
    _records="$TMP_BASE/records.tsv"
    manifest_to_tsv "$_records"
    _total=0; _changed=0; _skipped=0; _failed=0
    while IFS="$(printf '\t')" read -r _u _t _s _h _date_orig; do
        [ -n "$_u" ] || continue
        _total=$((_total + 1))
        msg "—— pull：$_u"
        if ! is_safe_target "$_t"; then
            msg "非法 target：'$_t'，跳过"
            _failed=$((_failed + 1))
            continue
        fi
        if ! check_clean_target "$_t" "$_force"; then
            _failed=$((_failed + 1))
            continue
        fi
        if ! download_pkg "$_u"; then
            _failed=$((_failed + 1))
            continue
        fi
        # 内容无变化且目标非空：免解压，保持现状
        if [ "$DOWNLOAD_SHA" = "$_h" ] && [ -n "$(ls -A "$_t" 2>/dev/null)" ]; then
            msg "   无变化，跳过"
            _skipped=$((_skipped + 1))
            continue
        fi
        if ! sync_payload "$_t" "$_s"; then
            _failed=$((_failed + 1))
            continue
        fi
        upsert_manifest "$_u" "$_t" "$_s" "$DOWNLOAD_SHA" "$(date +%F)"
        msg "   已更新（sha256: $DOWNLOAD_SHA）"
        _changed=$((_changed + 1))
    done < "$_records"
    msg "pull 完成：共 $_total 条，更新 $_changed，跳过 $_skipped，失败 $_failed"
    [ "$_failed" -eq 0 ]
}

cmd_list() {
    _records="$TMP_BASE/list.tsv"
    manifest_to_tsv "$_records"
    if [ ! -s "$_records" ]; then
        msg "(清单为空)"
        return 0
    fi
    while IFS="$(printf '\t')" read -r _u _t _s _h _l_date; do
        _short=$(printf '%s' "$_h" | cut -c1-12)
        printf '%s\n  -> %s  strip=%s  %s  %s\n' "$_u" "$_t" "$_s" "$_short" "$_l_date"
    done < "$_records"
}

main() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi
    _subcmd=$1
    shift
    case $_subcmd in
        pull)             ensure_tools; cmd_pull "$@" ;;
        list)             cmd_list ;;
        help|-h|--help)   usage ;;
        *)                ensure_tools; cmd_add "$_subcmd" "$@" ;;
    esac
}

main "$@"
