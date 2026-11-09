import io
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from examples import ch32_import_v1 as v1
from examples import ch33_importer as imp

DATA = Path(__file__).resolve().parent.parent / "examples" / "data"


class SameBehaviourForCsvTest(unittest.TestCase):
    def test_refactoring_keeps_the_csv_results(self):
        old = v1.read_csv((DATA / "supplier_a.csv").read_text(encoding="utf-8"))
        new = imp.import_file(DATA / "supplier_a.csv")
        self.assertEqual(new.products, old.products)
        self.assertEqual(
            [f"{p.where}：{p.message}" for p in new.problems],
            [f"第 {p.line} 行：{p.message}" for p in old.problems],
        )


class JsonTest(unittest.TestCase):
    def test_supplier_b(self):
        result = imp.import_file(DATA / "supplier_b.json")
        self.assertEqual([p.sku for p in result.products], ["YN-2001", "YN-2002"])
        self.assertEqual([p.where for p in result.problems], ["第 3 条", "第 4 条", "第 5 条"])

    def test_json_prices_never_pass_through_float(self):
        rows = imp.read_json_rows('{"items": [{"code": "YN-0001", "title": "茶", "price": 0.29, "qty": 1}]}')
        self.assertEqual(imp.validate(rows).products[0].price_cents, 29)

    def test_short_rows_same_as_first_version(self):
        text = "sku,name,price,stock\nTE-1008,茶,38\nTE-1009,茶,38,5\n"
        old = v1.read_csv(text)
        new = imp.validate(imp.read_csv_rows(text))
        self.assertEqual(new.products, old.products)
        self.assertEqual([p.message for p in new.problems], [p.message for p in old.problems])

    def test_malformed_json_is_a_format_error(self):
        for text in ('{"items": [', '{"items": [1, 2]}'):
            with self.subTest(text=text):
                with self.assertRaises(imp.FormatError):
                    imp.read_json_rows(text)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text('{"items": [', encoding="utf-8")
            self.assertEqual(imp.main([str(path)], io.StringIO()), 2)

    def test_bad_json_shape(self):
        with self.assertRaises(imp.FormatError):
            imp.read_json_rows('{"goods": []}')


class RulesTest(unittest.TestCase):
    def test_independent_rules_report_together(self):
        rows = [("第 2 行", {"sku": "bad", "name": "茶", "price": "-1", "stock": "1"})]
        message = imp.validate(rows).problems[0].message
        self.assertEqual(message, "sku 格式应为两个大写字母加四位数字：bad；价格必须大于 0：-1")

    def test_a_new_rule_is_one_more_function(self):
        def no_test_items(row):
            return "测试商品不能导入" if "测试" in row["name"] else None

        rows = [("第 2 行", {"sku": "TE-0001", "name": "测试茶", "price": "1", "stock": "1"})]
        self.assertEqual(imp.validate(rows, [*imp.RULES, no_test_items]).problems[0].message, "测试商品不能导入")


class SinkTest(unittest.TestCase):
    def test_sqlite_upsert(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "shop.db"
            sink = imp.SqliteSink(db)
            sink.write(imp.import_file(DATA / "supplier_b.json"))
            again = imp.Result(products=[v1.Product("YN-2001", "滇红金芽 200g", 9000, 10)])
            sink.write(again)
            with closing(sqlite3.connect(db)) as conn:
                rows = conn.execute("SELECT sku, price_cents, stock FROM products ORDER BY sku").fetchall()
        self.assertEqual(rows, [("YN-2001", 9000, 10), ("YN-2002", 15680, 12)])

    def test_main_with_both_sinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = io.StringIO()
            code = imp.main([str(DATA / "supplier_b.json"), "--db", str(Path(tmp) / "shop.db")], out)
            self.assertEqual(code, 1)
            self.assertIn('"imported": 2', out.getvalue())

    def test_unsupported_file_type(self):
        with self.assertRaises(imp.FormatError):
            imp.import_file(Path("价目表.xlsx"))


if __name__ == "__main__":
    unittest.main()
