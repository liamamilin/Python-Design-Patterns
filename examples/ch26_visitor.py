"""第 26 章：访问者。内容块的种类固定；每种新操作是一个访问者，必须处理所有种类。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from examples.ch26_article_v1 import chars


class Visitor(ABC):
    @abstractmethod
    def visit_heading(self, b: Heading) -> None: ...

    @abstractmethod
    def visit_paragraph(self, b: Paragraph) -> None: ...

    @abstractmethod
    def visit_image(self, b: Image) -> None: ...

    @abstractmethod
    def visit_table(self, b: Table) -> None: ...


@dataclass
class Heading:
    level: int
    text: str

    def accept(self, v: Visitor) -> None:
        v.visit_heading(self)


@dataclass
class Paragraph:
    text: str

    def accept(self, v: Visitor) -> None:
        v.visit_paragraph(self)


@dataclass
class Image:
    src: str
    alt: str = ""

    def accept(self, v: Visitor) -> None:
        v.visit_image(self)


@dataclass
class Table:
    rows: list[list[str]]

    def accept(self, v: Visitor) -> None:
        v.visit_table(self)


Block = Heading | Paragraph | Image | Table


class WordCounter(Visitor):
    def __init__(self) -> None:
        self.total = 0

    def visit_heading(self, b: Heading) -> None:
        self.total += chars(b.text)

    def visit_paragraph(self, b: Paragraph) -> None:
        self.total += chars(b.text)

    def visit_image(self, b: Image) -> None:
        pass  # 图片的替代文字不算正文字数

    def visit_table(self, b: Table) -> None:
        self.total += sum(chars(cell) for row in b.rows for cell in row)


class AltChecker(Visitor):
    """无障碍检查：没有替代文字的图片，读屏软件无法描述。"""

    def __init__(self) -> None:
        self.problems: list[str] = []

    def visit_heading(self, b: Heading) -> None:
        pass

    def visit_paragraph(self, b: Paragraph) -> None:
        pass

    def visit_image(self, b: Image) -> None:
        if not b.alt.strip():
            self.problems.append(f"图片 {b.src} 缺少替代文字")

    def visit_table(self, b: Table) -> None:
        if len(b.rows) < 2:
            self.problems.append("表格至少要有表头和一行数据")


def run(blocks: list[Block], visitor: Visitor) -> Visitor:
    for b in blocks:
        b.accept(visitor)
    return visitor


article: list[Block] = [
    Heading(1, "春季露营指南"),
    Paragraph("带上防潮垫和保暖衣物。"),
    Image("tent.jpg"),
    Table([["物品", "数量"], ["帐篷", "1"]]),
]


if __name__ == "__main__":
    print("字数：", run(article, WordCounter()).total)
    print(run(article, AltChecker()).problems)
