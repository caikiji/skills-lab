"""cardify 核心：卡片 markdown 的解析、校验与序列化。

build_html.py 与 parse_html.py 共用本模块。
硬约束阈值的唯一定义处，references/style-rules.md 与此处冲突时以本文件为准。
"""

import json
import re
from dataclasses import dataclass, field

# ---- 硬约束常量 ----

CARD_TYPES: tuple[str, ...] = ("总卡", "概念卡", "流程卡", "决策卡", "陷阱卡", "接口卡")
BANNED_WORDS: tuple[str, ...] = (
    "本质", "核心", "赋能", "闭环", "范式", "护城河", "引擎", "中枢", "关键",
    "深度", "价值", "智能", "高效", "强大", "优雅", "完美", "无缝", "打通",
)
MIN_TOTAL: int = 4
MAX_TOTAL: int = 9
TITLE_MAX: int = 12
ONE_BODY_MIN: int = 8   # 一句话正文下限：防电报体（锚点不计入）
ONE_BODY_MAX: int = 40  # 一句话正文上限：防长句（锚点不计入）
POINT_MAX: int = 5
POINT_BODY_MIN: int = 12  # 要点正文下限：防电报体（锚点不计入）
POINT_BODY_MAX: int = 60  # 要点正文上限：防长文（锚点不计入）
CODE_MAX_LINES: int = 15
CODE_SPAN_MIN: int = 5   # 代码引用最小跨度：单行引用看不到逻辑
CODE_SPAN_MAX: int = 20  # 代码引用最大跨度：太长破坏浓缩
# 动作词标记：要点必须含其一，否则是纯符号罗列不成知识
VERB_MARKERS: tuple[str, ...] = (
    "负责", "用于", "因为", "触发", "校验", "检查", "保存", "读取", "发送",
    "计算", "判断", "选择", "优先", "重置", "累计", "共享", "写入", "查询",
    "调用", "返回", "失败", "成功", "支持", "防止", "避免", "基于", "通过",
    "进入", "生成", "执行", "更新", "记录", "派生", "随机", "替换", "剔除",
    "模拟", "统计", "上报", "注册", "解析", "转换", "监听", "超时", "重试",
    "保护", "拦截", "限制", "依赖", "实现", "扣费", "抽取", "掉落", "回包",
    "查重", "流转", "判定", "命中", "展示", "复用", "等待", "收取", "落单",
    "置位", "清除", "合并", "分发", "同步", "缓存", "匹配", "排序", "过滤",
    "聚合", "分组", "监控", "降级", "限流", "补偿",
)

ANCHOR_RE = re.compile(r"（([^（）\n]{1,60})）")  # 锚点：成对中文括号，捕获组为括号内容
CODE_REF_RE = re.compile(r"([A-Za-z0-9_./\\-]+):(\d+)(?:~(\d+))?")  # 文件:行号 或 文件:起始~结束
DIR_REF_RE = re.compile(r"^[\w./\\-]+/$")  # 目录锚点（模块级引用）
CARD_HEAD_RE = re.compile(r"^◆ 卡 (\d+)/(\d+) ｜ (.+)$")
ONE_RE = re.compile(r"^一句话：(.*)$")
LINK_RE = re.compile(r"^关联：(.*)$")
POINT_RE = re.compile(r"^- (.*)$")
TOPIC_RE = re.compile(r"^# (.+)$")
LINK_PART_RE = re.compile(r"^[←→] 卡(\d+)$")


@dataclass
class CodeRef:
    """代码引用：文件与行范围（start==end 表单行）。"""

    file: str
    start: int
    end: int


@dataclass
class Card:
    """一张卡片。"""

    num: int
    total: int
    ctype: str
    title: str
    one: str = ""
    points: list[str] = field(default_factory=list)
    code: str = ""
    links_in: list[int] = field(default_factory=list)
    links_out: list[int] = field(default_factory=list)
    line: int = 0


def parse_md(text: str) -> tuple[list[Card], list[str]]:
    """解析卡片 markdown。返回卡片列表与全部错误（带行号）。"""
    cards: list[Card] = []
    errors: list[str] = []
    topic = ""
    current: Card | None = None
    in_code = False
    code_lines: list[str] = []

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if in_code:
            if line.strip() == "```":
                if current is not None:
                    current.code = "\n".join(code_lines)
                in_code = False
            else:
                code_lines.append(line)
            continue
        if line.strip() == "```":
            if current is None:
                errors.append(f"第 {lineno} 行：代码块出现在卡片外")
            else:
                in_code = True
                code_lines = []
            continue
        head = CARD_HEAD_RE.match(line)
        if head:
            if current is not None:
                cards.append(current)
            current = _start_card(head, lineno, errors)
            continue
        topic_match = TOPIC_RE.match(line)
        if topic_match:
            topic = topic_match.group(1).strip()
            continue
        if current is None:
            if line.strip():
                errors.append(f"第 {lineno} 行：内容出现在卡片块外")
            continue
        one = ONE_RE.match(line)
        if one:
            current.one = one.group(1).strip()
            continue
        point = POINT_RE.match(line)
        if point:
            current.points.append(point.group(1).strip())
            continue
        link = LINK_RE.match(line)
        if link:
            errors.extend(_parse_links(current, link.group(1), lineno))
            continue
        if line.strip():
            errors.append(f"第 {lineno} 行：无法识别的行")
    if in_code:
        errors.append("代码块未闭合")
    if current is not None:
        cards.append(current)
    errors.extend(validate(topic, cards))
    return cards, errors


def _start_card(m: re.Match[str], lineno: int, errors: list[str]) -> Card | None:
    """解析卡片头，语法错误时记错并返回 None。"""
    num, total = int(m.group(1)), int(m.group(2))
    ctype, sep, title = m.group(3).partition(" · ")
    if not sep:
        errors.append(f"第 {lineno} 行：卡片头缺 ` · `，格式 `◆ 卡 N/M ｜ <类型> · <标题>`")
        return None
    return Card(num=num, total=total, ctype=ctype.strip(), title=title.strip(), line=lineno)


def _parse_links(card: Card, text: str, lineno: int) -> list[str]:
    """解析关联行，返回该行的错误。"""
    errors: list[str] = []
    for part in text.split("｜"):
        part = part.strip()
        if not part:
            continue
        m = LINK_PART_RE.match(part)
        if m is None:
            errors.append(f"第 {lineno} 行：关联语法错误，应为 `← 卡N` 或 `→ 卡M`")
            continue
        target = int(m.group(1))
        if part.startswith("←"):
            card.links_in.append(target)
        else:
            card.links_out.append(target)
    return errors


def validate(topic: str, cards: list[Card]) -> list[str]:
    """按硬约束校验卡片列表，返回全部错误。"""
    errors: list[str] = []
    if not cards:
        return ["文件里没有卡片块"]
    total = cards[0].total
    if not (MIN_TOTAL <= total <= MAX_TOTAL):
        errors.append(f"总张数须为 {MIN_TOTAL}~{MAX_TOTAL}（1 总卡 + 3~8 子卡），当前 {total}")
    if any(c.total != total for c in cards):
        errors.append("各卡头的 /M 不一致")
    nums = [c.num for c in cards]
    if sorted(nums) != list(range(1, total + 1)):
        errors.append(f"卡号须为 1..{total} 连续编号，当前 {sorted(nums)}")
    if cards[0].ctype != "总卡":
        errors.append("第一张卡必须是总卡")
    if not any(c.ctype == "决策卡" for c in cards):
        errors.append("每套卡片至少 1 张决策卡：记录设计取舍与原因")
    for card in cards:
        errors.extend(validate_card(card, cards))
    return errors


def validate_card(card: Card, cards: list[Card]) -> list[str]:
    """校验单张卡，返回错误列表。"""
    errors: list[str] = []
    where = f"卡{card.num}"
    if card.ctype not in CARD_TYPES:
        errors.append(f"{where}：类型须为 {CARD_TYPES} 之一，当前 {card.ctype}")
    if not card.title:
        errors.append(f"{where}：缺标题")
    elif len(card.title) > TITLE_MAX:
        errors.append(f"{where}：标题超 {TITLE_MAX} 字")
    elif card.title[0].isascii() and card.title[0].isupper():
        errors.append(f"{where}：标题不得以大写标识符开头，请用中文概念命名")
    if not card.one:
        errors.append(f"{where}：缺一句话")
    else:
        body = ANCHOR_RE.sub("", card.one)
        if len(body) < ONE_BODY_MIN:
            errors.append(f"{where}：一句话正文 {len(body)} 字不足 {ONE_BODY_MIN} 字")
        if len(body) > ONE_BODY_MAX:
            errors.append(f"{where}：一句话正文超 {ONE_BODY_MAX} 字（锚点不计入）")
        if not ANCHOR_RE.search(card.one):
            errors.append(f"{where}：一句话缺锚点（成对中文括号内的代码实体）")
    if not card.points:
        errors.append(f"{where}：至少一条要点")
    if card.ctype == "总卡":
        errors.extend(validate_index(card, cards))
    else:
        errors.extend(validate_points(card))
    errors.extend(validate_code(card))
    errors.extend(validate_anchors(card))
    errors.extend(validate_links(card, cards[0].total))
    errors.extend(check_banned(where, card.one))
    for idx, point in enumerate(card.points, start=1):
        errors.extend(check_banned(f"{where}要点{idx}", point))
    return errors


def validate_index(card: Card, cards: list[Card]) -> list[str]:
    """校验总卡要点与子卡标题一一对应，返回错误列表。"""
    errors: list[str] = []
    sub_titles = [c.title for c in cards if c.num != card.num]
    for point in card.points:
        if point not in sub_titles:
            errors.append(f"卡{card.num}：总卡要点须与子卡标题一致，多余项 {point}")
    for c in cards:
        if c.num != card.num and c.title not in card.points:
            errors.append(f"卡{card.num}：总卡缺子卡标题 {c.title}")
    return errors


def validate_points(card: Card) -> list[str]:
    """校验子卡要点，返回错误列表。"""
    errors: list[str] = []
    where = f"卡{card.num}"
    if len(card.points) > POINT_MAX:
        errors.append(f"{where}：要点超 {POINT_MAX} 条")
    for idx, point in enumerate(card.points, start=1):
        body = ANCHOR_RE.sub("", point)
        if len(body) < POINT_BODY_MIN:
            errors.append(f"{where}要点{idx}：正文 {len(body)} 字不足 {POINT_BODY_MIN} 字，请写全机制（触发条件/动作/后果）")
        if len(body) > POINT_BODY_MAX:
            errors.append(f"{where}要点{idx}：正文超 {POINT_BODY_MAX} 字（锚点不计入），请拆分")
        if "。" in point:
            errors.append(f"{where}要点{idx}：只能一个句子，去掉句号或拆成多条")
        if not ANCHOR_RE.search(point):
            errors.append(f"{where}要点{idx}：缺锚点（成对中文括号内写代码实体或 文件:行号）")
        if point[0].isascii() and (point[0].isupper() or point[0] == "_"):
            errors.append(f"{where}要点{idx}：不得以大写标识符开头，用中文陈述事实、符号只进锚点")
        if not any(marker in point for marker in VERB_MARKERS):
            errors.append(f"{where}要点{idx}：缺动作词，纯符号罗列不成知识")
    return errors


def validate_anchors(card: Card) -> list[str]:
    """C15/C16：锚点须含 文件:行号 或为目录路径，代码引用必须为 5~20 行范围。"""
    errors: list[str] = []
    texts: list[tuple[str, str]] = [("一句话", card.one)]
    texts.extend((f"要点{idx}", p) for idx, p in enumerate(card.points, start=1))
    for label, text in texts:
        for m in ANCHOR_RE.finditer(text):
            content = m.group(1)
            if DIR_REF_RE.match(content):
                continue
            for ref in CODE_REF_RE.finditer(content):
                start = int(ref.group(2))
                end = int(ref.group(3)) if ref.group(3) else start
                span = end - start + 1
                if span < CODE_SPAN_MIN:
                    errors.append(
                        f"卡{card.num}{label}：代码引用须为范围 文件:起始~结束（跨度 {CODE_SPAN_MIN}~{CODE_SPAN_MAX} 行），"
                        f"单行引用看不到逻辑（{ref.group(0)}）"
                    )
                    break
                if span > CODE_SPAN_MAX:
                    errors.append(
                        f"卡{card.num}{label}：代码引用跨度 {span} 行超上限 {CODE_SPAN_MAX} 行，请缩小到逻辑块（{ref.group(0)}）"
                    )
                    break
            if not CODE_REF_RE.search(content):
                errors.append(
                    f"卡{card.num}{label}：锚点须含 文件:行号 或目录路径，纯符号名无法回代码验证（{content}）"
                )
    return errors


def validate_code(card: Card) -> list[str]:
    """校验代码块行数，返回错误列表。"""
    if card.code and len(card.code.splitlines()) > CODE_MAX_LINES:
        return [f"卡{card.num}：代码块超 {CODE_MAX_LINES} 行"]
    return []


def validate_links(card: Card, total: int) -> list[str]:
    """校验关联卡号，返回错误列表。"""
    errors: list[str] = []
    for target in card.links_in + card.links_out:
        if not (1 <= target <= total):
            errors.append(f"卡{card.num}：关联卡号 {target} 超出 1..{total}")
        elif target == card.num:
            errors.append(f"卡{card.num}：不能关联自身")
    return errors


def check_banned(where: str, text: str) -> list[str]:
    """检查禁用词，返回错误列表。"""
    errors: list[str] = []
    for word in BANNED_WORDS:
        if word in text:
            errors.append(f"{where}：出现禁用词「{word}」，请改写成具体描述")
    return errors


def extract_code_refs(card: Card) -> list[CodeRef]:
    """提取卡片内全部 文件:行号 引用（一句话+要点，按文件+行范围去重）。"""
    refs: list[CodeRef] = []
    seen: set[tuple[str, int, int]] = set()
    for text in [card.one, *card.points]:
        for m in CODE_REF_RE.finditer(text):
            start = int(m.group(2))
            end = int(m.group(3)) if m.group(3) else start
            key = (m.group(1), start, end)
            if key in seen:
                continue
            seen.add(key)
            refs.append(CodeRef(file=m.group(1), start=start, end=end))
    return refs


def render_md(topic: str, cards: list[Card]) -> str:
    """把卡片列表还原为 markdown 文本。"""
    lines: list[str] = []
    if topic:
        lines.append(f"# {topic}")
        lines.append("")
    for card in cards:
        lines.append(f"◆ 卡 {card.num}/{card.total} ｜ {card.ctype} · {card.title}")
        if card.one:
            lines.append(f"一句话：{card.one}")
        lines.extend(f"- {p}" for p in card.points)
        if card.code:
            lines.append("```")
            lines.append(card.code)
            lines.append("```")
        links = [f"← 卡{n}" for n in card.links_in] + [f"→ 卡{n}" for n in card.links_out]
        if links:
            lines.append("关联：" + " ｜ ".join(links))
        lines.append("")
    return "\n".join(lines)


def cards_to_json(topic: str, cards: list[Card]) -> dict:
    """卡片列表转可内嵌 HTML 的 JSON 字典。"""
    return {
        "topic": topic,
        "total": cards[0].total if cards else 0,
        "cards": [
            {
                "num": c.num,
                "type": c.ctype,
                "title": c.title,
                "one": c.one,
                "points": c.points,
                "code": c.code,
                "linksIn": c.links_in,
                "linksOut": c.links_out,
            }
            for c in cards
        ],
    }


def json_to_cards(data: dict) -> tuple[str, list[Card]]:
    """JSON 字典转主题与卡片列表。"""
    topic = str(data.get("topic", ""))
    cards = [
        Card(
            num=item["num"], total=data["total"], ctype=item["type"],
            title=item["title"], one=item.get("one", ""),
            points=item.get("points", []), code=item.get("code", ""),
            links_in=item.get("linksIn", []), links_out=item.get("linksOut", []),
        )
        for item in data["cards"]
    ]
    return topic, cards


if __name__ == "__main__":
    import sys

    for path in sys.argv[1:]:
        cards, errors = parse_md(open(path, encoding="utf-8").read())
        print(path, "OK" if not errors else "\n".join(errors))
