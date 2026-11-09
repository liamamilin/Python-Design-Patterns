"""第 26 章：Python 角度。用 match 按类型分派；assert_never 让类型检查器发现漏掉的种类。"""
from __future__ import annotations

from functools import singledispatch
from typing import assert_never

from examples.ch26_article_v1 import chars
from examples.ch26_visitor import Block, Heading, Image, Paragraph, Table, article


def to_text(b: Block) -> str:
    match b:
        case Heading(level, text):
            return "#" * level + " " + text
        case Paragraph(text):
            return text
        case Image(src, alt):
            return f"[图片：{alt or src}]"
        case Table(rows):
            return "\n".join(" | ".join(row) for row in rows)
        case _:
            assert_never(b)


@singledispatch
def word_count(b: object) -> int:
    raise TypeError(f"不知道怎样统计 {type(b).__name__} 的字数")


@word_count.register
def _(b: Heading) -> int:
    return chars(b.text)


@word_count.register
def _(b: Paragraph) -> int:
    return chars(b.text)


@word_count.register
def _(b: Image) -> int:
    return 0


@word_count.register
def _(b: Table) -> int:
    return sum(chars(cell) for row in b.rows for cell in row)


if __name__ == "__main__":
    print("\n".join(to_text(b) for b in article))
    print("字数：", sum(word_count(b) for b in article))
