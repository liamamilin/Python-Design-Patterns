"""第 30 章：第一版。批量重命名照片，一个循环做完所有事。中途出错会留下一半改了、一半没改的文件夹。"""
from __future__ import annotations

from pathlib import Path


def rename_all(folder: Path, prefix: str) -> list[str]:
    done = []
    for i, path in enumerate(sorted(folder.glob("*.jpg")), 1):
        target = path.with_name(f"{prefix}_{i:03d}.jpg")
        if target.exists():
            raise FileExistsError(target.name)
        path.rename(target)
        done.append(target.name)
    return done


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in ("IMG_0102.jpg", "IMG_0101.jpg"):
            (folder / name).write_bytes(b"")
        print(rename_all(folder, "西湖"))
