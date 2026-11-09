"""第 14 章：外观。给备份涉及的几个模块提供一个简单的入口，但不把它们藏起来。"""
from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path

SKIP = {".DS_Store", "Thumbs.db"}


class Backup:
    def __init__(self, source: Path, dest: Path, keep: int = 3) -> None:
        self.source, self.dest, self.keep = source, dest, keep

    def run(self, now: datetime) -> Path:
        """备份一次：打包、写清单、只保留最近 keep 份。"""
        self.dest.mkdir(parents=True, exist_ok=True)
        archive = self.dest / f"backup-{now:%Y%m%d-%H%M%S}.zip"
        manifest = {}
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in self._files():
                name = path.relative_to(self.source).as_posix()
                manifest[name] = _sha256(path)
                zf.write(path, arcname=name)
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        self._rotate()
        return archive

    def verify(self, archive: Path) -> list[str]:
        """检查压缩包里的每个文件是否和清单一致，返回问题列表。"""
        problems = []
        with zipfile.ZipFile(archive) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            for name, digest in manifest.items():
                if hashlib.sha256(zf.read(name)).hexdigest() != digest:
                    problems.append(f"内容不一致：{name}")
        return problems

    def archives(self) -> list[Path]:
        return sorted(self.dest.glob("backup-*.zip"))

    def _files(self) -> list[Path]:
        return [p for p in sorted(self.source.rglob("*")) if p.is_file() and p.name not in SKIP]

    def _rotate(self) -> None:
        for old in self.archives()[: -self.keep]:
            old.unlink()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp, "文档")
        (src / "合同").mkdir(parents=True)
        (src / "合同" / "租房.txt").write_text("月租 5800", "utf-8")
        (src / ".DS_Store").write_bytes(b"\0")
        backup = Backup(src, Path(tmp, "备份"))
        archive = backup.run(datetime(2026, 3, 9, 2, 0))
        with zipfile.ZipFile(archive) as zf:
            print(zf.namelist())
        print("校验：", backup.verify(archive) or "全部一致")
