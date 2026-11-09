"""第 09 章：Python 角度。普通的类，在一个地方创建一次，再传给需要它的对象。"""
from __future__ import annotations

import threading


class TicketMachine:
    def __init__(self, prefix: str = "A") -> None:
        self.prefix = prefix
        self._count = 0
        self._lock = threading.Lock()

    def take(self) -> str:
        with self._lock:
            self._count += 1
            return f"{self.prefix}{self._count:03d}"


class Kiosk:
    def __init__(self, machine: TicketMachine) -> None:
        self.machine = machine

    def press(self) -> str:
        return self.machine.take()


class PhoneBooking:
    def __init__(self, machine: TicketMachine) -> None:
        self.machine = machine

    def book(self) -> str:
        return self.machine.take()


def build_branch() -> tuple[Kiosk, PhoneBooking]:
    machine = TicketMachine()  # 唯一的实例在这里创建，再交给需要它的对象
    return Kiosk(machine), PhoneBooking(machine)


# 另一种写法：模块级对象。模块在一个进程里只导入一次，这个对象自然只有一个。
default_machine = TicketMachine()


if __name__ == "__main__":
    kiosk, phone = build_branch()
    print("大厅：", kiosk.press(), "手机：", phone.book())
    business = TicketMachine("B")
    print("对公：", business.take())
