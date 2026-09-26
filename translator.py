# -*- coding: utf-8 -*-
"""百度翻译 API（可选增强）

在 config.py 填入 BAIDU_APPID / BAIDU_KEY 后启用；
未配置时所有函数返回 None，主程序自动回退到内置词典。
"""

import hashlib
import random

import requests

from config import BAIDU_APPID, BAIDU_KEY

API_URL = "https://fanyi-api.baidu.com/api/trans/vip/translate"


def enabled() -> bool:
    return bool(BAIDU_APPID and BAIDU_KEY)


def translate(text: str, from_lang: str, to_lang: str = "zh"):
    """调用百度翻译，返回译文文本；失败或未配置返回 None。

    from_lang: en / ja
    """
    if not enabled():
        return None

    lang_map = {"en": "en", "ja": "jp"}
    sl = lang_map.get(from_lang, "en")
    salt = str(random.randint(32768, 65536))
    sign = hashlib.md5(
        (BAIDU_APPID + text + salt + BAIDU_KEY).encode("utf-8")
    ).hexdigest()

    params = {
        "q": text,
        "from": sl,
        "to": to_lang,
        "appid": BAIDU_APPID,
        "salt": salt,
        "sign": sign,
    }
    try:
        r = requests.get(API_URL, params=params, timeout=8)
        data = r.json()
        if "trans_result" in data:
            return data["trans_result"][0]["dst"]
    except Exception as e:
        print(f"[翻译] 调用失败: {e}")
    return None


def make_example(word: str, pos: str, from_lang: str = "en"):
    """按词性用模板造一个包含原词的句子，再调API翻译成中文。
    返回 (英文/外文例句, 中文翻译)，失败返回 (None, None)。
    """
    if not enabled() or not word:
        return None, None

    word = word.strip()
    p = (pos or "").lower()

    if from_lang == "en":
        if p.startswith("vt") or p == "v" or p.startswith("v"):
            en = f"She decided to {word} the old plan."
        elif p.startswith("n"):
            en = f"This {word} plays an important role."
        elif p.startswith("a"):
            en = f"The result was quite {word}."
        elif p.startswith("ad"):
            en = f"She finished the work {word}."
        else:
            en = f"The word '{word}' is commonly used in daily life."
    elif from_lang == "ja":
        en = f"「{word}」という言葉をしっかり覚えます。"
    elif from_lang == "ru":
        en = f"Слово «{word}» часто используется в речи."
    elif from_lang == "fr":
        en = f"Le mot «{word}» est souvent utilisé."
    else:
        en = f"The word '{word}' is commonly used."

    zh = translate(en, from_lang)
    return (en, zh) if zh else (None, None)
