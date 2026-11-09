"""把 book/ 下的 Markdown 正文生成在线阅读的网页，写到 docs/book/。

book/*.md 是唯一的源文件，docs/book/ 下的网页全部由本脚本生成，不要手工修改。
只用标准库，只支持本书用到的那部分 Markdown：标题、段落、引用、列表、表格、
代码块（python / text / mermaid）、行内代码、链接、粗体和斜体。

用法（在仓库根目录）：
    python tools/build_site.py          # 重新生成 docs/book/
    python tools/build_site.py --check  # 只检查 docs/book/ 是否和正文一致，不写文件
"""
from __future__ import annotations

import html
import json
import posixpath
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book"
OUT = ROOT / "docs" / "book"
ASSETS = Path(__file__).resolve().parent / "site_assets"
REPO = "https://github.com/liamamilin/Python-Design-Patterns"
BLOB = REPO + "/blob/main/"
BOOK_TITLE = "Python 设计模式：从问题到方案"
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"


# ---------------------------------------------------------------- 行内元素

CODE_SPAN = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<![*\w])\*(?![\s*])([^*\n]+?)(?<!\s)\*(?![*\w])")


def protect_code(text: str) -> tuple[str, list[str]]:
    """把行内代码换成占位符，免得里面的 * | [ ] 被当成标记。"""
    spans: list[str] = []

    def keep(m: re.Match[str]) -> str:
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    return CODE_SPAN.sub(keep, text), spans


def restore_code(text: str, spans: list[str]) -> str:
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{html.escape(spans[int(m.group(1))], quote=False)}</code>", text)


def inline(text: str, page: "Page") -> str:
    text, spans = protect_code(text)
    text = html.escape(text, quote=False)

    def link(m: re.Match[str]) -> str:
        href = page.resolve_link(html.unescape(m.group(2)))
        external = href.startswith(("http://", "https://"))
        attrs = ' target="_blank" rel="noopener"' if external else ""
        return f'<a href="{html.escape(href)}"{attrs}>{m.group(1)}</a>'

    text = LINK.sub(link, text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = ITALIC.sub(r"<em>\1</em>", text)
    return restore_code(text, spans)


def plain(text: str) -> str:
    """去掉标记，只留下文字（用于标题锚点、搜索索引）。"""
    text = CODE_SPAN.sub(r"\1", text)
    text = LINK.sub(r"\1", text)
    return text.replace("**", "").replace("*", "")


# ---------------------------------------------------------------- 代码高亮

PY_KEYWORDS = (
    "False None True and as assert async await break case class continue def del elif else except "
    "finally for from global if import in is lambda match nonlocal not or pass raise return try while "
    "with yield"
).split()
PY_BUILTINS = (
    "abs all any bool bytes callable dict dir enumerate filter float frozenset getattr hasattr hash "
    "id int isinstance issubclass iter len list map max min next object open print property range repr "
    "reversed round set setattr sorted staticmethod classmethod str sum super tuple type vars zip "
    "Exception ValueError TypeError KeyError AttributeError RuntimeError IndexError NotImplementedError "
    "StopIteration ExceptionGroup PermissionError FileNotFoundError OSError ZeroDivisionError self cls"
).split()
PY_TOKEN = re.compile(
    r"""(?P<str>(?:[rRbBuUfF]{1,2})?(?:'''[\s\S]*?(?:'''|$)|\"\"\"[\s\S]*?(?:\"\"\"|$)|'(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*"))"""
    r"|(?P<com>\#[^\n]*)"
    r"|(?P<deco>^[ \t]*@[\w.]+)"
    r"|(?P<num>\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<name>\b[A-Za-z_]\w*\b)",
    re.M,
)


def highlight_python(code: str) -> str:
    out: list[str] = []
    pos = 0
    after_def = False
    for m in PY_TOKEN.finditer(code):
        out.append(html.escape(code[pos:m.start()], quote=False))
        pos = m.end()
        word = m.group()
        kind = m.lastgroup
        cls = ""
        if kind == "str":
            cls = "s"
        elif kind == "com":
            cls = "c"
        elif kind == "deco":
            cls = "d"
        elif kind == "num":
            cls = "n"
        elif after_def:
            cls = "f"
        elif word in PY_KEYWORDS:
            cls = "k"
        elif word in PY_BUILTINS:
            cls = "b"
        after_def = kind == "name" and word in ("def", "class")
        text = html.escape(word, quote=False)
        out.append(f'<span class="{cls}">{text}</span>' if cls else text)
    out.append(html.escape(code[pos:], quote=False))
    return "".join(out)


# ---------------------------------------------------------------- 块级元素

@dataclass
class Heading:
    level: int
    text: str
    anchor: str


@dataclass
class Page:
    src: Path                    # book/ 下的 .md
    title: str = ""
    part: str = ""
    headings: list[Heading] = field(default_factory=list)
    sections: list[tuple[str, str, str]] = field(default_factory=list)  # (锚点, 标题, 文字)
    has_mermaid: bool = False

    @property
    def rel(self) -> str:
        """相对 book/ 的输出路径，例如 part-04/20-state.html。"""
        rel = self.src.relative_to(BOOK).as_posix()
        return "index.html" if rel == "README.md" else rel[:-3] + ".html"

    @property
    def depth(self) -> int:
        return self.rel.count("/")

    def resolve_link(self, target: str) -> str:
        if target.startswith(("http://", "https://", "#")):
            return target
        path, _, frag = target.partition("#")
        frag = "#" + frag if frag else ""
        here = posixpath.dirname(self.src.relative_to(ROOT).as_posix())
        dest = posixpath.normpath(posixpath.join(here, path))
        if dest.startswith("book/") and dest.endswith(".md"):
            rel = posixpath.relpath(dest, here)
            rel = rel[:-len("README.md")] + "index.html" if rel.endswith("README.md") else rel[:-3] + ".html"
            return rel + frag
        return BLOB + dest + frag


TABLE_ROW = re.compile(r"^\|.*\|\s*$")
TABLE_RULE = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")
UL_ITEM = re.compile(r"^[-*] (.*)$")
OL_ITEM = re.compile(r"^(\d+)\. (.*)$")


def split_row(line: str) -> list[str]:
    masked, spans = protect_code(line.strip().strip("|"))
    cells = [c.strip() for c in masked.split("|")]
    return [re.sub(r"\x00(\d+)\x00", lambda m: "`" + spans[int(m.group(1))] + "`", c) for c in cells]


def slug(text: str, used: set[str]) -> str:
    base = re.sub(r"[^\w一-鿿-]+", "-", plain(text)).strip("-").lower() or "section"
    anchor, n = base, 2
    while anchor in used:
        anchor, n = f"{base}-{n}", n + 1
    used.add(anchor)
    return anchor


def render(md: str, page: Page) -> str:
    lines = md.splitlines()
    out: list[str] = []
    used: set[str] = set()
    i = 0
    section = ["", page.title, []]  # 当前小节：锚点、标题、文字

    def flush_section() -> None:
        text = " ".join(section[2]).strip()
        if text:
            page.sections.append((section[0], section[1], text))

    def note(text: str) -> None:
        section[2].append(plain(text))

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        if line.startswith("```"):
            lang = line[3:].strip()
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            code = "\n".join(lines[i + 1:j])
            if lang == "mermaid":
                page.has_mermaid = True
                out.append(f'<figure class="diagram"><pre class="mermaid">{html.escape(code, quote=False)}</pre></figure>')
            else:
                body = highlight_python(code) if lang == "python" else html.escape(code, quote=False)
                # text 块里有输出、数据、命令，也有伪代码，所以不加标签
                label = f' data-lang="{ {"python": "Python"}.get(lang, lang)}"' if lang and lang != "text" else ""
                out.append(f'<div class="code"{label}><pre><code>{body}</code></pre></div>')
                section[2].append(code if lang == "python" else "")
            i = j + 1
            continue

        m = re.match(r"^(#{1,4}) (.*)$", line)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 1:
                out.append(f"<h1>{inline(text, page)}</h1>")
            else:
                anchor = slug(text, used)
                page.headings.append(Heading(level, plain(text), anchor))
                if level == 2:
                    flush_section()
                    section[:] = [anchor, plain(text), []]
                out.append(
                    f'<h{level} id="{anchor}">{inline(text, page)}'
                    f'<a class="anchor" href="#{anchor}" aria-label="本节链接">#</a></h{level}>'
                )
            i += 1
            continue

        if line.startswith(">"):
            quoted = []
            while i < len(lines) and lines[i].startswith(">"):
                quoted.append(lines[i][1:].strip())
                i += 1
            paras = [f"<p>{inline(q, page)}</p>" for q in quoted if q]
            for q in quoted:
                note(q)
            out.append("<blockquote>" + "".join(paras) + "</blockquote>")
            continue

        if TABLE_ROW.match(line) and i + 1 < len(lines) and TABLE_RULE.match(lines[i + 1]):
            head = split_row(line)
            rows = []
            i += 2
            while i < len(lines) and TABLE_ROW.match(lines[i]):
                rows.append(split_row(lines[i]))
                i += 1
            thead = "".join(f"<th>{inline(c, page)}</th>" for c in head)
            labels = [html.escape(plain(h)) for h in head]
            tbody = "".join(
                "<tr>"
                + "".join(f'<td data-label="{labels[k] if k < len(labels) else ""}">{inline(c, page)}</td>' for k, c in enumerate(r))
                + "</tr>"
                for r in rows
            )
            for r in [head, *rows]:
                note(" ".join(r))
            out.append(f'<div class="table"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>')
            continue

        if UL_ITEM.match(line) or OL_ITEM.match(line):
            ordered = bool(OL_ITEM.match(line))
            pattern = OL_ITEM if ordered else UL_ITEM
            items: list[str] = []
            start = int(OL_ITEM.match(line).group(1)) if ordered else 1
            while i < len(lines):
                m = pattern.match(lines[i])
                if not m:
                    break
                text = m.group(2) if ordered else m.group(1)
                items.append(f"<li>{inline(text, page)}</li>")
                note(text)
                i += 1
            if ordered:
                attr = f' start="{start}"' if start != 1 else ""
                out.append(f"<ol{attr}>" + "".join(items) + "</ol>")
            else:
                out.append("<ul>" + "".join(items) + "</ul>")
            continue

        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(```|#|>|\||[-*] |\d+\. )", lines[i]):
            para.append(lines[i].strip())
            i += 1
        text = "".join(para)
        note(text)
        out.append(f"<p>{inline(text, page)}</p>")

    flush_section()
    return "\n".join(out)


# ---------------------------------------------------------------- 目录与页面

@dataclass
class TocPart:
    name: str
    pages: list[tuple[str, str]]  # (相对 book/ 的 .md 路径, 显示名称)


def read_toc() -> list[TocPart]:
    parts: list[TocPart] = []
    in_toc = False
    for line in (BOOK / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_toc = line.strip() == "## 目录"
            continue
        if not in_toc:
            continue
        if line.startswith("### "):
            parts.append(TocPart(line[4:].strip(), []))
        m = re.match(r"^- \[(.+?)\]\((.+?\.md)\)", line)
        if m and parts:
            parts[-1].pages.append((m.group(2), m.group(1)))
    return parts


def reading_order(toc: list[TocPart]) -> list[tuple[str, str, str]]:
    """全书阅读顺序：(md 路径, 显示名称, 所属部分)。"""
    order = [("preface.md", "前言", "")]
    for part in toc:
        order += [(path, name, part.name) for path, name in part.pages]
    order.append(("glossary.md", "术语表", ""))
    return order


def sidebar(current: Page, toc: list[TocPart]) -> str:
    up = "../" * current.depth

    def item(md: str, label: str) -> str:
        href = up + ("index.html" if md == "README.md" else md[:-3] + ".html")
        here = ' aria-current="page"' if current.src == BOOK / md else ""
        m = re.match(r"^(\d\d) (.*)$", label)
        if m:
            label_html = f'<span class="no">{m.group(1)}</span><span>{html.escape(m.group(2))}</span>'
        else:
            label_html = f"<span>{html.escape(label)}</span>"
        return f'<li><a href="{href}"{here}>{label_html}</a></li>'

    parts = [
        '<ul class="toc-top">'
        + item("README.md", "目录与说明")
        + item("preface.md", "前言")
        + "</ul>"
    ]
    for part in toc:
        name, _, rest = part.name.partition(" · ")
        has_current = any(current.src == BOOK / md for md, _ in part.pages)
        parts.append(
            f'<details class="toc-part"{" open" if has_current or current.rel == "index.html" else ""}>'
            f'<summary><span class="pn">{html.escape(name)}</span>{html.escape(rest)}</summary>'
            f'<ul>{"".join(item(md, label) for md, label in part.pages)}</ul></details>'
        )
    parts.append('<ul class="toc-top">' + item("glossary.md", "术语表") + "</ul>")
    return "".join(parts)


def page_toc(page: Page) -> str:
    items = [h for h in page.headings if h.level == 2]
    if len(items) < 3:
        return ""
    links = "".join(f'<li><a href="#{h.anchor}">{html.escape(h.text)}</a></li>' for h in items)
    return f'<nav class="pagetoc" aria-label="本页内容"><p>本页内容</p><ul>{links}</ul></nav>'


def pager(page: Page, order: list[tuple[str, str, str]]) -> str:
    paths = [md for md, _, _ in order]
    here = page.src.relative_to(BOOK).as_posix()
    if here not in paths:
        first = order[0]
        up = "../" * page.depth
        return (
            '<nav class="pager"><span></span>'
            f'<a class="next" href="{up}{first[0][:-3]}.html"><small>开始阅读</small>{html.escape(first[1])}</a></nav>'
        )
    idx = paths.index(here)
    up = "../" * page.depth

    def card(n: int, cls: str, label: str) -> str:
        if not 0 <= n < len(order):
            return "<span></span>"
        md, name, _ = order[n]
        return f'<a class="{cls}" href="{up}{md[:-3]}.html"><small>{label}</small>{html.escape(name)}</a>'

    return f'<nav class="pager">{card(idx - 1, "prev", "上一篇")}{card(idx + 1, "next", "下一篇")}</nav>'


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#16212e">
<link rel="icon" href="{up}assets/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{up}assets/book.css">
<script>try{{var t=localStorage.getItem("dp-theme");if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
</head>
<body data-root="{up}">
<a class="skip" href="#content">跳到正文</a>
<header class="bar">
  <button class="menu" type="button" aria-controls="sidebar" aria-expanded="false" aria-label="打开目录">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
  </button>
  <a class="brand" href="{up}index.html">Python 设计模式<span>：从问题到方案</span></a>
  <a class="guide" href="{up}../index.html">导读</a>
  <button class="theme" type="button" aria-label="切换深浅色">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z"/></svg>
  </button>
</header>
<div class="layout">
  <aside class="sidebar" id="sidebar">
    <div class="search">
      <input type="search" id="q" placeholder="搜索全书" autocomplete="off" aria-label="搜索全书">
      <div class="hits" id="hits" hidden></div>
    </div>
    <nav aria-label="全书目录">{sidebar}</nav>
  </aside>
  <div class="scrim" hidden></div>
  <main id="content">
    <article class="prose">
{kicker}{body}
    </article>
{pager}
    <footer class="foot">《{book}》 · 代码只用 Python 标准库，可在 <a href="{repo}" target="_blank" rel="noopener">GitHub 仓库</a>中运行全部示例和测试 · <a href="{source}" target="_blank" rel="noopener">查看本页源文件</a></footer>
  </main>
  {pagetoc}
</div>
<script src="{up}assets/book.js"></script>
{mermaid}</body>
</html>
"""


def build(out: Path) -> list[Path]:
    toc = read_toc()
    order = reading_order(toc)
    part_of = {md: part for md, _, part in order}
    pages = [Page(BOOK / "README.md"), *(Page(BOOK / md) for md, _, _ in order)]
    written: list[Path] = []
    index: list[dict[str, str]] = []

    for page in pages:
        md = page.src.read_text(encoding="utf-8")
        first = md.splitlines()[0]
        page.title = plain(first.lstrip("# ").strip()).replace("　", " ")
        page.part = part_of.get(page.src.relative_to(BOOK).as_posix(), "")
        body = render(md, page)
        up = "../" * page.depth
        description = next((t for _, _, t in page.sections if t), "")[:120]
        kicker = f'<p class="kicker">{html.escape(page.part)}</p>\n' if page.part else ""
        mermaid = ""
        if page.has_mermaid:
            mermaid = f'<script src="{MERMAID}"></script>\n<script src="{up}assets/diagrams.js"></script>\n'
        title = BOOK_TITLE if page.rel == "index.html" else f"{page.title} · {BOOK_TITLE}"
        text = TEMPLATE.format(
            title=html.escape(title),
            description=html.escape(description),
            up=up,
            sidebar=sidebar(page, toc),
            kicker=kicker,
            body=body,
            pager=pager(page, order),
            book=BOOK_TITLE,
            repo=REPO,
            source=BLOB + page.src.relative_to(ROOT).as_posix(),
            pagetoc=page_toc(page),
            mermaid=mermaid,
        )
        target = out / page.rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        written.append(target)
        for anchor, heading, words in page.sections:
            index.append({"u": page.rel + (f"#{anchor}" if anchor else ""), "p": page.title, "h": heading, "x": words})

    (out / "search.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    written.append(out / "search.json")
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for asset in sorted(ASSETS.iterdir()):
        shutil.copyfile(asset, assets / asset.name)
        written.append(assets / asset.name)
    return written


def snapshot(folder: Path) -> dict[str, bytes]:
    if not folder.exists():
        return {}
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def stale_files() -> list[str]:
    """返回 docs/book/ 中和正文不一致的文件；空列表表示网页是最新的。"""
    with tempfile.TemporaryDirectory() as tmp:
        build(Path(tmp))
        fresh = snapshot(Path(tmp))
    current = snapshot(OUT)
    return sorted(name for name in fresh.keys() | current.keys() if fresh.get(name) != current.get(name))


def main(argv: list[str]) -> int:
    if "--check" in argv:
        stale = stale_files()
        for name in stale:
            print(f"docs/book/{name} 和正文不一致")
        print("网页与正文一致。" if not stale else "请运行 python tools/build_site.py 重新生成。")
        return 1 if stale else 0
    if OUT.exists():
        shutil.rmtree(OUT)
    written = build(OUT)
    print(f"已生成 {len(written)} 个文件到 docs/book/。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
