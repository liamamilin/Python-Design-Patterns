"""第 23 章：迭代器。按需一页一页地取，调用方用普通的 for 循环。"""
from __future__ import annotations

from collections import deque

from examples.ch23_photos_v1 import FakePhotoApi


class PhotoIterator:
    """实现 Python 的迭代器协议：__iter__ 返回自己，__next__ 给出下一张或抛出 StopIteration。"""

    def __init__(self, api: FakePhotoApi) -> None:
        self.api = api
        self.page = 0
        self.buffer: deque[dict] = deque()
        self.finished = False

    def __iter__(self) -> PhotoIterator:
        return self

    def __next__(self) -> dict:
        if not self.buffer:
            if self.finished:
                raise StopIteration
            self.page += 1
            self.buffer.extend(self.api.get_page(self.page))
            if not self.buffer:
                self.finished = True
                raise StopIteration
        return self.buffer.popleft()


if __name__ == "__main__":
    api = FakePhotoApi()
    first = next(p for p in PhotoIterator(api) if p["place"] == "成都")
    print(first, "请求次数：", api.requests)
