"""第 15 章：第一版。每条刷卡记录都保存一份完整的车站信息。"""
from __future__ import annotations

from dataclasses import dataclass

STATIONS = ["西直门,2号线,1", "国贸,1号线,1", "望京,14号线,2", "天通苑,5号线,3", "亦庄桥,亦庄线,3"]


def raw_lines(n: int) -> list[str]:
    """模拟闸机导出的文本：卡号,分钟,车站,线路,票价区。"""
    return [f"C{i % 500:04d},{i % 1440},{STATIONS[i % len(STATIONS)]}" for i in range(n)]


@dataclass
class Tap:
    card: str
    minute: int
    station: str
    line: str
    zone: int


def parse(lines: list[str]) -> list[Tap]:
    taps = []
    for text in lines:
        card, minute, station, line, zone = text.split(",")
        taps.append(Tap(card, int(minute), station, line, int(zone)))
    return taps


if __name__ == "__main__":
    taps = parse(raw_lines(10))
    print(taps[0])
    print("两条记录的车站名是同一个字符串对象吗？", taps[0].station is taps[5].station)
