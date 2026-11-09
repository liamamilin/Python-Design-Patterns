"""第 32 章：数据导入工具的第一版。只支持一种 CSV 格式，不用任何模式，先把它做对。

用法（在仓库根目录）：
    python -m examples.ch32_import_v1 examples/data/supplier_a.csv
"""
from __future__ import annotations

import csv
import io
import json
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED = ("sku", "name", "price", "stock")


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price_cents: int
    stock: int


@dataclass(frozen=True)
class Problem:
    line: int
    message: str


@dataclass
class Result:
    products: list[Product] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)


def parse_price(text: str) -> int:
    """把“12.5”这样的价格转换成分。用 Decimal，避免二进制浮点数的误差。"""
    try:
        value = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError(f"价格不是数字：{text!r}") from None
    if not value.is_finite():
        raise ValueError(f"价格不是有限的数字：{text!r}")
    if value <= 0:
        raise ValueError(f"价格必须大于 0：{text}")
    if value >= 1_000_000:
        raise ValueError(f"价格超出合理范围：{text}")
    if value != value.quantize(Decimal("0.01")):
        raise ValueError(f"价格最多两位小数：{text}")
    return int(value * 100)


def parse_stock(text: str) -> int:
    if not text.strip().isdecimal():
        raise ValueError(f"库存必须是非负整数：{text!r}")
    return int(text)


def read_csv(text: str) -> Result:
    result = Result()
    reader = csv.DictReader(io.StringIO(text))
    missing = [name for name in REQUIRED if name not in (reader.fieldnames or [])]
    if missing:
        result.problems.append(Problem(1, f"缺少列：{', '.join(missing)}"))
        return result
    seen: set[str] = set()
    for line, raw in enumerate(reader, start=2):  # 第 1 行是表头
        row = {k: raw[k] or "" for k in REQUIRED}  # 列数不足的行，缺的字段是 None
        try:
            sku, name = row["sku"].strip(), row["name"].strip()
            if not sku or not name:
                raise ValueError("sku 和 name 不能为空")
            if sku in seen:
                raise ValueError(f"sku 重复：{sku}")
            product = Product(sku, name, parse_price(row["price"]), parse_stock(row["stock"]))
        except ValueError as e:
            result.problems.append(Problem(line, str(e)))
            continue
        seen.add(sku)
        result.products.append(product)
    return result


def report(result: Result) -> dict:
    return {
        "imported": len(result.products),
        "rejected": len(result.problems),
        "stock_value_yuan": f"{sum(p.price_cents * p.stock for p in result.products) / 100:.2f}",
        "problems": [f"第 {p.line} 行：{p.message}" for p in result.problems],
    }


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("用法：python -m examples.ch32_import_v1 <文件.csv>", file=sys.stderr)
        return 2
    text = Path(argv[0]).read_text(encoding="utf-8-sig")  # utf-8-sig：去掉 Excel 写入的 BOM
    result = read_csv(text)
    print(json.dumps(report(result), ensure_ascii=False, indent=2))
    return 1 if result.problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["examples/data/supplier_a.csv"]))
