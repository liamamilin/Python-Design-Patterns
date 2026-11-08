"""第 10 章：不用适配器。为了接入新考勤机，修改了共用的报表模块。"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from examples.ch10_attendance import BEIJING, HQ_RECORDS, LocalClock, Punch, late_arrivals
from examples.ch10_cloud_sdk import BRANCH_EVENTS, BRANCH_STAFF, CloudAttendanceClient


def late_report(sources: Iterable[object]) -> list[str]:
    punches: list[Punch] = []
    for source in sources:
        if isinstance(source, LocalClock):
            punches += source.punches()
        elif isinstance(source, CloudAttendanceClient):
            for e in source.fetch_events():
                if e["type"] not in ("IN", "OUT"):
                    continue
                at = datetime.fromtimestamp(e["ts"] / 1000, tz=BEIJING)
                kind = "上班" if e["type"] == "IN" else "下班"
                punches.append(Punch(BRANCH_STAFF[e["uid"]], at, kind))
        else:
            raise TypeError(f"不认识的考勤来源: {source!r}")
    return late_arrivals(punches)


if __name__ == "__main__":
    print(late_report([LocalClock(HQ_RECORDS), CloudAttendanceClient(BRANCH_EVENTS)]))
