"""第 20 章：第一版。会议室预订用一个字符串记录状态，每个方法自己检查。"""
from __future__ import annotations

from datetime import datetime, timedelta

EARLY = timedelta(minutes=10)  # 最早提前 10 分钟签到
GRACE = timedelta(minutes=15)  # 开始后 15 分钟内不签到，自动释放


class Booking:
    def __init__(self, room: str, start: datetime) -> None:
        self.room, self.start = room, start
        self.status = "待审批"

    def approve(self) -> None:
        if self.status != "待审批":
            raise ValueError(f"{self.status}的预订不能审批")
        self.status = "已确认"

    def check_in(self, now: datetime) -> None:
        if self.status != "已确认":
            raise ValueError(f"{self.status}的预订不能签到")
        if not self.start - EARLY <= now <= self.start + GRACE:
            raise ValueError("不在签到时间内")
        self.status = "已签到"

    def expire(self, now: datetime) -> None:
        if self.status == "已确认" and now > self.start + GRACE:
            self.status = "已释放"

    def cancel(self) -> None:
        if self.status in ("已取消", "已释放"):  # 后来加的，漏掉了“已签到”
            raise ValueError(f"{self.status}的预订不能取消")
        self.status = "已取消"


if __name__ == "__main__":
    b = Booking("301", datetime(2026, 3, 9, 14, 0))
    b.approve()
    b.check_in(datetime(2026, 3, 9, 13, 55))
    b.cancel()  # 会议正在进行，预订却被取消了，会议室在系统里变成空闲
    print(b.status)
