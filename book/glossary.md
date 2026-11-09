# 术语表

本书用到的主要术语，按首次详细讨论的章节排列。中文译名采用本书正文的用法，“英文”一列是常见的英文说法。

## 通用术语

| 术语 | 英文 | 含义 | 见 |
|---|---|---|---|
| 数据类 | dataclass | 用 `@dataclass` 声明的类，自动生成构造方法、显示和比较；加 `frozen=True` 后不可修改。 | [第 01 章](part-01/01-data-and-processing.md) |
| 状态 | state | 对象记住的、会影响之后结果的数据。 | [第 01 章](part-01/01-data-and-processing.md) |
| 副作用 | side effect | 函数除了返回结果之外，对外部世界产生的影响，如写文件、打印、发消息。 | [第 01 章](part-01/01-data-and-processing.md) |
| 重构 | refactoring | 不改变外部行为，只改善代码结构的修改。重构前要有测试保证行为不变。 | [第 02 章](part-01/02-when-simple-code-resists-change.md) |
| 组合 | composition | 把部件装进一个对象里来复用和搭配行为，与继承相对。 | [第 03 章](part-01/03-python-building-blocks.md) |
| 继承 | inheritance | 子类在父类的基础上复用并改写行为。 | [第 03 章](part-01/03-python-building-blocks.md) |
| 抽象基类 | abstract base class (ABC) | 用 `abc` 模块声明的基类，带 `@abstractmethod` 的方法没实现时，子类无法实例化。 | [第 03 章](part-01/03-python-building-blocks.md) |
| 协议 | protocol (`typing.Protocol`) | 只规定需要哪些方法、不要求继承的接口描述，即结构化类型。 | [第 03 章](part-01/03-python-building-blocks.md) |
| 可调用对象 | callable | 能用 `()` 调用的对象：函数、类、实现了 `__call__` 的实例。 | [第 03 章](part-01/03-python-building-blocks.md) |
| 简单工厂 | simple factory | 根据参数决定创建哪种对象的普通函数。很常用，但不是 GoF 23 种模式之一。 | [第 05 章](part-02/05-factory-method.md) |
| 浅拷贝 | shallow copy | 只复制最外层对象，内部引用的对象与原件共享。 | [第 08 章](part-02/08-prototype.md) |
| 深拷贝 | deep copy | 顺着引用把整个对象图都复制一份。 | [第 08 章](part-02/08-prototype.md) |
| 依赖注入 | dependency injection | 对象需要的东西由外部传入，而不是自己创建或查找。 | [第 09 章](part-02/09-singleton.md) |
| 内部状态／外部状态 | intrinsic / extrinsic state | 享元中可共享、与场合无关的部分／随场合变化、不能共享的部分。 | [第 15 章](part-03/15-flyweight.md) |
| 虚代理 | virtual proxy | 延迟创建昂贵对象的代理。 | [第 16 章](part-03/16-proxy.md) |
| 保护代理 | protection proxy | 在转交请求前检查权限的代理。 | [第 16 章](part-03/16-proxy.md) |
| 幂等 | idempotence | 同一个操作执行一次和执行多次，效果相同。 | [第 19 章](part-04/19-command.md) |
| 钩子 | hook | 模板方法中有默认实现、子类可以选择覆盖的步骤。 | [第 21 章](part-04/21-template-method.md) |
| 生成器 | generator | 含有 `yield` 的函数，调用后返回一个按需产出值的迭代器。 | [第 23 章](part-04/23-iterator.md) |
| 迭代器／可迭代对象 | iterator / iterable | 迭代器有 `__next__`、只能走一遍；可迭代对象的 `__iter__` 每次给出新的迭代器。 | [第 23 章](part-04/23-iterator.md) |
| 双重分派 | double dispatch | 执行哪段代码同时取决于两个对象的类型；访问者用 `accept` 实现它。 | [第 26 章](part-04/26-visitor.md) |
| 闭包 | closure | 记住了创建时所在环境中变量的函数。 | [第 28 章](part-05/28-functions-as-design-tools.md) |
| 高阶函数 | higher-order function | 接收函数作为参数，或返回函数的函数。 | [第 28 章](part-05/28-functions-as-design-tools.md) |
| 字典分派 | dict dispatch | 用字典把名字映射到函数或类，代替一串 `if`。 | [第 28 章](part-05/28-functions-as-design-tools.md) |
| 类型检查器 | type checker | 如 mypy、pyright，在运行前根据类型标注检查代码。Python 运行时不检查标注。 | [第 29 章](part-05/29-types-and-interfaces.md) |
| 上下文管理器 | context manager | 配合 `with` 使用、负责准备和收尾的对象。 | [第 30 章](part-05/30-decorators-context-managers-generators.md) |

## GoF 23 种设计模式

注意：“组合”既指组合模式（Composite），也泛指“组合优于继承”中的对象组合（composition），本书在上下文中区分。

| 模式 | 英文 | 见 |
|---|---|---|
| 工厂方法 | Factory Method | [第 05 章](part-02/05-factory-method.md) |
| 抽象工厂 | Abstract Factory | [第 06 章](part-02/06-abstract-factory.md) |
| 建造者 | Builder | [第 07 章](part-02/07-builder.md) |
| 原型 | Prototype | [第 08 章](part-02/08-prototype.md) |
| 单例 | Singleton | [第 09 章](part-02/09-singleton.md) |
| 适配器 | Adapter | [第 10 章](part-03/10-adapter.md) |
| 桥接 | Bridge | [第 11 章](part-03/11-bridge.md) |
| 组合 | Composite | [第 12 章](part-03/12-composite.md) |
| 装饰器 | Decorator | [第 13 章](part-03/13-decorator.md) |
| 外观 | Facade | [第 14 章](part-03/14-facade.md) |
| 享元 | Flyweight | [第 15 章](part-03/15-flyweight.md) |
| 代理 | Proxy | [第 16 章](part-03/16-proxy.md) |
| 策略 | Strategy | [第 17 章](part-04/17-strategy.md) |
| 观察者 | Observer | [第 18 章](part-04/18-observer.md) |
| 命令 | Command | [第 19 章](part-04/19-command.md) |
| 状态 | State | [第 20 章](part-04/20-state.md) |
| 模板方法 | Template Method | [第 21 章](part-04/21-template-method.md) |
| 责任链 | Chain of Responsibility | [第 22 章](part-04/22-chain-of-responsibility.md) |
| 迭代器 | Iterator | [第 23 章](part-04/23-iterator.md) |
| 中介者 | Mediator | [第 24 章](part-04/24-mediator.md) |
| 备忘录 | Memento | [第 25 章](part-04/25-memento.md) |
| 访问者 | Visitor | [第 26 章](part-04/26-visitor.md) |
| 解释器 | Interpreter | [第 27 章](part-04/27-interpreter.md) |
