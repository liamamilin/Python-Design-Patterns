import unittest

from examples import ch05_factory_method as fm
from examples import ch05_factory_method_v1 as v1
from examples import ch05_pythonic as py
from examples import ch05_simple_factory as sf
from examples.ch05_factory_method_v1 import Task, tasks

WEEKLY = "# 周会纪要\n- [x] 登录页改版\n- [ ] 修复导出乱码\n- [x] 接入短信验证码"
CLIENT = "<h1>项目进度</h1>\n<li>✔ 登录页改版</li>\n<li>✔ 接入短信验证码</li>"
RELEASE = "发布说明\n========\n* 登录页改版\n* 接入短信验证码"
DONE = [t for t in tasks if t.done]


class FirstVersionTest(unittest.TestCase):
    def test_markdown_and_html(self):
        self.assertEqual(v1.render("周会纪要", tasks), WEEKLY)
        self.assertEqual(v1.render("项目进度", DONE, "html"), CLIENT)

    def test_unknown_format(self):
        with self.assertRaises(ValueError):
            v1.render("x", tasks, "pdf")

    def test_html_is_escaped(self):
        self.assertIn("&lt;b&gt;", v1.render("t", [Task("<b>", True)], "html"))


class SimpleFactoryTest(unittest.TestCase):
    def test_same_output_as_first_version(self):
        self.assertEqual(sf.render("周会纪要", tasks, "markdown"), WEEKLY)
        self.assertEqual(sf.render("项目进度", DONE, "html"), CLIENT)

    def test_factory_returns_new_objects(self):
        self.assertIsInstance(sf.make_renderer("html"), sf.HtmlRenderer)
        self.assertIsNot(sf.make_renderer("html"), sf.make_renderer("html"))
        with self.assertRaises(ValueError):
            sf.make_renderer("pdf")


class FactoryMethodTest(unittest.TestCase):
    def test_each_document_creates_its_own_renderer(self):
        self.assertEqual(fm.WeeklyNotes().build(tasks), WEEKLY)
        self.assertEqual(fm.ClientReport().build(tasks), CLIENT)

    def test_new_document_type_without_touching_the_base_class(self):
        self.assertEqual(fm.ReleaseNotes().build(tasks), RELEASE)

    def test_base_class_cannot_be_used_directly(self):
        with self.assertRaises(TypeError):
            fm.Document()


class PythonicTest(unittest.TestCase):
    def test_pass_the_class_as_the_factory(self):
        self.assertEqual(py.weekly_notes(tasks), WEEKLY)
        self.assertEqual(py.client_report(tasks), CLIENT)

    def test_any_combination_without_new_classes(self):
        out = py.build_document("项目进度", tasks, sf.MarkdownRenderer, keep=lambda t: t.done)
        self.assertEqual(out, "# 项目进度\n- [x] 登录页改版\n- [x] 接入短信验证码")


if __name__ == "__main__":
    unittest.main()
