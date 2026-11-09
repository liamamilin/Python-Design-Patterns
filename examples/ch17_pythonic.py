"""第 17 章：Python 角度。策略只有一个计算时，直接传函数；需要配置时用 partial。"""
from __future__ import annotations

import math
from collections.abc import Callable
from functools import partial

from examples.ch17_shipping_v1 import Order

FeeRule = Callable[[Order], int]


def express_fee(order: Order, first: int = 800, per_extra_kg: int = 300, free_over: int = 9900) -> int:
    if order.subtotal >= free_over:
        return 0
    return first + (math.ceil(order.weight_g / 1000) - 1) * per_extra_kg


def same_city_fee(order: Order) -> int:
    return 1500 + math.ceil(order.distance_km) * 200


def pickup_fee(order: Order) -> int:
    return 0


FEES: dict[str, FeeRule] = {
    "express": express_fee,
    "same_city": same_city_fee,
    "pickup": pickup_fee,
}

# 会员日：普通快递满 59 元包邮。不用新写一个函数，固定一个参数即可。
member_day_express = partial(express_fee, free_over=5900)


def checkout_fee(order: Order, rule: FeeRule) -> int:
    return rule(order)


if __name__ == "__main__":
    order = Order(weight_g=2300, distance_km=8.5, subtotal=6800)
    print(checkout_fee(order, FEES["express"]), checkout_fee(order, member_day_express))
