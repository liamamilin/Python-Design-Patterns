"""第 24 章：Python 角度。联动状态是表单内容的纯函数：输入一份内容，算出界面该怎样显示。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from examples.ch24_form_v1 import DOMESTIC


@dataclass(frozen=True)
class FormValues:
    origin: str | None = None
    dest: str | None = None
    depart: date | None = None
    round_trip: bool = False
    return_date: date | None = None


@dataclass(frozen=True)
class UiState:
    passport_visible: bool
    return_date_enabled: bool
    search_enabled: bool


def ui_state(v: FormValues) -> UiState:
    cities = {v.origin, v.dest} - {None}
    return UiState(
        passport_visible=any(c not in DOMESTIC for c in cities),
        return_date_enabled=v.round_trip,
        search_enabled=(
            v.origin is not None
            and v.dest is not None
            and v.origin != v.dest
            and v.depart is not None
            and (not v.round_trip or v.return_date is not None)
        ),
    )


if __name__ == "__main__":
    print(ui_state(FormValues(origin="东京", dest="上海", depart=date(2026, 5, 1))))
