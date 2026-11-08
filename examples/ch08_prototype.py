"""第 08 章：原型。计划自己知道怎样复制自己；动作库条目在复制时保持共享。"""
from __future__ import annotations

import copy
from dataclasses import dataclass


@dataclass(eq=False)
class Movement:
    """动作库里的一个动作。教练改了讲解视频，所有计划都应该看到新视频。"""

    name: str
    video: str

    def __deepcopy__(self, memo: dict) -> Movement:
        return self  # 共享，不复制


def make_library() -> dict[str, Movement]:
    return {
        "深蹲": Movement("深蹲", "videos/squat.mp4"),
        "俯卧撑": Movement("俯卧撑", "videos/push-up.mp4"),
        "硬拉": Movement("硬拉", "videos/deadlift.mp4"),
    }


@dataclass
class Exercise:
    movement: Movement
    sets: int
    reps: int


@dataclass
class Plan:
    title: str
    days: dict[str, list[Exercise]]

    def clone(self, title: str) -> Plan:
        twin = copy.deepcopy(self)
        twin.title = title
        return twin


def beginner_template(lib: dict[str, Movement]) -> Plan:
    return Plan(
        "新手计划",
        {
            "周一": [Exercise(lib["深蹲"], 3, 10), Exercise(lib["俯卧撑"], 3, 8)],
            "周四": [Exercise(lib["硬拉"], 3, 8)],
        },
    )


class TemplateShelf:
    """原型注册表：按名字保存模板，需要时复制一份。"""

    def __init__(self) -> None:
        self._templates: dict[str, Plan] = {}

    def save(self, name: str, plan: Plan) -> None:
        self._templates[name] = plan.clone(plan.title)  # 存一份副本，之后再改草稿不影响已存的模板

    def new_plan(self, name: str, title: str) -> Plan:
        return self._templates[name].clone(title)

    def names(self) -> list[str]:
        return sorted(self._templates)


if __name__ == "__main__":
    lib = make_library()
    template = beginner_template(lib)
    chen = template.clone("小陈的计划")
    chen.days["周一"][0].sets = 4
    print("小陈：", chen.days["周一"][0].sets, "组；模板：", template.days["周一"][0].sets, "组")
    lib["深蹲"].video = "videos/squat-v2.mp4"
    print("小陈看到的视频：", chen.days["周一"][0].movement.video)
