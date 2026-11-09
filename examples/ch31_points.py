"""第 31 章：会员积分。同一套规则的两种写法：一个函数，或者一组可以增减、排序的规则。"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Order:
    amount: int  # 分
    day: date
    tier: str  # "普通" 或 "金卡"
    birthday_month: int


def points_simple(o: Order) -> int:
    points = o.amount // 100  # 每消费 1 元得 1 分
    if o.day.weekday() == 2:
        points *= 2  # 周三双倍
    if o.tier == "金卡":
        points = points * 3 // 2  # 金卡 1.5 倍
    if o.day.month == o.birthday_month:
        points += 100  # 生日月额外送 100 分，不参与倍数
    return points


Rule = Callable[[int, Order], int]


def wednesday_double(points: int, o: Order) -> int:
    return points * 2 if o.day.weekday() == 2 else points


def gold_card(points: int, o: Order) -> int:
    return points * 3 // 2 if o.tier == "金卡" else points


def birthday_bonus(points: int, o: Order) -> int:
    return points + 100 if o.day.month == o.birthday_month else points


RULES: list[Rule] = [wednesday_double, gold_card, birthday_bonus]


def points_rules(o: Order, rules: list[Rule] = RULES) -> int:
    points = o.amount // 100
    for rule in rules:
        points = rule(points, o)
    return points


if __name__ == "__main__":
    order = Order(amount=12800, day=date(2026, 3, 11), tier="金卡", birthday_month=3)
    print(points_simple(order), points_rules(order))
    print(points_rules(order, [birthday_bonus, gold_card, wednesday_double]))
