"""第 11 章：Python 角度。图表没有自己的状态时，一个接收画布参数的函数就是“桥”。"""
from __future__ import annotations

from examples.ch11_bridge import Canvas, Chart, SvgCanvas, TextCanvas
from examples.ch11_charts_v1 import rainfall


def draw_bars(data: dict[str, int], canvas: Canvas) -> str:
    label_w = max(len(k) for k in data) + 1
    room = canvas.width - label_w
    top = max(data.values())
    for row, (label, value) in enumerate(data.items()):
        canvas.text(0, row, label)
        length = Chart.scale(value, top, room)
        if length:
            canvas.fill(label_w, row, length, 1)
    return canvas.render()


if __name__ == "__main__":
    print(draw_bars(rainfall, TextCanvas(23, 4)))
    print(draw_bars(rainfall, SvgCanvas(23, 4)).count("<rect"))
