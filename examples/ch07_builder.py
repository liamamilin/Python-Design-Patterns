"""第 07 章：GoF 建造者。同一个构建过程（读表单），交给不同的建造者，得到不同的结果。"""
from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod

from examples.ch07_search_v1 import connect

SORTS = {
    "price": ("rent", "按租金从低到高"),
    "price_desc": ("rent DESC", "按租金从高到低"),
    "area": ("area DESC", "按面积从大到小"),
}


class SearchBuilder(ABC):
    @abstractmethod
    def district(self, name: str) -> None: ...

    @abstractmethod
    def max_rent(self, yuan: int) -> None: ...

    @abstractmethod
    def min_rooms(self, n: int) -> None: ...

    @abstractmethod
    def near_subway(self) -> None: ...

    @abstractmethod
    def sort(self, key: str) -> None: ...


class SqlBuilder(SearchBuilder):
    def __init__(self) -> None:
        self.conds: list[str] = []
        self.params: list[object] = []
        self.order = "rent"

    def district(self, name: str) -> None:
        self.conds.append("district = ?")
        self.params.append(name)

    def max_rent(self, yuan: int) -> None:
        self.conds.append("rent <= ?")
        self.params.append(yuan)

    def min_rooms(self, n: int) -> None:
        self.conds.append("rooms >= ?")
        self.params.append(n)

    def near_subway(self) -> None:
        self.conds.append("near_subway = 1")

    def sort(self, key: str) -> None:
        self.order = SORTS[key][0]  # 列名只从白名单里取，从不拼接用户输入

    def result(self) -> tuple[str, list[object]]:
        sql = "SELECT title, rent FROM listings"
        if self.conds:
            sql += " WHERE " + " AND ".join(self.conds)
        return sql + f" ORDER BY {self.order}", self.params


class DescriptionBuilder(SearchBuilder):
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.order = SORTS["price"][1]

    def district(self, name: str) -> None:
        self.parts.append(f"{name}区")

    def max_rent(self, yuan: int) -> None:
        self.parts.append(f"月租不超过 {yuan} 元")

    def min_rooms(self, n: int) -> None:
        self.parts.append(f"至少 {n} 室")

    def near_subway(self) -> None:
        self.parts.append("近地铁")

    def sort(self, key: str) -> None:
        self.order = SORTS[key][1]

    def result(self) -> str:
        return ("，".join(self.parts) or "全部房源") + "；" + self.order


def apply_form(form: dict[str, str], builder: SearchBuilder) -> None:
    """指挥者：只负责读表单、决定调用哪些步骤，不关心最后造出什么。"""
    if form.get("district"):
        builder.district(form["district"])
    if form.get("max_rent"):
        builder.max_rent(int(form["max_rent"]))
    if form.get("min_rooms"):
        builder.min_rooms(int(form["min_rooms"]))
    if form.get("subway"):
        builder.near_subway()
    sort = form.get("sort") or "price"
    if sort not in SORTS:
        raise ValueError(f"未知排序: {sort}")
    builder.sort(sort)


def search(conn: sqlite3.Connection, form: dict[str, str]) -> tuple[str, list[tuple[str, int]]]:
    sql_builder, text_builder = SqlBuilder(), DescriptionBuilder()
    apply_form(form, sql_builder)
    apply_form(form, text_builder)
    sql, params = sql_builder.result()
    return text_builder.result(), conn.execute(sql, params).fetchall()


if __name__ == "__main__":
    text, rows = search(connect(), {"district": "朝阳", "subway": "on", "sort": "price_desc"})
    print("筛选条件：", text)
    for row in rows:
        print(row)
