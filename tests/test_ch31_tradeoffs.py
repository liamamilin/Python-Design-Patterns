import itertools
import unittest
from datetime import date

from examples import ch31_points as p

ORDERS = [
    p.Order(12800, date(2026, 3, 11), "金卡", 3),  # 周三、金卡、生日月
    p.Order(12800, date(2026, 3, 12), "普通", 7),  # 什么都不沾
    p.Order(5000, date(2026, 7, 15), "普通", 7),  # 周三、生日月
    p.Order(9999, date(2026, 1, 2), "金卡", 5),  # 只有金卡
]


class SameRulesTest(unittest.TestCase):
    def test_both_versions_agree(self):
        self.assertEqual([p.points_simple(o) for o in ORDERS], [484, 128, 200, 148])
        self.assertEqual([p.points_rules(o) for o in ORDERS], [484, 128, 200, 148])


class OrderDependenceTest(unittest.TestCase):
    def test_rule_order_changes_the_result(self):
        order = ORDERS[0]
        results = {
            tuple(r.__name__ for r in perm): p.points_rules(order, list(perm))
            for perm in itertools.permutations(p.RULES)
        }
        self.assertEqual(sorted(set(results.values())), [484, 534, 584, 684])  # 六种排列，四种不同的积分
        self.assertEqual(results[("birthday_bonus", "gold_card", "wednesday_double")], 684)


class ChangeTest(unittest.TestCase):
    def test_adding_a_rule_is_one_line_in_the_list(self):
        def new_member(points, o):
            return points + 50

        rules = [*p.RULES, new_member]
        self.assertEqual(p.points_rules(ORDERS[1], rules), 178)

    def test_turning_a_rule_off(self):
        rules = [r for r in p.RULES if r is not p.wednesday_double]
        self.assertEqual(p.points_rules(ORDERS[0], rules), 292)


if __name__ == "__main__":
    unittest.main()
