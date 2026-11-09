# 第 09 章　单例 Singleton

> 本章要回答：程序里某样东西只能有一份时，真的需要一个“只能创建一次的类”吗？“唯一”到底是在什么范围内唯一？

单例大概是最容易学会、也最容易被滥用的模式。它的写法只有几行，但这几行背后藏着三个问题：唯一的范围有多大；第二次“创建”时发生了什么；以及测试怎么办。这一章从一个必须唯一的东西开始，把这三个问题逐个摆出来。

## 眼前的任务

一家银行网点要做一个排队取号程序。号码从 `A001` 开始依次递增：

```python
class TicketMachine:
    def __init__(self, prefix: str = "A") -> None:
        self.prefix = prefix
        self.count = 0

    def take(self) -> str:
        self.count += 1
        return f"{self.prefix}{self.count:03d}"
```

一开始只有大厅里的一台取号机。程序启动时创建一个 `TicketMachine`，每按一次按钮调用一次 `take()`。**这是好代码**，没有任何需要“设计”的地方。

## 不用模式的写法，以及第一个问题

后来网点加了手机预约：客户在手机上点“取号”，也拿到一个号码。负责这个功能的同事照着大厅取号机的写法，也在自己的类里创建了一个计数器：

```python
class Kiosk:
    """大厅里的取号机。"""

    def __init__(self) -> None:
        self.machine = TicketMachine()

    def press(self) -> str:
        return self.machine.take()


class PhoneBooking:
    """手机预约取号。"""

    def __init__(self) -> None:
        self.machine = TicketMachine()

    def book(self) -> str:
        return self.machine.take()
```

上线第一天：

```text
大厅： A001
手机： A001
```

两位客户拿着同一个号码，在窗口前争了起来。（测试 `test_two_machines_give_the_same_number`。）

问题很清楚：**号码序列只能有一个**，两个入口必须共用同一个计数器。第一反应往往是：让 `TicketMachine` 这个类自己保证只能有一个实例，谁再“创建”都拿到同一个。这正是 GoF 的单例。

## 单例：让类自己保证唯一

GoF 对单例的描述是：**保证一个类仅有一个实例，并提供一个访问它的全局访问点。**

在 Python 里，创建对象分两步：`__new__` 负责造出对象，`__init__` 负责初始化。要让“创建”总是返回同一个对象，常见的写法是改写 `__new__`：

```python
class BrokenTicketMachine:
    _instance: BrokenTicketMachine | None = None

    def __new__(cls) -> BrokenTicketMachine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.count = 0  # 每次调用 BrokenTicketMachine() 都会重新执行这一行
```

这个类的名字已经说明了结果：它是错的。`BrokenTicketMachine()` 第二次被调用时，`__new__` 确实返回了同一个对象，**但 Python 接着还会对这个对象调用一次 `__init__`**，计数器被清零。大厅已经发到 `A002`，手机预约的模块此时才第一次创建取号机，下一个号码又回到 `A001`（测试 `test_init_runs_again_and_resets_the_count`）。

这是 Python 单例最常见的错误，而且在只有一个使用者的时候完全看不出来。修正的方法是把初始化也放进 `__new__`，只在第一次创建时执行：

```python
class TicketMachine:
    _instance: TicketMachine | None = None
    _create_lock = threading.Lock()

    def __new__(cls) -> TicketMachine:
        with cls._create_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._count = 0
                instance._lock = threading.Lock()
                cls._instance = instance
        return cls._instance

    def take(self) -> str:
        with self._lock:
            self._count += 1
            return f"A{self._count:03d}"
```

现在 `Kiosk` 和 `PhoneBooking` 照旧写 `TicketMachine()`，拿到的却是同一个对象，号码依次是 `A001`、`A002`、`A003`。

代码里有两把锁，各管一件事：

- `_create_lock` 保护“检查是否已有实例，没有就创建”这一步。如果两个线程同时第一次调用 `TicketMachine()`，没有这把锁，它们可能都看到 `_instance is None`，各自创建一个，其中一个随后被覆盖，拿到它的那一方就和别人用的不是同一个计数器了。
- `_lock` 保护 `take()`。`self._count += 1` 是“读出、加一、写回”三步，Python 不保证另一个线程不会插在中间。

需要说明的是，这类竞争**能否在某次运行中被观察到**取决于时机，不是每次都会出现。测试 `test_unique_across_threads` 用 8 个线程各取 250 个号，验证有锁时 2000 个号码互不重复；但它不能证明没有锁就一定会出错。正确性来自锁的语义，而不是来自测试碰巧通过。

### 唯一的范围：只在一个进程里

网点的系统后来升级了：为了同时服务更多手机用户，预约服务用了多个进程。每个进程都 `import` 了取号模块，都调用了 `TicketMachine()`。

```text
进程一： ['A001', 'A002']
进程二： ['A001', 'A002']
```

号码又重复了。单例模式并没有失效，它一直在做它承诺的事：**每个进程里只有一个实例**。但每个进程有自己独立的内存，`TicketMachine._instance` 在每个进程里都是各自的一份。测试 `test_each_process_has_its_own_instance` 用两个新进程复现了这一点。

（这个例子用 `spawn` 方式启动新进程，子进程从头导入模块，所以都从 `A001` 开始。如果用 `fork` 方式，子进程会继承父进程当时的内存，计数会从父进程当时的值继续。但那仍然是一份**复制品**，各进程之后各数各的，号码同样会重复。）

“唯一”的范围可以分成几层：

| 范围 | 单例能保证吗 | 需要什么 |
|---|---|---|
| 一个线程内 | 能 | 什么都不用做 |
| 一个进程的多个线程之间 | 能，前提是创建和修改都加了锁 | `threading.Lock` |
| 多个进程之间（包括进程池） | **不能** | 把状态放到进程之外 |
| 多台机器之间 | **不能** | 数据库、专门的序号服务等 |

要让多个进程共用一个号码序列，计数必须放在所有进程都能访问、并且能正确处理并发的地方。标准库里的 SQLite 就可以做到：

```python
def take_from(path: Path) -> str:
    conn = sqlite3.connect(path, isolation_level=None, timeout=10)
    try:
        conn.execute("BEGIN IMMEDIATE")  # 立即加写锁，其他进程要等这次取号结束
        conn.execute("UPDATE counter SET n = n + 1")
        (n,) = conn.execute("SELECT n FROM counter").fetchone()
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
    return f"A{n:03d}"
```

`BEGIN IMMEDIATE` 让这次事务一开始就拿到数据库的写锁，“加一”和“读出新值”在同一个事务里完成，别的进程只能等它提交之后再来。两个进程各取两个号，得到的是 `A001` 到 `A004`，没有重复（测试 `test_unique_across_processes`）。

注意，此时“唯一”是靠**数据库文件**保证的，而不是靠 Python 里某个类只有一个实例。到了这一步，单例模式已经不再是答案的一部分。

## 代价与边界

单例解决了“两个入口共用一个计数器”，但也带来了它自己的问题：

- **它是一个隐藏的全局变量。** `Kiosk.__init__` 里写的是 `TicketMachine()`，看起来像是新建一个对象，实际上拿到的是全局共享的那一个。读代码的人从调用处看不出这一点。
- **测试之间互相影响。** 第一个测试取了三个号，第二个测试再取，就从 `A004` 开始了。为了让每个测试从头开始，`TicketMachine` 不得不加一个 `_reset_for_tests` 方法，这是一个专门给测试开的后门，正式代码里不应该被调用，却必须存在。
- **“只能有一个”很快就会变成“需要两个”。** 网点开了对公业务窗口，要发 `B` 字头的号码。可 `TicketMachine` 的设计就是“全世界只有一个”，想要第二个序列，只能改类的设计，或者再复制出一个 `BusinessTicketMachine` 类。“唯一”被写死在了类本身上。
- **唯一的范围比名字暗示的小。** 如上一节所示，单例只在一个进程内有效。如果真正的需求是“全系统唯一”，单例给人的安全感是虚假的。

**什么时候不该用**：几乎所有“我需要一个大家共用的对象”的场合。共用一个对象，和“这个类只能被实例化一次”，是两件不同的事。前者是很常见的需求，后者很少是真正的约束。

## Python 角度：创建一次，传给需要的人

回到问题本身：两个入口要用**同一个**计数器。最直接的办法是只创建一次，然后**交给**它们，而不是让它们各自去“创建”：

```python
class Kiosk:
    def __init__(self, machine: TicketMachine) -> None:
        self.machine = machine

    def press(self) -> str:
        return self.machine.take()
```

`PhoneBooking` 也一样，在构造时接收一个取号机。然后在程序启动的地方，把它们组装起来：

```python
def build_branch() -> tuple[Kiosk, PhoneBooking]:
    machine = TicketMachine()  # 唯一的实例在这里创建，再交给需要它的对象
    return Kiosk(machine), PhoneBooking(machine)
```

这里的 `TicketMachine` 是一个普通的类，没有改写 `__new__`，也没有类变量。“只有一个”不是类的性质，而是 `build_branch` 的**用法**：它只创建了一个，并把同一个对象交给了两个使用者。

前面列出的前三个代价都消失了（第四个，唯一的范围只在一个进程内，这种写法同样存在，解决办法仍然是上一节的数据库）：

- 共享是显式的：看 `Kiosk(machine)` 就知道它用的是外面传进来的取号机。
- 每个测试调用 `build_branch()` 就得到全新的一套，不需要任何重置后门（测试 `test_each_test_gets_a_fresh_machine`）。
- 对公窗口需要第二个序列？`TicketMachine("B")` 就是了（测试 `test_second_queue_is_just_another_instance`）。

这种做法通常被称为**依赖注入**：对象需要的东西由外部传入，而不是自己去找或自己去造。听起来像个大概念，在 Python 里它往往就是一个构造参数。

### 模块级对象

如果程序很小，组装一层显得多余，Python 还有一个更省事的写法：在模块里直接创建对象。

```python
# 另一种写法：模块级对象。模块在一个进程里只导入一次，这个对象自然只有一个。
default_machine = TicketMachine()
```

Python 第一次导入一个模块时执行它，然后把模块对象缓存在 `sys.modules` 里，之后再导入，拿到的都是缓存的那一个（测试 `test_module_level_object_is_imported_once`）。所以模块级的 `default_machine`，在一个进程里天然只有一个。这是 Python 里最常见的“单例”，标准库里也随处可见，比如 `random` 模块的那些函数，背后用的就是模块里创建好的一个随机数生成器对象。

它的局限和单例一样：仍然是全局状态，测试时仍然可能互相影响，范围仍然只在一个进程内。另外有一个容易踩到的坑：如果同一个文件既被当作脚本直接运行（模块名是 `__main__`），又被别的模块用包名导入，Python 会把它当作**两个不同的模块**，各执行一次，`default_machine` 也就有了两个。

三种写法的选择：

- **默认做法**：普通的类，在启动时创建一次，通过参数传给需要的对象。
- **小脚本、确实全进程只需要一个、而且不太需要测试**：模块级对象就够了。
- **经典单例（改写 `__new__`）**：几乎没有必须用它的场合。如果你在维护的代码已经这样写了，至少要确认初始化不会被重复执行，创建过程有锁保护，并且清楚它只在一个进程内有效。

## 小结

- “大家要共用同一个对象”是常见需求；“这个类只能被实例化一次”很少是真正的约束。不要把前者误当成后者。
- 在 Python 里改写 `__new__` 实现单例时，`__init__` 仍会在每次调用时执行，这是最常见的错误。创建和修改都需要锁，才能在多线程下保持正确。
- 单例只在一个进程内唯一。多进程或多台机器之间的唯一性，必须把状态放到进程之外，比如数据库。
- 优先在一个地方创建对象，再把它传给需要的人；小程序里，模块级对象是 Python 天然的单例。

## 练习

网点的程序里还有一个“营业配置”对象，包含营业时间、窗口数量等信息，从一个配置文件读取。几乎每个模块都要用到它。同事提议把它写成单例。

1. 配置对象和取号机都是“大家共用一个”，它们有什么本质区别？（提示：想想谁会**修改**它。）
2. 如果把配置写成单例，测试“周末只开 2 个窗口时的排队逻辑”会遇到什么麻烦？
3. 你会怎样提供这个配置？

**思路提示**：取号机有持续变化的状态，共用是为了让所有人看到同一个计数；配置在启动后通常只读，共用只是为了不重复读文件。只读的东西即使有多份也不会出错，所以“必须唯一”对它并不是真正的约束。写成单例后，测试“周末 2 个窗口”就得去修改全局的那一份，而且测试结束后要记得改回来，否则会影响下一个测试。更好的做法是：启动时读一次文件，得到一个冻结的数据类（见[第 07 章](07-builder.md)和[第 08 章](08-prototype.md)），作为参数传给需要它的对象；测试时直接构造一个 `windows=2` 的配置传进去。如果嫌层层传递麻烦，在入口模块里用一个模块级变量也可以，但要接受它带来的全局状态。

完整代码：
- [`examples/ch09_ticket_v1.py`](../../examples/ch09_ticket_v1.py)：两个入口各建一个计数器（含错误）
- [`examples/ch09_singleton.py`](../../examples/ch09_singleton.py)：错误的和修正后的单例，以及跨进程的演示
- [`examples/ch09_shared_counter.py`](../../examples/ch09_shared_counter.py)：用 SQLite 保证跨进程唯一
- [`examples/ch09_pythonic.py`](../../examples/ch09_pythonic.py)：创建一次再传入，模块级对象

测试：[`tests/test_ch09_singleton.py`](../../tests/test_ch09_singleton.py)。
