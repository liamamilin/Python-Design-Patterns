"""第 10 章：已有的考勤报表模块。工资、排班等好几处代码都在用它。"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Protocol

BEIJING = timezone(timedelta(hours=8))
WORK_START = time(9, 0)


@dataclass(frozen=True)
class Punch:
    employee: str
    at: datetime  # 带时区的本地时间
    kind: str  # "上班" 或 "下班"


class PunchSource(Protocol):
    def punches(self) -> list[Punch]: ...


class LocalClock:
    """总部那台考勤机的驱动，直接给出打卡记录。"""

    def __init__(self, records: list[Punch]) -> None:
        self.records = records

    def punches(self) -> list[Punch]:
        return list(self.records)


def late_arrivals(punches: Iterable[Punch]) -> list[str]:
    first_in: dict[tuple[str, date], datetime] = {}
    for p in punches:
        if p.kind != "上班":
            continue
        key = (p.employee, p.at.date())
        if key not in first_in or p.at < first_in[key]:
            first_in[key] = p.at
    return sorted(
        f"{day:%m-%d} {name}" for (name, day), at in first_in.items() if at.time() > WORK_START
    )


def late_report(sources: Iterable[PunchSource]) -> list[str]:
    return late_arrivals(p for source in sources for p in source.punches())


HQ_RECORDS = [
    Punch("王芳", datetime(2026, 3, 9, 8, 58, tzinfo=BEIJING), "上班"),
    Punch("李雷", datetime(2026, 3, 9, 9, 5, tzinfo=BEIJING), "上班"),
    Punch("王芳", datetime(2026, 3, 9, 18, 0, tzinfo=BEIJING), "下班"),
    Punch("李雷", datetime(2026, 3, 9, 18, 10, tzinfo=BEIJING), "下班"),
]


if __name__ == "__main__":
    print(late_report([LocalClock(HQ_RECORDS)]))
