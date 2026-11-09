# 第 27 章　解释器 Interpreter

> 本章要回答：当规则需要由不写程序的人来编写和修改时，怎样设计一门足够小、足够安全的规则语言？为什么绝不能把用户写的规则交给 `eval`？

这是 GoF 23 种模式的最后一个。解释器模式是为一门**语言**中的每一条语法规则写一个类，再用这些类组成的树来计算结果。听起来像在写编译器，但它要解决的问题很日常：**让规则变成数据**，由使用者自己填写，而不是每次都找程序员改代码。

## 眼前的任务

一所大学的学生活动平台，每个活动都有报名资格。比如天文观测营：

```text
年级 >= 2 and (学院 == "物理" or 社团 == "天文社")
```

活动由各学院的老师在后台发布，资格规则也由老师自己填写。每个活动的规则都不一样，不可能每次都让程序员改代码。

## 不用模式的写法

规则看起来就是一个 Python 表达式，学生信息是一个字典。最省事的写法是：

```python
def eligible(rule: str, student: dict) -> bool:
    return bool(eval(rule, {}, student))  # 危险：rule 里的任何 Python 代码都会被执行
```

它确实能工作，三位学生里，周晴（物理学院、二年级）和高远（三年级、天文社）有资格。

**这是一个严重的安全漏洞。** `eval` 会执行字符串中的**任何** Python 代码。老师（或者盗用了老师账号的人）可以填写：

```text
__import__("os").getpid() > 0
```

`eval` 会照做：导入 `os` 模块，调用其中的函数，返回 `True`（测试 `test_eval_runs_arbitrary_code`）。示例只调用了一个无害的函数，但同样的方式可以读取服务器上的文件、删除数据、执行系统命令。

常见的“补救”是把 `eval` 的第二个参数设成 `{"__builtins__": {}}`，以为这样就禁掉了危险的函数。**这不安全。** 通过对象的属性链（比如 `().__class__.__bases__`）一步步找到危险的函数，是众所周知的绕过手法。Python 官方文档也明确表示，不应该用 `eval` 处理不可信的输入。

**规则：不可信的输入，永远不要交给 `eval` 或 `exec`。** 这里的“不可信”包括一切不是你自己写死在代码里的字符串：用户输入、数据库里的配置、文件内容、网络请求。

## 困难在哪里

我们真正需要的，远比“任意 Python 代码”少：

- 字段名（年级、学院、社团）；
- 数字和字符串；
- 六种比较：`==`、`!=`、`>=`、`<=`、`>`、`<`；
- `and`、`or`、`not` 和括号。

没有函数调用，没有属性访问，没有导入。如果有一门**只包含这些东西**的小语言，那么规则里根本**写不出**危险的操作，这比“执行任意代码，再设法禁止其中危险的部分”安全得多。

## 解释器：为语法的每条规则写一个类

GoF 对解释器的描述是：**给定一个语言，定义它的文法的一种表示，并定义一个解释器，这个解释器使用该表示来解释语言中的句子。**

先写出这门语言的语法（文法）。从上到下，优先级从低到高：

```text
expr := and ("or" and)*
and  := not ("and" not)*
not  := "not" not | cmp
cmp  := atom (比较符 atom)?
atom := 数字 | "字符串" | 字段名 | "(" expr ")"
```

`and` 写在 `or` 的下一层，所以 `and` 比 `or` 结合得更紧，`a or b and c` 的意思是 `a or (b and c)`，和 Python 一样（测试 `test_precedence_and_binds_tighter_than_or`）。

然后，**每种语法成分是一个类**，都有一个 `evaluate` 方法。字段从学生信息里取值，找不到就报错：

```python
@dataclass(frozen=True)
class Field:
    name: str

    def evaluate(self, ctx: dict[str, Value]) -> Value:
        if self.name not in ctx:
            raise RuleError(f"没有这个字段：{self.name}")
        return ctx[self.name]
```

比较先算出两边的值，再比较。字符串和数字比大小没有意义，直接报错，而不是让 Python 抛出一个让老师看不懂的 `TypeError`：

```python
@dataclass(frozen=True)
class Compare:
    op: str
    left: Expr
    right: Expr

    def evaluate(self, ctx: dict[str, Value]) -> bool:
        a, b = self.left.evaluate(ctx), self.right.evaluate(ctx)
        if self.op not in ("==", "!=") and type(a) is not type(b):
            raise RuleError(f"不能比较 {a!r} 和 {b!r} 的大小")
        return OPS[self.op](a, b)
```

`And` 让两边分别求值再组合：

```python
@dataclass(frozen=True)
class And:
    left: Expr
    right: Expr

    def evaluate(self, ctx: dict[str, Value]) -> bool:
        return bool(self.left.evaluate(ctx)) and bool(self.right.evaluate(ctx))
```

`Or`、`Not`、`Literal` 也都只有几行。一条规则就是由这些对象组成的一棵树。天文观测营的规则，解析后是这样的：

```text
And(
  Compare('>=', Field('年级'), Literal(2)),
  Or(
    Compare('==', Field('学院'), Literal('物理')),
    Compare('==', Field('社团'), Literal('天文社')),
  ),
)
```

在树的根节点调用 `evaluate(学生信息)`，它会递归地让每个子节点求值，最后得出 `True` 或 `False`。结果和 `eval` 版本完全一样：周晴和高远（测试 `test_same_answers`）。

### 解析：从文字到树

GoF 的解释器模式只讲“怎样用对象树表示和计算一个句子”，**不讲怎样把文字变成树**，那是解析器的工作。本例的解析器分两步：

1. **切分记号**：用一个正则表达式把规则切成数字、字符串、比较符、括号、关键字和字段名。任何不属于这几类的字符都会被拒绝。
2. **递归下降**：语法里的每一行对应解析器的一个方法，`expr` 调用 `and_`，`and_` 调用 `not_`，依此类推。

```python
    def expr(self) -> Expr:
        node = self.and_()
        while self.peek() == ("kw", "or"):
            self.i += 1
            node = Or(node, self.and_())
        return node
```

`__import__("os").getpid() > 0` 这样的规则在切分记号时就被拒绝了，因为语言里没有 `.` 这个符号；即使去掉点号，`__import__("os")` 也会因为“字段名后面跟着括号”不符合语法而被拒绝。即使有人设法让 `__import__` 作为一个字段名通过了解析，`Field.evaluate` 做的也只是在学生信息字典里查找这个名字，**这门语言里根本没有“调用”这个动作**（测试 `test_hostile_rules_are_rejected`）。

错误信息也是给老师看的：“这里应该是 )，实际是 结尾”“没有这个字段：专业”“不能比较 2 和 '二' 的大小”（测试 `test_friendly_errors`）。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 抽象表达式（AbstractExpression） | `Expr` 协议 | 声明 `evaluate` |
| 终结符表达式（TerminalExpression） | `Literal`、`Field` | 语法中不能再分解的部分 |
| 非终结符表达式（NonterminalExpression） | `Compare`、`And`、`Or`、`Not` | 由其他表达式组成，递归求值 |
| 上下文（Context） | 学生信息字典 | 求值时需要的外部数据 |
| 客户（Client） | `compile_rule` 及调用方 | 构造（解析出）表达式树并求值 |

## 代价与边界

- **你在设计一门语言。** 语法、优先级、错误信息、类型规则，全都要自己定义、自己测试。老师会问：“能不能写 `年级 在 [2, 3] 中`？”“能不能不区分大小写？”每一个“能不能”都是一次语言设计。
- **语法一复杂，类和解析器都会膨胀。** GoF 原书也指出，解释器模式适合**简单的**文法。如果规则语言需要变量、函数、循环，就应该使用专门的解析工具，或者换一种方案。
- **性能一般。** 每次求值都要遍历整棵树。对报名资格这样的规则，完全够用；对每秒要计算几百万次的规则，可能需要别的做法。
- **安全来自语言本身的“小”。** 解释器之所以安全，是因为语言里没有危险的操作。每给语言加一个功能，都要重新想一想它会不会被滥用，比如“允许调用几个函数”就要限定是哪几个、参数是什么。

**什么时候不该用**：规则的种类是固定的几种，只是参数不同。比如资格永远是“年级不低于 N，并且属于这几个学院之一”，那就做一个表单：一个年级下拉框，一组学院复选框。表单比任何语言都更容易使用，也更不容易出错。只有当规则的**结构**本身需要由使用者自由组合时，才需要一门语言。

## Python 角度：借用 `ast` 解析，但不要用 `eval` 执行

本例的规则语法恰好是 Python 表达式的一个子集。于是还有一种做法：用标准库的 `ast` 模块把规则解析成 Python 的语法树，然后**检查**树里只有允许的节点，最后**自己**遍历这棵树求值：

```python
def check(rule: str) -> ast.Expression:
    tree = ast.parse(rule, mode="eval")
    allowed = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
               ast.Compare, ast.Name, ast.Load, ast.Constant, *COMPARE)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(f"规则里不允许出现：{type(node).__name__}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, str)):
            raise ValueError(f"不支持的常量：{node.value!r}")
    return tree
```

`ast.parse` 只做解析，不执行任何东西。白名单里没有函数调用（`Call`）、属性访问（`Attribute`）、下标、推导式，`__import__(...)`、`().__class__` 等都会在检查时被拒绝（测试 `test_hostile_rules_are_rejected`）。求值用一个 `match` 语句，按节点类型分别处理（[第 26 章](26-visitor.md)讲过的写法）：

```python
        case ast.Compare(left, [op], [right]):
            return COMPARE[type(op)](evaluate(left, ctx), evaluate(right, ctx))
```

这种做法省去了自己写解析器，规则的写法和 Python 完全一致。代价是：

- 语法由 Python 决定，你只能**收窄**它，不能**改变**它。想支持中文的“且”“或”，或者自定义的运算符，就做不到。
- 白名单必须严格。漏掉一种危险节点，就是一个漏洞。**只列出允许的，不要列出禁止的**，本例的 `allowed` 就是白名单。
- Python 的一些语法细节会“漏”进你的语言。比如 `1 < 年级 < 3` 是合法的 Python 链式比较，本例的求值函数没有处理这种形式，会报错（测试 `test_chained_comparison_is_not_supported`）。每一种 Python 允许的写法，你都要决定支持还是拒绝。

两种做法如何选：

- **规则语法和 Python 表达式很接近，使用者是技术人员**：`ast` 加白名单，代码最少。
- **规则面向非技术人员，需要中文关键字、更友好的错误信息，或者和 Python 不同的语法**：自己定义语言，用本章的解释器类加一个小解析器。

无论哪一种，**都不要调用 `eval`**。

## 小结

- 当规则需要由非程序员编写，而且规则的结构需要自由组合时，可以设计一门小语言：为语法的每条规则写一个类，句子解析成由这些类组成的树，再递归求值。这就是解释器模式。
- 解释器模式只描述怎样表示和计算句子；把文字变成树，需要另外写解析器。
- 不可信的输入绝不能交给 `eval`/`exec`，限制 `__builtins__` 也不能使其安全。安全应该来自语言本身没有危险的操作。
- 在 Python 里，如果规则语法是 Python 表达式的子集，可以用 `ast.parse` 解析，再用严格的白名单检查和自己写的求值函数代替 `eval`。

## 练习

老师们提出了两个新需求：

- 支持“属于”：`学院 in ("物理", "天文")`；
- 支持中文关键字：`年级 >= 2 且 学院 == "物理"`。

1. 在自己定义语言的写法里，这两个需求分别要修改哪些部分：记号切分、语法、表达式类？
2. 在 `ast` 白名单的写法里，哪一个需求容易支持，哪一个做不到？
3. 支持 `in` 之后，要不要允许 `学院 in 社团`（右边是一个字段，而不是一组字面值）？这会带来什么问题？

**思路提示**：`in` 需要在记号里加上逗号、关键字 `in`，在语法里加一种“字面值列表”，再加一个 `In` 表达式类。中文关键字只需要在切分记号时把“且”“或”“非”映射成 `and`、`or`、`not`，语法和表达式类都不用改，这体现了“切分记号”和“语法”分开的好处。`ast` 的写法可以通过在白名单里加入 `ast.In` 和 `ast.Tuple` 来支持 `in`，但中文关键字根本无法通过 Python 的解析。第 3 问：右边是字段时，`in` 的含义变成了“子字符串”或“列表成员”，取决于字段的类型，语义变得模糊，错误也更难解释。规则语言的每一项能力都要想清楚它的含义和边界，**能力越少，越容易保证正确和安全**。

完整代码：
- [`examples/ch27_rules_v1.py`](../../examples/ch27_rules_v1.py)：用 `eval` 计算规则（危险，仅作反例）
- [`examples/ch27_interpreter.py`](../../examples/ch27_interpreter.py)：表达式类、记号切分与递归下降解析器
- [`examples/ch27_pythonic.py`](../../examples/ch27_pythonic.py)：`ast` 解析、白名单检查与自定义求值

测试：[`tests/test_ch27_interpreter.py`](../../tests/test_ch27_interpreter.py)。
