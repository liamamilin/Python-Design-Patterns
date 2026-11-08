"""第 05 章：GoF 工厂方法。

父类 Document 固定“生成文档”的流程，并留出 create_renderer 这个创建入口；
每种文档（子类）决定自己用哪种渲染器。新增文档类型时，不需要修改父类。
运行：python -m examples.ch05_factory_method
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from examples.ch05_factory_method_v1 import Task, tasks
from examples.ch05_simple_factory import HtmlRenderer, MarkdownRenderer, Renderer


class Document(ABC):
    title = "文档"

    def build(self, items: list[Task]) -> str:
        renderer = self.create_renderer()  # 工厂方法：由子类决定创建什么
        lines = [renderer.title(self.title)]
        lines += [renderer.item(t) for t in self.select(items)]
        return "\n".join(lines)

    def select(self, items: list[Task]) -> list[Task]:
        return items

    @abstractmethod
    def create_renderer(self) -> Renderer:
        """返回这种文档使用的渲染器。"""


class WeeklyNotes(Document):
    title = "周会纪要"

    def create_renderer(self) -> Renderer:
        return MarkdownRenderer()


class ClientReport(Document):
    title = "项目进度"

    def select(self, items: list[Task]) -> list[Task]:
        return [t for t in items if t.done]

    def create_renderer(self) -> Renderer:
        return HtmlRenderer()


# 另一位同事在自己的模块里新增文档类型，不需要修改 Document
class PlainTextRenderer:
    def title(self, text: str) -> str:
        return f"{text}\n{'=' * len(text) * 2}"

    def item(self, task: Task) -> str:
        return f"* {task.name}"


class ReleaseNotes(Document):
    title = "发布说明"

    def select(self, items: list[Task]) -> list[Task]:
        return [t for t in items if t.done]

    def create_renderer(self) -> Renderer:
        return PlainTextRenderer()


if __name__ == "__main__":
    for doc in (WeeklyNotes(), ClientReport(), ReleaseNotes()):
        print(doc.build(tasks))
        print()
