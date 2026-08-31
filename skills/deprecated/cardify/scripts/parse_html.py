"""cardify 反推器：从构建产物 HTML 提取内嵌卡片数据。

用法：
  python parse_html.py <视图.html>        输出 JSON
  python parse_html.py <视图.html> --md   还原 markdown
"""

import argparse
import json
import re
import sys
from pathlib import Path

from cardfmt import json_to_cards, render_md

DATA_RE = re.compile(
    r'<script type="application/json" id="cards-data">(.*?)</script>', re.S
)


def extract(html: str) -> dict:
    """从 HTML 提取内嵌卡片 JSON，失败时打印错误并退出。"""
    m = DATA_RE.search(html)
    if m is None:
        print("错误: 未找到内嵌卡片数据，请确认文件由 build_html.py 生成")
        sys.exit(1)
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        print(f"错误: 内嵌数据不是合法 JSON：{exc}")
        sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    """入口：提取并输出 JSON 或 markdown。"""
    parser = argparse.ArgumentParser(description="从 cardify HTML 提取卡片")
    parser.add_argument("file", help="由 build_html.py 生成的 HTML")
    parser.add_argument("--md", action="store_true", help="还原 markdown 而非 JSON")
    args = parser.parse_args(argv)
    path = Path(args.file)
    if not path.exists():
        print(f"错误: 文件不存在 {path}")
        return 1
    data = extract(path.read_text(encoding="utf-8"))
    if args.md:
        topic, cards = json_to_cards(data)
        print(render_md(topic, cards), end="")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
