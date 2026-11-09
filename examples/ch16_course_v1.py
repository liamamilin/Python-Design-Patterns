"""第 16 章：第一版。打开课程页面时，每一课的讲义都被读进内存；付费课谁都能看。"""
from __future__ import annotations

from pathlib import Path


class RealLesson:
    loads = 0  # 仅用于演示：统计一共读了几次文件

    def __init__(self, title: str, path: Path) -> None:
        self.title = title
        self._text = path.read_text("utf-8")  # 真实场景里是一个很大的视频或讲义文件
        RealLesson.loads += 1

    def content(self) -> str:
        return self._text

    def __str__(self) -> str:
        return f"《{self.title}》"


def open_course(folder: Path) -> list[RealLesson]:
    return [RealLesson(p.stem, p) for p in sorted(folder.glob("*.txt"))]


def outline(lessons: list) -> list[str]:
    return [lesson.title for lesson in lessons]


def make_demo_course(folder: Path, n: int = 5) -> None:
    for i in range(1, n + 1):
        (folder / f"{i:02d}-第{i}课.txt").write_text(f"第 {i} 课的讲义……", "utf-8")


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        make_demo_course(Path(tmp))
        course = open_course(Path(tmp))
        print(outline(course), "读了", RealLesson.loads, "个文件")
