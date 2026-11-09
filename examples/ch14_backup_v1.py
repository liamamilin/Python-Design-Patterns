"""第 14 章：第一版。夜间备份脚本直接调用 zipfile、hashlib、json 等模块。"""
from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path


def nightly_backup(source: Path, dest: Path, now: datetime) -> Path:
    archive = dest / f"backup-{now:%Y%m%d-%H%M%S}.zip"
    manifest = {}
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                manifest[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                zf.write(path)  # 忘了 arcname：压缩包里存的是完整路径
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
    return archive


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp, "文档"), Path(tmp, "备份")
        (src / "合同").mkdir(parents=True)
        dst.mkdir()
        (src / "合同" / "租房.txt").write_text("月租 5800", "utf-8")
        with zipfile.ZipFile(nightly_backup(src, dst, datetime(2026, 3, 9, 2, 0))) as zf:
            print(zf.namelist())
