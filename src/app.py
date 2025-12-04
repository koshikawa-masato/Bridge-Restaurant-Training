"""
Bridge - Restaurant Staff Japanese Training App
外国人飲食店スタッフ向け日本語・接客トレーニングアプリ
"""

import streamlit as st
import os
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Bridge - Restaurant Training",
    page_icon="🍽️",
    layout="wide"
)

# Initialize providers (cached for performance)
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
# Restaurant Phrases Database
# ===========================================
RESTAURANT_PHRASES = {
    "greeting": {
        "title": {"ja": "挨拶", "en": "Greeting", "zh": "问候", "vi": "Chào hỏi", "ne": "अभिवादन"},
        "tips": {
            "en": "In Japan, bowing while greeting shows respect. A slight bow (15°) is appropriate for customers.",
            "zh": "在日本，鞠躬问候表示尊重。对顾客轻微鞠躬（15度）是合适的。",
            "vi": "Ở Nhật Bản, cúi chào khi chào hỏi thể hiện sự tôn trọng. Cúi nhẹ (15°) là phù hợp với khách hàng.",
            "ne": "जापानमा, अभिवादन गर्दा झुक्नुले सम्मान देखाउँछ। ग्राहकहरूको लागि हल्का झुकाइ (१५°) उपयुक्त छ।"
        },
        "phrases": [
            {"ja": "いらっしゃいませ", "romaji": "Irasshaimase", "en": "Welcome!", "zh": "欢迎光临", "vi": "Xin chào quý khách", "ne": "स्वागत छ"},
            {"ja": "何名様ですか？", "romaji": "Nan-mei-sama desu ka?", "en": "How many people?", "zh": "请问几位？", "vi": "Quý khách có mấy người?", "ne": "कति जना हुनुहुन्छ?"},
            {"ja": "こちらへどうぞ", "romaji": "Kochira e douzo", "en": "This way please", "zh": "这边请", "vi": "Mời đi lối này", "ne": "यता आउनुहोस्"},
            {"ja": "少々お待ちください", "romaji": "Shoushou omachi kudasai", "en": "Please wait a moment", "zh": "请稍等", "vi": "Xin vui lòng đợi một chút", "ne": "कृपया केही समय पर्खनुहोस्"},
        ]
    },
    "order": {
        "title": {"ja": "注文", "en": "Taking Order", "zh": "点餐", "vi": "Nhận đơn", "ne": "अर्डर"},
        "tips": {
            "en": "Japanese customers often take time to decide. Never rush them. Wait patiently until they call you.",
            "zh": "日本顾客通常需要时间做决定。不要催促他们。耐心等待直到他们叫你。",
            "vi": "Khách hàng Nhật thường mất thời gian để quyết định. Đừng bao giờ vội vàng. Hãy kiên nhẫn chờ đợi cho đến khi họ gọi bạn.",
            "ne": "जापानी ग्राहकहरूले निर्णय गर्न समय लिन्छन्। तिनीहरूलाई कहिल्यै हतार नगर्नुहोस्। तिनीहरूले बोलाउँदासम्म धैर्यपूर्वक पर्खनुहोस्।"
        },
        "phrases": [
            {"ja": "ご注文はお決まりですか？", "romaji": "Go-chuumon wa okimari desu ka?", "en": "Are you ready to order?", "zh": "请问您要点什么？", "vi": "Quý khách đã sẵn sàng gọi món chưa?", "ne": "अर्डर तयार छ?"},
            {"ja": "おすすめは〇〇です", "romaji": "Osusume wa ... desu", "en": "I recommend...", "zh": "推荐...", "vi": "Tôi khuyên dùng...", "ne": "सिफारिस छ..."},
            {"ja": "以上でよろしいですか？", "romaji": "Ijou de yoroshii desu ka?", "en": "Will that be all?", "zh": "就这些吗？", "vi": "Có còn gì khác không?", "ne": "यति मात्र हो?"},
            {"ja": "かしこまりました", "romaji": "Kashikomarimashita", "en": "Certainly / Understood", "zh": "好的，明白了", "vi": "Vâng, tôi hiểu rồi", "ne": "ठीक छ, बुझें"},
        ]
    },
    "serving": {
        "title": {"ja": "料理提供", "en": "Serving", "zh": "上菜", "vi": "Phục vụ", "ne": "खाना दिने"},
        "tips": {
            "en": "Always serve with both hands. Place dishes gently on the table. Say the dish name clearly.",
            "zh": "务必双手上菜。轻轻地将菜品放在桌上。清楚地说出菜名。",
            "vi": "Luôn phục vụ bằng cả hai tay. Đặt món ăn nhẹ nhàng lên bàn. Nói tên món rõ ràng.",
            "ne": "सधैं दुवै हातले सेवा गर्नुहोस्। थालहरू टेबलमा बिस्तारै राख्नुहोस्। खानाको नाम स्पष्ट भन्नुहोस्।"
        },
        "phrases": [
            {"ja": "お待たせいたしました", "romaji": "Omatase itashimashita", "en": "Sorry to keep you waiting", "zh": "让您久等了", "vi": "Xin lỗi đã để quý khách chờ", "ne": "पर्खाएकोमा माफी"},
            {"ja": "〇〇でございます", "romaji": "... de gozaimasu", "en": "Here is your...", "zh": "这是您的...", "vi": "Đây là món...", "ne": "यो तपाईंको..."},
            {"ja": "ごゆっくりどうぞ", "romaji": "Go-yukkuri douzo", "en": "Please enjoy / Take your time", "zh": "请慢用", "vi": "Xin mời quý khách thưởng thức", "ne": "आराम गरेर खानुहोस्"},
        ]
    },
    "payment": {
        "title": {"ja": "会計", "en": "Payment", "zh": "结账", "vi": "Thanh toán", "ne": "भुक्तानी"},
        "tips": {
            "en": "There is NO tipping culture in Japan. Do not expect or ask for tips. It may be considered rude.",
            "zh": "日本没有小费文化。不要期待或索要小费。这可能被认为是不礼貌的。",
            "vi": "Nhật Bản KHÔNG có văn hóa tip. Không mong đợi hoặc yêu cầu tiền tip. Điều này có thể bị coi là bất lịch sự.",
            "ne": "जापानमा टिप दिने संस्कृति छैन। टिपको अपेक्षा वा माग नगर्नुहोस्। यो असभ्य मानिन सक्छ।"
        },
        "phrases": [
            {"ja": "お会計は〇〇円です", "romaji": "Okaikei wa ... en desu", "en": "The total is ... yen", "zh": "一共是...日元", "vi": "Tổng cộng là ... yên", "ne": "जम्मा ... येन"},
            {"ja": "現金ですか？カードですか？", "romaji": "Genkin desu ka? Kaado desu ka?", "en": "Cash or card?", "zh": "现金还是刷卡？", "vi": "Tiền mặt hay thẻ?", "ne": "नगद वा कार्ड?"},
            {"ja": "〇〇円お預かりします", "romaji": "... en oazukari shimasu", "en": "I'll take ... yen", "zh": "收您...日元", "vi": "Tôi nhận ... yên", "ne": "... येन लिन्छु"},
            {"ja": "〇〇円のお返しです", "romaji": "... en no okaeshi desu", "en": "Here's your change, ... yen", "zh": "找您...日元", "vi": "Tiền thối lại ... yên", "ne": "फिर्ता ... येन"},
        ]
    },
    "trouble": {
        "title": {"ja": "トラブル対応", "en": "Problem Handling", "zh": "问题处理", "vi": "Xử lý sự cố", "ne": "समस्या समाधान"},
        "tips": {
            "en": "Always apologize first, even if it's not your fault. Japanese service culture prioritizes customer satisfaction above all.",
            "zh": "即使不是你的错，也要先道歉。日本服务文化把顾客满意度放在首位。",
            "vi": "Luôn xin lỗi trước, ngay cả khi không phải lỗi của bạn. Văn hóa dịch vụ Nhật Bản đặt sự hài lòng của khách hàng lên hàng đầu.",
            "ne": "तपाईंको गल्ती नभए पनि पहिले माफी माग्नुहोस्। जापानी सेवा संस्कृतिले ग्राहक सन्तुष्टिलाई सबैभन्दा माथि राख्छ।"
        },
        "phrases": [
            {"ja": "申し訳ございません", "romaji": "Moushiwake gozaimasen", "en": "I'm very sorry", "zh": "非常抱歉", "vi": "Tôi rất xin lỗi", "ne": "मलाई धेरै माफी छ"},
            {"ja": "すぐにお取り替えします", "romaji": "Sugu ni otorikae shimasu", "en": "I'll replace it right away", "zh": "马上为您更换", "vi": "Tôi sẽ đổi ngay", "ne": "तुरुन्तै साट्दिन्छु"},
            {"ja": "店長を呼んでまいります", "romaji": "Tenchou wo yonde mairimasu", "en": "I'll call the manager", "zh": "我去叫店长", "vi": "Tôi sẽ gọi quản lý", "ne": "म्यानेजर बोलाउँछु"},
            {"ja": "少々お待ちいただけますか？", "romaji": "Shoushou omachi itadakemasu ka?", "en": "Could you wait a moment?", "zh": "能稍等一下吗？", "vi": "Quý khách có thể đợi một chút không?", "ne": "केही समय पर्खिदिनु हुन्छ?"},
        ]
    },
    "farewell": {
        "title": {"ja": "お見送り", "en": "Farewell", "zh": "送别", "vi": "Tiễn khách", "ne": "विदाई"},
        "tips": {
            "en": "Bow as customers leave. Continue saying 'Arigatou gozaimashita' until they are out of sight. This shows gratitude.",
            "zh": "顾客离开时鞠躬。持续说「非常感谢」直到他们离开视线。这表示感谢。",
            "vi": "Cúi chào khi khách hàng rời đi. Tiếp tục nói 'Arigatou gozaimashita' cho đến khi họ khuất tầm nhìn. Điều này thể hiện lòng biết ơn.",
            "ne": "ग्राहकहरू जाँदा झुक्नुहोस्। तिनीहरू नदेखिएसम्म 'Arigatou gozaimashita' भन्न जारी राख्नुहोस्। यसले कृतज्ञता देखाउँछ।"
        },
        "phrases": [
            {"ja": "ありがとうございました", "romaji": "Arigatou gozaimashita", "en": "Thank you very much", "zh": "非常感谢", "vi": "Cảm ơn quý khách rất nhiều", "ne": "धेरै धन्यवाद"},
            {"ja": "またのお越しをお待ちしております", "romaji": "Mata no okoshi wo omachi shite orimasu", "en": "We look forward to seeing you again", "zh": "欢迎下次光临", "vi": "Hẹn gặp lại quý khách", "ne": "फेरि भेटौंला"},
        ]
    }
}

# Supported native languages
NATIVE_LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸"},
    "zh": {"name": "中文", "flag": "🇨🇳"},
    "vi": {"name": "Tiếng Việt", "flag": "🇻🇳"},
    "ne": {"name": "नेपाली", "flag": "🇳🇵"},
}

# UI Text translations
UI_TEXT = {
    "en": {
        "app_title": "Bridge - Restaurant Japanese Training",
        "select_language": "Your Native Language",
        "mode_practice": "Practice Mode",
        "mode_help": "Help Mode (Real-time)",
        "category": "Category",
        "phrase": "Phrase",
        "listen": "Listen",
        "speak": "Speak",
        "check": "Check Pronunciation",
        "next": "Next Phrase",
        "help_input": "What do you want to say? (in your language)",
        "translate": "Translate to Japanese",
        "speak_for_me": "Speak for me",
        "your_try": "Now you try!",
        "good_job": "Good job!",
        "try_again": "Try again",
        "practice_hint": "Learn Japanese phrases for restaurant service",
        "help_hint": "Get instant translation when you're stuck",
    },
    "zh": {
        "app_title": "Bridge - 餐厅日语培训",
        "select_language": "您的母语",
        "mode_practice": "练习模式",
        "mode_help": "帮助模式（实时）",
        "category": "类别",
        "phrase": "短语",
        "listen": "听",
        "speak": "说",
        "check": "检查发音",
        "next": "下一句",
        "help_input": "您想说什么？（用母语）",
        "translate": "翻译成日语",
        "speak_for_me": "帮我说",
        "your_try": "现在你试试！",
        "good_job": "做得好！",
        "try_again": "再试一次",
        "practice_hint": "学习餐厅服务日语短语",
        "help_hint": "遇到困难时获得即时翻译",
    },
    "vi": {
        "app_title": "Bridge - Đào tạo tiếng Nhật nhà hàng",
        "select_language": "Ngôn ngữ của bạn",
        "mode_practice": "Chế độ luyện tập",
        "mode_help": "Chế độ trợ giúp (Thời gian thực)",
        "category": "Danh mục",
        "phrase": "Cụm từ",
        "listen": "Nghe",
        "speak": "Nói",
        "check": "Kiểm tra phát âm",
        "next": "Câu tiếp theo",
        "help_input": "Bạn muốn nói gì? (bằng ngôn ngữ của bạn)",
        "translate": "Dịch sang tiếng Nhật",
        "speak_for_me": "Nói giúp tôi",
        "your_try": "Bây giờ bạn thử!",
        "good_job": "Tốt lắm!",
        "try_again": "Thử lại",
        "practice_hint": "Học cụm từ tiếng Nhật phục vụ nhà hàng",
        "help_hint": "Nhận bản dịch ngay khi bạn gặp khó khăn",
    },
    "ne": {
        "app_title": "Bridge - रेस्टुरेन्ट जापानी तालिम",
        "select_language": "तपाईंको मातृभाषा",
        "mode_practice": "अभ्यास मोड",
        "mode_help": "मद्दत मोड (रियल-टाइम)",
        "category": "श्रेणी",
        "phrase": "वाक्यांश",
        "listen": "सुन्नुहोस्",
        "speak": "बोल्नुहोस्",
        "check": "उच्चारण जाँच गर्नुहोस्",
        "next": "अर्को वाक्यांश",
        "help_input": "तपाईं के भन्न चाहनुहुन्छ? (तपाईंको भाषामा)",
        "translate": "जापानीमा अनुवाद गर्नुहोस्",
        "speak_for_me": "मेरो लागि बोल्नुहोस्",
        "your_try": "अब तपाईं प्रयास गर्नुहोस्!",
        "good_job": "राम्रो काम!",
        "try_again": "फेरि प्रयास गर्नुहोस्",
        "practice_hint": "रेस्टुरेन्ट सेवाको लागि जापानी वाक्यांशहरू सिक्नुहोस्",
        "help_hint": "अड्किँदा तुरुन्त अनुवाद पाउनुहोस्",
    }
}

# Session state initialization
def init_session_state():
    defaults = {
        "native_lang": "en",
        "mode": "practice",  # "practice" or "help"
        "current_category": "greeting",
        "current_phrase_idx": 0,
        "audio_data": None,
        "spoken_text": "",
        "translation_result": None,
        "help_input": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Restore from URL params
    params = st.query_params
    if "lang" in params and params["lang"] in NATIVE_LANGUAGES:
        st.session_state.native_lang = params["lang"]
    if "mode" in params and params["mode"] in ["practice", "help"]:
        st.session_state.mode = params["mode"]

init_session_state()

def get_ui(key: str) -> str:
    """Get UI text in user's native language"""
    lang = st.session_state.native_lang
    return UI_TEXT.get(lang, UI_TEXT["en"]).get(key, key)

def get_phrase_text(phrase: dict, lang: str) -> str:
    """Get phrase text in specified language"""
    return phrase.get(lang, phrase.get("en", ""))

# ===========================================
# Main UI
# ===========================================

# Sidebar
with st.sidebar:
    st.title("🍽️ Bridge")

    # Language selection
    st.subheader(get_ui("select_language"))
    lang_options = {code: f"{info['flag']} {info['name']}" for code, info in NATIVE_LANGUAGES.items()}
    selected_lang = st.selectbox(
        "Language",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(st.session_state.native_lang),
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state.native_lang:
        st.session_state.native_lang = selected_lang
        st.query_params["lang"] = selected_lang
        st.rerun()

    st.divider()

    # Mode selection
    mode = st.radio(
        "Mode",
        options=["practice", "help"],
        format_func=lambda x: get_ui(f"mode_{x}"),
        index=0 if st.session_state.mode == "practice" else 1,
        label_visibility="collapsed"
    )
    if mode != st.session_state.mode:
        st.session_state.mode = mode
        st.query_params["mode"] = mode
        st.rerun()

    st.divider()

    # Category selection (Practice mode only)
    if st.session_state.mode == "practice":
        st.subheader(get_ui("category"))
        categories = list(RESTAURANT_PHRASES.keys())
        category_names = {cat: RESTAURANT_PHRASES[cat]["title"].get(st.session_state.native_lang, RESTAURANT_PHRASES[cat]["title"]["en"]) for cat in categories}

        selected_cat = st.selectbox(
            "Category",
            options=categories,
            format_func=lambda x: category_names[x],
            index=categories.index(st.session_state.current_category),
            label_visibility="collapsed"
        )
        if selected_cat != st.session_state.current_category:
            st.session_state.current_category = selected_cat
            st.session_state.current_phrase_idx = 0
            st.rerun()

# Main content
st.title(get_ui("app_title"))

if st.session_state.mode == "practice":
    # ===========================================
    # Practice Mode
    # ===========================================
    st.info(f"💡 {get_ui('practice_hint')}")

    # Get current phrase
    category = st.session_state.current_category
    phrases = RESTAURANT_PHRASES[category]["phrases"]
    phrase_idx = st.session_state.current_phrase_idx
    current_phrase = phrases[phrase_idx]

    # Progress indicator
    st.progress((phrase_idx + 1) / len(phrases), text=f"{phrase_idx + 1} / {len(phrases)}")

    # Display cultural tip
    category_data = RESTAURANT_PHRASES[category]
    if "tips" in category_data:
        tip_text = category_data["tips"].get(st.session_state.native_lang, category_data["tips"].get("en", ""))
        if tip_text:
            st.warning(f"💡 **Cultural Tip:** {tip_text}")

    # Display phrase
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"""
        ### 🇯🇵 {current_phrase['ja']}
        **Romaji:** {current_phrase['romaji']}

        **{NATIVE_LANGUAGES[st.session_state.native_lang]['flag']} {get_phrase_text(current_phrase, st.session_state.native_lang)}**
        """)

    with col2:
        # Listen button
        if st.button(f"🔊 {get_ui('listen')}", use_container_width=True):
            try:
                tts = get_tts()
                audio_data = tts.generate_speech(current_phrase['ja'], voice_id=os.getenv("ELEVENLABS_VOICE_ID_USER"))
                if audio_data:
                    st.session_state.audio_data = audio_data
            except Exception as e:
                st.error(f"TTS Error: {e}")

        # Play audio if available
        if st.session_state.audio_data:
            st.audio(st.session_state.audio_data, format="audio/mp3")

    st.divider()

    # Speaking practice
    st.subheader(f"🎤 {get_ui('speak')}")

    audio_input = st.audio_input(f"{get_ui('your_try')}", key=f"audio_{phrase_idx}")

    if audio_input:
        try:
            stt = get_stt()
            spoken_text = stt.transcribe(audio_input, language="ja")
            st.session_state.spoken_text = spoken_text

            st.markdown(f"**You said:** {spoken_text}")

            # Simple comparison
            if current_phrase['ja'] in spoken_text or spoken_text in current_phrase['ja']:
                st.success(f"✅ {get_ui('good_job')}")
            else:
                st.warning(f"🔄 {get_ui('try_again')}")
                st.markdown(f"**Target:** {current_phrase['ja']}")
        except Exception as e:
            st.error(f"STT Error: {e}")

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("⬅️ Previous", disabled=phrase_idx == 0, use_container_width=True):
            st.session_state.current_phrase_idx -= 1
            st.session_state.audio_data = None
            st.rerun()

    with col3:
        if st.button(f"{get_ui('next')} ➡️", disabled=phrase_idx >= len(phrases) - 1, use_container_width=True):
            st.session_state.current_phrase_idx += 1
            st.session_state.audio_data = None
            st.rerun()

else:
    # ===========================================
    # Help Mode (Real-time translation)
    # ===========================================
    st.info(f"🆘 {get_ui('help_hint')}")

    # Input in native language
    help_input = st.text_area(
        get_ui("help_input"),
        value=st.session_state.help_input,
        height=100,
        placeholder="Example: I want to tell the customer to wait..."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(f"🔄 {get_ui('translate')}", use_container_width=True, type="primary"):
            if help_input:
                try:
                    kimi = get_kimi()

                    lang_name = NATIVE_LANGUAGES[st.session_state.native_lang]["name"]
                    prompt = f"""You are a helpful assistant for restaurant staff.
Translate the following {lang_name} text to polite Japanese (keigo) suitable for restaurant service.
Also provide the romaji pronunciation.

Input: {help_input}

Respond in this exact JSON format:
{{"japanese": "日本語テキスト", "romaji": "romaji text", "explanation": "brief explanation in {lang_name}"}}"""

                    response = kimi.generate(prompt, system_prompt="You are a Japanese language expert specializing in restaurant service phrases. Always respond in valid JSON.")

                    # Parse JSON response
                    try:
                        # Try to extract JSON from response
                        import re
                        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group())
                            st.session_state.translation_result = result
                            st.session_state.help_input = help_input
                    except json.JSONDecodeError:
                        st.session_state.translation_result = {"japanese": response, "romaji": "", "explanation": ""}

                except Exception as e:
                    st.error(f"Translation Error: {e}")

    # Display translation result
    if st.session_state.translation_result:
        result = st.session_state.translation_result

        st.markdown("---")
        st.markdown(f"""
        ### 🇯🇵 {result.get('japanese', '')}
        **Romaji:** {result.get('romaji', '')}

        *{result.get('explanation', '')}*
        """)

        with col2:
            if st.button(f"🔊 {get_ui('speak_for_me')}", use_container_width=True):
                try:
                    tts = get_tts()
                    audio_data = tts.generate_speech(result.get('japanese', ''), voice_id=os.getenv("ELEVENLABS_VOICE_ID_USER"))
                    if audio_data:
                        st.session_state.audio_data = audio_data
                except Exception as e:
                    st.error(f"TTS Error: {e}")

        if st.session_state.audio_data:
            st.audio(st.session_state.audio_data, format="audio/mp3")

        # Practice prompt
        st.markdown("---")
        st.markdown(f"### 🎤 {get_ui('your_try')}")
        st.markdown(f"*Next time, try saying: **{result.get('japanese', '')}***")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8em;">
    Bridge - Connecting restaurant staff with Japanese language<br>
    Powered by ElevenLabs TTS, OpenAI Whisper, and Kimi LLM
</div>
""", unsafe_allow_html=True)
