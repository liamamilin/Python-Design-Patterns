# 第 11 章　桥接 Bridge

> 本章要回答：当一个东西同时沿着两个方向变化时，怎样避免为每一种组合写一个类？

[第 05 章](../part-02/05-factory-method.md)的练习留下了一个问题：文档类型和输出格式是两个独立变化的维度，工厂方法把它们绑在同一个子类上，于是每种组合都要一个子类。当时的答案是“把格式改成参数”。这一章换一个例子，把这个问题和它的模式名称完整地讲清楚。

## 眼前的任务

一个气象爱好者小组每月整理本地的降雨量，想在终端里快速看一眼：

```python
rainfall = {"1月": 12, "2月": 30, "3月": 0, "4月": 45}
```

画成横向条形图，最长的一条占满可用宽度，其他按比例缩短：

```text
1月 █████
2月 █████████████
3月
4月 ████████████████████
```

## 不用模式的写法

一个类，一个方法：算出标签宽度，按最大值缩放，每行拼一条：

```python
class TextBarChart:
    def __init__(self, width: int) -> None:
        self.width = width

    def draw(self, data: dict[str, int]) -> str:
        label_w = max(len(k) for k in data) + 1
        room = self.width - label_w
        top = max(data.values()) or 1  # 全为 0 时避免除以 0（后来修的）
        lines = []
        for label, value in data.items():
            bar = "█" * round(value / top * room)
            lines.append(f"{label:<{label_w}}{bar}".rstrip())
        return "\n".join(lines)
```

（`or 1` 那一处，是有一次只画旱季几个月、数据全部为 0 时，程序因为除以 0 崩溃之后加上的。）

**这是好代码。** 只有一种图、一种输出方式时，这就够了。

## 变化：两个方向同时增长

小组要把图表放到网站上，网页要的是 SVG 图形。于是有了 `SvgBarChart`，复制了 `TextBarChart` 的布局计算，把输出换成 `<rect>` 和 `<text>` 元素。

又过了一阵，有人想看纵向的柱状图，比较各月份的高低更直观。于是又要有 `TextColumnChart` 和 `SvgColumnChart`。

| | 终端文本 | SVG |
|---|---|---|
| 横向条形图 | `TextBarChart` | `SvgBarChart` |
| 纵向柱状图 | `TextColumnChart` | `SvgColumnChart` |

两种图、两种输出，四个类。再加一种折线图，就是六个；再加一种输出方式（比如给打印机用的 PostScript），就是九个。**类的数量是两个维度的乘积。**

数量还不是最糟的。同一种图在不同输出方式下的布局计算是重复的，修一处就要记得修所有副本。全为 0 的那个修复只加到了 `TextBarChart` 里：

```python
        top = max(data.values())  # 这里忘了同样的修复
```

于是同样的数据，终端版能画，网页版直接崩溃（测试 `test_fix_landed_in_only_one_combination`）。

## 困难在哪里

每个类其实回答了两个问题：

1. **画什么**：横的还是竖的，标签放在哪里，每个类别占多大地方。这是图表的**布局**。
2. **怎么画出来**：用字符填格子，还是生成 SVG 元素。这是**输出方式**。

这两个问题彼此独立。横向条形图的布局，和最后输出成字符还是 SVG 毫无关系；SVG 怎么画一个矩形，也和这个矩形属于条形图还是柱状图毫无关系。把两个独立的问题塞进同一个类，才导致了乘法。

## 桥接：两个维度各自成为一个层次

GoF 对桥接的描述是：**将抽象部分与它的实现部分分离，使它们都可以独立地变化。**

这里的“抽象”和“实现”不是抽象类和具体类的意思，而是指两个层次：

- **抽象**（Abstraction）一侧：图表。它知道布局，但不知道怎么画出来。
- **实现**（Implementor）一侧：画布。它只会最基本的绘图操作，不知道自己在画什么图。

两侧之间的“桥”，是图表**持有**一个画布对象。

先定义画布要提供的基本操作。只有三个：在某处写字、填满一个矩形、输出结果：

```python
class Canvas(Protocol):
    width: int
    height: int

    def text(self, x: int, y: int, s: str) -> None: ...
    def fill(self, x: int, y: int, w: int, h: int) -> None: ...
    def render(self) -> str: ...
```

文本画布把格子填成字符：

```python
    def fill(self, x: int, y: int, w: int, h: int) -> None:
        for row in range(y, y + h):
            for col in range(x, x + w):
                self.grid[row][col] = "█"
```

SVG 画布把同样的操作翻译成 SVG 元素，每个格子放大成 10 像素：

```python
    def fill(self, x: int, y: int, w: int, h: int) -> None:
        u = self.UNIT
        self.parts.append(f'<rect x="{x * u}" y="{y * u}" width="{w * u}" height="{h * u}"/>')
```

图表一侧，基类保存画布，并且提供共用的缩放计算。全为 0 的情况在这里**只处理一次**：

```python
class Chart:
    def __init__(self, canvas: Canvas) -> None:
        self.canvas = canvas

    @staticmethod
    def scale(value: int, top: int, room: int) -> int:
        return round(value / top * room) if top else 0
```

横向条形图只用画布的基本操作来描述布局：

```python
class BarChart(Chart):
    """横向条形图：每行一个类别。"""

    def draw(self, data: dict[str, int]) -> str:
        label_w = max(len(k) for k in data) + 1
        room = self.canvas.width - label_w
        top = max(data.values())
        for row, (label, value) in enumerate(data.items()):
            self.canvas.text(0, row, label)
            length = self.scale(value, top, room)
            if length:
                self.canvas.fill(label_w, row, length, 1)
        return self.canvas.render()
```

纵向柱状图 `ColumnChart` 也一样，只是把条形竖了起来，标签放到最下面一行。

现在任意组合都是“一个图表 + 一块画布”：

```python
    print(BarChart(TextCanvas(23, 4)).draw(rainfall))
    print(ColumnChart(TextCanvas(12, 6)).draw(rainfall))
    print(BarChart(SvgCanvas(23, 4)).draw(rainfall))
```

```text
         ██
         ██
   ██    ██
   ██    ██
██ ██    ██
1月 2月 3月 4月
```

同一个 `BarChart` 放在 `SvgCanvas` 上，生成的 SVG 里矩形的位置和长度，正好是文本版的 10 倍（测试 `test_bar_chart_on_svg_has_same_layout`）。布局只写了一次，两种输出自然一致。全为 0 的数据，四种组合全都能画（测试 `test_zero_data_works_for_every_combination`）。

再加一种折线图，写一个 `Chart` 子类；再加一种输出方式，写一个画布类。**类的数量从乘积变成了加法。**

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 抽象（Abstraction） | `Chart` | 定义图表的接口，持有一个画布 |
| 扩充抽象（RefinedAbstraction） | `BarChart`、`ColumnChart` | 用画布的基本操作实现各自的布局 |
| 实现者（Implementor） | `Canvas` 协议 | 定义基本绘图操作 |
| 具体实现者（ConcreteImplementor） | `TextCanvas`、`SvgCanvas` | 用具体技术完成基本操作 |

### 和适配器的区别

桥接和[第 10 章](10-adapter.md)的适配器都是“一个对象持有另一个对象，通过它完成工作”，结构上很像。区别在于**时机和目的**：

- 适配器是**事后**补救：两个已经存在的接口对不上，加一层翻译。
- 桥接是**事先**设计：一开始就预见到两个维度会独立变化，于是把它们分成两个层次，并约定好之间的接口（`Canvas` 的三个基本操作）。

## 代价与边界

- **实现者的接口很难设计。** `Canvas` 的三个操作是从现有的两种图里提炼出来的。如果将来要画折线图，需要“画一条斜线”，三个操作就不够了，要给 `Canvas` 加 `line` 方法，所有画布都得实现它。桥接让两侧独立变化，前提是它们之间的接口足够稳定。
- **最低公共能力。** 画布的接口只能包含所有画布都能做到的操作。SVG 能画渐变、圆角、半透明，但文本画布做不到，所以这些都不能进入 `Canvas`。想用 SVG 的特有能力，要么接受图表在文本画布上效果打折，要么在接口之外另开口子。
- **本例的文本画布有一个已知的限制**：它把一个汉字当作一个格子，而终端里一个汉字通常占两列宽。标签都是“某月”时，每行的偏差相同，图看起来仍然对齐；标签长短不一的汉字时就会错位。这是 `TextCanvas` 这一侧的问题，修它不需要动任何图表类，这也正是桥接的好处之一。
- **一开始就分层可能是过度设计。** 如果只有一种输出方式，`Canvas` 这一层就只是多出来的间接性。

**什么时候不该用**：只有一个维度在变化。比如图表种类会越来越多，但永远只在终端里显示，那就让每种图直接输出字符，不需要画布这一层。等第二种输出方式真的出现了，再把布局和绘制分开，这时你也已经知道画布需要哪些基本操作了。

## Python 角度：桥就是一个参数

在 Python 里，桥接经常简单到看不出是一个模式。如果图表本身没有需要保存的状态，抽象一侧根本不必是类，一个接收画布参数的函数就够了：

```python
def draw_bars(data: dict[str, int], canvas: Canvas) -> str:
    label_w = max(len(k) for k in data) + 1
    room = canvas.width - label_w
    top = max(data.values())
    for row, (label, value) in enumerate(data.items()):
        canvas.text(0, row, label)
        length = Chart.scale(value, top, room)
        if length:
            canvas.fill(label_w, row, length, 1)
    return canvas.render()
```

它的输出和 `BarChart` 完全一样。两个维度依然是分开的：画什么由调用哪个函数决定，怎么画由传入哪个画布决定。

回头看[第 05 章](../part-02/05-factory-method.md)的 `build_document(title, items, make_renderer, keep)`：文档类型由调用哪个函数决定，格式由传入哪个渲染器决定。那其实就是同一种结构。所以[第 05 章](../part-02/05-factory-method.md)练习的答案，用这一章的话来说就是：**用桥接取代每种组合一个子类**，而在 Python 里，它常常就是“把实现作为参数传进去”。

另外，`Canvas` 用 `Protocol` 描述，具体画布不需要继承任何基类。实现者一侧本来就应该彼此独立，`Protocol` 正好表达了这一点。

什么时候值得把图表写成类？当图表有自己的配置和状态时，比如标题、颜色方案、是否显示数值、图例位置等。这些设置跟着图表走，和用哪块画布无关，放在图表对象里比每次调用都传一长串参数更清楚。

## 小结

- 当一个东西同时沿两个独立的方向变化，而每个方向都用继承来扩展时，类的数量会变成两个维度的乘积，而且重复的代码会在不同组合之间悄悄走样。
- 桥接把两个维度分成两个层次：抽象一侧（画什么）持有一个实现一侧（怎么画）的对象，两侧通过一个稳定的基本操作接口合作。类的数量变成两者之和。
- 桥接的难点是设计好两侧之间的接口；接口只能包含所有实现者都能做到的事。
- 在 Python 里，桥常常就是一个参数：把实现对象传进函数或构造函数。

## 练习

小组想加一张折线图：每个月一个点，相邻的点用线连起来。

1. 现有的 `Canvas` 只有 `text` 和 `fill` 两种绘图操作。画折线图需要给它加什么操作？
2. 给 `Canvas` 加了新操作之后，`TextCanvas` 和 `SvgCanvas` 各要做什么？文本画布画斜线，效果会怎样？
3. 如果不想让每块画布都实现斜线，还有什么办法？

**思路提示**：折线图需要一个 `line(x1, y1, x2, y2)` 操作。`SvgCanvas` 用 `<line>` 元素一行就能实现；`TextCanvas` 只能用字符近似，比如沿着线的路线把经过的格子标成 `•`，效果会很粗糙。这正是“实现者接口难设计”和“最低公共能力”的体现。第 3 问的一个办法是：在 `Chart` 一侧用多个 `fill(x, y, 1, 1)` 拼出斜线的近似，这样不需要改 `Canvas`，所有画布自动支持，代价是 SVG 版本也只能画出锯齿状的线。另一个办法是让 `Canvas` 提供 `line`，但在基类或一个辅助函数里给出“用 `fill` 拼”的默认实现，SVG 画布再用自己的原生能力覆盖它。选哪一种，取决于你更在意接口的简单，还是 SVG 的效果。

完整代码：
- [`examples/ch11_charts_v1.py`](../../examples/ch11_charts_v1.py)：每种组合一个类（含错误）
- [`examples/ch11_bridge.py`](../../examples/ch11_bridge.py)：图表与画布两个层次
- [`examples/ch11_pythonic.py`](../../examples/ch11_pythonic.py)：接收画布参数的函数

测试：[`tests/test_ch11_bridge.py`](../../tests/test_ch11_bridge.py)。
