"""第 28 章：类的写法。账单分类规则、命令和工厂，各是一组小类。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    desc: str
    amount: int  # 分


class Rule(ABC):
    @abstractmethod
    def match(self, r: Record) -> str | None: ...


class KeywordRule(Rule):
    def __init__(self, words: tuple[str, ...], category: str) -> None:
        self.words, self.category = words, category

    def match(self, r: Record) -> str | None:
        return self.category if any(w in r.desc for w in self.words) else None


class OverRule(Rule):
    def __init__(self, amount: int, category: str) -> None:
        self.amount, self.category = amount, category

    def match(self, r: Record) -> str | None:
        return self.category if r.amount > self.amount else None


class Classifier:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules

    def classify(self, r: Record) -> str:
        for rule in self.rules:
            category = rule.match(r)
            if category is not None:
                return category
        return "其他"


class Command(ABC):
    @abstractmethod
    def execute(self, book: list[Record], args: list[str]) -> str: ...


class AddCommand(Command):
    def execute(self, book: list[Record], args: list[str]) -> str:
        book.append(Record(args[0], int(args[1])))
        return f"已记录：{args[0]}"


class TotalCommand(Command):
    def execute(self, book: list[Record], args: list[str]) -> str:
        return f"合计 {sum(r.amount for r in book) / 100:.2f} 元"


class CommandFactory:
    def create(self, name: str) -> Command:
        if name == "add":
            return AddCommand()
        if name == "total":
            return TotalCommand()
        raise ValueError(f"未知命令: {name}")


RULES: list[Rule] = [
    OverRule(50000, "大额支出"),
    KeywordRule(("咖啡", "拿铁", "奶茶"), "饮品"),
    KeywordRule(("地铁", "公交", "打车"), "交通"),
]


if __name__ == "__main__":
    book: list[Record] = []
    factory = CommandFactory()
    for line in ["add 瑞幸拿铁 1600", "add 地铁 400", "add 买显示器 129900", "total"]:
        name, *args = line.split()
        print(factory.create(name).execute(book, args))
    print([Classifier(RULES).classify(r) for r in book])
