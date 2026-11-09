# 第 32 章　第一次实现：不使用模式

> 本章要回答：面对一个真实的小工具，怎样先让最简单的版本正确地运行，并用测试把它固定下来？哪些地方现在就值得认真对待，哪些可以等一等？

最后一部分用一个贯穿三章的案例，把前面的选择放回真实项目里。这一章故意**不使用任何模式**：先把一种格式的导入做对，写好测试。下一章再根据真实出现的变化，有选择地重构。

## 眼前的任务

一家卖茶叶的小网店，每周从供应商那里收到一份价目表，是 Excel 导出的 CSV 文件：

```text
sku,name,price,stock
TE-1001,西湖龙井 250g,128.00,40
TE-1002,碧螺春 250g,96.5,25
TE-1003,白毫银针 100g,-3,10
```

店主想要一个命令行小工具：读入这份文件，检查每一行是否合理，把合格的商品整理出来，并给出一份报告：导入了几个、拒绝了几个、合格商品的库存总值是多少、每个被拒绝的行错在哪里。

“合理”的标准是：

- `sku` 和 `name` 不能为空；同一个 `sku` 不能出现两次；
- 价格必须是大于 0 的数字，最多两位小数；
- 库存必须是非负整数。

## 先定数据的样子

[第 01 章](../part-01/01-data-and-processing.md)的建议：先想清楚数据长什么样，再写处理。导入的结果有三种数据：

```python
@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price_cents: int
    stock: int


@dataclass(frozen=True)
class Problem:
    line: int
    message: str
```

价格存成**分**，用整数，这一点和[第 01 章](../part-01/01-data-and-processing.md)的小票一样。`Problem` 记下行号，因为店主要回到 Excel 里去改那一行。

## 现在就值得认真的地方

“不用模式”不等于“随便写”。有几处细节，现在不处理好，以后会以更隐蔽的方式出错。

### 价格：不要用浮点数

```python
def parse_price(text: str) -> int:
    """把“12.5”这样的价格转换成分。用 Decimal，避免二进制浮点数的误差。"""
    try:
        value = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError(f"价格不是数字：{text!r}") from None
    if not value.is_finite():
        raise ValueError(f"价格不是有限的数字：{text!r}")
    if value <= 0:
        raise ValueError(f"价格必须大于 0：{text}")
    if value != value.quantize(Decimal("0.01")):
        raise ValueError(f"价格最多两位小数：{text}")
    return int(value * 100)
```

如果写成 `int(float(text) * 100)`，价格 `0.29` 会变成 28 分，因为 `0.29 * 100` 在二进制浮点数里是 `28.999999999999996`，`int` 会直接截断（测试 `test_no_float_rounding_error`）。标准库的 `decimal.Decimal` 按十进制精确表示，适合金额。

几个边界情况也在这里一并处理：`Decimal` 能解析 `"NaN"` 和 `"Infinity"`，必须拒绝；`210.125` 这种三位小数，与其悄悄四舍五入，不如让店主确认。所有问题都转换成 `ValueError` 和一句店主看得懂的中文。

### Excel 的 BOM

Excel 在保存 UTF-8 格式的 CSV 时，常常会在文件开头写入三个看不见的字节（`EF BB BF`），叫 BOM。如果用普通的 `utf-8` 读取，第一个列名会变成 `"﻿sku"` 而不是 `"sku"`，程序就会报告“缺少列：sku”，而用户在 Excel 里明明看到了这一列（测试 `test_bom_without_utf8_sig_breaks_the_header`）。

解决办法是读取时使用 `utf-8-sig` 编码，它会自动去掉开头的 BOM：

```python
    text = Path(argv[0]).read_text(encoding="utf-8-sig")  # utf-8-sig：去掉 Excel 写入的 BOM
```

### 逐行报告，而不是遇错即停

一份价目表有几百行，第 4 行错了就停下来，店主改好之后再运行，又在第 5 行停下来……所以每一行的错误都被收集起来，继续处理下一行，最后一起报告：

```python
    seen: set[str] = set()
    for line, row in enumerate(reader, start=2):  # 第 1 行是表头
        try:
            sku, name = row["sku"].strip(), row["name"].strip()
            if not sku or not name:
                raise ValueError("sku 和 name 不能为空")
            if sku in seen:
                raise ValueError(f"sku 重复：{sku}")
            product = Product(sku, name, parse_price(row["price"]), parse_stock(row["stock"]))
        except ValueError as e:
            result.problems.append(Problem(line, str(e)))
            continue
        seen.add(sku)
        result.products.append(product)
```

行号从 2 开始，因为第 1 行是表头，这样报告里的行号和 Excel 里看到的一致。缺少必要的列是另一种错误：整个文件都无法处理，只报告一次，行号是 1（测试 `test_missing_column`）。

### 退出码

命令行工具有一个容易被忽视的“输出”：退出码。有被拒绝的行时返回 1，全部成功返回 0，用法错误返回 2。这样店主以后可以把它放进自动化脚本里，脚本能知道这次导入是否完全成功（测试 `test_exit_code_and_output`）。

## 运行结果

对示例文件运行：

```text
python -m examples.ch32_import_v1 examples/data/supplier_a.csv
```

```text
{
  "imported": 2,
  "rejected": 6,
  "stock_value_yuan": "7532.50",
  "problems": [
    "第 4 行：价格必须大于 0：-3",
    "第 5 行：价格不是数字：'abc'",
    "第 6 行：sku 重复：TE-1002",
    "第 7 行：sku 和 name 不能为空",
    "第 8 行：价格最多两位小数：210.125",
    "第 9 行：库存必须是非负整数：''"
  ]
}
```

示例文件故意包含了各种问题。每一种都对应一个测试。

## 现在可以等一等的地方

整个工具是一个文件、几个函数，没有类层次，没有接口，没有注册表。下面这些问题，现在**有意不去解决**：

- **只支持 CSV。** 将来可能有别的格式，但现在只有一家供应商，只有这一种格式。
- **校验规则写在一个循环里。** 现在只有五条规则，读起来很清楚。
- **只输出一份报告。** 不写数据库，不调用网店的接口。
- **整个文件一次读进内存。** 价目表只有几百行。

对照[第 04 章](../part-01/04-choosing-a-pattern.md)的检查清单：这些变化**还没有发生，也没有明确的计划**。现在为它们设计扩展点，只会让代码更难读，而且很可能猜错扩展的方向。

但是，**有一件事现在就要做**：测试。下一章要重构这个工具，重构的前提是“行为不变”，而能证明行为不变的只有测试。本章的测试覆盖了价格解析的各种边界、每一种被拒绝的行、缺少列、BOM、退出码。它们是下一章的安全网。

## 小结

- 第一个版本只解决眼前的一种格式，但要把它做对：用 `Decimal` 处理金额，用 `utf-8-sig` 处理 Excel 的 BOM，逐行收集错误并报告行号，用退出码表达结果。
- 先定数据的样子（`Product`、`Problem`），再写处理。
- 还没有发生的变化，先不为它设计扩展点。
- 测试是现在就要做的投资：它们固定了行为，是下一章重构的安全网。

## 练习

店主反馈：有时候供应商的价格写成 `"¥128.00"` 或者 `"1,280.00"`。

1. 这算“格式的变化”，还是“校验规则的变化”，还是“数据清洗”？应该改在哪里？
2. 应该自动接受这些写法，还是报错让供应商改？各有什么风险？
3. 写出你会为这个修改增加的测试用例。

**思路提示**：这是对价格**文本**的清洗，最合适的位置是 `parse_price` 开头：去掉货币符号和千位分隔符，再交给 `Decimal`。是否自动接受，要看风险：`¥` 符号基本没有歧义，可以去掉；而 `1,280.00` 在一些国家的写法里，逗号是小数点，`1,280` 可能表示 1.28，自动处理就有可能出错。比较稳妥的做法是只接受“逗号后面正好三位数字”的千位分隔写法，其他情况报错。测试至少要包括 `"¥128.00"`、`"1,280.00"`，以及一个应该被拒绝的模糊写法，比如 `"1,28"`。这个练习说明，“小改动”也需要先想清楚含义，并用测试把决定固定下来。

完整代码：
- [`examples/ch32_import_v1.py`](../../examples/ch32_import_v1.py)：第一版导入工具
- [`examples/data/supplier_a.csv`](../../examples/data/supplier_a.csv)：示例价目表

测试：[`tests/test_ch32_import_v1.py`](../../tests/test_ch32_import_v1.py)。
