import tempfile
import threading
import unittest
from pathlib import Path

from examples import ch09_pythonic as py
from examples import ch09_shared_counter as shared
from examples import ch09_singleton as s
from examples import ch09_ticket_v1 as v1


class FirstVersionTest(unittest.TestCase):
    def test_two_machines_give_the_same_number(self):
        self.assertEqual(v1.Kiosk().press(), "A001")
        self.assertEqual(v1.PhoneBooking().book(), "A001")


class SingletonTest(unittest.TestCase):
    def setUp(self):
        s.TicketMachine._reset_for_tests()
        s.BrokenTicketMachine._instance = None
        self.addCleanup(s.TicketMachine._reset_for_tests)

    def test_init_runs_again_and_resets_the_count(self):
        kiosk = s.BrokenTicketMachine()
        self.assertEqual([kiosk.take(), kiosk.take()], ["A001", "A002"])
        phone = s.BrokenTicketMachine()  # 同一个对象，但 __init__ 又执行了一次
        self.assertIs(phone, kiosk)
        self.assertEqual(phone.take(), "A001")

    def test_one_instance_shared(self):
        kiosk, phone = s.Kiosk(), s.PhoneBooking()
        self.assertIs(kiosk.machine, phone.machine)
        self.assertEqual([kiosk.press(), phone.book(), kiosk.press()], ["A001", "A002", "A003"])

    def test_unique_across_threads(self):
        results: list[str] = []

        def worker():
            machine = s.TicketMachine()
            got = [machine.take() for _ in range(250)]
            results.extend(got)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(results), 2000)
        self.assertEqual(len(set(results)), 2000)

    def test_each_process_has_its_own_instance(self):
        self.assertEqual(s.take_in_new_process(2), ["A001", "A002"])
        self.assertEqual(s.take_in_new_process(2), ["A001", "A002"])


class SharedCounterTest(unittest.TestCase):
    def test_unique_across_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "tickets.db"
            shared.create_counter(db)
            first = shared.take_in_new_process(db, 2)
            second = shared.take_in_new_process(db, 2)
            self.assertEqual(first + second, ["A001", "A002", "A003", "A004"])


class PassItInTest(unittest.TestCase):
    def test_shared_by_construction(self):
        kiosk, phone = py.build_branch()
        self.assertEqual([kiosk.press(), phone.book()], ["A001", "A002"])

    def test_each_test_gets_a_fresh_machine(self):
        kiosk, _ = py.build_branch()
        self.assertEqual(kiosk.press(), "A001")

    def test_second_queue_is_just_another_instance(self):
        kiosk, _ = py.build_branch()
        business = py.TicketMachine("B")
        self.assertEqual([kiosk.press(), business.take(), kiosk.press()], ["A001", "B001", "A002"])

    def test_module_level_object_is_imported_once(self):
        import importlib

        again = importlib.import_module("examples.ch09_pythonic")
        self.assertIs(again.default_machine, py.default_machine)


if __name__ == "__main__":
    unittest.main()
