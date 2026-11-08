"""第 10 章：Python 角度。核心逻辑只接收数据，适配器就是边界上的一个转换函数。"""
from __future__ import annotations

from datetime import datetime, tzinfo

from examples.ch10_attendance import BEIJING, HQ_RECORDS, Punch, late_arrivals
from examples.ch10_cloud_sdk import BRANCH_EVENTS, BRANCH_STAFF, CloudAttendanceClient

KINDS = {"IN": "上班", "OUT": "下班"}


def punches_from_cloud(events: list[dict], staff: dict[str, str], tz: tzinfo) -> list[Punch]:
    return [
        Punch(staff[e["uid"]], datetime.fromtimestamp(e["ts"] / 1000, tz=tz), KINDS[e["type"]])
        for e in events
        if e["type"] in KINDS
    ]


if __name__ == "__main__":
    client = CloudAttendanceClient(BRANCH_EVENTS)
    branch = punches_from_cloud(client.fetch_events(), BRANCH_STAFF, BEIJING)
    print(late_arrivals(HQ_RECORDS + branch))
