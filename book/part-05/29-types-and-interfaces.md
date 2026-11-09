# 第 29 章　类型与接口的轻量表达

> 本章要回答：类型标注、`Protocol`、`ABC`、`dataclass`、`NewType`、`TypedDict` 各自能保证什么，不能保证什么？怎样用它们表达设计，而不是为了类型而写类型？

前面几乎每一章都用到了 `Protocol` 描述接口、用 `dataclass` 表示数据、用 `ABC` 强制子类实现方法。[第 03 章](../part-01/03-python-building-blocks.md)初步比较过它们。这一章把它们放在一起，回答一个具体的问题：**写了这些，到底有什么东西被检查了？由谁检查，在什么时候检查？**

## 一个最重要的事实

先看一个函数：

```python
def total_fee(visits: int, price: int) -> int:
    return visits * price
```

标注说两个参数都是整数。如果传入一个字符串 `"3"` 呢？

```text
>>> total_fee("3", 2)
'33'
```

**没有报错**，而是返回了字符串 `"33"`（测试 `test_wrong_type_runs_and_gives_a_wrong_answer`）。Python 在运行时**不检查**类型标注。标注对解释器来说只是附加在函数上的一些信息。字符串乘以整数在 Python 里恰好是合法操作（重复字符串），于是错误的输入变成了错误的结果，而不是一个异常。

那么标注有什么用？它们服务于两类读者：

- **人**：读代码的人一眼就知道参数应该是什么；
- **类型检查器**：比如 mypy、pyright。它们在**运行之前**读代码，发现 `total_fee("3", 2)` 这样的调用并报告错误。

所以理解这一章的关键是区分**两个时间点**：类型检查器在运行前做的静态检查，和程序运行时真正发生的检查。下面每一种工具，都要问清楚它在哪个时间点起作用。

## 场景：宠物医院预约

一家宠物医院做了一个预约小程序。宠物、主人各有编号，预约时要记录主人、宠物和时间段，预约后给主人发提醒短信。

## `NewType`：只给类型检查器看的区分

预约函数的两个编号都是整数，很容易传反：

```python
PetId = NewType("PetId", int)
OwnerId = NewType("OwnerId", int)


def book(owner: OwnerId, pet: PetId, slot: str) -> str:
    return f"主人 {owner} 为宠物 {pet} 预约了 {slot}"
```

`NewType` 为整数创建了两个“名义上不同”的类型。如果写成 `book(PetId(7), OwnerId(3), ...)`，参数顺序反了，类型检查器会报告：期望 `OwnerId`，得到 `PetId`。

但在**运行时**，`PetId(7)` 就是整数 `7`，没有任何包装，传反了照样执行，结果是“主人 7 为宠物 3 预约了周六上午”（测试 `test_newtype_is_the_plain_value_at_runtime`）。`NewType` 的全部价值在静态检查，它几乎没有运行时开销，也没有运行时保护。

## `dataclass`：结构，不是校验

宠物的信息用数据类表示，种类用 `Literal` 限定为猫或狗：

```python
Species = Literal["猫", "狗"]


@dataclass
class Pet:
    name: str
    species: Species
    weight_kg: float
```

`Pet("团子", "兔", "4")`：种类不在允许范围里，体重是字符串。数据类会**照样创建**这个对象（测试 `test_fields_are_not_validated`）。`dataclass` 根据标注生成 `__init__`、`__repr__`、`__eq__`，但不检查传入的值。`Literal` 同样只对类型检查器有效。

如果数据来自外部（表单、文件、网络），**校验必须自己写**。数据类提供了一个合适的位置：`__post_init__`，它在 `__init__` 执行完之后被调用：

```python
    def __post_init__(self) -> None:
        if self.species not in ("猫", "狗"):
            raise ValueError(f"本院只接诊猫和狗，不接诊：{self.species}")
        if not isinstance(self.weight_kg, (int, float)) or not 0 < self.weight_kg < 100:
            raise ValueError(f"体重不合理：{self.weight_kg!r}")
```

现在兔子、字符串体重、0 公斤都会在创建时被拒绝（测试 `test_post_init_validates`）。[第 07 章](../part-02/07-builder.md)的 `SearchFilter`、[第 25 章](../part-04/25-memento.md)的 `from_json` 都是同样的思路：**在数据进入程序的边界上校验一次，之后程序内部就可以信任这些对象。**

## `Protocol`：结构化的接口

发提醒的部分，用 `Protocol` 描述“能发通知的东西”：

```python
@runtime_checkable
class Notifier(Protocol):
    def notify(self, owner: OwnerId, text: str) -> None: ...
```

任何有 `notify(owner, text)` 方法的类，不需要继承 `Notifier`，类型检查器就认为它符合这个接口。这叫**结构化类型**（也常被称为“静态的鸭子类型”）。短信、微信、测试用的假对象，都可以各自实现，互不相干。

加上 `@runtime_checkable` 之后，还可以在运行时用 `isinstance` 检查。但[第 03 章](../part-01/03-python-building-blocks.md)提醒过：这个检查**只看有没有这个名字的方法，不看参数和返回值**。一个 `notify(self)` 什么参数都不接受的类，`isinstance(..., Notifier)` 照样是 `True`（测试 `test_runtime_checkable_only_checks_the_name`）。真正的签名检查，仍然要靠类型检查器。

## `ABC`：运行时强制实现

抽象基类在运行时提供了一个真实的保证：

```python
class Reminder(ABC):
    @abstractmethod
    def remind(self, pet: PetId) -> str: ...
```

继承 `Reminder` 却没有实现 `remind` 的类，在**创建实例时**就会抛出 `TypeError`（测试 `test_abc_checks_at_instantiation`）。前面很多章都用到了这个保证：[第 06 章](../part-02/06-abstract-factory.md)防止“半个家族”，[第 07 章](../part-02/07-builder.md)防止建造者漏掉一个步骤，[第 26 章](../part-04/26-visitor.md)防止访问者漏掉一种元素。

它的检查也只到“方法存在”为止，不检查方法的参数是否正确。另外，`ABC` 提供了一个 `register` 方法，可以把任意类登记为“虚拟子类”，这样 `isinstance` 会返回 `True`，**但不做任何检查**，即使那个类根本没有 `remind` 方法（测试 `test_register_skips_the_check`）。这是为了兼容无法修改的已有类型而设计的，用的时候要清楚自己放弃了什么。

## `TypedDict`：给字典的结构写说明

预约数据经常以 JSON 的形式进出。用 `TypedDict` 可以说明这个字典应该有哪些键、每个键是什么类型：

```python
class VisitJson(TypedDict):
    pet: int
    slot: str
```

类型检查器会检查对这个字典的读写是否符合声明。在运行时，`VisitJson(pet=7, slot="周六上午")` 创建的就是一个**普通的 `dict`**，`VisitJson(pet="七", slot=3)` 也一样能创建（测试 `test_typed_dict_is_a_plain_dict`）。它适合描述“JSON 长什么样”，但从外部读进来的 JSON 是否真的长这样，仍然要另外校验。

## 汇总：谁在什么时候检查什么

| 工具 | 类型检查器（运行前） | 运行时 |
|---|---|---|
| 参数和返回值标注 | 检查调用是否匹配 | **不检查** |
| `NewType` | 区分名义上不同的类型 | 就是原来的值，**不检查** |
| `Literal` | 检查取值是否在列举范围内 | **不检查** |
| `dataclass` 字段标注 | 检查构造参数 | **不检查**；需要校验就写 `__post_init__` |
| `Protocol` | 检查方法名和签名 | 默认不能用于 `isinstance`；加 `@runtime_checkable` 后只检查方法名 |
| `ABC` + `@abstractmethod` | 检查 | 实例化时检查抽象方法是否都已实现，不检查签名 |
| `TypedDict` | 检查键和值的类型 | 就是普通的 `dict`，**不检查** |

表里的“不检查”不是缺点，而是 Python 的设计选择：类型标注是可选的、渐进的，不会拖慢程序运行，也不会让没有标注的旧代码无法运行。但它意味着：**运行时需要保证的事情，必须用运行时的手段去保证**，比如 `__post_init__`、显式的校验函数、抽象基类。

## 不为类型而类型

类型标注是表达设计的工具，不是目的。几条经验：

- **在边界上写得清楚，在内部写得简洁。** 模块对外的函数、跨团队使用的接口，标注要准确完整；一个三行的内部辅助函数，标注可以少一些。
- **标注要描述你真正需要的，不要更多。** 一个函数只是遍历参数，就标 `Iterable[Record]`，而不是 `list[Record]`，这样调用方传生成器也可以。反过来，不要为了“通用”写出 `Callable[[Mapping[str, Sequence[tuple[int, ...]]]], ...]` 这种谁也读不懂的类型；如果类型复杂到需要这样写，往往说明数据应该有一个名字，写成一个 `dataclass`。
- **`Protocol` 和 `ABC` 选哪个？** 需要运行时强制（漏写就立即报错），或者希望别人通过继承来扩展：`ABC`。只想说明“需要什么方法”，不想要求继承，尤其是要接纳别人写的、无法修改的类：`Protocol`。
- **不要用运行时类型检查代替设计。** 函数开头写一串 `if not isinstance(x, int): raise TypeError` 通常不是好主意。只在数据进入程序的地方校验，内部依靠类型检查器和测试。

## 小结

- Python 的类型标注在运行时不被检查。它们写给人和类型检查器看，类型检查器在运行前发现不匹配的调用。
- `NewType`、`Literal`、`TypedDict`、`dataclass` 的字段标注，都只在静态检查中起作用；`Protocol` 加上 `@runtime_checkable` 也只在运行时检查方法名；`ABC` 在实例化时检查抽象方法是否实现。
- 运行时必须成立的约束，要用运行时的手段保证：在数据进入程序的边界上校验，比如 `dataclass` 的 `__post_init__`。
- 类型用来表达设计：边界清晰、内部简洁；描述真正需要的东西；复杂的类型往往说明数据需要一个名字。

## 练习

宠物医院的预约接口收到这样一份 JSON：

```text
{"owner": 3, "pet": 7, "slot": "周六上午", "species": "猫", "weight_kg": 4.2}
```

1. 你会用哪些工具来表示和校验它？`TypedDict`、`dataclass`，还是两者都用？各自负责什么？
2. 校验应该在哪里进行？如果预约处理函数的参数类型是 `CheckedPet`，它内部还需要检查种类和体重吗？
3. 如果团队里没人运行类型检查器，`NewType` 还有价值吗？

**思路提示**：一种清晰的分工是：`TypedDict` 描述“原始 JSON 应该长什么样”，供解析代码和类型检查器使用；一个解析函数读取 JSON，逐项检查，然后构造 `OwnerId`、`PetId` 和 `CheckedPet`。之后的业务代码只接受这些已经校验过的对象，不需要再次检查，这就是“边界上校验一次”。第 3 问：没有类型检查器时，`NewType` 至少还是一种文档，函数签名 `book(owner: OwnerId, pet: PetId)` 比 `book(owner: int, pet: int)` 更不容易被传反。但它不会阻止任何错误。如果参数传反的代价很高，就要用运行时的手段，比如关键字参数（`book(*, owner, pet)`），强迫调用方写出名字。

完整代码：
- [`examples/ch29_types.py`](../../examples/ch29_types.py)：本章所有示例

测试：[`tests/test_ch29_types.py`](../../tests/test_ch29_types.py)。
