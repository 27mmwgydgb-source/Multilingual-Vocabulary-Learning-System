# -*- coding: utf-8 -*-
"""解析 mahavivo/english-wordlists 的 CET4/CET6 词表，生成项目 CSV。

输入格式:
    abandon [əˈbændən] vt.丢弃；放弃，抛弃
    a art.一(个)；每一(个)
输出 CSV: word,phonetic,pos,meaning,example,synonyms,derivatives
"""

import re
import csv
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(DATA_DIR, "data")

POS_PATTERN = r"(?:vt|vi|v|n|a|ad|adj|adv|art|prep|conj|pron|num|int|abbr|aux|int|pref|suf|pl)\."

# 标准行: word [phonetic] pos.meaning
RE_BRACKET = re.compile(r"^(\S+)\s*\[([^\]]+)\]\s*(.*)$")
# 无音标行: word pos.meaning
RE_NOBRACKET = re.compile(r"^(\S+)\s+(" + POS_PATTERN + r".+)$")
# 词性前缀
RE_POS = re.compile(r"^(" + POS_PATTERN + r")\s*(.*)$")


def parse_line(line):
    line = line.strip()
    if not line:
        return None
    # 跳过标题行、纯字母分类行
    if len(line) <= 2 and line.isalpha():
        return None
    if "大纲" in line or "共" in line and "词" in line:
        return None
    if line.startswith("(") and "词" in line:
        return None

    word, phonetic, rest = None, "", line
    m = RE_BRACKET.match(line)
    if m:
        word, phonetic, rest = m.group(1), m.group(2).strip(), m.group(3).strip()
    else:
        m2 = RE_NOBRACKET.match(line)
        if m2:
            word, rest = m2.group(1), m2.group(2)
        else:
            return None

    # 拆分词性和释义
    pos, meaning = "", rest
    pm = RE_POS.match(rest)
    if pm:
        pos = pm.group(1).rstrip(".")
        meaning = pm.group(2).strip()

    if not meaning:
        return None
    return {
        "word": word,
        "phonetic": "/" + phonetic + "/" if phonetic else "",
        "pos": pos,
        "meaning": meaning,
        "example": "",
        "synonyms": "",
        "derivatives": "",
    }


def process(in_file, out_file):
    rows = []
    with open(in_file, "r", encoding="utf-8") as f:
        for line in f:
            r = parse_line(line)
            if r:
                rows.append(r)
    # 去重
    seen = set()
    uniq = []
    for r in rows:
        if r["word"].lower() not in seen:
            seen.add(r["word"].lower())
            uniq.append(r)
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["word", "phonetic", "pos", "meaning",
                                          "example", "synonyms", "derivatives"])
        w.writeheader()
        w.writerows(uniq)
    print(f"{out_file}: {len(uniq)} 词")


process(os.path.join(RAW_DIR, "CET4_raw.txt"), os.path.join(RAW_DIR, "CET4.csv"))
process(os.path.join(RAW_DIR, "CET6_raw.txt"), os.path.join(RAW_DIR, "CET6.csv"))
print("完成")
