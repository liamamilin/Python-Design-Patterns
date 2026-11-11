import unittest

from examples.ch03_objects import (
    OwnWordsCensor,
    counting_through_a_pipeline,
    equal_but_not_same,
    make_step,
    remember,
    remember_bad,
    separate_word_lists,
    shared_word_list,
)
from examples.ch03_tools import Censor, Lowercase, Pipeline, strip_spaces


class AliasingTest(unittest.TestCase):
    def test_two_censors_share_one_list(self):
        forum, shop = shared_word_list()
        self.assertIs(forum.words, shop.words)
        self.assertEqual(shop("咖啡难喝"), "咖啡**")

    def test_own_copy_keeps_censors_apart(self):
        forum, shop = separate_word_lists()
        self.assertEqual(forum.words, ("垃圾", "难喝"))
        self.assertEqual(shop.words, ("垃圾",))
        self.assertEqual(shop("咖啡难喝"), "咖啡难喝")

    def test_tuple_cannot_be_changed_in_place(self):
        with self.assertRaises(AttributeError):
            OwnWordsCensor(["垃圾"]).words.append("难喝")

    def test_caller_list_changes_do_not_leak_in(self):
        words = ["垃圾"]
        censor = OwnWordsCensor(words)
        words.append("难喝")
        self.assertEqual(censor.words, ("垃圾",))

    def test_pipeline_copies_its_step_list(self):
        steps = [strip_spaces]
        pipeline = Pipeline(*steps)
        steps.append(Lowercase())
        self.assertEqual(pipeline("  ABC  "), "ABC")


class IdentityTest(unittest.TestCase):
    def test_equal_but_not_same(self):
        self.assertEqual(equal_but_not_same(), (True, False))

    def test_state_seen_through_another_name(self):
        self.assertEqual(counting_through_a_pipeline(), 2)


class DefaultArgumentTest(unittest.TestCase):
    def test_mutable_default_is_shared_between_calls(self):
        first = remember_bad("第一条")
        second = remember_bad("第二条")
        self.assertIs(first, second)
        self.assertEqual(second[-2:], ["第一条", "第二条"])

    def test_none_default_gives_a_fresh_list(self):
        self.assertEqual(remember("第一条"), ["第一条"])
        self.assertEqual(remember("第二条"), ["第二条"])


class ClassesAreObjectsTest(unittest.TestCase):
    def test_class_in_a_dict_makes_new_objects(self):
        self.assertEqual(make_step("lower")("ABC"), "abc")
        a = make_step("censor", ["垃圾"])
        b = make_step("censor", ["垃圾"])
        self.assertIsInstance(a, Censor)
        self.assertIsNot(a, b)


if __name__ == "__main__":
    unittest.main()
