import contextlib
import io
import tempfile
import unittest
from datetime import date
from pathlib import Path

from examples import ch06_abstract_factory as af
from examples import ch06_pythonic as py
from examples import ch06_reminders_v1 as v1
from examples.ch06_reminders_v1 import loans

TODAY = date(2026, 3, 9)
EXPECTED = [
    "王芳，您借的《城南旧事》将于3月10日到期",
    "李雷，您借的《活着》将于3月11日到期",
]


def quiet(func, *args):
    """运行 func，返回 (结果, 打印出的文字)。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = func(*args)
    return result, buf.getvalue()


class TempFolderTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)

    def outbox_lines(self):
        path = self.folder / "outbox.txt"
        return path.read_text("utf-8").splitlines() if path.exists() else []


class FirstVersionBugTest(TempFolderTest):
    def test_dry_run_swallows_the_real_reminders(self):
        outbox, log = self.folder / "outbox.txt", self.folder / "sent.json"
        count, printed = quiet(v1.send_reminders, loans, TODAY, outbox, log, True)
        self.assertEqual(count, 2)
        self.assertIn("[演练] " + EXPECTED[0], printed)
        # 演练把记录写进了正式文件，正式运行以为已经发过了
        self.assertEqual(v1.send_reminders(loans, TODAY, outbox, log), 0)
        self.assertEqual(self.outbox_lines(), [])


class AbstractFactoryTest(TempFolderTest):
    def test_dry_run_then_live(self):
        count, printed = quiet(af.send_reminders, loans, TODAY, af.DryRunServices(self.folder))
        self.assertEqual(count, 2)
        self.assertEqual(printed.splitlines(), ["[演练] " + t for t in EXPECTED])
        self.assertFalse((self.folder / "sent.json").exists())
        self.assertEqual(af.send_reminders(loans, TODAY, af.LiveServices(self.folder)), 2)
        self.assertEqual(self.outbox_lines(), EXPECTED)

    def test_live_does_not_send_twice(self):
        services = af.services_for("live", self.folder)
        self.assertEqual(af.send_reminders(loans, TODAY, services), 2)
        self.assertEqual(af.send_reminders(loans, TODAY, services), 0)
        self.assertEqual(self.outbox_lines(), EXPECTED)

    def test_dry_run_reads_the_live_record(self):
        af.send_reminders(loans, TODAY, af.LiveServices(self.folder))
        count, printed = quiet(af.send_reminders, loans, TODAY, af.DryRunServices(self.folder))
        self.assertEqual((count, printed), (0, ""))

    def test_memory_family(self):
        services = af.MemoryServices()
        self.assertEqual(af.send_reminders(loans, TODAY, services), 2)
        self.assertEqual(services.sender.messages, EXPECTED)

    def test_unknown_mode(self):
        with self.assertRaises(ValueError):
            af.services_for("staging", self.folder)

    def test_incomplete_family_cannot_be_created(self):
        class HalfServices(af.ReminderServices):
            def create_sender(self):
                return af.PrintSender()

        with self.assertRaises(TypeError):
            HalfServices()


class KitTest(TempFolderTest):
    def test_same_behaviour_with_a_plain_bundle(self):
        count, _ = quiet(py.send_with_kit, loans, TODAY, py.dry_run_kit(self.folder))
        self.assertEqual(count, 2)
        self.assertEqual(py.send_with_kit(loans, TODAY, py.live_kit(self.folder)), 2)
        self.assertEqual(self.outbox_lines(), EXPECTED)


if __name__ == "__main__":
    unittest.main()
