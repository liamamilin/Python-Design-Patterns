import unittest

from examples import ch15_flyweight as fw
from examples import ch15_pythonic as py
from examples import ch15_taps_v1 as v1

LINES = v1.raw_lines(20_000)


class PlainTest(unittest.TestCase):
    def test_every_record_has_its_own_strings(self):
        taps = v1.parse(LINES)
        self.assertIsNot(taps[0].station, taps[5].station)
        self.assertEqual(len({id(t.station) for t in taps}), len(taps))


class FlyweightTest(unittest.TestCase):
    def test_stations_are_shared(self):
        pool = fw.StationPool()
        taps = fw.parse(LINES, pool)
        self.assertEqual(len(pool), 5)
        self.assertIs(taps[0].station, taps[5].station)
        self.assertEqual(len({id(t.station) for t in taps}), 5)

    def test_shared_state_cannot_be_changed(self):
        station = fw.StationPool().get("国贸", "1号线", 1)
        with self.assertRaises(AttributeError):
            station.zone = 2  # type: ignore[misc]

    def test_same_information(self):
        plain = v1.parse(LINES[:10])
        shared = fw.parse(LINES[:10], fw.StationPool())
        self.assertEqual(
            [(p.card, p.minute, p.station, p.line, p.zone) for p in plain],
            [(s.card, s.minute, s.station.name, s.station.line, s.station.zone) for s in shared],
        )

    def test_measured_memory_is_lower(self):
        # 只断言相对大小，不断言具体字节数
        plain = fw.measure(lambda: v1.parse(LINES))
        shared = fw.measure(lambda: fw.parse(LINES, fw.StationPool()))
        self.assertLess(shared, plain)


class PythonicTest(unittest.TestCase):
    def test_cache_as_factory(self):
        self.assertIs(py.station("国贸", "1号线", 1), py.station("国贸", "1号线", 1))

    def test_interning_alone_helps(self):
        interned = py.parse_interned(LINES)
        self.assertIs(interned[0].station, interned[5].station)
        interned_size = fw.measure(lambda: py.parse_interned(LINES))
        self.assertLess(interned_size, fw.measure(lambda: v1.parse(LINES)))
        # 享元版本还用了 __slots__，字段也更少，所以更小
        self.assertLess(fw.measure(lambda: fw.parse(LINES, fw.StationPool())), interned_size)

    def test_counting_without_keeping_records(self):
        counts = py.taps_per_station(LINES)
        self.assertEqual(sum(counts.values()), 20_000)
        self.assertEqual(counts["望京"], 4000)


if __name__ == "__main__":
    unittest.main()
