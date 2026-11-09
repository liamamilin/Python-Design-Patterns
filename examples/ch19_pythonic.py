"""第 19 章：Python 角度。命令是纯数据；执行时算出“反向命令”，撤销就是执行它。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Add:
    sku: str
    qty: int


@dataclass(frozen=True)
class Remove:
    sku: str
    qty: int


@dataclass(frozen=True)
class Recount:
    sku: str
    value: int


Cmd = Add | Remove | Recount


def apply(inv: dict[str, int], cmd: Cmd) -> Cmd:
    """执行命令，返回能抵消它的反向命令。"""
    match cmd:
        case Add(sku, qty):
            inv[sku] = inv.get(sku, 0) + qty
            return Remove(sku, qty)
        case Remove(sku, qty):
            if inv.get(sku, 0) < qty:
                raise ValueError(f"{sku} 库存不足")
            inv[sku] -= qty
            return Add(sku, qty)
        case Recount(sku, value):
            previous = inv.get(sku, 0)
            inv[sku] = value
            return Recount(sku, previous)
    raise TypeError(f"未知命令: {cmd!r}")


def replay(commands: list[Cmd]) -> dict[str, int]:
    """命令是数据，可以存下来，以后从头重放一遍得到同样的结果。"""
    inv: dict[str, int] = {}
    for cmd in commands:
        apply(inv, cmd)
    return inv


if __name__ == "__main__":
    inv = {"螺丝M4": 100}
    undo_stack = [apply(inv, Remove("螺丝M4", 30)), apply(inv, Recount("螺丝M4", 65))]
    apply(inv, undo_stack.pop())
    print(inv, replay([Add("螺丝M4", 100), Remove("螺丝M4", 30)]))
