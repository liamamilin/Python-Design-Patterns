"""第 02 章：用普通的重构修好成绩单，没有使用任何设计模式。

- 及格规则只写一次，两个功能共用；
- 姓名和分数放在同一个字典里，不再靠两个列表的位置对应；
- 求中位数不再修改调用者的数据。
"""
from __future__ import annotations

PASS_MARKS = {"物理": 55, "化学": 50}
DEFAULT_PASS_MARK = 60


def passed(subject: str, score: int) -> bool:
    return score >= PASS_MARKS.get(subject, DEFAULT_PASS_MARK)


def median(values: list[int]) -> float:
    ordered = sorted(values)  # 返回新列表，不碰调用者的数据
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2


def class_report(subject: str, scores: dict[str, int]) -> list[str]:
    lines = [f"{subject} 中位数：{median(list(scores.values()))}"]
    for name, score in scores.items():
        lines.append(f"{name} {score} {'及格' if passed(subject, score) else '不及格'}")
    return lines


def parent_notice(subject: str, name: str, score: int) -> str:
    result = "已及格" if passed(subject, score) else "未及格，请留意"
    return f"{name} 家长：本次{subject} {score} 分，{result}。"


math_scores = {"小林": 72, "小周": 48, "小吴": 91, "小郑": 65}


if __name__ == "__main__":
    for line in class_report("数学", math_scores):
        print(line)
    print(parent_notice("化学", "小周", 52))
