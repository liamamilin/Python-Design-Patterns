# 第 30 章　Python 装饰器、上下文管理器和生成器

> 本章要回答：Python 的 `@` 装饰器、`with` 语句和 `yield`，分别让哪些经典模式变了样子？怎样区分“用了某种语法”和“用了某个模式”？

前面的模式章里，这三种语言机制已经多次出现：[第 13 章](../part-03/13-decorator.md)用 `@` 写函数装饰器，[第 23 章](../part-04/23-iterator.md)用生成器写迭代器。这一章用一个小脚本把三者放在一起，说明它们各自承担了哪种经典模式的工作，以及在哪里不能混为一谈。

## 眼前的任务

旅行回来，相机里的照片名字是 `IMG_0101.jpg`、`IMG_0102.jpg`……想批量改成 `西湖_001.jpg`、`西湖_002.jpg`。

## 不用这些机制的写法

一个循环做完所有事：

```python
def rename_all(folder: Path, prefix: str) -> list[str]:
    done = []
    for i, path in enumerate(sorted(folder.glob("*.jpg")), 1):
        target = path.with_name(f"{prefix}_{i:03d}.jpg")
        if target.exists():
            raise FileExistsError(target.name)
        path.rename(target)
        done.append(target.name)
    return done
```

大多数时候，**这就够了**。

问题出现在中途出错时。文件夹里已经有一张上次整理好的 `西湖_002.jpg`，脚本把第一张改成 `西湖_001.jpg`，处理第二张时发现目标已存在，抛出异常。文件夹停在了一半改过、一半没改的状态（测试 `test_failure_leaves_half_renamed_folder`）。用户得手动去理清哪些改过了。

后来还有别的需求：命名方式要能选（只用序号、保留原名加序号……）；先列出改名计划给用户确认，再执行。

## 上下文管理器：成对的“准备”和“收尾”

“要么全改，要么全不改”需要两件事：执行过程中记下改了哪些；出错时按相反顺序改回去。这是一个“准备 → 执行用户的代码 → 收尾”的结构，收尾的方式取决于执行是否成功。

在经典的面向对象设计里，这种结构常用[第 21 章](../part-04/21-template-method.md)的模板方法实现：父类的 `run()` 先调用 `setup()`，再调用子类的 `body()`，最后调用 `teardown()`。Python 把这个结构做进了语言：`with` 语句。

用标准库 `contextlib.contextmanager`，一个生成器函数就能写出上下文管理器：`yield` 之前是准备，`yield` 交出的值给 `with ... as` 使用，`yield` 之后（或者异常处理里）是收尾：

```python
@contextmanager
def all_or_nothing() -> Iterator[Callable[[Path, Path], None]]:
    """进入时准备好一个“改名”函数；离开时如果出了错，按相反顺序全部改回去。"""
    done: list[tuple[Path, Path]] = []

    def rename(src: Path, dst: Path) -> None:
        if dst.exists():
            raise FileExistsError(dst.name)
        src.rename(dst)
        done.append((src, dst))

    try:
        yield rename
    except BaseException:
        for src, dst in reversed(done):
            dst.rename(src)
        raise
```

使用它的代码只需要把改名操作放进 `with` 块：

```python
def rename_folder(folder: Path, rule_name: str, prefix: str = "") -> list[str]:
    with all_or_nothing() as rename:
        steps = list(plan(photos(folder), RULES[rule_name], prefix))
        for src, dst in steps:
            rename(src, dst)
    return [dst.name for _, dst in steps]
```

同样的文件夹，第二张改名失败时，第一张被改回了原名，文件夹恢复原状，异常照常抛出（测试 `test_failure_rolls_everything_back`）。

同样的上下文管理器也可以写成类，实现 `__enter__` 和 `__exit__` 两个方法：

```python
    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            for src, dst in reversed(self.done):
                dst.rename(src)
        return False  # 不吞掉异常
```

`__exit__` 返回 `False` 表示“异常继续往外传”。返回 `True` 会把异常吞掉，除非确有理由，否则不要这样做。两种写法行为相同（测试 `test_class_based_context_manager_behaves_the_same`）。准备和收尾的逻辑简单时，用 `@contextmanager`；上下文管理器本身还需要提供方法、保存较多状态时，写成类。

和模板方法相比，上下文管理器有一个重要的不同：**它不需要继承。** 任何代码块都可以放进 `with` 里，准备和收尾的逻辑与具体要做的事完全分开。文件的 `with open(...)`、锁的 `with lock:`、数据库事务的 `with conn:`，都是这种结构。

**注意：** 这个“回滚”只覆盖本程序自己做的改名。如果另一个程序同时在动这个文件夹，或者回滚时又出了错（比如磁盘满了），它保证不了一致性。它是一个实用的“尽力而为”，不是数据库那样的事务。

## 生成器：按需产出的迭代器

先列出改名计划，再执行。“计划”是一串 `(原路径, 新路径)`，用生成器逐个产出：

```python
def photos(folder: Path) -> Iterator[Path]:
    yield from sorted(p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))


def plan(paths: Iterator[Path], name_rule: NameRule, prefix: str = "") -> Iterator[tuple[Path, Path]]:
    for i, path in enumerate(paths, 1):
        target = path.with_name(prefix + name_rule(i, path))
        if target != path:
            yield path, target
```

[第 23 章](../part-04/23-iterator.md)讲过，生成器就是 Python 版的迭代器模式。这里还体现了它的另一个用途：**管道**。`photos` 产出照片，`plan` 消费照片、产出计划，每一级只在下一级需要时才工作。测试 `test_plan_is_lazy` 显示，只取第一项计划时，上游只产出了一张照片。

在 `rename_folder` 里，计划被 `list(...)` 一次性取完。这是有意的：改名会改变文件夹的内容，如果边遍历文件夹边改名，遍历可能看到刚改过名的文件。**先把计划算完，再执行**，避免了遍历和修改互相干扰，这和[第 18 章](../part-04/18-observer.md)“遍历订阅者的快照”是同一个道理。

## 装饰器：登记，而不是包装

命名方式要能选。每种方式是一个函数，接收序号和原路径，返回新名字。用一个装饰器把它们**登记**到一张表里：

```python
def rule(name: str) -> Callable[[NameRule], NameRule]:
    """登记用的装饰器：把函数放进 RULES，原样返回它。这不是 GoF 的装饰器模式。"""

    def register(func: NameRule) -> NameRule:
        RULES[name] = func
        return func

    return register


@rule("序号")
def numbered(i: int, path: Path) -> str:
    return f"{i:03d}{path.suffix}"
```

定义函数的同时就完成了登记，不需要在别处维护一张“名字 → 函数”的表，也不会出现“写了新规则却忘了登记”。用户选择命名方式时，用 `RULES[rule_name]` 查找即可，这就是[第 05 章](../part-02/05-factory-method.md)的简单工厂，只是登记的过程由装饰器自动完成。

注意注释里的那句话：**这不是 GoF 的装饰器模式。** `register` 没有包装任何东西，它原样返回了传入的函数（测试 `test_rules_registered_by_decorator` 检查了 `RULES["序号"] is numbered`）。它只是借用了 `@` 语法“在定义时执行一段代码”的能力。[第 13 章](../part-03/13-decorator.md)的 `@masking` 才是包装：返回一个新函数，在调用原函数前后加上额外的行为。

## 语法和模式的对应

| 经典模式 | Python 中常见的形态 | 要注意的区别 |
|---|---|---|
| 迭代器（[第 23 章](../part-04/23-iterator.md)） | 生成器函数、生成器表达式 | 生成器只能遍历一次 |
| 模板方法中的“准备／收尾”（[第 21 章](../part-04/21-template-method.md)） | 上下文管理器、`with` 语句 | 不需要继承；收尾在出错时也会执行 |
| 装饰器（[第 13 章](../part-03/13-decorator.md)） | 用 `@` 包装函数的高阶函数 | `@` 在定义时执行一次，包装永久生效；按次组合时直接调用包装函数 |
| 简单工厂的登记表（[第 05 章](../part-02/05-factory-method.md)） | 用 `@` 登记到字典 | 这是登记，不是包装，和装饰器模式无关 |
| 命令（[第 19 章](../part-04/19-command.md)）中的“延后执行” | `functools.partial`、`lambda` | 需要撤销时，单个函数就不够了 |

这张表说明的是：**同一个设计思想，在 Python 里常常有比类层次更轻的表达方式。** 但反过来，看到 `@` 不等于看到了装饰器模式，看到 `with` 也不等于用了模板方法。判断的依据始终是：这段代码在解决什么问题。

## 小结

- 上下文管理器把“准备—执行—收尾”的结构做进了语言，承担了模板方法中准备和收尾的部分，而且不需要继承；收尾逻辑在出错时也会执行。
- 生成器是 Python 版的迭代器，还可以组成按需工作的管道。会修改数据源的操作，先把计划算完，再执行。
- `@` 语法只是“在定义时用一个函数处理另一个函数”。包装函数是装饰器思想的体现；登记函数则是简单工厂的登记表，和装饰器模式无关。
- 判断用了什么模式，看代码解决的问题，而不是看用了什么语法。

## 练习

用户希望在真正改名之前看到计划，确认后再执行；还希望有一个 `--dry-run` 选项，只打印计划，不改任何文件。

1. 用本章的 `plan` 生成器，怎样实现“先显示，再确认”？如果用户确认之前文件夹被修改了，会发生什么？
2. `--dry-run` 应该在哪里实现：给 `all_or_nothing` 加一个参数，还是写另一个上下文管理器，或者干脆不进入 `with`？
3. 回顾[第 06 章](../part-02/06-abstract-factory.md)的“演练”问题。本章的情况和[第 06 章](../part-02/06-abstract-factory.md)有什么相同和不同？

**思路提示**：先 `steps = list(plan(...))`，显示 `steps`，用户确认后再在 `with all_or_nothing()` 里执行同一份 `steps`。如果确认之前文件夹被改了，执行时 `rename` 里的 `exists()` 检查和回滚能防止最坏的情况，但计划可能已经过时，比较稳妥的做法是执行前重新生成计划并与显示过的计划比较。`--dry-run` 最简单的实现是只生成并打印计划，根本不进入 `with` 块，因为这里只有一个会产生副作用的部件（改名）。[第 06 章](../part-02/06-abstract-factory.md)的演练需要同时替换两个部件（发送和记录），所以才需要“家族”；部件只有一个时，一个 `if` 就够了。

完整代码：
- [`examples/ch30_rename_v1.py`](../../examples/ch30_rename_v1.py)：一个循环完成所有事（中途出错会留下半成品）
- [`examples/ch30_language.py`](../../examples/ch30_language.py)：登记装饰器、生成器管道、两种写法的上下文管理器

测试：[`tests/test_ch30_language.py`](../../tests/test_ch30_language.py)。
