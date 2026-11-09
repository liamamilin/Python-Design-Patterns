"""第 34 章：另一种可行的设计。用模板方法：父类固定“读取 → 校验 → 输出”，子类只提供读取这一步。"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path

from examples.ch33_importer import (
    RULES,
    FormatError,
    RawRow,
    Result,
    Sink,
    read_csv_rows,
    read_json_rows,
    validate,
)


class Importer(ABC):
    def run(self, path: Path, sinks: list[Sink]) -> Result:
        """模板方法：流程固定。"""
        rows = self.rows(path.read_text(encoding="utf-8-sig"))
        result = validate(rows, [*RULES, *self.extra_rules()])
        for sink in sinks:
            sink.write(result)
        return result

    @abstractmethod
    def rows(self, text: str) -> list[tuple[str, RawRow]]:
        """每种格式必须提供：把文件内容变成统一的行。"""

    def extra_rules(self) -> list:
        """钩子：某种格式特有的校验规则，默认没有。"""
        return []


class CsvImporter(Importer):
    def rows(self, text: str) -> list[tuple[str, RawRow]]:
        return read_csv_rows(text)


class JsonImporter(Importer):
    def rows(self, text: str) -> list[tuple[str, RawRow]]:
        return read_json_rows(text)


def has_weight(row: RawRow) -> str | None:
    """云岭茶业的要求：商品名里必须写明克重，比如“200g”。"""
    return None if re.search(r"\d+g", row["name"]) else f"商品名缺少克重：{row['name'][:10]}…"


class YunlingImporter(JsonImporter):
    def extra_rules(self) -> list:
        return [has_weight]


IMPORTERS: dict[str, type[Importer]] = {".csv": CsvImporter, ".json": JsonImporter}


def import_file(path: Path, sinks: list[Sink] | None = None) -> Result:
    importer = IMPORTERS.get(path.suffix.lower())
    if importer is None:
        raise FormatError(f"不支持的文件类型：{path.suffix}")
    return importer().run(path, sinks or [])


if __name__ == "__main__":
    import sys

    from examples.ch33_importer import JsonReport

    result = YunlingImporter().run(Path("examples/data/supplier_b.json"), [JsonReport(sys.stdout)])
