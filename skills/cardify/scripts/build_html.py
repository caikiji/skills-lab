"""cardify 构建器：markdown → 校验 → 单文件 HTML。

用法：
  python build_html.py --check <卡片.md>                    只校验
  python build_html.py <卡片.md> -o <视图.html>             构建单文件 HTML
  python build_html.py <卡片.md> --root <项目根>            显式指定代码引用基准目录
"""

import argparse
import json
import re
import sys
from pathlib import Path

from cardfmt import Card, cards_to_json, extract_code_refs, parse_md

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "templates"
VENDOR_FILE = SKILL_DIR / "vendor" / "vis-network.min.js"
HLJS_FILE = SKILL_DIR / "vendor" / "highlight.min.js"
HLJS_CSS_LIGHT = SKILL_DIR / "vendor" / "highlight-github.css"
HLJS_CSS_DARK = SKILL_DIR / "vendor" / "highlight-github-dark.css"
JSON_PLACEHOLDER = "__CARDS_JSON__"
VENDOR_PLACEHOLDER = "<!-- VENDOR_JS -->"
HLJS_PLACEHOLDER = "<!-- HLJS_JS -->"
HLJS_CSS_PLACEHOLDER = "/*__HLJS_CSS__*/"
STYLE_PLACEHOLDER = "/*__STYLE__*/"
APP_PLACEHOLDER = "/*__APP_JS__*/"
# 只转义真正的危险序列：内联脚本提前闭合。全局 </ 会破坏正则字面量（如 /</）
SCRIPT_END_RE = re.compile(r"</script", re.IGNORECASE)


def safe_inline(text: str) -> str:
    """转义 </script 序列，返回可安全内联进 HTML 的文本。"""
    return SCRIPT_END_RE.sub(r"<\\/script", text)


def read_asset(name: str) -> str:
    """读取模板目录下的资源文件，缺失时报错。"""
    path = TEMPLATE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"缺少模板资源 {path}")
    return path.read_text(encoding="utf-8")


def default_root(src: Path) -> Path:
    """推断项目根：卡片文件默认位于 <项目根>/.temp/cardify/ 下。"""
    return src.resolve().parents[2]


def resolve_code(cards: list[Card], root: Path) -> tuple[dict[int, list[dict]], list[str]]:
    """读取卡片引用的代码片段，返回按卡号分组的代码块与错误列表。"""
    blocks: dict[int, list[dict]] = {}
    errors: list[str] = []
    for card in cards:
        card_blocks: list[dict] = []
        for ref in extract_code_refs(card):
            path = (root / ref.file).resolve()
            if not path.exists():
                errors.append(f"卡{card.num}：代码引用文件不存在 {ref.file}")
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            if ref.end > len(lines):
                errors.append(f"卡{card.num}：行号 {ref.end} 超出 {ref.file} 总行数 {len(lines)}")
                continue
            text = "\n".join(lines[ref.start - 1:ref.end])
            card_blocks.append({"file": ref.file, "start": ref.start, "end": ref.end, "text": text})
        if card_blocks:
            blocks[card.num] = card_blocks
    return blocks, errors


def print_errors(path: Path, errors: list[str]) -> None:
    """打印校验失败信息。"""
    print(f"{path} 校验失败：")
    for err in errors:
        print(f"  错误: {err}")


def check_file(path: Path, root: Path) -> int:
    """校验卡片文件与代码引用，打印结果并返回退出码。"""
    cards, errors = parse_md(path.read_text(encoding="utf-8"))
    if errors:
        print_errors(path, errors)
        return 1
    blocks, ref_errors = resolve_code(cards, root)
    if ref_errors:
        print_errors(path, ref_errors)
        return 1
    total_blocks = sum(len(b) for b in blocks.values())
    print(f"校验通过：共 {len(cards)} 张卡（1 总卡 + {len(cards) - 1} 子卡），提取 {total_blocks} 个代码块")
    return 0


def build_file(path: Path, out: Path, root: Path) -> int:
    """校验并把卡片构建为单文件 HTML，返回退出码。"""
    cards, errors = parse_md(path.read_text(encoding="utf-8"))
    if errors:
        print_errors(path, errors)
        return 1
    blocks, ref_errors = resolve_code(cards, root)
    if ref_errors:
        print_errors(path, ref_errors)
        return 1
    data = cards_to_json(path.stem, cards)
    for item in data["cards"]:
        item["codeBlocks"] = blocks.get(item["num"], [])
    payload = safe_inline(json.dumps(data, ensure_ascii=False))
    if not VENDOR_FILE.exists():
        print(f"错误: 缺少 {VENDOR_FILE}，请重新拉取技能")
        return 1
    for f in (HLJS_FILE, HLJS_CSS_LIGHT, HLJS_CSS_DARK):
        if not f.exists():
            print(f"错误: 缺少 {f}，请重新拉取技能")
            return 1
    vendor = safe_inline(VENDOR_FILE.read_text(encoding="utf-8"))
    hljs = safe_inline(HLJS_FILE.read_text(encoding="utf-8"))
    hljs_css = (
        "@media (prefers-color-scheme: light) {\n"
        + HLJS_CSS_LIGHT.read_text(encoding="utf-8")
        + "\n}\n@media (prefers-color-scheme: dark) {\n"
        + HLJS_CSS_DARK.read_text(encoding="utf-8")
        + "\n}"
    )
    html = read_asset("view.html")
    html = html.replace(HLJS_CSS_PLACEHOLDER, hljs_css)
    html = html.replace(STYLE_PLACEHOLDER, read_asset("style.css"))
    html = html.replace(APP_PLACEHOLDER, read_asset("app.js"))
    html = html.replace(VENDOR_PLACEHOLDER, f"<script>\n{vendor}\n</script>")
    html = html.replace(HLJS_PLACEHOLDER, f"<script>\n{hljs}\n</script>")
    html = html.replace(JSON_PLACEHOLDER, payload)
    out.write_text(html, encoding="utf-8")
    print(f"已生成 {out}（{out.stat().st_size // 1024} KB）")
    return 0


def main(argv: list[str] | None = None) -> int:
    """入口：解析参数并分发到校验或构建。"""
    parser = argparse.ArgumentParser(description="cardify 校验与 HTML 构建")
    parser.add_argument("file", help="卡片 markdown 文件")
    parser.add_argument("-o", "--output", help="HTML 输出路径（默认同名 .html）")
    parser.add_argument("--check", action="store_true", help="只校验，不构建")
    parser.add_argument("--root", help="代码引用基准目录（默认卡片文件祖父目录）")
    args = parser.parse_args(argv)
    src = Path(args.file)
    if not src.exists():
        print(f"错误: 文件不存在 {src}")
        return 1
    root = Path(args.root).resolve() if args.root else default_root(src)
    if args.check:
        return check_file(src, root)
    out = Path(args.output) if args.output else src.with_suffix(".html")
    return build_file(src, out, root)


if __name__ == "__main__":
    sys.exit(main())
