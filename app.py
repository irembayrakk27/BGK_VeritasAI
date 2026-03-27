"""
VeritasAI — Gelişmiş UI: mor/lacivert tema, görsel yükleme, renk skoru.
"""

import hashlib
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.analysis import analyze_news_text

load_dotenv(Path(__file__).resolve().parent / ".env")

st.set_page_config(
    page_title="VeritasAI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Mor + Lacivert Tema ──────────────────────────────────────────
st.markdown("""
<style>
    /* Arka plan */
    .stApp {
        background: linear-gradient(135deg, #0d0d2b 0%, #1a0533 100%);
    }
    /* Başlık */
    h1 { color: #c084fc !important; font-size: 2.8rem !important; }
    h2, h3 { color: #a855f7 !important; }
    p, label, .stMarkdown { color: #e2d9f3 !important; }

    /* Buton */
    .stButton > button {
        background: linear-gradient(90deg, #7c3aed, #4f46e5) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        padding: 0.75rem !important;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }

    /* Text area */
    .stTextArea textarea {
        background: #1e1b4b !important;
        color: #e2d9f3 !important;
        border: 1px solid #7c3aed !important;
        border-radius: 10px !important;
    }

    /* Skor kutusu */
    .skor-kutu {
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        font-size: 3rem;
        font-weight: 900;
        margin: 1rem 0;
    }
    .skor-yesil { background: #052e16; color: #4ade80; border: 2px solid #4ade80; }
    .skor-sari  { background: #1c1700; color: #facc15; border: 2px solid #facc15; }
    .skor-kirmizi { background: #1f0707; color: #f87171; border: 2px solid #f87171; }

    /* Gerekçe kartları */
    .gerekcekart {
        background: #1e1b4b;
        border-left: 4px solid #7c3aed;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        color: #e2d9f3;
    }

    /* File uploader */
    .stFileUploader {
        background: #1e1b4b !important;
        border: 2px dashed #7c3aed !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Başlık ───────────────────────────────────────────────────────
st.markdown("# 🔍 VeritasAI")
st.markdown("##### 🧠 Yapay zeka destekli haber doğrulama platformu")
st.divider()

# ── Session state ────────────────────────────────────────────────
for key in ["last_report", "last_hash"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ── Input alanı ──────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📝 Haber Metni")
    news_text = st.text_area(
        "Haber metni",
        height=250,
        placeholder="Haberin tam metnini veya başlık + gövdeyi buraya yazın…",
        label_visibility="collapsed",
    )

with col2:
    st.markdown("### 🖼️ Görsel Ekle (opsiyonel)")
    uploaded_image = st.file_uploader(
        "Haber görseli",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )
    if uploaded_image:
        st.image(uploaded_image, caption="Yüklenen görsel", use_container_width=True)

st.markdown("")

# ── Hash hesapla ─────────────────────────────────────────────────
news_text_clean = (news_text or "").strip()
current_hash = (
    hashlib.sha256(news_text_clean.encode("utf-8")).hexdigest()
    if news_text_clean else None
)

# ── Buton ────────────────────────────────────────────────────────
if st.button("🔎 Gerçeği Sorgula", type="primary", use_container_width=True):
    if not news_text_clean:
        st.warning("⚠️ Lütfen analiz için bir haber metni girin.")
    else:
        try:
            cached = (
                current_hash
                and st.session_state.get("last_hash") == current_hash
                and st.session_state.get("last_report") is not None
            )
            if cached:
                st.success("✅ Aynı metin: önbellekten gösteriliyor.")
            else:
                with st.spinner("🤖 Yapay zeka analiz ediyor..."):
                    report = analyze_news_text(news_text_clean, language="tr", max_retries=1)
                st.session_state["last_report"] = report
                st.session_state["last_hash"] = current_hash
                st.success("✅ Analiz tamamlandı!")
        except Exception as e:
            st.error(f"❌ API bağlantı hatası: {e}")

# ── Sonuç gösterimi ───────────────────────────────────────────────
if (
    current_hash
    and st.session_state.get("last_report") is not None
    and st.session_state.get("last_hash") == current_hash
):
    report = st.session_state["last_report"]
    st.divider()
    st.markdown("## 📊 Analiz Sonucu")

    skor = report.get("skor", 50)

    # Renk sınıfı
    if skor >= 80:
        css_sinif = "skor-yesil"
        etiket = "✅ Güvenilir"
    elif skor >= 50:
        css_sinif = "skor-sari"
        etiket = "⚠️ Şüpheli"
    else:
        css_sinif = "skor-kirmizi"
        etiket = "❌ Güvenilmez"

    # Skor kutusu
    st.markdown(f"""
    <div class="skor-kutu {css_sinif}">
        {etiket}<br>
        <span style="font-size:1.2rem">Güvenilirlik Skoru</span><br>
        %{skor}
    </div>
    """, unsafe_allow_html=True)

    # Progress bar
    st.progress(skor / 100)

    # Gerekçeler
    if report.get("gerekceler"):
        st.markdown("### 📌 Gerekçeler")
        ikonlar = ["1️⃣", "2️⃣", "3️⃣"]
        for i, g in enumerate(report["gerekceler"]):
            st.markdown(f"""
            <div class="gerekcekart">{ikonlar[i]} {g}</div>
            """, unsafe_allow_html=True)

    # Özet
    if report.get("ozet"):
        st.markdown("### 💬 Genel Değerlendirme")
        st.info(report["ozet"])

elif st.session_state.get("last_report") is not None and news_text_clean:
    st.info("ℹ️ Metin değişti. Yeniden 'Gerçeği Sorgula'ya bas.")