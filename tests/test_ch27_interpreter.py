import unittest

from examples import ch27_interpreter as it
from examples import ch27_pythonic as py
from examples import ch27_rules_v1 as v1
from examples.ch27_rules_v1 import students

RULE = '年级 >= 2 and (学院 == "物理" or 社团 == "天文社")'
HOSTILE = [
    '__import__("os").getpid() > 0',
    '().__class__',
    '年级 >= 2 and open("x")',
    '[x for x in 年级]',
]


def names(pred):
    return [s["姓名"] for s in students if pred(s)]


class EvalTest(unittest.TestCase):
    def test_eval_runs_arbitrary_code(self):
        self.assertEqual(names(lambda s: v1.eligible(RULE, s)), ["周晴", "高远"])
        self.assertTrue(v1.eligible('__import__("os").getpid() > 0', students[0]))


class InterpreterTest(unittest.TestCase):
    def test_same_answers(self):
        rule = it.compile_rule(RULE)
        self.assertEqual(names(rule.evaluate), ["周晴", "高远"])

    def test_tree_shape(self):
        rule = it.compile_rule('not 年级 < 2 or 社团 == "天文社"')
        self.assertIsInstance(rule, it.Or)
        self.assertIsInstance(rule.left, it.Not)

    def test_precedence_and_binds_tighter_than_or(self):
        rule = it.compile_rule('学院 == "化学" or 年级 >= 3 and 社团 == "无"')
        self.assertEqual(names(rule.evaluate), ["林木", "高远"])

    def test_hostile_rules_are_rejected(self):
        for text in HOSTILE:
            with self.subTest(text=text):
                with self.assertRaises(it.RuleError):
                    it.compile_rule(text)

    def test_friendly_errors(self):
        with self.assertRaises(it.RuleError):
            it.compile_rule("年级 >=")
        with self.assertRaises(it.RuleError):
            it.compile_rule("(年级 >= 2")
        with self.assertRaises(it.RuleError):
            it.compile_rule("专业 == \"天文\"").evaluate(students[0])
        with self.assertRaises(it.RuleError):
            it.compile_rule('年级 > "二"').evaluate(students[0])


class AstWhitelistTest(unittest.TestCase):
    def test_same_answers(self):
        tree = py.check(RULE)
        self.assertEqual(names(lambda s: py.evaluate(tree, s)), ["周晴", "高远"])

    def test_hostile_rules_are_rejected(self):
        for text in HOSTILE:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    py.check(text)

    def test_chained_comparison_is_not_supported(self):
        with self.assertRaises(ValueError):
            py.evaluate(py.check("1 < 年级 < 3"), students[0])


if __name__ == "__main__":
    unittest.main()
