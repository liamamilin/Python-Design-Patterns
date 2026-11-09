"""第 24 章：中介者。控件只通知表单“我变了”；所有联动规则集中在表单里。"""
from __future__ import annotations

from datetime import date
from typing import Protocol

from examples.ch24_form_v1 import DOMESTIC


class Mediator(Protocol):
    def changed(self, field: Field) -> None: ...


class Field:
    def __init__(self, mediator: Mediator, value: object = None, visible: bool = True) -> None:
        self.mediator = mediator
        self.value = value
        self.enabled = True
        self.visible = visible

    def set(self, value: object) -> None:
        self.value = value
        self.mediator.changed(self)  # 控件不认识别的控件，只告诉中介者


class TicketForm:
    def __init__(self) -> None:
        self.origin = Field(self)
        self.dest = Field(self)
        self.depart = Field(self)
        self.round_trip = Field(self, value=False)
        self.return_date = Field(self)
        self.passport = Field(self, visible=False)
        self.search = Field(self)
        self._refresh()

    def changed(self, field: Field) -> None:
        self._refresh()

    def _refresh(self) -> None:
        """每次有控件变化，都从完整的表单内容重新算出所有联动状态。"""
        cities = {self.origin.value, self.dest.value} - {None}
        self.passport.visible = any(c not in DOMESTIC for c in cities)
        self.return_date.enabled = bool(self.round_trip.value)
        self.search.enabled = (
            self.origin.value is not None
            and self.dest.value is not None
            and self.origin.value != self.dest.value
            and self.depart.value is not None
            and (not self.round_trip.value or self.return_date.value is not None)
        )


if __name__ == "__main__":
    form = TicketForm()
    form.origin.set("北京")
    form.dest.set("东京")
    form.origin.set("东京")
    print("查询按钮可用？", form.search.enabled)
    form.dest.set("上海")
    form.depart.set(date(2026, 5, 1))
    print("护照栏显示？", form.passport.visible, "查询按钮可用？", form.search.enabled)
