"""第 23 章：Python 角度。生成器函数就是最省事的迭代器；可迭代对象每次给出一个新的迭代器。"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from itertools import islice

from examples.ch23_photos_v1 import FakePhotoApi


def iter_photos(api: FakePhotoApi) -> Iterator[dict]:
    page = 1
    while batch := api.get_page(page):
        yield from batch
        page += 1


class Album:
    """可迭代对象：每次 for 循环都从头开始，得到一个新的迭代器。"""

    def __init__(self, api: FakePhotoApi) -> None:
        self.api = api

    def __iter__(self) -> Iterator[dict]:
        return iter_photos(self.api)


def places_by_year(api: FakePhotoApi, year: int) -> Counter[str]:
    """边取边数：任何时刻内存里最多只有一页照片。"""
    return Counter(p["place"] for p in iter_photos(api) if p["year"] == year)


if __name__ == "__main__":
    api = FakePhotoApi()
    print([p["id"] for p in islice(iter_photos(api), 25)][-3:], "请求次数：", api.requests)
    print(places_by_year(FakePhotoApi(), 2024).most_common(2))
