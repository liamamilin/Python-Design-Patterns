import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from examples import ch32_import_v1 as imp

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "data" / "supplier_a.csv"


class ParsePriceTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(imp.parse_price("128.00"), 12800)
        self.assertEqual(imp.parse_price(" 96.5 "), 9650)
        self.assertEqual(imp.parse_price("38"), 3800)

    def test_invalid(self):
        for text in ("-3", "0", "abc", "", "210.125", "NaN", "Infinity", "1e3x", "1e30", "1000000"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    imp.parse_price(text)

    def test_no_float_rounding_error(self):
        self.assertEqual(imp.parse_price("0.29"), 29)  # 用 float 计算 0.29 * 100 会得到 28.999999999999996


class ReadCsvTest(unittest.TestCase):
    def setUp(self):
        self.result = imp.read_csv(SAMPLE.read_text(encoding="utf-8"))

    def test_good_rows(self):
        self.assertEqual(
            self.result.products,
            [imp.Product("TE-1001", "西湖龙井 250g", 12800, 40), imp.Product("TE-1002", "碧螺春 250g", 9650, 25)],
        )

    def test_every_bad_row_is_reported_with_its_line(self):
        self.assertEqual([p.line for p in self.result.problems], [4, 5, 6, 7, 8, 9])
        self.assertIn("sku 重复", self.result.problems[2].message)

    def test_missing_column(self):
        result = imp.read_csv("sku,name,price\nA,茶,1\n")
        self.assertEqual(result.problems, [imp.Problem(1, "缺少列：stock")])
        self.assertEqual(result.products, [])

    def test_short_row_is_reported_not_crashing(self):
        result = imp.read_csv("sku,name,price,stock\nTE-1008,茶,38\nTE-1009,茶,38,5\n")
        self.assertEqual(result.problems, [imp.Problem(2, "库存必须是非负整数：''")])
        self.assertEqual([p.sku for p in result.products], ["TE-1009"])

    def test_report(self):
        rep = imp.report(self.result)
        self.assertEqual((rep["imported"], rep["rejected"], rep["stock_value_yuan"]), (2, 6, "7532.50"))


class MainTest(unittest.TestCase):
    def run_main(self, path):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = imp.main([str(path)])
        return code, json.loads(out.getvalue())

    def test_exit_code_and_output(self):
        code, rep = self.run_main(SAMPLE)
        self.assertEqual(code, 1)
        self.assertEqual(rep["imported"], 2)

    def test_excel_bom_is_handled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bom.csv"
            path.write_bytes(b"\xef\xbb\xbf" + "sku,name,price,stock\nTE-1,茶,1.00,1\n".encode("utf-8"))
            code, rep = self.run_main(path)
        self.assertEqual((code, rep["imported"]), (0, 1))

    def test_bom_without_utf8_sig_breaks_the_header(self):
        text = "﻿sku,name,price,stock\nTE-1,茶,1.00,1\n"
        self.assertEqual(imp.read_csv(text).problems, [imp.Problem(1, "缺少列：sku")])


if __name__ == "__main__":
    unittest.main()
