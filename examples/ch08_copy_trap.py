"""第 08 章：从模板复制训练计划。浅拷贝只复制了最外面一层。"""
from __future__ import annotations

import copy
from dataclasses import dataclass, replace


@dataclass
class Exercise:
    name: str
    sets: int
    reps: int


@dataclass
class Plan:
    title: str
    days: dict[str, list[Exercise]]


def beginner_template() -> Plan:
    return Plan(
        "新手计划",
        {
            "周一": [Exercise("深蹲", 3, 10), Exercise("俯卧撑", 3, 8)],
            "周四": [Exercise("硬拉", 3, 8)],
        },
    )


def plan_for(template: Plan, student: str) -> Plan:
    return replace(template, title=f"{student}的计划")


def show_the_trap() -> tuple[Plan, Plan, Plan]:
    template = beginner_template()
    chen = plan_for(template, "小陈")
    wang = plan_for(template, "小王")
    chen.days["周一"][0].sets = 4  # 只想给小陈的深蹲加到 4 组
    return template, chen, wang


def plan_for_shallow_copy(template: Plan, student: str) -> Plan:
    plan = copy.copy(template)
    plan.title = f"{student}的计划"
    return plan


if __name__ == "__main__":
    template, chen, wang = show_the_trap()
    print("小王：", wang.days["周一"][0])
    print("模板：", template.days["周一"][0])
    print("同一个字典吗？", chen.days is template.days)
