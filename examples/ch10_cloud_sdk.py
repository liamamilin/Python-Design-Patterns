"""第 10 章：分店新装的云考勤，厂商提供的 SDK。我们不能修改它。"""
from __future__ import annotations


class CloudAttendanceClient:
    def __init__(self, events: list[dict]) -> None:
        self._events = events  # 真实的 SDK 会通过网络取数据，这里用列表代替

    def fetch_events(self, since_ms: int = 0) -> list[dict]:
        return [e for e in self._events if e["ts"] >= since_ms]


BRANCH_EVENTS = [
    {"uid": "E-2001", "ts": 1773017520000, "type": "IN"},
    {"uid": "E-2002", "ts": 1773019020000, "type": "IN"},
    {"uid": "E-2002", "ts": 1773028800000, "type": "BREAK"},
    {"uid": "E-2001", "ts": 1773050700000, "type": "OUT"},
    {"uid": "E-2002", "ts": 1773052200000, "type": "OUT"},
]

BRANCH_STAFF = {"E-2001": "赵敏", "E-2002": "孙浩"}
