# 第 03 章　Python 组织程序的基本工具

> 本章要回答：函数、类、组合、继承、抽象基类、协议分别解决什么问题？什么时候函数已经足够？在它们下面，Python 的名字、对象和引用是怎样工作的？

后面讲到的每一个设计模式，在 Python 里最终都要用这几样工具实现。如果不清楚每样工具擅长什么，就容易出现两种极端：要么什么都写成类，一个简单计算也要套三层；要么只会写函数，状态和规则散落各处。

这一章用同一个小任务，依次试一遍这些工具。任务是：一个点评网站要在发布用户评论前做清洗。

```python
comment = "  这家店的  咖啡 太难喝了，简直是垃圾！！  "
```

要做的事包括：合并多余空白、屏蔽不文明用词、过长时截断。

## 函数：只看输入，只给输出

最先写出来的，应该是函数：

```python
def strip_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"
```

`strip_spaces(comment)` 得到 `"这家店的 咖啡 太难喝了，简直是垃圾！！"`。

函数是 Python 里最轻的组织单位。只要一个处理满足“给定输入就能算出结果、不需要记住任何东西”，就先写成函数。它容易读、容易测试，也容易被别的代码复用。[第 01 章](01-data-and-processing.md)说过，这样的函数是最好理解的代码。

## 函数也是数据

在 Python 里，函数本身就是一个对象：可以放进列表、存进字典、当作参数传递。于是“依次执行几个清洗步骤”可以写得很直接：

```python
def apply_all(text: str, steps: list[Callable[[str], str]]) -> str:
    for step in steps:
        text = step(text)
    return text


basic_steps = [strip_spaces, partial(truncate, limit=12)]
```

`truncate` 需要两个参数，但列表里的每一步只接收文本。`functools.partial(truncate, limit=12)` 把 `limit` 预先填好，得到一个只需要文本的新函数。`apply_all(comment, basic_steps)` 的结果是 `"这家店的 咖啡 太难喝…"`。

这个小技巧值得记住：**很多看起来需要“一个类加一个配置字段”的场合，一个 `partial` 或一个闭包就够了。** [第 28 章](../part-05/28-functions-as-design-tools.md)会专门讨论函数作为设计工具的用法。

## 类：数据、处理和状态要放在一起

屏蔽不文明用词时，运营同事还想知道“一共屏蔽了多少处”，用来观察社区氛围。现在处理过程需要**记住**一个不断累加的数字。这正是类适合的地方：

```python
class Censor:
    def __init__(self, words: list[str]) -> None:
        self.words = words
        self.replaced = 0  # 状态：累计屏蔽了多少处

    def __call__(self, text: str) -> str:
        for word in self.words:
            count = text.count(word)
            if count:
                self.replaced += count
                text = text.replace(word, "*" * len(word))
        return text
```

`Censor` 把三样东西放在一起：词表（配置数据）、替换逻辑（处理）、累计次数（状态）。它实现了 `__call__`，所以它的对象可以像函数一样被调用：`censor(text)`。这样它就能和普通函数一起放进步骤列表。

什么时候该写类，而不是函数？一个实用的判断是：**当你发现要在多次调用之间记住东西，或者好几个函数总是一起操作同一份数据时。** 如果只是想“预先设好一个参数”，`partial` 往往更省事。

## 继承：在父类基础上改写一部分

假设我们先有一个通用的清洗器，后来需要一个“还会屏蔽脏话”的版本。继承是很自然的第一反应：

```python
class Cleaner:
    def __init__(self, limit: int) -> None:
        self.limit = limit

    def clean(self, text: str) -> str:
        return truncate(strip_spaces(text), self.limit)


class CensoringCleaner(Cleaner):
    def __init__(self, limit: int, words: list[str]) -> None:
        super().__init__(limit)
        self.censor = Censor(words)

    def clean(self, text: str) -> str:
        return super().clean(self.censor(text))
```

`CensoringCleaner(20, ["垃圾"]).clean(comment)` 得到 `"这家店的 咖啡 太难喝了，简直是**！！"`。子类复用了父类的空白处理和截断，只在前面加了一步屏蔽。

继承在这里工作得不错。但想想接下来可能出现的需求：英文评论要转小写；某些频道不截断；某些频道不屏蔽……每个选项都是“要或不要”，三个选项就有 2 × 2 × 2 = 8 种组合。如果每种组合都派生一个子类，类的数量会成倍增长，而且很多子类之间只差一行。

继承表达的是“A 是一种 B，并且共享 B 的大部分行为”。当变化来自**几个可以自由搭配的部件**时，继承就开始吃力了。

## 组合：把部件装在一起

另一种思路是：不派生新的类，而是把需要的步骤**装进**一个对象里。

```python
class Pipeline:
    def __init__(self, *steps: Callable[[str], str]) -> None:
        self.steps = list(steps)

    def __call__(self, text: str) -> str:
        return apply_all(text, self.steps)
```

现在任何一种组合都只是“列出不同的步骤”：

```python
only_censor = Pipeline(strip_spaces, Censor(["垃圾"]))
for_english = Pipeline(strip_spaces, Censor(["垃圾"]), Lowercase(), partial(truncate, limit=20))
```

`for_english("  GREAT 咖啡，垃圾服务  ")` 得到 `"great 咖啡，**服务"`。八种组合不需要八个类。（`Lowercase` 在下一节定义，它只是把文本转成小写。）

“优先使用组合而不是继承”是一句常被引用的建议。它的意思不是“不要用继承”，而是：**如果变化来自可以独立替换、自由搭配的部件，用组合；如果真的是“一种更具体的同类东西”，而且共享大量行为，继承才合适。** 后面的桥接（[第 11 章](../part-03/11-bridge.md)）、装饰器（[第 13 章](../part-03/13-decorator.md)）、策略（[第 17 章](../part-04/17-strategy.md)）都建立在组合之上。

## 抽象基类：要求实现者必须提供某些方法

当好几个类要扮演同一个角色时，我们可能希望明确规定：“凡是清洗步骤，都必须实现 `__call__`”。标准库 `abc` 提供了这种约束：

```python
class Step(ABC):
    @abstractmethod
    def __call__(self, text: str) -> str:
        """接收文本，返回处理后的文本。"""


class Lowercase(Step):
    def __call__(self, text: str) -> str:
        return text.lower()


class Forgetful(Step):
    """忘了实现 __call__：创建对象时就会报错。"""
```

`Lowercase()` 可以正常创建；`Forgetful()` 在创建时就报 `TypeError`，提醒你漏写了方法。错误出现得越早，越容易定位。

抽象基类的代价是：**必须显式继承它**。`strip_spaces` 这个普通函数明明也能完成“接收文本、返回文本”的工作，但 `isinstance(strip_spaces, Step)` 是 `False`。如果你的系统里大部分步骤都是普通函数，强行要求它们继承 `Step` 就很别扭。

## 协议：只关心“能不能这样用”

`typing.Protocol` 换了一个角度：不问“你继承了谁”，只问“你有没有这个方法”。

```python
@runtime_checkable
class TextStep(Protocol):
    def __call__(self, text: str) -> str: ...


def run_steps(text: str, steps: list[TextStep]) -> str:
    return apply_all(text, steps)
```

协议里方法体写的 `...` 是 Python 的合法语法，表示“这里只声明形状，不提供实现”。

现在普通函数、`Censor` 对象、`Lowercase` 对象都符合 `TextStep`，它们谁也不需要继承 `TextStep`。类型检查器（如 mypy）会在你传入一个不符合的对象时报错；加上 `@runtime_checkable` 后，`isinstance` 也能在运行时做粗略检查。

要注意“粗略”二字。运行时检查**只看有没有这个方法，不看参数和返回值**：`isinstance(print, TextStep)` 也是 `True`，因为 `print` 也能被调用。协议主要服务于读代码的人和类型检查器，不是运行时的安全网。[第 29 章](../part-05/29-types-and-interfaces.md)会更详细地讨论 `Protocol`、`ABC` 和类型标注的作用与局限。

## 怎么选

| 你遇到的情况 | 先考虑 |
|---|---|
| 给定输入就能算出结果，不需要记住任何东西 | 函数 |
| 只是想预先设好几个参数 | `functools.partial` 或闭包 |
| 要在多次调用之间记住东西，或几个函数总在操作同一份数据 | 类 |
| 几个可以独立替换、自由搭配的部件 | 组合 |
| 确实是“一种更具体的同类东西”，共享大量行为 | 继承 |
| 必须保证实现者提供某些方法，而且实现者都是你写的类 | 抽象基类 |
| 只关心“能这样用”，希望普通函数也能参与 | 协议 |

这张表是起点，不是规则。真实代码常常混用：`Pipeline` 是一个类，里面装的是函数和对象；`Censor` 是一个类，却通过 `__call__` 伪装成函数。

## 地基：名字、对象与引用

前面几节讲的都是“用什么工具组织代码”，上面的表也已经给出了选择的起点。最后来看一个更底层的问题，它藏在本章每一段代码里：`Censor` 记住的那份词表，到底是谁的？

这个问题不属于任何一种“工具”，而是所有工具共同的地基。后面的许多模式，原型、单例、享元、观察者、备忘录，都直接建立在它上面。这里不会把 Python 的对象模型讲全，只讲后面真正要用到的几件事。

### 赋值和传参都不复制对象

论坛和商城各有一个屏蔽器，开始时用同一份词表。后来论坛想多屏蔽一个词：

```python
def shared_word_list() -> tuple[Censor, Censor]:
    words = ["垃圾"]
    forum = Censor(words)
    shop = Censor(words)
    forum.words.append("难喝")  # 只想给论坛多屏蔽一个词
    return forum, shop
```

结果商城也开始屏蔽“难喝”了：`shop("咖啡难喝")` 得到 `"咖啡**"`，`forum.words is shop.words` 是 `True`。

原因在 `Censor.__init__` 里那一行 `self.words = words`。在 Python 里，**名字只是贴在对象上的标签**。赋值、传参、存进属性，都只是多贴一张标签，不会复制对象。从头到尾只有一个列表，`words`、`forum.words`、`shop.words` 是贴在它上面的三张标签。`append` 修改的是这个列表本身，所以从哪张标签看过去，都看到了变化。

这不一定是错误。如果本意就是“两个频道共用一份词表，改一处全都生效”，这正是想要的行为。问题在于，**共享应该是一个有意的决定，而不是赋值时顺手带来的副作用。**

### 在边界上复制，或者保存不可变的数据

如果每个屏蔽器应该有自己的词表，就在接收数据的地方复制一份。更彻底的做法是保存成不可变的元组。这里用一个子类，只改“怎样保存词表”这一处，屏蔽逻辑原样继承：

```python
class OwnWordsCensor(Censor):
    def __init__(self, words: list[str]) -> None:
        super().__init__(words)
        self.words = tuple(words)  # 自己的副本，而且不能被原地修改
```

现在要给论坛加词，就不能再 `append` 了，元组没有这个方法。只能造一个新元组，让论坛的标签贴过去：

```python
def separate_word_lists() -> tuple[OwnWordsCensor, OwnWordsCensor]:
    words = ["垃圾"]
    forum = OwnWordsCensor(words)
    shop = OwnWordsCensor(words)
    forum.words = (*forum.words, "难喝")  # 让 forum.words 指向一个新元组
    return forum, shop
```

论坛的词表是 `("垃圾", "难喝")`，商城的仍然是 `("垃圾",)`。

这里有两种完全不同的“改变”：

- **修改对象**：`list.append`、给字典加键、改属性。对象还是那个对象，所有指向它的名字都会看到变化。
- **让名字指向别的对象**：`forum.words = ...`。原来的对象没有动，只有这一个名字换了目标。

不可变对象（数字、字符串、元组、`frozen=True` 的数据类）只允许第二种改变，所以可以放心地共享。可变对象（列表、字典、集合、普通类的实例）被几处同时引用时，就要想清楚是谁在改、谁会受影响。

回头看本章的 `Pipeline`，它写的是 `self.steps = list(steps)`，在接收时就复制了一份。调用方之后再修改自己的步骤列表，管道不受影响。

### 身份与相等

既然“是不是同一个对象”这么重要，Python 就提供了两种不同的比较：

```python
def equal_but_not_same() -> tuple[bool, bool]:
    a = ["垃圾", "难喝"]
    b = ["垃圾", "难喝"]
    return a == b, a is b
```

结果是 `(True, False)`。`==` 问的是**内容一样吗**，`is` 问的是**是同一个对象吗**。这两个列表内容相同，却是两个独立的对象，改其中一个，另一个不受影响。

判断“共享了没有”要用 `is`。判断“值对不对”要用 `==`。不要用 `is` 比较数字和字符串的值：小整数、短字符串有时恰好是同一个对象，那是 CPython 的实现细节，不是语言的保证。

### 两个名字，一个对象

同一件事反过来，就成了一种有用的能力：

```python
def counting_through_a_pipeline() -> int:
    censor = Censor(["垃圾"])
    clean = Pipeline(strip_spaces, censor)
    clean("垃圾服务")
    clean("又是垃圾")
    return censor.replaced  # 管道里的那个，就是手里的这个
```

返回 `2`。我们把 `censor` 交给了管道，自己手里还留着一张标签。管道每次调用它，累加的都是同一个对象的计数，我们随时都能读到。**把一个对象交给别人，就等于和别人共享了它的状态。** 观察者模式里“目标持有订阅者”，中介者里“各方都持有同一个中介”，靠的都是这一点。

### 一个常见的坑：可变的默认参数

```python
def remember_bad(comment: str, history: list[str] = []) -> list[str]:
    history.append(comment)  # 每次调用都往同一个列表里加
    return history
```

`remember_bad("第一条")` 和 `remember_bad("第二条")` 返回的是同一个列表，里面有两条评论。默认值 `[]` 只在**定义函数时**求值一次，之后每次不传参数的调用，用的都是这一个列表。标准写法是用 `None` 当默认值，在函数里面再创建新列表：

```python
def remember(comment: str, history: list[str] | None = None) -> list[str]:
    history = [] if history is None else history
    history.append(comment)
    return history
```

### 函数、类、模块都是对象

前面说过“函数也是数据”。其实类也一样：类本身是一个对象，可以放进字典；调用它，就得到一个新的实例。

```python
STEP_TYPES = {"lower": Lowercase, "censor": Censor}


def make_step(kind: str, *args):
    return STEP_TYPES[kind](*args)
```

`make_step("lower")("ABC")` 得到 `"abc"`。这已经是[第 05 章](../part-02/05-factory-method.md)“简单工厂”的雏形：根据一个名字决定创建哪种对象。

模块也是对象。Python 第一次 `import` 一个模块时执行它，之后再导入，拿到的都是同一个模块对象。[第 09 章](../part-02/09-singleton.md)会用到这一点。

还有一点值得先记下：`censor(text)`、`len(x)`、`for item in x` 这类写法，Python 是通过对象的特殊方法（`__call__`、`__len__`、`__iter__`）来执行的，而且是到对象的**类型**上去找。`Censor` 能像函数一样调用，就是因为它的类定义了 `__call__`。[第 16 章](../part-03/16-proxy.md)和[第 23 章](../part-04/23-iterator.md)会再遇到这条规则。

### 这块地基在后面哪里用到

| 本节的概念 | 后面在哪里变得要紧 |
|---|---|
| 赋值不复制，可变对象被共享 | [第 08 章](../part-02/08-prototype.md)原型：浅拷贝让几份计划改到一起 |
| 身份与相等，模块只导入一次 | [第 09 章](../part-02/09-singleton.md)单例：“同一个对象”到底指什么 |
| 不可变对象可以放心共享 | [第 15 章](../part-03/15-flyweight.md)享元：共享的部分必须不可变 |
| 两个名字，一个对象 | [第 18 章](../part-04/18-observer.md)观察者、[第 24 章](../part-04/24-mediator.md)中介者：靠共享引用协作 |
| 修改对象与换一个对象 | [第 25 章](../part-04/25-memento.md)备忘录：快照里混进可变对象，就不再是快照 |
| 特殊方法在类型上查找 | [第 16 章](../part-03/16-proxy.md)代理、[第 23 章](../part-04/23-iterator.md)迭代器 |

读这些章节时如果觉得某个现象“说不通”，不妨回到这一节，问一句：**这里有几个对象？有几个名字指着它？谁在修改它？**

## 小结

- 先写函数。函数是 Python 里最轻、最容易测试的组织单位，而且函数本身就是可以传递的数据。
- 需要记住状态、或者数据和处理总是成对出现时，再写类。
- 变化来自可以自由搭配的部件时，用组合；只有真正的“同类细分”才用继承。
- 抽象基类在创建对象时就检查缺失的方法，但要求显式继承；协议只看“有没有这个方法”，普通函数也能符合，运行时检查只是粗略的。
- 许多设计模式，就是这几样工具在特定问题下的固定搭配。
- 名字只是指向对象的标签，赋值和传参都不复制对象。可变对象被几处引用时，一处修改处处可见；共享应该是有意的决定。需要独立时，在边界上复制，或者保存不可变的数据。`is` 判断是否同一个对象，`==` 判断内容是否相等。

## 练习

评论清洗又来了一个需求：把评论里的手机号码打码，例如 `13812345678` 变成 `138****5678`。

1. 你会把它写成函数、带 `__call__` 的类，还是 `Step` 的子类？
2. 如果运营同事也想知道“一共打码了多少个号码”，你的选择会变吗？
3. 它需要和 `Censor` 共享一个父类吗？

**思路提示**：只是打码，一个用 `re.sub` 的函数就够了，可以直接放进 `Pipeline`。要统计次数，就需要状态，写成和 `Censor` 类似的类。两者都只需要满足“接收文本、返回文本”这个协议，不需要共同的父类：它们共享的是**用法**，不是**实现**。

完整代码：
- [`examples/ch03_tools.py`](../../examples/ch03_tools.py)：函数、类、继承、组合、抽象基类、协议
- [`examples/ch03_objects.py`](../../examples/ch03_objects.py)：名字、对象与引用

测试：[`tests/test_ch03_tools.py`](../../tests/test_ch03_tools.py)、[`tests/test_ch03_objects.py`](../../tests/test_ch03_objects.py)。
