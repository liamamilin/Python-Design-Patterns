# 第 08 章　原型 Prototype

> 本章要回答：当新对象应该“照着一个现成的对象做一份”时，复制到底复制了什么？浅拷贝和深拷贝怎样影响程序的行为？哪些东西复制时反而不该复制？

前两章的工厂和建造者，都是“按照代码里写好的方法造一个新对象”。这一章换个角度：有时候，新对象的样子事先并不写在代码里，而是**由某个已经存在的对象决定的**。最自然的做法就是照着它复制一份。复制听起来很简单，但在 Python 里，一不小心就会复制出一个和原件藕断丝连的对象。

## 眼前的任务

一家小健身房的教练用一个小程序给学员排训练计划。一份计划有标题，以及每个训练日要做的动作，每个动作有组数和次数：

```python
@dataclass
class Exercise:
    name: str
    sets: int
    reps: int


@dataclass
class Plan:
    title: str
    days: dict[str, list[Exercise]]
```

教练给新学员用的基础计划是这样的：

```python
def beginner_template() -> Plan:
    return Plan(
        "新手计划",
        {
            "周一": [Exercise("深蹲", 3, 10), Exercise("俯卧撑", 3, 8)],
            "周四": [Exercise("硬拉", 3, 8)],
        },
    )
```

## 不用模式的写法

只要计划写在代码里，`beginner_template()` 就是一个够用的工厂函数：每次调用都会造出一份全新的计划，学员之间互不影响。**这已经是好代码**，如果需求停在这里，什么都不用改。

## 变化：模板由教练在程序里调整

用了一段时间，教练们不满意了：基础计划每个季度都要调，每次都得找程序员改代码。于是程序加了一个功能，教练可以在界面上编辑模板，改好后保存，然后从模板出发给每位学员生成计划，再根据学员的情况个别调整。

这样一来，**模板不再是代码，而是运行时的一个对象**，是教练一点点改出来的。代码里没有一个函数能“重新造出”它。要给新学员生成计划，只能照着这个对象复制。

第一版的复制用了数据类自带的 `dataclasses.replace`，它会复制一个对象，同时替换指定的字段，看起来正合适：

```python
def plan_for(template: Plan, student: str) -> Plan:
    return replace(template, title=f"{student}的计划")
```

然后教练给小陈的深蹲加到 4 组：

```python
def show_the_trap() -> tuple[Plan, Plan, Plan]:
    template = beginner_template()
    chen = plan_for(template, "小陈")
    wang = plan_for(template, "小王")
    chen.days["周一"][0].sets = 4  # 只想给小陈的深蹲加到 4 组
    return template, chen, wang
```

运行结果：

```text
小王： Exercise(name='深蹲', sets=4, reps=10)
模板： Exercise(name='深蹲', sets=4, reps=10)
同一个字典吗？ True
```

只改了小陈，小王的计划和模板也一起变成了 4 组。

## 困难在哪里：浅拷贝

`replace` 确实创建了一个新的 `Plan` 对象，标题也确实换了。但它只复制了**最外面一层**：新 `Plan` 的 `days` 字段，指向的还是模板的**同一个字典**，字典里还是**同一批列表和 `Exercise` 对象**。

这叫**浅拷贝**（shallow copy）：新建一个外壳，里面的东西照原样引用。标准库的 `copy.copy` 也是浅拷贝，换成它不会有任何改善。测试 `test_copy_copy_has_the_same_problem` 展示了另一种表现：给小陈去掉深蹲，模板里的深蹲也没了。

这类错误特别难发现，因为它**不会立刻出现**。生成计划的那一刻一切正常，直到某个学员的计划被修改，才悄悄波及其他人。而且不报错，只是数据不对。

与之相对的是**深拷贝**（deep copy）：`copy.deepcopy` 会顺着对象的引用一路复制下去，字典、列表、每个 `Exercise` 都复制一份新的。

但“全部复制”也不总是对的。下面会看到，有些东西复制时恰恰**应该**共享。

## 原型：让对象自己负责复制自己

GoF 对原型模式的描述是：**用原型实例指定创建对象的种类，并且通过复制这个原型来创建新的对象。**

这里的关键不是“复制”这个动作，而是**谁知道该怎么复制**。浅拷贝还是深拷贝，哪些部分共享、哪些部分独立，这些只有这个类的作者最清楚。所以原型模式让对象自己提供一个复制方法，调用方只管说“给我一份”。

先把需求补完整。教练们维护着一个**动作库**：每个动作有名称和一段讲解视频。计划里的每一项引用动作库中的动作。某天教练给深蹲换了一段更清楚的视频，**所有计划都应该看到新视频**。

也就是说，复制一份计划时：

- 训练日、动作列表、组数和次数：每份计划**各自独立**；
- 引用的动作库条目：所有计划**共同使用**同一个。

`Movement` 用 `__deepcopy__` 声明自己在深拷贝时不被复制：

```python
@dataclass(eq=False)
class Movement:
    """动作库里的一个动作。教练改了讲解视频，所有计划都应该看到新视频。"""

    name: str
    video: str

    def __deepcopy__(self, memo: dict) -> Movement:
        return self  # 共享，不复制
```

`copy.deepcopy` 遇到一个对象时，会先看它有没有 `__deepcopy__` 方法，有的话就交给它决定怎么复制。返回 `self`，意思是“我不复制，直接引用原来的我”。（`eq=False` 让两个动作只在是同一个对象时才相等，因为动作库里的条目是按身份区分的。）

`Plan` 提供自己的复制方法：

```python
    def clone(self, title: str) -> Plan:
        twin = copy.deepcopy(self)
        twin.title = title
        return twin
```

现在，`template.clone("小陈的计划")` 得到的计划可以随意修改，不会影响模板；而教练修改动作库里深蹲的视频后，小陈的计划里看到的也是新视频（测试 `test_clone_is_independent` 和 `test_movements_stay_shared`）。

### 原型注册表

模板不止一个：新手、减脂、康复……教练需要按名字保存和取用。GoF 把这种按名字保存原型的对象称为**原型管理器**：

```python
class TemplateShelf:
    """原型注册表：按名字保存模板，需要时复制一份。"""

    def __init__(self) -> None:
        self._templates: dict[str, Plan] = {}

    def save(self, name: str, plan: Plan) -> None:
        self._templates[name] = plan.clone(plan.title)  # 存一份副本，之后再改草稿不影响已存的模板

    def new_plan(self, name: str, title: str) -> Plan:
        return self._templates[name].clone(title)
```

注意 `save` 里也复制了一次。教练保存模板之后，往往还会继续在同一份草稿上改；如果直接把草稿对象存进去，已经保存的模板会跟着草稿一起变。**复制发生在两个地方：存进来的时候，取出去的时候。** 测试 `test_shelf_keeps_its_own_copy` 验证了这一点。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 原型（Prototype） | 有 `clone` 方法的 `Plan` | 声明复制自己的接口 |
| 具体原型（ConcretePrototype） | 教练编辑出的各个模板对象 | 实现复制，决定哪些部分独立、哪些共享 |
| 客户（Client） | 给学员生成计划的代码 | 让原型复制自己来得到新对象 |
| 原型管理器 | `TemplateShelf` | 按名字保存和取出原型 |

在 C++ 里，原型模式还有一层意义：代码不用写出具体类名就能创建对象。在 Python 里这一层不重要，因为类本身就能当参数传递（见第 05 章）。Python 里原型模式留下的价值，主要就是本章的这一层：**新对象的内容由一个运行时的对象决定，而复制的规则由这个对象的类负责**。

## 代价与边界

- **深拷贝的成本和对象的大小成正比。** 对象引用得越多、越深，复制要做的事就越多。本例的计划很小，无所谓；如果模板里挂着大量数据，就要掂量一下。这里不给具体数字，因为它完全取决于对象的结构，需要时请用 `timeit` 实测。
- **深拷贝会复制所有“不该复制”的东西，除非你告诉它。** 打开的文件、数据库连接、线程锁，深拷贝时会直接抛出 `TypeError`；本例的动作库条目则相反，能复制，却不该复制。每加一个这种字段，都要想一想它在复制时应该怎样处理。
- **共享是一个需要写下来的决定。** `Movement.__deepcopy__` 返回 `self`，意味着任何人修改动作库条目都会影响所有计划。这正是本例想要的，但对读代码的人来说并不显眼，所以要加注释、写测试。
- **循环引用是安全的。** `deepcopy` 用 `memo` 字典记住已经复制过的对象，所以对象之间互相引用也不会无限复制下去。这一点不用自己处理。

**什么时候不该用**：新对象的样子可以用代码直接描述，比如本章开头的 `beginner_template()`。这时调用工厂函数比复制一个对象更直接，也没有任何“共享了不该共享的东西”的风险。只有当原件是**运行时才确定的**（用户编辑出来的、从文件读进来的、计算代价很高的），复制才比重新构造更合适。

## Python 角度：复制的问题，往往是“可变”的问题

本章所有的麻烦都来自一件事：复制出来的对象和原件**共享了可以被修改的部分**。如果共享的部分根本不能被修改，浅拷贝就是安全的。

Python 提供了表达“不可修改”的工具：冻结的数据类，以及元组：

```python
@dataclass(frozen=True)
class Exercise:
    name: str
    sets: int
    reps: int


@dataclass(frozen=True)
class Plan:
    title: str
    days: tuple[tuple[str, tuple[Exercise, ...]], ...]
```

这时 `replace(BEGINNER, title="小陈的计划")` 虽然仍是浅拷贝，却不会再出问题：任何人试图写 `plan.days[0][1][0].sets = 4`，都会得到 `FrozenInstanceError`。

代价是，“修改”要写成“造一个新的”：

```python
def change_sets(plan: Plan, day: str, name: str, sets: int) -> Plan:
    new_days = tuple(
        (d, tuple(replace(e, sets=sets) if d == day and e.name == name else e for e in exercises))
        for d, exercises in plan.days
    )
    return replace(plan, days=new_days)
```

这个函数返回一份新计划，原计划不变；没改动的 `Exercise` 对象直接被新计划引用，因为它们不会被修改，所以共享也没关系（测试 `test_change_returns_a_new_plan`）。

两种做法怎么选？

- 如果数据经常要被**局部修改**（教练每天都在调某个学员的某个动作），可变对象加 `clone` 更顺手，`change_sets` 这种写法会越来越啰嗦。
- 如果数据**生成之后基本只读**（发布出去的模板、配置、历史记录），不可变数据更安全，浅拷贝随便用，也不需要原型模式。

在两者之间，还有一个常见的折中：模板本身用不可变数据保存，给学员生成计划时转换成可变对象，供教练编辑。

## 小结

- 当新对象的样子由一个运行时的对象决定，而不是由代码决定时，复制这个对象是自然的做法。这就是原型模式要处理的情况。
- `copy.copy` 和 `dataclasses.replace` 都是浅拷贝，内部的列表、字典和对象仍与原件共享。修改副本可能悄悄改了原件。
- `copy.deepcopy` 复制整个对象图；用 `__deepcopy__` 可以声明某些部分应该共享而不复制。复制规则应该由类自己负责，这正是原型模式的核心。
- 如果共享的部分不可修改，浅拷贝就是安全的。在 Python 里，冻结的数据类和元组常常能让复制问题消失。

## 练习

教练提出：每份计划要记录**修改历史**，即一个字符串列表，比如 `["3月2日 深蹲改为4组"]`。从模板生成新计划时，新计划的历史应该从空白开始，而不是继承模板的修改记录。

1. 如果给 `Plan` 加一个 `history: list[str]` 字段，现在的 `clone` 会怎样处理它？结果符合要求吗？
2. 应该在哪里修改，才能让新计划的历史从空白开始？
3. 如果把历史记录改成存在另一张独立的表里（按计划编号查询），复制的问题还存在吗？

**思路提示**：`deepcopy` 会把模板的历史也完整复制一份，新计划一出生就带着模板的修改记录，不符合要求。这说明“怎么复制”不只是“浅还是深”的技术问题，还取决于每个字段的含义：动作库条目要共享，训练内容要独立复制，修改历史要重置。最直接的改法是在 `clone` 里复制之后把 `history` 设为空列表，这个规则写在 `Plan` 自己的方法里，正是原型模式的意义。第 3 问提示了另一个方向：如果历史不是计划对象的一部分，复制时自然就不用考虑它。把对象的边界划清楚，有时比写复杂的复制规则更简单。

完整代码：
- [`examples/ch08_copy_trap.py`](../../examples/ch08_copy_trap.py)：浅拷贝的陷阱
- [`examples/ch08_prototype.py`](../../examples/ch08_prototype.py)：`clone`、共享的动作库条目、原型注册表
- [`examples/ch08_pythonic.py`](../../examples/ch08_pythonic.py)：不可变数据

测试：[`tests/test_ch08_prototype.py`](../../tests/test_ch08_prototype.py)。
