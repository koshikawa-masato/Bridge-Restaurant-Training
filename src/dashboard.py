"""
Bridge Staff Dashboard - 店員用ダッシュボード
リアルタイムで呼び出し通知を確認
"""

import streamlit as st
import sqlite3
from datetime import datetime
from pathlib import Path
import time

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "bridge.db"

# Page config
st.set_page_config(
    page_title="Bridge Staff Dashboard",
    page_icon="📊",
    layout="wide"
)

# ===========================================
# Database Functions
# ===========================================
def get_pending_calls():
    """Get all pending staff calls"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('''SELECT id, table_id, call_type, message, created_at
                     FROM staff_calls
                     WHERE status = 'pending'
                     ORDER BY created_at DESC''')
        calls = c.fetchall()
        conn.close()
        return calls
    except Exception as e:
        return []

def get_recent_calls(limit=20):
    """Get recent staff calls (all statuses)"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('''SELECT id, table_id, call_type, message, status, created_at, responded_at
                     FROM staff_calls
                     ORDER BY created_at DESC
                     LIMIT ?''', (limit,))
        calls = c.fetchall()
        conn.close()
        return calls
    except Exception as e:
        return []

def respond_to_call(call_id):
    """Mark a call as responded"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('''UPDATE staff_calls
                     SET status = 'responded', responded_at = CURRENT_TIMESTAMP
                     WHERE id = ?''', (call_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_usage_stats():
    """Get usage statistics"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()

        # Total phrase taps
        c.execute("SELECT COUNT(*) FROM usage_logs WHERE action = 'phrase_tap'")
        phrase_taps = c.fetchone()[0]

        # Total translations
        c.execute("SELECT COUNT(*) FROM usage_logs WHERE action = 'translate'")
        translations = c.fetchone()[0]

        # Language distribution
        c.execute('''SELECT language, COUNT(*) as count
                     FROM usage_logs
                     WHERE language IS NOT NULL
                     GROUP BY language
                     ORDER BY count DESC''')
        languages = c.fetchall()

        # Popular phrases
        c.execute('''SELECT phrase_ja, COUNT(*) as count
                     FROM usage_logs
                     WHERE action = 'phrase_tap' AND phrase_ja IS NOT NULL
                     GROUP BY phrase_ja
                     ORDER BY count DESC
                     LIMIT 10''')
        popular_phrases = c.fetchall()

        conn.close()
        return {
            "phrase_taps": phrase_taps,
            "translations": translations,
            "languages": languages,
            "popular_phrases": popular_phrases
        }
    except Exception as e:
        return {"phrase_taps": 0, "translations": 0, "languages": [], "popular_phrases": []}

# ===========================================
# UI
# ===========================================

st.title("📊 Bridge Staff Dashboard")
st.caption("店員用管理画面 - リアルタイム呼び出し通知")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (10秒)", value=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🔔 呼び出し通知", "📈 利用統計", "📋 履歴"])

with tab1:
    st.subheader("🔔 現在の呼び出し")

    pending_calls = get_pending_calls()

    if pending_calls:
        st.warning(f"⚠️ {len(pending_calls)}件の未対応呼び出しがあります")

        for call in pending_calls:
            call_id, table_id, call_type, message, created_at = call

            # Call type icons
            type_icons = {
                "call": "🙋",
                "bill": "💰",
                "toilet": "🚻",
                "water": "💧",
                "menu": "📋",
                "problem": "⚠️",
            }
            icon = type_icons.get(call_type, "🔔")

            col1, col2, col3 = st.columns([2, 3, 1])

            with col1:
                st.markdown(f"### テーブル {table_id}")

            with col2:
                st.markdown(f"{icon} **{call_type.upper()}**")
                st.caption(f"📝 {message}")
                st.caption(f"🕐 {created_at}")

            with col3:
                if st.button("✅ 対応済み", key=f"respond_{call_id}"):
                    respond_to_call(call_id)
                    st.rerun()

            st.divider()
    else:
        st.success("✅ 現在、未対応の呼び出しはありません")
        st.info("💡 お客様が「すみません」ボタンを押すと、ここに通知が表示されます")

with tab2:
    st.subheader("📈 利用統計")

    stats = get_usage_stats()

    # Key metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("フレーズタップ", stats["phrase_taps"])

    with col2:
        st.metric("翻訳回数", stats["translations"])

    with col3:
        total = stats["phrase_taps"] + stats["translations"]
        st.metric("総利用回数", total)

    st.divider()

    # Language distribution
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🌏 言語別利用")
        if stats["languages"]:
            for lang, count in stats["languages"]:
                flag_map = {
                    "en": "🇺🇸", "zh": "🇨🇳", "vi": "🇻🇳", "ne": "🇳🇵",
                    "ko": "🇰🇷", "tl": "🇵🇭", "id": "🇮🇩", "th": "🇹🇭",
                    "pt": "🇧🇷", "es": "🇪🇸"
                }
                flag = flag_map.get(lang, "🏳️")
                st.markdown(f"{flag} **{lang}**: {count}回")
        else:
            st.caption("データがありません")

    with col2:
        st.markdown("### ⭐ 人気フレーズ TOP 10")
        if stats["popular_phrases"]:
            for i, (phrase, count) in enumerate(stats["popular_phrases"], 1):
                st.markdown(f"{i}. **{phrase}** ({count}回)")
        else:
            st.caption("データがありません")

with tab3:
    st.subheader("📋 呼び出し履歴")

    recent_calls = get_recent_calls(20)

    if recent_calls:
        for call in recent_calls:
            call_id, table_id, call_type, message, status, created_at, responded_at = call

            # Status styling
            if status == "pending":
                status_badge = "🔴 未対応"
            else:
                status_badge = "🟢 対応済み"

            col1, col2, col3 = st.columns([1, 3, 1])

            with col1:
                st.markdown(f"**テーブル {table_id}**")

            with col2:
                st.markdown(f"**{call_type}**: {message}")
                st.caption(f"📅 {created_at}")

            with col3:
                st.markdown(status_badge)
                if responded_at:
                    st.caption(f"✓ {responded_at}")

            st.divider()
    else:
        st.info("呼び出し履歴がありません")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### 🍽️ Bridge")
st.sidebar.markdown("外国人対応AIアプリ")
st.sidebar.markdown("[← お客様向けアプリ](https://bridge.three-sisters.ai/)")

# Auto-refresh
if auto_refresh:
    time.sleep(10)
    st.rerun()
