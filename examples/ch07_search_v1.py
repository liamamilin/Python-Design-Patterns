"""第 07 章：第一版。租房搜索的查询和“当前筛选条件”说明，各自解析一遍表单。"""
from __future__ import annotations

import sqlite3

LISTINGS = [
    # 标题, 区, 月租(元), 室, 面积(平方米), 近地铁
    ("朝阳 两居 近地铁", "朝阳", 5800, 2, 68, 1),
    ("朝阳 一居", "朝阳", 4200, 1, 45, 0),
    ("朝阳 三居", "朝阳", 8800, 3, 105, 1),
    ("海淀 两居", "海淀", 6500, 2, 72, 1),
    ("海淀 两居 老小区", "海淀", 5200, 2, 60, 0),
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE listings (title TEXT, district TEXT, rent INTEGER,"
        " rooms INTEGER, area INTEGER, near_subway INTEGER)"
    )
    conn.executemany("INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?)", LISTINGS)
    return conn


def search(conn: sqlite3.Connection, form: dict[str, str]) -> list[tuple[str, int]]:
    conds: list[str] = []
    params: list[object] = []
    if form.get("district"):
        conds.append("district = ?")
        params.append(form["district"])
    if form.get("max_rent"):
        conds.append("rent <= ?")
        params.append(int(form["max_rent"]))
    if form.get("min_rooms"):
        conds.append("rooms >= ?")
        params.append(int(form["min_rooms"]))
    if form.get("subway"):
        conds.append("near_subway = 1")
    sql = "SELECT title, rent FROM listings"
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY rent"
    return conn.execute(sql, params).fetchall()


def describe(form: dict[str, str]) -> str:
    parts = []
    if form.get("district"):
        parts.append(f"{form['district']}区")
    if form.get("max_rent"):
        parts.append(f"月租不超过 {form['max_rent']} 元")
    if form.get("min_rooms"):
        parts.append(f"至少 {form['min_rooms']} 室")
    return "，".join(parts) or "全部房源"


if __name__ == "__main__":
    form = {"district": "朝阳", "subway": "on"}
    print("筛选条件：", describe(form))
    for row in search(connect(), form):
        print(row)
