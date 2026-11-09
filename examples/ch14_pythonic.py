"""第 14 章：Python 角度。模块本身就是外观：一个顶层函数，加上仍可单独使用的辅助函数。"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from examples.ch14_facade import Backup


def backup_folder(source: Path, dest: Path, keep: int = 3) -> Path:
    """给只想“备份一下”的调用方：用当前时间，其他全用默认值。"""
    return Backup(source, dest, keep).run(datetime.now())


def quick_archive(source: Path, dest: Path) -> Path:
    """标准库里的外观：shutil.make_archive 一行完成打包，但没有清单和轮换。"""
    return Path(shutil.make_archive(str(dest / source.name), "zip", root_dir=source))


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp, "文档")
        src.mkdir()
        (src / "a.txt").write_text("hello", "utf-8")
        print(backup_folder(src, Path(tmp, "备份")).name.startswith("backup-"))
        print(quick_archive(src, Path(tmp)).name)
