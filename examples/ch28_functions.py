"""第 28 章：函数的写法。规则是闭包，命令是字典里的函数，“工厂”就是一次字典查找。"""
from __future__ import annotations

from collections.abc import Callable

from examples.ch28_classes import Record

Rule = Callable[[Record], str | None]


def keyword(*words: str, category: str) -> Rule:
    def rule(r: Record) -> str | None:
        return category if any(w in r.desc for w in words) else None

    return rule


def over(amount: int, category: str) -> Rule:
    return lambda r: category if r.amount > amount else None


def classify(r: Record, rules: list[Rule]) -> str:
    return next((c for rule in rules if (c := rule(r)) is not None), "其他")


def add(book: list[Record], desc: str, amount: str) -> str:
    book.append(Record(desc, int(amount)))
    return f"已记录：{desc}"


def total(book: list[Record]) -> str:
    return f"合计 {sum(r.amount for r in book) / 100:.2f} 元"


COMMANDS: dict[str, Callable[..., str]] = {"add": add, "total": total}


def run(book: list[Record], line: str) -> str:
    name, *args = line.split()
    if name not in COMMANDS:
        raise ValueError(f"未知命令: {name}")
    return COMMANDS[name](book, *args)


RULES: list[Rule] = [
    over(50000, "大额支出"),
    keyword("咖啡", "拿铁", "奶茶", category="饮品"),
    keyword("地铁", "公交", "打车", category="交通"),
]


class CountingRule:
    """需要记住状态时，可调用对象和函数一样能放进规则列表。"""

    def __init__(self, rule: Rule) -> None:
        self.rule = rule
        self.hits = 0

    def __call__(self, r: Record) -> str | None:
        result = self.rule(r)
        if result is not None:
            self.hits += 1
        return result


def keyword_rules_wrong(categories: dict[str, str]) -> list[Rule]:
    """常见错误：在循环里创建 lambda，它们捕获的是同一个变量。"""
    return [lambda r: category if word in r.desc else None for word, category in categories.items()]


def keyword_rules(categories: dict[str, str]) -> list[Rule]:
    return [keyword(word, category=category) for word, category in categories.items()]


if __name__ == "__main__":
    book: list[Record] = []
    for line in ["add 瑞幸拿铁 1600", "add 地铁 400", "add 买显示器 129900", "total"]:
        print(run(book, line))
    print([classify(r, RULES) for r in book])
