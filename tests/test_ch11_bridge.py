import unittest

from examples import ch11_bridge as br
from examples import ch11_charts_v1 as v1
from examples import ch11_pythonic as py
from examples.ch11_charts_v1 import rainfall

BARS = "1月 █████\n2月 █████████████\n3月\n4月 ████████████████████"
COLUMNS = "\n".join([
    "         ██",
    "         ██",
    "   ██    ██",
    "   ██    ██",
    "██ ██    ██",
    "1月 2月 3月 4月",
])
ZEROS = {"1月": 0, "2月": 0}


class CombinationClassesTest(unittest.TestCase):
    def test_fix_landed_in_only_one_combination(self):
        self.assertEqual(v1.TextBarChart(23).draw(rainfall), BARS)
        self.assertEqual(v1.TextBarChart(23).draw(ZEROS), "1月\n2月")
        with self.assertRaises(ZeroDivisionError):
            v1.SvgBarChart(23).draw(ZEROS)


class BridgeTest(unittest.TestCase):
    def test_bar_chart_on_text(self):
        self.assertEqual(br.BarChart(br.TextCanvas(23, 4)).draw(rainfall), BARS)

    def test_column_chart_on_text(self):
        self.assertEqual(br.ColumnChart(br.TextCanvas(12, 6)).draw(rainfall), COLUMNS)

    def test_bar_chart_on_svg_has_same_layout(self):
        svg = br.BarChart(br.SvgCanvas(23, 4)).draw(rainfall)
        self.assertTrue(svg.startswith('<svg xmlns="http://www.w3.org/2000/svg" width="230" height="40">'))
        self.assertIn('<rect x="30" y="0" width="50" height="10"/>', svg)
        self.assertIn('<rect x="30" y="30" width="200" height="10"/>', svg)
        self.assertEqual(svg.count("<rect"), 3)  # 3 月为 0，不画

    def test_zero_data_works_for_every_combination(self):
        for chart in (br.BarChart, br.ColumnChart):
            for canvas in (br.TextCanvas, br.SvgCanvas):
                with self.subTest(chart=chart.__name__, canvas=canvas.__name__):
                    chart(canvas(12, 6)).draw(ZEROS)


class FunctionTest(unittest.TestCase):
    def test_function_gives_the_same_output(self):
        self.assertEqual(py.draw_bars(rainfall, br.TextCanvas(23, 4)), BARS)
        self.assertEqual(
            py.draw_bars(rainfall, br.SvgCanvas(23, 4)),
            br.BarChart(br.SvgCanvas(23, 4)).draw(rainfall),
        )


if __name__ == "__main__":
    unittest.main()
