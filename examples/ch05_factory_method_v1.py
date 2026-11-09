"""第 05 章：没有任何模式的第一版。

团队工具把任务清单生成文档。先只有 Markdown，后来客户要 HTML，加一个参数即可。
"""
from __future__ import annotations

import html
from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    name: str
    done: bool


tasks = [
    Task("登录页改版", True),
    Task("修复导出乱码", False),
    Task("接入短信验证码", True),
]


def render(title: str, items: list[Task], fmt: str = "markdown") -> str:
    if fmt == "markdown":
        lines = [f"# {title}"]
        lines += [f"- [{'x' if t.done else ' '}] {t.name}" for t in items]
    elif fmt == "html":
        lines = [f"<h1>{html.escape(title)}</h1>"]
        lines += [f"<li>{'✔' if t.done else '…'} {html.escape(t.name)}</li>" for t in items]
    else:
        raise ValueError(f"未知格式: {fmt}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render("周会纪要", tasks))
    print(render("项目进度", [t for t in tasks if t.done], "html"))
