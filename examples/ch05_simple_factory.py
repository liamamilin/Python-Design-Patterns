"""第 05 章：把“格式”变成对象，再用一个简单工厂函数集中选择。

简单工厂函数很常用，但它不是 GoF 23 种模式之一。
"""
from __future__ import annotations

import html
from typing import Protocol

from examples.ch05_factory_method_v1 import Task, tasks


class Renderer(Protocol):
    def title(self, text: str) -> str: ...

    def item(self, task: Task) -> str: ...


class MarkdownRenderer:
    def title(self, text: str) -> str:
        return f"# {text}"

    def item(self, task: Task) -> str:
        return f"- [{'x' if task.done else ' '}] {task.name}"


class HtmlRenderer:
    def title(self, text: str) -> str:
        return f"<h1>{html.escape(text)}</h1>"

    def item(self, task: Task) -> str:
        return f"<li>{'✔' if task.done else '…'} {html.escape(task.name)}</li>"


def make_renderer(fmt: str) -> Renderer:
    renderers = {"markdown": MarkdownRenderer, "html": HtmlRenderer}
    try:
        return renderers[fmt]()
    except KeyError:
        raise ValueError(f"未知格式: {fmt}") from None


def render(title: str, items: list[Task], fmt: str) -> str:
    renderer = make_renderer(fmt)
    return "\n".join([renderer.title(title)] + [renderer.item(t) for t in items])


if __name__ == "__main__":
    print(render("周会纪要", tasks, "markdown"))
