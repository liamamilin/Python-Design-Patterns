"""第 29 章：宠物医院预约。类型标注、NewType、Protocol、ABC、dataclass、TypedDict 各自能做什么，不能做什么。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, NewType, Protocol, TypedDict, runtime_checkable

def total_fee(visits: int, price: int) -> int:
    return visits * price


PetId = NewType("PetId", int)
OwnerId = NewType("OwnerId", int)


def book(owner: OwnerId, pet: PetId, slot: str) -> str:
    return f"主人 {owner} 为宠物 {pet} 预约了 {slot}"


Species = Literal["猫", "狗"]


@dataclass
class Pet:
    name: str
    species: Species
    weight_kg: float


@dataclass(frozen=True)
class CheckedPet:
    name: str
    species: Species
    weight_kg: float

    def __post_init__(self) -> None:
        if self.species not in ("猫", "狗"):
            raise ValueError(f"本院只接诊猫和狗，不接诊：{self.species}")
        if not isinstance(self.weight_kg, (int, float)) or not 0 < self.weight_kg < 100:
            raise ValueError(f"体重不合理：{self.weight_kg!r}")


@runtime_checkable
class Notifier(Protocol):
    def notify(self, owner: OwnerId, text: str) -> None: ...


class SmsNotifier:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def notify(self, owner: OwnerId, text: str) -> None:
        self.sent.append(f"{owner}:{text}")


class WrongNotifier:
    def notify(self) -> None:  # 参数完全不对
        pass


class Reminder(ABC):
    @abstractmethod
    def remind(self, pet: PetId) -> str: ...


class VisitJson(TypedDict):
    pet: int
    slot: str


if __name__ == "__main__":
    print(total_fee("3", 2))  # type: ignore[arg-type]  # 运行时不检查类型：得到 "33"
    print(book(PetId(7), OwnerId(3), "周六上午"))  # type: ignore[arg-type]  # 参数顺序反了，照样运行
    print(Pet("团子", "兔", "4"))  # type: ignore[arg-type]
    print(isinstance(WrongNotifier(), Notifier))
