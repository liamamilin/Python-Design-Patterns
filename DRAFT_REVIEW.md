# 初稿进度与审阅记录 · DRAFT REVIEW

> 写作过程中持续更新。只有写出真实正文、示例与测试通过的章节才记为“完成”。

## 检查方法

在仓库根目录运行（需要 Python 3.11+）：

```text
python -m unittest discover -s tests -v
python tools/check_book_code.py
```

- `tests/` 验证各章示例的行为，以及正文中声称的输出。
- `tools/check_book_code.py` 确认正文里每个 ```python 代码块都原样出自对应的 `examples/chXX_*.py`，避免书中代码与仓库代码不一致。它也作为 `tests/test_book_code.py` 的一部分自动运行。

## 章节状态

| 章 | 标题 | 正文 | 示例 | 测试 |
|---|---|---|---|---|
| 01 | 从数据与处理理解程序 | 完成 | `ch01_receipt.py` | 通过 |
| 02 | 当简单代码开始难以改变 | 完成 | `ch02_report_v1.py`、`_before.py`、`_after.py` | 通过 |
| 03 | Python 组织程序的基本工具 | 完成 | `ch03_tools.py` | 通过 |
| 04 | 从问题选择模式 | 完成 | `ch04_parking.py` | 通过 |
| 05 | 工厂方法 | 完成 | `ch05_factory_method_v1.py`、`_simple_factory.py`、`ch05_factory_method.py`、`ch05_pythonic.py` | 通过 |
| 06 | 抽象工厂 | 完成 | `ch06_reminders_v1.py`、`ch06_abstract_factory.py`、`ch06_pythonic.py` | 通过 |
| 07 | 建造者 | 完成 | `ch07_search_v1.py`、`ch07_builder.py`、`ch07_pythonic.py` | 通过 |
| 08–34 | | 未开始 | | |

已执行的检查（第一批，第 01–05 章）：
- 42 个测试在 Python 3.11.13 和 3.12.14 下全部通过；
- `tools/check_book_code.py`：正文代码与示例文件一致；
- `book/` 内所有相对链接有效；每个示例模块都能单独运行。

## 留待人工判断的问题

1. **第 05 章没有沿用 `samples/factory-method-walkthrough.md` 的邮件／短信例子**，改用“任务清单生成文档”。依据是 AGENT_TASK 说示范稿只示范思考过程、不是让人复制案例。但在线指南的推导示例写着“完整内容见第 05 章”，下次更新指南时需要改成类似“第 05 章用另一个例子完整展开”。
2. **第 04 章的 GoF 意图表**是对原书意图的中文概括，不是原文引用。第 05 章引用了工厂方法意图的常见中文表述，并注明出处。如需与某个中译本的措辞完全一致，请人工核对。
3. **第 01–03 章没有对应的 GoF 模式**，但同样配了示例和测试，用来验证正文里声称的输出（例如第 02 章两处错误能被复现）。
