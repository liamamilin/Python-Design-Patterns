"""第 12 章：第一版。装修预算是固定两层的字典：房间 → 项目。"""
from __future__ import annotations

budget = {
    "客厅": {"地板": 8000, "沙发": 6500},
    "厨房": {"橱柜": 12000, "油烟机": 3000, "灶具": 2000},
}


def total(budget: dict) -> int:
    return sum(sum(room.values()) for room in budget.values())


# 需求变了：有直接挂在最外层的费用，厨房里的电器又单独成组
budget_later = {
    "设计费": 5000,
    "客厅": {"地板": 8000, "沙发": 6500},
    "厨房": {"橱柜": 12000, "电器": {"油烟机": 3000, "灶具": 2000}},
}


if __name__ == "__main__":
    print(total(budget))
    try:
        total(budget_later)
    except AttributeError as e:
        print("出错：", e)
