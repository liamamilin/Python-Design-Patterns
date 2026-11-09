import unittest

from examples import ch19_command as c
from examples import ch19_pythonic as py
from examples import ch19_stock_v1 as v1


class PlainFunctionsTest(unittest.TestCase):
    def test_resent_request_is_applied_twice(self):
        inv = {"螺丝M4": 100}
        v1.stock_out(inv, "螺丝M4", 30)
        v1.stock_out(inv, "螺丝M4", 30)
        self.assertEqual(inv, {"螺丝M4": 40})


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.ledger = c.Ledger({"螺丝M4": 100})

    def test_same_id_applies_once(self):
        out = c.StockOut("op-17", "螺丝M4", 30)
        self.assertTrue(self.ledger.run(out))
        self.assertFalse(self.ledger.run(out))  # 重试：不会再扣一次
        self.assertEqual(self.ledger.inventory["螺丝M4"], 70)

    def test_undo_in_reverse_order(self):
        self.ledger.run(c.StockIn("op-1", "螺丝M4", 50))
        self.ledger.run(c.StockOut("op-2", "螺丝M4", 20))
        self.ledger.undo()
        self.assertEqual(self.ledger.inventory["螺丝M4"], 150)
        self.ledger.undo()
        self.assertEqual(self.ledger.inventory["螺丝M4"], 100)
        self.assertIsNone(self.ledger.undo())

    def test_recount_remembers_previous_value(self):
        self.ledger.run(c.SetCount("op-3", "螺丝M4", 65))
        self.assertEqual(self.ledger.inventory["螺丝M4"], 65)
        self.ledger.undo()
        self.assertEqual(self.ledger.inventory["螺丝M4"], 100)

    def test_irreversible_step_blocks_undo(self):
        outbox: list[str] = []
        self.ledger.run(c.StockOut("op-4", "螺丝M4", 90))
        self.ledger.run(c.NotifySupplier("op-5", "螺丝M4", outbox))
        self.assertEqual(outbox, ["请补货：螺丝M4，当前库存 10"])
        self.assertFalse(self.ledger.can_undo())
        self.assertIsNone(self.ledger.undo())
        self.assertEqual(self.ledger.inventory["螺丝M4"], 10)

    def test_failed_command_is_not_recorded(self):
        with self.assertRaises(ValueError):
            self.ledger.run(c.StockOut("op-6", "螺丝M4", 500))
        self.assertTrue(self.ledger.run(c.StockOut("op-6", "螺丝M4", 5)))  # 失败的编号可以再用


class DataCommandTest(unittest.TestCase):
    def test_inverse_commands(self):
        inv = {"螺丝M4": 100}
        stack = [py.apply(inv, py.Remove("螺丝M4", 30)), py.apply(inv, py.Recount("螺丝M4", 65))]
        self.assertEqual(stack, [py.Add("螺丝M4", 30), py.Recount("螺丝M4", 70)])
        py.apply(inv, stack.pop())
        py.apply(inv, stack.pop())
        self.assertEqual(inv, {"螺丝M4": 100})

    def test_replay(self):
        log = [py.Add("螺丝M4", 100), py.Remove("螺丝M4", 30), py.Recount("螺丝M4", 65)]
        self.assertEqual(py.replay(log), {"螺丝M4": 65})


if __name__ == "__main__":
    unittest.main()
