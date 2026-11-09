"""第 20 章：Python 角度。状态用枚举，允许的转换写成一张表，整个状态机一眼看全。"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from examples.ch20_booking_v1 import EARLY, GRACE


class Status(Enum):
    PENDING = "待审批"
    CONFIRMED = "已确认"
    CHECKED_IN = "已签到"
    CANCELLED = "已取消"
    RELEASED = "已释放"


TRANSITIONS: dict[tuple[Status, str], Status] = {
    (Status.PENDING, "approve"): Status.CONFIRMED,
    (Status.PENDING, "cancel"): Status.CANCELLED,
    (Status.CONFIRMED, "cancel"): Status.CANCELLED,
    (Status.CONFIRMED, "check_in"): Status.CHECKED_IN,
    (Status.CONFIRMED, "expire"): Status.RELEASED,
}


class Booking:
    def __init__(self, room: str, start: datetime) -> None:
        self.room, self.start = room, start
        self.status = Status.PENDING

    def fire(self, event: str, now: datetime | None = None) -> None:
        target = TRANSITIONS.get((self.status, event))
        if target is None:
            if event == "expire":
                return  # 和状态对象版本一致：其他状态忽略超时
            raise ValueError(f"{self.status.value}的预订不能执行 {event}")
        if event == "check_in" and not (now and self.start - EARLY <= now <= self.start + GRACE):
            raise ValueError("不在签到时间内")
        if event == "expire" and not (now and now > self.start + GRACE):
            return
        self.status = target


def allowed(status: Status) -> list[str]:
    return [event for (s, event) in TRANSITIONS if s is status]


if __name__ == "__main__":
    for s in Status:
        print(f"{s.value}：{', '.join(allowed(s)) or '（无可执行的操作）'}")
