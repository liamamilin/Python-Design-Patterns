import unittest

from examples import ch29_types as t


class AnnotationsAreNotCheckedTest(unittest.TestCase):
    def test_wrong_type_runs_and_gives_a_wrong_answer(self):
        self.assertEqual(t.total_fee("3", 2), "33")  # type: ignore[arg-type]

    def test_newtype_is_the_plain_value_at_runtime(self):
        self.assertIs(type(t.PetId(7)), int)
        self.assertEqual(t.PetId(7), 7)
        swapped = t.book(t.PetId(7), t.OwnerId(3), "周六上午")  # type: ignore[arg-type]
        self.assertEqual(swapped, "主人 7 为宠物 3 预约了 周六上午")


class DataclassTest(unittest.TestCase):
    def test_fields_are_not_validated(self):
        pet = t.Pet("团子", "兔", "4")  # type: ignore[arg-type]
        self.assertEqual(pet.weight_kg, "4")

    def test_post_init_validates(self):
        self.assertEqual(t.CheckedPet("咪咪", "猫", 4.2).name, "咪咪")
        for args in (("团子", "兔", 2.0), ("旺财", "狗", "4"), ("旺财", "狗", 0)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    t.CheckedPet(*args)


class ProtocolAndAbcTest(unittest.TestCase):
    def test_runtime_checkable_only_checks_the_name(self):
        self.assertIsInstance(t.SmsNotifier(), t.Notifier)
        self.assertIsInstance(t.WrongNotifier(), t.Notifier)  # 签名完全不对，也算

    def test_abc_checks_at_instantiation(self):
        class Forgetful(t.Reminder):
            pass

        with self.assertRaises(TypeError):
            Forgetful()

    def test_register_skips_the_check(self):
        class Anything:
            pass

        t.Reminder.register(Anything)
        self.assertIsInstance(Anything(), t.Reminder)
        self.assertFalse(hasattr(Anything(), "remind"))


class TypedDictTest(unittest.TestCase):
    def test_typed_dict_is_a_plain_dict(self):
        visit = t.VisitJson(pet=7, slot="周六上午")
        self.assertIs(type(visit), dict)
        wrong = t.VisitJson(pet="七", slot=3)  # type: ignore[typeddict-item]
        self.assertEqual(wrong["pet"], "七")


if __name__ == "__main__":
    unittest.main()
