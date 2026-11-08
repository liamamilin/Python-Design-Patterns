import dataclasses
import unittest

from examples import ch08_copy_trap as trap
from examples import ch08_prototype as proto
from examples import ch08_pythonic as py


class ShallowCopyTrapTest(unittest.TestCase):
    def test_replace_shares_the_inner_lists(self):
        template, chen, wang = trap.show_the_trap()
        self.assertEqual(chen.title, "小陈的计划")
        self.assertEqual(template.title, "新手计划")
        # 只改了小陈，小王和模板也变成了 4 组
        self.assertEqual(wang.days["周一"][0].sets, 4)
        self.assertEqual(template.days["周一"][0].sets, 4)
        self.assertIs(chen.days, template.days)

    def test_copy_copy_has_the_same_problem(self):
        template = trap.beginner_template()
        chen = trap.plan_for_shallow_copy(template, "小陈")
        chen.days["周一"].pop(0)  # 小陈膝盖不好，去掉深蹲
        self.assertEqual([e.name for e in template.days["周一"]], ["俯卧撑"])


class PrototypeTest(unittest.TestCase):
    def setUp(self):
        self.lib = proto.make_library()
        self.template = proto.beginner_template(self.lib)

    def test_clone_is_independent(self):
        chen = self.template.clone("小陈的计划")
        chen.days["周一"][0].sets = 4
        chen.days["周四"].clear()
        self.assertEqual(self.template.days["周一"][0].sets, 3)
        self.assertEqual(len(self.template.days["周四"]), 1)
        self.assertEqual(self.template.title, "新手计划")

    def test_movements_stay_shared(self):
        chen = self.template.clone("小陈的计划")
        self.assertIs(chen.days["周一"][0].movement, self.lib["深蹲"])
        self.lib["深蹲"].video = "videos/squat-v2.mp4"
        self.assertEqual(chen.days["周一"][0].movement.video, "videos/squat-v2.mp4")

    def test_shelf_keeps_its_own_copy(self):
        shelf = proto.TemplateShelf()
        shelf.save("新手", self.template)
        self.template.days["周一"][0].sets = 99  # 教练继续改草稿
        plan = shelf.new_plan("新手", "小王的计划")
        self.assertEqual(plan.days["周一"][0].sets, 3)
        self.assertEqual(plan.title, "小王的计划")
        self.assertEqual(shelf.names(), ["新手"])

    def test_unknown_template(self):
        with self.assertRaises(KeyError):
            proto.TemplateShelf().new_plan("减脂", "x")


class FrozenDataTest(unittest.TestCase):
    def test_change_returns_a_new_plan(self):
        chen = py.change_sets(py.BEGINNER, "周一", "深蹲", 4)
        self.assertEqual(chen.days[0][1][0].sets, 4)
        self.assertEqual(py.BEGINNER.days[0][1][0].sets, 3)
        # 没改动的动作对象直接共享，因为它们不会被修改
        self.assertIs(chen.days[0][1][1], py.BEGINNER.days[0][1][1])
        self.assertIs(chen.days[1][1][0], py.BEGINNER.days[1][1][0])

    def test_cannot_modify_in_place(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            py.BEGINNER.days[0][1][0].sets = 4  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
