import dataclasses
import json
import unittest

from examples import ch25_farm_v1 as v1
from examples import ch25_memento as mm
from examples import ch25_pythonic as py


class SharedDictTest(unittest.TestCase):
    def test_saved_game_changes_after_saving(self):
        farm = v1.Farm()
        farm.plant("萝卜", 3)
        slot = farm.save()
        farm.plant("萝卜", 2)
        farm.next_day()
        farm.load(slot)
        self.assertEqual(farm.summary(), "第 1 天，金币 70，萝卜×5")


class MementoTest(unittest.TestCase):
    def test_restore_brings_back_the_exact_state(self):
        farm, slots = mm.Farm(), mm.SaveSlots()
        farm.plant("萝卜", 3)
        slots.save("开局", farm)
        farm.plant("萝卜", 2)
        farm.harvest("萝卜")
        farm.next_day()
        self.assertEqual(farm.summary(), "第 2 天，金币 175，空地")
        slots.load("开局", farm)
        self.assertEqual(farm.summary(), "第 1 天，金币 70，萝卜×3")

    def test_one_memento_can_be_restored_many_times(self):
        farm = mm.Farm()
        farm.plant("南瓜", 1)
        snap = farm.save()
        for _ in range(2):
            farm.plant("南瓜", 2)
            farm.restore(snap)
            self.assertEqual(farm.summary(), "第 1 天，金币 90，南瓜×1")

    def test_memento_is_immutable(self):
        snap = mm.Farm().save()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            snap._coins = 9999  # type: ignore[misc]

    def test_slots(self):
        farm, slots = mm.Farm(), mm.SaveSlots()
        slots.save("B", farm)
        slots.save("A", farm)
        self.assertEqual(slots.names(), ["A", "B"])
        with self.assertRaises(KeyError):
            slots.load("C", farm)


class JsonTest(unittest.TestCase):
    def test_round_trip(self):
        farm = mm.Farm()
        farm.plant("萝卜", 3)
        snap = farm.save()
        self.assertEqual(py.from_json(py.to_json(snap)), snap)

    def test_rejects_tampered_or_unknown_saves(self):
        good = json.loads(py.to_json(mm.Farm().save()))
        for change in ({"version": 2}, {"coins": -5}, {"day": "1"}, {"crops": {"萝卜": 0}}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    py.from_json(json.dumps({**good, **change}))


if __name__ == "__main__":
    unittest.main()
