"""第 12 章：Python 角度。数据本来就是嵌套的字典时，一个递归函数就能统一处理任意深度。"""
from __future__ import annotations

from examples.ch12_budget_v1 import budget_later

Budget = int | dict[str, "Budget"]


def total(node: Budget) -> int:
    if isinstance(node, int):
        return node
    return sum(total(child) for child in node.values())


def lines(name: str, node: Budget, depth: int = 0) -> list[str]:
    result = [f"{'  ' * depth}{name} {total(node):,}"]
    if isinstance(node, dict):
        for child_name, child in node.items():
            result += lines(child_name, child, depth + 1)
    return result


if __name__ == "__main__":
    print(total(budget_later))
    print("\n".join(lines("新房装修", budget_later)))
