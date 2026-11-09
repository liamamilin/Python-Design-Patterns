"""第 05 章：Python 角度。类本身就是可以调用的工厂，直接把它当参数传进去。"""
from __future__ import annotations

from typing import Callable

from examples.ch05_factory_method_v1 import Task, tasks
from examples.ch05_simple_factory import HtmlRenderer, MarkdownRenderer, Renderer


def build_document(
    title: str,
    items: list[Task],
    make_renderer: Callable[[], Renderer] = MarkdownRenderer,
    keep: Callable[[Task], bool] = lambda task: True,
) -> str:
    renderer = make_renderer()
    lines = [renderer.title(title)]
    lines += [renderer.item(t) for t in items if keep(t)]
    return "\n".join(lines)


def weekly_notes(items: list[Task]) -> str:
    return build_document("周会纪要", items)


def client_report(items: list[Task]) -> str:
    return build_document("项目进度", items, HtmlRenderer, keep=lambda t: t.done)


if __name__ == "__main__":
    print(weekly_notes(tasks))
    print(client_report(tasks))
