# -*- coding: utf-8 -*-
"""SQLite 数据库：词书导入、用户单词状态、学习记录、签到、设置"""

import csv
import sqlite3
from datetime import date, datetime, timedelta

from config import DB_PATH, WORDBOOKS, DEFAULT_SETTINGS


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS word (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id    TEXT NOT NULL,
            word       TEXT NOT NULL,
            phonetic   TEXT,
            pos        TEXT,
            meaning    TEXT,
            example    TEXT,
            synonyms   TEXT,
            derivatives TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_word (
            user_id       TEXT DEFAULT 'default',
            word_id       INTEGER NOT NULL,
            status        TEXT DEFAULT 'new',
            n             INTEGER DEFAULT 0,
            interval      INTEGER DEFAULT 0,
            ef            REAL DEFAULT 2.5,
            lapses        INTEGER DEFAULT 0,
            next_review   TEXT,
            last_review   TEXT,
            PRIMARY KEY (user_id, word_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS study_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   TEXT DEFAULT 'default',
            word_id   INTEGER,
            date      TEXT,
            kind      TEXT,
            correct   INTEGER,
            grade     INTEGER
        )
    """)
    # 签到表（exp = 学习值）
    c.execute("""
        CREATE TABLE IF NOT EXISTS checkin (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            date    TEXT UNIQUE,
            exp     INTEGER DEFAULT 0
        )
    """)
    # 设置表
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id TEXT DEFAULT 'default',
            key     TEXT,
            value   TEXT,
            PRIMARY KEY (user_id, key)
        )
    """)
    conn.commit()

    for book_id, info in WORDBOOKS.items():
        cnt = c.execute("SELECT COUNT(*) FROM word WHERE book_id=?", (book_id,)).fetchone()[0]
        if cnt == 0:
            _import_csv(c, book_id, info["file"])
    conn.commit()
    conn.close()


def _import_csv(c, book_id, path):
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            c.execute("""
                INSERT INTO word (book_id, word, phonetic, pos, meaning, example, synonyms, derivatives)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                book_id, row.get("word", ""), row.get("phonetic", ""),
                row.get("pos", ""), row.get("meaning", ""),
                row.get("example", ""), row.get("synonyms", ""), row.get("derivatives", ""),
            ))


# ---------- 词书 / 单词查询 ----------

def get_words(book_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM word WHERE book_id=? ORDER BY id", (book_id,)).fetchall()
    conn.close()
    return rows


def get_word(word_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM word WHERE id=?", (word_id,)).fetchone()
    conn.close()
    return row


def get_new_words(book_id, limit, user_id="default"):
    conn = get_conn()
    rows = conn.execute("""
        SELECT w.* FROM word w
        LEFT JOIN user_word u ON u.word_id = w.id AND u.user_id = ?
        WHERE w.book_id = ? AND u.word_id IS NULL
        ORDER BY w.id LIMIT ?
    """, (user_id, book_id, limit)).fetchall()
    conn.close()
    return rows


def get_due_words(book_id, limit=100, user_id="default"):
    today = date.today().isoformat()
    conn = get_conn()
    rows = conn.execute("""
        SELECT w.*, u.n, u.interval, u.ef, u.lapses
        FROM user_word u JOIN word w ON w.id = u.word_id
        WHERE u.user_id=? AND w.book_id=? AND u.status != 'known'
              AND u.next_review <= ?
        ORDER BY u.next_review LIMIT ?
    """, (user_id, book_id, today, limit)).fetchall()
    conn.close()
    return rows


# ---------- 状态更新 ----------

def mark_new_learned(word_id, user_id="default"):
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO user_word (user_id, word_id, status, n, interval, ef, lapses, next_review, last_review)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (user_id, word_id, "learning", 0, 1, 2.5, 0,
          date.today().isoformat(), date.today().isoformat()))
    conn.commit()
    conn.close()


def mark_known(word_id, user_id="default"):
    """标熟：直接归档，不再复习"""
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO user_word (user_id, word_id, status, n, interval, ef, lapses, next_review, last_review)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (user_id, word_id, "known", 99, 9999, 2.5, 0,
          "2099-12-31", date.today().isoformat()))
    conn.commit()
    conn.close()


def update_after_grade(word_id, n, interval, ef, lapses, next_date, user_id="default"):
    status = "known" if n >= 5 else "learning"
    conn = get_conn()
    conn.execute("""
        UPDATE user_word SET status=?, n=?, interval=?, ef=?, lapses=?, next_review=?, last_review=?
        WHERE user_id=? AND word_id=?
    """, (status, n, interval, ef, lapses, next_date, date.today().isoformat(), user_id, word_id))
    conn.commit()
    conn.close()


def log_study(word_id, kind, correct, grade, user_id="default"):
    conn = get_conn()
    conn.execute("""
        INSERT INTO study_log (user_id, word_id, date, kind, correct, grade)
        VALUES (?,?,?,?,?,?)
    """, (user_id, word_id, date.today().isoformat(), kind, correct, grade))
    conn.commit()
    conn.close()


# ---------- 签到 ----------

def has_checked_today(user_id="default"):
    today = date.today().isoformat()
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM checkin WHERE user_id=? AND date=?", (user_id, today)).fetchone()
    conn.close()
    return row is not None


def do_checkin(user_id="default"):
    """签到：返回 (连续天数, 获得学习值)"""
    today = date.today()
    conn = get_conn()
    yesterday = (today - timedelta(days=1)).isoformat()
    row = conn.execute("SELECT date FROM checkin WHERE user_id=? ORDER BY date DESC LIMIT 1",
                        (user_id,)).fetchone()
    if row and row["date"] == yesterday:
        streak = _calc_streak(conn, user_id)
    else:
        streak = 1
    if conn.execute("SELECT 1 FROM checkin WHERE user_id=? AND date=?",
                    (user_id, today.isoformat())).fetchone():
        conn.close()
        return streak, 0
    exp = 10
    conn.execute("INSERT INTO checkin (user_id, date, exp) VALUES (?,?,?)",
                 (user_id, today.isoformat(), exp))
    conn.commit()
    streak = _calc_streak(conn, user_id)
    conn.close()
    return streak, exp


def add_exp(amount, user_id="default"):
    """学习/复习获得学习值：写入今天的签到记录（没有则补一条）"""
    today = date.today().isoformat()
    conn = get_conn()
    row = conn.execute("SELECT exp FROM checkin WHERE user_id=? AND date=?",
                       (user_id, today)).fetchone()
    if row:
        conn.execute("UPDATE checkin SET exp = exp + ? WHERE user_id=? AND date=?",
                     (amount, user_id, today))
    else:
        conn.execute("INSERT INTO checkin (user_id, date, exp) VALUES (?,?,?)",
                     (user_id, today, amount))
    conn.commit()
    conn.close()


def _calc_streak(conn, user_id):
    rows = conn.execute("SELECT date FROM checkin WHERE user_id=? ORDER BY date DESC",
                        (user_id,)).fetchall()
    if not rows:
        return 0
    dates = [datetime.strptime(r["date"], "%Y-%m-%d").date() for r in rows]
    streak = 1
    for i in range(len(dates) - 1):
        if (dates[i] - dates[i + 1]).days == 1:
            streak += 1
        else:
            break
    return streak


def get_checkin_dates(user_id="default"):
    conn = get_conn()
    rows = conn.execute("SELECT date FROM checkin WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    return {r["date"] for r in rows}


def get_exp(user_id="default"):
    """总学习值"""
    conn = get_conn()
    row = conn.execute("SELECT SUM(exp) AS total FROM checkin WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row["total"] or 0


# ---------- 设置 ----------

def get_settings(user_id="default"):
    conn = get_conn()
    rows = conn.execute("SELECT key, value FROM settings WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    s = dict(DEFAULT_SETTINGS)
    for r in rows:
        s[r["key"]] = r["value"]
    return s


def save_setting(key, value, user_id="default"):
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?,?,?)
    """, (user_id, key, str(value)))
    conn.commit()
    conn.close()


# ---------- 统计 ----------

def get_stats(book_id, user_id="default"):
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM word WHERE book_id=?", (book_id,)).fetchone()[0]
    learned = conn.execute("""
        SELECT COUNT(*) FROM user_word u JOIN word w ON w.id=u.word_id
        WHERE u.user_id=? AND w.book_id=?
    """, (user_id, book_id)).fetchone()[0]
    known = conn.execute("""
        SELECT COUNT(*) FROM user_word u JOIN word w ON w.id=u.word_id
        WHERE u.user_id=? AND w.book_id=? AND u.status='known'
    """, (user_id, book_id)).fetchone()[0]
    due = len(get_due_words(book_id, 100, user_id))

    today = date.today().isoformat()
    row = conn.execute("""
        SELECT SUM(CASE WHEN correct=1 THEN 1 ELSE 0 END) AS right_n,
               COUNT(*) AS total_n
        FROM study_log WHERE user_id=? AND date=?
    """, (user_id, today)).fetchone()
    right_n = row["right_n"] or 0
    total_n = row["total_n"] or 0
    accuracy = round(right_n / total_n * 100, 1) if total_n else 0.0

    conn.close()
    return {"total": total, "learned": learned, "known": known,
            "due": due, "accuracy": accuracy, "today_answers": total_n}


def get_today_count(user_id="default"):
    today = date.today().isoformat()
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) AS n FROM study_log WHERE user_id=? AND date=?",
                       (user_id, today)).fetchone()
    conn.close()
    return row["n"]


def get_total_learned(user_id="default"):
    conn = get_conn()
    row = conn.execute("SELECT COUNT(DISTINCT word_id) AS n FROM study_log WHERE user_id=?",
                       (user_id,)).fetchone()
    conn.close()
    return row["n"]


def get_history(days=14, user_id="default"):
    conn = get_conn()
    rows = conn.execute("""
        SELECT date,
               COUNT(*) AS total,
               SUM(CASE WHEN kind='new' THEN 1 ELSE 0 END) AS learn_n,
               SUM(CASE WHEN kind='review' THEN 1 ELSE 0 END) AS review_n,
               SUM(CASE WHEN correct=1 THEN 1 ELSE 0 END) AS right_n
        FROM study_log WHERE user_id=?
        GROUP BY date ORDER BY date DESC LIMIT ?
    """, (user_id, days)).fetchall()
    conn.close()
    return list(reversed(rows))
