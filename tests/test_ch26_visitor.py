import unittest
from dataclasses import dataclass

from examples import ch26_article_v1 as v1
from examples import ch26_pythonic as py
from examples import ch26_visitor as vi


class MethodsOnBlocksTest(unittest.TestCase):
    def test_forgotten_method_silently_counts_zero(self):
        self.assertEqual(sum(b.word_count() for b in v1.article), 17)  # 表格里的 7 个字没算进去


class VisitorTest(unittest.TestCase):
    def test_word_count(self):
        self.assertEqual(vi.run(vi.article, vi.WordCounter()).total, 24)

    def test_alt_checker(self):
        self.assertEqual(vi.run(vi.article, vi.AltChecker()).problems, ["图片 tent.jpg 缺少替代文字"])
        ok = [vi.Image("a.jpg", alt="帐篷搭在湖边")]
        self.assertEqual(vi.run(ok, vi.AltChecker()).problems, [])

    def test_visitor_must_handle_every_block(self):
        class HeadingsOnly(vi.Visitor):
            def visit_heading(self, b):
                pass

        with self.assertRaises(TypeError):
            HeadingsOnly()

    def test_new_operation_without_touching_blocks(self):
        class Outline(vi.Visitor):
            def __init__(self):
                self.lines = []

            def visit_heading(self, b):
                self.lines.append("  " * (b.level - 1) + b.text)

            def visit_paragraph(self, b):
                pass

            def visit_image(self, b):
                pass

            def visit_table(self, b):
                pass

        doc = [vi.Heading(1, "露营"), vi.Heading(2, "装备"), vi.Paragraph("……")]
        self.assertEqual(vi.run(doc, Outline()).lines, ["露营", "  装备"])


class DispatchTest(unittest.TestCase):
    def test_match_and_singledispatch(self):
        self.assertEqual(sum(py.word_count(b) for b in vi.article), 24)
        self.assertEqual(py.to_text(vi.article[0]), "# 春季露营指南")

    def test_unknown_block_type_is_an_error(self):
        @dataclass
        class Video:
            src: str

        with self.assertRaises(TypeError):
            py.word_count(Video("a.mp4"))
        with self.assertRaises(AssertionError):
            py.to_text(Video("a.mp4"))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
