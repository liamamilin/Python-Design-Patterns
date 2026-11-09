import unittest
from datetime import datetime

from examples import ch20_booking_v1 as v1
from examples import ch20_pythonic as py
from examples import ch20_state as st

START = datetime(2026, 3, 9, 14, 0)
EARLY_OK = datetime(2026, 3, 9, 13, 55)
TOO_EARLY = datetime(2026, 3, 9, 13, 40)
LATE = datetime(2026, 3, 9, 14, 20)


class StringStatusTest(unittest.TestCase):
    def test_cancel_after_check_in_slips_through(self):
        b = v1.Booking("301", START)
        b.approve()
        b.check_in(EARLY_OK)
        b.cancel()
        self.assertEqual(b.status, "已取消")


class StateObjectTest(unittest.TestCase):
    def confirmed(self):
        b = st.Booking("301", START)
        b.approve()
        return b

    def test_happy_path(self):
        b = self.confirmed()
        b.check_in(EARLY_OK)
        self.assertEqual(b.status, "已签到")

    def test_cancel_after_check_in_is_refused(self):
        b = self.confirmed()
        b.check_in(EARLY_OK)
        with self.assertRaises(st.NotAllowed):
            b.cancel()
        self.assertEqual(b.status, "已签到")

    def test_check_in_window(self):
        b = self.confirmed()
        with self.assertRaises(st.NotAllowed):
            b.check_in(TOO_EARLY)
        self.assertEqual(b.status, "已确认")

    def test_expire_only_after_grace(self):
        b = self.confirmed()
        b.expire(EARLY_OK)
        self.assertEqual(b.status, "已确认")
        b.expire(LATE)
        self.assertEqual(b.status, "已释放")
        with self.assertRaises(st.NotAllowed):
            b.check_in(LATE)

    def test_new_state_refuses_everything_by_default(self):
        class OnHold(st.State):
            name = "暂停"

        b = st.Booking("301", START)
        b.state = OnHold()
        for action in (b.approve, b.cancel):
            with self.assertRaises(st.NotAllowed):
                action()


class TableTest(unittest.TestCase):
    def test_same_rules(self):
        b = py.Booking("301", START)
        b.fire("approve")
        b.fire("check_in", EARLY_OK)
        with self.assertRaises(ValueError):
            b.fire("cancel")
        self.assertIs(b.status, py.Status.CHECKED_IN)

    def test_expire(self):
        b = py.Booking("301", START)
        b.fire("approve")
        b.fire("expire", EARLY_OK)
        self.assertIs(b.status, py.Status.CONFIRMED)
        b.fire("expire", LATE)
        self.assertIs(b.status, py.Status.RELEASED)

    def test_table_can_be_listed(self):
        self.assertEqual(py.allowed(py.Status.CONFIRMED), ["cancel", "check_in", "expire"])
        self.assertEqual(py.allowed(py.Status.CHECKED_IN), [])


if __name__ == "__main__":
    unittest.main()
