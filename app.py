# -*- coding: utf-8 -*-
"""多语言词汇学习系统 v6 - 不背单词三轮交错学习"""

import base64
import random
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import db
import sm2
import translator
import tts
from config import WORDBOOKS

st.set_page_config(page_title="多语言词汇学习", layout="wide", page_icon="📚")
db.init_db()
settings = db.get_settings()

if "page" not in st.session_state:
    st.session_state.page = "home"
if "book_id" not in st.session_state:
    st.session_state.book_id = "CET4"

book_id = st.session_state.book_id
book = WORDBOOKS[book_id]
lang = book["lang"]
exp = db.get_exp()


@st.cache_data(ttl=86400, show_spinner=False)
def get_example(word, pos, lg):
    """模板造句 + 百度翻译，返回 (外文例句, 中文翻译)"""
    en, zh = translator.make_example(word, pos, lg)
    return en or "", zh or ""


def speaker(text, key, small=False):
    """小喇叭按钮，点击播放"""
    label = "🔊" if small else "🔊 发音"
    if st.button(label, key=f"spk_{key}"):
        path = tts.speak(text, lang)
        if path:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
                unsafe_allow_html=True,
            )


# ---------- CSS ----------
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #e8f0f8 0%, #fdf2e8 50%, #e8f8ef 100%); }

    section[data-testid="stSidebar"] { font-size: 20px; line-height: 2.2; }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] li { font-size: 20px !important; line-height: 2.2 !important; }
    section[data-testid="stSidebar"] h3 { font-size: 24px !important; }
    section[data-testid="stSidebar"] button { font-size: 19px !important; padding: 12px 0 !important; }

    /* 首页大卡片导航按钮 */
    .home-card {
        width: 100%; text-align: center; border-radius: 22px; border: none;
        padding: 36px 20px; background: #fff;
        box-shadow: 0 6px 24px rgba(100,150,200,0.15);
        transition: all .2s; font-family: "Microsoft YaHei", sans-serif;
    }
    .home-card:hover { transform: translateY(-5px); box-shadow: 0 12px 32px rgba(255,106,0,0.25); }
    .home-card .hc-emoji { font-size: 52px; }
    .home-card .hc-title { font-size: 27px; font-weight: 800; color: #1a1a2e; margin-top: 10px; }
    .home-card .hc-sub { font-size: 15px; color: #999; margin-top: 6px; }


    .big-word {
        font-size: 84px; font-weight: 800; text-align: center;
        color: #1a1a2e; letter-spacing: 3px; padding: 10px 0 2px 0;
        font-family: Georgia, "Times New Roman", serif;
    }
    .phonetic-center {
        text-align: center; color: #e67e22; font-size: 24px; margin: 6px 0 18px 0;
        font-family: monospace;
    }
    .stage-tag {
        text-align: center; font-size: 17px; color: #fff; background: #ff6a00;
        border-radius: 20px; padding: 6px 22px; display: inline-block; margin-bottom: 8px;
    }
    .meaning-box {
        background: #ffffff; border-radius: 18px; padding: 24px 30px;
        box-shadow: 0 6px 24px rgba(100,150,200,0.15);
        font-size: 25px; text-align: center; margin: 12px 0;
        border-left: 5px solid #ff6a00;
    }
    .example-box {
        background: linear-gradient(135deg, #eef5fc, #fef0e8);
        border-radius: 14px; padding: 18px 26px;
        margin: 12px 0; font-size: 18px; color: #333; line-height: 1.8;
    }
    .meta-row { font-size: 16px; color: #666; margin: 8px 0; }

    div.stButton > button {
        width: 100%; border-radius: 16px; border: none;
        font-size: 22px; font-weight: 700; padding: 20px 0;
        font-family: "Microsoft YaHei", sans-serif;
        transition: all .18s ease;
    }
    div.stButton > button, div.stButton > button p, div.stButton > button span {
        white-space: pre-line !important; line-height: 1.5;
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(255,106,0,0.3); }

    /* 首页大卡片：更高、文字三行居中 */
    .home-card-row button {
        padding: 44px 20px !important; font-size: 24px !important; line-height: 1.6 !important;
    }

    /* 学习/复习页底部操作按钮：放大 */
    .action-btn button {
        font-size: 34px !important; padding: 36px 0 !important; border-radius: 20px !important;
    }
    [class*="st-key-rstarbtn_"] button, [class*="st-key-rgrade_"] button,
    [class*="st-key-lstarbtn_"] button, [class*="st-key-know_"] button,
    [class*="st-key-forget_"] button {
        font-size: 34px !important; padding: 22px 0 !important; border-radius: 28px !important;
        min-height: 80px;
    }
    /* 第1轮未答题选项：大卡片 */
    [class*="st-key-l1_"] button, [class*="st-key-opt_"] button {
        font-size: 28px !important; padding: 26px 28px !important;
        text-align: left !important; border-radius: 16px !important;
        line-height: 1.6 !important;
    }

    /* 顶部返回按钮 */
    .back-bar { margin-bottom: 10px; }
    .back-bar button {
        width: auto !important; padding: 8px 22px !important; font-size: 18px !important;
        border-radius: 12px !important; background: #eef2f7 !important; color: #333 !important;
    }


    .nav-card {
        background: #fff; border-radius: 22px; padding: 36px 24px; text-align: center;
        box-shadow: 0 6px 24px rgba(100,150,200,0.15); height: 100%;
        transition: transform .2s;
    }
    .nav-card:hover { transform: translateY(-5px); box-shadow: 0 12px 32px rgba(100,150,200,0.25); }
    .nav-emoji { font-size: 56px; }
    .nav-title { font-size: 26px; font-weight: 700; margin-top: 12px; color: #1a1a2e; }
    .nav-sub { color: #999; font-size: 15px; margin-top: 6px; }

    .book-card {
        border-radius: 22px; padding: 28px; color: #fff; min-height: 300px;
        display: flex; flex-direction: column; justify-content: space-between;
        box-shadow: 0 8px 28px rgba(0,0,0,0.18);
        transition: transform .2s, box-shadow .2s; cursor: pointer;
    }
    .book-card:hover { transform: scale(1.03); box-shadow: 0 12px 36px rgba(0,0,0,0.25); }
    .book-emoji { font-size: 64px; }
    .book-name { font-size: 28px; font-weight: 800; margin-top: 10px; }
    .book-desc { font-size: 14px; opacity: .92; margin-top: 10px; line-height: 1.6; }
    .locked { filter: grayscale(0.85) brightness(0.85); cursor: not-allowed; }

    /* 词书卡片：透明按钮覆盖在彩色卡片上 */
    .pick-wrap { position: relative; }
    .pick-wrap button {
        position: absolute !important; top: 0; left: 0;
        width: 100% !important; height: 100% !important;
        background: transparent !important; border: none !important;
        opacity: 0; z-index: 10; margin: 0 !important;
    }

    .quiz-btn {
        width: 100%; text-align: left; padding: 24px 28px;
        border-radius: 16px; background: #fff;
        box-shadow: 0 3px 12px rgba(100,150,200,0.12);
        border: 2px solid transparent; font-size: 22px; font-weight: 600;
        margin: 10px 0; transition: all .18s;
    }
    .quiz-btn:hover { border-color: #ff6a00; transform: translateX(6px); }
    .quiz-correct { background: #d4edda !important; border-color: #28a745 !important; color: #155724 !important; }
    .quiz-wrong { background: #f8d7da !important; border-color: #dc3545 !important; color: #721c24 !important; }
    .opt-word { font-size: 15px; color: #888; margin-top: 6px; }

    .center-btn { display: flex; justify-content: center; margin-top: 20px; }
    .center-btn button { width: 60% !important; font-size: 26px !important; padding: 22px 0 !important; }
    .center-col { max-width: 760px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)


def goto(page):
    st.session_state.page = page
    st.rerun()


# ---------- 侧边栏 ----------
with st.sidebar:
    st.markdown("### 📚 多语言词汇学习")
    st.markdown(f"**当前词书**：{book['emoji']} {book['name']}")
    st.markdown(f"### ⭐ 学习值：{exp}")
    if st.button("🔍 单词查询"):
        goto("lookup")
    if st.button("📚 切换词书"):
        goto("books")
    st.divider()
    stats = db.get_stats(book_id)
    st.markdown(f"""
    - 总词数 **{stats['total']}**
    - 已学 **{stats['learned']}**
    - 已掌握 **{stats['known']}**
    - 待复习 **{stats['due']}**
    """)
    st.divider()
    checked = db.has_checked_today()
    if checked:
        st.success(f"今日已签到 | 学习值 {exp}")
    else:
        if st.button("每日签到 +10 学习值"):
            streak, e = db.do_checkin()
            st.toast(f"签到成功！连续 {streak} 天 +{e} 学习值", icon="🎉")
            st.balloons()
            st.rerun()

# ---------- 左上角全局返回按钮（非首页显示） ----------
if st.session_state.page != "home":
    st.markdown('<div class="back-bar">', unsafe_allow_html=True)
    if st.button("← 返回首页"):
        st.session_state.page = "home"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 词书选择页 ====================
if st.session_state.page == "books":
    st.markdown("# 选择词书")
    st.caption(f"当前学习值：{exp} ⭐（学习、复习、签到均可获得学习值，解锁高级词书）")
    st.markdown("---")
    cols = st.columns(2)
    for i, (bid, b) in enumerate(WORDBOOKS.items()):
        with cols[i % 2]:
            need = b.get("unlock", 0)
            locked = exp < need if need else False
            cnt = db.get_stats(bid)["total"]
            lock_cls = " locked" if locked else ""
            lock_badge = ("🔒 需 " + str(need) + " 学习值") if locked else "✅ 已解锁"
            st.markdown(f"""
            <div class="pick-wrap">
              <div class="book-card{lock_cls}" style="background:linear-gradient(135deg, {b['color']}, {b['color']}cc);">
                <div>
                    <div class="book-emoji">{b['emoji']}</div>
                    <div class="book-name">{b['name']}</div>
                </div>
                <div>
                    <div class="book-desc">{b['desc']}</div>
                    <div style="margin-top:10px;font-size:13px;opacity:0.9">{lock_badge} · 共 {cnt} 词</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(" ", key=f"pick_{bid}", use_container_width=True, disabled=locked):
                st.session_state.book_id = bid
                st.toast(f"已切换到 {b['name']}", icon="✅")
                goto("home")


# ==================== 首页 ====================
elif st.session_state.page == "home":
    st.markdown(f"# 今日学习 · {book['emoji']} {book['name']}")
    st.markdown("")
    new_per_day = int(settings["new_per_day"])
    due = db.get_due_words(book_id, int(settings["review_per_day"]))
    today_n = db.get_today_count()

    c1, c2 = st.columns(2)
    with c1:
        if st.button(f"📖\n学习新词\n今日待学 {new_per_day} 词 · 三轮掌握",
                     key="home_learn", use_container_width=True):
            goto("learn")
    with c2:
        if st.button(f"🔁\n复习旧词\n今日待复习 {len(due)} 词 · 复习优先",
                     key="home_review", use_container_width=True):
            goto("review")

    st.markdown("")
    c, d = st.columns(2)
    if c.button("✍️\n单词自查\n四选一检测", key="home_quiz", use_container_width=True):
        goto("quiz")
    if d.button("📊\n学习统计\n打卡与趋势", key="home_stats", use_container_width=True):
        goto("stats")
    e, f = st.columns(2)
    if e.button("📚\n切换词书\n8本词书", key="home_books", use_container_width=True):
        goto("books")
    if f.button("⚙️\n学习设置\n每日量/发音", key="home_settings", use_container_width=True):
        goto("settings")

    st.markdown("")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("今日已学", f"{today_n}")
    m2.metric("累计学习", f"{db.get_total_learned()}")
    m3.metric("今日正确率", f"{stats['accuracy']}%")
    m4.metric("学习值", f"{exp}")


# ==================== 学习新词：三轮交错 ====================
elif st.session_state.page == "learn":
    new_per_day = int(settings["new_per_day"])
    new_words = db.get_new_words(book_id, new_per_day)

    if not new_words:
        st.success("🎉 这本词书的新词已全部学完！")
    else:
        # 初始化学习队列
        if st.session_state.get("learn_book") != book_id:
            st.session_state.learn_book = book_id
            st.session_state.learn_words = {w["id"]: w for w in new_words}
            st.session_state.learn_queue = [{"id": w["id"], "stage": 1} for w in new_words]
            st.session_state.learn_finished = 0
            st.session_state.learn_total = len(new_words)
            st.session_state.learn_feedback = None  # 作答反馈
            st.session_state.learn_prev = []       # 上一个词历史栈
            st.session_state.opts_task = None      # 选项已生成的任务id

        words_map = st.session_state.learn_words
        queue = st.session_state.learn_queue
        total = st.session_state.learn_total
        finished = st.session_state.learn_finished

        def advance(next_stage, requeue=False):
            """推进当前词。一二三轮随机穿插：
            next_stage=None 表示完成；requeue=True 打回队尾（重做第1轮）；
            否则把下一轮随机插到队列前几个位置，让新词/复习轮次交错出现。
            """
            cur = st.session_state.learn_queue.pop(0)
            st.session_state.learn_prev.append({"id": cur["id"], "stage": cur["stage"]})
            if next_stage is not None:
                if requeue:
                    st.session_state.learn_queue.append({"id": cur["id"], "stage": next_stage})
                else:
                    # 随机插在 0~3 之间，交错出场
                    pos = random.randint(0, min(3, len(st.session_state.learn_queue)))
                    st.session_state.learn_queue.insert(pos, {"id": cur["id"], "stage": next_stage})

        st.caption(f"进度：{finished} / {total}")

        if queue:
            cur = queue[0]
            w = words_map[cur["id"]]
            word_text = w["word"] or "???"
            stage = cur["stage"]
            task_id = f"{cur['id']}_{stage}"
            stage_names = {1: "第 1 轮 · 看词选义", 2: "第 2 轮 · 回忆词义", 3: "第 3 轮 · 巩固记忆"}

            _, mc, _ = st.columns([1, 3, 1])
            with mc:
                st.markdown(f"<div style='text-align:center'><span class='stage-tag'>{stage_names[stage]}</span></div>",
                            unsafe_allow_html=True)
                st.markdown(f'<div class="big-word">{word_text}</div>', unsafe_allow_html=True)
                # 音标按钮：占满居中，在单词正下方
                if st.button(f"🔊  {w['phonetic'] or ''}", key=f"lw_{w['id']}_{stage}",
                             use_container_width=True):
                    p = tts.speak(word_text, lang)
                    if p:
                        with open(p, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        st.markdown(
                            f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>',
                            unsafe_allow_html=True)

                # ---------- 第1轮：四选一中英文释义 ----------
                if stage == 1:
                    # 进入新任务才生成选项，避免点喇叭rerun后选项变化
                    if st.session_state.opts_task != task_id:
                        all_w = db.get_words(book_id)
                        same_first = [x for x in all_w
                                      if x["id"] != w["id"] and x["word"]
                                      and x["word"][0] == (word_text[0] if word_text else "")]
                        pool = same_first if len(same_first) >= 3 else \
                            [x for x in all_w if x["id"] != w["id"]]
                        distractors = random.sample(pool, min(3, len(pool)))
                        opts = distractors + [w]
                        random.shuffle(opts)
                        st.session_state.learn_opts = opts
                        st.session_state.opts_task = task_id
                        st.session_state.learn_feedback = None

                    fb = st.session_state.learn_feedback

                    if fb is None:
                        st.markdown("<div style='text-align:center;color:#888;margin:10px 0'>选出这个单词正确的中文释义</div>",
                                    unsafe_allow_html=True)
                        for i, opt in enumerate(st.session_state.learn_opts):
                            label = f"{opt['pos'] or ''}. {opt['meaning']}"
                            if st.button(label, key=f"l1_{task_id}_{i}", use_container_width=True):
                                st.session_state.learn_feedback = {
                                    "chosen": opt["id"],
                                    "correct": opt["id"] == w["id"],
                                }
                                st.rerun()
                    else:
                        chosen_id = fb["chosen"]
                        is_correct = fb["correct"]

                        # 选对自动发音一次
                        if is_correct:
                            p = tts.speak(word_text, lang)
                            if p:
                                with open(p, "rb") as f:
                                    b64 = base64.b64encode(f.read()).decode()
                                st.markdown(
                                    f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>',
                                    unsafe_allow_html=True)

                        # 只把正确项标绿、把选错的那一项标红，其余保持白色
                        for opt in st.session_state.learn_opts:
                            label = f"{opt['pos'] or ''}. {opt['meaning']}"
                            if opt["id"] == w["id"]:
                                st.markdown(f'<div class="quiz-btn quiz-correct">✅ {label}</div>',
                                            unsafe_allow_html=True)
                            elif opt["id"] == chosen_id:
                                st.markdown(f'<div class="quiz-btn quiz-wrong">❌ {label}</div>',
                                            unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="quiz-btn">{label}</div>',
                                            unsafe_allow_html=True)

                        st.markdown(f'<div class="meaning-box"><b>{w["pos"] or ""}.</b> {w["meaning"]}</div>',
                                    unsafe_allow_html=True)
                        en_ex, zh_ex = get_example(word_text, w["pos"], lang)
                        if en_ex:
                            exl, exr = st.columns([5, 1])
                            with exl:
                                st.markdown(f'<div class="example-box">📖 {en_ex}<br>　　{zh_ex}</div>',
                                            unsafe_allow_html=True)
                            with exr:
                                speaker(en_ex, f"lex_{task_id}", small=True)

                        c1, c2 = st.columns(2)
                        c1.markdown(f'<div class="meta-row">🔗 <b>同义词</b>：{w["synonyms"] or "暂无"}</div>',
                                    unsafe_allow_html=True)
                        c2.markdown(f'<div class="meta-row">🌱 <b>派生词</b>：{w["derivatives"] or "暂无"}</div>',
                                    unsafe_allow_html=True)

                        if is_correct:
                            st.success("选对了！这个词将进入第 2 轮")
                        else:
                            st.error("选错了，这个词稍后会重新出现")

                        # 上一个词 / 下一个词
                        pb, pn = st.columns(2)
                        if pb.button("⬅ 上一个词", key=f"prev_{task_id}"):
                            if st.session_state.learn_prev:
                                prev = st.session_state.learn_prev.pop()
                                queue.insert(0, prev)
                            st.session_state.learn_feedback = None
                            st.session_state.opts_task = None
                            st.rerun()
                        if pn.button("下一个词 ➡", type="primary", key=f"next_{task_id}"):
                            if is_correct:
                                advance(2)
                            else:
                                advance(1, requeue=True)
                            st.session_state.learn_feedback = None
                            st.session_state.opts_task = None
                            st.rerun()

                # ---------- 第2轮 / 第3轮：只看单词，认识/忘记 ----------
                else:
                    st.markdown("<div style='text-align:center;color:#888;margin:16px 0;font-size:19px'>请在脑中回想这个词的意思</div>",
                                unsafe_allow_html=True)

            # 第2/3轮按钮放在 mc 外，占满整行宽度
            if stage != 1:
                bs, bk, bn = st.columns(3)
                star_key = f"lstar_{w['id']}"
                if bs.button("⭐" if st.session_state.get(star_key) else "☆ 标熟",
                             key=f"lstarbtn_{w['id']}", use_container_width=True):
                    st.session_state[star_key] = True
                    db.mark_known(w["id"])
                    db.log_study(w["id"], "new", 1, 5)
                    db.add_exp(2)
                    advance(None)
                    st.session_state.learn_finished += 1
                    st.toast("已标熟，+2 学习值", icon="⭐")
                    st.rerun()
                if bk.button("认识", type="primary", key=f"know_{w['id']}_{stage}",
                             use_container_width=True):
                    if stage == 2:
                        advance(3)
                        st.toast("进入第 3 轮巩固", icon="👍")
                    else:
                        advance(None)
                        db.mark_new_learned(w["id"])
                        db.log_study(w["id"], "new", 1, 5)
                        db.add_exp(1)
                        st.session_state.learn_finished += 1
                        st.balloons()
                    st.rerun()
                if bn.button("忘记", key=f"forget_{w['id']}_{stage}",
                             use_container_width=True):
                    advance(1, requeue=True)
                    st.toast("这个词将重新从第 1 轮开始", icon="🔁")
                    st.rerun()
        else:
            st.success("🎉 本批新词全部通过三轮学习，已进入复习队列！明天记得来复习。")


# ==================== 复习旧词（SM-2） ====================
elif st.session_state.page == "review":
    limit = int(settings["review_per_day"])
    due = db.get_due_words(book_id, limit)

    if not due:
        st.success("🎉 今天没有到期的复习单词！")
    else:
        if "rev_idx" not in st.session_state or st.session_state.get("cur_book") != book_id:
            st.session_state.rev_idx = 0
            st.session_state.cur_book = book_id
            st.session_state.rev_show = False

        idx = st.session_state.rev_idx
        st.caption(f"{idx} / {len(due)}")

        if idx < len(due):
            w = due[idx]
            word_text = w["word"] or "???"
            _, mc, _ = st.columns([1, 3, 1])
            with mc:
                st.markdown(f'<div class="big-word">{word_text}</div>', unsafe_allow_html=True)
                # 音标按钮：占满居中，在单词正下方
                if st.button(f"🔊  {w['phonetic'] or ''}", key=f"rv_{w['id']}",
                             use_container_width=True):
                    p = tts.speak(word_text, lang)
                    if p:
                        with open(p, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        st.markdown(
                            f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>',
                            unsafe_allow_html=True)

                if not st.session_state.rev_show:
                    st.markdown("<div style='text-align:center;color:#888;margin:14px 0;font-size:19px'>先回想词义，再点击查看</div>",
                                unsafe_allow_html=True)
                    st.markdown('<div class="center-btn">', unsafe_allow_html=True)
                    if st.button("显示释义"):
                        st.session_state.rev_show = True
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="meaning-box"><b>{w["pos"] or ""}.</b> {w["meaning"]}</div>',
                                unsafe_allow_html=True)
                    en_ex, zh_ex = get_example(word_text, w["pos"], lang)
                    if en_ex:
                        exl, exr = st.columns([5, 1])
                        with exl:
                            st.markdown(f'<div class="example-box">📖 {en_ex}<br>　　{zh_ex}</div>',
                                        unsafe_allow_html=True)
                        with exr:
                            speaker(en_ex, f"rve_{w['id']}", small=True)

            # 底部操作按钮：放在 mc 外占满宽度，放大
            if st.session_state.rev_show:
                st.markdown("")
                st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                b_star, b5, b3, b1 = st.columns(4)
                grade = None
                star_key = f"rstar_{w['id']}"
                if b_star.button("⭐" if st.session_state.get(star_key) else "☆",
                                 key=f"rstarbtn_{w['id']}", use_container_width=True):
                    st.session_state[star_key] = True
                    db.mark_known(w["id"])
                    db.add_exp(3)
                    st.toast("已标熟，+3 学习值", icon="⭐")
                    st.session_state.rev_idx += 1
                    st.session_state.rev_show = False
                    st.rerun()
                if b5.button("认识", key=f"rgrade_{w['id']}_5",
                             use_container_width=True):
                    grade = 5
                if b3.button("模糊", key=f"rgrade_{w['id']}_3",
                             use_container_width=True):
                    grade = 3
                if b1.button("不认识", key=f"rgrade_{w['id']}_1",
                             use_container_width=True):
                    grade = 1
                st.markdown('</div>', unsafe_allow_html=True)

                if grade is not None:
                    n, interval, ef, lapse, delta = sm2.next_review(
                        w["n"], w["interval"], w["ef"], grade)
                    next_date = sm2.due_date_str(delta)
                    db.update_after_grade(w["id"], n, interval, ef, w["lapses"] + lapse, next_date)
                    db.log_study(w["id"], "review", 1 if grade >= 3 else 0, grade)
                    db.add_exp(1)
                    tip = {5: "记得很牢，拉长复习间隔", 3: "有点模糊，提前复习",
                           1: "忘了，缩短间隔重新记"}[grade]
                    st.toast(f"{tip}｜下次：{next_date}", icon="📅")
                    st.session_state.rev_idx += 1
                    st.session_state.rev_show = False
                    st.rerun()
        else:
            st.success("✅ 复习完成！")


# ==================== 单词自查 ====================
elif st.session_state.page == "quiz":
    st.markdown("## 单词自查")
    all_words = db.get_words(book_id)
    if len(all_words) < 4:
        st.info("词量太少，无法出题。")
    else:
        if "quiz_word" not in st.session_state or st.session_state.get("quiz_reset"):
            st.session_state.quiz_word = random.choice(all_words)
            pool = [w for w in all_words if w["id"] != st.session_state.quiz_word["id"]]
            opts = random.sample(pool, 3) + [st.session_state.quiz_word]
            random.shuffle(opts)
            st.session_state.quiz_opts = opts
            st.session_state.quiz_reset = False
            st.session_state.quiz_answered = False
            st.session_state.quiz_choice = None

        qw = st.session_state.quiz_word
        _, mc, _ = st.columns([1, 3, 1])
        with mc:
            st.markdown(f'<div class="big-word">{qw["word"]}</div>', unsafe_allow_html=True)
            if st.button(f"🔊  {qw['phonetic'] or ''}", key=f"qzbtn_{qw['id']}",
                         use_container_width=True):
                p = tts.speak(qw["word"], lang)
                if p:
                    with open(p, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    st.markdown(
                        f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>',
                        unsafe_allow_html=True)
            st.caption("点选你认为正确的释义：")

            for i, opt in enumerate(st.session_state.quiz_opts):
                label = f"{opt['pos'] or ''}. {opt['meaning']}"
                if st.session_state.quiz_answered:
                    if opt["id"] == qw["id"]:
                        st.markdown(f'<div class="quiz-btn quiz-correct">✅ {label}<div class="opt-word">对应单词：{opt["word"]}</div></div>',
                                    unsafe_allow_html=True)
                    elif opt["id"] == st.session_state.quiz_choice:
                        st.markdown(f'<div class="quiz-btn quiz-wrong">❌ {label}<div class="opt-word">对应单词：{opt["word"]}</div></div>',
                                    unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="quiz-btn">{label}</div>', unsafe_allow_html=True)
                else:
                    if st.button(label, key=f"opt_{opt['id']}_{i}", use_container_width=True):
                        st.session_state.quiz_choice = opt["id"]
                        st.session_state.quiz_answered = True
                        if opt["id"] == qw["id"]:
                            db.log_study(qw["id"], "quiz", 1, 5)
                            db.add_exp(2)
                            st.balloons()
                        else:
                            db.log_study(qw["id"], "quiz", 0, 1)
                        st.rerun()

            if st.session_state.quiz_answered:
                if st.session_state.quiz_choice == qw["id"]:
                    st.success("✅ 回答正确！+2 学习值")
                else:
                    st.error(f"正确答案：{qw['pos']}. {qw['meaning']}（{qw['word']}）")
                st.markdown('<div class="center-btn">', unsafe_allow_html=True)
                if st.button("下一题 ➡", type="primary", use_container_width=True):
                    st.session_state.quiz_reset = True
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)


# ==================== 单词查询 ====================
elif st.session_state.page == "lookup":
    st.markdown("## 🔍 单词查询")
    st.caption("输入任意单词，查看释义、音标、发音与例句")
    q = st.text_input("输入单词", key="lookup_input", placeholder="例如：abandon")
    if q:
        q = q.strip().lower()
        # 先在当前词书里找
        hit = None
        for w in db.get_words(book_id):
            if (w["word"] or "").lower() == q:
                hit = w
                break
        if hit:
            word_text = hit["word"]
            phon = hit["phonetic"] or ""
            pos = hit["pos"] or ""
            meaning = hit["meaning"] or ""
            syn = hit["synonyms"] or "暂无"
            deriv = hit["derivatives"] or "暂无"
        else:
            word_text = q
            phon, pos, meaning, syn, deriv = "", "", "", "暂无", "暂无"
            # 用百度翻译查意思
            try:
                zh = translator.translate(q, lang, "zh")
                if zh:
                    meaning = zh
            except Exception:
                pass

        _, mc, _ = st.columns([1, 3, 1])
        with mc:
            st.markdown(f'<div class="big-word">{word_text}</div>', unsafe_allow_html=True)
            if st.button(f"🔊  {phon}", key=f"lk_{word_text}", use_container_width=True):
                p = tts.speak(word_text, lang)
                if p:
                    with open(p, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    st.markdown(
                        f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>',
                        unsafe_allow_html=True)

            if meaning:
                st.markdown(f'<div class="meaning-box"><b>{pos}.</b> {meaning}</div>',
                            unsafe_allow_html=True)
            en_ex, zh_ex = get_example(word_text, pos, lang)
            if en_ex:
                exl, exr = st.columns([5, 1])
                with exl:
                    st.markdown(f'<div class="example-box">📖 {en_ex}<br>　　{zh_ex}</div>',
                                unsafe_allow_html=True)
                with exr:
                    speaker(en_ex, f"lke_{word_text}", small=True)
            c1, c2 = st.columns(2)
            c1.markdown(f'<div class="meta-row">🔗 <b>同义词</b>：{syn}</div>',
                        unsafe_allow_html=True)
            c2.markdown(f'<div class="meta-row">🌱 <b>派生词</b>：{deriv}</div>',
                        unsafe_allow_html=True)


# ==================== 统计 ====================
elif st.session_state.page == "stats":
    st.markdown("## 我的数据")
    today_n = db.get_today_count()
    total_learned = db.get_total_learned()

    m1, m2 = st.columns(2)
    m1.markdown(f"""
    <div class="nav-card">
        <div class="nav-emoji">📚</div>
        <div class="nav-title">{today_n}</div>
        <div class="nav-sub">今日学习&复习（词）</div>
    </div>""", unsafe_allow_html=True)
    m2.markdown(f"""
    <div class="nav-card">
        <div class="nav-emoji">🏆</div>
        <div class="nav-title">{total_learned}</div>
        <div class="nav-sub">累计学习（词）</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown("### 签到日历")
    checked_dates = db.get_checkin_dates()
    streak = db._calc_streak(db.get_conn(), "default")
    st.caption(f"连续签到 {streak} 天 | 学习值 {exp}")

    today = date.today()
    days = [(today - timedelta(days=i)) for i in range(13, -1, -1)]
    cols = st.columns(14)
    for i, d in enumerate(days):
        is_checked = d.isoformat() in checked_dates
        bg = "#ff7a1a" if is_checked else "#e8eef5"
        fg = "#fff" if is_checked else "#999"
        cols[i].markdown(
            f"<div style='background:{bg};color:{fg};border-radius:50%;width:44px;height:44px;"
            f"line-height:44px;text-align:center;font-weight:700;margin:auto'>{d.day}</div>"
            f"<div style='text-align:center;font-size:11px;color:#aaa'>{d.strftime('%a')}</div>",
            unsafe_allow_html=True)

    st.markdown("")
    history = db.get_history(14)
    if history:
        df = pd.DataFrame([dict(r) for r in history])
        df["正确率"] = (df["right_n"] / df["total"] * 100).round(1)
        plot_df = df.rename(columns={
            "learn_n": "学习数", "review_n": "复习数", "total": "答题数"})
        fig = px.line(plot_df, x="date",
                      y=["学习数", "复习数", "答题数", "正确率"],
                      markers=True, title="近14天学习统计",
                      labels={"date": "日期", "value": "数量/百分比", "variable": "指标"})
        st.plotly_chart(fig, use_container_width=True)


# ==================== 设置 ====================
elif st.session_state.page == "settings":
    st.markdown("## 学习设置")
    st.markdown("### 学习量")
    new_n = st.number_input("每组学习单词数量", 5, 50, int(settings["new_per_day"]))
    rev_n = st.number_input("每组复习单词数量", 20, 200, int(settings["review_per_day"]))
    st.markdown("### 发音设置")
    accent = st.selectbox("单词发音类型", ["英式", "美式"], index=0 if settings["accent"] == "英" else 1)
    auto = st.toggle("自动发音（单词+例句自动播放）", value=settings["auto_play"] == "on")
    st.markdown("### 题型设置")
    quiz = st.toggle("听音选义题型", value=settings["quiz_type"] == "on")

    if st.button("保存设置", type="primary"):
        db.save_setting("new_per_day", new_n)
        db.save_setting("review_per_day", rev_n)
        db.save_setting("accent", "英" if accent == "英式" else "美")
        db.save_setting("auto_play", "on" if auto else "off")
        db.save_setting("quiz_type", "on" if quiz else "off")
        st.toast("设置已保存", icon="✅")
        st.rerun()
