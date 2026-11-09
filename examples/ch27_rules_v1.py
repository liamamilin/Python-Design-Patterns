"""第 27 章：第一版。报名资格规则由老师在后台填写，程序直接用 eval 计算。不要这样做。"""
from __future__ import annotations

students = [
    {"姓名": "周晴", "年级": 2, "学院": "物理", "社团": "无"},
    {"姓名": "林木", "年级": 1, "学院": "化学", "社团": "天文社"},
    {"姓名": "高远", "年级": 3, "学院": "化学", "社团": "天文社"},
]


def eligible(rule: str, student: dict) -> bool:
    return bool(eval(rule, {}, student))  # 危险：rule 里的任何 Python 代码都会被执行


if __name__ == "__main__":
    rule = '年级 >= 2 and (学院 == "物理" or 社团 == "天文社")'
    print([s["姓名"] for s in students if eligible(rule, s)])
    print(eligible('__import__("os").getpid() > 0', students[0]))  # 规则可以调用任意函数
