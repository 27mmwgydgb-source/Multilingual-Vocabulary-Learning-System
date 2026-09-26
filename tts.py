# -*- coding: utf-8 -*-
"""edge-tts 发音 + 本地音频缓存

每个单词/例句生成一次 mp3，存到 audio/ 目录，下次直接读缓存。
"""

import hashlib
import os
import asyncio

import edge_tts

from config import TTS_VOICE, AUDIO_DIR

os.makedirs(AUDIO_DIR, exist_ok=True)


def _cache_path(lang: str, text: str) -> str:
    key = f"{lang}_{text}".encode("utf-8")
    name = hashlib.md5(key).hexdigest() + ".mp3"
    return os.path.join(AUDIO_DIR, name)


async def _synthesize(text: str, lang: str, out_path: str):
    voice = TTS_VOICE.get(lang, TTS_VOICE["en"])
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)


def speak(text: str, lang: str) -> str:
    """生成或读取音频缓存，返回 mp3 文件路径。"""
    if not text:
        return ""
    path = _cache_path(lang, text)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        try:
            asyncio.run(_synthesize(text, lang, path))
        except Exception as e:
            print(f"[TTS] 发音失败: {e}")
            return ""
    return path
