"""第 16 章：代理。和真实对象接口相同，在中间控制访问：延迟加载、检查权限。"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from examples.ch16_course_v1 import RealLesson, make_demo_course, outline


class Lesson(Protocol):
    title: str

    def content(self) -> str: ...


class LazyLesson:
    """虚代理：标题马上就有，讲义等到第一次真正需要时才读。"""

    def __init__(self, title: str, path: Path) -> None:
        self.title = title
        self._path = path
        self._real: RealLesson | None = None

    def content(self) -> str:
        if self._real is None:
            self._real = RealLesson(self.title, self._path)
        return self._real.content()


class PaidLesson:
    """保护代理：只有已报名的学员能看讲义，标题谁都能看。"""

    def __init__(self, inner: Lesson, enrolled: set[str], user: str) -> None:
        self.inner = inner
        self.enrolled = enrolled
        self.user = user
        self.title = inner.title

    def content(self) -> str:
        if self.user not in self.enrolled:
            raise PermissionError(f"{self.user} 还没有报名，不能观看《{self.title}》")
        return self.inner.content()


def open_course(folder: Path, user: str, enrolled: set[str], free: int = 1) -> list[Lesson]:
    """前 free 课免费试看，其余需要报名。所有课都延迟加载。"""
    lessons: list[Lesson] = []
    for i, path in enumerate(sorted(folder.glob("*.txt"))):
        lesson: Lesson = LazyLesson(path.stem, path)
        if i >= free:
            lesson = PaidLesson(lesson, enrolled, user)
        lessons.append(lesson)
    return lessons


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        make_demo_course(Path(tmp))
        course = open_course(Path(tmp), user="小周", enrolled={"小林"})
        print(outline(course), "读了", RealLesson.loads, "个文件")
        print(course[0].content(), "读了", RealLesson.loads, "个文件")
        try:
            course[1].content()
        except PermissionError as e:
            print(e)
