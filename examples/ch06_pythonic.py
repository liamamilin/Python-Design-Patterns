"""第 06 章：Python 角度。部件只在开始时创建一次，用一个函数返回配套的一组就够了。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from examples.ch06_abstract_factory import (
    FileSender,
    FileSentLog,
    PrintSender,
    ReadOnlySentLog,
    Sender,
    SentLog,
)
from examples.ch06_reminders_v1 import Loan, due_soon, loans, reminder_text


@dataclass(frozen=True)
class Kit:
    sender: Sender
    sent_log: SentLog


def live_kit(folder: Path) -> Kit:
    return Kit(FileSender(folder / "outbox.txt"), FileSentLog(folder / "sent.json"))


def dry_run_kit(folder: Path) -> Kit:
    return Kit(PrintSender(), ReadOnlySentLog(folder / "sent.json"))


def send_with_kit(items: list[Loan], today: date, kit: Kit) -> int:
    count = 0
    for loan in due_soon(items, today):
        if loan.key in kit.sent_log:
            continue
        kit.sender.send(reminder_text(loan))
        kit.sent_log.add(loan.key)
        count += 1
    kit.sent_log.save()
    return count


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        today = date(2026, 3, 9)
        print("演练：", send_with_kit(loans, today, dry_run_kit(folder)))
        print("正式：", send_with_kit(loans, today, live_kit(folder)))
