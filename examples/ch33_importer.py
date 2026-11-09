"""第 33 章：需求变了之后的导入工具。只在真正痛的地方重构：读取、校验规则、输出。

用法（在仓库根目录）：
    python -m examples.ch33_importer examples/data/supplier_b.json --db 商品.db
"""
from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
import sys
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Protocol, TextIO

from examples.ch32_import_v1 import REQUIRED, Product, parse_price, parse_stock

RawRow = dict[str, str]  # 统一的中间形态：sku、name、price、stock 四个字段，都是字符串


class FormatError(ValueError):
    """整个文件都无法处理，比如缺少列。"""


@dataclass(frozen=True)
class Problem:
    where: str  # “第 4 行”或“第 3 条”
    message: str


@dataclass
class Result:
    products: list[Product] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)


# ---- 读取：每种格式一个函数，把来源的样子转换成统一的 RawRow ----

def read_csv_rows(text: str) -> list[tuple[str, RawRow]]:
    reader = csv.DictReader(io.StringIO(text))
    missing = [name for name in REQUIRED if name not in (reader.fieldnames or [])]
    if missing:
        raise FormatError(f"缺少列：{', '.join(missing)}")
    return [(f"第 {n} 行", {k: row[k] or "" for k in REQUIRED}) for n, row in enumerate(reader, start=2)]


def read_json_rows(text: str) -> list[tuple[str, RawRow]]:
    try:
        data = json.loads(text, parse_float=Decimal)  # 价格按十进制读入，不经过 float
    except json.JSONDecodeError as e:
        raise FormatError(f"不是合法的 JSON：第 {e.lineno} 行第 {e.colno} 列") from None
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise FormatError("缺少 items 列表")
    rows = []
    for n, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise FormatError(f"第 {n} 条不是一个对象")
        rows.append((f"第 {n} 条", {
            "sku": str(item.get("code", "")),
            "name": str(item.get("title", "")),
            "price": str(item.get("price", "")),
            "stock": str(item.get("qty", "")),
        }))
    return rows


READERS: dict[str, Callable[[str], list[tuple[str, RawRow]]]] = {
    ".csv": read_csv_rows,
    ".json": read_json_rows,
}


# ---- 校验：每条规则一个函数，互不依赖，返回错误信息或 None ----

def not_empty(row: RawRow) -> str | None:
    return None if row["sku"].strip() and row["name"].strip() else "sku 和 name 不能为空"


def sku_format(row: RawRow) -> str | None:
    sku = row["sku"].strip()
    if sku and not re.fullmatch(r"[A-Z]{2}-\d{4}", sku):
        return f"sku 格式应为两个大写字母加四位数字：{sku}"
    return None


def name_length(row: RawRow) -> str | None:
    return f"商品名超过 40 个字：{len(row['name'])}" if len(row["name"]) > 40 else None


def valid_price(row: RawRow) -> str | None:
    try:
        parse_price(row["price"])
    except ValueError as e:
        return str(e)
    return None


def valid_stock(row: RawRow) -> str | None:
    try:
        parse_stock(row["stock"])
    except ValueError as e:
        return str(e)
    return None


RULES: list[Callable[[RawRow], str | None]] = [not_empty, sku_format, name_length, valid_price, valid_stock]


def validate(rows: list[tuple[str, RawRow]], rules=RULES) -> Result:
    result = Result()
    seen: set[str] = set()
    for where, row in rows:
        messages = [m for rule in rules if (m := rule(row)) is not None]
        sku = row["sku"].strip()
        if not messages and sku in seen:
            messages.append(f"sku 重复：{sku}")  # 跨行的检查，不是单行规则
        if messages:
            result.problems.append(Problem(where, "；".join(messages)))
            continue
        seen.add(sku)
        result.products.append(Product(sku, row["name"].strip(), parse_price(row["price"]), parse_stock(row["stock"])))
    return result


# ---- 输出：每种去处一个对象，都有 write(result) ----

class Sink(Protocol):
    def write(self, result: Result) -> None: ...


class JsonReport:
    def __init__(self, out: TextIO) -> None:
        self.out = out

    def write(self, result: Result) -> None:
        report = {
            "imported": len(result.products),
            "rejected": len(result.problems),
            "stock_value_yuan": f"{sum(p.price_cents * p.stock for p in result.products) / 100:.2f}",
            "problems": [f"{p.where}：{p.message}" for p in result.problems],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2), file=self.out)


class SqliteSink:
    """把合格的商品写进 SQLite；同一个 sku 再次导入时更新价格和库存。"""

    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, result: Result) -> None:
        with closing(sqlite3.connect(self.path)) as conn, conn:  # closing 负责关闭，conn 负责提交或回滚
            conn.execute(
                "CREATE TABLE IF NOT EXISTS products"
                " (sku TEXT PRIMARY KEY, name TEXT, price_cents INTEGER, stock INTEGER)"
            )
            conn.executemany(
                "INSERT INTO products VALUES (?, ?, ?, ?) ON CONFLICT(sku) DO UPDATE SET"
                " name = excluded.name, price_cents = excluded.price_cents, stock = excluded.stock",
                [(p.sku, p.name, p.price_cents, p.stock) for p in result.products],
            )


def import_file(path: Path) -> Result:
    reader = READERS.get(path.suffix.lower())
    if reader is None:
        raise FormatError(f"不支持的文件类型：{path.suffix}")
    return validate(reader(path.read_text(encoding="utf-8-sig")))


def main(argv: list[str], out: TextIO = sys.stdout) -> int:
    if not argv:
        print("用法：python -m examples.ch33_importer <文件> [--db 数据库文件]", file=sys.stderr)
        return 2
    path, sinks = Path(argv[0]), [JsonReport(out)]
    if "--db" in argv:
        sinks.append(SqliteSink(Path(argv[argv.index("--db") + 1])))
    try:
        result = import_file(path)
    except FormatError as e:
        print(f"无法导入 {path.name}：{e}", file=sys.stderr)
        return 2
    for sink in sinks:
        sink.write(result)
    return 1 if result.problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["examples/data/supplier_b.json"]))
