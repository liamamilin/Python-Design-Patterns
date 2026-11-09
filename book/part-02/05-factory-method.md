# 第 05 章　工厂方法 Factory Method

> 本章要回答：当“创建哪种对象”的决定随具体情况而变时，这个决定应该放在哪里？简单工厂函数和 GoF 工厂方法有什么区别？

“工厂”是 Python 开发者最常听到的设计词汇之一，也是最常被用混的一个。这一章先从一个不需要任何模式的小程序开始，一步步走到真正需要工厂方法的地方，并且说清楚每一步叫什么、不叫什么。

## 眼前的任务

一个小团队用一份任务清单跟踪工作：

```python
tasks = [
    Task("登录页改版", True),
    Task("修复导出乱码", False),
    Task("接入短信验证码", True),
]
```

`Task` 是一个只有两个字段的数据类：任务名称 `name`，是否完成 `done`。团队想从这份清单自动生成文档。第一个需求是每周例会的 Markdown 纪要：

```text
# 周会纪要
- [x] 登录页改版
- [ ] 修复导出乱码
- [x] 接入短信验证码
```

## 不用模式的写法

后来客户也想看进度，但客户那边要 HTML，而且只看已完成的任务。加一个格式参数就能解决：

```python
def render(title: str, items: list[Task], fmt: str = "markdown") -> str:
    if fmt == "markdown":
        lines = [f"# {title}"]
        lines += [f"- [{'x' if t.done else ' '}] {t.name}" for t in items]
    elif fmt == "html":
        lines = [f"<h1>{html.escape(title)}</h1>"]
        lines += [f"<li>{'✔' if t.done else '…'} {html.escape(t.name)}</li>" for t in items]
    else:
        raise ValueError(f"未知格式: {fmt}")
    return "\n".join(lines)
```

`render("项目进度", [t for t in tasks if t.done], "html")` 得到：

```text
<h1>项目进度</h1>
<li>✔ 登录页改版</li>
<li>✔ 接入短信验证码</li>
```

（`html.escape` 把 `<`、`&` 这类字符转义，避免任务名里的特殊字符破坏网页。）

**这是好代码。** 两种格式、一个函数、一个 `if`，读的人一眼就能看全。如果需求停在这里，就不该再改。

## 第一次变化：选择格式的代码出现在多处

几周后，这个工具有了两个入口：开发者在命令行里手动生成，服务器上的定时任务每周五自动生成。两个入口都要根据配置决定用哪种格式。与此同时，每种格式的写法也在不断被单独调整：HTML 要改标题样式，Markdown 要改勾选框的写法。两种格式的细节挤在同一个函数里，`if` 分支越来越长。

这里有两个具体的困难：

1. 每种格式“怎么写标题、怎么写条目”的代码混在一个函数里，改 HTML 时要小心别碰到 Markdown。
2. “根据字符串选择格式”这件事，两个入口各写了一遍。

第一个困难的解法是：**把每种格式变成一个对象**，各自负责自己的写法。

```python
class MarkdownRenderer:
    def title(self, text: str) -> str:
        return f"# {text}"

    def item(self, task: Task) -> str:
        return f"- [{'x' if task.done else ' '}] {task.name}"


class HtmlRenderer:
    def title(self, text: str) -> str:
        return f"<h1>{html.escape(text)}</h1>"

    def item(self, task: Task) -> str:
        return f"<li>{'✔' if task.done else '…'} {html.escape(task.name)}</li>"
```

第二个困难的解法是：**把“选哪一个”集中到一个函数里**，两个入口都调用它。

```python
def make_renderer(fmt: str) -> Renderer:
    renderers = {"markdown": MarkdownRenderer, "html": HtmlRenderer}
    try:
        return renderers[fmt]()
    except KeyError:
        raise ValueError(f"未知格式: {fmt}") from None
```

`make_renderer` 是一个**简单工厂函数**：输入一个描述，返回一个新创建的对象。它把“创建什么”的决定集中到一处，以后加一种格式，只要在字典里加一行。

需要说清楚的是：**简单工厂函数不是 GoF 23 种模式之一。** 它非常有用，Python 代码里随处可见，但它只是“把创建逻辑提取成函数”这一普通重构的结果。把它叫作“工厂方法模式”是常见的误用。

## 第二次变化：创建的决定随文档类型而变

工具越来越受欢迎，团队里不同的人开始往里加新的文档类型：

- **周会纪要**：列出全部任务，用 Markdown。
- **客户进度报告**：只列已完成的任务，用 HTML。
- 另一位同事想加一个**发布说明**：只列已完成的任务，用纯文本，贴到应用商店的更新说明里。

观察这三种文档，会发现它们有一个共同的流程：

1. 写标题；
2. 挑出要展示的任务；
3. 每个任务写一行；
4. 拼成一篇文档。

不同的只有三点：标题是什么、挑哪些任务、**用哪种渲染器**。而且“用哪种渲染器”不是由用户传进来的配置决定的，而是**由文档类型本身决定的**：客户报告就是 HTML，这是这种文档的一部分定义。

更重要的是，新增文档类型的人（比如写发布说明的同事）不应该去修改共同流程的代码。他们只想说：“我的文档叫什么，挑哪些任务，用什么渲染器。”

这正是 GoF 工厂方法要解决的问题。

## 工厂方法：让子类决定创建什么

GoF 对工厂方法的经典描述是：**定义一个用于创建对象的接口，让子类决定实例化哪一个类。工厂方法使一个类的实例化延迟到其子类。**

落到我们的例子上：

```python
class Document(ABC):
    title = "文档"

    def build(self, items: list[Task]) -> str:
        renderer = self.create_renderer()  # 工厂方法：由子类决定创建什么
        lines = [renderer.title(self.title)]
        lines += [renderer.item(t) for t in self.select(items)]
        return "\n".join(lines)

    def select(self, items: list[Task]) -> list[Task]:
        return items

    @abstractmethod
    def create_renderer(self) -> Renderer:
        """返回这种文档使用的渲染器。"""
```

`Document.build` 固定了共同流程。流程中需要一个渲染器，但 `Document` 自己不知道该用哪一种，于是它调用 `self.create_renderer()`，这就是**工厂方法**。它被声明为抽象方法，每个子类必须给出自己的答案：

```python
class WeeklyNotes(Document):
    title = "周会纪要"

    def create_renderer(self) -> Renderer:
        return MarkdownRenderer()


class ClientReport(Document):
    title = "项目进度"

    def select(self, items: list[Task]) -> list[Task]:
        return [t for t in items if t.done]

    def create_renderer(self) -> Renderer:
        return HtmlRenderer()
```

`WeeklyNotes().build(tasks)` 和 `ClientReport().build(tasks)` 分别生成和之前完全一样的 Markdown 纪要和 HTML 报告。

现在写发布说明的同事可以在**自己的模块里**完成全部工作，不用碰 `Document`：

```python
class ReleaseNotes(Document):
    title = "发布说明"

    def select(self, items: list[Task]) -> list[Task]:
        return [t for t in items if t.done]

    def create_renderer(self) -> Renderer:
        return PlainTextRenderer()
```

```text
发布说明
========
* 登录页改版
* 接入短信验证码
```

### 角色对照

GoF 用四个角色描述这个模式，对应到代码里：

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 产品（Product） | `Renderer` 协议 | 规定渲染器要提供 `title` 和 `item` |
| 具体产品（ConcreteProduct） | `MarkdownRenderer`、`HtmlRenderer`、`PlainTextRenderer` | 各自的写法 |
| 创建者（Creator） | `Document` | 定义共同流程，声明工厂方法 `create_renderer` |
| 具体创建者（ConcreteCreator） | `WeeklyNotes`、`ClientReport`、`ReleaseNotes` | 实现工厂方法，决定创建哪种具体产品 |

`Renderer` 在这里用 `typing.Protocol` 来写（见[第 03 章](../part-01/03-python-building-blocks.md)），三个渲染器不需要继承任何基类，只要提供这两个方法即可。

### 和简单工厂、抽象工厂的区别

这三个名字常被混用，这里一次说清：

- **简单工厂函数**：一个普通函数根据参数决定创建什么，比如 `make_renderer("html")`。决定权在**参数**上。它不是 GoF 模式。
- **工厂方法**：父类的流程里调用一个可被子类重写的创建方法，比如 `self.create_renderer()`。决定权在**子类**上。创建通常只是更大流程中的一步。
- **抽象工厂**（[第 06 章](06-abstract-factory.md)）：一个对象负责创建**一整组**彼此匹配的产品，比如一套主题里的按钮、输入框和对话框。关注的是“同一家族的产品要配套”。

一个简单的判断方法：如果你的“工厂”是一个独立的函数，它是简单工厂；如果它是父类流程中、留给子类重写的那个方法，它是工厂方法。

## 代价与边界

工厂方法不是免费的：

- **多了一层继承。** 要知道 `ClientReport` 生成什么，得同时读 `ClientReport` 和 `Document`。流程在父类，细节在子类。
- **每种文档一个子类。** 只有两种文档时，这比一个带参数的函数重得多。
- **子类和父类的流程绑在一起。** 如果 `Document.build` 的流程改了（比如在标题后面加一个统计行），所有子类的输出都会跟着变。这有时正是你想要的，有时则是意外。
- **两个维度纠缠时会出现组合爆炸。** 如果客户报告也想要一份 Markdown 版本，你可能会写出 `ClientReportMarkdown`。文档类型和格式本来是两个独立的维度，工厂方法把它们绑在了同一个子类上（见本章练习）。

**什么时候不该用**：只有一两种文档，格式通过参数就能选择，没有第三方需要在不改动你代码的情况下扩展。这时一个带参数的函数，加上前面的简单工厂，已经足够好。

## Python 角度：类本身就是工厂

在 C++ 这类语言里，“创建一个对象”通常需要写 `new SomeClass()`，类名必须写死在代码里，所以要靠子类重写方法来改变创建的类型。

Python 不一样：**类本身就是一个可以调用的对象，调用它就会创建实例**。`MarkdownRenderer` 和 `HtmlRenderer` 可以像函数一样被传来传去。于是，很多需要工厂方法的场合，可以直接把“怎么创建”作为参数传进去：

```python
def build_document(
    title: str,
    items: list[Task],
    make_renderer: Callable[[], Renderer] = MarkdownRenderer,
    keep: Callable[[Task], bool] = lambda task: True,
) -> str:
    renderer = make_renderer()
    lines = [renderer.title(title)]
    lines += [renderer.item(t) for t in items if keep(t)]
    return "\n".join(lines)


def weekly_notes(items: list[Task]) -> str:
    return build_document("周会纪要", items)


def client_report(items: list[Task]) -> str:
    return build_document("项目进度", items, HtmlRenderer, keep=lambda t: t.done)
```

这两个函数的输出和 `WeeklyNotes`、`ClientReport` 完全一样，但没有任何子类。想要“Markdown 版的客户报告”，只要换一个参数，不需要新类。

那么，什么时候还值得用经典的工厂方法？

- 共同流程比较长，子类除了“创建什么”，还要定制好几个步骤，而且这些步骤之间有约束。这时把它们组织在一个子类里，比传一长串参数更清楚。这其实已经和[第 21 章](../part-04/21-template-method.md)的模板方法很接近，工厂方法常常就是模板方法中“负责创建”的那一步。
- 你在写一个框架或库，希望别人通过**继承**来扩展，而且这种扩展方式是使用者熟悉的约定。
- 产品的选择确实是这种类型的**固有属性**，而不是调用时的配置。

如果以上都不满足，先用“把类当参数传进去”的写法。

## 小结

- 创建什么对象的决定，最开始可以就是一个 `if`；在多处重复时，提取成一个简单工厂函数。简单工厂函数很有用，但它不是 GoF 模式。
- GoF 工厂方法：父类定义流程并调用一个创建方法，子类重写这个方法来决定创建哪种产品。它适合“创建是流程中的一步，而创建的种类由子类决定”的情况。
- 工厂方法的代价是继承带来的间接性，以及当产品选择和子类类型是两个独立维度时的组合爆炸。
- 在 Python 里，类本身就是工厂，直接把类或函数当参数传递，往往比工厂方法更简单。

## 练习

客户提出：除了 HTML 网页，他们还希望每周收到一封纯文本邮件，内容和进度报告一样（只列已完成的任务）。

1. 用工厂方法的写法，你需要新增什么？会不会出现 `ClientReportHtml`、`ClientReportText` 这样的类？
2. 用 `build_document` 的写法，你需要新增什么？
3. 如果将来格式有 4 种、文档类型有 5 种，两种写法分别需要多少个类或函数？

**思路提示**：工厂方法把“文档类型”和“格式”绑在同一个子类上，格式一多就要为每种组合写一个子类。`build_document` 把格式作为参数，文档类型和格式可以自由搭配，5 种文档只需要 5 个小函数，格式在调用时选择。当两个维度都在独立增长时，应该让它们分开变化，这正是[第 11 章](../part-03/11-bridge.md)“桥接”要讨论的问题。对本题来说，把格式改成参数是更好的选择；工厂方法更适合“格式是文档类型固有的一部分”的情况。

完整代码：
- [`examples/ch05_factory_method_v1.py`](../../examples/ch05_factory_method_v1.py)：第一版
- [`examples/ch05_simple_factory.py`](../../examples/ch05_simple_factory.py)：渲染器对象与简单工厂
- [`examples/ch05_factory_method.py`](../../examples/ch05_factory_method.py)：GoF 工厂方法
- [`examples/ch05_pythonic.py`](../../examples/ch05_pythonic.py)：把类当参数传入

测试：[`tests/test_ch05_factory_method.py`](../../tests/test_ch05_factory_method.py)。
