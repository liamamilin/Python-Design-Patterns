"""第 11 章：不用桥接。图表种类和输出方式绑在同一个类上，每种组合一个类。"""
from __future__ import annotations

rainfall = {"1月": 12, "2月": 30, "3月": 0, "4月": 45}


class TextBarChart:
    def __init__(self, width: int) -> None:
        self.width = width

    def draw(self, data: dict[str, int]) -> str:
        label_w = max(len(k) for k in data) + 1
        room = self.width - label_w
        top = max(data.values()) or 1  # 全为 0 时避免除以 0（后来修的）
        lines = []
        for label, value in data.items():
            bar = "█" * round(value / top * room)
            lines.append(f"{label:<{label_w}}{bar}".rstrip())
        return "\n".join(lines)


class SvgBarChart:
    def __init__(self, width: int) -> None:
        self.width = width

    def draw(self, data: dict[str, int]) -> str:
        label_w = max(len(k) for k in data) + 1
        room = self.width - label_w
        top = max(data.values())  # 这里忘了同样的修复
        parts = []
        for row, (label, value) in enumerate(data.items()):
            length = round(value / top * room)
            parts.append(f'<text x="0" y="{row * 10 + 8}">{label}</text>')
            parts.append(f'<rect x="{label_w * 10}" y="{row * 10}" width="{length * 10}" height="10"/>')
        return "\n".join(parts)


# 还有 TextColumnChart、SvgColumnChart……每加一种图表或一种输出方式，都要补齐所有组合。


if __name__ == "__main__":
    print(TextBarChart(23).draw(rainfall))
    try:
        SvgBarChart(23).draw({"1月": 0, "2月": 0})
    except ZeroDivisionError as e:
        print("SVG 版本出错：", e)
