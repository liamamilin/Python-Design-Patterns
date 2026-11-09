"""第 30 章：用语言机制改写。装饰器登记规则，生成器产出计划，上下文管理器保证要么全改、要么全不改。"""
from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

NameRule = Callable[[int, Path], str]
RULES: dict[str, NameRule] = {}


def rule(name: str) -> Callable[[NameRule], NameRule]:
    """登记用的装饰器：把函数放进 RULES，原样返回它。这不是 GoF 的装饰器模式。"""

    def register(func: NameRule) -> NameRule:
        RULES[name] = func
        return func

    return register


@rule("序号")
def numbered(i: int, path: Path) -> str:
    return f"{i:03d}{path.suffix}"


@rule("保留原名加序号")
def keep_stem(i: int, path: Path) -> str:
    return f"{i:03d}_{path.stem}{path.suffix}"


def photos(folder: Path) -> Iterator[Path]:
    yield from sorted(p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))


def plan(paths: Iterator[Path], name_rule: NameRule, prefix: str = "") -> Iterator[tuple[Path, Path]]:
    for i, path in enumerate(paths, 1):
        target = path.with_name(prefix + name_rule(i, path))
        if target != path:
            yield path, target


@contextmanager
def all_or_nothing() -> Iterator[Callable[[Path, Path], None]]:
    """进入时准备好一个“改名”函数；离开时如果出了错，按相反顺序全部改回去。"""
    done: list[tuple[Path, Path]] = []

    def rename(src: Path, dst: Path) -> None:
        if dst.exists():
            raise FileExistsError(dst.name)
        src.rename(dst)
        done.append((src, dst))

    try:
        yield rename
    except BaseException:
        for src, dst in reversed(done):
            dst.rename(src)
        raise


class AllOrNothing:
    """同样的上下文管理器，写成类：__enter__ 是准备，__exit__ 是收尾。"""

    def __enter__(self) -> AllOrNothing:
        self.done: list[tuple[Path, Path]] = []
        return self

    def rename(self, src: Path, dst: Path) -> None:
        if dst.exists():
            raise FileExistsError(dst.name)
        src.rename(dst)
        self.done.append((src, dst))

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            for src, dst in reversed(self.done):
                dst.rename(src)
        return False  # 不吞掉异常


def rename_folder(folder: Path, rule_name: str, prefix: str = "") -> list[str]:
    with all_or_nothing() as rename:
        steps = list(plan(photos(folder), RULES[rule_name], prefix))
        for src, dst in steps:
            rename(src, dst)
    return [dst.name for _, dst in steps]


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in ("IMG_0102.jpg", "IMG_0101.jpg", "说明.txt"):
            (folder / name).write_bytes(b"")
        print(sorted(RULES))
        print(rename_folder(folder, "序号", prefix="西湖_"))
