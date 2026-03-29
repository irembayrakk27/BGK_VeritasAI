import streamlit as st
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

st.set_page_config(
    page_title="VeritasAI — Otomasyon",
    page_icon="🤖",
    layout="wide",
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0d0d2b 0%, #1a0533 100%);
    }
    h1, h2, h3 { color: #c084fc !important; }
    p, label, .stMarkdown { color: #e2d9f3 !important; }
    .stButton > button {
        background: linear-gradient(90deg, #7c3aed, #4f46e5) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
    }
    .stTextArea textarea, .stTextInput input {
        background: #1e1b4b !important;
        color: #e2d9f3 !important;
        border: 1px solid #7c3aed !important;
        border-radius: 10px !important;
    }
    .akis-kutu {
        background: #1e1b4b;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #4f46e5;
        color: #e2d9f3;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🤖 Otomasyon Merkezi")
st.markdown("##### n8n ile güçlendirilmiş otomatik haber analiz akışı")
st.divider()

# ── Akış Diyagramı ────────────────────────────────────────────────
st.markdown("### 📊 Otomasyon Akışı")
st.markdown("""
<div class="akis-kutu">
    <p style="text-align:center; font-size:1.1rem;">
    📝 Haber Metni Gir
    &nbsp;→&nbsp;
    🔗 Webhook Tetiklenir
    &nbsp;→&nbsp;
    🤖 Groq AI Analiz Eder
    &nbsp;→&nbsp;
    📧 Gmail'e Sonuç Gönderilir
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Manuel Tetikleme ──────────────────────────────────────────────
st.markdown("### 🚀 Otomasyonu Manuel Tetikle")
st.caption("Haber metnini gir, n8n workflow'u çalıştır ve sonucu mail olarak al.")

# n8n Webhook URL
WEBHOOK_URL = st.text_input(
    "🔗 n8n Webhook URL",
    placeholder="https://irembayrakk.app.n8n.cloud/webhook/...",
    help="n8n'deki Webhook node'unun Üretim URL'sini buraya yapıştır",
)

haber_metni = st.text_area(
    "📝 Haber Metni",
    height=150,
    placeholder="Analiz edilecek haberi buraya yaz...",
)

email = st.text_input(
    "📧 Sonuç Gönderilecek E-posta",
    placeholder="ornek@gmail.com",
)

if st.button("🚀 Otomasyonu Başlat", type="primary", use_container_width=True):
    if not WEBHOOK_URL:
        st.warning("⚠️ Webhook URL girilmedi.")
    elif not haber_metni.strip():
        st.warning("⚠️ Haber metni girilmedi.")
    elif not email:
        st.warning("⚠️ E-posta adresi girilmedi.")
    else:
        try:
            with st.spinner("🤖 n8n workflow tetikleniyor..."):
                response = requests.post(
                    WEBHOOK_URL,
                    json={
                        "haber_metni": haber_metni,
                        "email": email,
                    },
                    timeout=30,
                )
            if response.status_code == 200:
                st.success("✅ Otomasyon başlatıldı! Sonuç e-posta adresine gönderilecek.")
                st.balloons()
            else:
                st.error(f"❌ Hata: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Bağlantı hatası: {e}")

st.divider()

# ── Bilgi Kutusu ──────────────────────────────────────────────────
st.markdown("### ℹ️ Nasıl Çalışır?")
st.markdown("""
<div class="akis-kutu">
<b>1.</b> n8n'de Webhook node'unun <b>Üretim URL</b>'sini kopyala<br><br>
<b>2.</b> Yukarıdaki kutuya yapıştır<br><br>
<b>3.</b> Analiz edilecek haberi yaz<br><br>
<b>4.</b> E-posta adresini gir<br><br>
<b>5.</b> "Otomasyonu Başlat" butonuna bas<br><br>
<b>6.</b> Birkaç saniye içinde mail kutuna analiz sonucu gelir! 📧
</div>
""", unsafe_allow_html=True)