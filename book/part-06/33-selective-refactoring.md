# 第 33 章　需求改变：有选择地重构

> 本章要回答：新格式、新校验规则、新的输出去处同时到来时，哪里真的痛？怎样只在痛的地方重构，而不是借机把 23 种模式都用一遍？

[第 32 章](32-first-version.md)的导入工具只做一件事：读一种 CSV，检查，出报告。它用了一个多月，一切正常。然后，三个变化在同一周到来。

## 三个变化

**一、第二家供应商。** 网店开始卖云南的茶，新供应商“云岭茶业”只提供 JSON 格式的价目表，字段名也不一样：

```text
{"code": "YN-2001", "title": "滇红金芽 200g", "price": 88.0, "qty": 30}
```

**二、新的校验规则。** 网店后台要求 `sku` 必须是“两个大写字母、一个短横线、四位数字”，商品名不能超过 40 个字，否则在手机上显示不全。

**三、写进数据库。** 除了报告，合格的商品还要写进网店使用的 SQLite 数据库；同一个 `sku` 再次导入时，更新价格和库存。

## 先看哪里痛

在动手之前，先设想一下：如果直接在[第 32 章](32-first-version.md)的代码上修改，会发生什么？

**读取。** `read_csv` 把“读 CSV”和“逐行校验”写在同一个循环里。要支持 JSON，要么在这个函数里加一个 `if 是 JSON`，两种格式的读取细节和校验逻辑搅在一起；要么复制一份 `read_json`，校验逻辑也跟着复制一份，以后加一条规则要改两处。这是**真的痛**。

而且 JSON 有两处和 CSV 不同的细节，必须专门处理：

- 没有“行号”。报告里要说“第 3 条”，而不是“第 3 行”。
- 价格是 JSON 数字。`json.loads` 默认把 `88.0` 读成 `float`，[第 32 章](32-first-version.md)刚刚说过金额不能经过 `float`。

**校验。** 现在的五条检查写在循环里的一个 `try` 块中，再加两条还能接受。但它们是**互相独立**的：sku 的格式和价格是否合法毫无关系。互相独立、数量在增加，这是适合拆开的情况（对比[第 31 章](../part-05/31-simple-versus-pattern-code.md)：那里的积分规则有先后依赖，所以不适合随意拆开）。这里**有点痛，而且会越来越痛**。

**输出。** 现在只有“打印一份 JSON 报告”。加上数据库，就是两个去处。以后可能还有第三个（比如直接调用网店的接口）。`main` 函数里加一段写数据库的代码就能解决，**目前不算痛**，但两种去处的接口如果统一，`main` 会更简单，测试也更容易。

还有什么**不痛**？

- 金额的处理、`Product` 的结构、BOM 的处理、退出码，都不需要改。
- 文件只有几百行，一次读进内存没有问题。
- 只有一种“商品”，没有“家族”。

## 重构之前：测试

[第 32 章](32-first-version.md)的测试固定了 CSV 导入的全部行为。重构后的工具读同一个 CSV 文件，必须得到**完全相同**的商品和错误信息。这条要求本身就写成了一个测试：

```text
old = v1.read_csv(...)
new = imp.import_file(...)
assert new.products == old.products
assert 新的错误信息 == 旧的错误信息
```

（测试 `test_refactoring_keeps_the_csv_results`。）有了它，重构过程中任何一步改坏了旧功能，都会立即知道。

## 读取：统一的中间形态

痛点是“每种格式的读取细节”和“校验”搅在了一起。解决办法是在两者之间定义一个**统一的中间形态**：不论来源是什么格式，都先转换成同样的样子，再交给同一套校验。

```python
RawRow = dict[str, str]  # 统一的中间形态：sku、name、price、stock 四个字段，都是字符串
```

每种格式一个读取函数，只负责把来源的样子翻译成 `RawRow`，并附上一个给人看的位置描述：

```python
def read_json_rows(text: str) -> list[tuple[str, RawRow]]:
    try:
        data = json.loads(text, parse_float=Decimal)  # 价格按十进制读入，不经过 float
    except json.JSONDecodeError as e:
        raise FormatError(f"不是合法的 JSON：第 {e.lineno} 行第 {e.colno} 列") from None
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise FormatError("缺少 items 列表")
    rows = []
    for n, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise FormatError(f"第 {n} 条不是一个对象")
        rows.append((f"第 {n} 条", {
            "sku": str(item.get("code", "")),
            "name": str(item.get("title", "")),
            "price": str(item.get("price", "")),
            "stock": str(item.get("qty", "")),
        }))
    return rows
```

文件本身不是合法的 JSON，或者 `items` 里混进了不是对象的东西，都属于“整个文件无法处理”，转换成 `FormatError`，`main` 会给出一句提示并返回退出码 2，而不是打印一大段异常信息（测试 `test_malformed_json_is_a_format_error`）。`parse_float=Decimal` 让 `json.loads` 把小数直接解析成 `Decimal`，于是 `0.29` 不会变成 28 分（测试 `test_json_prices_never_pass_through_float`）。字段名的对应（`code` → `sku`、`title` → `name`），以及“第几条”的说法，都只在这个函数里。

这正是[第 10 章](../part-03/10-adapter.md)“Python 角度”里说的：核心逻辑只认一种数据，外部的各种格式在**边界**上转换。这里的读取函数就是适配器，只不过它们是函数，适配的是数据。

根据文件扩展名选择读取函数，用一个字典：

```python
READERS: dict[str, Callable[[str], list[tuple[str, RawRow]]]] = {
    ".csv": read_csv_rows,
    ".json": read_json_rows,
}
```

这是[第 05 章](../part-02/05-factory-method.md)的简单工厂，用[第 28 章](../part-05/28-functions-as-design-tools.md)的字典分派来写。没有工厂类，也没有工厂方法，因为“选哪个读取函数”只取决于扩展名，没有任何流程需要子类来定制。

## 校验：一条规则一个函数

每条规则是一个函数，接收一行，返回错误信息或 `None`：

```python
def sku_format(row: RawRow) -> str | None:
    sku = row["sku"].strip()
    if sku and not re.fullmatch(r"[A-Z]{2}-\d{4}", sku):
        return f"sku 格式应为两个大写字母加四位数字：{sku}"
    return None
```

所有规则放在一个列表里：

```python
RULES: list[Callable[[RawRow], str | None]] = [not_empty, sku_format, name_length, valid_price, valid_stock]
```

因为规则互相独立，现在可以把一行的**所有**问题一次报告出来，而不是只报告第一个：

```python
        messages = [m for rule in rules if (m := rule(row)) is not None]
        sku = row["sku"].strip()
        if not messages and sku in seen:
            messages.append(f"sku 重复：{sku}")  # 跨行的检查，不是单行规则
```

一行 sku 格式错误、价格又是负数，报告里会同时列出两个问题（测试 `test_independent_rules_report_together`），供应商一次就能改完。

注意“sku 重复”**没有**写成规则函数。它需要记住前面出现过哪些 sku，是一个跨行的检查，和“只看一行”的规则性质不同。硬把它塞进 `RULES`，就得让规则函数带上状态，或者给所有规则加一个参数。把它留在循环里，保持两类检查的区别清楚可见。

加一条新规则，就是写一个函数、在列表里加一项（测试 `test_a_new_rule_is_one_more_function`）。这是[第 17 章](../part-04/17-strategy.md)的策略，用函数来写。

## 输出：同一个 `write`

报告和数据库，都是“拿到导入结果，把它送到某个地方”。给它们一个共同的接口：

```python
class Sink(Protocol):
    def write(self, result: Result) -> None: ...
```

数据库的写入用 SQLite 的 `ON CONFLICT ... DO UPDATE`，同一个 sku 再次导入时更新价格和库存（测试 `test_sqlite_upsert`）：

```python
        with closing(sqlite3.connect(self.path)) as conn, conn:  # closing 负责关闭，conn 负责提交或回滚
            conn.execute(
```

这一行有一个容易踩的坑：`with sqlite3.connect(...) as conn:` 只负责事务（成功提交、出错回滚），**不会关闭连接**。所以外面再套一层 `contextlib.closing`，保证连接被关闭（参见[第 30 章](../part-05/30-decorators-context-managers-generators.md)的上下文管理器）。

`main` 根据命令行参数组装需要的去处，然后依次写入：

```python
    for sink in sinks:
        sink.write(result)
```

## 没有用的模式

这次重构用到了适配器的思想（读取函数）、简单工厂（`READERS` 字典）、策略（规则函数列表），全部是函数和字典，只有输出用了一个 `Protocol` 和两个小类。同样值得说清楚的，是**没有用**哪些模式，以及为什么：

- **抽象工厂**：读取、校验、输出之间没有“必须成套切换”的家族关系。CSV 文件可以写进数据库，JSON 文件也可以只出报告。
- **模板方法**：可以把“读取 → 校验 → 输出”写成父类的模板方法，让 `CsvImporter`、`JsonImporter` 子类覆盖“读取”这一步。但各格式之间只有读取不同，一个字典就够了。[第 34 章](34-retrospective.md)会把这种写法实际做出来比较。
- **观察者**：输出的去处确实是“结果出来后通知多个对象”，但它们由 `main` 在启动时一次性确定，不会在运行中订阅、退订。一个列表加一个循环就够了。
- **建造者、责任链、访问者**：没有对应的困难。

[第 04 章](../part-01/04-choosing-a-pattern.md)的提醒在这里依然适用：**模式是对困难的回应，不是需要凑齐的清单。**

## 运行结果

```text
python -m examples.ch33_importer examples/data/supplier_b.json --db 商品.db
```

```text
{
  "imported": 2,
  "rejected": 3,
  "stock_value_yuan": "4521.60",
  "problems": [
    "第 3 条：sku 格式应为两个大写字母加四位数字：yn2003",
    "第 4 条：商品名超过 40 个字：50",
    "第 5 条：价格最多两位小数：59.999"
  ]
}
```

两件合格的商品同时写进了 `商品.db`。对[第 32 章](32-first-version.md)的 CSV 文件运行，报告和以前完全一样。

## 小结

- 需求变化时，先分别判断每个部分痛不痛：读取格式和校验搅在一起，痛；校验规则互相独立而且在增加，会痛；输出去处增加，暂时不痛但值得统一。金额处理、数据结构等没有变化的部分，不动。
- 重构前，先用测试固定旧的行为；重构后，旧格式的结果必须完全一样。
- 用一个统一的中间形态隔开“格式”和“校验”；用字典选择读取函数；用函数列表组织互相独立的规则；跨行的检查和单行规则分开。
- 说清楚没有用哪些模式、为什么没用，和说清楚用了什么同样重要。

## 练习

第三家供应商只能提供 Excel 文件（`.xlsx`）。标准库无法直接读取 `.xlsx`。

1. 有哪些选择？（提示：让供应商导出 CSV；引入第三方库；写一个小的转换脚本。）各有什么代价？
2. 如果决定引入第三方库，它应该出现在代码的哪里？怎样保证没有安装这个库的同事，仍然可以导入 CSV 和 JSON？
3. 这个新需求会让哪些部分感到“痛”？会不会改变本章的设计？

**思路提示**：最简单、最稳妥的往往是第一个选择：和供应商商量导出 CSV，代码一行都不用改。如果必须支持 `.xlsx`，第三方库只应该出现在一个新的读取函数里，在 `READERS` 里登记 `.xlsx`；导入那个库的语句放在读取函数内部（或者用 `try/except ImportError` 登记），这样没有安装它的环境依然可以使用其他格式。本章的设计正好能吸收这个变化：新增一种格式，只是新增一个读取函数，校验和输出都不用改。这说明重构的方向是对的：变化落在了预期的位置上。

完整代码：
- [`examples/ch33_importer.py`](../../examples/ch33_importer.py)：重构后的导入工具
- [`examples/data/supplier_b.json`](../../examples/data/supplier_b.json)：第二家供应商的价目表

测试：[`tests/test_ch33_importer.py`](../../tests/test_ch33_importer.py)。
