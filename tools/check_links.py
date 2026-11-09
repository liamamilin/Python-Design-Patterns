"""检查书稿中的相对链接，以及“第 NN 章”的引用。

规则：
1. book/ 下所有 Markdown 文件里的相对链接都必须指向存在的文件（代码块和行内代码不算）。
2. 正文里提到一个已经写好的章节（“第 NN 章”）时，应该写成链接；
   尚未写好的章节保持纯文本，等全书完成后统一补链接。

用法（在仓库根目录）：
    python tools/check_links.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
LINKED_REF = re.compile(r"\[第 \d\d 章\]\([^)]*\)")
PLAIN_REF = re.compile(r"第 (\d\d) 章")


def prose(text: str) -> str:
    return INLINE.sub("", FENCE.sub("", text))


def chapters() -> dict[str, Path]:
    return {p.name[:2]: p for p in ROOT.glob("book/part-*/[0-9][0-9]-*.md")}


def problems() -> list[str]:
    found: list[str] = []
    written = chapters()
    for md in sorted(ROOT.glob("book/**/*.md")):
        body = prose(md.read_text(encoding="utf-8"))
        name = md.relative_to(ROOT)
        for target in LINK.findall(body):
            if target.startswith(("http://", "https://")):
                continue
            if not (md.parent / target).exists():
                found.append(f"{name}：链接目标不存在：{target}")
        if md.name == "README.md":
            continue
        own = md.name[:2]
        lines = body.splitlines()[1:]  # 跳过本章标题
        for line in lines:
            for number in PLAIN_REF.findall(LINKED_REF.sub("", line)):
                if number in written and number != own:
                    found.append(f"{name}：第 {number} 章已经写好，应该写成链接")
    return found


def main() -> int:
    found = problems()
    for line in found:
        print(line)
    print("链接检查通过。" if not found else f"共 {len(found)} 处问题。")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
