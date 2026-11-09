# 初稿进度与审阅记录 · DRAFT REVIEW

> 写作过程中持续更新。只有写出真实正文、示例与测试通过的章节才记为“完成”。

## 检查方法

在仓库根目录运行（需要 Python 3.11+）：

```text
python -m unittest discover -s tests -v
python tools/check_book_code.py
python tools/check_links.py
```

- `tests/` 验证各章示例的行为，以及正文中声称的输出。
- `tools/check_book_code.py` 确认正文里每个 ```python 代码块都原样出自对应的 `examples/chXX_*.py`，避免书中代码与仓库代码不一致。它也作为 `tests/test_book_code.py` 的一部分自动运行。
- `tools/check_links.py` 确认 `book/` 里的相对链接都指向存在的文件（代码块不算），并要求提到已写好的章节时写成链接。它也作为 `tests/test_book_links.py` 的一部分自动运行。

## 章节状态

| 章 | 标题 | 例子（领域） | 正文 | 示例 | 测试 |
|---|---|---|---|---|---|
| 01 | 从数据与处理理解程序 | 咖啡店小票 | 完成 | `ch01_receipt.py` | 通过 |
| 02 | 当简单代码开始难以改变 | 班级成绩单 | 完成 | `ch02_report_v1.py`、`_before.py`、`_after.py` | 通过 |
| 03 | Python 组织程序的基本工具 | 评论清洗 | 完成 | `ch03_tools.py` | 通过 |
| 04 | 从问题选择模式 | 停车场收费 | 完成 | `ch04_parking.py` | 通过 |
| 05 | 工厂方法 | 任务清单生成文档 | 完成 | `ch05_factory_method_v1.py`、`_simple_factory.py`、`ch05_factory_method.py`、`ch05_pythonic.py` | 通过 |
| 06 | 抽象工厂 | 图书馆还书提醒（正式／演练／内存三个家族） | 完成 | `ch06_reminders_v1.py`、`ch06_abstract_factory.py`、`ch06_pythonic.py` | 通过 |
| 07 | 建造者 | 租房搜索（SQL 与筛选说明） | 完成 | `ch07_search_v1.py`、`ch07_builder.py`、`ch07_pythonic.py` | 通过 |
| 08 | 原型 | 健身训练计划模板 | 完成 | `ch08_copy_trap.py`、`ch08_prototype.py`、`ch08_pythonic.py` | 通过 |
| 09 | 单例 | 银行排队取号 | 完成 | `ch09_ticket_v1.py`、`ch09_singleton.py`、`ch09_shared_counter.py`、`ch09_pythonic.py` | 通过 |
| 10 | 适配器 | 考勤报表接入云考勤机 | 完成 | `ch10_attendance.py`、`ch10_cloud_sdk.py`、`ch10_report_v1.py`、`ch10_adapter.py`、`ch10_pythonic.py` | 通过 |
| 11 | 桥接 | 降雨量图表（图表种类 × 画布） | 完成 | `ch11_charts_v1.py`、`ch11_bridge.py`、`ch11_pythonic.py` | 通过 |
| 12 | 组合 | 装修预算（房间、项目、打包折扣） | 完成 | `ch12_budget_v1.py`、`ch12_composite.py`、`ch12_pythonic.py` | 通过 |
| 13 | 装饰器 | 客服聊天记录导出（打码、截断） | 完成 | `ch13_export_v1.py`、`ch13_decorator.py`、`ch13_pythonic.py` | 通过 |
| 14 | 外观 | 设计工作室文档备份（zip、清单、轮换） | 完成 | `ch14_backup_v1.py`、`ch14_facade.py`、`ch14_pythonic.py` | 通过 |
| 15 | 享元 | 地铁闸机刷卡记录（共享车站，tracemalloc 实测） | 完成 | `ch15_taps_v1.py`、`ch15_flyweight.py`、`ch15_pythonic.py` | 通过 |
| 16 | 代理 | 在线课程讲义（延迟加载、付费检查） | 完成 | `ch16_course_v1.py`、`ch16_proxy.py`、`ch16_pythonic.py` | 通过 |
| 17 | 策略 | 订单运费（AGENT_TASK 指定） | 完成 | `ch17_shipping_v1.py`、`ch17_strategy.py`、`ch17_pythonic.py` | 通过 |
| 18 | 观察者 | 温室温度传感器（风扇、记录、首次高温提醒） | 完成 | `ch18_greenhouse_v1.py`、`ch18_observer.py`、`ch18_pythonic.py` | 通过 |
| 19 | 命令 | 五金仓库库存（撤销、幂等、补货通知） | 完成 | `ch19_stock_v1.py`、`ch19_command.py`、`ch19_pythonic.py` | 通过 |
| 20 | 状态 | 会议室预订（审批、签到、超时释放） | 完成 | `ch20_booking_v1.py`、`ch20_state.py`、`ch20_pythonic.py` | 通过 |
| 21 | 模板方法 | 跳水与歌手比赛计分（同分并列） | 完成 | `ch21_contest_v1.py`、`ch21_template_method.py`、`ch21_pythonic.py` | 通过 |
| 22 | 责任链 | 智能音箱指令（儿童锁） | 完成 | `ch22_speaker_v1.py`、`ch22_chain.py`、`ch22_pythonic.py` | 通过 |
| 23 | 迭代器 | 分页的云相册（按需翻页） | 完成 | `ch23_photos_v1.py`、`ch23_iterator.py`、`ch23_pythonic.py` | 通过 |
| 24 | 中介者 | 机票预订表单联动（护照栏、查询按钮） | 完成 | `ch24_form_v1.py`、`ch24_mediator.py`、`ch24_pythonic.py` | 通过 |
| 25 | 备忘录 | 农场小游戏存档 | 完成 | `ch25_farm_v1.py`、`ch25_memento.py`、`ch25_pythonic.py` | 通过 |
| 26 | 访问者 | 文章内容块（字数、无障碍检查） | 完成 | `ch26_article_v1.py`、`ch26_visitor.py`、`ch26_pythonic.py` | 通过 |
| 27 | 解释器 | 活动报名资格规则（拒绝 eval） | 完成 | `ch27_rules_v1.py`、`ch27_interpreter.py`、`ch27_pythonic.py` | 通过 |
| 28 | 函数作为设计工具 | 命令行记账（分类规则、命令分派） | 完成 | `ch28_classes.py`、`ch28_functions.py` | 通过 |
| 29 | 类型与接口 | 宠物医院预约（标注、NewType、校验） | 完成 | `ch29_types.py` | 通过 |
| 30 | 装饰器、上下文管理器和生成器 | 批量重命名照片（全改或全不改） | 完成 | `ch30_rename_v1.py`、`ch30_language.py` | 通过 |
| 31 | 简单代码与模式代码的取舍 | 咖啡店会员积分（规则顺序依赖） | 完成 | `ch31_points.py` | 通过 |
| 32 | 第一次实现 | 数据导入工具：茶叶店供应商价目表（CSV） | 完成 | `ch32_import_v1.py`、`data/supplier_a.csv` | 通过 |
| 33 | 有选择地重构 | 数据导入工具：JSON 供应商、新规则、写入 SQLite | 完成 | `ch33_importer.py`、`data/supplier_b.json` | 通过 |
| 34 | 回顾 | 数据导入工具：两种设计的比较 | 完成 | `ch34_class_based.py` | 通过 |

已预留的例子：第 17 章策略用运费计算（AGENT_TASK 的示例）；第六部分（32–34）用数据导入工具。其余章节选用新的领域，不与上表重复。

已执行的检查（第一批，第 01–05 章）：
- 42 个测试在 Python 3.11.13 和 3.12.14 下全部通过；
- `tools/check_book_code.py`：正文代码与示例文件一致；
- `book/` 内所有相对链接有效；每个示例模块都能单独运行。

已执行的检查（第二批，第 06–09 章）：
- 全部 78 个测试在 Python 3.11.13 和 3.12.14 下通过，包括第 09 章用 `spawn` 方式启动子进程的两个测试；
- 正文代码与示例文件一致；`book/` 内相对链接有效；第 06–09 章每个示例模块都能单独运行。

已执行的检查（第三批，第 10–16 章）：
- 全部测试在 Python 3.11.13 和 3.12.14 下通过；正文代码与示例一致；`tools/check_links.py` 通过；每个示例模块都能单独运行。
- 第 15 章的内存结论只来自 `tracemalloc` 实测，测试只断言相对大小（共享版本更小），不断言字节数。

已执行的检查（第四批，第 17–27 章）：
- 全部测试在 Python 3.11.13 和 3.12.14 下通过；正文代码与示例一致；链接检查通过；每个示例模块都能单独运行。
- 第 18 章写明了通知顺序、快照遍历、错误隔离（`ExceptionGroup`）三条约定；第 19 章把撤销、幂等、重试分开讨论，并给出不可撤销操作；第 27 章的规则语言不使用 `eval`，并用测试验证恶意规则被拒绝。

已执行的检查（第五、六批及全书，第 28–34 章）：
- 全书 259 个测试在 Python 3.11.13 和 3.12.14 下全部通过；
- `tools/check_book_code.py`：34 章正文中的每个 Python 代码块都原样出自 `examples/`；
- `tools/check_links.py`：`book/` 内所有相对链接有效，所有章节引用都已写成链接；
- 88 个示例模块逐一单独运行，没有异常；
- 仓库 README 的状态说明、在线指南（`docs/index.html`）的状态标签和第 05 章措辞已更新，指南首页加了“阅读正文初稿”的链接（指向 GitHub 上的 `book/README.md`，需要合并到 main 后才有效）。

## 第二轮：全书校对（初稿合并之后）

- 机械检查：重复字、中英文标点混用、括号配对，全书没有发现问题（章标题中的全角空格是有意的）。
- 逐章通读第 06–34 章，修正的主要是表述不准确的地方，例如：第 06 章把 Java 式的 “new 一个对象” 改成 Python 的说法；第 07 章把 “塞进任意 SQL” 改为准确的 SQL 注入描述；第 09 章说明依赖注入并不能解决“只在一个进程内唯一”；第 12 章把“单价”改为“单项花费”；第 16 章说明 `cached_property` 可以用 `del` 手动失效；第 22 章修正“充话费”与关键词不一致；第 24 章删去“儿童票不需要护照”这一不准确的说法；第 28 章让类与闭包的对照写法和代码一致。
- 第六部分的导入工具补了三个边界情况：CSV 行缺列、价格超出范围（如 `1e30`）、JSON 格式错误，均有测试。
- 新增 [book/preface.md](book/preface.md) 前言，并在 `book/README.md` 中链接。
- 仍未做的：没有逐字的文字润色和统一的术语表；没有插图；书名仍为暂定。

## 第三轮（第二轮之后）

- 重读第 01–05 章，没有发现事实问题。
- 统一术语：一般意义上的“调用者”统一为“调用方”（第 19 章的 GoF 角色 Invoker 仍译作“调用者”）；“类型检查工具”统一为“类型检查器”。
- 新增 [book/glossary.md](book/glossary.md) 术语表：26 个通用术语和 23 种模式的中英对照，每项链接到详细讨论的章节。

## 尚待兑现的跨章承诺

写到目标章节时要回应这些前文的说法，写完后从这里划掉：

- ~~第 05 章练习指向第 11 章桥接~~：已在第 11 章开头和“Python 角度”中回应。
- ~~第 05 章：工厂方法是模板方法中负责创建的一步~~：第 21 章“和工厂方法的关系”一节已回应。
- ~~第 01–04 章对第 13、17、18、20、25、28、29、30 章的预告~~：全书完成后逐条核对，与正文一致。
- ~~第 13 章→第 30 章 `@` 语法~~：第 30 章“装饰器：登记，而不是包装”已回应。
- ~~第 15 章→第 23 章边读边处理~~：第 23 章“边读边处理”一节已回应。
- ~~第 16 章叠加顺序~~：第 22 章“顺序依然重要”一节已呼应第 13、16 章。
- ~~第 17、03 章→第 28 章~~：已回应。
- ~~第 03 章→第 29 章 `Protocol`~~：已回应。
- ~~第 01 章积分规则~~：第 31 章以积分规则为例回应。
- 链接规则：提到其他章节一律写成相对链接，`tools/check_links.py` 会检查。全书完成后，所有章节引用都已是链接。

## 留待人工判断的问题

1. **（已处理）第 05 章没有沿用 `samples/factory-method-walkthrough.md` 的邮件／短信例子**，改用“任务清单生成文档”。依据是 AGENT_TASK 说示范稿只示范思考过程、不是让人复制案例。但在线指南的推导示例写着“完整内容见第 05 章”，下次更新指南时需要改成类似“第 05 章用另一个例子完整展开”。
2. **（已核对含义）第 04 章的 GoF 意图表**是本书自己的中文概括，已逐条与 GoF 英文原书的意图对照，含义一致（去掉了解释器一行中原文没有的“简单”二字）。各模式章里“GoF 对……的描述是”后面的引文，采用的是常见的中文译法；如果正式出版，需要注明所依据的中译本及版次。
3. **第 01–03 章没有对应的 GoF 模式**，但同样配了示例和测试，用来验证正文里声称的输出（例如第 02 章两处错误能被复现）。
4. **第 09 章的进程测试**会启动子进程，在受限的沙箱或某些 CI 环境里可能无法运行。如果遇到这种情况，可以单独跳过 `test_each_process_has_its_own_instance` 和 `test_unique_across_processes`，其余测试不依赖子进程。
