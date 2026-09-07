import random
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from supabase import create_client
except Exception:
    create_client = None

st.set_page_config(page_title="けいさんクエスト", page_icon="🧮", layout="centered")

# GitHubへ全ファイルをそのままドラッグ＆ドロップできる「フラット版」。
# app.py と creatures.csv / wavファイルを同じ階層に置く。
BASE_DIR = Path(__file__).resolve().parent

CATALOG_FILE = BASE_DIR / "creatures.csv"
LOCAL_RESULTS_FILE = BASE_DIR / "results.csv"
LOCAL_COLLECTION_FILE = BASE_DIR / "collection.csv"

CORRECT_SOUND = BASE_DIR / "correct.wav"
WRONG_SOUND = BASE_DIR / "wrong.wav"
RARE_SOUND = BASE_DIR / "rare.wav"
PERFECT_SOUND = BASE_DIR / "perfect.wav"

QUESTION_COUNT = 10
AUTO_NEXT_SECONDS = 1.05

RARITY_LABEL = {
    "COMMON": "★",
    "RARE": "★★",
    "SUPER RARE": "★★★",
    "LEGEND": "★★★★",
}

st.markdown("""
<style>
.block-container{max-width:760px;padding-top:.7rem;padding-bottom:2rem}
.hero{text-align:center}
.question{font-size:clamp(3.4rem,13vw,5.6rem);font-weight:900;text-align:center;
padding:1rem;border-radius:24px;background:rgba(128,128,128,.08);margin:.6rem 0}
.feedback-ok,.feedback-ng{text-align:center;border-radius:24px;padding:1rem;margin:.4rem 0;animation:pop .3s ease}
.feedback-ok{background:rgba(46,204,113,.16);border:4px solid rgba(46,204,113,.65)}
.feedback-ng{background:rgba(231,76,60,.13);border:4px solid rgba(231,76,60,.58)}
.feedback-symbol{font-size:4.5rem}.feedback-main{font-size:1.9rem;font-weight:900}
.creature-card{text-align:center;border:2px solid rgba(128,128,128,.25);border-radius:18px;padding:.65rem;min-height:145px}
.creature-emoji{font-size:3.1rem}.locked{filter:grayscale(1);opacity:.35}
.new-creature{text-align:center;border-radius:24px;padding:1rem;background:rgba(255,193,7,.16);
border:4px solid rgba(255,193,7,.6);animation:pop .35s ease}
.new-emoji{font-size:4.2rem}.new-title{font-size:1.35rem;font-weight:900}
div.stButton>button,div[data-testid="stFormSubmitButton"]>button{
width:100%;min-height:3.6rem;font-size:1.2rem;font-weight:800;border-radius:16px}
div[data-testid="stNumberInput"] input{font-size:2rem;text-align:center;min-height:3.4rem}
@keyframes pop{0%{transform:scale(.72);opacity:.25}75%{transform:scale(1.05)}100%{transform:scale(1)}}
</style>
""", unsafe_allow_html=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_catalog():
    """生き物図鑑CSVを読み込む。

    Streamlit Cloudでファイル配置を間違えても、原因が分かるメッセージを出す。
    """
    if not CATALOG_FILE.exists():
        st.error(
            "生き物図鑑ファイルが見つからない。"
            f"\n\n探した場所：`{CATALOG_FILE}`"
            "\n\nGitHubで `creatures.csv` が app.py と同じ階層にあるか確認してほしい。"
        )
        st.stop()

    try:
        df = pd.read_csv(CATALOG_FILE, dtype={"id": str})
        df["id"] = df["id"].astype(str).str.zfill(3)
        return df
    except Exception as e:
        st.error(f"生き物図鑑ファイルの読み込みに失敗した：{e}")
        st.stop()

@st.cache_resource
def get_supabase():
    if create_client is None:
        return None
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None

def using_supabase():
    return get_supabase() is not None

# ---------- Results ----------
RESULT_COLUMNS = [
    "played_at","player","level","correct_count","question_count",
    "accuracy","total_time","average_time","best_time"
]

def load_results():
    sb = get_supabase()
    if sb:
        try:
            data = sb.table("results").select("*").order("played_at", desc=True).execute().data
            return pd.DataFrame(data) if data else pd.DataFrame(columns=RESULT_COLUMNS)
        except Exception as e:
            st.warning(f"Supabaseから結果を読めなかったためローカル表示に切り替えた。{e}")
    if LOCAL_RESULTS_FILE.exists():
        try:
            return pd.read_csv(LOCAL_RESULTS_FILE)
        except Exception:
            pass
    return pd.DataFrame(columns=RESULT_COLUMNS)

def save_result(row):
    sb = get_supabase()
    if sb:
        try:
            sb.table("results").insert(row).execute()
            return
        except Exception as e:
            st.warning(f"Supabaseへの結果保存に失敗したためローカル保存に切り替えた。{e}")
    df = load_local_results()
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(LOCAL_RESULTS_FILE, index=False)

def load_local_results():
    if LOCAL_RESULTS_FILE.exists():
        try:
            return pd.read_csv(LOCAL_RESULTS_FILE)
        except Exception:
            pass
    return pd.DataFrame(columns=RESULT_COLUMNS)

# ---------- Collection ----------
COLLECTION_COLUMNS = ["player","creature_id","count","first_acquired","last_acquired"]

def load_collection():
    sb = get_supabase()
    if sb:
        try:
            data = sb.table("collections").select("*").execute().data
            df = pd.DataFrame(data) if data else pd.DataFrame(columns=COLLECTION_COLUMNS)
            if not df.empty:
                df["creature_id"] = df["creature_id"].astype(str).str.zfill(3)
            return df
        except Exception as e:
            st.warning(f"Supabaseから図鑑を読めなかったためローカル表示に切り替えた。{e}")
    if LOCAL_COLLECTION_FILE.exists():
        try:
            df = pd.read_csv(LOCAL_COLLECTION_FILE, dtype={"creature_id": str})
            df["creature_id"] = df["creature_id"].astype(str).str.zfill(3)
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=COLLECTION_COLUMNS)

def add_creature(player, creature_id):
    creature_id = str(creature_id).zfill(3)
    sb = get_supabase()

    if sb:
        try:
            existing = (
                sb.table("collections")
                .select("*")
                .eq("player", player)
                .eq("creature_id", creature_id)
                .execute()
                .data
            )
            if existing:
                row = existing[0]
                new_count = int(row.get("count", 1)) + 1
                sb.table("collections").update({
                    "count": new_count,
                    "last_acquired": now_iso()
                }).eq("id", row["id"]).execute()
                return False
            else:
                sb.table("collections").insert({
                    "player": player,
                    "creature_id": creature_id,
                    "count": 1,
                    "first_acquired": now_iso(),
                    "last_acquired": now_iso()
                }).execute()
                return True
        except Exception as e:
            st.warning(f"Supabaseへの図鑑保存に失敗したためローカル保存に切り替えた。{e}")

    return add_creature_local(player, creature_id)

def add_creature_local(player, creature_id):
    df = load_local_collection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mask = (df["player"] == player) & (df["creature_id"].astype(str).str.zfill(3) == creature_id)
    is_new = not mask.any()
    if is_new:
        row = {
            "player": player, "creature_id": creature_id, "count": 1,
            "first_acquired": now, "last_acquired": now
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df.loc[mask, "count"] = pd.to_numeric(df.loc[mask, "count"], errors="coerce").fillna(0) + 1
        df.loc[mask, "last_acquired"] = now
    df.to_csv(LOCAL_COLLECTION_FILE, index=False)
    return is_new

def load_local_collection():
    if LOCAL_COLLECTION_FILE.exists():
        try:
            df = pd.read_csv(LOCAL_COLLECTION_FILE, dtype={"creature_id": str})
            df["creature_id"] = df["creature_id"].astype(str).str.zfill(3)
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=COLLECTION_COLUMNS)

# ---------- Creature draw ----------
def choose_creature(elapsed, combo, perfect_bonus=False):
    catalog = load_catalog()
    weights = {"COMMON":76,"RARE":19,"SUPER RARE":4,"LEGEND":1}
    if elapsed < 2.0:
        weights = {"COMMON":65,"RARE":25,"SUPER RARE":8,"LEGEND":2}
    if combo >= 3:
        weights = {"COMMON":55,"RARE":30,"SUPER RARE":12,"LEGEND":3}
    if combo >= 5:
        weights = {"COMMON":42,"RARE":34,"SUPER RARE":18,"LEGEND":6}
    if perfect_bonus:
        weights = {"COMMON":0,"RARE":55,"SUPER RARE":35,"LEGEND":10}
    rarity = random.choices(list(weights), weights=list(weights.values()), k=1)[0]
    return catalog[catalog["rarity"] == rarity].sample(1).iloc[0].to_dict()

# ---------- Audio ----------
def play_audio(path):
    if st.session_state.sound_on and path.exists():
        st.audio(str(path), autoplay=True)

def sound_fallback(path):
    if st.session_state.sound_on and st.session_state.show_sound_fallback and path.exists():
        st.caption("Safariで音が出ない場合は▶をタップ")
        st.audio(str(path), autoplay=False)

# ---------- State ----------
def init_state():
    defaults = {
        "game_started":False,"game_finished":False,"question_no":1,"score":0,
        "combo":0,"max_combo":0,"times":[],"a":None,"b":3,"question_started_at":None,
        "saved_result":False,"player":"チャレンジャー","sound_on":True,
        "show_sound_fallback":False,
        "last_creature":None,
        "last_creature_is_new":False,
        "show_book_home":False,
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def new_question():
    st.session_state.a = random.randint(1,10)
    st.session_state.question_started_at = time.perf_counter()

def start_game(player, level):
    st.session_state.player = player.strip() or "チャレンジャー"
    st.session_state.b = level
    st.session_state.game_started = True
    st.session_state.game_finished = False
    st.session_state.question_no = 1
    st.session_state.score = 0
    st.session_state.combo = 0
    st.session_state.max_combo = 0
    st.session_state.times = []
    st.session_state.saved_result = False
    st.session_state.last_creature = None
    st.session_state.last_creature_is_new = False
    new_question()

def reset():
    sound = st.session_state.get("sound_on", True)
    fallback = st.session_state.get("show_sound_fallback", False)
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.session_state.sound_on = sound
    st.session_state.show_sound_fallback = fallback
    st.rerun()

init_state()
catalog = load_catalog()

def render_collection(player_name, key_prefix="book"):
    collection = load_collection()
    mine = collection[collection["player"] == player_name].copy() if not collection.empty else collection
    owned = set(mine["creature_id"].astype(str).str.zfill(3).tolist()) if not mine.empty else set()

    st.metric("見つけた生き物", f"{len(owned)} / {len(catalog)}")
    st.progress(len(owned) / len(catalog))

    rarity_filter = st.selectbox(
        "レア度",
        ["すべて", "COMMON", "RARE", "SUPER RARE", "LEGEND"],
        key=f"{key_prefix}_rarity_filter",
    )
    view = catalog if rarity_filter == "すべて" else catalog[catalog["rarity"] == rarity_filter]

    cols = st.columns(3)
    for idx, (_, r) in enumerate(view.iterrows()):
        cid = str(r["id"]).zfill(3)
        got = cid in owned
        with cols[idx % 3]:
            if got:
                count = 1
                m = mine[mine["creature_id"] == cid]
                if not m.empty:
                    count = int(pd.to_numeric(m.iloc[0]["count"], errors="coerce") or 1)
                st.markdown(
                    f"<div class='creature-card'><div class='creature-emoji'>{r['emoji']}</div>"
                    f"<b>{r['name']}</b><br>{RARITY_LABEL[r['rarity']]} {r['rarity']}<br>"
                    f"<small>{r['group']} / ×{count}</small></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='creature-card locked'><div class='creature-emoji'>❓</div>"
                    f"<b>？？？</b><br>{RARITY_LABEL[r['rarity']]} {r['rarity']}<br>"
                    f"<small>{r['group']}</small></div>",
                    unsafe_allow_html=True,
                )

tab_game, tab_book, tab_record = st.tabs(["🎮 けいさん", "📚 いきもの図鑑", "🏆 きろく"])

with tab_book:
    player_for_book = st.text_input(
        "図鑑を見る人",
        value=st.session_state.player,
        key="book_player",
    )
    render_collection(player_for_book, key_prefix="tab_book")

with tab_record:
    player_for_record = st.text_input("記録を見る人", value=st.session_state.player, key="record_player")
    results = load_results()
    mine_results = results[results["player"] == player_for_record].copy() if not results.empty else results
    if mine_results.empty:
        st.info("まだ記録がないよ。")
    else:
        mine_results["level"] = pd.to_numeric(mine_results["level"], errors="coerce")
        mine_results["total_time"] = pd.to_numeric(mine_results["total_time"], errors="coerce")
        mine_results["accuracy"] = pd.to_numeric(mine_results["accuracy"], errors="coerce")
        st.subheader("自己ベスト")
        perfect = mine_results[mine_results["correct_count"] == QUESTION_COUNT].copy()
        if perfect.empty:
            st.write("まだPERFECT記録はないよ。")
        else:
            bests = perfect.sort_values("total_time").groupby("level", as_index=False).first()
            show = bests[["level","total_time","average_time","played_at"]].copy()
            show.columns = ["＋レベル","合計タイム","平均タイム","日時"]
            st.dataframe(show, use_container_width=True, hide_index=True)

        st.subheader("最近の記録")
        recent = mine_results.sort_values("played_at", ascending=False).head(20)
        st.dataframe(
            recent[["played_at","level","correct_count","accuracy","total_time","average_time"]],
            use_container_width=True,
            hide_index=True
        )

with tab_game:
    st.markdown(
        "<div class='hero'><h1>🧮 けいさんクエスト</h1>"
        "<p>せいかいして いきものを あつめよう！</p></div>",
        unsafe_allow_html=True
    )

    storage_text = "☁️ Supabase保存中" if using_supabase() else "💾 ローカル保存モード"
    st.caption(storage_text)

    if not st.session_state.game_started and not st.session_state.game_finished:
        player = st.text_input("なまえ", value=st.session_state.player, max_chars=20)
        level = st.select_slider("＋いくつ？", options=list(range(1,11)), value=3, format_func=lambda x:f"＋{x}")
        st.session_state.sound_on = st.toggle("🔊 効果音", value=st.session_state.sound_on)
        st.session_state.show_sound_fallback = st.toggle(
            "🍎 Safari用：手動再生ボタンも表示",
            value=st.session_state.show_sound_fallback,
        )

        if st.session_state.sound_on:
            with st.expander("🔊 効果音テスト"):
                st.write("Safariで下の▶を押して音が聞こえるか確認できる。")
                st.audio(str(CORRECT_SOUND), autoplay=False)

        if st.button("🔥 チャレンジ開始", type="primary"):
            start_game(player, level)
            st.rerun()

        if st.button("📚 いきもの図鑑を見る"):
            st.session_state.show_book_home = not st.session_state.show_book_home

        if st.session_state.show_book_home:
            st.divider()
            st.subheader("📚 いきもの図鑑")
            render_collection(player, key_prefix="home_book")
            st.divider()

        collection = load_collection()
        mine = collection[collection["player"] == player] if not collection.empty else collection
        found = mine["creature_id"].nunique() if not mine.empty else 0
        st.write(f"📚 **図鑑：{found} / {len(catalog)}種類 発見！**")

    elif st.session_state.game_started:
        # 前の問題で獲得した生き物を次の問題でも表示しておく。
        if st.session_state.last_creature is not None:
            c = st.session_state.last_creature
            new_text = "✨ NEW! " if st.session_state.last_creature_is_new else ""
            st.markdown(
                f"<div class='new-creature'>"
                f"<div class='new-emoji'>{c['emoji']}</div>"
                f"<div class='new-title'>前の問題でGET！ {new_text}{c['name']}</div>"
                f"{RARITY_LABEL[c['rarity']]} {c['rarity']} ／ {c['group']}"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.write(f"🔥 **＋{st.session_state.b} STAGE　{st.session_state.question_no} / {QUESTION_COUNT}**")
        st.progress(st.session_state.question_no/QUESTION_COUNT)
        c1,c2 = st.columns(2)
        c1.metric("せいかい", f"{st.session_state.score}")
        c2.metric("コンボ", f"{st.session_state.combo} 🔥")

        st.markdown(
            f"<div class='question'>{st.session_state.a} ＋ {st.session_state.b} ＝ ？</div>",
            unsafe_allow_html=True
        )

        with st.form("answer_form", clear_on_submit=True):
            answer = st.number_input(
                "こたえ", min_value=0, max_value=100, step=1, value=None,
                placeholder="こたえを入れてね", label_visibility="collapsed"
            )
            submitted = st.form_submit_button("✅ こたえる", type="primary", use_container_width=True)

        if submitted and answer is not None:
            elapsed = time.perf_counter() - st.session_state.question_started_at
            st.session_state.times.append(elapsed)
            correct = st.session_state.a + st.session_state.b
            ok = int(answer) == correct

            if ok:
                st.session_state.score += 1
                st.session_state.combo += 1
                st.session_state.max_combo = max(st.session_state.max_combo, st.session_state.combo)
                creature = choose_creature(elapsed, st.session_state.combo)
                is_new = add_creature(st.session_state.player, creature["id"])
                st.session_state.last_creature = creature
                st.session_state.last_creature_is_new = is_new

                st.markdown(
                    f"<div class='feedback-ok'><div class='feedback-symbol'>⭕</div>"
                    f"<div class='feedback-main'>せいかい！</div>⏱ {elapsed:.2f}秒</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div class='new-creature'><div class='new-emoji'>{creature['emoji']}</div>"
                    f"<div class='new-title'>{'✨ NEW! ' if is_new else ''}{creature['name']} をゲット！</div>"
                    f"{RARITY_LABEL[creature['rarity']]} {creature['rarity']} ／ {creature['group']}</div>",
                    unsafe_allow_html=True
                )
                if creature["rarity"] in ["SUPER RARE","LEGEND"]:
                    st.balloons()
                    play_audio(RARE_SOUND)
                    sound_fallback(RARE_SOUND)
                else:
                    play_audio(CORRECT_SOUND)
                    sound_fallback(CORRECT_SOUND)
            else:
                st.session_state.combo = 0
                st.session_state.last_creature = None
                st.session_state.last_creature_is_new = False
                st.markdown(
                    f"<div class='feedback-ng'><div class='feedback-symbol'>❌</div>"
                    f"<div class='feedback-main'>おしい！</div>"
                    f"{st.session_state.a} ＋ {st.session_state.b} ＝ <b>{correct}</b><br>⏱ {elapsed:.2f}秒</div>",
                    unsafe_allow_html=True
                )
                play_audio(WRONG_SOUND)
                sound_fallback(WRONG_SOUND)

            time.sleep(AUTO_NEXT_SECONDS)
            if st.session_state.question_no >= QUESTION_COUNT:
                st.session_state.game_started = False
                st.session_state.game_finished = True
            else:
                st.session_state.question_no += 1
                new_question()
            st.rerun()

    elif st.session_state.game_finished:
        times = st.session_state.times
        total = sum(times) if times else 0
        avg = total/len(times) if times else 0
        best = min(times) if times else 0
        acc = st.session_state.score/QUESTION_COUNT*100

        st.markdown("## 🏆 RESULT")

        if st.session_state.score == QUESTION_COUNT:
            st.balloons()
            bonus = choose_creature(best, st.session_state.max_combo, perfect_bonus=True)
            is_new = add_creature(st.session_state.player, bonus["id"])
            st.markdown(
                f"<div class='new-creature'><div class='new-emoji'>{bonus['emoji']}</div>"
                f"<div class='new-title'>🏆 PERFECT BONUS! {'NEW! ' if is_new else ''}{bonus['name']}</div>"
                f"{RARITY_LABEL[bonus['rarity']]} {bonus['rarity']}</div>",
                unsafe_allow_html=True
            )
            play_audio(PERFECT_SOUND)
            sound_fallback(PERFECT_SOUND)

        a,b = st.columns(2)
        a.metric("正解", f"{st.session_state.score} / {QUESTION_COUNT}")
        a.metric("正答率", f"{acc:.0f}%")
        b.metric("平均タイム", f"{avg:.2f}秒")
        b.metric("最速", f"{best:.2f}秒")
        st.metric("最大コンボ", f"{st.session_state.max_combo} 🔥")

        if not st.session_state.saved_result:
            save_result({
                "played_at": now_iso(),
                "player": st.session_state.player,
                "level": int(st.session_state.b),
                "correct_count": int(st.session_state.score),
                "question_count": QUESTION_COUNT,
                "accuracy": round(acc, 2),
                "total_time": round(total, 3),
                "average_time": round(avg, 3),
                "best_time": round(best, 3),
            })
            st.session_state.saved_result = True

        if st.button("🔁 もう一度", type="primary"):
            reset()
        if st.button("🏠 最初にもどる"):
            reset()
