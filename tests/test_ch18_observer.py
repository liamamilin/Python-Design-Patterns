import unittest

from examples import ch18_greenhouse_v1 as v1
from examples import ch18_observer as ob
from examples import ch18_pythonic as py


class HardWiredTest(unittest.TestCase):
    def test_greenhouse_calls_everyone_itself(self):
        fan, alarm, log = v1.Fan(), v1.Alarm(), v1.DataLog()
        house = v1.Greenhouse(fan, alarm, log)
        for t in (28, 31, 36):
            house.record(t)
        self.assertEqual((fan.on, alarm.messages, log.rows), (True, ["温度过高：36℃"], [28, 31, 36]))


class NaivePitfallsTest(unittest.TestCase):
    def test_detaching_during_notify_skips_the_next_observer(self):
        house = ob.NaiveGreenhouse()
        alert, log = ob.FirstHeatAlert(house), ob.DataLog()
        house.attach(alert)
        house.attach(log)
        for t in (28, 36, 37):
            house.record(t)
        self.assertEqual(log.rows, [28, 37])  # 36 这次读数被漏掉了

    def test_one_error_stops_everyone_after_it(self):
        house = ob.NaiveGreenhouse()
        uploader, log = ob.CloudUploader(), ob.DataLog()
        house.attach(uploader)
        house.attach(log)
        uploader.online = False
        with self.assertRaises(ConnectionError):
            house.record(30)
        self.assertEqual(log.rows, [])


class ObserverTest(unittest.TestCase):
    def test_subscribers_in_order(self):
        house = ob.Greenhouse()
        seen = []

        class Recorder:
            def __init__(self, name):
                self.name = name

            def update(self, temp):
                seen.append((self.name, temp))

        house.attach(Recorder("甲"))
        house.attach(Recorder("乙"))
        house.record(25)
        self.assertEqual(seen, [("甲", 25), ("乙", 25)])

    def test_detaching_during_notify_is_safe(self):
        house = ob.Greenhouse()
        alert, log = ob.FirstHeatAlert(house), ob.DataLog()
        house.attach(alert)
        house.attach(log)
        for t in (28, 36, 37):
            house.record(t)
        self.assertEqual(log.rows, [28, 36, 37])
        self.assertEqual(alert.messages, ["今天第一次超过 35℃：36℃"])

    def test_errors_are_collected_and_others_still_notified(self):
        house = ob.Greenhouse()
        uploader, fan, log = ob.CloudUploader(), ob.Fan(), ob.DataLog()
        for o in (uploader, fan, log):
            house.attach(o)
        uploader.online = False
        with self.assertRaises(ExceptionGroup) as caught:
            house.record(31)
        self.assertEqual([type(e) for e in caught.exception.exceptions], [ConnectionError])
        self.assertTrue(fan.on)
        self.assertEqual(log.rows, [31])
        self.assertEqual(house.temp, 31)

    def test_new_reaction_without_touching_greenhouse(self):
        house = ob.Greenhouse()
        fan = ob.Fan()
        house.attach(fan)
        house.record(32)
        self.assertTrue(fan.on)


class SignalTest(unittest.TestCase):
    def test_connect_returns_disconnect(self):
        house = py.Greenhouse()
        readings = []
        stop = house.temp_changed.connect(readings.append)
        house.record(28)
        stop()
        stop()  # 重复取消不会出错
        house.record(31)
        self.assertEqual(readings, [28])

    def test_same_error_policy(self):
        house = py.Greenhouse()
        readings = []

        def broken(temp):
            raise ValueError("坏了")

        house.temp_changed.connect(broken)
        house.temp_changed.connect(readings.append)
        with self.assertRaises(ExceptionGroup):
            house.record(30)
        self.assertEqual(readings, [30])


if __name__ == "__main__":
    unittest.main()
