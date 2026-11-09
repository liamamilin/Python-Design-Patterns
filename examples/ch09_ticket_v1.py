"""第 09 章：第一版。大厅取号机和手机预约各自创建了一个计数器。"""
from __future__ import annotations


class TicketMachine:
    def __init__(self, prefix: str = "A") -> None:
        self.prefix = prefix
        self.count = 0

    def take(self) -> str:
        self.count += 1
        return f"{self.prefix}{self.count:03d}"


class Kiosk:
    """大厅里的取号机。"""

    def __init__(self) -> None:
        self.machine = TicketMachine()

    def press(self) -> str:
        return self.machine.take()


class PhoneBooking:
    """手机预约取号。"""

    def __init__(self) -> None:
        self.machine = TicketMachine()

    def book(self) -> str:
        return self.machine.take()


if __name__ == "__main__":
    kiosk, phone = Kiosk(), PhoneBooking()
    print("大厅：", kiosk.press())
    print("手机：", phone.book())
