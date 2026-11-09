import unittest

from examples import ch22_chain as ch
from examples import ch22_pythonic as py
from examples import ch22_speaker_v1 as v1

SAMPLES = ["帮我买一盒彩笔", "帮我点个外卖", "明早七点的闹钟", "今天天气怎么样", "播放儿歌", "讲个笑话"]


class IfChainTest(unittest.TestCase):
    def test_new_branch_bypasses_the_child_check(self):
        self.assertEqual(v1.respond("帮我买一盒彩笔", child_mode=True), "儿童模式下不能购物")
        self.assertEqual(v1.respond("帮我点个外卖", child_mode=True), "已为你下单外卖")


class ChainTest(unittest.TestCase):
    def test_child_lock_comes_first(self):
        kids = ch.kids_speaker()
        self.assertEqual(kids.handle("帮我买一盒彩笔"), "儿童模式下不能消费")
        self.assertEqual(kids.handle("帮我点个外卖"), "儿童模式下不能消费")
        self.assertEqual(kids.handle("明早七点的闹钟"), "好的，闹钟已设好")

    def test_kitchen_speaker_has_no_lock(self):
        self.assertEqual(ch.kitchen_speaker().handle("帮我点个外卖"), "已为你下单外卖")

    def test_unhandled_request_is_explicit(self):
        self.assertEqual(ch.kids_speaker().handle("讲个笑话"), "抱歉，我没听懂")

    def test_order_matters(self):
        late_lock = ch.chain(*ch.common_handlers(), ch.ChildLock())
        self.assertEqual(late_lock.handle("帮我点个外卖"), "已为你下单外卖")  # 锁放到最后就形同虚设

    def test_first_match_wins(self):
        speaker = ch.kitchen_speaker()
        self.assertEqual(speaker.handle("播放天气预报"), "今天晴，18 到 26 度")


class ListTest(unittest.TestCase):
    def test_same_answers_as_the_linked_chain(self):
        for text in SAMPLES:
            with self.subTest(text=text):
                self.assertEqual(py.respond(text, py.KIDS), ch.kids_speaker().handle(text))
                self.assertEqual(py.respond(text, py.COMMON), ch.kitchen_speaker().handle(text))


if __name__ == "__main__":
    unittest.main()
