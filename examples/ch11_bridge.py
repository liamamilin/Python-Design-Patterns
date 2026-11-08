"""第 11 章：桥接。图表（抽象）持有一块画布（实现），两边各自扩展。"""
from __future__ import annotations

from typing import Protocol

from examples.ch11_charts_v1 import rainfall


# ---- 实现一侧：画布只提供最基本的绘图操作 ----

class Canvas(Protocol):
    width: int
    height: int

    def text(self, x: int, y: int, s: str) -> None: ...
    def fill(self, x: int, y: int, w: int, h: int) -> None: ...
    def render(self) -> str: ...


class TextCanvas:
    def __init__(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        self.grid = [[" "] * width for _ in range(height)]

    def text(self, x: int, y: int, s: str) -> None:
        for i, ch in enumerate(s):
            self.grid[y][x + i] = ch

    def fill(self, x: int, y: int, w: int, h: int) -> None:
        for row in range(y, y + h):
            for col in range(x, x + w):
                self.grid[row][col] = "█"

    def render(self) -> str:
        return "\n".join("".join(row).rstrip() for row in self.grid)


class SvgCanvas:
    UNIT = 10

    def __init__(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        self.parts: list[str] = []

    def text(self, x: int, y: int, s: str) -> None:
        u = self.UNIT
        self.parts.append(f'<text x="{x * u}" y="{y * u + 8}">{s}</text>')

    def fill(self, x: int, y: int, w: int, h: int) -> None:
        u = self.UNIT
        self.parts.append(f'<rect x="{x * u}" y="{y * u}" width="{w * u}" height="{h * u}"/>')

    def render(self) -> str:
        u = self.UNIT
        head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width * u}" height="{self.height * u}">'
        return "\n".join([head, *self.parts, "</svg>"])


# ---- 抽象一侧：图表只用画布的基本操作来画 ----

class Chart:
    def __init__(self, canvas: Canvas) -> None:
        self.canvas = canvas

    @staticmethod
    def scale(value: int, top: int, room: int) -> int:
        return round(value / top * room) if top else 0

    def draw(self, data: dict[str, int]) -> str:
        raise NotImplementedError


class BarChart(Chart):
    """横向条形图：每行一个类别。"""

    def draw(self, data: dict[str, int]) -> str:
        label_w = max(len(k) for k in data) + 1
        room = self.canvas.width - label_w
        top = max(data.values())
        for row, (label, value) in enumerate(data.items()):
            self.canvas.text(0, row, label)
            length = self.scale(value, top, room)
            if length:
                self.canvas.fill(label_w, row, length, 1)
        return self.canvas.render()


class ColumnChart(Chart):
    """纵向柱状图：每列一个类别，标签在最下面一行。"""

    def draw(self, data: dict[str, int]) -> str:
        room = self.canvas.height - 1
        top = max(data.values())
        for i, (label, value) in enumerate(data.items()):
            x = i * 3
            h = self.scale(value, top, room)
            if h:
                self.canvas.fill(x, room - h, 2, h)
            self.canvas.text(x, room, label[:2])
        return self.canvas.render()


if __name__ == "__main__":
    print(BarChart(TextCanvas(23, 4)).draw(rainfall))
    print(ColumnChart(TextCanvas(12, 6)).draw(rainfall))
    print(BarChart(SvgCanvas(23, 4)).draw(rainfall))
