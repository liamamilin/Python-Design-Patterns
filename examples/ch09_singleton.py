"""第 09 章：GoF 单例。类自己保证只有一个实例，以及这种保证的范围。"""
from __future__ import annotations

import multiprocessing
import threading
from concurrent.futures import ProcessPoolExecutor


class BrokenTicketMachine:
    _instance: BrokenTicketMachine | None = None

    def __new__(cls) -> BrokenTicketMachine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.count = 0  # 每次调用 BrokenTicketMachine() 都会重新执行这一行

    def take(self) -> str:
        self.count += 1
        return f"A{self.count:03d}"


class TicketMachine:
    _instance: TicketMachine | None = None
    _create_lock = threading.Lock()

    def __new__(cls) -> TicketMachine:
        with cls._create_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._count = 0
                instance._lock = threading.Lock()
                cls._instance = instance
        return cls._instance

    def take(self) -> str:
        with self._lock:
            self._count += 1
            return f"A{self._count:03d}"

    @classmethod
    def _reset_for_tests(cls) -> None:
        cls._instance = None


class Kiosk:
    def __init__(self) -> None:
        self.machine = TicketMachine()

    def press(self) -> str:
        return self.machine.take()


class PhoneBooking:
    def __init__(self) -> None:
        self.machine = TicketMachine()

    def book(self) -> str:
        return self.machine.take()


def take_many(n: int) -> list[str]:
    machine = TicketMachine()
    return [machine.take() for _ in range(n)]


def take_in_new_process(n: int) -> list[str]:
    spawn = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=spawn) as pool:
        return pool.submit(take_many, n).result()


if __name__ == "__main__":
    print("大厅：", Kiosk().press(), "手机：", PhoneBooking().book())
    print("进程一：", take_in_new_process(2))
    print("进程二：", take_in_new_process(2))
