"""第 24 章：第一版。订票表单的各个控件互相引用，各自去更新别人。"""
from __future__ import annotations

DOMESTIC = {"北京", "上海", "成都", "广州"}


class Widget:
    def __init__(self) -> None:
        self.value: object = None
        self.enabled = True
        self.visible = True


class SearchButton(Widget):
    pass


class PassportField(Widget):
    def __init__(self) -> None:
        super().__init__()
        self.visible = False


class CityBox(Widget):
    def __init__(self, search: SearchButton, passport: PassportField) -> None:
        super().__init__()
        self.search, self.passport = search, passport
        self.other: CityBox | None = None  # 另一个城市框，创建后再连上

    def set(self, city: str) -> None:
        self.value = city
        self.passport.visible = city not in DOMESTIC
        if self.other is not None and self.other.value is not None:
            self.search.enabled = city != self.other.value


class RoundTripBox(Widget):
    def __init__(self, return_date: Widget) -> None:
        super().__init__()
        self.return_date = return_date

    def set(self, checked: bool) -> None:
        self.value = checked
        self.return_date.enabled = checked


if __name__ == "__main__":
    search, passport = SearchButton(), PassportField()
    origin, dest = CityBox(search, passport), CityBox(search, passport)
    origin.other, dest.other = dest, origin
    origin.set("北京")
    dest.set("东京")
    origin.set("东京")  # 出发地和目的地一样了
    print("查询按钮可用？", search.enabled, "护照栏显示？", passport.visible)
    dest.set("上海")  # 现在是 东京 → 上海，国际航线
    print("护照栏显示？", passport.visible)
