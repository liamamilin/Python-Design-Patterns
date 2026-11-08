import copy
import io
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime

from examples.ch01_receipt import (
    MemberCard,
    OrderLine,
    format_yuan,
    order,
    order_total,
    print_receipt,
    total_of,
)


class OrderTotalTest(unittest.TestCase):
    def test_total_in_cents_and_formatted(self):
        self.assertEqual(order_total(order), 7100)
        self.assertEqual(format_yuan(order_total(order)), "¥71.00")

    def test_total_does_not_modify_the_order(self):
        before = copy.deepcopy(order)
        order_total(order)
        self.assertEqual(order, before)

    def test_float_yuan_would_be_inexact(self):
        # 正文用这个事实说明为什么金额用“分”保存
        self.assertNotEqual(0.1 + 0.2, 0.3)
        self.assertEqual(10 + 20, 30)


class MemberCardTest(unittest.TestCase):
    def test_same_call_gives_different_results_because_of_state(self):
        card = MemberCard()
        self.assertEqual(card.add_purchase(7100), 7)
        self.assertEqual(card.add_purchase(7100), 14)


class PrintReceiptTest(unittest.TestCase):
    def test_time_and_output_are_passed_in(self):
        out = io.StringIO()
        print_receipt(order, datetime(2026, 3, 1, 9, 30), out)
        self.assertEqual(
            out.getvalue(),
            "时间：2026-03-01 09:30\n"
            "拿铁 x2  ¥56.00\n"
            "可颂 x1  ¥15.00\n"
            "合计：¥71.00\n",
        )


class OrderLineTest(unittest.TestCase):
    def test_dataclass_gives_same_total(self):
        lines = [OrderLine("拿铁", 2800, 2), OrderLine("可颂", 1500, 1)]
        self.assertEqual(total_of(lines), order_total(order))

    def test_typo_in_field_name_fails_loudly(self):
        with self.assertRaises(TypeError):
            OrderLine(name="拿铁", prcie=2800, qty=2)

    def test_frozen_line_cannot_be_changed(self):
        line = OrderLine("拿铁", 2800, 2)
        with self.assertRaises(FrozenInstanceError):
            line.qty = 3


if __name__ == "__main__":
    unittest.main()
