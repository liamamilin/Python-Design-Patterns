# 第 07 章　建造者 Builder

> 本章要回答：一个结果需要分好几步拼出来时，“怎么拼”应该放在哪里？在 Python 里，命名参数和 `dataclass` 什么时候已经够用，什么时候才值得用建造者？

说起建造者，很多人想到的是一长串链式调用：`.where(...).order_by(...).limit(...)`。这种写法确实常见，但它只是建造者的一种外观。GoF 建造者真正要解决的问题，是**同一套构建步骤，造出不同的结果**。这一章从一个租房搜索页开始，看这个问题是怎样出现的。

## 眼前的任务

一个租房网站把房源存在 SQLite 里（标准库自带的 `sqlite3`），每条房源有标题、所在区、月租、几室、面积和是否近地铁。搜索页是一个表单，用户可以选区、填最高月租、选最少几室，提交后浏览器把表单变成一个字典交给程序，值都是字符串，没填的项是空字符串或者干脆没有：

```text
{"district": "朝阳", "max_rent": "6000", "min_rooms": "2"}
```

程序要把它变成一条 SQL 查询。

## 不用模式的写法

逐项检查表单，填了的就加一个条件。值通过 `?` 占位符交给数据库，不拼进 SQL 字符串里，这是防止 SQL 注入的基本做法：

```python
def search(conn: sqlite3.Connection, form: dict[str, str]) -> list[tuple[str, int]]:
    conds: list[str] = []
    params: list[object] = []
    if form.get("district"):
        conds.append("district = ?")
        params.append(form["district"])
    if form.get("max_rent"):
        conds.append("rent <= ?")
        params.append(int(form["max_rent"]))
    if form.get("min_rooms"):
        conds.append("rooms >= ?")
        params.append(int(form["min_rooms"]))
    if form.get("subway"):
        conds.append("near_subway = 1")
    sql = "SELECT title, rent FROM listings"
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY rent"
    return conn.execute(sql, params).fetchall()
```

（“近地铁”这一项是后来加的，下面会讲到。）

**这是好代码。** 一个函数，从上往下读，每个条件一目了然。很多人看到“一步步拼出 SQL”就想到建造者，但在这里，一个函数已经是最好的“建造者”。

## 第一次变化：同样的条件，要用两种方式表达

用户反馈：搜索结果页上看不出自己选了哪些条件，改了几次之后就不知道当前结果是怎么来的。产品经理要求在结果上方加一行“当前筛选条件”：

```text
朝阳区，月租不超过 6000 元，至少 2 室
```

于是有了第二个函数，同样逐项读表单：

```python
def describe(form: dict[str, str]) -> str:
    parts = []
    if form.get("district"):
        parts.append(f"{form['district']}区")
    if form.get("max_rent"):
        parts.append(f"月租不超过 {form['max_rent']} 元")
    if form.get("min_rooms"):
        parts.append(f"至少 {form['min_rooms']} 室")
    return "，".join(parts) or "全部房源"
```

又过了一个月，另一位同事加了“近地铁”复选框。他在 `search` 里加了 `near_subway = 1` 的条件，测了搜索结果，没问题，上线了。他不知道 `describe` 也要改。

于是用户勾选“朝阳”和“近地铁”，看到的是：

```text
筛选条件： 朝阳区
('朝阳 两居 近地铁', 5800)
('朝阳 三居', 8800)
```

说明里只有“朝阳区”，可朝阳那套月租 4200 的一居室不见了。用户以为数据丢了。测试 `test_description_forgets_the_subway_filter` 复现了这个错误。

## 变化带来的困难

问题不在某一行，而在结构：

1. **“读表单、决定有哪些条件”这件事写了两遍。** `search` 和 `describe` 各自检查一遍表单，两份逻辑没有任何东西把它们连在一起。
2. **两种结果的“零件”不一样。** SQL 要的是条件字符串和参数列表，说明要的是中文短语。所以不能简单地让一个函数调用另一个。

很快还有第三个需求：用户想按租金从高到低、或者按面积排序。排序用的是列名，而**列名不能用 `?` 占位符传入**，只能出现在 SQL 字符串里。如果有人顺手写出 `f"ORDER BY {form['sort']}"`，用户就可以在表单里塞进任意 SQL。排序也要同时出现在 SQL 和说明里，又多了一处可能不同步的地方。

我们希望：**表单只读一遍，读出的每一步，同时交给“造 SQL 的”和“造说明的”。**

## 建造者：把“按什么步骤造”和“造成什么样”分开

GoF 对建造者的描述是：**将一个复杂对象的构建与它的表示分离，使得同样的构建过程可以创建不同的表示。**

落到本例：“构建过程”是读表单、按顺序决定有哪些条件；“表示”是 SQL 或者中文说明。

第一步，列出所有构建步骤，作为建造者的接口：

```python
class SearchBuilder(ABC):
    @abstractmethod
    def district(self, name: str) -> None: ...

    @abstractmethod
    def max_rent(self, yuan: int) -> None: ...

    @abstractmethod
    def min_rooms(self, n: int) -> None: ...

    @abstractmethod
    def near_subway(self) -> None: ...

    @abstractmethod
    def sort(self, key: str) -> None: ...
```

第二步，每种表示一个具体建造者。造 SQL 的建造者收集条件和参数：

```python
    def near_subway(self) -> None:
        self.conds.append("near_subway = 1")

    def sort(self, key: str) -> None:
        self.order = SORTS[key][0]  # 列名只从白名单里取，从不拼接用户输入

    def result(self) -> tuple[str, list[object]]:
        sql = "SELECT title, rent FROM listings"
        if self.conds:
            sql += " WHERE " + " AND ".join(self.conds)
        return sql + f" ORDER BY {self.order}", self.params
```

造说明的建造者收集中文短语：

```python
    def near_subway(self) -> None:
        self.parts.append("近地铁")

    def sort(self, key: str) -> None:
        self.order = SORTS[key][1]

    def result(self) -> str:
        return ("，".join(self.parts) or "全部房源") + "；" + self.order
```

排序选项集中在一张表里，每个选项同时给出 SQL 片段和中文说明。`SqlBuilder.sort` 只从表里取列名，用户输入永远不会进入 SQL 字符串：

```python
SORTS = {
    "price": ("rent", "按租金从低到高"),
    "price_desc": ("rent DESC", "按租金从高到低"),
    "area": ("area DESC", "按面积从大到小"),
}
```

第三步，把“读表单”写成**指挥者**（Director）。它只决定调用哪些步骤，不关心最后造出的是什么：

```python
def apply_form(form: dict[str, str], builder: SearchBuilder) -> None:
    """指挥者：只负责读表单、决定调用哪些步骤，不关心最后造出什么。"""
    if form.get("district"):
        builder.district(form["district"])
    if form.get("max_rent"):
        builder.max_rent(int(form["max_rent"]))
    if form.get("min_rooms"):
        builder.min_rooms(int(form["min_rooms"]))
    if form.get("subway"):
        builder.near_subway()
    sort = form.get("sort") or "price"
    if sort not in SORTS:
        raise ValueError(f"未知排序: {sort}")
    builder.sort(sort)
```

最后，同一个表单交给两个建造者：

```python
def search(conn: sqlite3.Connection, form: dict[str, str]) -> tuple[str, list[tuple[str, int]]]:
    sql_builder, text_builder = SqlBuilder(), DescriptionBuilder()
    apply_form(form, sql_builder)
    apply_form(form, text_builder)
    sql, params = sql_builder.result()
    return text_builder.result(), conn.execute(sql, params).fetchall()
```

勾选“朝阳”和“近地铁”，说明变成了 `朝阳区，近地铁；按租金从低到高`，和结果一致。

**这个结构为什么能防止上一节的错误？** 下次有人加一个“可养宠物”的筛选项，他必须在 `SearchBuilder` 上加一个 `allow_pets` 抽象方法。只要加了，`SqlBuilder` 和 `DescriptionBuilder` 如果不实现它，连对象都创建不出来（测试 `test_builder_must_implement_every_step` 验证了这一点）。“只改了 SQL、忘了改说明”从一个上线后才被用户发现的错误，变成了一个运行测试就会暴露的错误。

如果有人在表单里提交 `sort=rent; DROP TABLE listings`，`apply_form` 会直接抛出 `ValueError`，数据表安然无恙（测试 `test_sort_is_whitelisted`）。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 建造者（Builder） | `SearchBuilder` | 声明所有构建步骤 |
| 具体建造者（ConcreteBuilder） | `SqlBuilder`、`DescriptionBuilder` | 实现每一步，并提供取得结果的方法 |
| 指挥者（Director） | `apply_form` | 决定按什么顺序调用哪些步骤 |
| 产品（Product） | `(sql, params)`、说明字符串 | 构建出的结果 |

注意 `result()` 没有放在 `SearchBuilder` 接口上。这不是遗漏：两个建造者的产品类型完全不同，一个是元组，一个是字符串，没有共同的接口可言。GoF 原书的结构图也是这样画的：取结果的方法只出现在具体建造者上，因为调用方本来就知道自己用的是哪一个建造者。

### 链式调用是什么

很多库的“建造者”长这样：`Query().where("district", "朝阳").order_by("rent").build()`，每个方法返回 `self`，于是可以连着写。这是一种**接口风格**（常被称为 fluent interface），可以和建造者配合使用，但它不是建造者的本质。本章的建造者方法都返回 `None`，并不影响模式成立；反过来，一个只是把构造参数拆成一串链式调用的类，如果只有一种产品，也谈不上“同一构建过程，不同表示”。

## 代价与边界

- **类和间接层多了。** 一个抽象建造者、两个具体建造者、一个指挥者，替代了原来的两个函数。读者要在三四个地方之间跳来跳去，才能拼出“近地铁”这个筛选项的全貌。
- **建造者是有状态的，用完不能接着用。** `SqlBuilder` 把条件累积在列表里。如果同一个对象被 `apply_form` 调用两次，就会得到 `district = ? AND district = ?` 这样重复的条件（测试 `test_builder_is_single_use`）。每次构建应该创建新的建造者。
- **步骤之间的顺序约束是隐含的。** 本例的步骤顺序不影响结果，但在别的场景中，比如“先设页眉再加正文”，顺序很重要，而 `SearchBuilder` 接口本身表达不了这种约束，只能靠指挥者遵守。
- **加一个步骤，要改所有建造者。** 这正是它能防止遗漏的原因，也是它的成本。

**什么时候不该用**：只有一种表示（只要 SQL，不要说明），或者所有参数在一次调用时就全部已知。这时一个带命名参数的函数最清楚。不要为了写出链式调用而引入建造者。

## Python 角度：先把表单变成一个值

本例真正的问题是“表单读了两遍”。在 Python 里，还有一种更直接的解法：**只解析一次，把结果存成一个不可变的数据类**，然后让 SQL 和说明各由一个普通函数从这个值生成。

```python
@dataclass(frozen=True, kw_only=True)
class SearchFilter:
    district: str | None = None
    max_rent: int | None = None
    min_rooms: int | None = None
    subway: bool = False
    sort: str = "price"

    def __post_init__(self) -> None:
        if self.sort not in SORTS:
            raise ValueError(f"未知排序: {self.sort}")
```

`kw_only=True` 让所有字段只能用名字传入，`SearchFilter(district="海淀", max_rent=6000)` 读起来和建造者的链式调用一样清楚，而不会因为位置写错把月租当成室数。`__post_init__` 在对象创建时就检查排序选项，非法的值连对象都造不出来。

```python
def search(conn: sqlite3.Connection, form: dict[str, str]) -> tuple[str, list[tuple[str, int]]]:
    f = parse_form(form)
    sql, params = to_sql(f)
    return describe(f), conn.execute(sql, params).fetchall()
```

测试 `test_same_results_as_builder` 确认，对几种不同的表单，这个版本和建造者版本的结果完全一样。

两种写法如何选？

- **数据类的写法**更短、更容易读，也更容易测试：`SearchFilter` 是一个普通的值，可以打印、比较、保存。它的弱点是：给 `SearchFilter` 加了 `allow_pets` 字段后，没有任何机制强迫 `to_sql` 和 `describe` 同时更新，只能靠测试或代码审查。
- **建造者**在以下情况更合适：构建步骤可以**重复**或有**顺序**意义（比如用户可以添加任意多个“或者”条件组，组里再有条件）；结果需要**边读边造**，等不到所有信息都齐了再生成，例如一边解析一份很长的文档一边写输出；或者表示有很多种，每加一个步骤都必须让所有表示跟上。

对本章的租房搜索来说，条件就是几个固定的可选项，**数据类加两个函数是更好的选择**。建造者的价值，要等到筛选条件可以任意组合、嵌套时才会显现出来。

## 小结

- 一步步拼出结果，本身不需要建造者，一个函数就是最简单的“建造过程”。
- GoF 建造者的核心是：同一个构建过程（指挥者），交给不同的建造者，得到不同的表示。当同一套步骤需要产出两种以上结果，且必须保持一致时，它才有用武之地。
- 链式调用只是一种接口风格，不等于建造者。
- 在 Python 里，如果所有参数一次就能确定，先把输入解析成一个带校验的 `dataclass`，再由不同的函数生成不同的结果，通常比建造者更简单。

## 练习

产品经理提出：用户想保存常用的搜索，下次一键恢复。保存的内容要能写进数据库的一个文本字段里，例如：

```text
district=朝阳&subway=1&sort=price_desc
```

1. 用建造者的写法，“保存”需要新增什么？
2. 用 `SearchFilter` 的写法，“保存”需要新增什么？“恢复”呢？
3. 两种写法里，哪一种更容易保证“保存后再恢复，得到的筛选条件和原来完全相同”？怎么测试？

**思路提示**：建造者的写法可以新增一个 `QueryStringBuilder`，指挥者 `apply_form` 不用改，这正是建造者擅长的“多一种表示”。但“恢复”是反方向的：从文本变回条件，建造者帮不上忙，还得另写解析。`SearchFilter` 的写法里，保存是一个 `to_query_string(f)` 函数，恢复就是 `parse_form`：用标准库的 `urllib.parse.parse_qsl` 把查询字符串拆成键值对，再转成字典，正好是表单那样的输入。数据类是一个值，可以直接写出“往返测试”：`parse_form(...)` 回来的对象等于原对象。这个练习说明，当“结果”需要被保存、比较、还原时，一个明确的值比一串构建步骤更方便。

完整代码：
- [`examples/ch07_search_v1.py`](../../examples/ch07_search_v1.py)：两个函数各读一遍表单（含错误）
- [`examples/ch07_builder.py`](../../examples/ch07_builder.py)：GoF 建造者，一个指挥者，两个建造者
- [`examples/ch07_pythonic.py`](../../examples/ch07_pythonic.py)：解析成 `dataclass` 再生成

测试：[`tests/test_ch07_builder.py`](../../tests/test_ch07_builder.py)。
