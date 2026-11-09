"""第 17 章：策略。每种配送方式是一个可替换的对象，所有页面都用同一套。"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import ClassVar, Protocol

from examples.ch17_shipping_v1 import Order


class ShippingMethod(Protocol):
    name: str

    def available(self, order: Order) -> bool: ...
    def fee(self, order: Order) -> int: ...
    def eta(self, order: Order) -> str: ...


@dataclass(frozen=True)
class Express:
    name: ClassVar[str] = "普通快递"
    first: int = 800
    per_extra_kg: int = 300
    free_over: int = 9900

    def available(self, order: Order) -> bool:
        return True

    def fee(self, order: Order) -> int:
        if order.subtotal >= self.free_over:
            return 0
        kg = math.ceil(order.weight_g / 1000)
        return self.first + (kg - 1) * self.per_extra_kg

    def eta(self, order: Order) -> str:
        return "2–3 天"


@dataclass(frozen=True)
class SameCity:
    name: ClassVar[str] = "同城急送"
    base: int = 1500
    per_km: int = 200
    max_km: float = 20

    def available(self, order: Order) -> bool:
        return order.distance_km <= self.max_km

    def fee(self, order: Order) -> int:
        return self.base + math.ceil(order.distance_km) * self.per_km

    def eta(self, order: Order) -> str:
        return "2 小时内"


@dataclass(frozen=True)
class Pickup:
    name: ClassVar[str] = "到店自提"

    def available(self, order: Order) -> bool:
        return True

    def fee(self, order: Order) -> int:
        return 0

    def eta(self, order: Order) -> str:
        return "今天可取"


METHODS: dict[str, ShippingMethod] = {
    "express": Express(),
    "same_city": SameCity(),
    "pickup": Pickup(),
}


def checkout_fee(order: Order, method: ShippingMethod) -> int:
    if not method.available(order):
        raise ValueError(f"{method.name}不支持这个订单")
    return method.fee(order)


def quote_all(order: Order, methods: dict[str, ShippingMethod] = METHODS) -> list[str]:
    return [
        f"{m.name}：{m.fee(order) / 100:.2f} 元，{m.eta(order)}"
        for m in methods.values()
        if m.available(order)
    ]


if __name__ == "__main__":
    order = Order(weight_g=2300, distance_km=8.5, subtotal=6800)
    print(checkout_fee(order, METHODS["express"]))
    print("\n".join(quote_all(order)))
    print("\n".join(quote_all(Order(weight_g=500, distance_km=25, subtotal=12000))))
