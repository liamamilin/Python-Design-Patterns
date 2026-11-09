"""第 22 章：第一版。智能音箱用一串 if/elif 判断该怎么回应。"""
from __future__ import annotations


def respond(text: str, child_mode: bool = False) -> str:
    if "闹钟" in text:
        return "好的，闹钟已设好"
    elif "天气" in text:
        return "今天晴，18 到 26 度"
    elif "外卖" in text:  # 新加的功能，插在了购物前面
        return "已为你下单外卖"
    elif "买" in text:
        if child_mode:
            return "儿童模式下不能购物"
        return "已加入购物车"
    elif "播放" in text:
        return "开始播放"
    return "抱歉，我没听懂"


if __name__ == "__main__":
    print(respond("帮我买一盒彩笔", child_mode=True))
    print(respond("帮我点个外卖", child_mode=True))
