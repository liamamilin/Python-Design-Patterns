"""第 02 章：经过四次需求变化之后的成绩单。

这份代码每一步改动单独看都合理，合在一起却藏着两个真实的错误：
- 化学及格线只改了一处，成绩单和家长通知给出相反的结论；
- 求中位数时就地排序，打乱了姓名和分数的对应关系。
测试 tests/test_ch02_report.py 会把这两个错误复现出来。
"""
from __future__ import annotations

students = ["小林", "小周", "小吴", "小郑"]
math_scores = [72, 48, 91, 65]


def median(values: list[int]) -> float:
    values.sort()  # 就地排序：调用者手里的列表也被改了
    middle = len(values) // 2
    if len(values) % 2 == 1:
        return float(values[middle])
    return (values[middle - 1] + values[middle]) / 2


def class_report(subject: str, names: list[str], scores: list[int]) -> list[str]:
    lines = [f"{subject} 中位数：{median(scores)}"]
    for name, score in zip(names, scores):
        if subject == "化学":
            passed = score >= 50
        elif subject == "物理":
            passed = score >= 55
        else:
            passed = score >= 60
        lines.append(f"{name} {score} {'及格' if passed else '不及格'}")
    return lines


def parent_notice(subject: str, name: str, score: int) -> str:
    # 这段及格判断是从 class_report 复制过来的
    if subject == "物理":
        passed = score >= 55
    else:
        passed = score >= 60
    result = "已及格" if passed else "未及格，请留意"
    return f"{name} 家长：本次{subject} {score} 分，{result}。"


if __name__ == "__main__":
    for line in class_report("数学", students, math_scores):
        print(line)
    print(parent_notice("化学", "小周", 52))
