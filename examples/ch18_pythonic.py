"""第 18 章：Python 角度。订阅者就是一个可调用对象；订阅时返回一个“取消订阅”的函数。"""
from __future__ import annotations

from collections.abc import Callable

Handler = Callable[[float], None]


class Signal:
    def __init__(self) -> None:
        self._handlers: list[Handler] = []

    def connect(self, handler: Handler) -> Callable[[], None]:
        self._handlers.append(handler)

        def disconnect() -> None:
            if handler in self._handlers:
                self._handlers.remove(handler)

        return disconnect

    def emit(self, value: float) -> None:
        errors: list[Exception] = []
        for handler in tuple(self._handlers):
            try:
                handler(value)
            except Exception as e:
                errors.append(e)
        if errors:
            raise ExceptionGroup(f"{len(errors)} 个订阅者出错", errors)


class Greenhouse:
    def __init__(self) -> None:
        self.temp_changed = Signal()

    def record(self, temp: float) -> None:
        self.temp_changed.emit(temp)


if __name__ == "__main__":
    house = Greenhouse()
    readings: list[float] = []
    stop = house.temp_changed.connect(readings.append)
    house.record(28)
    stop()
    house.record(31)
    print(readings)
