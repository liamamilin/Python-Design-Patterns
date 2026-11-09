"""第 13 章：GoF 装饰器。每一层包住另一个 Writer，增加一项职责，接口不变。"""
from __future__ import annotations

from typing import Protocol

from examples.ch13_export_v1 import PHONE, mask_phone, messages


class Writer(Protocol):
    def write(self, line: str) -> None: ...


class ListWriter:
    """最终的目的地。真实程序里可能是文件、屏幕或工单系统。"""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def write(self, line: str) -> None:
        self.lines.append(line)


class WriterDecorator:
    def __init__(self, inner: Writer) -> None:
        self.inner = inner

    def write(self, line: str) -> None:
        self.inner.write(line)


class Masking(WriterDecorator):
    def write(self, line: str) -> None:
        self.inner.write(PHONE.sub(mask_phone, line))


class Truncating(WriterDecorator):
    def __init__(self, inner: Writer, limit: int) -> None:
        super().__init__(inner)
        self.limit = limit

    def write(self, line: str) -> None:
        if len(line) > self.limit:
            line = line[: self.limit - 1] + "…"
        self.inner.write(line)


class Counting(WriterDecorator):
    def __init__(self, inner: Writer) -> None:
        super().__init__(inner)
        self.count = 0

    def write(self, line: str) -> None:
        self.count += 1
        self.inner.write(line)


def export(chat: list[tuple[str, str]], writer: Writer) -> None:
    for who, text in chat:
        writer.write(f"{who}：{text}")


def build_writer(dest: Writer, *, mask: bool = True, limit: int | None = None) -> Writer:
    writer = dest
    if limit is not None:
        writer = Truncating(writer, limit)
    if mask:
        writer = Masking(writer)  # 最后包上的一层最先执行：先打码，再截断
    return writer


if __name__ == "__main__":
    ticket = ListWriter()
    export(messages, Masking(Truncating(ticket, 16)))
    print(ticket.lines)

    leaky = ListWriter()
    export(messages, Truncating(Masking(leaky), 16))
    print(leaky.lines)
