"""第 21 章：模板方法。父类固定比赛结算的流程，子类只填写各自不同的步骤。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from examples.ch21_contest_v1 import Entry, divers, singers


class Contest(ABC):
    judges_required = 3

    def results(self, entries: list[Entry]) -> list[str]:
        """模板方法：流程固定，子类不应重写它。"""
        for e in entries:
            self.validate(e)
        scored = [(round(self.score(e) - self.penalty(e), 2), e.name) for e in entries]
        scored.sort(key=lambda pair: -pair[0])
        return self.format(scored)

    def validate(self, e: Entry) -> None:
        if len(e.judges) != self.judges_required:
            raise ValueError(f"{e.name}：需要 {self.judges_required} 位裁判的分数")

    @abstractmethod
    def score(self, e: Entry) -> float:
        """必须由子类提供：这项比赛怎么算分。"""

    def penalty(self, e: Entry) -> float:
        """钩子：默认不扣分，子类可以覆盖。"""
        return 0.0

    def format(self, scored: list[tuple[float, str]]) -> list[str]:
        """钩子：默认按分数排名，同分并列。"""
        return rank_lines(scored)


def rank_lines(scored: list[tuple[float, str]]) -> list[str]:
    lines, rank = [], 0
    for i, (score, name) in enumerate(scored, 1):
        if i == 1 or score != scored[i - 2][0]:
            rank = i  # 同分并列，下一名跳过相应的名次
        lines.append(f"{rank}. {name} {score:.2f}")
    return lines


class Diving(Contest):
    judges_required = 5

    def score(self, e: Entry) -> float:
        return sum(sorted(e.judges)[1:-1]) * e.difficulty  # 去掉最高和最低分，乘难度系数


class Singing(Contest):
    def score(self, e: Entry) -> float:
        return sum(e.judges) / len(e.judges)

    def penalty(self, e: Entry) -> float:
        return 0.5 if e.overtime_s > 0 else 0.0


if __name__ == "__main__":
    print(Diving().results(divers))
    print(Singing().results(singers))
