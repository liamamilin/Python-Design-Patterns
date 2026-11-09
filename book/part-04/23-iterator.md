# 第 23 章　迭代器 Iterator

> 本章要回答：怎样逐个访问一组元素，而不必关心它们存放在哪里、怎样取回？Python 已经把迭代器做进了语言，我们还需要知道什么？

迭代器是 GoF 23 种模式中，被 Python **完全吸收进语言**的一个。每一个 `for` 循环背后都是迭代器协议。所以这一章不是教你“怎样实现迭代器模式”，而是讲清楚：Python 的迭代器协议是什么，什么时候需要自己写一个迭代器，以及“按需取用”能带来什么。

## 眼前的任务

一个家庭照片整理程序，要从云相册里找照片。云相册的接口是**分页**的：每次请求返回一页，每页 20 张，翻过最后一页时返回空列表。

```python
    def get_page(self, page: int) -> list[dict]:
        self.requests += 1
        start = (page - 1) * self.page_size
        stop = min(start + self.page_size, self.total)
        return [{"id": i, "place": PLACES[i % len(PLACES)], "year": 2020 + i % 5} for i in range(start, stop)]
```

（示例用一个模拟的接口代替真实的网络请求，`requests` 记录一共请求了几次。）

用户的问题是：“找一张在成都拍的照片。”

## 不用模式的写法

先把所有页取回来，拼成一个列表，再在列表里找：

```python
def all_photos(api: FakePhotoApi) -> list[dict]:
    photos: list[dict] = []
    page = 1
    while True:
        batch = api.get_page(page)
        if not batch:
            break
        photos += batch
        page += 1
    return photos
```

相册只有几十张照片时，**这是好代码**：简单，取回来的列表可以反复使用。

## 变化：相册变大了

相册里有 200 张照片，10 页。第一张成都的照片就在第 1 页，可程序仍然把 10 页全部取了回来，外加一次确认“没有更多了”的空请求，一共 11 次网络请求（测试 `test_fetches_every_page_even_for_the_first_match`）。

如果相册有两万张照片，就是一千次请求，而用户只想看一张。如果用户只想看“最近的 25 张”，也是一样。更糟的是，所有照片的信息都要同时放在内存里。

## 困难在哪里

`all_photos` 把两件事绑在了一起：

1. **怎样取得下一张照片**：要知道当前在第几页、这一页取完了没有、什么时候算结束。
2. **拿到照片之后做什么**：找成都的、数一数、取前 25 张。

因为第 1 件事被写成了“一次全部取完”，第 2 件事无论多么简单，都要等全部取完才能开始。我们希望的是：**调用方要一张，就给一张；需要翻页时，才去请求下一页。** 至于怎样翻页，调用方不必知道。

## 迭代器：按需给出下一个元素

GoF 对迭代器的描述是：**提供一种方法顺序访问一个聚合对象中的各个元素，而又不需暴露该对象的内部表示。**

GoF 原书中的迭代器接口有四个操作：`First`、`Next`、`IsDone`、`CurrentItem`。Python 把它简化成了一个**协议**，只有两个方法：

- `__iter__()`：返回迭代器本身；
- `__next__()`：返回下一个元素；没有更多元素时，抛出 `StopIteration`。

`for` 循环、`list()`、`next()`、生成器表达式……Python 里所有“逐个取元素”的地方，都是在调用这两个方法。只要一个对象实现了它们，就可以用在所有这些地方。

把“翻页”的细节藏进一个迭代器：

```python
class PhotoIterator:
    """实现 Python 的迭代器协议：__iter__ 返回自己，__next__ 给出下一张或抛出 StopIteration。"""

    def __init__(self, api: FakePhotoApi) -> None:
        self.api = api
        self.page = 0
        self.buffer: deque[dict] = deque()
        self.finished = False

    def __iter__(self) -> PhotoIterator:
        return self

    def __next__(self) -> dict:
        if not self.buffer:
            if self.finished:
                raise StopIteration
            self.page += 1
            self.buffer.extend(self.api.get_page(self.page))
            if not self.buffer:
                self.finished = True
                raise StopIteration
        return self.buffer.popleft()
```

它在内部保存一页的缓冲区。缓冲区空了，才去请求下一页；请求到空页，就记下“已经结束”，之后再被调用也不会再发请求（测试 `test_stop_iteration_is_sticky`）。

调用方的代码几乎没变，只是把 `all_photos(api)` 换成了 `PhotoIterator(api)`：

```python
    first = next(p for p in PhotoIterator(api) if p["place"] == "成都")
```

```text
{'id': 1, 'place': '成都', 'year': 2021} 请求次数： 1
```

找到第一张成都的照片，只请求了 1 次（测试 `test_fetches_only_what_is_needed`）。如果完整地遍历一遍，仍然是 11 次请求，得到全部 200 张，一张不多、一张不少（测试 `test_full_iteration_gives_everything_once`）。迭代器没有让总的工作变少，它让调用方**只为自己用到的部分付出代价**。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 迭代器（Iterator） | Python 的迭代器协议 | `__next__` 给出下一个元素，`StopIteration` 表示结束 |
| 具体迭代器（ConcreteIterator） | `PhotoIterator` | 记住遍历到了哪里（第几页、缓冲区） |
| 聚合（Aggregate） | 云相册接口 | 存放元素，但不暴露它怎样分页 |

## 代价与边界

- **迭代器只能走一遍。** `PhotoIterator` 遍历完之后就结束了，再用它得到的是空的。想要再遍历一次，要重新创建一个。这是很多“为什么第二次循环什么都没有”的错误的来源（下一节会再谈）。
- **不能随机访问，也不知道总数。** 想要“第 150 张”，只能从头数过去；想知道“一共有几张”，只能全部遍历一遍。如果经常需要这些操作，取回一个列表反而更合适。
- **遍历过程中，数据可能变化。** 如果用户在遍历到第 3 页时删除了第 1 页的一张照片，后面的页会整体前移一位，迭代器会漏掉一张。这是分页接口的固有问题，迭代器解决不了，只能由接口本身提供稳定的游标。
- **错误发生的时机推迟了。** 网络错误不会在创建迭代器时出现，而是在遍历到需要翻页的那一刻才出现，可能在调用方的某个循环中间。

**什么时候不该用**：数据量小，或者调用方需要反复访问、随机访问、知道总数。一次取回一个列表，简单直接。

## Python 角度：生成器、可迭代对象和 `itertools`

### 生成器函数

自己写一个实现 `__iter__` 和 `__next__` 的类，需要手动管理“遍历到哪里了”。Python 提供了更省事的写法：**生成器函数**。函数里只要出现 `yield`，调用它就会返回一个迭代器：

```python
def iter_photos(api: FakePhotoApi) -> Iterator[dict]:
    page = 1
    while batch := api.get_page(page):
        yield from batch
        page += 1
```

这几行和 `PhotoIterator` 做的事情完全一样（测试 `test_same_items_as_the_class`）。每次执行到 `yield`，函数就暂停，把一个元素交给调用方；下次需要元素时，再从暂停的地方继续。“当前在第几页”就是函数里的局部变量 `page`，不需要自己保存在对象的字段里。`yield from batch` 把一页里的照片逐个交出去。

在 Python 里，**需要一个迭代器时，先写生成器函数**。只有当迭代器还需要提供别的方法（比如“跳到某一页”“当前进度”）时，才写成类。

### 迭代器和可迭代对象

Python 区分两个概念：

- **迭代器**（iterator）：有 `__next__`，记着遍历的位置，只能走一遍。`iter_photos(api)` 返回的就是迭代器。
- **可迭代对象**（iterable）：有 `__iter__`，每次被要求时，返回一个**新的**迭代器。列表就是可迭代对象，可以对同一个列表反复 `for` 循环。

```python
class Album:
    """可迭代对象：每次 for 循环都从头开始，得到一个新的迭代器。"""

    def __init__(self, api: FakePhotoApi) -> None:
        self.api = api

    def __iter__(self) -> Iterator[dict]:
        return iter_photos(self.api)
```

对同一个生成器对象连续两次 `list()`，第二次是空的；对同一个 `Album` 连续两次 `list()`，两次都完整（测试 `test_an_iterator_is_used_up` 和 `test_an_iterable_can_be_looped_again`）。如果你写的函数需要遍历参数**两次**，要么要求调用方传入可迭代对象，要么在函数开头用 `list()` 把它存下来，并且在文档里写清楚。

### 组合迭代器的工具

迭代器的另一个好处是可以**组合**。标准库的 `itertools` 提供了很多现成的工具，它们都只在需要时才向上游要元素。比如“最近的 25 张”：

```python
    print([p["id"] for p in islice(iter_photos(api), 25)][-3:], "请求次数：", api.requests)
```

`islice` 取够 25 张就停下，只请求了 2 页（测试 `test_islice_takes_just_enough_pages`）。

### 边读边处理

[第 15 章](../part-03/15-flyweight.md)提到过：面对大量数据，首先要问“需不需要把它们全部留在内存里”。迭代器正是回答这个问题的工具。统计某一年在各地拍了多少照片：

```python
def places_by_year(api: FakePhotoApi, year: int) -> Counter[str]:
    """边取边数：任何时刻内存里最多只有一页照片。"""
    return Counter(p["place"] for p in iter_photos(api) if p["year"] == year)
```

这一行需要遍历全部照片（测试 `test_streaming_count` 中仍然是 11 次请求），但任何时刻内存里只有当前这一页，以及一个计数器。照片从两百张变成两百万张，这个函数占用的内存也基本不变。读大文件时，`for line in file` 一行一行地读，是同样的道理。

## 小结

- 迭代器把“怎样取得下一个元素”和“拿到元素之后做什么”分开，让调用方按需取用，只为自己用到的部分付出代价。
- Python 把迭代器做进了语言：`__iter__` 和 `__next__` 两个方法，`StopIteration` 表示结束。所有 `for` 循环都基于这个协议。
- 需要迭代器时，优先写生成器函数。分清迭代器（只能走一遍）和可迭代对象（每次给出新的迭代器）。
- 迭代器可以用 `itertools` 组合，也可以让程序边读边处理，不必把全部数据同时放进内存。

## 练习

云相册接口升级了：不再用页码，而是每次返回一页数据和一个“下一页的游标”（一个字符串）；最后一页的游标是 `None`。

1. `iter_photos` 需要怎样修改？调用它的代码（查找成都、取前 25 张、按年份统计）需要修改吗？
2. 用户想要“从上次看到的地方继续”。你会怎样让迭代器支持这个需求？生成器函数还够用吗？
3. 如果在遍历过程中网络断了，你希望调用方看到什么？迭代器应该自动重试吗？

**思路提示**：只需要改 `iter_photos` 内部：把页码换成游标，`while` 的条件换成“游标不是 `None`”。所有调用方都不用改，这正是迭代器“不暴露内部表示”的好处。“从上次的地方继续”需要把当前游标交给调用方保存，下次从它开始。生成器函数可以接收一个起始游标参数，但它没有办法让外部随时读取“当前游标”，这时写成一个带 `cursor` 属性的迭代器类更合适。第 3 问：迭代器里的网络错误会在调用方的循环中间抛出。是否重试，取决于接口是否幂等，以及调用方能否承受等待（参见[第 19 章](19-command.md)关于重试与幂等的讨论）。通常让迭代器把错误抛出去、由调用方决定，比在迭代器里悄悄重试更清楚。

完整代码：
- [`examples/ch23_photos_v1.py`](../../examples/ch23_photos_v1.py)：模拟的分页接口，先取全部再查找
- [`examples/ch23_iterator.py`](../../examples/ch23_iterator.py)：实现迭代器协议的类
- [`examples/ch23_pythonic.py`](../../examples/ch23_pythonic.py)：生成器函数、可迭代对象、`islice` 与边读边统计

测试：[`tests/test_ch23_iterator.py`](../../tests/test_ch23_iterator.py)。
