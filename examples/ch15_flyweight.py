"""第 15 章：享元。车站信息只保存一份，所有刷卡记录共享它。"""
from __future__ import annotations

import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass

from examples.ch15_taps_v1 import parse as parse_plain
from examples.ch15_taps_v1 import raw_lines


@dataclass(frozen=True, slots=True)
class Station:
    """内部状态：同一个车站对所有记录都一样，而且不可修改。"""

    name: str
    line: str
    zone: int


class StationPool:
    """享元工厂：同样的车站只创建一次。"""

    def __init__(self) -> None:
        self._stations: dict[tuple[str, str, int], Station] = {}

    def get(self, name: str, line: str, zone: int) -> Station:
        key = (name, line, zone)
        station = self._stations.get(key)
        if station is None:
            station = self._stations[key] = Station(name, line, zone)
        return station

    def __len__(self) -> int:
        return len(self._stations)


@dataclass(slots=True)
class Tap:
    """外部状态：每条记录各不相同的部分，加上对共享车站的引用。"""

    card: str
    minute: int
    station: Station


def parse(lines: list[str], pool: StationPool) -> list[Tap]:
    taps = []
    for text in lines:
        card, minute, name, line, zone = text.split(",")
        taps.append(Tap(card, int(minute), pool.get(name, line, int(zone))))
    return taps


def measure(build: Callable[[], object]) -> int:
    """返回 build() 构造出的对象在保留状态下占用的内存（字节），由 tracemalloc 测得。"""
    tracemalloc.start()
    try:
        before = tracemalloc.get_traced_memory()[0]
        result = build()
        after = tracemalloc.get_traced_memory()[0]
    finally:
        tracemalloc.stop()
    del result
    return after - before


if __name__ == "__main__":
    lines = raw_lines(20_000)
    pool = StationPool()
    taps = parse(lines, pool)
    print("记录数：", len(taps), "车站对象数：", len(pool))
    plain = measure(lambda: parse_plain(lines))
    shared = measure(lambda: parse(lines, StationPool()))
    print(f"本机测得：每条记录各存一份 {plain:,} 字节；共享车站 {shared:,} 字节")
    print("（数字随 Python 版本和平台而变，只看相对大小）")
