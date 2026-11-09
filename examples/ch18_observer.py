"""第 18 章：观察者。温室只负责“温度变了”，谁关心谁来订阅。通知的顺序、出错和退订都要有明确的约定。"""
from __future__ import annotations

from typing import Protocol


class Observer(Protocol):
    def update(self, temp: float) -> None: ...


class NaiveGreenhouse:
    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def record(self, temp: float) -> None:
        for observer in self._observers:
            observer.update(temp)


class Greenhouse:
    """通知约定：
    1. 按订阅的先后顺序通知；
    2. 通知开始时对订阅者列表做一个快照，通知过程中的订阅和退订，从下一次才生效；
    3. 一个订阅者出错，不影响其他订阅者；全部通知完之后，把所有错误一起抛出。
    """

    def __init__(self) -> None:
        self._observers: list[Observer] = []
        self.temp: float | None = None

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def record(self, temp: float) -> None:
        self.temp = temp
        errors: list[Exception] = []
        for observer in tuple(self._observers):
            try:
                observer.update(temp)
            except Exception as e:
                errors.append(e)
        if errors:
            raise ExceptionGroup(f"{len(errors)} 个订阅者出错", errors)


class Fan:
    def __init__(self) -> None:
        self.on = False

    def update(self, temp: float) -> None:
        self.on = temp >= 30


class DataLog:
    def __init__(self) -> None:
        self.rows: list[float] = []

    def update(self, temp: float) -> None:
        self.rows.append(temp)


class FirstHeatAlert:
    """第一次超过 35℃ 时提醒一次，然后自己退订。"""

    def __init__(self, house: Greenhouse | NaiveGreenhouse) -> None:
        self.house = house
        self.messages: list[str] = []

    def update(self, temp: float) -> None:
        if temp >= 35:
            self.messages.append(f"今天第一次超过 35℃：{temp}℃")
            self.house.detach(self)


class CloudUploader:
    """把读数上传到云端。网络断了就抛出异常。"""

    def __init__(self) -> None:
        self.online = True

    def update(self, temp: float) -> None:
        if not self.online:
            raise ConnectionError("无法连接云端")


if __name__ == "__main__":
    house = Greenhouse()
    alert, log = FirstHeatAlert(house), DataLog()
    house.attach(alert)
    house.attach(log)
    for t in (28, 36, 37):
        house.record(t)
    print(alert.messages, log.rows)
