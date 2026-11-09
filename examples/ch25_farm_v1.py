"""第 25 章：第一版。农场小游戏的存档直接返回内部的字典。"""
from __future__ import annotations


class Farm:
    SEED_PRICE, CROP_PRICE = 10, 25

    def __init__(self) -> None:
        self.day = 1
        self.coins = 100
        self.crops: dict[str, int] = {}

    def plant(self, crop: str, n: int) -> None:
        cost = n * self.SEED_PRICE
        if cost > self.coins:
            raise ValueError("金币不够")
        self.coins -= cost
        self.crops[crop] = self.crops.get(crop, 0) + n

    def harvest(self, crop: str) -> None:
        self.coins += self.crops.pop(crop) * self.CROP_PRICE

    def next_day(self) -> None:
        self.day += 1

    def summary(self) -> str:
        crops = "、".join(f"{k}×{v}" for k, v in sorted(self.crops.items())) or "空地"
        return f"第 {self.day} 天，金币 {self.coins}，{crops}"

    def save(self) -> tuple[int, int, dict[str, int]]:
        return self.day, self.coins, self.crops  # 字典是同一个对象

    def load(self, saved: tuple[int, int, dict[str, int]]) -> None:
        self.day, self.coins, self.crops = saved


if __name__ == "__main__":
    farm = Farm()
    farm.plant("萝卜", 3)
    slot = farm.save()
    farm.plant("萝卜", 2)
    farm.next_day()
    farm.load(slot)
    print(farm.summary())  # 读档后，萝卜却是 5 棵
