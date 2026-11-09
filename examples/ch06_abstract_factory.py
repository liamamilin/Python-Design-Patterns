"""第 06 章：GoF 抽象工厂。一个工厂对象负责创建一整组彼此配套的部件。"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Protocol

from examples.ch06_reminders_v1 import Loan, due_soon, loans, reminder_text


class Sender(Protocol):
    def send(self, text: str) -> None: ...


class SentLog(Protocol):
    def __contains__(self, key: str) -> bool: ...
    def add(self, key: str) -> None: ...
    def save(self) -> None: ...


# ---- 正式家族：写入文件 ----

class FileSender:
    """把提醒写进发件箱文件，由另一个程序负责真正投递。"""

    def __init__(self, path: Path) -> None:
        self.path = path

    def send(self, text: str) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(text + "\n")


class FileSentLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.keys = set(json.loads(path.read_text("utf-8"))) if path.exists() else set()

    def __contains__(self, key: str) -> bool:
        return key in self.keys

    def add(self, key: str) -> None:
        self.keys.add(key)

    def save(self) -> None:
        self.path.write_text(json.dumps(sorted(self.keys), ensure_ascii=False), "utf-8")


# ---- 演练家族：只打印，读正式记录但从不写回 ----

class PrintSender:
    def send(self, text: str) -> None:
        print("[演练]", text)


class ReadOnlySentLog(FileSentLog):
    def save(self) -> None:
        pass  # 演练不改变任何正式状态


# ---- 内存家族：给单元测试用 ----

class MemorySender:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, text: str) -> None:
        self.messages.append(text)


class MemorySentLog:
    def __init__(self) -> None:
        self.keys: set[str] = set()

    def __contains__(self, key: str) -> bool:
        return key in self.keys

    def add(self, key: str) -> None:
        self.keys.add(key)

    def save(self) -> None:
        pass


# ---- 抽象工厂与具体工厂 ----

class ReminderServices(ABC):
    @abstractmethod
    def create_sender(self) -> Sender: ...

    @abstractmethod
    def create_sent_log(self) -> SentLog: ...


class LiveServices(ReminderServices):
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def create_sender(self) -> Sender:
        return FileSender(self.folder / "outbox.txt")

    def create_sent_log(self) -> SentLog:
        return FileSentLog(self.folder / "sent.json")


class DryRunServices(ReminderServices):
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def create_sender(self) -> Sender:
        return PrintSender()

    def create_sent_log(self) -> SentLog:
        return ReadOnlySentLog(self.folder / "sent.json")


class MemoryServices(ReminderServices):
    def __init__(self) -> None:
        self.sender = MemorySender()
        self.sent_log = MemorySentLog()

    def create_sender(self) -> Sender:
        return self.sender

    def create_sent_log(self) -> SentLog:
        return self.sent_log


def send_reminders(items: list[Loan], today: date, services: ReminderServices) -> int:
    sender = services.create_sender()
    sent = services.create_sent_log()
    count = 0
    for loan in due_soon(items, today):
        if loan.key in sent:
            continue
        sender.send(reminder_text(loan))
        sent.add(loan.key)
        count += 1
    sent.save()
    return count


def services_for(mode: str, folder: Path) -> ReminderServices:
    factories = {"live": LiveServices, "dry-run": DryRunServices}
    try:
        return factories[mode](folder)
    except KeyError:
        raise ValueError(f"未知模式: {mode}") from None


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        today = date(2026, 3, 9)
        print("演练：", send_reminders(loans, today, services_for("dry-run", folder)))
        print("正式：", send_reminders(loans, today, services_for("live", folder)))
        print((folder / "outbox.txt").read_text("utf-8"), end="")
