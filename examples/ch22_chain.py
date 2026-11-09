"""第 22 章：责任链。每个处理者要么处理请求，要么交给下一个。链怎么排，由组装的人决定。"""
from __future__ import annotations


class Handler:
    def __init__(self) -> None:
        self.next: Handler | None = None

    def handle(self, text: str) -> str:
        reply = self.try_handle(text)
        if reply is not None:
            return reply
        if self.next is None:
            return "抱歉，我没听懂"  # 链走到头也没人处理：明确地说出来
        return self.next.handle(text)

    def try_handle(self, text: str) -> str | None:
        return None


class Keyword(Handler):
    def __init__(self, word: str, reply: str) -> None:
        super().__init__()
        self.word, self.reply = word, reply

    def try_handle(self, text: str) -> str | None:
        return self.reply if self.word in text else None


class ChildLock(Handler):
    """儿童模式：遇到涉及花钱的指令，直接拒绝，不再往后传。"""

    def __init__(self, words: tuple[str, ...] = ("买", "外卖", "支付")) -> None:
        super().__init__()
        self.words = words

    def try_handle(self, text: str) -> str | None:
        if any(w in text for w in self.words):
            return "儿童模式下不能消费"
        return None


def chain(*handlers: Handler) -> Handler:
    for current, following in zip(handlers, handlers[1:]):
        current.next = following
    return handlers[0]


def common_handlers() -> list[Handler]:
    return [
        Keyword("闹钟", "好的，闹钟已设好"),
        Keyword("天气", "今天晴，18 到 26 度"),
        Keyword("外卖", "已为你下单外卖"),
        Keyword("买", "已加入购物车"),
        Keyword("播放", "开始播放"),
    ]


def kitchen_speaker() -> Handler:
    return chain(*common_handlers())


def kids_speaker() -> Handler:
    return chain(ChildLock(), *common_handlers())


if __name__ == "__main__":
    kids = kids_speaker()
    for text in ("帮我买一盒彩笔", "帮我点个外卖", "明早七点的闹钟", "讲个笑话"):
        print(text, "→", kids.handle(text))
