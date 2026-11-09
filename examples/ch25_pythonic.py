"""第 25 章：Python 角度。存档要写到磁盘时，用 JSON 这样只表示数据的格式，并在读档时检查。"""
from __future__ import annotations

import json

from examples.ch25_memento import Farm, FarmMemento


def to_json(m: FarmMemento) -> str:
    return json.dumps({"version": 1, "day": m._day, "coins": m._coins, "crops": dict(m._crops)}, ensure_ascii=False)


def from_json(text: str) -> FarmMemento:
    data = json.loads(text)
    if data.get("version") != 1:
        raise ValueError("不认识的存档版本")
    day, coins, crops = data["day"], data["coins"], data["crops"]
    if not (isinstance(day, int) and day >= 1 and isinstance(coins, int) and coins >= 0):
        raise ValueError("存档内容不合法")
    if not all(isinstance(k, str) and isinstance(v, int) and v > 0 for k, v in crops.items()):
        raise ValueError("存档里的作物数据不合法")
    return FarmMemento(day, coins, tuple(sorted(crops.items())))


if __name__ == "__main__":
    farm = Farm()
    farm.plant("萝卜", 3)
    text = to_json(farm.save())
    print(text)
    other = Farm()
    other.restore(from_json(text))
    print(other.summary())
