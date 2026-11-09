import unittest

from examples import ch17_pythonic as py
from examples import ch17_shipping_v1 as v1
from examples import ch17_strategy as st
from examples.ch17_shipping_v1 import Order

ORDER = Order(weight_g=2300, distance_km=8.5, subtotal=6800)
FAR = Order(weight_g=500, distance_km=25, subtotal=12000)


class TwoCopiesTest(unittest.TestCase):
    def test_pages_disagree_after_a_rate_change(self):
        self.assertEqual(v1.checkout_fee(ORDER, "express"), 1400)
        self.assertEqual(v1.quote_all(ORDER)["express"], 1200)


class StrategyTest(unittest.TestCase):
    def test_every_page_uses_the_same_rules(self):
        self.assertEqual(st.checkout_fee(ORDER, st.METHODS["express"]), 1400)
        self.assertEqual(
            st.quote_all(ORDER),
            ["普通快递：14.00 元，2–3 天", "同城急送：33.00 元，2 小时内", "到店自提：0.00 元，今天可取"],
        )

    def test_free_shipping_and_availability(self):
        self.assertEqual(st.quote_all(FAR), ["普通快递：0.00 元，2–3 天", "到店自提：0.00 元，今天可取"])
        with self.assertRaises(ValueError):
            st.checkout_fee(FAR, st.METHODS["same_city"])

    def test_configured_strategy(self):
        member_day = st.Express(free_over=5900)
        self.assertEqual(st.checkout_fee(ORDER, member_day), 0)
        self.assertEqual(st.Express().fee(ORDER), 1400)  # 默认配置不受影响

    def test_new_method_needs_no_change_elsewhere(self):
        class Locker:
            name = "快递柜"

            def available(self, order):
                return order.weight_g <= 5000

            def fee(self, order):
                return 500

            def eta(self, order):
                return "次日"

        methods = {**st.METHODS, "locker": Locker()}
        self.assertIn("快递柜：5.00 元，次日", st.quote_all(ORDER, methods))


class FunctionTest(unittest.TestCase):
    def test_functions_give_the_same_fees(self):
        for key, method in st.METHODS.items():
            with self.subTest(key=key):
                self.assertEqual(py.checkout_fee(ORDER, py.FEES[key]), method.fee(ORDER))

    def test_partial_as_configured_strategy(self):
        self.assertEqual(py.checkout_fee(ORDER, py.member_day_express), 0)


if __name__ == "__main__":
    unittest.main()
