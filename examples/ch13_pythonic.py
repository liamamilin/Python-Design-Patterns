"""第 13 章：Python 角度。Writer 只有一个方法时，可以就是一个函数；包装它的是高阶函数。"""
from __future__ import annotations

import functools
from collections.abc import Callable

from examples.ch13_export_v1 import PHONE, mask_phone, messages

WriteFn = Callable[[str], None]


def masking(write: WriteFn) -> WriteFn:
    @functools.wraps(write)
    def wrapped(line: str) -> None:
        write(PHONE.sub(mask_phone, line))

    return wrapped


def truncating(limit: int) -> Callable[[WriteFn], WriteFn]:
    def decorate(write: WriteFn) -> WriteFn:
        @functools.wraps(write)
        def wrapped(line: str) -> None:
            write(line if len(line) <= limit else line[: limit - 1] + "…")

        return wrapped

    return decorate


@masking
def print_line(line: str) -> None:
    """打印到屏幕。定义时就包上了打码，之后每次调用都会打码。"""
    print(line)


def export(chat: list[tuple[str, str]], write: WriteFn) -> None:
    for who, text in chat:
        write(f"{who}：{text}")


if __name__ == "__main__":
    export(messages, print_line)
    lines: list[str] = []
    export(messages, masking(truncating(16)(lines.append)))
    print(lines, print_line.__name__)
