import unittest

from examples import ch07_builder as b
from examples import ch07_pythonic as py
from examples import ch07_search_v1 as v1

FORM = {"district": "朝阳", "subway": "on"}
ROWS = [("朝阳 两居 近地铁", 5800), ("朝阳 三居", 8800)]
FULL_FORM = {"district": "朝阳", "max_rent": "6000", "min_rooms": "2", "subway": "on", "sort": "price"}


class FirstVersionTest(unittest.TestCase):
    def test_description_forgets_the_subway_filter(self):
        self.assertEqual(v1.search(v1.connect(), FORM), ROWS)
        # 结果已经按“近地铁”过滤了，说明里却没有这一条
        self.assertEqual(v1.describe(FORM), "朝阳区")


class BuilderTest(unittest.TestCase):
    def test_same_steps_two_representations(self):
        sql_builder, text_builder = b.SqlBuilder(), b.DescriptionBuilder()
        b.apply_form(FULL_FORM, sql_builder)
        b.apply_form(FULL_FORM, text_builder)
        self.assertEqual(
            sql_builder.result(),
            (
                "SELECT title, rent FROM listings WHERE district = ? AND rent <= ?"
                " AND rooms >= ? AND near_subway = 1 ORDER BY rent",
                ["朝阳", 6000, 2],
            ),
        )
        self.assertEqual(text_builder.result(), "朝阳区，月租不超过 6000 元，至少 2 室，近地铁；按租金从低到高")

    def test_search_keeps_description_and_results_in_step(self):
        text, rows = b.search(v1.connect(), FORM)
        self.assertEqual(text, "朝阳区，近地铁；按租金从低到高")
        self.assertEqual(rows, ROWS)

    def test_sort_and_empty_form(self):
        text, rows = b.search(v1.connect(), {"sort": "price_desc"})
        self.assertEqual(text, "全部房源；按租金从高到低")
        self.assertEqual([r[1] for r in rows], [8800, 6500, 5800, 5200, 4200])

    def test_sort_is_whitelisted(self):
        conn = v1.connect()
        with self.assertRaises(ValueError):
            b.search(conn, {"sort": "rent; DROP TABLE listings"})
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM listings").fetchone(), (5,))

    def test_builder_is_single_use(self):
        builder = b.SqlBuilder()
        b.apply_form({"district": "朝阳"}, builder)
        b.apply_form({"district": "朝阳"}, builder)
        self.assertIn("district = ? AND district = ?", builder.result()[0])

    def test_builder_must_implement_every_step(self):
        class NoSubway(b.SearchBuilder):
            def district(self, name): ...
            def max_rent(self, yuan): ...
            def min_rooms(self, n): ...
            def sort(self, key): ...

        with self.assertRaises(TypeError):
            NoSubway()


class DataclassTest(unittest.TestCase):
    def test_same_results_as_builder(self):
        for form in (FORM, FULL_FORM, {"sort": "area"}, {}):
            with self.subTest(form=form):
                self.assertEqual(py.search(v1.connect(), form), b.search(v1.connect(), form))

    def test_invalid_sort_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            py.SearchFilter(sort="rent; DROP TABLE listings")

    def test_keyword_only(self):
        with self.assertRaises(TypeError):
            py.SearchFilter("朝阳")  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
