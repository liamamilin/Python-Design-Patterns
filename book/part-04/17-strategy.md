# 第 17 章　策略 Strategy

> 本章要回答：同一件事有好几种可以互相替换的做法时，怎样避免在多处重复同一串判断？在 Python 里，直接传一个函数是不是就够了？

第四部分讨论对象之间怎样分配职责、怎样协作。第一个模式是策略。[第 04 章](../part-01/04-choosing-a-pattern.md)用停车场收费比较过三种写法，其中“每种规则一个类”就是策略的经典形式。那一章关心的是“怎样选择”；这一章把策略本身讲透：它真正解决的问题、策略对象应该长什么样，以及什么时候一个函数就够了。

## 眼前的任务

一家网店要为订单计算运费。订单的信息是这样的：

```python
@dataclass(frozen=True)
class Order:
    weight_g: int
    distance_km: float
    subtotal: int  # 商品金额，单位：分
```

今天只有普通快递：首重 1 公斤 8 元，续重每公斤 3 元，商品满 99 元包邮。一个函数、几行代码就能算出来。

后来加了同城急送（起步 15 元，每公里 2 元）和到店自提（免费）。函数里加两个判断，也完全合理。

## 不用模式的写法

结算页根据顾客选的配送方式算运费：

```python
def checkout_fee(order: Order, method: str) -> int:
    """结算页：顾客选定一种配送方式后显示运费。"""
    if method == "express":
        if order.subtotal >= 9900:
            return 0
        kg = math.ceil(order.weight_g / 1000)
        return 800 + (kg - 1) * 300  # 续重费上个月从 2 元调到了 3 元
    if method == "same_city":
        return 1500 + math.ceil(order.distance_km) * 200
    if method == "pickup":
        return 0
    raise ValueError(f"未知配送方式: {method}")
```

**单看这个函数，这是好代码。** 三种方式、三个分支，一目了然。

## 变化：同一套规则出现在好几个地方

问题出在别处。客服后台有一个“批量报价”功能，把一个订单所有配送方式的运费都列出来，方便回答顾客“哪种最便宜”。写它的同事没有调用 `checkout_fee`（那个函数一次只能算一种），而是照着规则又写了一遍：

```python
def quote_all(order: Order) -> dict[str, int]:
    """批量报价：给客服看一个订单所有配送方式的运费。"""
    kg = math.ceil(order.weight_g / 1000)
    express = 0 if order.subtotal >= 9900 else 800 + (kg - 1) * 200  # 这里还是旧费率
    return {
        "express": express,
        "same_city": 1500 + math.ceil(order.distance_km) * 200,
        "pickup": 0,
    }
```

上个月续重费从 2 元调到了 3 元，改的人只改了结算页。于是一个 2.3 公斤、68 元的订单，客服报价 12 元，顾客结算时却是 14 元（测试 `test_pages_disagree_after_a_rate_change`）。订单管理页面里还有第三份规则，用来在顾客改地址时重新计算运费。

## 困难在哪里

这不是“`if` 太多”的问题。三个分支一点都不多。真正的问题是：

1. **“普通快递怎么收费”这条知识，被复制到了好几个地方。** 每个地方都要按需要的形式用它：结算页算一种，报价页算全部，订单管理页重新算。没有一个地方是这条规则的“唯一出处”。
2. **规则不只是一个数字。** 普通快递有首重、续重、包邮门槛；同城急送有起步价、每公里价，还有最远距离，超过 20 公里不送。规则还要回答“多久送到”，报价页要显示这一项。

我们需要的是：**把每种配送方式的全部规则放到一个地方，做成一个可以拿来替换的东西**。结算页拿到顾客选中的那一个，报价页拿到所有的，订单管理页拿到订单原来的那一个，大家用的都是同一个东西。

## 策略：把可替换的做法变成对象

GoF 对策略的描述是：**定义一系列算法，把它们一个个封装起来，并且使它们可以相互替换。本模式使得算法可独立于使用它的客户而变化。**

先说清楚，一种配送方式需要回答哪些问题：

```python
class ShippingMethod(Protocol):
    name: str

    def available(self, order: Order) -> bool: ...
    def fee(self, order: Order) -> int: ...
    def eta(self, order: Order) -> str: ...
```

每种配送方式是一个对象，费率作为字段保存，所以“调整费率”只需要改一处默认值，或者创建一个不同配置的对象：

```python
@dataclass(frozen=True)
class Express:
    name: ClassVar[str] = "普通快递"
    first: int = 800
    per_extra_kg: int = 300
    free_over: int = 9900

    def available(self, order: Order) -> bool:
        return True

    def fee(self, order: Order) -> int:
        if order.subtotal >= self.free_over:
            return 0
        kg = math.ceil(order.weight_g / 1000)
        return self.first + (kg - 1) * self.per_extra_kg

    def eta(self, order: Order) -> str:
        return "2–3 天"
```

同城急送有自己的“最远距离”规则，这条规则就写在它自己的 `available` 里：

```python
    def available(self, order: Order) -> bool:
        return order.distance_km <= self.max_km
```

所有配送方式登记在一处：

```python
METHODS: dict[str, ShippingMethod] = {
    "express": Express(),
    "same_city": SameCity(),
    "pickup": Pickup(),
}
```

结算页和报价页都只和 `ShippingMethod` 接口打交道：

```python
def checkout_fee(order: Order, method: ShippingMethod) -> int:
    if not method.available(order):
        raise ValueError(f"{method.name}不支持这个订单")
    return method.fee(order)


def quote_all(order: Order, methods: dict[str, ShippingMethod] = METHODS) -> list[str]:
    return [
        f"{m.name}：{m.fee(order) / 100:.2f} 元，{m.eta(order)}"
        for m in methods.values()
        if m.available(order)
    ]
```

```text
普通快递：14.00 元，2–3 天
同城急送：33.00 元，2 小时内
到店自提：0.00 元，今天可取
```

两个页面的运费一定一致，因为它们调用的是同一个对象的同一个方法。一个 25 公里外的订单，报价页自动不显示同城急送，结算页如果被选了同城急送，会明确拒绝（测试 `test_free_shipping_and_availability`）。

### 策略对象可以带配置

会员日普通快递满 59 元包邮？不需要新的类，也不需要改 `Express`，创建一个不同配置的对象就行：

```text
member_day = Express(free_over=5900)
```

默认的 `Express()` 不受影响（测试 `test_configured_strategy`）。这是把策略写成“带字段的对象”的好处：**同一种算法、不同的参数**，也能当作不同的策略来替换。

### 新增一种方式，不碰任何页面

要加“快递柜自提”，写一个提供 `name`、`available`、`fee`、`eta` 的类，登记进 `METHODS`。结算页、报价页、订单管理页都不用改（测试 `test_new_method_needs_no_change_elsewhere`）。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 策略（Strategy） | `ShippingMethod` 协议 | 所有配送方式共同的接口 |
| 具体策略（ConcreteStrategy） | `Express`、`SameCity`、`Pickup` | 各自的规则 |
| 上下文（Context） | `checkout_fee`、`quote_all` 等 | 持有或接收一个策略，通过接口使用它 |

GoF 原书里，上下文通常是一个对象，把策略保存为字段。本例的上下文是两个函数，策略作为参数传入，这在 Python 里更常见，意思是一样的。

### “选择”去哪了

[第 04 章](../part-01/04-choosing-a-pattern.md)强调过：用了策略，“根据情况选哪一个”的判断并没有消失，只是换了位置。本例中它变成了一次字典查找 `METHODS[key]`，发生在请求进来的地方（顾客提交的配送方式是一个字符串）。好处是这个选择**只发生一次**，之后的代码拿到的就是一个对象，不用再关心它是哪一种。

## 代价与边界

- **接口要事先想好。** `ShippingMethod` 有四个成员。如果将来要加“是否需要上门签收”，四个类都要跟着改（或者给一个默认实现）。接口越大，加新策略的门槛越高。
- **策略需要的数据，要能从上下文拿到。** 同城急送要距离，普通快递要重量和金额。本例把整个 `Order` 传给每个策略，各取所需，这很简单，但也意味着每个策略都依赖 `Order` 的完整结构。另一种做法是只传策略需要的数据，接口会更窄，但每加一种需要新数据的策略，就要改接口。
- **调用方要知道有哪些策略可选。** 策略模式让“怎么算”可以替换，但“有哪些可以选”这件事仍然要有人管理，本例是 `METHODS` 字典。
- **策略之间不能互相依赖。** 如果“同城急送的价格不能高于普通快递的两倍”，这条规则跨越了两个策略，放在哪一个里面都不合适，只能放到上下文或一个单独的规则里。

**什么时候不该用**：只有一个地方用到这些规则，而且规则只是几个分支。开头那个 `checkout_fee` 函数，如果全网店只有结算页这一个地方算运费，就不需要任何改动。策略的价值，在于让**多个地方共享同一套可替换的规则**，或者让规则可以在运行时**按配置替换**。

## Python 角度：函数就是一种策略

如果每种策略只需要回答**一个**问题，比如“运费是多少”，那么它就是一个函数。函数在 Python 里本来就是可以传来传去的对象：

```python
def express_fee(order: Order, first: int = 800, per_extra_kg: int = 300, free_over: int = 9900) -> int:
    if order.subtotal >= free_over:
        return 0
    return first + (math.ceil(order.weight_g / 1000) - 1) * per_extra_kg
```

```python
FEES: dict[str, FeeRule] = {
    "express": express_fee,
    "same_city": same_city_fee,
    "pickup": pickup_fee,
}

# 会员日：普通快递满 59 元包邮。不用新写一个函数，固定一个参数即可。
member_day_express = partial(express_fee, free_over=5900)
```

`functools.partial` 把一个函数的部分参数固定下来，返回一个新的可调用对象。它在这里起的作用，和 `Express(free_over=5900)` 一样：同一个算法，不同的配置。

这一版的结果和类的版本完全一样（测试 `test_functions_give_the_same_fees`），代码却短得多。那为什么本章的主体用了类？

因为本例的每种配送方式要回答**三个**问题：能不能送、多少钱、多久到。如果用函数，就需要三个字典：`FEES`、`AVAILABLE`、`ETAS`。加一种配送方式，要在三个字典里各登记一次，漏掉一个也不会报错。这又回到了本章开头的问题：同一种配送方式的知识，被拆散到了多个地方。用一个类把三个方法放在一起，“一种配送方式”就是一个完整的单位。

所以判断很简单：

- **策略只有一个操作**：用函数。需要配置时用 `partial` 或闭包。登记在字典里。
- **策略有几个必须一起变化的操作，或者有自己的配置数据**：用类（`Protocol` 描述接口，`dataclass` 保存配置）。

[第 28 章](../part-05/28-functions-as-design-tools.md)会更全面地讨论“函数作为设计工具”，包括什么时候闭包比类更合适。

## 小结

- 策略把一系列可以互相替换的做法分别封装成对象，使用它们的代码只依赖共同的接口。
- 策略真正解决的，往往不是“`if` 太多”，而是“同一套规则在多处重复、需要在运行时替换”。
- 策略对象可以带配置：同一种算法、不同参数，也可以作为不同的策略。
- 在 Python 里，只有一个操作的策略就是一个函数，配合字典和 `functools.partial` 就够了；有多个必须一起变化的操作时，再用类把它们放在一起。

## 练习

网店接入了一家第三方物流公司，它的运费要调用对方的接口查询，可能需要一两秒，偶尔还会失败。

1. 把它写成一个新的 `ShippingMethod`，会遇到什么问题？想想报价页要同时算所有配送方式的情况。
2. 如果查询失败了，`fee` 应该返回什么？抛出异常、返回一个默认值，还是让 `available` 返回 `False`？
3. 这个新策略和其他三个“纯计算”的策略，是不是还应该共用同一个接口？

**思路提示**：作为策略接入本身没有问题，这正是策略的好处：上下文不用改。但策略接口隐含了一个假设，即 `fee` 是一个很快、不会失败的计算。新策略打破了这个假设：报价页依次调用每个策略，一个慢的就会拖慢整页，一个失败的会让整页出错。可以让 `available` 在接口查询失败时返回 `False`，报价页就会自然地不显示它；结算页则要给出明确的提示。如果这类“慢的、会失败的”策略越来越多，就值得把接口拆开，或者在上下文里加上超时和错误处理。这说明，策略能否互相替换，不只取决于方法签名是否相同，还取决于它们的行为（速度、是否会失败）是否在同一个范围内。

完整代码：
- [`examples/ch17_shipping_v1.py`](../../examples/ch17_shipping_v1.py)：两份规则，费率不一致
- [`examples/ch17_strategy.py`](../../examples/ch17_strategy.py)：配送方式策略对象
- [`examples/ch17_pythonic.py`](../../examples/ch17_pythonic.py)：函数、字典与 `partial`

测试：[`tests/test_ch17_strategy.py`](../../tests/test_ch17_strategy.py)。
