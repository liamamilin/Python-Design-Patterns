"""第 02 章：成绩单的第一版。只有数学一科，及格线 60 分。"""
from __future__ import annotations


def class_report(names: list[str], scores: list[int]) -> list[str]:
    lines = []
    for name, score in zip(names, scores):
        result = "及格" if score >= 60 else "不及格"
        lines.append(f"{name} {score} {result}")
    return lines


if __name__ == "__main__":
    for line in class_report(["小林", "小周"], [72, 48]):
        print(line)
