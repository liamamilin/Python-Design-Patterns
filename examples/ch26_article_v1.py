"""第 26 章：第一版。每种操作都写成内容块上的方法，基类给出默认值。"""
from __future__ import annotations


def chars(text: str) -> int:
    """字数：不算空白的字符数。"""
    return sum(1 for ch in text if not ch.isspace())


class Block:
    def word_count(self) -> int:
        return 0  # 默认值：子类没写就算 0

    def to_text(self) -> str:
        return ""


class Heading(Block):
    def __init__(self, level: int, text: str) -> None:
        self.level, self.text = level, text

    def word_count(self) -> int:
        return chars(self.text)

    def to_text(self) -> str:
        return self.text


class Paragraph(Block):
    def __init__(self, text: str) -> None:
        self.text = text

    def word_count(self) -> int:
        return chars(self.text)

    def to_text(self) -> str:
        return self.text


class Image(Block):
    def __init__(self, src: str, alt: str = "") -> None:
        self.src, self.alt = src, alt

    def to_text(self) -> str:
        return f"[图片：{self.alt or self.src}]"


class Table(Block):
    """后来加的。写的人只实现了 to_text，忘了 word_count。"""

    def __init__(self, rows: list[list[str]]) -> None:
        self.rows = rows

    def to_text(self) -> str:
        return "\n".join(" | ".join(row) for row in self.rows)


article = [
    Heading(1, "春季露营指南"),
    Paragraph("带上防潮垫和保暖衣物。"),
    Image("tent.jpg"),
    Table([["物品", "数量"], ["帐篷", "1"]]),
]


if __name__ == "__main__":
    print("字数：", sum(b.word_count() for b in article))
