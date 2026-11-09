"""第 25 章：备忘录。农场把自己的状态装进一个不可变的快照；存档栏只保管，不查看。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FarmMemento:
    """只有 Farm 知道怎样读它。其他代码只负责保管。"""

    _day: int
    _coins: int
    _crops: tuple[tuple[str, int], ...]


class Farm:
    SEED_PRICE, CROP_PRICE = 10, 25

    def __init__(self) -> None:
        self._day = 1
        self._coins = 100
        self._crops: dict[str, int] = {}

    def plant(self, crop: str, n: int) -> None:
        cost = n * self.SEED_PRICE
        if cost > self._coins:
            raise ValueError("金币不够")
        self._coins -= cost
        self._crops[crop] = self._crops.get(crop, 0) + n

    def harvest(self, crop: str) -> None:
        self._coins += self._crops.pop(crop) * self.CROP_PRICE

    def next_day(self) -> None:
        self._day += 1

    def summary(self) -> str:
        crops = "、".join(f"{k}×{v}" for k, v in sorted(self._crops.items())) or "空地"
        return f"第 {self._day} 天，金币 {self._coins}，{crops}"

    def save(self) -> FarmMemento:
        return FarmMemento(self._day, self._coins, tuple(sorted(self._crops.items())))

    def restore(self, m: FarmMemento) -> None:
        self._day, self._coins, self._crops = m._day, m._coins, dict(m._crops)


class SaveSlots:
    """负责人：按名字保管快照，不读取、不修改其中的内容。"""

    def __init__(self) -> None:
        self._slots: dict[str, FarmMemento] = {}

    def save(self, name: str, farm: Farm) -> None:
        self._slots[name] = farm.save()

    def load(self, name: str, farm: Farm) -> None:
        farm.restore(self._slots[name])

    def names(self) -> list[str]:
        return sorted(self._slots)


if __name__ == "__main__":
    farm, slots = Farm(), SaveSlots()
    farm.plant("萝卜", 3)
    slots.save("开局", farm)
    farm.plant("萝卜", 2)
    farm.next_day()
    slots.load("开局", farm)
    print(farm.summary())
