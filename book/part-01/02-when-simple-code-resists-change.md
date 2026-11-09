# 第 02 章　当简单代码开始难以改变

> 本章要回答：重复的判断、共享的变化、意外的影响和复制粘贴，是怎样一步步出现的？

很少有代码是一开始就写坏的。更常见的情况是：第一版简洁清楚，之后每次需求变化，开发者都做了“在当时看来最合理”的小改动。几轮之后，代码里出现了错误，而且没有哪一步改动明显是错的。

这一章跟踪一个真实感很强的小程序，看困难究竟是怎样长出来的。我们要练的是**指出具体哪几行代码让修改变难**，而不是笼统地说“耦合太高”“扩展性差”。

## 第一版：一份数学成绩单

班主任想把数学成绩整理成一份名单，标出每个人是否及格。及格线 60 分。

```python
def class_report(names: list[str], scores: list[int]) -> list[str]:
    lines = []
    for name, score in zip(names, scores):
        result = "及格" if score >= 60 else "不及格"
        lines.append(f"{name} {score} {result}")
    return lines
```

`class_report(["小林", "小周"], [72, 48])` 得到 `["小林 72 及格", "小周 48 不及格"]`。数据是两份列表：姓名和分数，按位置一一对应；处理是逐个判断是否及格。

这段代码没有任何问题。接下来的四次变化，每一次都很普通。

## 四次普通的变化

**变化一：给家长发通知。** 学校要求给每位学生的家长发一句成绩通知。开发者小王打开 `class_report`，把及格判断复制出来，写了 `parent_notice`。复制粘贴是最快的办法，而且两处代码现在完全一致。

**变化二：物理及格线是 55 分。** 成绩单要支持多个科目，物理的及格线比较低。小王在 `class_report` 里加了一个 `if subject == "物理"`，然后想起家长通知里也有一份同样的判断，于是也改了。改一条规则要动两个地方，但他都记得。

**变化三：化学及格线是 50 分。** 一个月后，化学也调整了及格线。这次是同事小李改的。他找到了 `class_report`，加上了化学的分支。他不知道家长通知里还有一份复制品。

**变化四：成绩单开头显示中位数。** 小李又写了一个求中位数的函数，在成绩单第一行显示出来。

四次改动之后，代码是这样的：

```python
def class_report(subject: str, names: list[str], scores: list[int]) -> list[str]:
    lines = [f"{subject} 中位数：{median(scores)}"]
    for name, score in zip(names, scores):
        if subject == "化学":
            passed = score >= 50
        elif subject == "物理":
            passed = score >= 55
        else:
            passed = score >= 60
        lines.append(f"{name} {score} {'及格' if passed else '不及格'}")
    return lines


def parent_notice(subject: str, name: str, score: int) -> str:
    # 这段及格判断是从 class_report 复制过来的
    if subject == "物理":
        passed = score >= 55
    else:
        passed = score >= 60
    result = "已及格" if passed else "未及格，请留意"
    return f"{name} 家长：本次{subject} {score} 分，{result}。"
```

每一处单独看都说得过去。但这份代码里已经藏着两个真实的错误。

## 错误一：两处结论相反

小周化学考了 52 分。成绩单上写着：

```text
小周 52 及格
```

发给家长的通知却是：

```text
小周 家长：本次化学 52 分，未及格，请留意。
```

原因一眼就能看到：“及格线是多少”这条规则写在两个地方，变化三只改了其中一个。这就是**共享的变化**：同一条业务规则被两个功能使用，规则一变，两处都得跟着变；而代码里没有任何东西提醒你“这里还有一份”。

复制粘贴本身不是罪过。问题在于被复制的东西是**会变的规则**。如果复制的是一段永远不会变的格式代码，影响就小得多。

## 错误二：姓名和分数对不上

更隐蔽的是第二个错误。生成数学成绩单，实际输出是：

```text
数学 中位数：68.5
小林 48 不及格
小周 65 及格
小吴 72 及格
小郑 91 及格
```

中位数是对的，但名单错了：小林考了 72，小周才是 48。罪魁祸首在 `median` 里：

```python
def median(values: list[int]) -> float:
    values.sort()  # 就地排序：调用者手里的列表也被改了
    middle = len(values) // 2
    if len(values) % 2 == 1:
        return float(values[middle])
    return (values[middle - 1] + values[middle]) / 2
```

`list.sort()` 会**就地**修改列表。`class_report` 把自己的 `scores` 传给 `median`，回来时这份列表已经从小到大排好了，而 `names` 还是原来的顺序。两份靠位置对应的列表，就这样错开了。

这是一种**意外影响**：一个看起来只是“算一个数”的函数，悄悄修改了别人的数据。它之所以造成这么大的伤害，还因为第一版选择了“两个列表按位置对应”来表示数据。这种表示方式本身就很脆弱，任何一方被单独排序、插入或删除，对应关系就断了。

## 回头数一数：困难具体在哪里

把问题落实到代码上：

| 困难 | 出现在哪里 | 后果 |
|---|---|---|
| 判断重复 | `class_report` 和 `parent_notice` 各有一串 `if subject == ...` | 每加一科，要改两处 |
| 复制粘贴了会变的规则 | `parent_notice` 里的及格判断 | 变化三只改了一处，结论相反 |
| 意外影响 | `median` 里的 `values.sort()` | 调用者的列表被改，名单错位 |
| 脆弱的数据表示 | 姓名和分数分成两个列表 | 只要一方顺序变了，对应关系就断 |

注意这张表里没有“耦合太高”这种词。每一行都能指到具体的代码，也都能写成一个会失败的测试（见 [`tests/test_ch02_report.py`](../../tests/test_ch02_report.py) 中的 `BeforeRefactorBugsTest`）。**能写出失败测试的困难，才是值得动手解决的困难。**

## 修好它：只用最普通的手段

这些问题都不需要设计模式，用最基础的重构就够了：

```python
PASS_MARKS = {"物理": 55, "化学": 50}
DEFAULT_PASS_MARK = 60


def passed(subject: str, score: int) -> bool:
    return score >= PASS_MARKS.get(subject, DEFAULT_PASS_MARK)


def median(values: list[int]) -> float:
    ordered = sorted(values)  # 返回新列表，不碰调用者的数据
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2
```

三处改动各自对应一个困难：

1. **把规则放到一个地方。** 各科及格线变成一个字典 `PASS_MARKS`，判断变成一个函数 `passed`。成绩单和家长通知都调用它。以后再加“生物 58 分”，只改字典里的一行。
2. **不修改别人的数据。** `sorted(values)` 返回一个新列表，调用者的列表保持原样。
3. **换一种更稳的数据表示。** 姓名和分数放进同一个字典，例如 `{"小林": 72, "小周": 48, ...}`，对应关系由数据结构本身保证，不再依赖“第几个”。

改完之后，两个功能变成这样：

```python
def class_report(subject: str, scores: dict[str, int]) -> list[str]:
    lines = [f"{subject} 中位数：{median(list(scores.values()))}"]
    for name, score in scores.items():
        lines.append(f"{name} {score} {'及格' if passed(subject, score) else '不及格'}")
    return lines


def parent_notice(subject: str, name: str, score: int) -> str:
    result = "已及格" if passed(subject, score) else "未及格，请留意"
    return f"{name} 家长：本次{subject} {score} 分，{result}。"
```

现在小周化学 52 分，两边都说“及格”；数学名单也恢复正确。

## 什么时候这些手段不够了

上面用的是函数、字典和不修改输入，这是日常维护中最常用、也最该先用的工具。大多数“代码开始难改”的问题，到这一步就解决了。

设计模式通常出现在**这些手段开始不够用**的时候。比如：

- 及格规则不再只是一个分数线。体育只看“合格/不合格”，某些科目要算平时成绩加权，补考规则又不一样。规则从“一个数字”变成了“一段行为”，字典里放数字就不够了。这时值得考虑[第 17 章](../part-04/17-strategy.md)的“策略”，或者先试试“字典里放函数”。
- 成绩单要输出成网页、表格、短信等多种格式，而且格式还在增加。这时要考虑“生成什么样的输出对象”应该由谁决定（[第 05 章](../part-02/05-factory-method.md)“工厂方法”）。
- 成绩一录入，就有成绩单、家长通知、教务统计等好几个功能需要知道。这时可能需要[第 18 章](../part-04/18-observer.md)的“观察者”。

但现在，这些需求都还没有出现。为它们提前准备抽象，只会让现在的代码更难读。

## 小结

- 代码变难改通常不是一次坏决定造成的，而是一连串合理的小改动累积出来的。
- 常见的困难有：重复的判断、复制了会变的规则、修改了别人数据的函数、依赖位置对应的脆弱数据结构。
- 描述困难时，要指到具体代码，最好能写出一个会失败的测试。
- 先用最普通的手段：提取函数、把规则集中成数据、不修改输入、换更稳的数据表示。
- 只有当规则从“数据”变成“行为”，或者变化的种类不断增加时，才轮到设计模式。

## 练习

班主任又提了一个需求：成绩单要按分数从高到低排列。

1. 在修好的版本里，你会怎样实现？会不会再次碰到“修改了调用者数据”的问题？
2. 现在有人提议：“为了将来支持各种排序方式，我们先写一个 `SortStrategy` 抽象类，再写 `ByScoreDesc`、`ByName` 两个子类。”你同意吗？

**思路提示**：`sorted(scores.items(), key=lambda item: item[1], reverse=True)` 一行就能完成，而且返回新列表。目前只有一种排序需求，`key` 参数本身就是“可替换的排序规则”。为了“将来可能有”的需求提前建一套类，不划算。如果以后排序方式真的变多，而且要由用户在界面上选择，再把几个 `key` 函数放进一个字典也不迟。

完整代码：[`examples/ch02_report_v1.py`](../../examples/ch02_report_v1.py)（第一版）、[`examples/ch02_report_before.py`](../../examples/ch02_report_before.py)（四次变化之后）、[`examples/ch02_report_after.py`](../../examples/ch02_report_after.py)（重构之后），测试：[`tests/test_ch02_report.py`](../../tests/test_ch02_report.py)。
