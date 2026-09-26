# -*- coding: utf-8 -*-
"""SM-2 间隔重复算法（SuperMemo 2 简化实现）

每个单词记录：
    n        已成功复习次数
    interval 当前复习间隔（天）
    ef       难易系数（easiness factor），默认 2.5，最小 1.3
    lapses   遗忘次数

反馈等级 grade（0-5），对应不背单词的三档：
    5 / 4  -> "认识"
    3      -> "模糊"
    2 / 1 / 0 -> "不认识"
"""

from datetime import date, timedelta


def grade_to_feedback(grade: int) -> str:
    if grade >= 4:
        return "认识"
    if grade == 3:
        return "模糊"
    return "不认识"


def next_review(n: int, interval: int, ef: float, grade: int):
    """根据本次反馈等级，计算下一次复习的状态。

    返回 (new_n, new_interval, new_ef, new_lapses_delta, delta_days)
    delta_days = 距今天多少天后复习
    """
    if grade < 3:
        # 不认识：打回重学，明天再来
        new_n = 0
        new_interval = 1
        new_ef = max(1.3, ef - 0.2)
        return new_n, new_interval, new_ef, +1, 1

    # 认识 / 模糊
    if grade == 3:
        # 模糊：小幅缩短，1 天后再来
        new_n = max(1, n)
        new_interval = 1
        new_ef = max(1.3, ef - 0.15)
        return new_n, new_interval, new_ef, 0, 1

    # grade >= 4 认识：正常推进间隔
    if n == 0:
        new_n = 1
        new_interval = 1
    elif n == 1:
        new_n = 2
        new_interval = 3
    else:
        new_n = n + 1
        new_interval = max(1, round(interval * ef))

    # 根据记忆质量微调 ef
    new_ef = ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    new_ef = max(1.3, new_ef)
    return new_n, new_interval, new_ef, 0, new_interval


def due_date_str(interval: int) -> str:
    """返回 interval 天后的日期字符串 YYYY-MM-DD"""
    d = date.today() + timedelta(days=interval)
    return d.isoformat()
