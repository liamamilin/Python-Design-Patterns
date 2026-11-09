import tempfile
import unittest
from pathlib import Path

from examples import ch30_language as lang
from examples import ch30_rename_v1 as v1


class FolderTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)

    def make(self, *names):
        for name in names:
            (self.folder / name).write_bytes(name.encode())

    def names(self):
        return sorted(p.name for p in self.folder.iterdir())


class LoopTest(FolderTest):
    def test_failure_leaves_half_renamed_folder(self):
        self.make("IMG_0101.jpg", "IMG_0102.jpg", "西湖_002.jpg")
        with self.assertRaises(FileExistsError):
            v1.rename_all(self.folder, "西湖")
        self.assertEqual(self.names(), ["IMG_0102.jpg", "西湖_001.jpg", "西湖_002.jpg"])


class LanguageFeaturesTest(FolderTest):
    def test_rules_registered_by_decorator(self):
        self.assertEqual(sorted(lang.RULES), ["保留原名加序号", "序号"])
        self.assertIs(lang.RULES["序号"], lang.numbered)  # 登记装饰器原样返回函数

    def test_rename(self):
        self.make("IMG_0102.jpg", "IMG_0101.jpg", "说明.txt")
        self.assertEqual(lang.rename_folder(self.folder, "序号", "西湖_"), ["西湖_001.jpg", "西湖_002.jpg"])
        self.assertEqual(self.names(), ["西湖_001.jpg", "西湖_002.jpg", "说明.txt"])
        self.assertEqual((self.folder / "西湖_001.jpg").read_bytes(), b"IMG_0101.jpg")

    def test_failure_rolls_everything_back(self):
        self.make("IMG_0101.jpg", "IMG_0102.jpg", "西湖_002.jpg")
        with self.assertRaises(FileExistsError):
            lang.rename_folder(self.folder, "序号", "西湖_")
        self.assertEqual(self.names(), ["IMG_0101.jpg", "IMG_0102.jpg", "西湖_002.jpg"])

    def test_class_based_context_manager_behaves_the_same(self):
        self.make("a.jpg", "b.jpg")
        with self.assertRaises(RuntimeError):
            with lang.AllOrNothing() as tx:
                tx.rename(self.folder / "a.jpg", self.folder / "x.jpg")
                raise RuntimeError("中途出错")
        self.assertEqual(self.names(), ["a.jpg", "b.jpg"])

    def test_plan_is_lazy(self):
        seen = []

        def spy():
            for name in ("1.jpg", "2.jpg", "3.jpg"):
                seen.append(name)
                yield self.folder / name

        first = next(lang.plan(spy(), lang.numbered))
        self.assertEqual(first[1].name, "001.jpg")
        self.assertEqual(seen, ["1.jpg"])  # 只取了需要的那一个


if __name__ == "__main__":
    unittest.main()
