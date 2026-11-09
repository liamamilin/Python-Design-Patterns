import unittest
from datetime import datetime, timezone

from examples import ch10_adapter as ad
from examples import ch10_pythonic as py
from examples import ch10_report_v1 as v1
from examples.ch10_attendance import BEIJING, HQ_RECORDS, LocalClock, Punch, late_report
from examples.ch10_cloud_sdk import BRANCH_EVENTS, BRANCH_STAFF, CloudAttendanceClient

EXPECTED = ["03-09 孙浩", "03-09 李雷"]


def branch_adapter(tz=BEIJING):
    return ad.CloudClockAdapter(CloudAttendanceClient(BRANCH_EVENTS), BRANCH_STAFF, tz)


class ExistingReportTest(unittest.TestCase):
    def test_headquarters_only(self):
        self.assertEqual(late_report([LocalClock(HQ_RECORDS)]), ["03-09 李雷"])


class IsinstanceVersionTest(unittest.TestCase):
    def test_works_but_report_knows_every_vendor(self):
        sources = [LocalClock(HQ_RECORDS), CloudAttendanceClient(BRANCH_EVENTS)]
        self.assertEqual(v1.late_report(sources), EXPECTED)
        with self.assertRaises(TypeError):
            v1.late_report([object()])


class AdapterTest(unittest.TestCase):
    def test_report_unchanged_with_adapter(self):
        self.assertEqual(late_report([LocalClock(HQ_RECORDS), branch_adapter()]), EXPECTED)

    def test_translation(self):
        punches = branch_adapter().punches()
        self.assertEqual(len(punches), 4)  # BREAK 被丢弃
        self.assertEqual(punches[1], Punch("孙浩", datetime(2026, 3, 9, 9, 17, tzinfo=BEIJING), "上班"))

    def test_time_zone_is_a_real_decision(self):
        # 同样的时间戳，按 UTC 解释是凌晨 1 点多，于是没有人迟到
        self.assertEqual(late_report([branch_adapter(timezone.utc)]), [])
        self.assertEqual(late_report([branch_adapter()]), ["03-09 孙浩"])

    def test_unknown_employee(self):
        client = CloudAttendanceClient([{"uid": "E-9999", "ts": 1773017520000, "type": "IN"}])
        with self.assertRaises(ValueError):
            ad.CloudClockAdapter(client, BRANCH_STAFF, BEIJING).punches()

    def test_class_adapter_also_exposes_the_sdk(self):
        both = ad.CloudClockClassAdapter(BRANCH_EVENTS, BRANCH_STAFF, BEIJING)
        self.assertEqual(late_report([both]), ["03-09 孙浩"])
        self.assertEqual(len(both.fetch_events()), 5)  # SDK 的方法也一起暴露了出来


class FunctionAdapterTest(unittest.TestCase):
    def test_same_punches_as_the_object_adapter(self):
        events = CloudAttendanceClient(BRANCH_EVENTS).fetch_events()
        self.assertEqual(py.punches_from_cloud(events, BRANCH_STAFF, BEIJING), branch_adapter().punches())


if __name__ == "__main__":
    unittest.main()
