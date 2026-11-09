"""第 03 章：Python 组织程序的基本工具。

同一个任务（清洗用户评论），依次用函数、类、继承、组合、抽象基类和协议来组织，
看每种工具分别解决什么问题。
运行：python -m examples.ch03_tools
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from functools import partial
from typing import Callable, Protocol, runtime_checkable


# 1. 函数：只看输入，只给输出
def strip_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


# 2. 函数也是数据：可以放进列表，按顺序执行
def apply_all(text: str, steps: list[Callable[[str], str]]) -> str:
    for step in steps:
        text = step(text)
    return text


basic_steps = [strip_spaces, partial(truncate, limit=12)]


# 3. 类：数据、处理和状态需要放在一起
class Censor:
    def __init__(self, words: list[str]) -> None:
        self.words = words
        self.replaced = 0  # 状态：累计屏蔽了多少处

    def __call__(self, text: str) -> str:
        for word in self.words:
            count = text.count(word)
            if count:
                self.replaced += count
                text = text.replace(word, "*" * len(word))
        return text


# 4. 继承：在父类的基础上改写一部分行为
class Cleaner:
    def __init__(self, limit: int) -> None:
        self.limit = limit

    def clean(self, text: str) -> str:
        return truncate(strip_spaces(text), self.limit)


class CensoringCleaner(Cleaner):
    def __init__(self, limit: int, words: list[str]) -> None:
        super().__init__(limit)
        self.censor = Censor(words)

    def clean(self, text: str) -> str:
        return super().clean(self.censor(text))


# 5. 组合：把几个部件装在一起，而不是派生新的类
class Pipeline:
    def __init__(self, *steps: Callable[[str], str]) -> None:
        self.steps = list(steps)

    def __call__(self, text: str) -> str:
        return apply_all(text, self.steps)


# 6. 抽象基类：要求子类必须提供某些方法
class Step(ABC):
    @abstractmethod
    def __call__(self, text: str) -> str:
        """接收文本，返回处理后的文本。"""


class Lowercase(Step):
    def __call__(self, text: str) -> str:
        return text.lower()


class Forgetful(Step):
    """忘了实现 __call__：创建对象时就会报错。"""


# 7. 协议：只关心“有没有这个方法”，不要求继承任何类
@runtime_checkable
class TextStep(Protocol):
    def __call__(self, text: str) -> str: ...


def run_steps(text: str, steps: list[TextStep]) -> str:
    return apply_all(text, steps)


comment = "  这家店的  咖啡 太难喝了，简直是垃圾！！  "

only_censor = Pipeline(strip_spaces, Censor(["垃圾"]))
for_english = Pipeline(strip_spaces, Censor(["垃圾"]), Lowercase(), partial(truncate, limit=20))


if __name__ == "__main__":
    print(apply_all(comment, basic_steps))
    censor = Censor(["垃圾"])
    print(Pipeline(strip_spaces, censor)(comment), censor.replaced)
    print(CensoringCleaner(20, ["垃圾"]).clean(comment))
