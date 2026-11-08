"""第 04 章：从问题选择模式。

停车场按车型收费。同一个需求用三种写法实现，行为完全一样，
区别在于新增车型时要改哪里、谁能扩展、要付出什么代价。
运行：python -m examples.ch04_parking
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod


def billable_hours(minutes: int) -> int:
    """不足一小时按一小时算，最少收一小时。"""
    return max(1, math.ceil(minutes / 60))


# 写法一：条件判断
def fee_by_if(vehicle: str, minutes: int) -> int:
    hours = billable_hours(minutes)
    if vehicle == "car":
        return 5 * hours
    if vehicle == "motorcycle":
        return 2 * hours
    raise ValueError(f"未知车型: {vehicle}")


# 写法二：字典里放函数
RATES = {
    "car": lambda hours: 5 * hours,
    "motorcycle": lambda hours: 2 * hours,
}


def fee_by_table(vehicle: str, minutes: int) -> int:
    try:
        rule = RATES[vehicle]
    except KeyError:
        raise ValueError(f"未知车型: {vehicle}") from None
    return rule(billable_hours(minutes))


# 写法三：每种收费规则一个类
class FeeRule(ABC):
    @abstractmethod
    def fee(self, hours: int) -> int:
        """根据计费小时数返回费用（元）。"""


class CarRule(FeeRule):
    def fee(self, hours: int) -> int:
        return 5 * hours


class MotorcycleRule(FeeRule):
    def fee(self, hours: int) -> int:
        return 2 * hours


def fee_by_rule(rule: FeeRule, minutes: int) -> int:
    return rule.fee(billable_hours(minutes))


# 调用方仍然要把“car”这样的字符串变成规则对象：选择并没有消失，只是挪了位置
RULES = {"car": CarRule(), "motorcycle": MotorcycleRule()}


# 新需求：货车每小时 10 元，最低收 20 元
def truck_fee(hours: int) -> int:
    return max(20, 10 * hours)


class TruckRule(FeeRule):
    def fee(self, hours: int) -> int:
        return truck_fee(hours)


if __name__ == "__main__":
    for vehicle, minutes in [("car", 90), ("motorcycle", 30)]:
        print(vehicle, fee_by_if(vehicle, minutes), fee_by_table(vehicle, minutes), fee_by_rule(RULES[vehicle], minutes))
    RATES["truck"] = truck_fee
    print("truck", fee_by_table("truck", 61), fee_by_rule(TruckRule(), 61))
