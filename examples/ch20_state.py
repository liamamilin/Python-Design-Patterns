"""第 20 章：状态模式。每个状态是一个对象，只实现自己允许的操作，其余一律拒绝。"""
from __future__ import annotations

from datetime import datetime

from examples.ch20_booking_v1 import EARLY, GRACE


class NotAllowed(Exception):
    pass


class State:
    name = "?"

    def approve(self, b: Booking) -> State:
        raise NotAllowed(f"{self.name}的预订不能审批")

    def cancel(self, b: Booking) -> State:
        raise NotAllowed(f"{self.name}的预订不能取消")

    def check_in(self, b: Booking, now: datetime) -> State:
        raise NotAllowed(f"{self.name}的预订不能签到")

    def expire(self, b: Booking, now: datetime) -> State:
        return self  # 只有“已确认”会因超时而改变，其他状态忽略


class Pending(State):
    name = "待审批"

    def approve(self, b: Booking) -> State:
        return Confirmed()

    def cancel(self, b: Booking) -> State:
        return Cancelled()


class Confirmed(State):
    name = "已确认"

    def cancel(self, b: Booking) -> State:
        return Cancelled()

    def check_in(self, b: Booking, now: datetime) -> State:
        if not b.start - EARLY <= now <= b.start + GRACE:
            raise NotAllowed("不在签到时间内")
        return CheckedIn()

    def expire(self, b: Booking, now: datetime) -> State:
        return Released() if now > b.start + GRACE else self


class CheckedIn(State):
    name = "已签到"


class Cancelled(State):
    name = "已取消"


class Released(State):
    name = "已释放"


class Booking:
    def __init__(self, room: str, start: datetime) -> None:
        self.room, self.start = room, start
        self.state: State = Pending()

    @property
    def status(self) -> str:
        return self.state.name

    def approve(self) -> None:
        self.state = self.state.approve(self)

    def cancel(self) -> None:
        self.state = self.state.cancel(self)

    def check_in(self, now: datetime) -> None:
        self.state = self.state.check_in(self, now)

    def expire(self, now: datetime) -> None:
        self.state = self.state.expire(self, now)


if __name__ == "__main__":
    b = Booking("301", datetime(2026, 3, 9, 14, 0))
    b.approve()
    b.check_in(datetime(2026, 3, 9, 13, 55))
    try:
        b.cancel()
    except NotAllowed as e:
        print(e)
