import json
import tempfile
import unittest
import zipfile
from datetime import datetime
from pathlib import Path

from examples import ch14_backup_v1 as v1
from examples import ch14_facade as f
from examples import ch14_pythonic as py

NIGHT = datetime(2026, 3, 9, 2, 0)


class FolderTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.src = self.root / "文档"
        for folder in ("合同", "照片"):
            (self.src / folder).mkdir(parents=True)
            (self.src / folder / "说明.txt").write_text(f"{folder}的说明", "utf-8")
        (self.src / "合同" / "租房.txt").write_text("月租 5800", "utf-8")
        (self.src / ".DS_Store").write_bytes(b"\0")
        self.dest = self.root / "备份"


class FirstVersionTest(FolderTest):
    def test_full_paths_and_name_collisions(self):
        self.dest.mkdir()
        with zipfile.ZipFile(v1.nightly_backup(self.src, self.dest, NIGHT)) as zf:
            names = zf.namelist()
            manifest = json.loads(zf.read("manifest.json"))
        self.assertNotIn("合同/租房.txt", names)
        self.assertTrue(any(n.endswith("文档/合同/租房.txt") and len(n) > len("文档/合同/租房.txt") for n in names))
        self.assertIn(".DS_Store", manifest)
        # 两个“说明.txt”在清单里只剩一条
        self.assertEqual(sum(1 for k in manifest if k == "说明.txt"), 1)
        self.assertEqual(len(manifest), 3)


class FacadeTest(FolderTest):
    def test_one_call_does_everything(self):
        backup = f.Backup(self.src, self.dest)
        archive = backup.run(NIGHT)
        self.assertEqual(archive.name, "backup-20260309-020000.zip")
        with zipfile.ZipFile(archive) as zf:
            self.assertEqual(
                sorted(zf.namelist()),
                ["manifest.json", "合同/租房.txt", "合同/说明.txt", "照片/说明.txt"],
            )
        self.assertEqual(backup.verify(archive), [])

    def test_keeps_only_the_latest(self):
        backup = f.Backup(self.src, self.dest, keep=3)
        for day in range(1, 6):
            backup.run(datetime(2026, 3, day, 2, 0))
        self.assertEqual(
            [p.name for p in backup.archives()],
            ["backup-20260303-020000.zip", "backup-20260304-020000.zip", "backup-20260305-020000.zip"],
        )

    def test_verify_finds_a_tampered_file(self):
        backup = f.Backup(self.src, self.dest)
        archive = backup.run(NIGHT)
        tampered = self.dest / "tampered.zip"
        with zipfile.ZipFile(archive) as old, zipfile.ZipFile(tampered, "w") as new:
            for name in old.namelist():
                data = b"changed" if name == "合同/租房.txt" else old.read(name)
                new.writestr(name, data)
        self.assertEqual(backup.verify(tampered), ["内容不一致：合同/租房.txt"])

    def test_subsystem_is_still_available(self):
        archive = f.Backup(self.src, self.dest).run(NIGHT)
        with zipfile.ZipFile(archive) as zf:  # 恢复单个文件：外观没有提供，直接用 zipfile
            self.assertEqual(zf.read("合同/租房.txt").decode("utf-8"), "月租 5800")


class ModuleFunctionTest(FolderTest):
    def test_shortcuts(self):
        self.assertTrue(py.backup_folder(self.src, self.dest).name.startswith("backup-"))
        with zipfile.ZipFile(py.quick_archive(self.src, self.root)) as zf:
            self.assertIn(".DS_Store", zf.namelist())  # 一行打包，但不会替你排除系统文件
            self.assertNotIn("manifest.json", zf.namelist())


if __name__ == "__main__":
    unittest.main()
