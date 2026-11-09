"""第 18 章：第一版。温室每记录一次温度，就逐个调用风扇、警报和记录器。"""
from __future__ import annotations


class Fan:
    def __init__(self) -> None:
        self.on = False

    def update(self, temp: float) -> None:
        self.on = temp >= 30


class Alarm:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def check(self, temp: float) -> None:
        if temp >= 35:
            self.messages.append(f"温度过高：{temp}℃")


class DataLog:
    def __init__(self) -> None:
        self.rows: list[float] = []

    def write(self, temp: float) -> None:
        self.rows.append(temp)


class Greenhouse:
    def __init__(self, fan: Fan, alarm: Alarm, log: DataLog) -> None:
        self.fan, self.alarm, self.log = fan, alarm, log
        self.temp: float | None = None

    def record(self, temp: float) -> None:
        self.temp = temp
        self.fan.update(temp)
        self.alarm.check(temp)
        self.log.write(temp)


if __name__ == "__main__":
    fan, alarm, log = Fan(), Alarm(), DataLog()
    house = Greenhouse(fan, alarm, log)
    for t in (28, 31, 36):
        house.record(t)
    print(fan.on, alarm.messages, log.rows)
