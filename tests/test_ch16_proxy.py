import tempfile
import unittest
from pathlib import Path

from examples import ch16_course_v1 as v1
from examples import ch16_proxy as px
from examples import ch16_pythonic as py
from examples.ch16_course_v1 import RealLesson, make_demo_course, outline

TITLES = ["01-第1课", "02-第2课", "03-第3课", "04-第4课", "05-第5课"]


class CourseTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        make_demo_course(self.folder)
        RealLesson.loads = 0


class FirstVersionTest(CourseTest):
    def test_outline_reads_every_file_and_paid_lessons_are_open(self):
        course = v1.open_course(self.folder)
        self.assertEqual(outline(course), TITLES)
        self.assertEqual(RealLesson.loads, 5)
        self.assertEqual(course[4].content(), "第 5 课的讲义……")  # 没有任何检查


class ProxyTest(CourseTest):
    def test_outline_reads_nothing(self):
        course = px.open_course(self.folder, user="小周", enrolled=set())
        self.assertEqual(outline(course), TITLES)
        self.assertEqual(RealLesson.loads, 0)

    def test_loads_once_on_first_use(self):
        course = px.open_course(self.folder, user="小林", enrolled={"小林"})
        self.assertEqual(course[2].content(), "第 3 课的讲义……")
        course[2].content()
        self.assertEqual(RealLesson.loads, 1)

    def test_free_trial_and_paid_lessons(self):
        course = px.open_course(self.folder, user="小周", enrolled={"小林"})
        self.assertEqual(course[0].content(), "第 1 课的讲义……")
        with self.assertRaises(PermissionError):
            course[1].content()
        self.assertEqual(RealLesson.loads, 1)  # 被拒绝时不会去读文件

    def test_proxies_stack(self):
        lesson = px.open_course(self.folder, user="小林", enrolled={"小林"})[1]
        self.assertIsInstance(lesson, px.PaidLesson)
        self.assertIsInstance(lesson.inner, px.LazyLesson)


class PythonicTest(CourseTest):
    def test_cached_property_reads_once(self):
        path = self.folder / "01-第1课.txt"
        lesson = py.Lesson("入门", path)
        self.assertNotIn("text", vars(lesson))
        self.assertEqual(lesson.text, "第 1 课的讲义……")
        path.write_text("已修改", "utf-8")
        self.assertEqual(lesson.text, "第 1 课的讲义……")  # 缓存的值，不会再读

    def test_generic_proxy_pitfalls(self):
        real = RealLesson("入门", self.folder / "01-第1课.txt")
        proxy = py.AnyProxy(real)
        self.assertEqual(proxy.content(), real.content())  # 普通方法能转发
        self.assertEqual(str(real), "《入门》")
        self.assertNotEqual(str(proxy), "《入门》")  # 特殊方法不经过 __getattr__
        self.assertFalse(isinstance(proxy, RealLesson))


if __name__ == "__main__":
    unittest.main()
