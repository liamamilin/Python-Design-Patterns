"""第 06 章：第一版。还书提醒加上“演练”开关之后，dry_run 判断分散在多处。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(frozen=True)
class Loan:
    reader: str
    book: str
    due: date

    @property
    def key(self) -> str:
        return f"{self.reader}|{self.book}|{self.due.isoformat()}"


loans = [
    Loan("王芳", "城南旧事", date(2026, 3, 10)),
    Loan("李雷", "活着", date(2026, 3, 11)),
    Loan("赵敏", "围城", date(2026, 3, 20)),
]


def due_soon(items: list[Loan], today: date, days: int = 2) -> list[Loan]:
    return [x for x in items if today <= x.due <= today + timedelta(days=days)]


def reminder_text(loan: Loan) -> str:
    return f"{loan.reader}，您借的《{loan.book}》将于{loan.due.month}月{loan.due.day}日到期"


def send_reminders(
    items: list[Loan], today: date, outbox: Path, log: Path, dry_run: bool = False
) -> int:
    sent = set(json.loads(log.read_text("utf-8"))) if log.exists() else set()
    count = 0
    for loan in due_soon(items, today):
        if loan.key in sent:
            continue
        if dry_run:
            print("[演练]", reminder_text(loan))
        else:
            with outbox.open("a", encoding="utf-8") as f:
                f.write(reminder_text(loan) + "\n")
        sent.add(loan.key)
        count += 1
    log.write_text(json.dumps(sorted(sent), ensure_ascii=False), "utf-8")
    return count


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        today = date(2026, 3, 9)
        print("演练：", send_reminders(loans, today, folder / "outbox.txt", folder / "sent.json", dry_run=True))
        print("正式：", send_reminders(loans, today, folder / "outbox.txt", folder / "sent.json"))
