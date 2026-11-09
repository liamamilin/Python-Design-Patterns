"""第 22 章：Python 角度。处理者是函数，链是一个列表，顺序一眼可见。"""
from __future__ import annotations

from collections.abc import Callable

Rule = Callable[[str], str | None]


def keyword(word: str, reply: str) -> Rule:
    return lambda text: reply if word in text else None


def child_lock(*words: str) -> Rule:
    return lambda text: "儿童模式下不能消费" if any(w in text for w in words) else None


COMMON: list[Rule] = [
    keyword("闹钟", "好的，闹钟已设好"),
    keyword("天气", "今天晴，18 到 26 度"),
    keyword("外卖", "已为你下单外卖"),
    keyword("买", "已加入购物车"),
    keyword("播放", "开始播放"),
]
KIDS: list[Rule] = [child_lock("买", "外卖", "支付"), *COMMON]


def respond(text: str, rules: list[Rule]) -> str:
    for rule in rules:
        reply = rule(text)
        if reply is not None:
            return reply
    return "抱歉，我没听懂"


if __name__ == "__main__":
    print(respond("帮我点个外卖", KIDS), respond("帮我点个外卖", COMMON))
