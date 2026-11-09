import unittest

from examples import ch21_contest_v1 as v1
from examples import ch21_pythonic as py
from examples import ch21_template_method as tm
from examples.ch21_contest_v1 import Entry, divers, singers

DIVING = ["1. 林 70.50", "1. 陈 70.50", "3. 吴 65.60"]
SINGING = ["1. 小雨 8.83", "1. 木子 8.83", "3. 阿杰 8.33"]


class TwoFunctionsTest(unittest.TestCase):
    def test_tie_fix_only_in_one_copy(self):
        self.assertEqual(v1.diving_results(divers), DIVING)
        self.assertEqual(v1.singing_results(singers), ["1. 小雨 8.83", "2. 木子 8.83", "3. 阿杰 8.33"])


class TemplateMethodTest(unittest.TestCase):
    def test_both_contests_share_the_same_ranking(self):
        self.assertEqual(tm.Diving().results(divers), DIVING)
        self.assertEqual(tm.Singing().results(singers), SINGING)

    def test_validation_uses_each_contests_requirement(self):
        with self.assertRaises(ValueError):
            tm.Diving().results([Entry("x", [8.0, 8.0, 8.0])])
        with self.assertRaises(ValueError):
            tm.Singing().results(divers)

    def test_new_contest_only_fills_in_the_steps(self):
        class Calligraphy(tm.Contest):
            def score(self, e):
                return max(e.judges)  # 书法比赛：取最高分

        entries = [Entry("甲", [7.0, 9.5, 8.0]), Entry("乙", [9.0, 9.0, 9.0])]
        self.assertEqual(Calligraphy().results(entries), ["1. 甲 9.50", "2. 乙 9.00"])

    def test_score_is_required(self):
        with self.assertRaises(TypeError):
            tm.Contest()  # type: ignore[abstract]


class FunctionTest(unittest.TestCase):
    def test_same_results_with_functions(self):
        out = py.results(singers, py.average, penalty=lambda e: 0.5 if e.overtime_s else 0.0)
        self.assertEqual(out, SINGING)
        diving = py.results(divers, lambda e: sum(sorted(e.judges)[1:-1]) * e.difficulty, judges=5)
        self.assertEqual(diving, DIVING)


if __name__ == "__main__":
    unittest.main()
