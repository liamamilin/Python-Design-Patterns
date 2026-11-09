"""第 19 章：命令。每个操作是一个对象：能执行，（多数）能撤销，有唯一编号。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class Command(Protocol):
    id: str
    undoable: bool

    def execute(self, inv: dict[str, int]) -> None: ...
    def undo(self, inv: dict[str, int]) -> None: ...


@dataclass
class StockIn:
    id: str
    sku: str
    qty: int
    undoable: bool = True

    def execute(self, inv: dict[str, int]) -> None:
        inv[self.sku] = inv.get(self.sku, 0) + self.qty

    def undo(self, inv: dict[str, int]) -> None:
        inv[self.sku] -= self.qty


@dataclass
class StockOut:
    id: str
    sku: str
    qty: int
    undoable: bool = True

    def execute(self, inv: dict[str, int]) -> None:
        if inv.get(self.sku, 0) < self.qty:
            raise ValueError(f"{self.sku} 库存不足")
        inv[self.sku] -= self.qty

    def undo(self, inv: dict[str, int]) -> None:
        inv[self.sku] += self.qty


@dataclass
class SetCount:
    """盘点：把库存改成实际清点出的数量。撤销需要知道改之前是多少。"""

    id: str
    sku: str
    counted: int
    undoable: bool = True
    _previous: int | None = field(default=None, repr=False)

    def execute(self, inv: dict[str, int]) -> None:
        self._previous = inv.get(self.sku, 0)
        inv[self.sku] = self.counted

    def undo(self, inv: dict[str, int]) -> None:
        assert self._previous is not None, "还没有执行过，不能撤销"
        inv[self.sku] = self._previous


@dataclass
class NotifySupplier:
    """给供应商发补货通知。消息发出去就收不回来了。"""

    id: str
    sku: str
    outbox: list[str]
    undoable: bool = False

    def execute(self, inv: dict[str, int]) -> None:
        self.outbox.append(f"请补货：{self.sku}，当前库存 {inv.get(self.sku, 0)}")

    def undo(self, inv: dict[str, int]) -> None:
        raise NotImplementedError("已发出的通知无法撤回")


class Ledger:
    """调用者：执行命令，记住执行过哪些，负责撤销。"""

    def __init__(self, inventory: dict[str, int]) -> None:
        self.inventory = inventory
        self._done_ids: set[str] = set()
        self._undo_stack: list[Command] = []

    def run(self, cmd: Command) -> bool:
        """执行一条命令。同一编号的命令只生效一次，重复提交返回 False。"""
        if cmd.id in self._done_ids:
            return False
        cmd.execute(self.inventory)
        self._done_ids.add(cmd.id)
        if cmd.undoable:
            self._undo_stack.append(cmd)
        else:
            self._undo_stack.clear()  # 不可撤销的操作之前的步骤，也不能再撤销了
        return True

    def undo(self) -> Command | None:
        if not self._undo_stack:
            return None
        cmd = self._undo_stack.pop()
        cmd.undo(self.inventory)
        return cmd

    def can_undo(self) -> bool:
        return bool(self._undo_stack)


if __name__ == "__main__":
    ledger = Ledger({"螺丝M4": 100})
    out = StockOut("op-17", "螺丝M4", 30)
    print(ledger.run(out), ledger.run(out), ledger.inventory)
    ledger.run(SetCount("op-18", "螺丝M4", 65))
    ledger.undo()
    print(ledger.inventory)
