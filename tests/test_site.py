"""在线阅读网页（docs/book/）必须和 book/ 正文一致，而且没有漏转换的 Markdown。"""
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from tools import build_site

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE = DOCS / "book"


class Collector(HTMLParser):
    """收集链接、元素 id 和去掉代码之后的可见文字。"""

    def __init__(self):
        super().__init__()
        self.hrefs, self.ids, self.text, self.counts = [], set(), [], {}
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.counts[tag] = self.counts.get(tag, 0) + 1
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.hrefs.append(attrs[key])
        if tag in ("pre", "code", "script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("pre", "code", "script", "style"):
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)


def parse(path: Path) -> Collector:
    c = Collector()
    c.feed(path.read_text(encoding="utf-8"))
    return c


def pages():
    return sorted(SITE.rglob("*.html"))


class SiteTest(unittest.TestCase):
    def test_site_is_up_to_date(self):
        self.assertEqual(build_site.stale_files(), [], "请运行 python tools/build_site.py")

    def test_every_book_file_has_a_page(self):
        sources = {p.relative_to(ROOT / "book").as_posix() for p in (ROOT / "book").rglob("*.md")}
        expected = {"index.html" if s == "README.md" else s[:-3] + ".html" for s in sources}
        self.assertEqual({p.relative_to(SITE).as_posix() for p in pages()}, expected)

    def test_no_markdown_left_in_the_text(self):
        for page in pages():
            text = "".join(parse(page).text)
            for mark in ("**", "`", "](", "```"):
                self.assertNotIn(mark, text, f"{page.name} 里还有未转换的 {mark}")

    def test_code_blocks_and_tables_are_all_rendered(self):
        for page in pages():
            md = page.relative_to(SITE).as_posix()
            src = ROOT / "book" / ("README.md" if md == "index.html" else md[:-5] + ".md")
            body = src.read_text(encoding="utf-8")
            fences = len(re.findall(r"^```", body, re.M)) // 2
            tables = len(re.findall(r"^\|(\s*:?-+:?\s*\|)+\s*$", body, re.M))
            counts = parse(page).counts
            self.assertEqual(counts.get("pre", 0), fences, page.name)
            self.assertEqual(counts.get("table", 0), tables, page.name)

    def test_internal_links_resolve(self):
        for page in [*pages(), DOCS / "index.html"]:
            for href in parse(page).hrefs:
                parts = urlsplit(href)
                if parts.scheme or href.startswith(("data:", "mailto:")):
                    continue
                self.assertFalse(href.startswith("/"), f"{page.name}：项目站点不能用绝对路径 {href}")
                if not parts.path:
                    continue
                target = (page.parent / unquote(parts.path)).resolve()
                self.assertTrue(target.exists(), f"{page.name}：链接目标不存在：{href}")
                self.assertFalse(target.suffix == ".md", f"{page.name}：网页不应链接到 .md：{href}")
                if parts.fragment and target.suffix == ".html":
                    self.assertIn(unquote(parts.fragment), parse(target).ids, f"{page.name}：锚点不存在：{href}")

    def test_guide_links_every_chapter_page(self):
        guide = (DOCS / "index.html").read_text(encoding="utf-8")
        files = json.loads(re.search(r"var FILES = (\{.*?\});", guide).group(1))
        self.assertEqual(sorted(files), [f"{n:02d}" for n in range(1, 35)])
        for num, rel in files.items():
            self.assertTrue((DOCS / rel).exists(), rel)
            self.assertTrue((DOCS / rel).name.startswith(num), rel)

    def test_search_index_covers_every_page(self):
        index = json.loads((SITE / "search.json").read_text(encoding="utf-8"))
        urls = {item["u"].split("#")[0] for item in index}
        self.assertEqual(urls, {p.relative_to(SITE).as_posix() for p in pages()})


class ConverterTest(unittest.TestCase):
    def page(self):
        return build_site.Page(ROOT / "book" / "part-04" / "20-state.md")

    def test_code_span_keeps_stars_and_brackets(self):
        html = build_site.inline("调用 `validate(rows, [*RULES, x])` 和 `**kwargs`", self.page())
        self.assertIn("<code>validate(rows, [*RULES, x])</code>", html)
        self.assertIn("<code>**kwargs</code>", html)

    def test_links_inside_and_outside_the_book(self):
        page = self.page()
        self.assertEqual(page.resolve_link("../part-01/01-data-and-processing.md"), "../part-01/01-data-and-processing.html")
        self.assertEqual(page.resolve_link("../README.md"), "../index.html")
        self.assertEqual(
            page.resolve_link("../../examples/ch20_state.py"),
            build_site.BLOB + "examples/ch20_state.py",
        )

    def test_pipe_inside_code_does_not_split_a_cell(self):
        self.assertEqual(build_site.split_row("| a | `X | None` |"), ["a", "`X | None`"])

    def test_html_in_text_is_escaped(self):
        self.assertIn("&lt;rect&gt;", build_site.inline("`<rect>` 元素", self.page()))


if __name__ == "__main__":
    unittest.main()
