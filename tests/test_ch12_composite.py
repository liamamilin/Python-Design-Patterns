import unittest

from examples import ch12_budget_v1 as v1
from examples import ch12_composite as c
from examples import ch12_pythonic as py

REPORT = """新房装修 36,000
  设计费 5,000
  客厅 14,500
    地板 8,000
    沙发 6,500
  厨房 16,500
    橱柜 12,000
    电器 4,500（打包 9 折）
      油烟机 3,000
      灶具 2,000"""


class FixedDepthTest(unittest.TestCase):
    def test_two_levels_work(self):
        self.assertEqual(v1.total(v1.budget), 31500)

    def test_mixed_depth_breaks(self):
        with self.assertRaises(AttributeError):  # 最外层出现了一个数字
            v1.total(v1.budget_later)
        with self.assertRaises(TypeError):  # 房间里又套了一层字典
            v1.total({"厨房": {"橱柜": 12000, "电器": {"油烟机": 3000}}})


class CompositeTest(unittest.TestCase):
    def test_report_at_any_depth(self):
        self.assertEqual("\n".join(c.new_home().lines()), REPORT)

    def test_leaf_and_group_are_used_the_same_way(self):
        home = c.new_home()
        self.assertEqual([child.cost() for child in home.children], [5000, 14500, 16500])

    def test_expensive_items(self):
        self.assertEqual(c.expensive(c.new_home(), 6000), ["地板", "沙发", "橱柜"])

    def test_no_cycles(self):
        kitchen = c.Group("厨房")
        appliances = c.Group("电器")
        kitchen.add(appliances)
        with self.assertRaises(ValueError):
            appliances.add(kitchen)
        with self.assertRaises(ValueError):
            kitchen.add(kitchen)


class RecursiveFunctionTest(unittest.TestCase):
    def test_any_depth_without_classes(self):
        self.assertEqual(py.total(v1.budget_later), 36500)  # 没有打折这个概念
        self.assertEqual(py.lines("新房装修", v1.budget_later)[5], "  厨房 17,000")


if __name__ == "__main__":
    unittest.main()
