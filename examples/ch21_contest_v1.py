"""第 21 章：第一版。跳水和歌手比赛各写一个计分函数，流程大同小异。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    name: str
    judges: list[float]
    difficulty: float = 1.0  # 跳水的难度系数
    overtime_s: int = 0  # 歌手超时的秒数


divers = [
    Entry("林", [7.5, 8.0, 8.0, 7.0, 8.5], difficulty=3.0),
    Entry("陈", [8.0, 8.0, 7.5, 8.0, 7.5], difficulty=3.0),
    Entry("吴", [6.5, 7.0, 7.0, 7.5, 6.0], difficulty=3.2),
]

singers = [
    Entry("小雨", [9.0, 8.5, 9.0]),
    Entry("阿杰", [8.5, 9.0, 9.0], overtime_s=15),
    Entry("木子", [9.0, 8.5, 9.0]),
]


def diving_results(entries: list[Entry]) -> list[str]:
    for e in entries:
        if len(e.judges) != 5:
            raise ValueError(f"{e.name}：跳水需要 5 位裁判的分数")
    scored = [(round(sum(sorted(e.judges)[1:-1]) * e.difficulty, 2), e.name) for e in entries]
    scored.sort(key=lambda pair: -pair[0])
    lines, rank = [], 0
    for i, (score, name) in enumerate(scored, 1):
        if i == 1 or score != scored[i - 2][0]:
            rank = i  # 同分并列（后来修的）
        lines.append(f"{rank}. {name} {score:.2f}")
    return lines


def singing_results(entries: list[Entry]) -> list[str]:
    for e in entries:
        if len(e.judges) != 3:
            raise ValueError(f"{e.name}：歌手比赛需要 3 位评委的分数")
    scored = []
    for e in entries:
        score = round(sum(e.judges) / len(e.judges), 2)
        if e.overtime_s > 0:
            score -= 0.5
        scored.append((round(score, 2), e.name))
    scored.sort(key=lambda pair: -pair[0])
    return [f"{i}. {name} {score:.2f}" for i, (score, name) in enumerate(scored, 1)]  # 没有并列


if __name__ == "__main__":
    print(diving_results(divers))
    print(singing_results(singers))
