import unittest

from examples import ch04_parking as p


class BillableHoursTest(unittest.TestCase):
    def test_rounds_up_with_minimum_one_hour(self):
        self.assertEqual(p.billable_hours(0), 1)
        self.assertEqual(p.billable_hours(60), 1)
        self.assertEqual(p.billable_hours(61), 2)
        self.assertEqual(p.billable_hours(90), 2)


class ThreeWaysAgreeTest(unittest.TestCase):
    CASES = [("car", 90, 10), ("car", 30, 5), ("motorcycle", 30, 2), ("motorcycle", 181, 8)]

    def test_same_results(self):
        for vehicle, minutes, expected in self.CASES:
            with self.subTest(vehicle=vehicle, minutes=minutes):
                self.assertEqual(p.fee_by_if(vehicle, minutes), expected)
                self.assertEqual(p.fee_by_table(vehicle, minutes), expected)
                self.assertEqual(p.fee_by_rule(p.RULES[vehicle], minutes), expected)

    def test_unknown_vehicle(self):
        with self.assertRaises(ValueError):
            p.fee_by_if("bus", 30)
        with self.assertRaises(ValueError):
            p.fee_by_table("bus", 30)


class AddingTruckTest(unittest.TestCase):
    def test_if_version_needs_editing_the_function(self):
        with self.assertRaises(ValueError):
            p.fee_by_if("truck", 61)

    def test_table_can_be_extended_from_outside(self):
        p.RATES["truck"] = p.truck_fee
        try:
            self.assertEqual(p.fee_by_table("truck", 61), 20)
            self.assertEqual(p.fee_by_table("truck", 180), 30)
        finally:
            del p.RATES["truck"]

    def test_rule_class(self):
        self.assertEqual(p.fee_by_rule(p.TruckRule(), 61), 20)
        self.assertEqual(p.fee_by_rule(p.TruckRule(), 180), 30)


if __name__ == "__main__":
    unittest.main()
