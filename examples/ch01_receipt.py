"""第 01 章：从数据与处理理解程序。

一家咖啡店的小票：先看数据，再看处理，最后看状态、副作用和时间。
运行：python -m examples.ch01_receipt
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from typing import TextIO

# 数据：一张订单由若干行组成，每行记录商品名、单价（单位：分）和数量
order = [
    {"name": "拿铁", "price": 2800, "qty": 2},
    {"name": "可颂", "price": 1500, "qty": 1},
]


def order_total(lines: list[dict]) -> int:
    """处理：输入订单，输出总价（分）。不修改订单，也不依赖外部状态。"""
    return sum(line["price"] * line["qty"] for line in lines)


def format_yuan(cents: int) -> str:
    return f"¥{cents / 100:.2f}"


class MemberCard:
    """会员卡记住累计积分：同样的调用，结果取决于之前发生过什么。"""

    def __init__(self) -> None:
        self.points = 0

    def add_purchase(self, cents: int) -> int:
        earned = cents // 1000  # 每满 10 元积 1 分
        self.points += earned
        return self.points


def print_receipt(lines: list[dict], now: datetime, out: TextIO) -> None:
    """副作用：把小票写到 out。时间和输出位置都由调用方传入。"""
    out.write(f"时间：{now:%Y-%m-%d %H:%M}\n")
    for line in lines:
        subtotal = line["price"] * line["qty"]
        out.write(f"{line['name']} x{line['qty']}  {format_yuan(subtotal)}\n")
    out.write(f"合计：{format_yuan(order_total(lines))}\n")


@dataclass(frozen=True)
class OrderLine:
    name: str
    price: int  # 单位：分
    qty: int

    @property
    def subtotal(self) -> int:
        return self.price * self.qty


def total_of(lines: list[OrderLine]) -> int:
    return sum(line.subtotal for line in lines)


if __name__ == "__main__":
    print(format_yuan(order_total(order)))  # ¥71.00
    card = MemberCard()
    print(card.add_purchase(order_total(order)))  # 7
    print(card.add_purchase(order_total(order)))  # 14
    print_receipt(order, datetime.now(), sys.stdout)
