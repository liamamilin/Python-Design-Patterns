"""第 15 章：Python 角度。functools.cache 当享元工厂；更常见的是根本不保留这么多对象。"""
from __future__ import annotations

import sys
from collections import Counter
from functools import cache

from examples.ch15_flyweight import Station
from examples.ch15_taps_v1 import Tap, raw_lines


@cache
def station(name: str, line: str, zone: int) -> Station:
    return Station(name, line, zone)


def parse_interned(lines: list[str]) -> list[Tap]:
    """不改记录的类，只让相同的字符串共享同一个对象。"""
    taps = []
    for text in lines:
        card, minute, name, line, zone = text.split(",")
        taps.append(Tap(card, int(minute), sys.intern(name), sys.intern(line), int(zone)))
    return taps


def taps_per_station(lines: list[str]) -> Counter[str]:
    """如果只需要统计，边读边数，不必为每一行保留一个对象。"""
    counts: Counter[str] = Counter()
    for text in lines:
        counts[text.split(",")[2]] += 1
    return counts


if __name__ == "__main__":
    print(station("国贸", "1号线", 1) is station("国贸", "1号线", 1))
    print(taps_per_station(raw_lines(20_000)).most_common(2))
