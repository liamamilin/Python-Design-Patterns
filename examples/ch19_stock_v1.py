"""第 19 章：第一版。库存操作就是直接修改字典的函数。"""
from __future__ import annotations


def stock_in(inventory: dict[str, int], sku: str, qty: int) -> None:
    inventory[sku] = inventory.get(sku, 0) + qty


def stock_out(inventory: dict[str, int], sku: str, qty: int) -> None:
    if inventory.get(sku, 0) < qty:
        raise ValueError(f"{sku} 库存不足")
    inventory[sku] -= qty


if __name__ == "__main__":
    inv = {"螺丝M4": 100}
    stock_out(inv, "螺丝M4", 30)
    stock_out(inv, "螺丝M4", 30)  # 扫码枪网络超时后重发了同一条出库
    print(inv)
