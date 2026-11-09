"""第 23 章：第一版。先把云相册的所有照片取回来放进列表，再查找。"""
from __future__ import annotations

PLACES = ["杭州", "成都", "大理", "青岛", "西安", "厦门", "拉萨"]


class FakePhotoApi:
    """模拟云相册的分页接口：每次请求返回一页，超出范围返回空列表。"""

    def __init__(self, total: int = 200, page_size: int = 20) -> None:
        self.total, self.page_size = total, page_size
        self.requests = 0  # 统计发出了几次网络请求

    def get_page(self, page: int) -> list[dict]:
        self.requests += 1
        start = (page - 1) * self.page_size
        stop = min(start + self.page_size, self.total)
        return [{"id": i, "place": PLACES[i % len(PLACES)], "year": 2020 + i % 5} for i in range(start, stop)]


def all_photos(api: FakePhotoApi) -> list[dict]:
    photos: list[dict] = []
    page = 1
    while True:
        batch = api.get_page(page)
        if not batch:
            break
        photos += batch
        page += 1
    return photos


if __name__ == "__main__":
    api = FakePhotoApi()
    first = next(p for p in all_photos(api) if p["place"] == "成都")
    print(first, "请求次数：", api.requests)
