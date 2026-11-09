import unittest
from functools import partial

from examples.ch03_tools import (
    Censor,
    CensoringCleaner,
    Cleaner,
    Forgetful,
    Lowercase,
    Pipeline,
    Step,
    TextStep,
    apply_all,
    basic_steps,
    comment,
    for_english,
    only_censor,
    run_steps,
    strip_spaces,
    truncate,
)


class FunctionTest(unittest.TestCase):
    def test_strip_spaces(self):
        self.assertEqual(strip_spaces(comment), "这家店的 咖啡 太难喝了，简直是垃圾！！")

    def test_truncate_keeps_short_text_and_marks_cut(self):
        self.assertEqual(truncate("短评", 12), "短评")
        self.assertEqual(truncate("一二三四五六七八九十", 5), "一二三四…")

    def test_functions_in_a_list(self):
        self.assertEqual(apply_all(comment, basic_steps), "这家店的 咖啡 太难喝…")


class ClassWithStateTest(unittest.TestCase):
    def test_censor_remembers_how_many_it_replaced(self):
        censor = Censor(["垃圾"])
        self.assertEqual(censor("垃圾垃圾"), "****")
        self.assertEqual(censor("还是垃圾"), "还是**")
        self.assertEqual(censor.replaced, 3)


class InheritanceAndCompositionTest(unittest.TestCase):
    def test_inheritance(self):
        self.assertEqual(Cleaner(12).clean(comment), "这家店的 咖啡 太难喝…")
        self.assertEqual(CensoringCleaner(20, ["垃圾"]).clean(comment), "这家店的 咖啡 太难喝了，简直是**！！")

    def test_composition_builds_any_combination(self):
        censor = Censor(["垃圾"])
        self.assertEqual(Pipeline(strip_spaces, censor)(comment), "这家店的 咖啡 太难喝了，简直是**！！")
        self.assertEqual(censor.replaced, 1)
        self.assertEqual(for_english("  GREAT 咖啡，垃圾服务  "), "great 咖啡，**服务")
        self.assertEqual(only_censor(comment), "这家店的 咖啡 太难喝了，简直是**！！")


class AbstractBaseClassTest(unittest.TestCase):
    def test_missing_method_fails_at_creation(self):
        with self.assertRaises(TypeError):
            Forgetful()

    def test_abc_requires_explicit_inheritance(self):
        self.assertTrue(isinstance(Lowercase(), Step))
        self.assertFalse(isinstance(strip_spaces, Step))


class ProtocolTest(unittest.TestCase):
    def test_functions_and_objects_both_fit(self):
        self.assertTrue(isinstance(strip_spaces, TextStep))
        self.assertTrue(isinstance(Censor([]), TextStep))
        self.assertFalse(isinstance("abc", TextStep))
        self.assertEqual(run_steps("  ABC  ", [strip_spaces, Lowercase()]), "abc")

    def test_runtime_check_only_looks_for_the_method(self):
        # print 也能“通过”运行时检查：它只看有没有 __call__，不看参数和返回值
        self.assertTrue(isinstance(print, TextStep))


if __name__ == "__main__":
    unittest.main()
