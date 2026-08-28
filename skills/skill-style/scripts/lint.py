#!/usr/bin/env python3
"""SKILL.md 质量机检：执行 skill-style 红线中可自动判定的项。

用法：python lint.py <技能目录或 SKILL.md 路径>...（目录须直接包含 SKILL.md）
检查分三类：元数据/链接硬校验、词表扫描（中英双语，扩词直接改顶部常量）、
散文段结构检查。frontmatter 解析支持单行键值与 YAML 块标量（>- 与 | 系）。
退出码：有 error 为 1，否则 0。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

SOFT_LINE_LIMIT = 60
HARD_LINE_LIMIT = 120
DESC_CHAR_LIMIT = 300
DUP_MIN_CHARS = 12
# 连续散文行达到该数量判为论述段（R4）；单行/超长阈值见 PROSE_*_CHARS
PROSE_BLOCK_LIMIT = 3
# 非结构化单行达到该字符数判为长段散文（R4）
PROSE_LINE_CHARS = 200
# 任何形态（含编号列表项、表格行）超过该长度判为内容臃肿（R4）
EXTREME_LINE_CHARS = 300

# R4 哲学/励志/叙述填充特征词，命中即 error；中英混排，匹配不分大小写。
# 扩词方式：从问题文件统计频率、并用自家人文件做阴性对照后收录。
PHILOSOPHY_WORDS: tuple[str, ...] = (
    "本质是", "本质在于", "旨在", "致力于", "宝贵的", "愿景",
    "核心理念", "设计理念", "设计思想", "取舍权", "喧宾夺主",
    "应运而生", "至关重要", "不可或缺", "赋能", "事半功倍",
    "保驾护航", "让我们", "有的放矢",
    "essentially", "importantly,", "seamless", "empower",
    "ecosystem", "philosophy", "game changer", "let's ", "let us ",
    "of course,", "goes without saying", "feel free", "in lieu of",
    "at a high level", "this is important", "productively",
)
# R4 元叙述/类比标记：来源、动机、原理类说明（使用方不关心），命中即 error
# 收录依据：herdr-flows 会话中出现过的“这是我们实战跑出来的”“实测不生效”等写法
NARRATIVE_WORDS: tuple[str, ...] = (
    "我们实战", "实战跑出来", "经验教训", "踩坑", "我们发现", "据此",
    "实测不生效", "实测发现", "实测验证", "实测证明",
    "与官方一致", "与官方不同", "此处以",
    "打个比方", "相当于", "类比", "比喻", "说白了",
)
# R5 不可度量表述特征词，命中即 warn；扩词规则同上
VAGUE_WORDS: tuple[str, ...] = (
    "适当", "酌情", "尽量", "适时", "必要时", "尽可能",
    "视情况", "适量", "适度", "一般而言",
    "try to ", "consider ", "appropriately", "reasonably",
    "preferably", "as needed", "generally ",
    "figure out", "come up with", "best practices", "flexible",
    "proactively ", "you'll ", "you should ", "you can also",
    "it's ok to", "worth noting", "keep in mind",
    "delve", "leverage ", "comprehensive", "vibe ",
)

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
META_KEY_RE = re.compile(r"^([A-Za-z_-]+):\s*(.*)$")
# YAML 块标量标记：值在后续缩进行里
BLOCK_SCALARS = {">-", ">", ">+", "|-", "|", "|+"}
FENCE_RE = re.compile(r"^(?:`{3,}|~{3,})")
NUM_ITEM_RE = re.compile(r"^(?:\d+[.、)]|[-*+]\s)")
# 行内代码段在扫描前剥离：引用违禁词举例属"提及"而非"使用"
INLINE_CODE_RE = re.compile(r"`[^`]*`")


class Finding(NamedTuple):
    """单条检查结果；line 为 None 表示针对整个文件。"""

    level: str  # "E" 或 "W"
    path: Path
    line: int | None
    msg: str


def split_frontmatter(text: str) -> tuple[dict[str, str], int]:
    """返回 (元数据字典, 正文起始零基行号)；支持块标量续行，无 frontmatter 时从第 0 行起。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta: dict[str, str] = {}
    idx = 1
    while idx < len(lines):
        line = lines[idx]
        if line.strip() == "---":
            return meta, idx + 1
        m = META_KEY_RE.match(line)
        if m is None:
            idx += 1
            continue
        if m.group(2).strip() in BLOCK_SCALARS:
            chunks: list[str] = []
            idx += 1
            while (
                idx < len(lines)
                and lines[idx].strip() != "---"
                and (not lines[idx].strip() or lines[idx][:1] in " \t")
            ):
                chunks.append(lines[idx].strip())
                idx += 1
            meta[m.group(1)] = " ".join(c for c in chunks if c)
        else:
            meta[m.group(1)] = m.group(2).strip()
            idx += 1
    return meta, 0


def strip_code_fences(text: str, base: int) -> tuple[str, list[int]]:
    """删除围栏代码块，返回 (剩余文本, 各剩余行的原始 1 基行号)。"""
    kept: list[str] = []
    linenos: list[int] = []
    inside = False
    for offset, line in enumerate(text.splitlines()):
        if FENCE_RE.match(line.strip()):
            inside = not inside
            continue
        if not inside:
            kept.append(line)
            linenos.append(base + offset + 1)
    return "\n".join(kept), linenos


def check_meta(path: Path, meta: dict[str, str], findings: list[Finding]) -> None:
    """R1/R2：元数据完整性与 description 长度。"""
    if not meta:
        findings.append(Finding("E", path, None, "R1 缺少 frontmatter"))
        return
    for key in ("name", "description"):
        if key not in meta or not meta[key]:
            findings.append(Finding("E", path, None, f"R1 frontmatter 缺 {key}"))
    if path.parent.name and meta.get("name") not in (None, path.parent.name):
        findings.append(Finding("E", path, None, f"R1 name({meta.get('name')}) 与目录名不一致"))
    desc = meta.get("description", "")
    if len(desc) > DESC_CHAR_LIMIT:
        findings.append(Finding("W", path, None, f"R2 description {len(desc)} 字符 > {DESC_CHAR_LIMIT}"))


def check_lines(path: Path, text: str, findings: list[Finding]) -> None:
    """R3：全文行数预算。"""
    n = len(text.splitlines())
    if n > HARD_LINE_LIMIT:
        findings.append(Finding("E", path, None, f"R3 全文 {n} 行 > 硬上限 {HARD_LINE_LIMIT}"))
    elif n > SOFT_LINE_LIMIT:
        findings.append(Finding("W", path, None, f"R3 全文 {n} 行 > 目标 {SOFT_LINE_LIMIT}，建议拆分"))


def scan_words(
    path: Path,
    body: str,
    linenos: list[int],
    words: tuple[str, ...],
    level: str,
    rule: str,
    findings: list[Finding],
) -> None:
    """大小写无关地扫描特征词，同一行同一词只报一次；linenos 与 body 行一一对应。"""
    lowered_words = [(w, w.lower()) for w in words]
    for offset, line in enumerate(body.splitlines()):
        low_line = INLINE_CODE_RE.sub("", line).lower()
        for display, needle in lowered_words:
            if needle in low_line:
                findings.append(
                    Finding(level, path, linenos[offset], f"{rule} 特征词「{display}」")
                )


def is_structured(line: str) -> bool:
    """判定一行是否为结构化内容（列表/表格/标题/引用/空行）。"""
    stripped = line.strip()
    return (not stripped) or stripped[:1] in "#>|>`" or bool(NUM_ITEM_RE.match(stripped))


def check_prose(
    path: Path,
    body: str,
    linenos: list[int],
    findings: list[Finding],
) -> None:
    """R4 结构检查：连续散文块、超长散文行、任何形态的超长行。"""
    block: list[int] = []

    def flush() -> None:
        """把当前积累的散文块按长度阈值上报，并清空缓冲。"""
        if len(block) >= PROSE_BLOCK_LIMIT:
            first, last = block[0], block[-1]
            span = f"第 {first} 行" if first == last else f"第 {first}-{last} 行"
            findings.append(Finding("E", path, first, f"R4 连续 {len(block)} 行散文叙述（{span}）"))
        block.clear()

    for offset, line in enumerate(body.splitlines()):
        stripped = line.strip()
        length = len(stripped)
        if length >= EXTREME_LINE_CHARS:
            findings.append(Finding("E", path, linenos[offset], f"R4 超长行 {length} 字符"))
            continue
        if is_structured(line):
            flush()
            continue
        if length >= PROSE_LINE_CHARS:
            findings.append(Finding("E", path, linenos[offset], f"R4 单行长段散文 {length} 字符"))
            continue
        block.append(linenos[offset])
    flush()


def check_duplicates(path: Path, body: str, findings: list[Finding]) -> None:
    """R6：正文中较长语句不得原样出现在 references/ 文件里（双方均已去代码围栏）。"""
    dup_candidates = {
        line.strip()
        for line in body.splitlines()
        if len(line.strip()) >= DUP_MIN_CHARS and line.strip()[:1] not in "|<>#`"
    }
    ref_dir = path.parent / "references"
    if not ref_dir.is_dir():
        return
    seen: set[str] = set()
    for ref in sorted(ref_dir.rglob("*.md")):
        ref_body, _ = strip_code_fences(ref.read_text(encoding="utf-8"), 0)
        for line in ref_body.splitlines():
            stripped = line.strip()
            if stripped in dup_candidates and stripped not in seen:
                seen.add(stripped)
                findings.append(
                    Finding("W", path, None, f"R6 语句同时出现在 {ref.name}：「{stripped[:30]}…」")
                )


def check_links(path: Path, text: str, findings: list[Finding]) -> None:
    """R7：markdown 相对链接目标必须存在。"""
    for offset, line in enumerate(text.splitlines()):
        for target in LINK_RE.findall(line):
            if re.match(r"^[a-z]+:", target):  # http:// 等外部链接跳过
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                findings.append(Finding("E", path, offset + 1, f"R7 链接目标不存在：{target}"))


def check_skill(path: Path, findings: list[Finding]) -> None:
    """对一个 SKILL.md 执行全部机检项。"""
    text = path.read_text(encoding="utf-8")
    meta, start = split_frontmatter(text)
    body_lines = text.splitlines()[start:]
    body_no_fence, linenos = strip_code_fences("\n".join(body_lines), start)
    check_meta(path, meta, findings)
    check_lines(path, text, findings)
    scan_words(path, body_no_fence, linenos, PHILOSOPHY_WORDS, "E", "R4", findings)
    scan_words(path, body_no_fence, linenos, NARRATIVE_WORDS, "E", "R4", findings)
    scan_words(path, body_no_fence, linenos, VAGUE_WORDS, "W", "R5", findings)
    check_prose(path, body_no_fence, linenos, findings)
    check_duplicates(path, body_no_fence, findings)
    check_links(path, text, findings)


def resolve_skill_files(args: list[str]) -> list[Path]:
    """把命令行参数解析为待检 SKILL.md 列表。"""
    files: list[Path] = []
    for arg in args:
        p = Path(arg)
        target = p if p.name == "SKILL.md" else p / "SKILL.md"
        if target.exists():
            files.append(target)
        else:
            print(f"未找到 {target}，跳过", file=sys.stderr)
    return files


def report(findings: list[Finding]) -> int:
    """打印报告并返回退出码。"""
    errors = [f for f in findings if f.level == "E"]
    for f in findings:
        loc = f"{f.path}:{f.line}" if f.line else str(f.path)
        print(f"{'ERROR' if f.level == 'E' else 'WARN '} {loc}  {f.msg}")
    status = "未通过" if errors else ("通过（含告警）" if findings else "通过")
    print(f"—— {len(errors)} error / {len(findings) - len(errors)} warn → {status}", file=sys.stderr)
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    """入口：依次机检每个技能并汇总退出码。"""
    files = resolve_skill_files(argv[1:])
    if not files:
        print(__doc__, file=sys.stderr)
        return 2
    findings: list[Finding] = []
    for f in files:
        check_skill(f, findings)
    return report(findings)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
