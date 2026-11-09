# 第 10 章　适配器 Adapter

> 本章要回答：两段已经写好、都不方便修改的代码，接口对不上时怎么办？适配器除了“改个名字”，还要承担哪些翻译工作？

从这一章开始进入第三部分：对象怎样**组合**起来。第一个问题最常见：手上有两块现成的东西，各自都没毛病，就是接不上。

## 眼前的任务

一家公司的总部有一套考勤报表模块，已经用了好几年。工资计算、排班、月度出勤统计都在用它。它的核心是打卡记录：

```python
@dataclass(frozen=True)
class Punch:
    employee: str
    at: datetime  # 带时区的本地时间
    kind: str  # "上班" 或 "下班"
```

报表从“考勤来源”取数据。任何对象，只要有一个返回打卡记录列表的 `punches()` 方法，就是一个考勤来源：

```python
class PunchSource(Protocol):
    def punches(self) -> list[Punch]: ...
```

总部考勤机的驱动 `LocalClock` 就是这样一个来源。迟到报表把所有来源的记录合在一起，找出每人每天第一次上班打卡晚于 9 点的情况：

```python
def late_report(sources: Iterable[PunchSource]) -> list[str]:
    return late_arrivals(p for source in sources for p in source.punches())
```

总部今天的结果是 `['03-09 李雷']`，李雷 9:05 到的。

## 变化：分店装了另一家的考勤机

公司开了一家分店，分店装的是一套云考勤，厂商提供了 Python SDK：

```python
class CloudAttendanceClient:
    def __init__(self, events: list[dict]) -> None:
        self._events = events  # 真实的 SDK 会通过网络取数据，这里用列表代替

    def fetch_events(self, since_ms: int = 0) -> list[dict]:
        return [e for e in self._events if e["ts"] >= since_ms]
```

它返回的数据长这样：

```text
{"uid": "E-2002", "ts": 1773019020000, "type": "IN"}
{"uid": "E-2002", "ts": 1773028800000, "type": "BREAK"}
```

老板想在同一张迟到报表里看到总部和分店的情况。

两边的东西都不能随便改：

- **报表模块**是共用的。工资、排班都依赖它，改动它要通知好几个团队、重新测试一大片。
- **SDK** 是厂商的代码，改了下次升级就会被覆盖。

而它们之间的差别，比方法名不同要多得多：

| 报表需要的 | SDK 给的 |
|---|---|
| 方法 `punches()` | 方法 `fetch_events()` |
| 员工姓名 | 工号 `uid`，姓名要查花名册 |
| 带时区的 `datetime` | 从 1970 年开始的**毫秒数** |
| `"上班"` / `"下班"` | `"IN"` / `"OUT"`，还有一种 `"BREAK"`（午休打卡） |

## 不用模式的写法

最快的办法是在报表模块里加一个分支，认出 SDK 对象就地转换：

```python
def late_report(sources: Iterable[object]) -> list[str]:
    punches: list[Punch] = []
    for source in sources:
        if isinstance(source, LocalClock):
            punches += source.punches()
        elif isinstance(source, CloudAttendanceClient):
            for e in source.fetch_events():
                if e["type"] not in ("IN", "OUT"):
                    continue
                at = datetime.fromtimestamp(e["ts"] / 1000, tz=BEIJING)
                kind = "上班" if e["type"] == "IN" else "下班"
                punches.append(Punch(BRANCH_STAFF[e["uid"]], at, kind))
        else:
            raise TypeError(f"不认识的考勤来源: {source!r}")
    return late_arrivals(punches)
```

它能用，结果是 `['03-09 孙浩', '03-09 李雷']`。但看看它带来了什么：

- **共用模块知道了一家具体厂商的细节**：毫秒时间戳、`"BREAK"`、分店的花名册。下次再开一家用第三种考勤机的分店，又要改这个函数，又要通知所有依赖它的团队。
- **而且只改了这一个函数。** 工资计算和排班也从考勤来源取数据，它们各自也要加一样的 `isinstance` 分支，否则把云考勤对象传给它们，会因为没有 `punches()` 方法而出错。
- 报表的签名从 `Iterable[PunchSource]` 退化成了 `Iterable[object]`，类型检查帮不上忙了。

## 适配器：在两者之间加一层翻译

GoF 对适配器的描述是：**将一个类的接口转换成客户希望的另一个接口，使原本由于接口不兼容而不能一起工作的类可以一起工作。**

我们不改报表，也不改 SDK，而是写一个新的类：它**对外**长得像报表认识的考勤来源，**对内**持有一个 SDK 对象，把所有的翻译工作都包在里面：

```python
class CloudClockAdapter:
    """对象适配器：持有一个 SDK 对象，对外提供 punches()。"""

    KINDS = {"IN": "上班", "OUT": "下班"}

    def __init__(self, client: CloudAttendanceClient, staff: dict[str, str], tz: tzinfo) -> None:
        self.client = client
        self.staff = staff
        self.tz = tz

    def punches(self) -> list[Punch]:
        result = []
        for e in self.client.fetch_events():
            kind = self.KINDS.get(e["type"])
            if kind is None:
                continue  # 午休打卡（BREAK）在报表里没有对应的概念，丢弃
            name = self.staff.get(e["uid"])
            if name is None:
                raise ValueError(f"花名册里没有工号 {e['uid']}")
            at = datetime.fromtimestamp(e["ts"] / 1000, tz=self.tz)
            result.append(Punch(name, at, kind))
        return result
```

使用时，把 SDK 对象包一层，和总部的考勤机放在一起交给报表：

```python
    branch = CloudClockAdapter(CloudAttendanceClient(BRANCH_EVENTS), BRANCH_STAFF, BEIJING)
    print(late_report([LocalClock(HQ_RECORDS), branch]))
```

报表模块一个字都没有改，结果同样是 `['03-09 孙浩', '03-09 李雷']`。工资和排班模块拿到这个适配器，也能直接用。下次再接入第三种考勤机，就再写一个适配器。

### 适配不只是改名字

这个适配器里真正有分量的，不是把 `fetch_events` 换成 `punches`，而是几个**翻译决定**：

1. **时区。** 毫秒时间戳是一个绝对时刻，本身不带“几点”的概念，要变成“9 点 17 分”，必须指定时区。同样的时间戳按北京时间解释是 9:17，按 UTC 解释是凌晨 1:17。测试 `test_time_zone_is_a_real_decision` 显示：如果适配器用错时区，报表里**一个迟到的人都没有**，而且不会报任何错。所以时区作为参数显式传入，而不是悄悄依赖服务器的系统设置。
2. **报表里没有的概念。** 云考勤有午休打卡，报表的世界里只有上班和下班。适配器选择丢弃它，并在注释里写明。如果将来报表需要统计午休，这个决定就要改。
3. **对不上的数据。** 花名册里查不到的工号，适配器选择立即报错，而不是填一个“未知员工”继续。对考勤来说，宁可让人发现花名册漏了人，也不要让一条打卡记录悄悄算到一个不存在的人头上。

这些决定都是业务判断，而适配器把它们集中在了**一个**地方。在不用模式的写法里，它们散在报表函数中间，和迟到的判断逻辑混在一起。

### 对象适配器和类适配器

GoF 描述了两种适配器。上面的是**对象适配器**：适配器**持有**被适配的对象。另一种是**类适配器**：适配器**继承**被适配的类，再补上目标接口的方法：

```python
class CloudClockClassAdapter(CloudAttendanceClient):
    """类适配器：继承 SDK 的类，再补上 punches()。"""

    def __init__(self, events: list[dict], staff: dict[str, str], tz: tzinfo) -> None:
        super().__init__(events)
        self._adapter = CloudClockAdapter(self, staff, tz)

    def punches(self) -> list[Punch]:
        return self._adapter.punches()
```

它也能工作，但有两个问题。第一，它的构造函数要照着 SDK 的构造函数写，SDK 升级改了构造参数，适配器也要跟着改。第二，SDK 的所有方法都一起暴露了出来：`fetch_events()` 照样可以调用（测试 `test_class_adapter_also_exposes_the_sdk`），使用者可能绕过翻译直接拿原始数据。在 Python 里，**优先使用对象适配器**。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 目标（Target） | `PunchSource` 协议 | 客户期望的接口 |
| 客户（Client） | `late_report` 及其他报表 | 只通过目标接口使用对象 |
| 被适配者（Adaptee） | `CloudAttendanceClient` | 已有的、接口不兼容的类 |
| 适配器（Adapter） | `CloudClockAdapter` | 实现目标接口，内部调用被适配者 |

## 代价与边界

- **多了一层，也多了一个可能出错的地方。** 翻译本身可能出错，比如上面的时区。所以适配器需要自己的测试，而且要测那些“翻译决定”，不只是测它能运行。
- **翻译可能丢信息。** 午休打卡被丢弃了。如果适配器丢掉的信息后来又需要了，要回头修改适配器，甚至扩展目标接口。
- **接口差别太大时，适配器会变成一个小系统。** 如果被适配的东西在概念上和目标差得很远，比如一边按“事件”推送，一边按“记录”拉取，适配器里会出现缓存、状态、重试等等。这时要想一想，是不是目标接口本身需要重新设计。
- **适配器容易越积越多。** 每接入一种来源就加一个适配器，这本身没问题；但如果几个适配器里出现了大段相同的转换代码，就该把共同的部分提取出来。

**什么时候不该用**：两边代码中至少有一边是你能**方便修改**的。如果报表模块是你自己刚写的、没有别人依赖，直接让它支持新的数据形状，或者调整接口，通常比加一层适配器更简单。适配器适用于两边都不该动的情况。

## Python 角度：让核心只接收数据

回头看报表模块：它其实分成两层。`late_report` 从**来源对象**取记录；真正的判断逻辑 `late_arrivals` 只接收**打卡记录本身**。如果其他报表也都像 `late_arrivals` 这样只接收数据，那么“接入新考勤机”就只需要一个转换函数：

```python
def punches_from_cloud(events: list[dict], staff: dict[str, str], tz: tzinfo) -> list[Punch]:
    return [
        Punch(staff[e["uid"]], datetime.fromtimestamp(e["ts"] / 1000, tz=tz), KINDS[e["type"]])
        for e in events
        if e["type"] in KINDS
    ]
```

```python
    client = CloudAttendanceClient(BRANCH_EVENTS)
    branch = punches_from_cloud(client.fetch_events(), BRANCH_STAFF, BEIJING)
    print(late_arrivals(HQ_RECORDS + branch))
```

这就是[第 01 章](../part-01/01-data-and-processing.md)里“数据与处理分开”的回报：核心逻辑只认数据，外部世界的各种格式在**边界**上一次转换完毕。转换函数也是适配器，只是它适配的是数据，不是对象。（这个简短版本对查不到的工号会直接抛出 `KeyError`，而不是像对象适配器那样给出中文提示。写在边界上的转换函数同样需要想清楚这些决定。）

什么时候仍然需要一个适配器**对象**？

- 客户代码要的是一个**对象**，并且会在不同时间多次调用它，比如报表每天调用一次 `punches()`，每次都应该拿到最新数据。转换函数只能转换已经取回的数据，而适配器对象可以在每次调用时去取。
- 目标接口有不止一个方法，或者需要保存状态（比如记住上次取到哪个时间点，下次只取新的）。
- 你不能改变客户代码的调用方式，它就是要调用 `source.punches()`。

## 小结

- 当两段都不方便修改的代码接口不一致时，适配器在中间加一层翻译，让两边都不用改。
- 适配器的价值主要在于把翻译决定（时区、单位、缺失的概念、对不上的数据）集中到一个地方，并让它们可以被单独测试。只改方法名的适配器很少见，也很少是难点。
- 在 Python 里优先使用对象适配器（持有被适配者），而不是类适配器（继承被适配者）。
- 如果核心逻辑只接收普通数据，适配器往往可以简化为边界上的一个转换函数。

## 练习

一年后，云考勤厂商发布了 SDK 2.0：`fetch_events` 改名为 `list_records`，时间戳从毫秒改成了带时区的 ISO 8601 字符串（如 `"2026-03-09T09:17:00+08:00"`），而且新增了 `"OVERTIME_IN"` 类型，表示加班签到。

1. 在适配器的写法下，需要修改哪些代码？报表模块需要改吗？
2. 在不用模式的写法下，需要修改哪些代码？
3. `"OVERTIME_IN"` 应该翻译成“上班”，还是丢弃？谁来做这个决定？

**思路提示**：适配器的写法只需要改 `CloudClockAdapter` 一个类（或者为 2.0 新写一个适配器，让两种版本并存一段时间）。时间戳变成 ISO 字符串后，可以用 `datetime.fromisoformat` 解析，它自带时区，适配器的 `tz` 参数可能就不需要了。不用模式的写法要改共用的报表函数，以及所有加了同样分支的工资、排班代码。第 3 问没有技术上的标准答案：加班签到算不算“上班打卡”，会直接影响迟到统计，这需要问人事部门。适配器的作用是让这个决定**有一个明确的地方可以写下来**，而不是让它散落在各处。

完整代码：
- [`examples/ch10_attendance.py`](../../examples/ch10_attendance.py)：已有的考勤报表模块
- [`examples/ch10_cloud_sdk.py`](../../examples/ch10_cloud_sdk.py)：云考勤 SDK（模拟）
- [`examples/ch10_report_v1.py`](../../examples/ch10_report_v1.py)：在报表里加 `isinstance` 分支
- [`examples/ch10_adapter.py`](../../examples/ch10_adapter.py)：对象适配器与类适配器
- [`examples/ch10_pythonic.py`](../../examples/ch10_pythonic.py)：边界上的转换函数

测试：[`tests/test_ch10_adapter.py`](../../tests/test_ch10_adapter.py)。
