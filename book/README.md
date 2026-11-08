# 《Python 设计模式：从问题到方案》正文

> 不从模式名称开始，而从它要解决的问题开始。

本目录是全书正文。每章先讲一个具体的小问题和最简单的 Python 写法，再让需求发生明确的变化，看原写法在哪里变难，然后才讨论设计模式和更轻量的 Python 替代方案，最后说明代价和不该使用的情况。

## 如何阅读

- 第一部分是全书的基础，建议按顺序读。
- 第二到第四部分的每个模式章都可以单独阅读；遇到前面讲过的概念，会给出章节链接。
- 第五部分回到 Python 语言本身，第六部分用一个贯穿案例把前面的选择放回真实项目。

## 运行示例与测试

需要 Python 3.11 或更高版本，只用标准库，不需要网络或 API 密钥。在仓库根目录运行：

```text
python -m unittest discover -s tests -v
```

单独运行某一章的示例，例如：

```text
python -m examples.ch05_factory_method
```

书中的每段 Python 代码都原样摘自 `examples/` 目录下对应的文件。`python tools/check_book_code.py` 会检查这一点，它也包含在上面的测试里。

## 目录

### 第一部分 · 为什么需要设计

- [01 从数据与处理理解程序](part-01/01-data-and-processing.md)
- [02 当简单代码开始难以改变](part-01/02-when-simple-code-resists-change.md)
- [03 Python 组织程序的基本工具](part-01/03-python-building-blocks.md)
- [04 从问题选择模式](part-01/04-choosing-a-pattern.md)

### 第二部分 · 创建对象（GoF 创建型）

- [05 工厂方法 Factory Method](part-02/05-factory-method.md)
- [06 抽象工厂 Abstract Factory](part-02/06-abstract-factory.md)
- [07 建造者 Builder](part-02/07-builder.md)
- [08 原型 Prototype](part-02/08-prototype.md)
- [09 单例 Singleton](part-02/09-singleton.md)

### 第三部分 · 组合对象（GoF 结构型）

- [10 适配器 Adapter](part-03/10-adapter.md)
- 11 桥接 Bridge（写作中）
- 12 组合 Composite（写作中）
- 13 装饰器 Decorator（写作中）
- 14 外观 Facade（写作中）
- 15 享元 Flyweight（写作中）
- 16 代理 Proxy（写作中）

### 第四部分 · 协调处理（GoF 行为型）

- 17 策略 Strategy（写作中）
- 18 观察者 Observer（写作中）
- 19 命令 Command（写作中）
- 20 状态 State（写作中）
- 21 模板方法 Template Method（写作中）
- 22 责任链 Chain of Responsibility（写作中）
- 23 迭代器 Iterator（写作中）
- 24 中介者 Mediator（写作中）
- 25 备忘录 Memento（写作中）
- 26 访问者 Visitor（写作中）
- 27 解释器 Interpreter（写作中）

### 第五部分 · 回到 Python

- 28 函数就是一种设计工具（写作中）
- 29 类型与接口的轻量表达（写作中）
- 30 Python 装饰器、上下文管理器和生成器（写作中）
- 31 简单代码与模式代码的取舍（写作中）

### 第六部分 · 把选择放回真实项目

- 32 第一次实现：不使用模式（写作中）
- 33 需求改变：有选择地重构（写作中）
- 34 回顾：能解释自己为什么这样写（写作中）
