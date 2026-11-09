import unittest

from examples import ch28_classes as cl
from examples import ch28_functions as fn
from examples.ch28_classes import Record

LINES = ["add 瑞幸拿铁 1600", "add 地铁 400", "add 买显示器 129900", "add 理发 3000"]
CATEGORIES = ["饮品", "交通", "大额支出", "其他"]


class SameBehaviourTest(unittest.TestCase):
    def test_both_versions_agree(self):
        book_c, book_f = [], []
        factory = cl.CommandFactory()
        for line in LINES:
            name, *args = line.split()
            factory.create(name).execute(book_c, args)
            fn.run(book_f, line)
        self.assertEqual(book_c, book_f)
        self.assertEqual([cl.Classifier(cl.RULES).classify(r) for r in book_c], CATEGORIES)
        self.assertEqual([fn.classify(r, fn.RULES) for r in book_f], CATEGORIES)
        self.assertEqual(fn.run(book_f, "total"), "合计 1349.00 元")

    def test_unknown_command(self):
        with self.assertRaises(ValueError):
            fn.run([], "delete 1")
        with self.assertRaises(ValueError):
            cl.CommandFactory().create("delete")


class CallableObjectTest(unittest.TestCase):
    def test_object_with_state_fits_the_same_slot(self):
        drinks = fn.CountingRule(fn.keyword("拿铁", "奶茶", category="饮品"))
        rules = [drinks, *fn.RULES]
        records = [Record("拿铁", 1600), Record("奶茶", 1200), Record("地铁", 400)]
        self.assertEqual([fn.classify(r, rules) for r in records], ["饮品", "饮品", "交通"])
        self.assertEqual(drinks.hits, 2)


class LateBindingTest(unittest.TestCase):
    def test_lambdas_in_a_loop_share_the_last_value(self):
        mapping = {"地铁": "交通", "拿铁": "饮品"}
        wrong = fn.keyword_rules_wrong(mapping)
        self.assertEqual(fn.classify(Record("地铁", 400), wrong), "其他")
        self.assertEqual(fn.classify(Record("拿铁", 1600), wrong), "饮品")
        right = fn.keyword_rules(mapping)
        self.assertEqual(fn.classify(Record("地铁", 400), right), "交通")


if __name__ == "__main__":
    unittest.main()
