"""第 07 章：Python 角度。表单只解析一次，变成一个数据类；SQL 和说明各由一个函数生成。"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from examples.ch07_builder import SORTS
from examples.ch07_search_v1 import connect


@dataclass(frozen=True, kw_only=True)
class SearchFilter:
    district: str | None = None
    max_rent: int | None = None
    min_rooms: int | None = None
    subway: bool = False
    sort: str = "price"

    def __post_init__(self) -> None:
        if self.sort not in SORTS:
            raise ValueError(f"未知排序: {self.sort}")


def parse_form(form: dict[str, str]) -> SearchFilter:
    return SearchFilter(
        district=form.get("district") or None,
        max_rent=int(form["max_rent"]) if form.get("max_rent") else None,
        min_rooms=int(form["min_rooms"]) if form.get("min_rooms") else None,
        subway=bool(form.get("subway")),
        sort=form.get("sort") or "price",
    )


def to_sql(f: SearchFilter) -> tuple[str, list[object]]:
    conds: list[str] = []
    params: list[object] = []
    if f.district:
        conds.append("district = ?")
        params.append(f.district)
    if f.max_rent is not None:
        conds.append("rent <= ?")
        params.append(f.max_rent)
    if f.min_rooms is not None:
        conds.append("rooms >= ?")
        params.append(f.min_rooms)
    if f.subway:
        conds.append("near_subway = 1")
    sql = "SELECT title, rent FROM listings"
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    return sql + f" ORDER BY {SORTS[f.sort][0]}", params


def describe(f: SearchFilter) -> str:
    parts = []
    if f.district:
        parts.append(f"{f.district}区")
    if f.max_rent is not None:
        parts.append(f"月租不超过 {f.max_rent} 元")
    if f.min_rooms is not None:
        parts.append(f"至少 {f.min_rooms} 室")
    if f.subway:
        parts.append("近地铁")
    return ("，".join(parts) or "全部房源") + "；" + SORTS[f.sort][1]


def search(conn: sqlite3.Connection, form: dict[str, str]) -> tuple[str, list[tuple[str, int]]]:
    f = parse_form(form)
    sql, params = to_sql(f)
    return describe(f), conn.execute(sql, params).fetchall()


if __name__ == "__main__":
    print(search(connect(), {"district": "朝阳", "subway": "on"}))
    print(SearchFilter(district="海淀", max_rent=6000))
