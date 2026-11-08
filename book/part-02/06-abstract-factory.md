# 第 06 章　抽象工厂 Abstract Factory

> 本章要回答：当程序需要好几个部件，而这些部件必须“成套”使用时，怎样保证不会有人拿错一件？抽象工厂和上一章的工厂方法有什么不同？

上一章的工厂只负责创建**一种**东西：一个渲染器。这一章的问题多了一个维度：程序要用到**几种**东西，它们之间有搭配关系，配错了不会报错，却会悄悄地做错事。

## 眼前的任务

一个社区图书馆每天早上给快到期的读者发还书提醒。借阅记录长这样：

```python
loans = [
    Loan("王芳", "城南旧事", date(2026, 3, 10)),
    Loan("李雷", "活着", date(2026, 3, 11)),
    Loan("赵敏", "围城", date(2026, 3, 20)),
]
```

`Loan` 是一个冻结的数据类，有读者、书名、到期日三个字段，还有一个 `key` 属性，把三者拼成一个字符串，用来识别“这一条借阅”。

程序做三件事：找出两天内到期的借阅；给每位读者写一条提醒；记下发过哪些，避免明天重复发送。提醒先写进一个发件箱文件 `outbox.txt`，由图书馆已有的短信程序负责真正投递；发送记录存在 `sent.json` 里。

3 月 9 日运行，发件箱里会多出两行：

```text
王芳，您借的《城南旧事》将于3月10日到期
李雷，您借的《活着》将于3月11日到期
```

## 不用模式的写法

第一版很直接。后来管理员提出：改了提醒的措辞之后，想先**演练**一遍，看看会发给谁、发什么，但不要真的发出去。于是函数多了一个 `dry_run` 参数：

```python
def send_reminders(
    items: list[Loan], today: date, outbox: Path, log: Path, dry_run: bool = False
) -> int:
    sent = set(json.loads(log.read_text("utf-8"))) if log.exists() else set()
    count = 0
    for loan in due_soon(items, today):
        if loan.key in sent:
            continue
        if dry_run:
            print("[演练]", reminder_text(loan))
        else:
            with outbox.open("a", encoding="utf-8") as f:
                f.write(reminder_text(loan) + "\n")
        sent.add(loan.key)
        count += 1
    log.write_text(json.dumps(sorted(sent), ensure_ascii=False), "utf-8")
    return count
```

演练时屏幕上打印出两条 `[演练] ……`，看起来一切正常。

**问题出在第二天早上。** 管理员先演练，再正式运行，正式运行返回 `0`，发件箱是空的。两位读者都没收到提醒。

原因在最后一行：演练只换掉了“怎么发送”，却没换掉“怎么记录”。`log.write_text` 照样执行，把两条借阅写进了正式的 `sent.json`。正式运行读到这份记录，以为已经发过了。测试 `test_dry_run_swallows_the_real_reminders` 稳定地复现了这个错误。

修起来只要一行：`if not dry_run: log.write_text(...)`。但这个错误的根源不在某一行，而在结构上。

## 变化带来的困难

“演练”不是一个开关，而是**一整套不同的部件**：

| 部件 | 正式运行 | 演练 |
|---|---|---|
| 发送 | 写进发件箱文件 | 打印到屏幕 |
| 发送记录 | 读正式记录，运行后写回 | 读正式记录，**不写回** |

两个部件必须一起切换。只换发送不换记录，就是上面的错误；只换记录不换发送，演练会真的把短信发出去，更糟。

在第一版里，这两个决定分散在函数的不同位置，各自用 `if dry_run` 判断。没有任何东西把它们绑在一起，漏掉一个也不会报错。

接着又来了第三个需求：写单元测试时，希望发送和记录都放在内存里，既不打印，也不碰文件。这又是一套部件。如果继续加开关，函数里就会出现 `dry_run` 和 `testing` 两个参数，四种组合里只有三种有意义，剩下一种是什么行为，没人说得清。

问题可以说得更准确一些：**程序需要好几种部件；部件有几个“家族”；同一次运行必须从同一个家族里取全部部件。**

## 抽象工厂：一个对象负责一整套

GoF 对抽象工厂的描述是：**提供一个接口，用于创建一系列相关或相互依赖的对象，而无需指定它们的具体类。**

第一步，先说清楚部件长什么样。和第 05 章一样，用 `Protocol` 描述，不要求继承：

```python
class Sender(Protocol):
    def send(self, text: str) -> None: ...


class SentLog(Protocol):
    def __contains__(self, key: str) -> bool: ...
    def add(self, key: str) -> None: ...
    def save(self) -> None: ...
```

每个家族各写一组部件。演练家族的发送记录很能说明“家族”的意思：它要**读**正式记录，这样才知道哪些已经发过，演练结果才和正式运行一致；但它**从不写回**：

```python
class PrintSender:
    def send(self, text: str) -> None:
        print("[演练]", text)


class ReadOnlySentLog(FileSentLog):
    def save(self) -> None:
        pass  # 演练不改变任何正式状态
```

第二步，定义“工厂”的接口：它有几种部件，就有几个创建方法。

```python
class ReminderServices(ABC):
    @abstractmethod
    def create_sender(self) -> Sender: ...

    @abstractmethod
    def create_sent_log(self) -> SentLog: ...
```

每个家族一个具体工厂。一个工厂里的所有创建方法，返回的都是同一家族的部件：

```python
class LiveServices(ReminderServices):
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def create_sender(self) -> Sender:
        return FileSender(self.folder / "outbox.txt")

    def create_sent_log(self) -> SentLog:
        return FileSentLog(self.folder / "sent.json")


class DryRunServices(ReminderServices):
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def create_sender(self) -> Sender:
        return PrintSender()

    def create_sent_log(self) -> SentLog:
        return ReadOnlySentLog(self.folder / "sent.json")
```

第三步，发送函数只认工厂，不再知道“演练”这回事：

```python
def send_reminders(items: list[Loan], today: date, services: ReminderServices) -> int:
    sender = services.create_sender()
    sent = services.create_sent_log()
    count = 0
    for loan in due_soon(items, today):
        if loan.key in sent:
            continue
        sender.send(reminder_text(loan))
        sent.add(loan.key)
        count += 1
    sent.save()
    return count
```

现在先演练、再正式运行，两次都返回 `2`，发件箱里是那两行提醒，演练结束后 `sent.json` 根本不存在。函数里没有一个 `if dry_run`，所以也没有“漏掉一个”的机会：**切换家族就是换一个工厂对象，部件不可能只换一半。**

测试用的第三个家族 `MemoryServices` 也照此写出，`send_reminders` 一行都不用改。

### 选工厂的那一步

命令行里的 `--mode live` 或 `--mode dry-run` 最终要变成一个工厂对象。这一步用的正是上一章的简单工厂函数：

```python
def services_for(mode: str, folder: Path) -> ReminderServices:
    factories = {"live": LiveServices, "dry-run": DryRunServices}
    try:
        return factories[mode](folder)
    except KeyError:
        raise ValueError(f"未知模式: {mode}") from None
```

两者并不冲突：简单工厂决定**用哪个家族**，抽象工厂负责**把这个家族的部件一件件交出来**。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 抽象工厂（AbstractFactory） | `ReminderServices` | 声明每种部件的创建方法 |
| 具体工厂（ConcreteFactory） | `LiveServices`、`DryRunServices`、`MemoryServices` | 创建同一家族的全部部件 |
| 抽象产品（AbstractProduct） | `Sender`、`SentLog` 协议 | 规定每种部件的接口 |
| 具体产品（ConcreteProduct） | `FileSender`、`PrintSender`、`ReadOnlySentLog` 等 | 各家族的具体部件 |
| 客户（Client） | `send_reminders` | 只通过抽象接口使用部件 |

### 和工厂方法的区别

两个名字都有“工厂”，关注点不同：

- **工厂方法**（第 05 章）：一个流程里有**一个**创建步骤，由子类决定创建什么。重点是“流程固定，创建的种类可变”。
- **抽象工厂**：一个对象提供**一组**创建方法，保证这组部件属于同一家族。重点是“部件要配套”。

两者经常一起出现：抽象工厂里的每个创建方法，本身就可以看作一个工厂方法。GoF 原书的典型实现正是这样。

## 代价与边界

- **增加家族容易，增加部件种类难。** 加一个“预发布环境”家族，写一个新的具体工厂就行。但如果发送提醒还需要第三种部件，比如一个可替换的时钟，就得在 `ReminderServices` 上加 `create_clock`，然后**修改每一个**具体工厂。GoF 原书也把这一点列为这个模式的主要缺点。
- **类的数量明显增加。** 本例为两个部件、三个家族写了一个抽象工厂、三个具体工厂，加上六个具体部件。如果只有一个家族，这些全是负担。
- **它只管“一起创建”，不管“一起使用”。** 工厂交出一套配好的部件，但如果调用方又自己 `new` 了一个 `FileSentLog` 混进来，模式拦不住。
- **抽象基类能防止“半个家族”。** 这是一个小好处：`ReminderServices` 的子类如果漏写了 `create_sent_log`，实例化时就会抛出 `TypeError`（见测试 `test_incomplete_family_cannot_be_created`），不会等到运行到一半才发现。

**什么时候不该用**：部件之间没有搭配约束，换掉其中一个不会让另一个出错。这时把各个部件分别作为参数传进去，就是最清楚的写法；没有“家族”，就不需要“家族工厂”。

## Python 角度：一组部件，一个函数

GoF 的抽象工厂每次调用 `create_xxx()` 都可以创建新对象。但在本例里，每次运行只在开头创建一次部件。这种情况下，Python 有更轻的写法：用一个冻结的数据类装下一套部件，每个家族一个普通函数。

```python
@dataclass(frozen=True)
class Kit:
    sender: Sender
    sent_log: SentLog


def live_kit(folder: Path) -> Kit:
    return Kit(FileSender(folder / "outbox.txt"), FileSentLog(folder / "sent.json"))


def dry_run_kit(folder: Path) -> Kit:
    return Kit(PrintSender(), ReadOnlySentLog(folder / "sent.json"))
```

`send_with_kit(loans, today, dry_run_kit(folder))` 的行为和抽象工厂版本完全一样。家族的搭配仍然集中在一处（`dry_run_kit` 函数里），`Kit` 的两个字段都是必填的，也不会出现“半套”。

那为什么不更进一步，把发送器和记录直接作为两个参数传给 `send_reminders`？因为那样调用方可以写出 `PrintSender()` 搭配 `FileSentLog(...)`，回到了本章开头的错误。**把部件打包成一个整体，正是在表达“它们必须一起选”。**

以下情况，经典的抽象工厂仍然值得：

- 部件需要**在运行过程中多次创建**，比如每处理一批数据就要一个新的连接或新的写入器。这时你需要的是“能造部件的对象”，而不是“已经造好的部件”。
- 家族由**别人**来扩展，你希望用抽象基类明确列出“一个家族必须提供哪些部件”。
- 家族本身有配置和状态，比如本例中正式家族要知道文件夹在哪里。用一个对象保存这些配置，比让每个函数都接收一遍更整齐。不过，像 `live_kit(folder)` 这样的函数也能做到。

## 小结

- 当程序需要几种部件，部件分成几个家族，同一次运行必须用同一家族时，就出现了抽象工厂要解决的问题。
- 抽象工厂把“同一家族的全部创建方法”放在一个对象上。切换家族就是换一个工厂，部件不会只换一半。
- 它让增加家族变得容易，却让增加部件种类变得困难：每加一种部件，所有具体工厂都要改。
- 在 Python 里，如果部件只在开始时创建一次，用一个数据类装下一套部件，再为每个家族写一个函数，通常就够了。

## 练习

图书馆想再加一个功能：每周日晚上，把下周到期的借阅汇总成一份清单，打印出来贴在服务台。这份清单只读借阅记录，不发提醒，也不需要发送记录。

1. 汇总清单要不要用 `ReminderServices`？如果用，它需要哪些部件？
2. 如果硬把汇总也放进 `ReminderServices`，加一个 `create_printer` 方法，会对现有的三个具体工厂产生什么影响？
3. 什么情况下，汇总清单也需要“正式／演练”两个家族？

**思路提示**：抽象工厂的边界是“一起切换的那组部件”。汇总清单和提醒不共享部件，也不需要一起切换，应该是一个独立的普通函数，参数里接收借阅记录和一个输出位置就够了。硬塞进 `ReminderServices` 会让三个具体工厂都多出一个和自己无关的方法，这正是“增加部件种类难”的代价在起作用。只有当汇总清单也会写入某种正式状态（比如标记“已通知服务台”），演练时需要和正式运行用不同的部件时，它才需要自己的家族。

完整代码：
- [`examples/ch06_reminders_v1.py`](../../examples/ch06_reminders_v1.py)：带 `dry_run` 开关的第一版（含错误）
- [`examples/ch06_abstract_factory.py`](../../examples/ch06_abstract_factory.py)：GoF 抽象工厂，三个家族
- [`examples/ch06_pythonic.py`](../../examples/ch06_pythonic.py)：用数据类装下一套部件

测试：[`tests/test_ch06_abstract_factory.py`](../../tests/test_ch06_abstract_factory.py)。
