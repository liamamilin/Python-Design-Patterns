import unittest
from pathlib import Path

from examples import ch33_importer as functional
from examples import ch34_class_based as classes

DATA = Path(__file__).resolve().parent.parent / "examples" / "data"


class TwoDesignsTest(unittest.TestCase):
    def test_same_results_for_every_sample(self):
        for name in ("supplier_a.csv", "supplier_b.json"):
            with self.subTest(file=name):
                self.assertEqual(classes.import_file(DATA / name), functional.import_file(DATA / name))

    def test_same_errors_for_unsupported_files(self):
        for module in (functional, classes):
            with self.assertRaises(functional.FormatError):
                module.import_file(Path("价目表.xlsx"))

    def test_supplier_specific_rule_in_both_designs(self):
        path = DATA / "supplier_b.json"
        by_class = classes.YunlingImporter().run(path, [])
        rows = functional.read_json_rows(path.read_text(encoding="utf-8"))
        by_function = functional.validate(rows, [*functional.RULES, classes.has_weight])
        self.assertEqual(by_class, by_function)
        self.assertIn("商品名缺少克重", by_class.problems[1].message)


if __name__ == "__main__":
    unittest.main()
