"""第 08 章：Python 角度。数据整体不可变时，浅拷贝就足够安全，代价是修改要写成“造一个新的”。"""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Exercise:
    name: str
    sets: int
    reps: int


@dataclass(frozen=True)
class Plan:
    title: str
    days: tuple[tuple[str, tuple[Exercise, ...]], ...]


BEGINNER = Plan(
    "新手计划",
    (
        ("周一", (Exercise("深蹲", 3, 10), Exercise("俯卧撑", 3, 8))),
        ("周四", (Exercise("硬拉", 3, 8),)),
    ),
)


def change_sets(plan: Plan, day: str, name: str, sets: int) -> Plan:
    new_days = tuple(
        (d, tuple(replace(e, sets=sets) if d == day and e.name == name else e for e in exercises))
        for d, exercises in plan.days
    )
    return replace(plan, days=new_days)


if __name__ == "__main__":
    chen = change_sets(replace(BEGINNER, title="小陈的计划"), "周一", "深蹲", 4)
    print(chen.days[0][1][0], BEGINNER.days[0][1][0])
