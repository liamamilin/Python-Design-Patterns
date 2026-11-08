# 写作示范：为什么会需要“工厂”？

> 这不是“工厂方法”一章的完成稿，而是展示如何从问题出发、识别何时真正有设计需要的**推导样例**。正式写作参见 [BOOK_PLAN.md](../BOOK_PLAN.md) 第 05 章。

## 1. 先做一件非常普通的事

我们写一个小工具，生成一段发给用户的通知文字。现在只有邮件一种方式。

```python
class EmailSender:
    def send(self, message: str) -> str:
        return f"Email: {message}"


sender = EmailSender()
print(sender.send("订单已发货"))  # Email: 订单已发货
```

这段代码可以解决当前任务。不存在需要“升级”它的理由。

这里的数据是消息正文、发送方式；处理是选择发送者并生成消息。这个示例只**模拟返回文字**，没有发送真实邮件。

## 2. 增加需求：短信通知

现在需要邮件或短信两种方式，可以先直接判断：

```python
class SmsSender:
    def send(self, message: str) -> str:
        return f"SMS: {message}"


def notify(channel: str, message: str) -> str:
    if channel == "email":
        sender = EmailSender()
    elif channel == "sms":
        sender = SmsSender()
    else:
        raise ValueError(f"未知渠道: {channel}")
    return sender.send(message)


print(notify("sms", "订单已发货"))  # SMS: 订单已发货
```

如果只有这一个入口、两种方式，**这依然是好代码**。不要为了有两行判断就立即引入设计模式。

## 3. 什么时候出现实际困难？

假设另一处“发送每日报告”也写了一套相同的条件判断。后来增加第三种渠道，开发者必须在多个位置修改选择逻辑，还可能漏掉其中一处。

真正的问题是**创建什么发送者这一决策分散在多处**；不是 `if` 语句本身有错。

对于这个具体问题，最朴素的解决方法通常是**集中创建逻辑**：

```python
def make_sender(channel: str):
    senders = {"email": EmailSender, "sms": SmsSender}
    try:
        sender_type = senders[channel]
    except KeyError:
        raise ValueError(f"未知渠道: {channel}") from None
    return sender_type()


def notify(channel: str, message: str) -> str:
    return make_sender(channel).send(message)
```

这个 `make_sender` 是一种**简单工厂函数**。它已经解决了“多处重复选择”的问题。不要仅因为使用了“工厂”这个词，就把它宣称为 GoF 的 **Factory Method（工厂方法）**。

## 4. 进一步变化：创建决策随调用方类型而变

现在不是所有调用场景都允许相同渠道。比如，“交易通知”默认用邮件，“紧急通知”默认用短信；创建逻辑与不同任务类型本身绑定，且这些任务有共同的工作流程。

一个经典的 GoF 工厂方法示范是：**父类定义工作流程和创建入口，让子类决定创建哪一种具体产品**。

```python
from abc import ABC, abstractmethod


class NotificationJob(ABC):
    def run(self, message: str) -> str:
        sender = self.create_sender()
        return sender.send(message)

    @abstractmethod
    def create_sender(self):
        """由不同类型的任务决定使用哪种发送者。"""


class TransactionJob(NotificationJob):
    def create_sender(self):
        return EmailSender()


class UrgentJob(NotificationJob):
    def create_sender(self):
        return SmsSender()


print(TransactionJob().run("订单已发货"))  # Email: 订单已发货
print(UrgentJob().run("系统告警"))           # SMS: 系统告警
```

这里的角色关系是：

- **产品**：具备 `send` 能力的发送者，这个小例子里不需要专门创建一个产品基类；
- **创建者**：`NotificationJob` 定义固定工作流程与 `create_sender` 入口；
- **具体创建者**：`TransactionJob` / `UrgentJob` 决定实例化哪一种具体发送者。

这体现了 GoF 工厂方法的核心：**通过子类决定要实例化哪个具体产品**。它不是“任何返回对象的函数”都可以算作的模式。

## 5. 这样写就一定更好吗？

不一定。此时只有两个场景，不同任务之间的处理步骤也没有真正出现复杂差异，那么新增抽象基类和两个子类可能比两行判断更费解。

如果不需要父类固定流程、不需要不同子类复用和定制创建行为，**保留一个简单工厂函数更合适**。

这就是全书希望读者学会的判断：

> 模式存在，不代表当前必须采用。先看问题有没有发生，再看模式能否用合理的成本解决问题。

## 6. 本例还欠什么？

作为写作示范，这里有意没有实现完整的业务异常处理、渠道配置和真实发送服务。正式章节需要补充：

- 同一需求在“普通函数方案”和“经典工厂方法方案”中的对照，并解释为何会选择其中之一；
- 实际可执行的 `examples/` 文件及对应 `tests/`；
- 返回类型协议（可选择 `Protocol`）与更清晰的注释；
- 简单工厂、GoF 工厂方法、抽象工厂三个术语的分界；
- 一道练习：当新通知渠道不断添加，但通知任务流程固定时，哪种写法最容易维护？当渠道仅两种且变化很少呢？

本例只是**教学形态示范**，不是为了强行证明工厂方法胜过简单函数。