# 第 28 章　函数就是一种设计工具

> 本章要回答：在 Python 里，可调用对象、高阶函数、闭包和字典分派，怎样替代那些只有一个方法的小类？什么时候还是应该写类？

第五部分回到 Python 语言本身。前面的模式章里，“Python 角度”一节反复出现同一个结论：**只有一个方法的策略，就是一个函数**；**工厂可以就是一次字典查找**；**延后执行的命令，可以是一个包好参数的函数**。这一章把这些零散的结论放在一起，用同一个例子，系统地看一遍 Python 提供的这些工具，以及它们的边界。

## 眼前的任务

一个命令行记账小工具。用户输入一行命令，比如 `add 瑞幸拿铁 1600`（金额以分为单位），程序记下一笔账；输入 `total` 显示合计。程序还会按规则给每笔账分类：超过 500 元的是“大额支出”，含“咖啡”“拿铁”的是“饮品”，含“地铁”“打车”的是“交通”，都不匹配的是“其他”。

## 类的写法

按经典的模式写法，这里有三组小类：

- **分类规则**是策略：一个 `Rule` 抽象基类，`KeywordRule`、`OverRule` 两个子类，每个只有一个 `match` 方法；
- **命令**是命令模式：一个 `Command` 抽象基类，`AddCommand`、`TotalCommand` 两个子类，每个只有一个 `execute` 方法；
- **创建命令**用一个工厂：`CommandFactory.create(name)`。

```python
class KeywordRule(Rule):
    def __init__(self, words: tuple[str, ...], category: str) -> None:
        self.words, self.category = words, category

    def match(self, r: Record) -> str | None:
        return self.category if any(w in r.desc for w in self.words) else None
```

```python
class CommandFactory:
    def create(self, name: str) -> Command:
        if name == "add":
            return AddCommand()
        if name == "total":
            return TotalCommand()
        raise ValueError(f"未知命令: {name}")
```

它能正常工作。但数一数：两个抽象基类、四个具体类、一个工厂类，每个类的核心都只有一两行。

## 函数的写法

同样的功能，换一种写法。下面依次介绍用到的每一种工具。

### 函数是对象

Python 的函数和其他对象一样，可以赋值给变量、放进列表和字典、作为参数传递、作为返回值返回。这一点是本章所有写法的基础。

### 闭包：带配置的函数

`KeywordRule` 的作用是“记住几个关键词和一个类别，然后对每笔账做判断”。一个**闭包**可以做到完全一样的事：

```python
def keyword(*words: str, category: str) -> Rule:
    def rule(r: Record) -> str | None:
        return category if any(w in r.desc for w in words) else None

    return rule
```

`keyword(...)` 返回内层函数 `rule`。`rule` 用到了外层函数的参数 `words` 和 `category`，即使 `keyword` 已经执行完毕，`rule` 依然记得它们。这就是闭包：**一个函数，加上它创建时所在环境中的变量。**

`KeywordRule(("地铁", "打车"), "交通")` 的构造参数，在这里变成了 `keyword("地铁", "打车", category="交通")` 的参数；`match` 方法的方法体，变成了内层函数的函数体。

### 高阶函数：接收函数作为参数

分类器接收一个规则函数的列表，依次调用：

```python
def classify(r: Record, rules: list[Rule]) -> str:
    return next((c for rule in rules if (c := rule(r)) is not None), "其他")
```

接收函数、或者返回函数的函数，叫作**高阶函数**。`classify` 是前一种，`keyword` 是后一种。`Rule` 只是一个类型别名 `Callable[[Record], str | None]`，表示“接收一笔账、返回类别或 `None` 的可调用对象”，并不是一个需要继承的基类。

### 字典分派：替代工厂和 `if` 链

命令就是普通函数。“根据名字找到命令”这件事，用一个字典完成：

```python
COMMANDS: dict[str, Callable[..., str]] = {"add": add, "total": total}


def run(book: list[Record], line: str) -> str:
    name, *args = line.split()
    if name not in COMMANDS:
        raise ValueError(f"未知命令: {name}")
    return COMMANDS[name](book, *args)
```

`CommandFactory` 和两个命令类，变成了一个字典和两个函数。加一个新命令，就是写一个函数、在字典里加一行。

两种写法对同一组输入，记下的账、分出的类别、算出的合计完全相同（测试 `test_both_versions_agree`）。

### 可调用对象：需要状态时

如果某条规则需要**记住一些东西**，比如“统计它一共匹配了几次”，函数就不那么方便了。这时可以写一个类，实现 `__call__` 方法，它的实例就能像函数一样被调用：

```python
class CountingRule:
    """需要记住状态时，可调用对象和函数一样能放进规则列表。"""

    def __init__(self, rule: Rule) -> None:
        self.rule = rule
        self.hits = 0

    def __call__(self, r: Record) -> str | None:
        result = self.rule(r)
        if result is not None:
            self.hits += 1
        return result
```

`CountingRule` 的实例可以和普通的规则函数放在同一个列表里，`classify` 完全不需要知道它是一个对象（测试 `test_object_with_state_fits_the_same_slot`）。

这说明了一件重要的事：**`Callable` 这个类型不关心你是函数还是对象。** 先用函数，等到确实需要状态或多个方法时，换成一个可调用对象，使用它的代码一行都不用改。

### `functools.partial`：固定部分参数

[第 17 章](../part-04/17-strategy.md)用过 `partial(express_fee, free_over=5900)`，它和闭包的作用相似：把一个通用函数的部分参数固定下来，得到一个更具体的函数。如果需要的只是“固定参数”，`partial` 比手写闭包更短，而且它会保留原函数和参数的信息，调试时更容易看清楚。

## 一个常见的陷阱：循环里的闭包

运营同事给了一个“关键词 → 类别”的对照表，想批量生成规则。最自然的写法是这样：

```python
def keyword_rules_wrong(categories: dict[str, str]) -> list[Rule]:
    """常见错误：在循环里创建 lambda，它们捕获的是同一个变量。"""
    return [lambda r: category if word in r.desc else None for word, category in categories.items()]
```

对照表是 `{"地铁": "交通", "拿铁": "饮品"}`，可“地铁”被分到了“其他”（测试 `test_lambdas_in_a_loop_share_the_last_value`）。

原因是：闭包记住的是**变量**，而不是创建时变量的**值**。列表推导式里的所有 `lambda` 共享同一个 `word` 和 `category` 变量，循环结束时，它们都指向最后一项（“拿铁”和“饮品”）。所以每条规则检查的都是“拿铁”。

修正的办法是：让每条规则在**一次单独的函数调用**中创建，这样每次调用都有自己的一组变量：

```python
def keyword_rules(categories: dict[str, str]) -> list[Rule]:
    return [keyword(word, category=category) for word, category in categories.items()]
```

另一种常见写法是 `lambda r, word=word: ...`，利用默认参数在创建时求值。它也能工作，但读起来不够直观，还会让函数多出一个可以被意外传入的参数。

## 什么时候还是写类

函数并不总是更好。以下情况，类更合适：

- **有好几个必须一起变化的操作。** [第 17 章](../part-04/17-strategy.md)的配送方式要回答“能不能送、多少钱、多久到”三个问题。拆成三个函数、放进三个字典，加一种配送方式时就要改三处。一个类把它们绑在一起。
- **有需要修改的状态。** 闭包也能保存可修改的状态（用 `nonlocal`），但当状态有好几个字段、还要从外面读取时（比如 `CountingRule.hits`），类更清楚。
- **需要被继承扩展，或者需要 `isinstance` 判断。** 框架的扩展点、需要在运行时区分种类的地方。
- **对象需要一个有意义的显示形式，或者需要被比较、被保存。** `dataclass` 自动提供 `__repr__` 和 `__eq__`；闭包打印出来只是 `<function keyword.<locals>.rule at 0x...>`。

一个实用的判断方法：**如果一个类除了 `__init__` 之外只有一个方法，而且这个方法的名字是个动词（`match`、`execute`、`apply`），它多半可以是一个函数。**

## 小结

- 在 Python 里，函数是对象：可以存进容器、作为参数和返回值。这让很多“只有一个方法的小类”可以直接写成函数。
- 闭包是带配置的函数，可以替代“构造参数 + 一个方法”的策略类；字典分派可以替代简单的工厂和 `if` 链；`partial` 可以固定参数。
- 需要状态时，实现 `__call__` 的对象可以放在函数的位置，使用方不必改动。
- 注意循环中创建闭包的陷阱：闭包记住的是变量，不是值。
- 有多个一起变化的操作、有需要从外部读取的状态、需要继承或有意义的显示形式时，写类。

## 练习

记账工具要加一个 `undo` 命令，撤销最近一次 `add`。

1. 在字典分派的写法里，`undo` 需要知道“最近一次添加了什么”。这个信息放在哪里？
2. 如果 `add` 和 `undo` 都需要访问同一份“历史记录”，用闭包实现会是什么样子？用一个类呢？哪种更清楚？
3. 结合[第 19 章](../part-04/19-command.md)，这时命令还适合只是“字典里的函数”吗？

**思路提示**：最简单的做法是把历史放进账本本身，比如 `book` 改成一个包含记录列表和历史栈的对象，命令函数通过参数拿到它。用闭包实现时，`add` 和 `undo` 要定义在同一个外层函数里，共享一个 `history` 列表，这能工作，但“哪些函数共享哪些状态”藏在了函数嵌套的结构里。用一个类（比如 `Ledger`，带 `add`、`undo` 方法和 `history` 字段）会更清楚。这正是“有多个操作共享状态时，写类”的情况。至于第 3 问：一旦命令需要撤销，每个命令就要提供“执行”和“撤销”两个操作，[第 19 章](../part-04/19-command.md)的命令对象（或“执行时返回反向命令”的写法）比单个函数更合适。

完整代码：
- [`examples/ch28_classes.py`](../../examples/ch28_classes.py)：规则类、命令类和工厂
- [`examples/ch28_functions.py`](../../examples/ch28_functions.py)：闭包、字典分派、可调用对象与循环闭包陷阱

测试：[`tests/test_ch28_functions.py`](../../tests/test_ch28_functions.py)。
