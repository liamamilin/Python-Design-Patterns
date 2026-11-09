"""第 16 章：Python 角度。cached_property 实现延迟加载；通用的 __getattr__ 代理有坑。"""
from __future__ import annotations

from functools import cached_property
from pathlib import Path


class Lesson:
    def __init__(self, title: str, path: Path) -> None:
        self.title = title
        self.path = path

    @cached_property
    def text(self) -> str:
        return self.path.read_text("utf-8")  # 第一次访问时才读，之后直接用缓存的值


class AnyProxy:
    """把所有找不到的属性都转给被代理的对象。"""

    def __init__(self, target: object) -> None:
        self._target = target

    def __getattr__(self, name: str):
        return getattr(self._target, name)


if __name__ == "__main__":
    import tempfile

    from examples.ch16_course_v1 import RealLesson

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp, "01-入门.txt")
        path.write_text("讲义", "utf-8")
        lesson = Lesson("入门", path)
        print("text" in vars(lesson), lesson.text, "text" in vars(lesson))
        proxy = AnyProxy(RealLesson("入门", path))
        print(proxy.content(), str(proxy).startswith("<"), isinstance(proxy, RealLesson))
