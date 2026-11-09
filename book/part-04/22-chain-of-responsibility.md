# 第 22 章　责任链 Chain of Responsibility

> 本章要回答：一个请求可能由好几个处理者中的某一个来处理，而由谁处理要依次试过才知道时，怎样避免一个越写越长、顺序越来越脆弱的 `if/elif`？

## 眼前的任务

一家小公司做智能音箱。用户说一句话，音箱把它转成文字，程序决定怎样回应：设闹钟、报天气、放音乐、购物……

## 不用模式的写法

按关键词依次判断，第一个匹配上的就回应：

```python
def respond(text: str, child_mode: bool = False) -> str:
    if "闹钟" in text:
        return "好的，闹钟已设好"
    elif "天气" in text:
        return "今天晴，18 到 26 度"
    elif "外卖" in text:  # 新加的功能，插在了购物前面
        return "已为你下单外卖"
    elif "买" in text:
        if child_mode:
            return "儿童模式下不能购物"
        return "已加入购物车"
    elif "播放" in text:
        return "开始播放"
    return "抱歉，我没听懂"
```

“外卖”分支加进来之前，**这是好代码**。

## 变化：新功能绕过了儿童锁

公司推出了一款儿童音箱，开启了“儿童模式”：不能购物。写购物功能的同事把这个检查放在了购物分支里面。

后来另一位同事加了“点外卖”。他把新分支插在了购物前面（因为“帮我买个外卖”里也有“买”字，必须先匹配“外卖”）。他没有注意到，儿童模式的检查只在购物分支里。于是，儿童音箱不能买彩笔，却能点外卖（测试 `test_new_branch_bypasses_the_child_check`）。

## 困难在哪里

1. **一条横跨多个功能的规则，被写在了某一个功能的分支里。** “儿童模式下不能花钱”不属于购物，也不属于外卖，它应该在所有花钱的功能**之前**生效。
2. **顺序是隐含的。** 哪个分支在前，决定了谁先有机会处理。这个顺序散落在一长串 `elif` 中，加一个分支，要理解它和前后每个分支的关系。
3. **不同产品要不同的组合。** 厨房音箱没有儿童锁，儿童音箱有；以后车载音箱可能不要购物、要导航。一个函数加越来越多的开关，组合会越来越难管。

## 责任链：一个接一个地问

GoF 对责任链的描述是：**使多个对象都有机会处理请求，从而避免请求的发送者和接收者之间的耦合关系。将这些对象连成一条链，并沿着这条链传递该请求，直到有一个对象处理它为止。**

每个处理者只做一件事：看看这个请求自己能不能处理；能，就给出回应；不能，就交给链上的下一个。

```python
class Handler:
    def __init__(self) -> None:
        self.next: Handler | None = None

    def handle(self, text: str) -> str:
        reply = self.try_handle(text)
        if reply is not None:
            return reply
        if self.next is None:
            return "抱歉，我没听懂"  # 链走到头也没人处理：明确地说出来
        return self.next.handle(text)

    def try_handle(self, text: str) -> str | None:
        return None
```

普通功能是按关键词回应的处理者：

```python
class Keyword(Handler):
    def __init__(self, word: str, reply: str) -> None:
        super().__init__()
        self.word, self.reply = word, reply

    def try_handle(self, text: str) -> str | None:
        return self.reply if self.word in text else None
```

儿童锁也是一个处理者。它“处理”请求的方式是**拒绝**，并且不再往后传：

```python
class ChildLock(Handler):
    """儿童模式：遇到涉及花钱的指令，直接拒绝，不再往后传。"""

    def __init__(self, words: tuple[str, ...] = ("买", "外卖", "支付")) -> None:
        super().__init__()
        self.words = words

    def try_handle(self, text: str) -> str | None:
        if any(w in text for w in self.words):
            return "儿童模式下不能消费"
        return None
```

不同的产品，就是不同的链：

```python
def kitchen_speaker() -> Handler:
    return chain(*common_handlers())


def kids_speaker() -> Handler:
    return chain(ChildLock(), *common_handlers())
```

`chain` 只是把处理者按顺序连起来。儿童音箱把儿童锁放在**最前面**，于是任何涉及花钱的话，在到达购物、外卖之前就被拦住了：

```text
帮我买一盒彩笔 → 儿童模式下不能消费
帮我点个外卖 → 儿童模式下不能消费
明早七点的闹钟 → 好的，闹钟已设好
讲个笑话 → 抱歉，我没听懂
```

以后再加“充话费”功能，只要把“充值”“话费”这类关键词加进儿童锁的列表。新功能本身不需要知道儿童模式的存在。

### 顺序依然重要

责任链没有消除顺序问题，而是把顺序**集中到了组装链的地方**。如果有人把儿童锁放到链的末尾，外卖处理者先匹配上，儿童锁就形同虚设（测试 `test_order_matters`）。

同样，“播放天气预报”这句话既有“播放”又有“天气”，谁先匹配谁回应（测试 `test_first_match_wins`）。在本例的链里，天气在播放之前，所以音箱会报天气。这是不是想要的行为，要由设计链的人决定，并写进测试。

这和[第 13 章](../part-03/13-decorator.md)装饰器的叠加顺序、[第 16 章](../part-03/16-proxy.md)代理的“权限检查放在缓存外面”是同一类问题：**一串对象依次处理请求时，起把关作用的那一个必须排在它要保护的对象前面。**

### 没人处理怎么办

请求可能走完整条链也没有人处理。这是责任链的固有特点，必须明确决定怎么办。本例在链的末端返回“抱歉，我没听懂”（测试 `test_unhandled_request_is_explicit`）。另一些系统会抛出异常，或者记录日志。最不好的做法是什么都不返回，让调用方拿到一个 `None`。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 处理者（Handler） | `Handler` | 定义处理请求的接口，持有下一个处理者 |
| 具体处理者（ConcreteHandler） | `Keyword`、`ChildLock` | 处理自己负责的请求，否则转发 |
| 客户（Client） | 音箱程序 | 把请求交给链的第一个处理者 |

GoF 原书中的责任链，一个请求只由一个处理者处理。实践中还有一种常见的变体：每个处理者都处理一下，再交给下一个，比如 Web 框架的中间件，每一层都可能修改请求或响应。那更接近一串装饰器。本章讨论的是 GoF 原意：**找到第一个能处理的，就停下来。**

## 代价与边界

- **请求的去向不直观。** 读 `kids.handle(text)` 这一行，看不出会被谁处理，要沿着链一个个看。调试时，可以让每个处理者在处理时记一笔日志。
- **不保证一定被处理。** 链的末尾必须有明确的兜底行为。
- **链的组装容易出错，而且检查不出来。** 顺序错了、漏了一环，类型系统都发现不了，只能靠测试。
- **链接是对象上的状态。** `chain()` 会修改每个处理者的 `next` 字段，所以同一个处理者对象不能同时出现在两条链上。本例每次都调用 `common_handlers()` 创建新的处理者，避开了这个问题。
- **性能和链的长度成正比。** 每个请求最坏要问遍所有处理者。对音箱的几十个功能无所谓；如果有上千个规则，就要考虑按关键词建索引，直接找到候选的处理者。

**什么时候不该用**：处理者很少，顺序固定，不需要按产品组合不同的链。开头那串 `if/elif` 只要把儿童锁的检查移到最前面，也能修好这个问题。责任链的价值，在于**处理者需要灵活地增减、重新排列**的时候。

## Python 角度：链就是一个列表

GoF 的责任链是一个链表：每个处理者持有下一个。在 Python 里，更直接的写法是把处理者放进一个**列表**，用循环依次询问：

```python
def respond(text: str, rules: list[Rule]) -> str:
    for rule in rules:
        reply = rule(text)
        if reply is not None:
            return reply
    return "抱歉，我没听懂"
```

处理者也不必是类，一个返回“回应或 `None`”的函数就够了：

```python
def keyword(word: str, reply: str) -> Rule:
    return lambda text: reply if word in text else None


def child_lock(*words: str) -> Rule:
    return lambda text: "儿童模式下不能消费" if any(w in text for w in words) else None
```

两款音箱就是两个列表：

```python
KIDS: list[Rule] = [child_lock("买", "外卖", "支付"), *COMMON]
```

对所有测试用的句子，这个版本和链表版本的回应完全相同（测试 `test_same_answers_as_the_linked_chain`）。

列表的写法有几个好处：

- **顺序一眼可见**：链的全部顺序就是列表的顺序，不用沿着 `next` 一个个找。
- **处理者不需要知道彼此**：没有 `next` 字段，同一个处理者可以出现在多个列表里。
- **没人处理的情况集中在一处**：循环结束后的那一行。

链表的写法在一种情况下更合适：处理者需要**自己决定**是否以及怎样把请求传下去，比如在传给下一个之前修改请求，或者根据结果再做一些事。这时每个处理者都要能控制“下一步”，`next` 字段就有了用处。

## 小结

- 当一个请求可能由多个处理者中的某一个处理，而要依次尝试才知道由谁处理时，责任链把处理者连成一条链，请求沿链传递，直到有人处理。
- 责任链没有消除顺序问题，而是把顺序集中到组装链的地方。起把关作用的处理者必须排在它要保护的处理者前面。
- 必须明确规定没有人处理时的行为。
- 在 Python 里，链常常就是一个处理函数的列表加一个循环，顺序更直观，处理者之间也不需要互相引用。

## 练习

音箱要支持“家长口令”：家长说出“口令 芝麻开门，帮我点个外卖”时，即使在儿童模式下也允许消费。

1. 这个功能应该怎样加入链里？是修改 `ChildLock`，还是新增一个处理者？
2. 如果新增一个处理者，它应该排在儿童锁的前面还是后面？它处理完之后，请求应该停下来，还是继续往后传？
3. 在“处理者是函数、链是列表”的写法里，这个需求会遇到什么困难？

**思路提示**：口令处理者需要在儿童锁之前识别口令，然后让请求（去掉口令部分之后）**跳过儿童锁**，继续交给后面的处理者。这超出了“找到一个就停”的简单责任链：处理者需要修改请求，并且决定从链的哪个位置继续。一种简单的做法是修改 `ChildLock`，让它在发现正确口令时不拦截，返回 `None`。这样不改变链的结构，但儿童锁要知道口令。在函数列表的写法里，函数只能返回“回应或 `None`”，无法表达“修改请求后继续”，需要改变规则的签名（比如返回一个修改后的请求）。这个练习显示了简单责任链的边界：一旦处理者之间需要传递修改后的请求，就更接近中间件或装饰器的结构了。

完整代码：
- [`examples/ch22_speaker_v1.py`](../../examples/ch22_speaker_v1.py)：一串 `if/elif`（含错误）
- [`examples/ch22_chain.py`](../../examples/ch22_chain.py)：处理者链与两种音箱
- [`examples/ch22_pythonic.py`](../../examples/ch22_pythonic.py)：函数列表

测试：[`tests/test_ch22_chain.py`](../../tests/test_ch22_chain.py)。
