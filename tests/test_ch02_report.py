import unittest

from examples import ch02_report_after as after
from examples import ch02_report_before as before
from examples import ch02_report_v1 as v1


class FirstVersionTest(unittest.TestCase):
    def test_first_report(self):
        self.assertEqual(v1.class_report(["小林", "小周"], [72, 48]), ["小林 72 及格", "小周 48 不及格"])


class BeforeRefactorBugsTest(unittest.TestCase):
    def test_report_and_notice_disagree_about_chemistry(self):
        report = before.class_report("化学", ["小周"], [52])
        notice = before.parent_notice("化学", "小周", 52)
        self.assertEqual(report[1], "小周 52 及格")
        self.assertEqual(notice, "小周 家长：本次化学 52 分，未及格，请留意。")

    def test_median_scrambles_names_and_scores(self):
        scores = list(before.math_scores)
        lines = before.class_report("数学", list(before.students), scores)
        # 小林实际考了 72 分、小周 48 分，报告却按排好序的分数对上了原来的名字
        self.assertEqual(
            lines,
            [
                "数学 中位数：68.5",
                "小林 48 不及格",
                "小周 65 及格",
                "小吴 72 及格",
                "小郑 91 及格",
            ],
        )
        self.assertEqual(scores, [48, 65, 72, 91])


class AfterRefactorTest(unittest.TestCase):
    def test_report_is_correct(self):
        self.assertEqual(
            after.class_report("数学", after.math_scores),
            [
                "数学 中位数：68.5",
                "小林 72 及格",
                "小周 48 不及格",
                "小吴 91 及格",
                "小郑 65 及格",
            ],
        )

    def test_report_and_notice_agree(self):
        self.assertEqual(after.class_report("化学", {"小周": 52})[1], "小周 52 及格")
        self.assertEqual(after.parent_notice("化学", "小周", 52), "小周 家长：本次化学 52 分，已及格。")

    def test_new_pass_mark_is_one_edit(self):
        original = dict(after.PASS_MARKS)
        try:
            after.PASS_MARKS["生物"] = 58
            self.assertFalse(after.passed("生物", 57))
            self.assertEqual(after.class_report("生物", {"小林": 57})[1], "小林 57 不及格")
            self.assertEqual(after.parent_notice("生物", "小林", 57), "小林 家长：本次生物 57 分，未及格，请留意。")
        finally:
            after.PASS_MARKS.clear()
            after.PASS_MARKS.update(original)

    def test_median_leaves_input_alone(self):
        values = [72, 48, 91, 65]
        self.assertEqual(after.median(values), 68.5)
        self.assertEqual(values, [72, 48, 91, 65])


if __name__ == "__main__":
    unittest.main()
