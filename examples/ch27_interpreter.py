"""第 27 章：解释器。为一门很小的规则语言定义语法，每条语法规则对应一个类。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

Value = int | str


class Expr(Protocol):
    def evaluate(self, ctx: dict[str, Value]) -> Value | bool: ...


@dataclass(frozen=True)
class Literal:
    value: Value

    def evaluate(self, ctx: dict[str, Value]) -> Value:
        return self.value


@dataclass(frozen=True)
class Field:
    name: str

    def evaluate(self, ctx: dict[str, Value]) -> Value:
        if self.name not in ctx:
            raise RuleError(f"没有这个字段：{self.name}")
        return ctx[self.name]


OPS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
}


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


@dataclass(frozen=True)
class And:
    left: Expr
    right: Expr

    def evaluate(self, ctx: dict[str, Value]) -> bool:
        return bool(self.left.evaluate(ctx)) and bool(self.right.evaluate(ctx))


@dataclass(frozen=True)
class Or:
    left: Expr
    right: Expr

    def evaluate(self, ctx: dict[str, Value]) -> bool:
        return bool(self.left.evaluate(ctx)) or bool(self.right.evaluate(ctx))


@dataclass(frozen=True)
class Not:
    inner: Expr

    def evaluate(self, ctx: dict[str, Value]) -> bool:
        return not self.inner.evaluate(ctx)


class RuleError(ValueError):
    pass


TOKEN = re.compile(r'\s*(?:(\d+)|"([^"]*)"|(==|!=|>=|<=|>|<|\(|\))|(\w+))')


def tokenize(text: str) -> list[tuple[str, str]]:
    tokens, pos = [], 0
    text = text.rstrip()
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            raise RuleError(f"第 {pos + 1} 个字符附近无法识别：{text[pos:pos + 10]!r}")
        number, string, op, word = m.groups()
        if number is not None:
            tokens.append(("num", number))
        elif string is not None:
            tokens.append(("str", string))
        elif op is not None:
            tokens.append(("op", op))
        else:
            tokens.append(("kw" if word in ("and", "or", "not") else "name", word))
        pos = m.end()
    return tokens


class Parser:
    """按语法规则把记号组装成表达式树：
    expr := and ("or" and)*
    and  := not ("and" not)*
    not  := "not" not | cmp
    cmp  := atom (比较符 atom)?
    atom := 数字 | "字符串" | 字段名 | "(" expr ")"
    """

    def __init__(self, text: str) -> None:
        self.tokens = tokenize(text)
        self.i = 0

    def parse(self) -> Expr:
        expr = self.expr()
        if self.i != len(self.tokens):
            raise RuleError(f"多余的内容：{self.tokens[self.i][1]}")
        return expr

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self, kind: str, value: str | None = None) -> str:
        tok = self.peek()
        if tok is None or tok[0] != kind or (value is not None and tok[1] != value):
            raise RuleError(f"这里应该是 {value or kind}，实际是 {tok[1] if tok else '结尾'}")
        self.i += 1
        return tok[1]

    def expr(self) -> Expr:
        node = self.and_()
        while self.peek() == ("kw", "or"):
            self.i += 1
            node = Or(node, self.and_())
        return node

    def and_(self) -> Expr:
        node = self.not_()
        while self.peek() == ("kw", "and"):
            self.i += 1
            node = And(node, self.not_())
        return node

    def not_(self) -> Expr:
        if self.peek() == ("kw", "not"):
            self.i += 1
            return Not(self.not_())
        return self.cmp()

    def cmp(self) -> Expr:
        left = self.atom()
        tok = self.peek()
        if tok and tok[0] == "op" and tok[1] in OPS:
            self.i += 1
            return Compare(tok[1], left, self.atom())
        return left

    def atom(self) -> Expr:
        tok = self.peek()
        if tok is None:
            raise RuleError("规则不完整")
        kind, value = tok
        if kind == "num":
            self.i += 1
            return Literal(int(value))
        if kind == "str":
            self.i += 1
            return Literal(value)
        if kind == "name":
            self.i += 1
            return Field(value)
        self.take("op", "(")
        inner = self.expr()
        self.take("op", ")")
        return inner


def compile_rule(text: str) -> Expr:
    return Parser(text).parse()


if __name__ == "__main__":
    from examples.ch27_rules_v1 import students

    rule = compile_rule('年级 >= 2 and (学院 == "物理" or 社团 == "天文社")')
    print(rule)
    print([s["姓名"] for s in students if rule.evaluate(s)])
    try:
        compile_rule('__import__("os").getpid() > 0')
    except RuleError as e:
        print("拒绝：", e)
