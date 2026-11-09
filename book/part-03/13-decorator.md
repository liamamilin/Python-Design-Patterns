# 第 13 章　装饰器 Decorator

> 本章要回答：怎样在不改变对象接口的前提下，一层层地给它加上新的职责？GoF 的装饰器模式和 Python 的 `@` 装饰器语法是什么关系？

先说清楚名字的问题。Python 有一个 `@` 语法，也叫“装饰器”。它和 GoF 的装饰器模式有共同的思想，但不是同一个东西。这一章先讲模式，再讲语法，最后把两者的异同摆在一起。

## 眼前的任务

一家网店的客服系统要导出聊天记录，用于存档、质检和转交工单。每条消息有发送者和内容：

```python
messages = [
    ("客户", "请回电 13812345678 谢谢"),
    ("客服", "好的，稍后联系您"),
]
```

导出时要把手机号打码，只保留前三位和后四位：`138****5678`。

## 不用模式的写法

一个导出函数。后来工单系统要求每行不超过 16 个字，于是又加了一个截断参数：

```python
def export(chat: list[tuple[str, str]], *, mask: bool = False, limit: int | None = None) -> list[str]:
    out = []
    for who, text in chat:
        line = f"{who}：{text}"
        if limit is not None and len(line) > limit:
            line = line[: limit - 1] + "…"  # 先截断
        if mask:
            line = PHONE.sub(mask_phone, line)  # 再打码
        out.append(line)
    return out
```

只打码时一切正常：`客户：请回电 138****5678 谢谢`。

**打码加截断时，手机号泄露了**：

```text
客户：请回电 13812345…
```

截断先执行，把 11 位的号码切成了 8 位。打码用的正则表达式找的是“1 开头的 11 位数字”，8 位数字它不认识，于是原样放过。号码的前 8 位就这样进了工单系统（测试 `test_truncating_first_leaks_digits`）。

修起来只要交换两个 `if` 的顺序。但这个错误暴露了这种写法的结构问题。

## 变化带来的困难

导出的目的地越来越多，每个目的地要的处理也不一样：

| 目的地 | 打码 | 截断 | 其他 |
|---|---|---|---|
| 存档文件 | 否（存档要求保留原文，有权限控制） | 否 | |
| 质检屏幕 | 是 | 否 | 统计条数 |
| 工单系统 | 是 | 16 字 | |

在一个函数里用开关表达这些组合，有三个问题：

1. **处理的顺序被写死在函数里。** 先截断还是先打码，由两个 `if` 的位置决定，调用方看不到，也改不了。刚才的泄露就是这么来的。
2. **每加一种处理，就要改这个函数。** 统计条数、加时间戳、过滤敏感词……函数的参数列表和 `if` 会一直变长。
3. **处理逻辑和目的地绑在一起。** 函数返回一个列表；如果要直接写进文件，或者推送到工单系统，又要再写一份带同样开关的函数。

我们希望的是：每种处理是一个**独立的小部件**，可以按需要的顺序**一层层叠加**到任何目的地上。

## 装饰器：一层包一层，接口不变

GoF 对装饰器的描述是：**动态地给一个对象添加一些额外的职责。就增加功能来说，装饰器模式相比生成子类更为灵活。**

先定义“写一行”的接口，以及最终的目的地：

```python
class Writer(Protocol):
    def write(self, line: str) -> None: ...


class ListWriter:
    """最终的目的地。真实程序里可能是文件、屏幕或工单系统。"""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def write(self, line: str) -> None:
        self.lines.append(line)
```

装饰器的关键在于：**它自己也是一个 `Writer`，同时持有另一个 `Writer`**。它在把这一行交给里面那个 `Writer` 之前（或之后），做一点自己的事：

```python
class WriterDecorator:
    def __init__(self, inner: Writer) -> None:
        self.inner = inner

    def write(self, line: str) -> None:
        self.inner.write(line)


class Masking(WriterDecorator):
    def write(self, line: str) -> None:
        self.inner.write(PHONE.sub(mask_phone, line))
```

截断、计数也各是一个装饰器，各自只做一件事。比如计数，它不改变内容，只是多了一项职责：

```python
class Counting(WriterDecorator):
    def __init__(self, inner: Writer) -> None:
        super().__init__(inner)
        self.count = 0

    def write(self, line: str) -> None:
        self.count += 1
        self.inner.write(line)
```

导出函数只认 `Writer`，不再有任何开关：

```python
def export(chat: list[tuple[str, str]], writer: Writer) -> None:
    for who, text in chat:
        writer.write(f"{who}：{text}")
```

给工单系统用的写法，是把目的地一层层包起来：

```python
    ticket = ListWriter()
    export(messages, Masking(Truncating(ticket, 16)))
    print(ticket.lines)
```

```text
['客户：请回电 138****5…', '客服：好的，稍后联系您']
```

### 顺序：外层先执行

`Masking(Truncating(ticket, 16))` 读起来是“打码，包着截断，包着工单”。调用 `write` 时，最外层的 `Masking` 先拿到这一行，打完码交给 `Truncating`，截断后再交给 `ticket`。所以**写在最外面的，最先执行**。

反过来包，`Truncating(Masking(leaky), 16)`，就是先截断、后打码，泄露又出现了（测试 `test_outer_layer_runs_first`）。

装饰器并没有自动消除顺序问题，顺序依然重要。不同的是，**顺序现在是在组装的地方显式写出来的**，而不是藏在一个函数的两个 `if` 之间。为了不让每个调用处都要想一遍，可以把正确的组装方式写成一个函数，并在注释里写明理由：

```python
def build_writer(dest: Writer, *, mask: bool = True, limit: int | None = None) -> Writer:
    writer = dest
    if limit is not None:
        writer = Truncating(writer, limit)
    if mask:
        writer = Masking(writer)  # 最后包上的一层最先执行：先打码，再截断
    return writer
```

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 组件（Component） | `Writer` 协议 | 被装饰对象和装饰器共同的接口 |
| 具体组件（ConcreteComponent） | `ListWriter` | 最终完成工作的对象 |
| 装饰器（Decorator） | `WriterDecorator` | 持有一个组件，默认把请求原样转交 |
| 具体装饰器（ConcreteDecorator） | `Masking`、`Truncating`、`Counting` | 在转交前后加上自己的职责 |

### 标准库里的装饰器

Python 的文件读写就是一个现成的例子。`open("chat.txt", "w", encoding="utf-8")` 返回的对象，是三层叠起来的：最里面的 `io.FileIO` 只会写字节；外面包一层 `io.BufferedWriter`，加上缓冲；最外面是 `io.TextIOWrapper`，负责把字符串按指定编码转成字节。每一层都提供 `write` 方法，每一层都持有里面那一层。`gzip.GzipFile` 也可以包住一个已经打开的文件对象，给它加上压缩。

## 代价与边界

- **对象变多，调试要一层层剥开。** 出错时调用栈里是 `Masking.write → Truncating.write → ListWriter.write`，要知道哪一层出了问题，得一层一层地看。
- **顺序很重要，而且类型系统检查不出来。** `Masking(Truncating(...))` 和 `Truncating(Masking(...))` 的类型完全一样，都是合法的 `Writer`。正确的顺序只能靠测试和集中的组装函数来保证。
- **被包起来之后，内层对象特有的东西就看不见了。** 外面拿到的是一个 `Masking` 对象，它只有 `write`。想看 `Counting` 的 `count`，必须在组装时自己保留对那一层的引用，就像测试 `test_layers_stack_freely` 里的 `counter` 那样。
- **对象的身份变了。** 包装之后的对象不再是原来那个对象，`is` 比较和 `isinstance` 检查都可能不再成立。

**什么时候不该用**：处理的组合是固定的，而且只有一两种。如果工单系统永远是“打码加截断”，一个按正确顺序写好的普通函数比三个装饰器类加一个组装函数简单得多。装饰器适用于**组合需要在运行时、按配置变化**的情况。

## Python 角度：`@` 装饰器语法

现在来看 Python 的 `@` 语法。当 `Writer` 只有一个方法时，它完全可以就是一个**函数**：接收一行字符串，什么也不返回。这时，“包住一个 Writer 并加一项职责”就成了**接收一个函数、返回一个新函数**：

```python
def masking(write: WriteFn) -> WriteFn:
    @functools.wraps(write)
    def wrapped(line: str) -> None:
        write(PHONE.sub(mask_phone, line))

    return wrapped
```

这和 `Masking` 类做的事完全一样，只是用函数和闭包表达。组合方式也一样，外层先执行：

```python
    lines: list[str] = []
    export(messages, masking(truncating(16)(lines.append)))
```

（`truncating(16)` 先根据参数生成一个装饰函数，再用它去包 `lines.append`。需要参数的装饰器通常写成这样的三层函数。`functools.wraps` 把被包函数的名字和文档字符串复制到新函数上，否则调试时看到的名字都是 `wrapped`。）

`@` 语法就是这种“用一个函数包另一个函数”的简写：

```python
@masking
def print_line(line: str) -> None:
    """打印到屏幕。定义时就包上了打码，之后每次调用都会打码。"""
    print(line)
```

它的意思**完全等于**在函数定义之后写一句 `print_line = masking(print_line)`。

### 异同

两者的共同点是同一个思想：**用一个和原来接口相同的东西包住原来的东西，在调用前后加一点行为。**

不同点：

| | GoF 装饰器模式 | Python `@` 语法 |
|---|---|---|
| 包的是什么 | 对象（或在 Python 里，也可以是函数） | 函数或类，写在它的定义上方 |
| 什么时候包 | 运行时，组装对象的时候 | 定义的时候，模块被导入时执行一次 |
| 能否按需组合 | 能，同一个 `ListWriter` 可以有时打码、有时不打码 | `@` 写死在定义上，每次调用 `print_line` 都会打码 |
| 典型用途 | 按配置给某个对象叠加职责 | 给一个函数统一加上横切的行为：缓存、计时、权限检查、注册 |

所以，`@` 语法是实现装饰器思想的一种**语言工具**，而它最擅长的是“这个函数**永远**需要这层包装”的场合。像本章这样“**这一次**导出要打码和截断，**那一次**不要”的需求，要么像上面那样不用 `@`、直接调用 `masking(...)` 来组合函数，要么用装饰器类。`@` 的更多用法，[第 30 章](../part-05/30-decorators-context-managers-generators.md)会专门讨论。

还有一点需要注意：`@` 也常用来做一些和 GoF 装饰器毫无关系的事，比如 `@dataclass` 会给类生成新方法，`@app.route("/")` 这类写法常用来把函数登记到一个表里。它们都用 `@` 语法，但并不是“包一层、接口不变”。**看到 `@` 不等于看到了装饰器模式。**

### 和适配器、代理的区别

[第 10 章](10-adapter.md)的适配器也是“持有一个对象、包一层”。区别是：适配器**改变**接口，让对象适应另一个接口；装饰器**保持**接口，只增加职责，而且可以一层层叠加。[第 16 章](16-proxy.md)的代理也保持接口，但它的目的是**控制对对象的访问**（延迟创建、权限、缓存），而不是给对象增加新的职责。

## 小结

- 当需要给对象叠加若干项独立的职责，而且组合方式在运行时变化时，装饰器让每项职责成为一个和原对象接口相同的包装层，可以按需要叠加。
- 包装的顺序很重要：最外层最先执行。顺序问题不会消失，但会从函数内部移到组装的地方，可以显式写出来、集中管理。
- Python 的 `@` 语法是“用一个函数包另一个函数”的简写，在定义时执行一次。它体现了同样的思想，但适合“永远需要”的包装；按次组合时，直接调用包装函数或使用装饰器对象。
- 不是所有的 `@` 都是装饰器模式，也不是所有的装饰器模式都要用 `@`。

## 练习

质检部门提出：质检屏幕上的消息，如果包含“退款”“投诉”这类词，要在行首加上 `【重点】` 标记。

1. 用装饰器的写法，你会新增一个什么类？它应该包在 `Masking` 的外面还是里面？会不会和截断产生顺序问题？
2. 如果用 `@` 语法给一个 `show_on_screen` 函数加上这个标记，有什么限制？
3. 如果标记的规则需要质检人员在界面上随时修改（比如今天加一个关键词“发票”），哪一种写法更容易支持？

**思路提示**：新增一个 `Highlighting(WriterDecorator)`，它检查关键词并在行首加标记。它和打码互不影响，内外都可以；但如果它和截断叠在一起，就要想清楚：先加标记再截断，标记会占用字数；先截断再加标记，关键词可能刚好被截掉，从而漏标。这又是一个顺序问题，应该写进组装函数，并配上测试。用 `@` 语法的话，标记就永久附着在 `show_on_screen` 上，其他目的地如果不想要标记，就得另写一个函数。第 3 问中，装饰器对象可以在构造时接收关键词列表，甚至持有一个会被界面修改的关键词集合；`@` 写在定义处，适合规则固定的情况。

完整代码：
- [`examples/ch13_export_v1.py`](../../examples/ch13_export_v1.py)：用开关控制的导出函数（含泄露）
- [`examples/ch13_decorator.py`](../../examples/ch13_decorator.py)：装饰器类与组装函数
- [`examples/ch13_pythonic.py`](../../examples/ch13_pythonic.py)：函数装饰器与 `@` 语法

测试：[`tests/test_ch13_decorator.py`](../../tests/test_ch13_decorator.py)。
