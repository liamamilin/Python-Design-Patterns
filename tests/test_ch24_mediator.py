import unittest
from datetime import date

from examples import ch24_form_v1 as v1
from examples import ch24_mediator as md
from examples import ch24_pythonic as py

MAY_DAY = date(2026, 5, 1)


class TangledWidgetsTest(unittest.TestCase):
    def test_passport_depends_on_whichever_city_changed_last(self):
        search, passport = v1.SearchButton(), v1.PassportField()
        origin, dest = v1.CityBox(search, passport), v1.CityBox(search, passport)
        origin.other, dest.other = dest, origin
        origin.set("东京")
        dest.set("上海")
        self.assertFalse(passport.visible)  # 东京 → 上海 是国际航线，却不显示护照栏


class MediatorTest(unittest.TestCase):
    def test_passport_considers_both_cities(self):
        form = md.TicketForm()
        form.origin.set("东京")
        form.dest.set("上海")
        self.assertTrue(form.passport.visible)
        form.origin.set("北京")
        self.assertFalse(form.passport.visible)

    def test_search_needs_a_complete_and_sensible_form(self):
        form = md.TicketForm()
        self.assertFalse(form.search.enabled)
        form.origin.set("北京")
        form.dest.set("北京")
        form.depart.set(MAY_DAY)
        self.assertFalse(form.search.enabled)  # 出发地等于目的地
        form.dest.set("成都")
        self.assertTrue(form.search.enabled)
        form.round_trip.set(True)
        self.assertTrue(form.return_date.enabled)
        self.assertFalse(form.search.enabled)  # 勾了往返，还没选返程日期
        form.return_date.set(date(2026, 5, 5))
        self.assertTrue(form.search.enabled)

    def test_fields_do_not_know_each_other(self):
        form = md.TicketForm()
        self.assertEqual(set(vars(form.origin)), {"mediator", "value", "enabled", "visible"})


class PureFunctionTest(unittest.TestCase):
    def test_same_rules_as_the_mediator(self):
        cases = [
            py.FormValues(),
            py.FormValues(origin="东京", dest="上海", depart=MAY_DAY),
            py.FormValues(origin="北京", dest="北京", depart=MAY_DAY),
            py.FormValues(origin="北京", dest="成都", depart=MAY_DAY, round_trip=True),
        ]
        for values in cases:
            with self.subTest(values=values):
                form = md.TicketForm()
                for name in ("origin", "dest", "depart", "round_trip", "return_date"):
                    getattr(form, name).set(getattr(values, name))
                state = py.ui_state(values)
                self.assertEqual(
                    (state.passport_visible, state.return_date_enabled, state.search_enabled),
                    (form.passport.visible, form.return_date.enabled, form.search.enabled),
                )


if __name__ == "__main__":
    unittest.main()
