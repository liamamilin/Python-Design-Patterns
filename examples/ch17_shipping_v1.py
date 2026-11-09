"""第 17 章：第一版。结算页和批量报价各自维护一套运费规则。"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    weight_g: int
    distance_km: float
    subtotal: int  # 商品金额，单位：分


def checkout_fee(order: Order, method: str) -> int:
    """结算页：顾客选定一种配送方式后显示运费。"""
    if method == "express":
        if order.subtotal >= 9900:
            return 0
        kg = math.ceil(order.weight_g / 1000)
        return 800 + (kg - 1) * 300  # 续重费上个月从 2 元调到了 3 元
    if method == "same_city":
        return 1500 + math.ceil(order.distance_km) * 200
    if method == "pickup":
        return 0
    raise ValueError(f"未知配送方式: {method}")


def quote_all(order: Order) -> dict[str, int]:
    """批量报价：给客服看一个订单所有配送方式的运费。"""
    kg = math.ceil(order.weight_g / 1000)
    express = 0 if order.subtotal >= 9900 else 800 + (kg - 1) * 200  # 这里还是旧费率
    return {
        "express": express,
        "same_city": 1500 + math.ceil(order.distance_km) * 200,
        "pickup": 0,
    }


if __name__ == "__main__":
    order = Order(weight_g=2300, distance_km=8.5, subtotal=6800)
    print("结算页：", checkout_fee(order, "express"))
    print("批量报价：", quote_all(order)["express"])
