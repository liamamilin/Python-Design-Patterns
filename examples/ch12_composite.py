"""第 12 章：组合。单个项目和项目组实现同一个接口，调用方不用区分。"""
from __future__ import annotations

from typing import Protocol


class BudgetNode(Protocol):
    name: str

    def cost(self) -> int: ...
    def lines(self, depth: int = 0) -> list[str]: ...


class Item:
    """叶子：一个具体的项目。"""

    def __init__(self, name: str, unit_price: int, qty: int = 1) -> None:
        self.name, self.unit_price, self.qty = name, unit_price, qty

    def cost(self) -> int:
        return self.unit_price * self.qty

    def lines(self, depth: int = 0) -> list[str]:
        return [f"{'  ' * depth}{self.name} {self.cost():,}"]


class Group:
    """组合：包含若干项目或子组，可以打折。"""

    def __init__(self, name: str, percent: int = 100) -> None:
        self.name, self.percent = name, percent
        self.children: list[BudgetNode] = []

    def add(self, *nodes: BudgetNode) -> Group:
        for node in nodes:
            if node is self or (isinstance(node, Group) and node.contains(self)):
                raise ValueError(f"不能把“{node.name}”放进它自己里面")
            self.children.append(node)
        return self

    def contains(self, target: BudgetNode) -> bool:
        return any(
            child is target or (isinstance(child, Group) and child.contains(target))
            for child in self.children
        )

    def cost(self) -> int:
        return round(sum(child.cost() for child in self.children) * self.percent / 100)

    def lines(self, depth: int = 0) -> list[str]:
        note = f"（打包 {self.percent / 10:g} 折）" if self.percent != 100 else ""
        head = f"{'  ' * depth}{self.name} {self.cost():,}{note}"
        return [head] + [line for child in self.children for line in child.lines(depth + 1)]


def new_home() -> Group:
    return Group("新房装修").add(
        Item("设计费", 5000),
        Group("客厅").add(Item("地板", 200, qty=40), Item("沙发", 6500)),
        Group("厨房").add(
            Item("橱柜", 12000),
            Group("电器", percent=90).add(Item("油烟机", 3000), Item("灶具", 2000)),
        ),
    )


def expensive(node: BudgetNode, limit: int) -> list[str]:
    """找出单项超过 limit 的叶子项目。"""
    if isinstance(node, Group):
        return [name for child in node.children for name in expensive(child, limit)]
    return [node.name] if node.cost() > limit else []


if __name__ == "__main__":
    home = new_home()
    print("\n".join(home.lines()))
    print(expensive(home, 6000))
