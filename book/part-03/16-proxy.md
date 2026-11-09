# 第 16 章　代理 Proxy

> 本章要回答：怎样在不改变调用方式的前提下，在调用方和真实对象之间加一道关卡，用来延迟创建、检查权限或缓存结果？代理和装饰器长得那么像，区别在哪里？

[第 13 章](13-decorator.md)的装饰器是“包一层、接口不变、加一项职责”。这一章的代理结构上几乎一样，但它要解决的是另一类问题：不是给对象**增加**能力，而是**控制**别人怎样接触到这个对象。

## 眼前的任务

一个在线课程网站，每门课程分成若干课，每一课有一份讲义。讲义存成文件，真实场景里它可能是几百 MB 的视频；示例里用文本文件代替。

```python
class RealLesson:
    loads = 0  # 仅用于演示：统计一共读了几次文件

    def __init__(self, title: str, path: Path) -> None:
        self.title = title
        self._text = path.read_text("utf-8")  # 真实场景里是一个很大的视频或讲义文件
        RealLesson.loads += 1

    def content(self) -> str:
        return self._text
```

课程页面先列出目录，学员点开某一课再看讲义：

```python
def outline(lessons: list) -> list[str]:
    return [lesson.title for lesson in lessons]
```

## 不用模式的写法

打开课程时，为每个文件创建一个 `RealLesson`：

```python
def open_course(folder: Path) -> list[RealLesson]:
    return [RealLesson(p.stem, p) for p in sorted(folder.glob("*.txt"))]
```

功能都对。课程只有几课、讲义很小的时候，**这是好代码**。

## 变化：课程变大，而且开始收费

网站发展起来后，出现了两个问题。

**第一，打开目录太慢。** 一门课 40 课，每课一个大文件。学员只是想看一眼目录，程序却把 40 个文件全部读了一遍。在示例的 5 课里，仅仅显示目录，`RealLesson.loads` 就是 5（测试 `test_outline_reads_every_file_and_paid_lessons_are_open`）。

**第二，开始收费。** 每门课的第一课免费试看，其余要报名后才能看。可 `RealLesson.content()` 谁调用都会返回讲义，测试里没报名的人也看到了第 5 课。

两个需求都可以直接写进 `RealLesson`：构造时不读文件，`content()` 里先判断有没有读过；再给它加一个“当前用户”的参数，判断有没有报名。但这样，一个“表示一课内容”的类，就要同时关心文件什么时候读、当前用户是谁、哪些课免费。而且网站上还有别的地方会用到 `RealLesson`，比如后台的讲义审核，那里既不需要延迟加载，也不需要检查报名。

我们希望：课程页面和后续代码照旧调用 `lesson.title` 和 `lesson.content()`，`RealLesson` 本身也不用改；“什么时候读文件”和“谁能看”这两件事，由站在中间的对象负责。

## 代理：替真实对象把关

GoF 对代理的描述是：**为其他对象提供一种代理以控制对这个对象的访问。**

代理和真实对象实现同一个接口，调用方分不出自己拿到的是哪一个：

```python
class Lesson(Protocol):
    title: str

    def content(self) -> str: ...
```

### 虚代理：用到时才创建

第一个代理解决“太早读文件”。它手里只有标题和文件路径，真正的 `RealLesson` 等到第一次调用 `content()` 时才创建：

```python
class LazyLesson:
    """虚代理：标题马上就有，讲义等到第一次真正需要时才读。"""

    def __init__(self, title: str, path: Path) -> None:
        self.title = title
        self._path = path
        self._real: RealLesson | None = None

    def content(self) -> str:
        if self._real is None:
            self._real = RealLesson(self.title, self._path)
        return self._real.content()
```

GoF 把这种代理叫作**虚代理**（virtual proxy）：它代表一个“还没有真正存在”的昂贵对象。显示目录时一个文件都不读；点开某一课，只读这一个文件；再点一次，用已经创建好的那个（测试 `test_outline_reads_nothing` 和 `test_loads_once_on_first_use`）。

### 保护代理：先检查权限

第二个代理解决“谁都能看”。它包住另一个课程对象，在转交请求之前检查当前用户有没有报名：

```python
class PaidLesson:
    """保护代理：只有已报名的学员能看讲义，标题谁都能看。"""

    def __init__(self, inner: Lesson, enrolled: set[str], user: str) -> None:
        self.inner = inner
        self.enrolled = enrolled
        self.user = user
        self.title = inner.title

    def content(self) -> str:
        if self.user not in self.enrolled:
            raise PermissionError(f"{self.user} 还没有报名，不能观看《{self.title}》")
        return self.inner.content()
```

这是**保护代理**（protection proxy）。注意它只拦住了 `content()`，标题照样可以看，因为未报名的学员也需要看到目录才会决定报名。

### 组装

两种代理可以叠在一起，保护代理在外，虚代理在里：

```python
def open_course(folder: Path, user: str, enrolled: set[str], free: int = 1) -> list[Lesson]:
    """前 free 课免费试看，其余需要报名。所有课都延迟加载。"""
    lessons: list[Lesson] = []
    for i, path in enumerate(sorted(folder.glob("*.txt"))):
        lesson: Lesson = LazyLesson(path.stem, path)
        if i >= free:
            lesson = PaidLesson(lesson, enrolled, user)
        lessons.append(lesson)
    return lessons
```

```text
['01-第1课', '02-第2课', '03-第3课', '04-第4课', '05-第5课'] 读了 0 个文件
第 1 课的讲义…… 读了 1 个文件
小周 还没有报名，不能观看《02-第2课》
```

顺序在这里也有意义：保护代理在外面，没报名的人被拒绝时，里面的虚代理根本不会被调用，文件也就不会被读（测试 `test_free_trial_and_paid_lessons`）。如果反过来，先读文件再检查权限，就白白读了一个大文件。

`outline` 函数、`RealLesson` 类，一行都没有改。后台审核讲义的代码继续直接用 `RealLesson`，不受任何影响。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 主题（Subject） | `Lesson` 协议 | 真实对象和代理共同的接口 |
| 真实主题（RealSubject） | `RealLesson` | 真正持有讲义内容 |
| 代理（Proxy） | `LazyLesson`、`PaidLesson` | 持有（或知道如何得到）真实对象，控制对它的访问 |

GoF 列出了几种常见的代理，本章演示了前两种：

- **虚代理**：延迟创建昂贵的对象；
- **保护代理**：检查调用方是否有权限；
- **远程代理**：在本地代表一个位于其他进程或机器上的对象，调用它的方法会变成一次网络请求；
- **智能引用**：访问对象时顺带做一些管理工作，比如计数、加锁。缓存代理也常被归入这一类。

### 和装饰器的区别

代理和装饰器的代码结构几乎一样：同样的接口，持有另一个对象，转交请求。区别在于**意图**：

| | 装饰器 | 代理 |
|---|---|---|
| 目的 | 给对象增加职责（打码、截断、计数） | 控制对对象的访问（何时创建、谁能用、是否走缓存） |
| 和真实对象的关系 | 通常由外部传入一个已经存在的对象 | 常常自己负责创建或找到真实对象（如 `LazyLesson`） |
| 叠加 | 常常叠很多层，每层一项职责 | 通常一两层 |

一个实用的判断方法：如果去掉这一层，功能还完整，只是少了点“附加”的东西，那多半是装饰器；如果去掉这一层，就失去了对“何时、谁、怎样接触真实对象”的控制，那多半是代理。不过，两者的边界并不总是清楚，比如缓存既可以说是“加了一项职责”，也可以说是“控制了访问”。叫什么名字不重要，重要的是这一层在做什么，以及为什么放在这里。

## 代价与边界

- **延迟不等于消除。** 虚代理把读文件的时间从“打开目录时”挪到了“第一次点开时”。如果学员点开的那一刻读文件很慢，他依然要等。而且读文件可能出错（文件被删除了），错误也被推迟到了点开的那一刻。
- **代理和真实对象的行为可能悄悄不同。** `PaidLesson.content()` 可能抛出 `PermissionError`，而 `RealLesson.content()` 从不抛出。调用方以为自己面对的是同一个接口，却要处理一种原本不存在的异常。这一点要在接口文档里写清楚。
- **保护代理不是安全边界的全部。** 任何能拿到里面那个 `LazyLesson` 或 `RealLesson` 的代码，都可以绕过检查。真正的权限控制，还要保证未授权的代码根本拿不到真实对象（比如服务器只把代理对象交给处理用户请求的代码），以及在数据源头（文件权限、数据库权限）上也有控制。
- **对象的身份变了。** 代理不是真实对象，`isinstance(lesson, RealLesson)` 不成立，依赖具体类型的代码会出错。

**什么时候不该用**：对象创建很便宜，或者没有访问控制的需求。几 KB 的讲义一次全部读进来，比任何延迟加载都简单，也不会有“点开时出错”的意外。

## Python 角度：属性级别的延迟加载，以及通用代理的坑

如果只是想延迟加载一个**属性**，Python 有现成的工具 `functools.cached_property`：

```python
class Lesson:
    def __init__(self, title: str, path: Path) -> None:
        self.title = title
        self.path = path

    @cached_property
    def text(self) -> str:
        return self.path.read_text("utf-8")  # 第一次访问时才读，之后直接用缓存的值
```

第一次访问 `lesson.text` 时执行函数，把结果存进实例的 `__dict__`；之后再访问就直接读存好的值。这不需要单独的代理类，适合“这个对象的某个字段很贵”的情况。它的缓存不会自动失效：文件后来被修改了，`lesson.text` 仍然是旧内容（测试 `test_cached_property_reads_once`），除非手动执行 `del lesson.text`，下次访问时才会重新读取。

另一个常见的想法是写一个“通用代理”，用 `__getattr__` 把所有属性访问都转给真实对象，一个类代理所有东西：

```python
class AnyProxy:
    """把所有找不到的属性都转给被代理的对象。"""

    def __init__(self, target: object) -> None:
        self._target = target

    def __getattr__(self, name: str):
        return getattr(self._target, name)
```

`proxy.content()` 能正常工作。但它有两个不太容易发现的坑（测试 `test_generic_proxy_pitfalls`）：

1. **特殊方法不经过 `__getattr__`。** `str(x)`、`len(x)`、`x == y`、`for i in x` 这类操作，Python 会直接到对象的**类型**上去找 `__str__`、`__len__` 等方法，不会调用实例的 `__getattr__`。`RealLesson` 定义了 `__str__`，`str(real)` 是 `《入门》`；而 `str(proxy)` 得到的是 `AnyProxy` 从 `object` 继承来的默认表示，类似 `<…AnyProxy object at 0x…>`。不报错，只是结果悄悄地不对。
2. **`isinstance` 检查失败。** 代理不是 `RealLesson` 的实例。

所以，除非有充分的理由，**优先写显式的代理类**，只实现确实需要的那几个方法，就像本章的 `LazyLesson` 和 `PaidLesson`。它们的代码更多，但行为清清楚楚。

## 小结

- 代理和真实对象实现同一个接口，站在调用方和真实对象之间，控制访问：延迟创建（虚代理）、检查权限（保护代理）、代表远程对象（远程代理）、顺带做管理工作（智能引用）。
- 代理和装饰器结构相同，区别在意图：装饰器增加职责，代理控制访问。
- 代理会改变一些行为：延迟的开销和错误、新的异常、对象身份。这些都要在接口说明里讲清楚。保护代理不能代替数据源头的权限控制。
- 在 Python 里，属性级别的延迟加载可以用 `functools.cached_property`；用 `__getattr__` 写通用代理时，要注意特殊方法和 `isinstance` 都不会被转发。

## 练习

网站上线了视频的“倍速播放”功能。视频转码很慢，于是要求：同一课、同一倍速的转码结果，第一次生成之后要缓存起来，下次直接用。

1. 你会把缓存写成一个新的代理，还是写进 `LazyLesson`？
2. 缓存代理应该放在 `PaidLesson` 的里面还是外面？如果放在外面，会出现什么问题？
3. 讲义文件更新后，缓存要怎样失效？

**思路提示**：写成一个独立的 `CachedLesson` 代理更清楚，每一层只管一件事。它必须放在 `PaidLesson` **里面**：如果放在外面，一个已报名的学员看过之后，结果进了缓存，未报名的学员再请求时，缓存层直接返回了内容，权限检查被跳过了。这是代理叠加顺序中最需要警惕的一类错误，一定要写测试覆盖。第 3 问涉及缓存失效，这是缓存最难的部分：可以把文件的修改时间或内容哈希作为缓存键的一部分，文件一变，键就变了，旧的缓存自然不再命中。`cached_property` 只能靠手动 `del` 来失效，它不知道文件什么时候变了，所以更适合“值不会变”的场合。

完整代码：
- [`examples/ch16_course_v1.py`](../../examples/ch16_course_v1.py)：一次读完所有讲义，没有权限检查
- [`examples/ch16_proxy.py`](../../examples/ch16_proxy.py)：虚代理、保护代理及组装
- [`examples/ch16_pythonic.py`](../../examples/ch16_pythonic.py)：`cached_property` 与通用代理的坑

测试：[`tests/test_ch16_proxy.py`](../../tests/test_ch16_proxy.py)。
