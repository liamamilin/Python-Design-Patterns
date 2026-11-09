"""第 27 章：Python 角度。借用 ast 模块解析，但只允许白名单里的语法，并且自己求值，绝不调用 eval。"""
from __future__ import annotations

import ast
import operator

COMPARE = {
    ast.Eq: operator.eq, ast.NotEq: operator.ne,
    ast.GtE: operator.ge, ast.LtE: operator.le,
    ast.Gt: operator.gt, ast.Lt: operator.lt,
}


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


def evaluate(node: ast.AST, ctx: dict) -> object:
    match node:
        case ast.Expression(body):
            return evaluate(body, ctx)
        case ast.BoolOp(ast.And(), values):
            return all(evaluate(v, ctx) for v in values)
        case ast.BoolOp(ast.Or(), values):
            return any(evaluate(v, ctx) for v in values)
        case ast.UnaryOp(ast.Not(), operand):
            return not evaluate(operand, ctx)
        case ast.Compare(left, [op], [right]):
            return COMPARE[type(op)](evaluate(left, ctx), evaluate(right, ctx))
        case ast.Name(name):
            if name not in ctx:
                raise ValueError(f"没有这个字段：{name}")
            return ctx[name]
        case ast.Constant(value):
            return value
    raise ValueError(f"无法计算：{ast.dump(node)}")


if __name__ == "__main__":
    from examples.ch27_rules_v1 import students

    tree = check('年级 >= 2 and (学院 == "物理" or 社团 == "天文社")')
    print([s["姓名"] for s in students if evaluate(tree, s)])
    try:
        check('__import__("os").getpid() > 0')
    except ValueError as e:
        print("拒绝：", e)
