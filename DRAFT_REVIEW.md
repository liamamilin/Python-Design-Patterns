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
| 04 | 从问题选择模式 | 未开始 | | |
| 05–34 | | 未开始 | | |

## 留待人工判断的问题

（随章节补充）
