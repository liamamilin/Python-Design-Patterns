"""第 13 章：第一版。导出客服聊天记录，用几个开关控制打码和截断。"""
from __future__ import annotations

import re

PHONE = re.compile(r"1\d{10}")

messages = [
    ("客户", "请回电 13812345678 谢谢"),
    ("客服", "好的，稍后联系您"),
]


def mask_phone(match: re.Match[str]) -> str:
    s = match.group()
    return s[:3] + "****" + s[-4:]


def export(chat: list[tuple[str, str]], *, mask: bool = False, limit: int | None = None) -> list[str]:
    out = []
    for who, text in chat:
        line = f"{who}：{text}"
        if limit is not None and len(line) > limit:
            line = line[: limit - 1] + "…"  # 先截断
        if mask:
            line = PHONE.sub(mask_phone, line)  # 再打码
        out.append(line)
    return out


if __name__ == "__main__":
    print(export(messages, mask=True))
    print(export(messages, mask=True, limit=16))
