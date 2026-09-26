# -*- coding: utf-8 -*-
"""全局配置：词书、TTS音色、翻译API密钥、学习设置"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
DB_PATH = os.path.join(BASE_DIR, "vocab.db")

# ---------- TTS 音色：每种语言固定 1 个 ----------
TTS_VOICE = {
    "en": "en-US-AriaNeural",        # 英语女声
    "ja": "ja-JP-NanamiNeural",      # 日语女声
    "ru": "ru-RU-SvetlanaNeural",    # 俄语女声
    "fr": "fr-FR-DeniseNeural",      # 法语女声
}

# ---------- 百度翻译 API（已配置） ----------
BAIDU_APPID = ""
BAIDU_KEY = ""

# ---------- 词书定义 ----------
WORDBOOKS = {
    "CET4":    {"name": "英语四级",       "lang": "en", "file": os.path.join(DATA_DIR, "CET4.csv"),
                "desc": "大学英语四级大纲 4500+ 核心词汇，备考四级必备。", "color": "#4A90D9", "emoji": "📘"},
    "CET6":    {"name": "英语六级",       "lang": "en", "file": os.path.join(DATA_DIR, "CET6.csv"),
                "desc": "大学英语六级大纲词汇，难度进阶，冲刺高分。", "color": "#E67E22", "emoji": "📗"},
    "JLPT_N5": {"name": "日语 JLPT N5",   "lang": "ja", "file": os.path.join(DATA_DIR, "JLPT_N5.csv"),
                "desc": "日语能力考 N5 基础词汇，入门五十音后必背。", "color": "#E74C3C", "emoji": "🗾"},
    "JLPT_N2": {"name": "日语 JLPT N2",   "lang": "ja", "file": os.path.join(DATA_DIR, "JLPT_N2.csv"),
                "desc": "日语能力考 N2 中级词汇，日常交流无障碍。", "color": "#9B59B6", "emoji": "🌸"},
    "RU_BASIC": {"name": "俄语基础",      "lang": "ru", "file": os.path.join(DATA_DIR, "RU_BASIC.csv"),
                "desc": "俄语入门基础词汇，日常会话高频词。", "color": "#34495E", "emoji": "🇷🇺"},
    "FR_BASIC": {"name": "法语基础",      "lang": "fr", "file": os.path.join(DATA_DIR, "FR_BASIC.csv"),
                "desc": "法语入门基础词汇，浪漫语言从零开始。", "color": "#2980B9", "emoji": "🇫🇷"},
    "TOEFL":    {"name": "托福 TOEFL",    "lang": "en", "file": os.path.join(DATA_DIR, "TOEFL.csv"),
                "desc": "托福核心词汇，留学考试必备。", "color": "#C0392B", "emoji": "🎓", "unlock": 100},
    "IELTS":    {"name": "雅思 IELTS",    "lang": "en", "file": os.path.join(DATA_DIR, "IELTS.csv"),
                "desc": "雅思高频词汇，留学考试必备。", "color": "#27AE60", "emoji": "🎯", "unlock": 300},
}

# ---------- 默认学习设置 ----------
DEFAULT_SETTINGS = {
    "new_per_day": 20,       # 每组学习单词量
    "review_per_day": 100,    # 每组复习单词量
    "auto_play": "on",       # 自动发音 on/off
    "quiz_type": "on",       # 听音选义题型 on/off
    "accent": "英",          # 发音类型（英式/美式）
}
