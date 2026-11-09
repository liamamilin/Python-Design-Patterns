import contextlib
import io
import unittest

from examples import ch13_decorator as d
from examples import ch13_export_v1 as v1
from examples import ch13_pythonic as py
from examples.ch13_export_v1 import messages

SAFE = ["客户：请回电 138****5…", "客服：好的，稍后联系您"]
LEAK = ["客户：请回电 13812345…", "客服：好的，稍后联系您"]


class FlagsVersionTest(unittest.TestCase):
    def test_mask_only(self):
        self.assertEqual(v1.export(messages, mask=True)[0], "客户：请回电 138****5678 谢谢")

    def test_truncating_first_leaks_digits(self):
        self.assertEqual(v1.export(messages, mask=True, limit=16), LEAK)


class DecoratorTest(unittest.TestCase):
    def run_export(self, make):
        dest = d.ListWriter()
        d.export(messages, make(dest))
        return dest.lines

    def test_outer_layer_runs_first(self):
        self.assertEqual(self.run_export(lambda w: d.Masking(d.Truncating(w, 16))), SAFE)
        self.assertEqual(self.run_export(lambda w: d.Truncating(d.Masking(w), 16)), LEAK)

    def test_build_writer_puts_masking_outside(self):
        self.assertEqual(self.run_export(lambda w: d.build_writer(w, limit=16)), SAFE)

    def test_layers_stack_freely(self):
        dest = d.ListWriter()
        counter = d.Counting(dest)
        d.export(messages, d.Masking(counter))
        self.assertEqual(counter.count, 2)
        self.assertEqual(dest.lines[0], "客户：请回电 138****5678 谢谢")

    def test_each_layer_alone(self):
        dest = d.ListWriter()
        d.Truncating(dest, 5).write("一二三四五六")
        self.assertEqual(dest.lines, ["一二三四…"])


class FunctionDecoratorTest(unittest.TestCase):
    def test_same_order_rule(self):
        lines: list[str] = []
        py.export(messages, py.masking(py.truncating(16)(lines.append)))
        self.assertEqual(lines, SAFE)

    def test_at_syntax_applies_once_at_definition(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            py.print_line("电话 13812345678")
        self.assertEqual(buf.getvalue(), "电话 138****5678\n")
        self.assertEqual(py.print_line.__name__, "print_line")  # functools.wraps 保留了名字


if __name__ == "__main__":
    unittest.main()
