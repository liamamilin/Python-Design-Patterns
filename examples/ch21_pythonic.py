"""第 21 章：Python 角度。流程是一个函数，可变的步骤作为参数传入。"""
from __future__ import annotations

from collections.abc import Callable

from examples.ch21_contest_v1 import Entry, singers
from examples.ch21_template_method import rank_lines


def results(
    entries: list[Entry],
    score: Callable[[Entry], float],
    judges: int = 3,
    penalty: Callable[[Entry], float] = lambda e: 0.0,
) -> list[str]:
    for e in entries:
        if len(e.judges) != judges:
            raise ValueError(f"{e.name}：需要 {judges} 位裁判的分数")
    scored = [(round(score(e) - penalty(e), 2), e.name) for e in entries]
    scored.sort(key=lambda pair: -pair[0])
    return rank_lines(scored)


def average(e: Entry) -> float:
    return sum(e.judges) / len(e.judges)


if __name__ == "__main__":
    print(results(singers, average, penalty=lambda e: 0.5 if e.overtime_s else 0.0))
