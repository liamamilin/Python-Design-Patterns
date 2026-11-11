"""第 03 章：名字、对象与引用。

后面各章的模式都建立在 Python 的对象模型之上：名字只是指向对象，
赋值和传参都不会复制对象；可变对象被几处同时引用时，一处修改处处可见。
仍然使用本章“清洗评论”的例子。
运行：python -m examples.ch03_objects
"""
from __future__ import annotations

from examples.ch03_tools import Censor, Pipeline, strip_spaces


# 1. 赋值和传参不复制对象：两个屏蔽器拿到的是同一份词表
def shared_word_list() -> tuple[Censor, Censor]:
    words = ["垃圾"]
    forum = Censor(words)
    shop = Censor(words)
    forum.words.append("难喝")  # 只想给论坛多屏蔽一个词
    return forum, shop


# 2. 在边界上复制一份，或者干脆保存不可变的数据
class OwnWordsCensor(Censor):
    def __init__(self, words: list[str]) -> None:
        super().__init__(words)
        self.words = tuple(words)  # 自己的副本，而且不能被原地修改


def separate_word_lists() -> tuple[OwnWordsCensor, OwnWordsCensor]:
    words = ["垃圾"]
    forum = OwnWordsCensor(words)
    shop = OwnWordsCensor(words)
    forum.words = (*forum.words, "难喝")  # 让 forum.words 指向一个新元组
    return forum, shop


# 3. 身份与相等：== 问“内容一样吗”，is 问“是同一个对象吗”
def equal_but_not_same() -> tuple[bool, bool]:
    a = ["垃圾", "难喝"]
    b = ["垃圾", "难喝"]
    return a == b, a is b


# 4. 两个名字，一个对象：交出去的对象，状态变化你也看得见
def counting_through_a_pipeline() -> int:
    censor = Censor(["垃圾"])
    clean = Pipeline(strip_spaces, censor)
    clean("垃圾服务")
    clean("又是垃圾")
    return censor.replaced  # 管道里的那个，就是手里的这个


if __name__ == "__main__":
    forum, shop = shared_word_list()
    print("商城也屏蔽了“难喝”：", shop("咖啡难喝"), forum.words is shop.words)
    forum, shop = separate_word_lists()
    print("各自的词表：", forum.words, shop.words)
    print("相等、同一个：", equal_but_not_same())
    print("管道里屏蔽了：", counting_through_a_pipeline())
