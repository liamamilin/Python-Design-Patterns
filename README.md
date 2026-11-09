# Python 设计模式：从问题到方案

> 不从模式名称开始，而从它要解决的问题开始。
>
> 核心问题：当程序不断变化时，为什么普通的 Python 写法有时不再好用？什么时候值得引入一种设计模式？

这是一本面向**掌握 Python 基础语法、希望学会组织程序的读者**的中文书稿项目。它以「数据与数据的处理」作为思考起点，逐步走向对象、协作、变化和设计模式。重点是理解**为什么这样设计**，而不是背诵 23 个名称。

## 阅读本仓库

- [正文 book/](book/README.md)：全书 34 章初稿，从这里开始阅读。每章的示例代码在 [examples/](examples/)，测试在 [tests/](tests/)。
- [在线阅读全书](https://liamamilin.github.io/Python-Design-Patterns/book/)：34 章正文、前言和术语表的网页版，带目录、全书搜索、代码高亮和示意图。网页由 `python tools/build_site.py` 从 `book/` 生成到 `docs/book/`，不要手工修改；改了正文后重新运行这条命令，测试会检查网页是否和正文一致。
- [在线指南](https://liamamilin.github.io/Python-Design-Patterns/)：网站首页，包括读法、34 章路线图、按问题查找章节和一个模式的推导示例（源文件 [docs/index.html](docs/index.html)），路线图和查找结果直接链接到各章网页。
- [BOOK_PLAN.md](BOOK_PLAN.md)：本书目标、边界、内容结构及逐章问题清单；**全书内容的基准**。
- [WRITING_GUIDE.md](WRITING_GUIDE.md)：章节叙述方法、Python 代码质量和审稿标准。
- [AGENT_TASK.md](AGENT_TASK.md)：直接交给 Codex / Claude Code 的写作任务书。
- [samples/factory-method-walkthrough.md](samples/factory-method-walkthrough.md)：如何从「不需要模式」推导到「什么时候值得考虑工厂方法」的写作示范。

## 本书采用的基本方法

1. 先讲一个真实、具体、很小的问题，再写最简单的可行 Python。
2. 让问题发生**明确的变化**，观察原写法究竟在哪里变得难用；如果没有困难，就不强行使用模式。
3. 解释设计模式改变了哪些责任、数据关系或处理步骤。
4. 写出可运行的 Python 实现，同时给出更符合 Python 习惯的简单替代。
5. 清楚地说明：**什么时候不应该用这个模式**。

## 内容范围

完整讨论 GoF 的 23 个经典设计模式，但不把 GoF 的类图当成 Python 的唯一标准答案。还会介绍函数、字典、协议、装饰器、组合和依赖注入等 Python 常见做法，以及在实际项目中如何做取舍。

**当前状态：** 全书 34 章**正文初稿已完成**，等待人工审阅。每章都配有可运行的示例和测试；书中的每段 Python 代码都原样出自 `examples/` 中的文件。写作进度、已执行的检查和待人工判断的问题记录在 [DRAFT_REVIEW.md](DRAFT_REVIEW.md)。

在仓库根目录运行全部测试（需要 Python 3.11 或更高版本，只用标准库）：

```text
python -m unittest discover -s tests
```

## 读者需要什么

能读懂变量、条件判断、循环、函数与最基本的类即可。每一章都应尽量独立阅读；遇到必须使用的新概念，先用普通语言解释，再引入术语。

## 书名

《Python 设计模式：从问题到方案》

副标题：理解设计模式为什么存在、何时使用，以及 Python 还能怎样做。

---

本仓库把“书的写作规格”和“正式书稿”区分开：规划文件约束方向，正文可以在具体问题和实例上持续改进，不必机械服从某一种代码结构。