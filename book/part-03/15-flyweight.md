# 第 15 章　享元 Flyweight

> 本章要回答：当程序里有大量对象，每个都保存着一份同样的数据时，哪些部分可以共享？共享真的能省下内存吗？什么情况下根本不值得这样做？

享元是一个关于**内存**的模式，所以这一章会比其他章节多一件事：**测量**。凡是“省了多少”的说法，都应该由实际测量支撑，而不是凭感觉。本章所有关于内存的结论，都有对应的测试，而且测试只断言相对大小（“比原来小”），不断言具体字节数，因为具体数字在不同的 Python 版本和平台上都不一样。

## 眼前的任务

一座城市的地铁公司要分析一天的闸机刷卡记录。闸机导出的是文本，每行一条：卡号、当天第几分钟、车站、线路、票价区。

```text
C0000,0,西直门,2号线,1
C0001,1,国贸,1号线,1
C0002,2,望京,14号线,2
```

一天有几十万条。示例代码用 2 万条模拟，车站只有 5 个。

## 不用模式的写法

每行解析成一个数据类对象：

```python
@dataclass
class Tap:
    card: str
    minute: int
    station: str
    line: str
    zone: int


def parse(lines: list[str]) -> list[Tap]:
    taps = []
    for text in lines:
        card, minute, station, line, zone = text.split(",")
        taps.append(Tap(card, int(minute), station, line, int(zone)))
    return taps
```

**这是好代码。** 清楚、直接，大多数时候完全够用。

## 变化：数据量变大了

分析范围从一天扩大到一个月，记录数从几十万变成上千万，程序开始占用大量内存，在分析服务器上被系统强行终止。

看一看这些对象里存的是什么。2 万条记录、5 个车站，每个车站平均出现 4000 次。“西直门”“2号线”这两段文字，在内存里是不是只存了一份？

```text
两条记录的车站名是同一个字符串对象吗？ False
```

**不是。** `text.split(",")` 每次都会创建新的字符串对象。第 0 行和第 5 行都是“西直门”，内容相同，却是两个不同的对象。2 万条记录，就有 2 万个“西直门”“国贸”……的副本（测试 `test_every_record_has_its_own_strings`）。

## 困难在哪里

每条记录里的数据分成两类：

- **每条记录各不相同的**：卡号、时间。
- **大量记录完全相同的**：车站名、线路、票价区。它们其实描述的是“车站”，而不是“这一次刷卡”。

第二类数据被复制了成千上万份。如果能让所有在西直门刷卡的记录**共享同一个**“西直门车站”对象，这部分的内存就只需要一份。

## 享元：共享不变的部分

GoF 对享元的描述是：**运用共享技术有效地支持大量细粒度的对象。**

GoF 把对象的状态分成两部分：

- **内部状态**（intrinsic state）：可以共享的部分，与使用场合无关。本例中是车站的名称、线路、票价区。
- **外部状态**（extrinsic state）：随场合变化、不能共享的部分。本例中是卡号和时间。

共享的部分单独成为一个对象，而且**必须是不可变的**。原因很简单：几千条记录引用同一个车站对象，如果有人改了它，所有记录都会跟着变。

```python
@dataclass(frozen=True, slots=True)
class Station:
    """内部状态：同一个车站对所有记录都一样，而且不可修改。"""

    name: str
    line: str
    zone: int
```

谁来保证“同一个车站只创建一次”？一个**享元工厂**：先查有没有，有就返回已有的，没有才创建：

```python
class StationPool:
    """享元工厂：同样的车站只创建一次。"""

    def __init__(self) -> None:
        self._stations: dict[tuple[str, str, int], Station] = {}

    def get(self, name: str, line: str, zone: int) -> Station:
        key = (name, line, zone)
        station = self._stations.get(key)
        if station is None:
            station = self._stations[key] = Station(name, line, zone)
        return station
```

刷卡记录只保存外部状态，加上对共享车站的引用：

```python
@dataclass(slots=True)
class Tap:
    """外部状态：每条记录各不相同的部分，加上对共享车站的引用。"""

    card: str
    minute: int
    station: Station
```

解析 2 万条记录之后，工厂里只有 5 个车站对象，所有记录引用的都是这 5 个之一（测试 `test_stations_are_shared`）。信息一点没少：每条记录的卡号、时间、车站名、线路、票价区，和原来逐一相同（测试 `test_same_information`）。试图修改共享的车站会立即报错（测试 `test_shared_state_cannot_be_changed`）。

### 测量

省了多少内存？用标准库的 `tracemalloc` 测：记下构造前后 Python 分配的内存差。

```python
def measure(build: Callable[[], object]) -> int:
    """返回 build() 构造出的对象在保留状态下占用的内存（字节），由 tracemalloc 测得。"""
    tracemalloc.start()
    try:
        before = tracemalloc.get_traced_memory()[0]
        result = build()
        after = tracemalloc.get_traced_memory()[0]
    finally:
        tracemalloc.stop()
    del result
    return after - before
```

运行 `python -m examples.ch15_flyweight` 可以看到你机器上的数字。在我们测试过的 Python 3.11 和 3.12 上，共享车站的版本占用的内存明显少于原来的版本，但具体字节数两个版本并不相同。测试 `test_measured_memory_is_lower` 只断言“更小”这一个事实。

**不要把任何一次测量的具体数字当作普遍结论。** 它取决于 Python 的版本、平台、字符串的长度和内容（纯 ASCII 字符串和含中文的字符串内部表示不同）、对象的字段数。需要做决定时，用自己的真实数据测。

### 省下的内存从哪里来

仔细看，这个版本其实同时做了两件事：

1. 车站信息被**共享**了；
2. `Tap` 用了 `slots=True`，字段也从 5 个减少到 3 个。

两者各贡献了多少？可以把它们拆开测量。只做第一件事、不改 `Tap` 类的写法，是用 `sys.intern` 让相同内容的字符串共享同一个对象：

```python
def parse_interned(lines: list[str]) -> list[Tap]:
    """不改记录的类，只让相同的字符串共享同一个对象。"""
    taps = []
    for text in lines:
        card, minute, name, line, zone = text.split(",")
        taps.append(Tap(card, int(minute), sys.intern(name), sys.intern(line), int(zone)))
    return taps
```

测试 `test_interning_alone_helps` 测得的大小顺序是：

```text
原来的版本  >  只共享字符串（sys.intern）  >  享元版本（共享车站 + __slots__）
```

在本例中，**单是共享字符串就带来了很大一部分节省**，`__slots__` 和减少字段又省下了一部分。这说明：享元的“思想”（共享重复的不可变数据）是省内存的关键，而“享元工厂加一个新类”只是实现这种共享的一种方式。在 Python 里，对于重复的字符串，`sys.intern` 是更轻的实现。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 享元（Flyweight） | `Station` | 保存内部状态，不可变，可以被共享 |
| 享元工厂（FlyweightFactory） | `StationPool` | 创建并管理享元，保证相同的享元只有一个 |
| 客户（Client） | `Tap` 与 `parse` | 保存外部状态，引用享元 |

GoF 原书中的享元还会在调用时接收外部状态作为参数（例如“在这个位置画这个字符”）。本例的车站不需要外部状态就能回答自己的问题，所以省略了这一部分。

## 代价与边界

- **共享的部分必须不可变。** 这是硬性约束。如果某天需要“修改某个车站的票价区”，不能直接改共享对象，而要创建一个新的车站对象，再让需要的记录指向它。
- **工厂本身也占内存，而且可能一直增长。** `StationPool` 会记住它创建过的每一个车站。车站只有几百个，没有问题；如果被共享的东西种类非常多、而且不断出现新的，工厂会变成一个只增不减的缓存。
- **代码变得间接。** 原来 `tap.station` 就是车站名，现在要写 `tap.station.name`。数据的结构也不再是“一行一个扁平记录”，导出时需要重新展开。
- **只有在数量巨大且重复度高时才有意义。** 如果车站有几万个，每个只出现几次，共享几乎省不了什么，反而多了一个工厂。

**什么时候不该用**：

- 对象数量不大。几千个对象，内存从来不是问题。
- 你**根本不需要同时在内存里保留所有对象**。这是最常被忽视的一点，见下一节。
- 没有测量过。如果没有证据表明内存是瓶颈，也没有测过改动的效果，就不要为了省内存而改变数据结构。

## Python 角度：先问“需不需要这么多对象”

面对“对象太多、内存不够”，Python 程序员首先应该问的不是“怎么共享”，而是“**为什么要把它们全部留在内存里**”。

如果分析的目标是“每个车站有多少人次进站”，那么根本不需要为每一行创建一个对象：

```python
def taps_per_station(lines: list[str]) -> Counter[str]:
    """如果只需要统计，边读边数，不必为每一行保留一个对象。"""
    counts: Counter[str] = Counter()
    for text in lines:
        counts[text.split(",")[2]] += 1
    return counts
```

边读边统计，内存里只有 5 个计数器。如果数据来自文件，逐行读取（`for line in file`），整个文件甚至不需要一次读进内存。第 23 章讨论迭代器时还会回到这一点。

当确实需要保留大量对象时，Python 提供了几种比完整享元更轻的工具：

- **`sys.intern`**：让内容相同的字符串共享同一个对象，适合大量重复的短字符串，比如本例的车站名、日志里的级别名称。
- **`__slots__`**（或 `@dataclass(slots=True)`）：去掉每个实例的 `__dict__`，减少每个对象的固定开销。它和共享无关，但常常和享元一起出现，因为两者解决的是同一个问题。
- **`functools.cache`**：一个现成的享元工厂。相同参数的调用返回同一个对象：

```python
@cache
def station(name: str, line: str, zone: int) -> Station:
    return Station(name, line, zone)
```

`station("国贸", "1号线", 1) is station("国贸", "1号线", 1)` 为 `True`。它的缓存同样只增不减，和 `StationPool` 一样需要注意。

顺便一提：CPython 自己也会在某些情况下共享对象，比如小整数、某些字符串常量。这些是**实现细节**，不同版本之间可能变化，不能作为程序正确性或性能的依据。本例的票价区 `zone` 是小整数，即使不共享，它对内存的影响也微乎其微。

## 小结

- 当大量对象各自保存一份相同的数据时，享元把这部分数据（内部状态）抽出来成为不可变的共享对象，由一个工厂保证每种只有一个；各不相同的部分（外部状态）仍留在各自的对象里。
- 享元是为了省内存。是否值得，要用真实数据**测量**，并且只依据测量得出的相对结论；不要引用一个脱离环境的字节数。
- 在本例中，共享字符串本身就带来了很大一部分节省。Python 里，`sys.intern`、`__slots__`、`functools.cache` 往往能以更小的代价达到类似效果。
- 更根本的问题是：是否真的需要同时保留这么多对象。只需要统计时，边读边处理通常比任何共享技巧都有效。

## 练习

2 万条记录里只有 500 张不同的卡，每张卡平均刷 40 次。

1. 卡号应该算内部状态还是外部状态？能不能像车站一样共享？
2. 如果用 `sys.intern` 共享卡号字符串，你预计内存会怎样变化？请修改 `parse_interned`，用 `measure` 实际测一下，再和你的预计对比。
3. 如果真实的数据是一个月、上千万条记录、上百万张不同的卡，结论会改变吗？

**思路提示**：卡号是“这次刷卡是谁刷的”，属于每条记录的外部状态；但它的**值**大量重复，所以字符串本身可以共享。这说明“内部／外部状态”是从对象的含义来划分的，而“能不能共享”看的是值的重复程度，两者不完全是一回事。卡号 `C0000` 是短的 ASCII 字符串，单个对象本来就不大，共享后能省多少，要测了才知道，不要凭感觉下结论。第 3 问：卡的种类越多、每张卡出现的次数越少，共享的收益就越小，而 `sys.intern` 内部维护的表会越来越大。重复度是决定享元是否值得的关键数字。

完整代码：
- [`examples/ch15_taps_v1.py`](../../examples/ch15_taps_v1.py)：每条记录各存一份车站信息
- [`examples/ch15_flyweight.py`](../../examples/ch15_flyweight.py)：共享的 `Station`、享元工厂与测量函数
- [`examples/ch15_pythonic.py`](../../examples/ch15_pythonic.py)：`sys.intern`、`functools.cache`、边读边统计

测试：[`tests/test_ch15_flyweight.py`](../../tests/test_ch15_flyweight.py)。
