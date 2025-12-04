"""
Bridge for Restaurants - 外国人対応AIアプリ
言葉の壁を0秒で壊す、飲食店の新常識
"""

import streamlit as st
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "bridge.db"
DB_PATH.parent.mkdir(exist_ok=True)

# Page config
st.set_page_config(
    page_title="Bridge for Restaurants",
    page_icon="🍽️",
    layout="wide"
)

# ===========================================
# Database Functions
# ===========================================
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # Staff calls table
    c.execute('''CREATE TABLE IF NOT EXISTS staff_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id TEXT NOT NULL,
        call_type TEXT NOT NULL,
        message TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        responded_at TIMESTAMP
    )''')

    # Usage logs table
    c.execute('''CREATE TABLE IF NOT EXISTS usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        phrase_ja TEXT,
        phrase_category TEXT,
        language TEXT,
        table_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

def log_usage(action: str, phrase_ja: str = None, phrase_category: str = None, language: str = None, table_id: str = None):
    """Log usage data"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('''INSERT INTO usage_logs (action, phrase_ja, phrase_category, language, table_id)
                     VALUES (?, ?, ?, ?, ?)''', (action, phrase_ja, phrase_category, language, table_id))
        conn.commit()
        conn.close()
    except Exception as e:
        pass  # Silent fail for logging

def call_staff(table_id: str, call_type: str, message: str = None):
    """Create a staff call notification"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('''INSERT INTO staff_calls (table_id, call_type, message)
                     VALUES (?, ?, ?)''', (table_id, call_type, message))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

# Initialize database
init_db()

# ===========================================
# Initialize providers (cached)
# ===========================================
@st.cache_resource
def get_kimi():
    from llm import KimiLLM
    return KimiLLM()

@st.cache_resource
def get_tts():
    from tts import ElevenLabsTTS
    return ElevenLabsTTS()

@st.cache_resource
def get_stt():
    from stt import WhisperSTT
    return WhisperSTT()

# ===========================================
# 20 Essential Restaurant Phrases (基本フレーズ)
# ===========================================
QUICK_PHRASES = [
    # Customer Call (お客様用)
    {"ja": "すみません！", "romaji": "Sumimasen!", "icon": "🙋", "category": "call",
     "en": "Excuse me!", "zh": "不好意思！", "vi": "Xin lỗi!", "ne": "माफ गर्नुहोस्!"},
    {"ja": "お会計お願いします", "romaji": "Okaikei onegaishimasu", "icon": "💰", "category": "payment",
     "en": "Check please", "zh": "结账", "vi": "Tính tiền", "ne": "बिल दिनुहोस्"},
    {"ja": "トイレはどこですか？", "romaji": "Toire wa doko desu ka?", "icon": "🚻", "category": "question",
     "en": "Where is the restroom?", "zh": "厕所在哪里？", "vi": "Nhà vệ sinh ở đâu?", "ne": "शौचालय कहाँ छ?"},
    {"ja": "カードは使えますか？", "romaji": "Kaado wa tsukaemasu ka?", "icon": "💳", "category": "payment",
     "en": "Can I use a card?", "zh": "可以刷卡吗？", "vi": "Có thể dùng thẻ không?", "ne": "कार्ड चल्छ?"},
    {"ja": "おすすめは何ですか？", "romaji": "Osusume wa nan desu ka?", "icon": "⭐", "category": "order",
     "en": "What do you recommend?", "zh": "推荐什么？", "vi": "Món nào ngon?", "ne": "के सिफारिस गर्नुहुन्छ?"},
    {"ja": "これをください", "romaji": "Kore wo kudasai", "icon": "👆", "category": "order",
     "en": "I'll have this", "zh": "我要这个", "vi": "Cho tôi cái này", "ne": "यो दिनुहोस्"},
    {"ja": "水をください", "romaji": "Mizu wo kudasai", "icon": "💧", "category": "order",
     "en": "Water please", "zh": "请给我水", "vi": "Cho tôi nước", "ne": "पानी दिनुहोस्"},
    {"ja": "メニューをください", "romaji": "Menyuu wo kudasai", "icon": "📋", "category": "order",
     "en": "Menu please", "zh": "请给我菜单", "vi": "Cho tôi menu", "ne": "मेनु दिनुहोस्"},
    {"ja": "アレルギーがあります", "romaji": "Arerugii ga arimasu", "icon": "⚠️", "category": "allergy",
     "en": "I have allergies", "zh": "我有过敏", "vi": "Tôi bị dị ứng", "ne": "मलाई एलर्जी छ"},
    {"ja": "辛くしないでください", "romaji": "Karaku shinaide kudasai", "icon": "🌶️", "category": "order",
     "en": "Not spicy please", "zh": "请不要辣", "vi": "Đừng cay", "ne": "पिरो नबनाउनुहोस्"},
    # Staff Phrases (スタッフ用)
    {"ja": "いらっしゃいませ", "romaji": "Irasshaimase", "icon": "🙇", "category": "greeting",
     "en": "Welcome!", "zh": "欢迎光临", "vi": "Xin chào", "ne": "स्वागत छ"},
    {"ja": "少々お待ちください", "romaji": "Shoushou omachi kudasai", "icon": "⏳", "category": "service",
     "en": "Please wait a moment", "zh": "请稍等", "vi": "Xin đợi một chút", "ne": "कृपया पर्खनुहोस्"},
    {"ja": "お待たせいたしました", "romaji": "Omatase itashimashita", "icon": "🍽️", "category": "service",
     "en": "Sorry for the wait", "zh": "让您久等了", "vi": "Xin lỗi đã để chờ", "ne": "पर्खाएकोमा माफी"},
    {"ja": "かしこまりました", "romaji": "Kashikomarimashita", "icon": "✅", "category": "service",
     "en": "Understood", "zh": "好的，明白了", "vi": "Vâng, tôi hiểu", "ne": "बुझें"},
    {"ja": "申し訳ございません", "romaji": "Moushiwake gozaimasen", "icon": "🙏", "category": "apology",
     "en": "I'm very sorry", "zh": "非常抱歉", "vi": "Tôi rất xin lỗi", "ne": "माफी चाहन्छु"},
    {"ja": "ありがとうございました", "romaji": "Arigatou gozaimashita", "icon": "🎉", "category": "farewell",
     "en": "Thank you very much", "zh": "非常感谢", "vi": "Cảm ơn rất nhiều", "ne": "धेरै धन्यवाद"},
    {"ja": "またのお越しをお待ちしております", "romaji": "Mata no okoshi wo omachi shite orimasu", "icon": "👋", "category": "farewell",
     "en": "Please come again", "zh": "欢迎下次光临", "vi": "Hẹn gặp lại", "ne": "फेरि आउनुहोस्"},
    {"ja": "こちらへどうぞ", "romaji": "Kochira e douzo", "icon": "➡️", "category": "service",
     "en": "This way please", "zh": "这边请", "vi": "Mời đi lối này", "ne": "यता आउनुहोस्"},
    {"ja": "ご注文はお決まりですか？", "romaji": "Go-chuumon wa okimari desu ka?", "icon": "📝", "category": "order",
     "en": "Ready to order?", "zh": "您要点什么？", "vi": "Quý khách gọi món?", "ne": "अर्डर तयार?"},
    {"ja": "以上でよろしいですか？", "romaji": "Ijou de yoroshii desu ka?", "icon": "✔️", "category": "order",
     "en": "Will that be all?", "zh": "就这些吗？", "vi": "Còn gì khác không?", "ne": "यति मात्र?"},
]

# Supported languages with auto-detection mapping
LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸", "accept": ["en", "en-US", "en-GB"]},
    "zh": {"name": "中文", "flag": "🇨🇳", "accept": ["zh", "zh-CN", "zh-TW", "zh-Hans", "zh-Hant"]},
    "vi": {"name": "Tiếng Việt", "flag": "🇻🇳", "accept": ["vi", "vi-VN"]},
    "ne": {"name": "नेपाली", "flag": "🇳🇵", "accept": ["ne", "ne-NP"]},
    "ko": {"name": "한국어", "flag": "🇰🇷", "accept": ["ko", "ko-KR"]},
    "tl": {"name": "Tagalog", "flag": "🇵🇭", "accept": ["tl", "fil", "fil-PH"]},
    "id": {"name": "Bahasa", "flag": "🇮🇩", "accept": ["id", "id-ID"]},
    "th": {"name": "ไทย", "flag": "🇹🇭", "accept": ["th", "th-TH"]},
    "pt": {"name": "Português", "flag": "🇧🇷", "accept": ["pt", "pt-BR", "pt-PT"]},
    "es": {"name": "Español", "flag": "🇪🇸", "accept": ["es", "es-ES", "es-MX"]},
}

# UI Text translations
UI_TEXT = {
    "en": {
        "app_title": "Bridge for Restaurants",
        "tagline": "Break the language barrier in 0 seconds",
        "select_language": "Your Language",
        "table_number": "Table Number",
        "mode_quick": "Quick Phrases",
        "mode_call": "Call Staff",
        "mode_practice": "Practice",
        "mode_translate": "Translate",
        "call_staff": "Call Staff",
        "call_sent": "Staff has been notified!",
        "speak": "Speak",
        "listen": "Listen",
        "translate": "Translate",
        "your_try": "Now you try!",
        "good_job": "Great job!",
        "try_again": "Try again",
    },
    "zh": {
        "app_title": "Bridge 餐厅助手",
        "tagline": "0秒打破语言障碍",
        "select_language": "您的语言",
        "table_number": "桌号",
        "mode_quick": "快捷短语",
        "mode_call": "呼叫服务员",
        "mode_practice": "练习",
        "mode_translate": "翻译",
        "call_staff": "呼叫服务员",
        "call_sent": "已通知服务员！",
        "speak": "说",
        "listen": "听",
        "translate": "翻译",
        "your_try": "你来试试！",
        "good_job": "做得好！",
        "try_again": "再试一次",
    },
    "vi": {
        "app_title": "Bridge Nhà Hàng",
        "tagline": "Phá vỡ rào cản ngôn ngữ trong 0 giây",
        "select_language": "Ngôn ngữ của bạn",
        "table_number": "Số bàn",
        "mode_quick": "Cụm từ nhanh",
        "mode_call": "Gọi nhân viên",
        "mode_practice": "Luyện tập",
        "mode_translate": "Dịch",
        "call_staff": "Gọi nhân viên",
        "call_sent": "Đã thông báo nhân viên!",
        "speak": "Nói",
        "listen": "Nghe",
        "translate": "Dịch",
        "your_try": "Bạn thử đi!",
        "good_job": "Tốt lắm!",
        "try_again": "Thử lại",
    },
    "ne": {
        "app_title": "Bridge रेस्टुरेन्ट",
        "tagline": "भाषाको बाधा ० सेकेन्डमा तोड्नुहोस्",
        "select_language": "तपाईंको भाषा",
        "table_number": "टेबल नम्बर",
        "mode_quick": "द्रुत वाक्यांश",
        "mode_call": "कर्मचारी बोलाउनुहोस्",
        "mode_practice": "अभ्यास",
        "mode_translate": "अनुवाद",
        "call_staff": "कर्मचारी बोलाउनुहोस्",
        "call_sent": "कर्मचारीलाई सूचित गरियो!",
        "speak": "बोल्नुहोस्",
        "listen": "सुन्नुहोस्",
        "translate": "अनुवाद",
        "your_try": "अब तपाईं प्रयास गर्नुहोस्!",
        "good_job": "राम्रो!",
        "try_again": "फेरि प्रयास",
    },
}

# Add fallback for missing languages
for lang_code in LANGUAGES:
    if lang_code not in UI_TEXT:
        UI_TEXT[lang_code] = UI_TEXT["en"]

# ===========================================
# Session State Initialization
# ===========================================
def init_session_state():
    defaults = {
        "lang": "en",
        "table_id": "1",
        "mode": "quick",  # quick, call, practice, translate
        "audio_data": None,
        "selected_phrase": None,
        "translation_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Auto-detect language from URL params
    params = st.query_params
    if "lang" in params and params["lang"] in LANGUAGES:
        st.session_state.lang = params["lang"]
    if "table" in params:
        st.session_state.table_id = params["table"]
    if "mode" in params and params["mode"] in ["quick", "call", "practice", "translate"]:
        st.session_state.mode = params["mode"]

init_session_state()

def get_ui(key: str) -> str:
    """Get UI text in user's language"""
    lang = st.session_state.lang
    return UI_TEXT.get(lang, UI_TEXT["en"]).get(key, key)

def get_phrase_translation(phrase: dict, lang: str) -> str:
    """Get phrase in specified language"""
    return phrase.get(lang, phrase.get("en", phrase["ja"]))

# ===========================================
# Auto Language Detection (JavaScript)
# ===========================================
def inject_language_detection():
    """Inject JavaScript to detect browser language"""
    st.components.v1.html("""
    <script>
        const browserLang = navigator.language || navigator.userLanguage;
        const urlParams = new URLSearchParams(window.location.search);
        if (!urlParams.has('lang')) {
            const langCode = browserLang.split('-')[0];
            const supportedLangs = ['en', 'zh', 'vi', 'ne', 'ko', 'tl', 'id', 'th', 'pt', 'es'];
            if (supportedLangs.includes(langCode)) {
                urlParams.set('lang', langCode);
                window.location.search = urlParams.toString();
            }
        }
    </script>
    """, height=0)

# Inject language detection on first load
if "lang_detected" not in st.session_state:
    inject_language_detection()
    st.session_state.lang_detected = True

# ===========================================
# Main UI
# ===========================================

# Sidebar
with st.sidebar:
    st.title("🍽️ Bridge")
    st.caption(get_ui("tagline"))

    st.divider()

    # Language selection
    st.subheader(get_ui("select_language"))
    lang_options = {code: f"{info['flag']} {info['name']}" for code, info in LANGUAGES.items()}
    selected_lang = st.selectbox(
        "Language",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(st.session_state.lang),
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state.lang:
        st.session_state.lang = selected_lang
        st.query_params["lang"] = selected_lang
        log_usage("language_change", language=selected_lang)
        st.rerun()

    # Table number
    st.subheader(get_ui("table_number"))
    table_id = st.text_input("Table", value=st.session_state.table_id, label_visibility="collapsed")
    if table_id != st.session_state.table_id:
        st.session_state.table_id = table_id
        st.query_params["table"] = table_id

    st.divider()

    # Mode selection
    mode_options = {
        "quick": f"⚡ {get_ui('mode_quick')}",
        "call": f"🔔 {get_ui('mode_call')}",
        "practice": f"📚 {get_ui('mode_practice')}",
        "translate": f"🌐 {get_ui('mode_translate')}",
    }
    selected_mode = st.radio(
        "Mode",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        index=list(mode_options.keys()).index(st.session_state.mode),
        label_visibility="collapsed"
    )
    if selected_mode != st.session_state.mode:
        st.session_state.mode = selected_mode
        st.query_params["mode"] = selected_mode
        st.rerun()

# Main content
st.title(get_ui("app_title"))

if st.session_state.mode == "quick":
    # ===========================================
    # Quick Phrases Mode (20基本フレーズ)
    # ===========================================
    st.info(f"⚡ {get_ui('mode_quick')} - Tap to speak instantly!")

    # Group phrases by category
    categories = {}
    for phrase in QUICK_PHRASES:
        cat = phrase["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(phrase)

    # Display phrases in grid
    for cat_name, phrases in categories.items():
        cols = st.columns(min(len(phrases), 4))
        for i, phrase in enumerate(phrases):
            with cols[i % 4]:
                btn_label = f"{phrase['icon']} {get_phrase_translation(phrase, st.session_state.lang)}"
                if st.button(btn_label, key=f"phrase_{phrase['ja']}", use_container_width=True):
                    st.session_state.selected_phrase = phrase
                    log_usage("phrase_tap", phrase["ja"], cat_name, st.session_state.lang, st.session_state.table_id)
                    # Generate TTS
                    try:
                        tts = get_tts()
                        audio_data = tts.generate_speech(phrase['ja'], voice_id=os.getenv("ELEVENLABS_VOICE_ID_USER"))
                        if audio_data:
                            st.session_state.audio_data = audio_data
                    except Exception as e:
                        st.error(f"TTS Error: {e}")

    # Show selected phrase details
    if st.session_state.selected_phrase:
        phrase = st.session_state.selected_phrase
        st.divider()

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            ### 🇯🇵 {phrase['ja']}
            **Romaji:** {phrase['romaji']}

            **{LANGUAGES[st.session_state.lang]['flag']} {get_phrase_translation(phrase, st.session_state.lang)}**
            """)

        with col2:
            if st.session_state.audio_data:
                st.audio(st.session_state.audio_data, format="audio/mp3", autoplay=True)

elif st.session_state.mode == "call":
    # ===========================================
    # Call Staff Mode (店員呼び出し)
    # ===========================================
    st.info(f"🔔 {get_ui('mode_call')} - One tap to notify staff!")

    col1, col2 = st.columns(2)

    with col1:
        # Big "Sumimasen" button
        if st.button("🙋 すみません！\nExcuse me!", key="call_sumimasen", use_container_width=True):
            if call_staff(st.session_state.table_id, "call", "すみません"):
                st.success(f"✅ {get_ui('call_sent')} (Table {st.session_state.table_id})")
                log_usage("staff_call", "すみません", "call", st.session_state.lang, st.session_state.table_id)
                # Play TTS
                try:
                    tts = get_tts()
                    audio_data = tts.generate_speech("すみません！", voice_id=os.getenv("ELEVENLABS_VOICE_ID_USER"))
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3", autoplay=True)
                except:
                    pass

    with col2:
        # Bill request button
        if st.button("💰 お会計\nCheck please", key="call_bill", use_container_width=True):
            if call_staff(st.session_state.table_id, "bill", "お会計お願いします"):
                st.success(f"✅ {get_ui('call_sent')} (Table {st.session_state.table_id})")
                log_usage("staff_call", "お会計", "payment", st.session_state.lang, st.session_state.table_id)

    st.divider()

    # Other quick calls
    st.subheader("Other requests")
    call_options = [
        ("🚻 Restroom?", "toilet", "トイレはどこですか"),
        ("💧 Water", "water", "お水ください"),
        ("📋 Menu", "menu", "メニューください"),
        ("⚠️ Problem", "problem", "問題があります"),
    ]

    cols = st.columns(4)
    for i, (label, call_type, message) in enumerate(call_options):
        with cols[i]:
            if st.button(label, key=f"call_{call_type}", use_container_width=True):
                if call_staff(st.session_state.table_id, call_type, message):
                    st.success("✅")
                    log_usage("staff_call", message, call_type, st.session_state.lang, st.session_state.table_id)

elif st.session_state.mode == "practice":
    # ===========================================
    # Practice Mode (学習モード)
    # ===========================================
    st.info(f"📚 {get_ui('mode_practice')} - Learn & practice Japanese!")

    # Select phrase to practice
    phrase_options = {p['ja']: f"{p['icon']} {p['ja']} ({p['romaji']})" for p in QUICK_PHRASES}
    selected_ja = st.selectbox("Select phrase to practice", options=list(phrase_options.keys()),
                               format_func=lambda x: phrase_options[x])

    selected_phrase = next((p for p in QUICK_PHRASES if p['ja'] == selected_ja), None)

    if selected_phrase:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"""
            ### 🇯🇵 {selected_phrase['ja']}
            **Romaji:** {selected_phrase['romaji']}

            **{LANGUAGES[st.session_state.lang]['flag']} {get_phrase_translation(selected_phrase, st.session_state.lang)}**
            """)

        with col2:
            if st.button(f"🔊 {get_ui('listen')}", use_container_width=True):
                try:
                    tts = get_tts()
                    audio_data = tts.generate_speech(selected_phrase['ja'], voice_id=os.getenv("ELEVENLABS_VOICE_ID_USER"))
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3", autoplay=True)
                        log_usage("listen", selected_phrase['ja'], selected_phrase['category'], st.session_state.lang)
                except Exception as e:
                    st.error(f"TTS Error: {e}")

        st.divider()

        # Speech practice
        st.subheader(f"🎤 {get_ui('your_try')}")
        audio_input = st.audio_input("Record your voice", key=f"practice_{selected_ja}")

        if audio_input:
            try:
                stt = get_stt()
                spoken_text = stt.transcribe(audio_input, language="ja")
                st.markdown(f"**You said:** {spoken_text}")

                # Simple scoring
                target = selected_phrase['ja'].replace("！", "").replace("？", "")
                if target in spoken_text or spoken_text in target:
                    st.success(f"🎉 {get_ui('good_job')}")
                    log_usage("practice_success", selected_phrase['ja'], selected_phrase['category'], st.session_state.lang)
                else:
                    st.warning(f"🔄 {get_ui('try_again')}")
                    st.markdown(f"**Target:** {selected_phrase['ja']}")
                    log_usage("practice_retry", selected_phrase['ja'], selected_phrase['category'], st.session_state.lang)
            except Exception as e:
                st.error(f"STT Error: {e}")

elif st.session_state.mode == "translate":
    # ===========================================
    # Translate Mode (リアルタイム翻訳)
    # ===========================================
    st.info(f"🌐 {get_ui('mode_translate')} - Translate anything to Japanese!")

    user_input = st.text_area(
        f"Enter text in {LANGUAGES[st.session_state.lang]['name']}",
        placeholder="What do you want to say?",
        height=100
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(f"🔄 {get_ui('translate')}", use_container_width=True, type="primary"):
            if user_input:
                try:
                    kimi = get_kimi()
                    lang_name = LANGUAGES[st.session_state.lang]["name"]

                    prompt = f"""Translate to polite Japanese (keigo) for restaurant use:
Input ({lang_name}): {user_input}

Respond in JSON: {{"japanese": "...", "romaji": "...", "explanation": "brief {lang_name} explanation"}}"""

                    response = kimi.generate(prompt, system_prompt="You are a Japanese restaurant language expert. Respond only in valid JSON.")

                    import re
                    json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        st.session_state.translation_result = result
                        log_usage("translate", result.get("japanese"), "translate", st.session_state.lang, st.session_state.table_id)
                except Exception as e:
                    st.error(f"Translation Error: {e}")

    if st.session_state.translation_result:
        result = st.session_state.translation_result
        st.divider()

        st.markdown(f"""
        ### 🇯🇵 {result.get('japanese', '')}
        **Romaji:** {result.get('romaji', '')}

        *{result.get('explanation', '')}*
        """)

        with col2:
            if st.button(f"🔊 Speak", use_container_width=True):
                try:
                    tts = get_tts()
                    audio_data = tts.generate_speech(result.get('japanese', ''), voice_id=os.getenv("ELEVENLABS_VOICE_ID_USER"))
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3", autoplay=True)
                except Exception as e:
                    st.error(f"TTS Error: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8em;">
    Bridge for Restaurants - 言葉の壁を0秒で壊す<br>
    <a href="/dashboard/" target="_blank">Staff Dashboard</a>
</div>
""", unsafe_allow_html=True)
