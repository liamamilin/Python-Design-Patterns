"""第 10 章：适配器。把云考勤 SDK 包装成报表认识的 PunchSource，两边的代码都不用改。"""
from __future__ import annotations

from datetime import datetime, tzinfo

from examples.ch10_attendance import BEIJING, HQ_RECORDS, LocalClock, Punch, late_report
from examples.ch10_cloud_sdk import BRANCH_EVENTS, BRANCH_STAFF, CloudAttendanceClient


class CloudClockAdapter:
    """对象适配器：持有一个 SDK 对象，对外提供 punches()。"""

    KINDS = {"IN": "上班", "OUT": "下班"}

    def __init__(self, client: CloudAttendanceClient, staff: dict[str, str], tz: tzinfo) -> None:
        self.client = client
        self.staff = staff
        self.tz = tz

    def punches(self) -> list[Punch]:
        result = []
        for e in self.client.fetch_events():
            kind = self.KINDS.get(e["type"])
            if kind is None:
                continue  # 午休打卡（BREAK）在报表里没有对应的概念，丢弃
            name = self.staff.get(e["uid"])
            if name is None:
                raise ValueError(f"花名册里没有工号 {e['uid']}")
            at = datetime.fromtimestamp(e["ts"] / 1000, tz=self.tz)
            result.append(Punch(name, at, kind))
        return result


class CloudClockClassAdapter(CloudAttendanceClient):
    """类适配器：继承 SDK 的类，再补上 punches()。"""

    def __init__(self, events: list[dict], staff: dict[str, str], tz: tzinfo) -> None:
        super().__init__(events)
        self._adapter = CloudClockAdapter(self, staff, tz)

    def punches(self) -> list[Punch]:
        return self._adapter.punches()


if __name__ == "__main__":
    branch = CloudClockAdapter(CloudAttendanceClient(BRANCH_EVENTS), BRANCH_STAFF, BEIJING)
    print(late_report([LocalClock(HQ_RECORDS), branch]))
