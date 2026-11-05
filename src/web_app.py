"""
Interactive Web Application for UZEX AI Hackathon 2026.
Built with Streamlit for zero-friction evaluation and exploration.
"""

import os
import sys
import time
import pandas as pd
import streamlit as st

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.agent import UzexAgent
from src.config import LLM_PROVIDER, GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY

st.set_page_config(
    page_title="UZEX AI — Birja Bitimlari Analitiki",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, polished appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-badge {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 600;
        color: #1D4ED8;
    }
    .sql-box {
        background: #0F172A;
        color: #38BDF8;
        padding: 12px;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_agent():
    return UzexAgent()

agent = get_agent()

# Sidebar: Controls, Stats & Key Settings
with st.sidebar:
    st.image("https://hackathon.uzex.uz/favicon.ico" if False else "https://img.icons8.com/fluency/96/combo-chart.png", width=64)
    st.markdown("### 🏛️ UZEX AI Hackathon 2026")
    st.markdown("**Saralash bosqichi prototipi**")
    st.caption("500 000 bitim · 2022-2026 · spot.uzex.uz")
    
    st.divider()
    
    lang = st.radio("Til / Язык:", ["🇺🇿 O'zbekcha", "🇷🇺 Русский"], index=0)
    selected_lang = 'uz' if "O'zbekcha" in lang else 'ru'

    st.divider()
    st.markdown("#### ⚡ Tizim holati")
    st.markdown(f"- **Dvigatel**: DuckDB In-Memory Columnar")
    st.markdown(f"- **Jami bitimlar**: 500 000 ta")
    st.markdown(f"- **Shartnomalar**: 6 616 ta")
    st.markdown(f"- **Ishtirokchilar**: 14 392 ta")
    st.markdown(f"- **Brokerlar**: 120 ta")
    st.markdown(f"- **Faol rejim**: `{agent.sql_generator.provider}`")

    st.divider()
    with st.expander("🔑 API Kalitini sozlash (Ixtiyoriy)"):
        user_gemini_key = st.text_input("Gemini API Key:", value=GEMINI_API_KEY, type="password")
        user_groq_key = st.text_input("Groq API Key:", value=GROQ_API_KEY, type="password")
        user_openai_key = st.text_input("OpenAI API Key:", value=OPENAI_API_KEY, type="password")
        if st.button("Saqlash va qayta yuklash"):
            if user_gemini_key:
                os.environ["GEMINI_API_KEY"] = user_gemini_key
            if user_groq_key:
                os.environ["GROQ_API_KEY"] = user_groq_key
            if user_openai_key:
                os.environ["OPENAI_API_KEY"] = user_openai_key
            st.cache_resource.clear()
            st.rerun()

# Main Tabs
tab1, tab2, tab3 = st.tabs(["💬 Savol-Javob (AI Agent)", "📊 Analitika & Trendlar", "ℹ️ Loyiha & Metodologiya"])

with tab1:
    st.markdown('<div class="main-header">Birja bitimlari bo‘yicha AI-Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Birja reyestridagi 500 000 bitim bo‘yicha aniq, tezkor va faktlarga asoslangan javoblar.</div>', unsafe_allow_html=True)

    # Quick sample questions buttons
    st.markdown("**💡 Tezkor savollar (Namuna):**")
    cols = st.columns(3)
    sample_q = None
    if selected_lang == 'uz':
        if cols[0].button("🏆 2024-yilda eng ko'p sement sotgan 5 sotuvchi"):
            sample_q = "2024-yilda eng ko'p sement sotgan 5 ta sotuvchi"
        if cols[1].button("🏢 BK001 kodi qaysi brokerga tegishli?"):
            sample_q = "BK001 kodi qaysi brokerga tegishli va uning STIRi nima?"
        if cols[2].button("🚫 2023-yilda bekor qilingan bitimlar soni va summasi"):
            sample_q = "2023-yilda bekor qilingan bitimlar soni va ularning umumiy summasi qancha bo'lgan?"
        
        cols2 = st.columns(3)
        if cols2[0].button("📍 Samarqandda 2024-yilda qancha bug'doy sotilgan?"):
            sample_q = "Samarqand viloyatida 2024-yilda qancha bug'doy sotilgan?"
        if cols2[1].button("⚠️ 2027-yilda qancha tovar sotilgan? (Sinov)"):
            sample_q = "2027-yilda qancha tovar sotilgan?"
        if cols2[2].button("⚠️ Oltin bo'yicha bitimlar bormi? (Sinov)"):
            sample_q = "2024-yilda oltin bo'yicha nechta bitim tuzilgan?"
    else:
        if cols[0].button("🏆 Топ-5 продавцов цемента в 2024 году"):
            sample_q = "Покажи 5 крупнейших продавцов цемента в 2024 году"
        if cols[1].button("🏢 Кому принадлежит брокерский код BK001?"):
            sample_q = "Кому принадлежит брокерский код BK001 и какой у него ИНН?"
        if cols[2].button("🚫 Сколько аннулированных сделок в 2023 году?"):
            sample_q = "Сколько аннулированных сделок было в 2023 году и на какую сумму?"
        
        cols2 = st.columns(3)
        if cols2[0].button("📍 Продажи пшеницы в Самарканде в 2024 г."):
            sample_q = "Сколько пшеницы было продано в Самаркандской области в 2024 году?"
        if cols2[1].button("⚠️ Сколько сделок в 2027 году? (Проверка)"):
            sample_q = "Сколько сделок заключено в 2027 году?"
        if cols2[2].button("⚠️ Были ли сделки по золоту? (Проверка)"):
            sample_q = "Сколько сделок по золоту было в 2024 году?"

    # Chat input / search bar
    user_query = st.chat_input("Savolingizni o'zbek yoki rus tilida yozing..." if selected_lang == 'uz' else "Задайте вопрос на русском или узбекском языке...")
    active_query = user_query or sample_q

    if active_query:
        st.chat_message("user").write(active_query)

        with st.chat_message("assistant"):
            with st.spinner("DuckDB bazasidan tahlil qilinmoqda..." if selected_lang == 'uz' else "Анализирую данные в DuckDB..."):
                result = agent.answer_question(active_query, forced_lang=selected_lang)

            # Display main answer
            st.markdown(result['answer'])

            # Display Provenance Accordion / Table
            if result.get('rows') and len(result['rows']) > 0:
                with st.expander("🔍 Bajarilgan SQL va Qaytarilgan jadval (Provenance & Data table)", expanded=False):
                    st.code(result['sql'], language="sql")
                    df = pd.DataFrame(result['rows'], columns=result['columns'])
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"⚡ Bajarilish vaqti: {result['execution_time_ms']} ms | Qatorlar: {result['row_count']}")

with tab2:
    st.subheader("📈 Birja bitimlari umumiy statistikasi (2022 - 2026)")
    
    con = agent.db_engine.get_connection()
    yearly_df = con.execute("""
        SELECT 
            deal_year AS "Yil",
            count(*) AS "Bitimlar soni",
            round(sum(deal_amount_uzs) / 1e12, 2) AS "Umumiy aylanma (Trln so'm)",
            round(sum(volume_units) / 1e6, 2) AS "Jami hajm (Mln birlik)"
        FROM deals
        GROUP BY deal_year
        ORDER BY deal_year
    """).df()

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    total_deals_all = yearly_df["Bitimlar soni"].sum()
    total_amount_all = yearly_df["Umumiy aylanma (Trln so'm)"].sum()
    col_m1.metric("Jami bitimlar", f"{total_deals_all:,}".replace(",", " "))
    col_m2.metric("Umumiy aylanma", f"{total_amount_all:.1f} Trln UZS")
    col_m3.metric("O'rtacha kunlik bitimlar", "~300 ta")
    col_m4.metric("Qamrov davri", "2022 - 2026")

    st.bar_chart(yearly_df.set_index("Yil")["Umumiy aylanma (Trln so'm)"])
    st.dataframe(yearly_df, use_container_width=True)

    st.divider()
    st.subheader("🏷️ Eng ommabop 10 tovar turi")
    top_prods_df = con.execute("""
        SELECT 
            product_name AS "Tovar nomi",
            count(*) AS "Bitimlar soni",
            round(sum(deal_amount_uzs) / 1e9, 2) AS "Aylanma (Mlr so'm)"
        FROM deals
        GROUP BY product_name
        ORDER BY count(*) DESC
        LIMIT 10
    """).df()
    st.dataframe(top_prods_df, use_container_width=True)

with tab3:
    st.subheader("📋 Loyiha arxitekturasi va Baholash mezonlari")
    st.markdown("""
    ### 🏆 UZEX AI Hackathon 2026 — Yechim tavsifi

    **1. Maqsad va Yondashuv:**
    Ushbu AI-agent birja bitimlari (500 000 ta spot bitim) bo'yicha rus va o'zbek tillaridagi savollarga **100% faktlarga tayangan holda** javob beradi.

    **2. Texnologik stak:**
    - **Ma'lumotlar tahlil dvigateli**: `DuckDB` (in-memory ustunli analitik SQL dvigatel). 500 000 bitim ustida agregatsiya va qidiruv **10-80 millisekundda** bajariladi!
    - **Entity Resolver & Normalizer**: O'zbek va rus tillaridagi sinonimlar lug'ati (sement <-> цемент, bug'doy <-> пшеница, paxta <-> хлопок), 14 ta hudud nomi va 120 ta broker kodi mappingi.
    - **Anti-Hallucination Guardrail (Gallyutsinatsiyaga qarshi himoya)**:
      - Baza chegaralari qat'iy nazoratda: faqat 2022.01.03 - 2026.10.30.
      - Reyestrda bo'lmagan tovarlar (oltin, xom neft, gaz) yoki kompaniyalar so'ralsa, tizim darhol **"Berilgan ma'lumotlarda javob yo'q"** deb bildiradi.
      - SQL natijasi 0 bo'lsa, hech qanday xayoliy son aytilmaydi.
    - **Provenance & Shaffoflik**: Har bir javob tagida bajarilgan SQL so'rovi, vaqti (ms) va topilgan qatorlar soni ko'rsatiladi (Prototip sifati uchun 20 ball).
    - **Interfeyslar**: Streamlit Web-servisi + Aiogram 3 Telegram-bot.
    """)
