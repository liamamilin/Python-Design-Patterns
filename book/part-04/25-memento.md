# 第 25 章　备忘录 Memento

> 本章要回答：怎样把一个对象此刻的状态保存下来，以后原样恢复，而又不让外面的代码随意查看和修改它的内部？保存的“快照”为什么常常并不是快照？

[第 01 章](../part-01/01-data-and-processing.md)说过，有状态的对象，结果取决于“之前发生过什么”。[第 19 章](19-command.md)的命令通过记录每一步操作来撤销。这一章换一种思路：不记录过程，直接把**某一时刻的整个状态**存下来，需要时整体恢复。

## 眼前的任务

一个农场经营小游戏：玩家有金币，可以买种子种菜，过几天收获卖钱。

```python
    def plant(self, crop: str, n: int) -> None:
        cost = n * self.SEED_PRICE
        if cost > self.coins:
            raise ValueError("金币不够")
        self.coins -= cost
        self.crops[crop] = self.crops.get(crop, 0) + n
```

游戏要有**存档**功能：玩家可以在任何时候存档，以后读档回到那时的状态。

## 不用模式的写法

把三个字段打包返回，读档时再放回去：

```python
    def save(self) -> tuple[int, int, dict[str, int]]:
        return self.day, self.coins, self.crops  # 字典是同一个对象

    def load(self, saved: tuple[int, int, dict[str, int]]) -> None:
        self.day, self.coins, self.crops = saved
```

看起来很合理，也很短。

## 问题：存档会自己变

玩家种了 3 棵萝卜，存档；又种了 2 棵，过了一天，觉得不划算，读档。读档之后：

```text
第 1 天，金币 70，萝卜×5
```

天数和金币都回去了，萝卜却是 5 棵（测试 `test_saved_game_changes_after_saving`）。

原因在注释里已经写了：`save` 返回的元组里，`self.crops` 是农场正在使用的**同一个字典**。存档之后再种萝卜，改的就是这个字典，存档里的“萝卜×3”也就跟着变成了“萝卜×5”。天数和金币是整数，整数不可变，`self.day += 1` 会让 `self.day` 指向一个新的整数，存档里的旧值不受影响。

这和[第 08 章](../part-02/08-prototype.md)的浅拷贝是同一个问题：**保存的不是状态的副本，而是对状态的引用。**

## 还有一个问题：谁能动存档

即使修好了引用的问题，这个写法还有另一个隐患：存档就是一个普通的元组，里面的字典谁都可以改。存档管理的代码、显示存档列表的代码，都可以写出 `saved[2]["萝卜"] = 999`。而 `load` 会照单全收。

我们希望：

1. 存档是保存那一刻状态的**真正副本**，之后农场怎么变都不影响它；
2. 存档对外是一个**不透明**的东西：其他代码可以保管它、传递它，但不应该查看或修改它的内容；只有农场自己知道怎样从中恢复。

## 备忘录：只有原主人能读的快照

GoF 对备忘录的描述是：**在不破坏封装性的前提下，捕获一个对象的内部状态，并在该对象之外保存这个状态。这样以后就可将该对象恢复到原先保存的状态。**

快照写成一个冻结的数据类。字段名以下划线开头，表示“这是内部的，只有 `Farm` 应该读它”：

```python
@dataclass(frozen=True)
class FarmMemento:
    """只有 Farm 知道怎样读它。其他代码只负责保管。"""

    _day: int
    _coins: int
    _crops: tuple[tuple[str, int], ...]
```

农场负责创建快照和从快照恢复：

```python
    def save(self) -> FarmMemento:
        return FarmMemento(self._day, self._coins, tuple(sorted(self._crops.items())))

    def restore(self, m: FarmMemento) -> None:
        self._day, self._coins, self._crops = m._day, m._coins, dict(m._crops)
```

这里有两处复制，缺一不可：

- **存档时**，把字典转换成元组。元组和其中的字符串、整数都不可变，农场之后怎样修改自己的字典，都影响不到快照。
- **读档时**，用 `dict(m._crops)` 新建一个字典。如果直接把快照里的东西拿来用，而它恰好是可变的，农场之后的修改就会反过来改坏快照。用了元组，这一点也一并保证了：同一个快照可以反复恢复多次，每次都一样（测试 `test_one_memento_can_be_restored_many_times`）。

快照本身是冻结的，试图修改它会立即报错（测试 `test_memento_is_immutable`）。

保管快照的是另一个对象，它只按名字存取，从不查看内容：

```python
class SaveSlots:
    """负责人：按名字保管快照，不读取、不修改其中的内容。"""

    def __init__(self) -> None:
        self._slots: dict[str, FarmMemento] = {}

    def save(self, name: str, farm: Farm) -> None:
        self._slots[name] = farm.save()

    def load(self, name: str, farm: Farm) -> None:
        farm.restore(self._slots[name])
```

现在，存档、继续玩、读档，农场回到的正是存档时的样子：第 1 天，金币 70，萝卜×3（测试 `test_restore_brings_back_the_exact_state`）。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 原发器（Originator） | `Farm` | 创建快照，从快照恢复自己 |
| 备忘录（Memento） | `FarmMemento` | 保存原发器的内部状态；对其他对象不透明 |
| 负责人（Caretaker） | `SaveSlots` | 保管快照，但从不查看或修改其内容 |

### Python 里的“不透明”

GoF 原书用 C++ 的 `friend` 机制，让备忘录对原发器提供“宽接口”（可以读写全部状态），对其他对象只提供“窄接口”（什么都看不到）。Python 没有这样的访问控制。`FarmMemento._coins` 前面的下划线只是一个**约定**：它告诉其他程序员“这不是给你用的”，但并不能阻止任何人读取它。

在 Python 里，备忘录的“封装”主要靠两点：**不可变**（冻结的数据类，没人能改），加上**约定**（下划线前缀，没人应该读）。对一个游戏存档来说，这已经足够。

### 和命令的撤销比较

[第 19 章](19-command.md)用命令实现撤销：每条命令知道怎样抵消自己。备忘录则是在某个时刻把整个状态存下来。两种方式各有长处：

| | 命令的撤销 | 备忘录 |
|---|---|---|
| 保存什么 | 每一步的操作，以及撤销它所需的少量信息 | 某一时刻的完整状态 |
| 占用空间 | 和操作的步数成正比，每步通常很小 | 和状态的大小成正比，每个快照都是完整的一份 |
| 实现难度 | 每种操作都要写正确的撤销 | 只需要一对 `save`/`restore` |
| 适合 | 逐步撤销、重做；操作日志 | 存档点、“回到某个时刻”、出错时整体回滚 |

两者也可以结合：命令执行前，先用备忘录记下受影响部分的状态，撤销时直接恢复它，就不必为每种命令写反向操作了。

## 代价与边界

- **快照可能很大。** 每个快照都是完整状态的一份副本。农场只有几个字段，无所谓；如果状态里有一张很大的地图，频繁存档就会占用大量内存。这时要考虑只保存变化的部分，或者限制快照的数量。
- **复制必须彻底。** 本章开头的错误说明，只要状态里有任何可变的部分被共享，快照就不再可靠。每给原发器加一个可变字段，都要检查 `save` 和 `restore` 是否正确地复制了它。
- **状态的结构变了，旧快照怎么办。** 游戏更新后，农场多了一个“天气”字段，旧存档里没有它。读旧存档时要给出合理的默认值，或者明确拒绝。下一节会看到，存档写到文件里时，这个问题更加突出。
- **不是所有状态都能或都应该保存。** 打开的网络连接、正在播放的音乐，这些是外部资源，不属于“可以存下来再恢复”的状态。

**什么时候不该用**：状态本身就是一个不可变的值。如果 `Farm` 的每次操作都返回一个新的 `Farm` 对象，而不是修改自己，那么“存档”就是保留一个旧对象的引用，不需要任何复制。[第 08 章](../part-02/08-prototype.md)的不可变数据，在这里同样适用。

## Python 角度：存到磁盘上的备忘录

游戏存档最终要写进文件，下次打开游戏时还在。这时备忘录要被**序列化**。

Python 标准库的 `pickle` 可以把几乎任何对象存成字节，写起来最省事。但**读取不可信的 pickle 数据可能执行任意代码**，Python 官方文档对此有明确的警告。存档文件放在玩家的电脑上，可以被修改，也可以从网上下载别人的“存档”。所以存档应该用只表示数据的格式，比如 JSON，并且在读取时检查内容：

```python
def from_json(text: str) -> FarmMemento:
    data = json.loads(text)
    if data.get("version") != 1:
        raise ValueError("不认识的存档版本")
    day, coins, crops = data["day"], data["coins"], data["crops"]
    if not (isinstance(day, int) and day >= 1 and isinstance(coins, int) and coins >= 0):
        raise ValueError("存档内容不合法")
    if not all(isinstance(k, str) and isinstance(v, int) and v > 0 for k, v in crops.items()):
        raise ValueError("存档里的作物数据不合法")
    return FarmMemento(day, coins, tuple(sorted(crops.items())))
```

几个要点：

- **版本号。** 存档里记下格式版本，以后格式变了，读档的代码可以识别旧版本，选择转换或拒绝。
- **检查。** 文件里的内容不可信。负数的金币、字符串类型的天数、数量为 0 的作物，都应该被拒绝，而不是悄悄地恢复成一个不合理的农场（测试 `test_rejects_tampered_or_unknown_saves`）。
- **往返测试。** 存下来再读回去，应该得到相等的快照（测试 `test_round_trip`）。冻结的数据类自动支持相等比较，这个测试写起来很简单。

至于“防止玩家修改存档作弊”，检查内容只能拦住明显不合理的值，拦不住“把金币从 70 改成 7000”。如果这对游戏很重要，需要对存档内容做签名，那已经超出了本章的范围。

## 小结

- 备忘录把对象某一时刻的内部状态存成一个快照，以后可以原样恢复；快照由别的对象保管，但只有原对象知道怎样读取它。
- 快照必须是真正的副本：存的时候复制，恢复的时候也复制，或者干脆用不可变的数据保存。共享任何可变部分，快照都会悄悄改变。
- Python 没有严格的访问控制。备忘录的封装主要依靠不可变（冻结的数据类）和约定（下划线前缀）。
- 存档写入磁盘时，使用 JSON 等只表示数据的格式，带上版本号，并检查读入的内容；不要用 `pickle` 读取不可信的文件。

## 练习

游戏更新了：农场新增了“仓库”，保存已收获但还没卖掉的作物（一个字典，作物名到数量）。

1. `FarmMemento`、`save`、`restore` 各要怎样修改？如果忘了修改 `save`，会发生什么？
2. 玩家用旧版本的存档（没有仓库字段）读档，你希望发生什么？`from_json` 要怎样修改？
3. 能不能写一个测试，在以后有人给 `Farm` 加新字段却忘了更新快照时，自动失败？

**思路提示**：快照要加一个 `_storage` 字段（同样转成元组），`save` 和 `restore` 都要处理它。如果忘了改 `save`，读档后仓库会保留读档前的内容，也就是“存档不完整”，而且不会报错。对旧存档，可以把格式版本升到 2，读到版本 1 时把仓库当作空的，这是一种合理的迁移；也可以直接拒绝，但对玩家不太友好。第 3 问的一种思路是：在测试里比较 `vars(farm)` 的键和快照的字段，确保农场的每个内部字段都在快照里有对应的一项。这类“结构一致性”的测试，是防止状态和快照悄悄走样的有效办法。

完整代码：
- [`examples/ch25_farm_v1.py`](../../examples/ch25_farm_v1.py)：存档共享了内部字典（含错误）
- [`examples/ch25_memento.py`](../../examples/ch25_memento.py)：不可变快照与存档栏
- [`examples/ch25_pythonic.py`](../../examples/ch25_pythonic.py)：JSON 存档、版本号与读档检查

测试：[`tests/test_ch25_memento.py`](../../tests/test_ch25_memento.py)。
