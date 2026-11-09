# 第 21 章　模板方法 Template Method

> 本章要回答：几段流程大体相同、只有个别步骤不同时，怎样让相同的部分只写一次？由父类控制流程、子类填写步骤，和把步骤作为函数传进去，各有什么得失？

[第 05 章](../part-02/05-factory-method.md)里，`Document.build` 固定了生成文档的流程，其中“创建渲染器”这一步留给子类决定。当时说过，工厂方法常常就是模板方法中“负责创建”的那一步。这一章把模板方法本身讲清楚。

## 眼前的任务

一所学校的体育节和艺术节都要用程序算比赛成绩。

跳水比赛：5 位裁判打分，去掉一个最高分和一个最低分，剩下三个分数相加，再乘以动作的难度系数。

校园歌手大赛：3 位评委打分，取平均分；演唱超时的扣 0.5 分。

两种比赛最后都要输出名次，**同分的选手名次并列**，下一名跳过相应的名次（两人并列第 1，下一位是第 3）。

## 不用模式的写法

体育老师先写了跳水的计分函数，几周后音乐老师照着它写了歌手比赛的：

```python
def singing_results(entries: list[Entry]) -> list[str]:
    for e in entries:
        if len(e.judges) != 3:
            raise ValueError(f"{e.name}：歌手比赛需要 3 位评委的分数")
    scored = []
    for e in entries:
        score = round(sum(e.judges) / len(e.judges), 2)
        if e.overtime_s > 0:
            score -= 0.5
        scored.append((round(score, 2), e.name))
    scored.sort(key=lambda pair: -pair[0])
    return [f"{i}. {name} {score:.2f}" for i, (score, name) in enumerate(scored, 1)]  # 没有并列
```

两个函数都是一样的步骤：检查裁判人数、逐个算分、扣分、排序、排名输出。**单独看每一个，都是好代码。**

## 变化：同一个修复只进了一个副本

跳水比赛先发现了并列的问题：两位选手同为 70.50 分，程序却排出了第 1 和第 2。体育老师修好了跳水的函数。音乐老师的函数是在那之前复制的，所以歌手比赛里，小雨和木子都是 8.83 分，一个第 1、一个第 2（测试 `test_tie_fix_only_in_one_copy`）。

明年还要加书法比赛、朗诵比赛。每多一种比赛就多一份复制，“同分并列”“检查裁判人数”这样的共同规则，就要在每份复制里各维护一遍。

## 困难在哪里

两个函数的**流程**是一样的，不同的只是其中几个**步骤**：

| 步骤 | 跳水 | 歌手 |
|---|---|---|
| 检查裁判人数 | 5 位 | 3 位 |
| 算分 | 去掉最高最低，乘难度系数 | 平均分 |
| 扣分 | 无 | 超时扣 0.5 |
| 排序、并列排名、输出 | 相同 | 相同 |

我们希望：流程只写一次，每种比赛只写它不同的那几步。

## 模板方法：父类定流程，子类填步骤

GoF 对模板方法的描述是：**定义一个操作中的算法的骨架，而将一些步骤延迟到子类中。模板方法使得子类可以不改变一个算法的结构即可重定义该算法的某些特定步骤。**

父类 `Contest` 写出完整的流程：

```python
class Contest(ABC):
    judges_required = 3

    def results(self, entries: list[Entry]) -> list[str]:
        """模板方法：流程固定，子类不应重写它。"""
        for e in entries:
            self.validate(e)
        scored = [(round(self.score(e) - self.penalty(e), 2), e.name) for e in entries]
        scored.sort(key=lambda pair: -pair[0])
        return self.format(scored)
```

`results` 就是**模板方法**。它调用的几个步骤分成两类：

- **必须由子类提供的步骤**，声明为抽象方法。每种比赛算分方式都不同，父类没有合理的默认做法：

```python
    @abstractmethod
    def score(self, e: Entry) -> float:
        """必须由子类提供：这项比赛怎么算分。"""
```

- **钩子**（hook）：父类给出一个默认做法，子类**可以**覆盖，不覆盖也能工作。比如扣分，大多数比赛不扣分：

```python
    def penalty(self, e: Entry) -> float:
        """钩子：默认不扣分，子类可以覆盖。"""
        return 0.0
```

裁判人数检查和排名输出也是钩子，默认做法就是共同的规则。“同分并列”只写在一处：

```python
def rank_lines(scored: list[tuple[float, str]]) -> list[str]:
    lines, rank = [], 0
    for i, (score, name) in enumerate(scored, 1):
        if i == 1 or score != scored[i - 2][0]:
            rank = i  # 同分并列，下一名跳过相应的名次
        lines.append(f"{rank}. {name} {score:.2f}")
    return lines
```

每种比赛现在只写自己不同的部分：

```python
class Diving(Contest):
    judges_required = 5

    def score(self, e: Entry) -> float:
        return sum(sorted(e.judges)[1:-1]) * e.difficulty  # 去掉最高和最低分，乘难度系数


class Singing(Contest):
    def score(self, e: Entry) -> float:
        return sum(e.judges) / len(e.judges)

    def penalty(self, e: Entry) -> float:
        return 0.5 if e.overtime_s > 0 else 0.0
```

```text
['1. 林 70.50', '1. 陈 70.50', '3. 吴 65.60']
['1. 小雨 8.83', '1. 木子 8.83', '3. 阿杰 8.33']
```

两种比赛的并列都正确了（测试 `test_both_contests_share_the_same_ranking`）。明年加书法比赛，只需要写一个 `score` 方法（测试 `test_new_contest_only_fills_in_the_steps`）。忘了写 `score` 的话，`Contest` 是抽象类，连对象都创建不出来（测试 `test_score_is_required`）。

### 好莱坞原则

模板方法有一个常被提到的特点：**父类调用子类，而不是子类调用父类。** 子类只是提供几个方法，什么时候调用、按什么顺序调用，全由父类的 `results` 决定。这常被概括为“别打电话给我们，我们会打给你”。

这正是它和普通继承的区别。普通继承里，子类常常调用 `super()` 来复用父类的代码，控制权在子类；模板方法里，控制权始终在父类。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 抽象类（AbstractClass） | `Contest` | 定义模板方法 `results`，声明抽象步骤，提供钩子的默认实现 |
| 具体类（ConcreteClass） | `Diving`、`Singing` | 实现抽象步骤，按需覆盖钩子 |

### 和工厂方法的关系

回头看[第 05 章](../part-02/05-factory-method.md)的 `Document.build`：它固定了“写标题、挑任务、逐条写、拼起来”的流程，其中 `create_renderer()` 由子类实现，`select()` 是一个有默认做法的钩子。所以 `Document.build` 就是一个模板方法，而 `create_renderer` 是它的一个步骤，恰好这一步的工作是**创建对象**，于是有了“工厂方法”这个专门的名字。这就是[第 05 章](../part-02/05-factory-method.md)所说的“工厂方法常常就是模板方法中负责创建的那一步”。

### 标准库里的模板方法

Python 程序员每天都在用模板方法，只是不一定注意到：

- `unittest.TestCase`：运行一个测试时，框架依次调用 `setUp()`、测试方法、`tearDown()`。你只需要覆盖这几个方法，调用顺序由 `TestCase` 决定。`setUp` 和 `tearDown` 就是默认什么都不做的钩子。
- `socketserver.BaseRequestHandler`：处理一个网络请求时，依次调用 `setup()`、`handle()`、`finish()`，子类通常只覆盖 `handle()`。

## 代价与边界

- **流程被继承锁死。** 子类只能改变父类允许改变的步骤。如果某种比赛需要在“算分”和“扣分”之间加一步（比如歌手比赛要先核对评委是否回避），要么修改父类的模板方法，影响所有比赛；要么在子类里重写 `results`，模板就失去了意义。
- **读代码要在父子类之间来回跳。** 想知道跳水比赛的完整计分过程，要同时读 `Contest.results` 和 `Diving.score`，还要知道哪些钩子被覆盖了、哪些用的是默认值。
- **父类的修改影响所有子类。** 把排名规则改成“同分按年龄排序”，所有比赛都会跟着变。这有时正是你想要的（并列规则统一修复），有时则是意外。
- **“子类不应重写模板方法”只是一个约定。** Python 没有 `final` 关键字来阻止重写（`typing.final` 只对类型检查器有效，运行时不会阻止）。

**什么时候不该用**：只有两种情况，而且以后不会增加。把共同的部分（比如排名）提取成一个函数，两个计分函数各自调用它，往往就够了。这是比模板方法更轻的复用方式：只共享**一个步骤**，不共享**整个流程**。

## Python 角度：流程是函数，步骤是参数

模板方法用继承来填写步骤。在 Python 里，步骤也可以作为**函数参数**传进去，流程本身就是一个普通函数：

```python
def results(
    entries: list[Entry],
    score: Callable[[Entry], float],
    judges: int = 3,
    penalty: Callable[[Entry], float] = lambda e: 0.0,
) -> list[str]:
    for e in entries:
        if len(e.judges) != judges:
            raise ValueError(f"{e.name}：需要 {judges} 位裁判的分数")
    scored = [(round(score(e) - penalty(e), 2), e.name) for e in entries]
    scored.sort(key=lambda pair: -pair[0])
    return rank_lines(scored)
```

```python
    print(results(singers, average, penalty=lambda e: 0.5 if e.overtime_s else 0.0))
```

结果和 `Singing().results(singers)` 完全一样（测试 `test_same_results_with_functions`）。“抽象步骤”成了必填参数，“钩子”成了有默认值的参数。

这其实就是[第 17 章](17-strategy.md)的策略：把可变的部分作为对象（函数）传进去。模板方法和策略解决的是同一类问题，区别在于手段：

| | 模板方法 | 把步骤作为参数传入 |
|---|---|---|
| 怎样提供可变步骤 | 继承，覆盖方法 | 组合，传入函数或对象 |
| 步骤之间共享数据 | 方便：都能访问 `self` | 要通过参数传递 |
| 一次运行中替换步骤 | 不行，由类决定 | 可以，每次调用传不同的参数 |
| 新增一种情况 | 写一个子类 | 写一个函数，或者直接在调用处传 `lambda` |

选择的依据：

- **步骤少、彼此独立**：传函数。就像本例的歌手比赛，一个算分函数加一个扣分函数。
- **步骤多、步骤之间要共享状态，或者你在写一个框架，希望使用者通过继承来扩展**：模板方法。像 `unittest.TestCase`，`setUp` 里准备的数据要在测试方法里用，`tearDown` 里清理，它们通过 `self` 自然地共享状态，这时继承比传一串函数清楚得多。

## 小结

- 当几段流程大体相同、只有个别步骤不同时，模板方法让父类写出完整的流程，子类只填写不同的步骤。必须提供的步骤是抽象方法，有默认做法的步骤是钩子。
- 控制权在父类：子类提供步骤，何时调用由父类决定。
- 工厂方法常常是模板方法中负责创建对象的那一步。`unittest.TestCase` 等标准库组件是模板方法的日常例子。
- 在 Python 里，步骤少时把它们作为函数参数传入更灵活；步骤多、需要共享状态或者面向“通过继承扩展”的使用者时，模板方法更合适。

## 练习

学校决定，所有比赛的成绩单在输出之前，都要先经过教务处的“复核”：如果某位选手的最高分和最低分相差超过 3 分，要在名字后面加上“（待复核）”。

1. 这条规则应该加在模板方法的哪里？需要修改几个类？
2. 如果书法比赛的组织者说：“我们的评分本来就差异很大，不要这条规则”，怎么办？
3. 在“把步骤作为参数传入”的写法里，同样的需求要怎样实现？

**思路提示**：这是“所有比赛共同的新步骤”，正是模板方法擅长的情况：在 `Contest.results` 里加一步，所有子类自动获得，一个子类都不用改。为了让书法比赛可以关掉它，把这一步做成钩子（比如 `needs_review(e)`，默认按 3 分的规则判断），书法比赛覆盖它、返回 `False`。在传函数的写法里，要给 `results` 加一个参数，并在每个调用处决定传什么，或者依赖一个合适的默认值。这个练习展示了模板方法的优势场景：**给所有子类统一增加一个步骤**。代价是，所有比赛都必须接受这个流程的变化，除非它是一个可以覆盖的钩子。

完整代码：
- [`examples/ch21_contest_v1.py`](../../examples/ch21_contest_v1.py)：两个复制出来的计分函数（含错误）
- [`examples/ch21_template_method.py`](../../examples/ch21_template_method.py)：`Contest` 模板方法与两种比赛
- [`examples/ch21_pythonic.py`](../../examples/ch21_pythonic.py)：流程函数与步骤参数

测试：[`tests/test_ch21_template_method.py`](../../tests/test_ch21_template_method.py)。
