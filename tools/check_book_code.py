"""检查书稿中的 Python 代码块是否与 examples/ 中的文件逐字一致。

规则：book/part-*/XX-*.md 里每个 ```python 代码块，都必须原样出现在
同一章号的某个 examples/chXX_*.py 文件中。不打算运行的片段请标成 ```text。

用法（在仓库根目录）：
    python tools/check_book_code.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"```python\n(.*?)```", re.S)


def problems() -> list[str]:
    found: list[str] = []
    for chapter in sorted(ROOT.glob("book/part-*/[0-9][0-9]-*.md")):
        number = chapter.name[:2]
        sources = [p.read_text(encoding="utf-8") for p in sorted(ROOT.glob(f"examples/ch{number}_*.py"))]
        blocks = BLOCK.findall(chapter.read_text(encoding="utf-8"))
        if blocks and not sources:
            found.append(f"{chapter.relative_to(ROOT)}：有 Python 代码块，但没有 examples/ch{number}_*.py")
            continue
        for index, block in enumerate(blocks, 1):
            snippet = block.rstrip("\n")
            if not any(snippet in source for source in sources):
                first = snippet.splitlines()[0] if snippet else "(空代码块)"
                found.append(f"{chapter.relative_to(ROOT)} 第 {index} 个代码块不在示例文件中：{first}")
    return found


def main() -> int:
    found = problems()
    for line in found:
        print(line)
    print("书中代码与示例文件一致。" if not found else f"共 {len(found)} 处不一致。")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
