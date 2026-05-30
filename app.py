"""
VeritasAI — Kalıcı sohbet geçmişi + sol sidebar.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.analysis import analyze_news_text

import requests
from bs4 import BeautifulSoup

load_dotenv(Path(__file__).resolve().parent / ".env")

def url_den_metin_cek(url:str) -> str:
    "Verilen URL'den haber metnini çeker ve temizler."
    try:
         # Tarayıcı gibi davran, yoksa bazı siteler 403 verir
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 404, 403 gibi hataları yakala

        soup = BeautifulSoup(response.text, "lxml")

        # Navigasyon, footer, reklam gibi gürültüyü temizle
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Önce <article> dene (haber siteleri genelde bunu kullanır)
        # Yoksa <main>, o da yoksa tüm sayfa
        article = soup.find("article") or soup.find("main") or soup

        # Sadece gerçek paragrafları al (40 karakterden kısa olanlar
        # genelde menü linkleri veya etiketlerdir, onları at)
        paragraflar = article.find_all("p")
        metin = " ".join(
            p.get_text(strip=True)
            for p in paragraflar
            if len(p.get_text(strip=True)) > 40
        )

        # Hiç paragraf bulunamazsa ham metni al
        if not metin:
            metin = soup.get_text(separator=" ", strip=True)

        # Groq'un token limitine karşı 3000 karakterde kes
        return metin[:3000]

    except requests.exceptions.Timeout:
        return "HATA: Sayfa 10 saniyede yanıt vermedi."
    except requests.exceptions.ConnectionError:
        return "HATA: URL'e erişilemedi, linki kontrol et."
    except Exception as e:
        return f"HATA: {e}"

# ── Geçmiş dosya yolu ────────────────────────────────────────────
GECMIS_DOSYA = Path(__file__).resolve().parent / "data" / "gecmis.json"
GECMIS_DOSYA.parent.mkdir(exist_ok=True)

def gecmis_yukle():
    if GECMIS_DOSYA.exists():
        with open(GECMIS_DOSYA, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def gecmis_kaydet(gecmis):
    with open(GECMIS_DOSYA, "w", encoding="utf-8") as f:
        json.dump(gecmis, f, ensure_ascii=False, indent=2)

def gecmise_ekle(metin, rapor):
    gecmis = gecmis_yukle()
    kayit = {
        "id": len(gecmis) + 1,
        "tarih": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "metin_ozet": metin[:60] + "..." if len(metin) > 60 else metin,
        "skor": rapor.get("skor", 0),
        "rapor": rapor,
    }
    gecmis.insert(0, kayit)
    gecmis = gecmis[:50]
    gecmis_kaydet(gecmis)
    return gecmis

# ── Rapor gösterme fonksiyonu ─────────────────────────────────────
def rapor_goster(report):
    skor = report.get("skor", 50)

    if skor >= 80:
        css_sinif, etiket = "skor-yesil", "✅ Güvenilir"
    elif skor >= 50:
        css_sinif, etiket = "skor-sari", "⚠️ Şüpheli"
    else:
        css_sinif, etiket = "skor-kirmizi", "❌ Güvenilmez"

    st.markdown(f"""
    <div class="skor-kutu {css_sinif}">
        {etiket}<br>
        <span style="font-size:1.2rem">Güvenilirlik Skoru</span><br>
        %{skor}
    </div>
    """, unsafe_allow_html=True)

    st.progress(skor / 100)

    st.markdown("### 🔎 Detay Analiz")
    dcol1, dcol2 = st.columns(2)

    with dcol1:
        manipulasyon = report.get("manipulasyon", "Tespit edilmedi")
        renk = "#f87171" if manipulasyon.lower() != "tespit edilmedi" else "#4ade80"
        st.markdown(f"""
        <div class="bilgi-kart">
            <div class="bilgi-baslik">⚠️ Manipülasyon Tekniği</div>
            <div class="bilgi-deger" style="color:{renk}">{manipulasyon}</div>
        </div>
        """, unsafe_allow_html=True)

    with dcol2:
        kaynak = report.get("kaynak_kalitesi", "Bilinmiyor")
        if "güçlü" in kaynak.lower():
            kaynak_renk = "#4ade80"
        elif "orta" in kaynak.lower():
            kaynak_renk = "#facc15"
        else:
            kaynak_renk = "#f87171"
        st.markdown(f"""
        <div class="bilgi-kart">
            <div class="bilgi-baslik">📰 Kaynak Kalitesi</div>
            <div class="bilgi-deger" style="color:{kaynak_renk}">{kaynak}</div>
        </div>
        """, unsafe_allow_html=True)

    if report.get("gerekceler"):
        st.markdown("### 📌 Gerekçeler")
        ikonlar = ["1️⃣", "2️⃣", "3️⃣"]
        for i, g in enumerate(report["gerekceler"]):
            st.markdown(f"""
            <div class="gerekcekart">{ikonlar[i]} {g}</div>
            """, unsafe_allow_html=True)

    if report.get("ozet"):
        st.markdown("### 💬 Genel Değerlendirme")
        st.info(report["ozet"])

    if report.get("kaynaklar"):
        st.markdown("### 🔗 İlgili Kaynaklar")
        for kaynak in report["kaynaklar"]:
            st.markdown(f"""
            <div class="gerekcekart">
                <b>📰 {kaynak.get('title', 'Kaynak')}</b><br>
                <small>{kaynak.get('content', '')[:200]}...</small><br>
                <a href="{kaynak.get('url', '#')}" target="_blank"
                   style="color:#a855f7;">🔗 Kaynağa Git</a>
            </div>
            """, unsafe_allow_html=True)

st.set_page_config(
    page_title="VeritasAI — Ana Sayfa",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Tema ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0d0d2b 0%, #1a0533 100%);
    }
    h1 { color: #c084fc !important; font-size: 2.8rem !important; }
    h2, h3 { color: #a855f7 !important; }
    p, label, .stMarkdown { color: #e2d9f3 !important; }

    .stButton > button {
        background: linear-gradient(90deg, #7c3aed, #4f46e5) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        padding: 0.75rem !important;
    }
    .stButton > button:hover { opacity: 0.85; }

    .stTextArea textarea {
        background: #1e1b4b !important;
        color: #e2d9f3 !important;
        border: 1px solid #7c3aed !important;
        border-radius: 10px !important;
    }

    .skor-kutu {
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        font-size: 3rem;
        font-weight: 900;
        margin: 1rem 0;
    }
    .skor-yesil   { background: #052e16; color: #4ade80; border: 2px solid #4ade80; }
    .skor-sari    { background: #1c1700; color: #facc15; border: 2px solid #facc15; }
    .skor-kirmizi { background: #1f0707; color: #f87171; border: 2px solid #f87171; }

    .gerekcekart {
        background: #1e1b4b;
        border-left: 4px solid #7c3aed;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        color: #e2d9f3;
    }

    .bilgi-kart {
        background: #1e1b4b;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        color: #e2d9f3;
        border: 1px solid #4f46e5;
    }
    .bilgi-baslik {
        font-size: 0.8rem;
        color: #a855f7;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.3rem;
    }
    .bilgi-deger {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e2d9f3;
    }

    [data-testid="stSidebar"] {
        background: #0d0d2b !important;
        border-right: 1px solid #4f46e5;
    }
    .gecmis-kart {
        background: #1e1b4b;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin: 0.4rem 0;
        cursor: pointer;
        border: 1px solid #4f46e5;
    }
    .gecmis-kart:hover { border-color: #a855f7; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────
for key in ["last_report", "last_hash", "secili_gecmis", "url_metin", "url_metin_kullanildi", "gorsel_sonuc", "video_sonuc"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🕒 Analiz Geçmişi")
    st.divider()

    gecmis = gecmis_yukle()

    if not gecmis:
        st.info("Henüz analiz yapılmadı.")
    else:
        if st.button("🗑️ Geçmişi Temizle", use_container_width=True):
            gecmis_kaydet([])
            st.session_state["secili_gecmis"] = None
            st.rerun()

        st.markdown(f"**{len(gecmis)} analiz kayıtlı**")
        st.markdown("")

        for kayit in gecmis:
            skor = kayit["skor"]
            if skor >= 80:
                skor_emoji = "🟢"
            elif skor >= 50:
                skor_emoji = "🟡"
            else:
                skor_emoji = "🔴"

            if st.button(
                f"{skor_emoji} %{skor} — {kayit['metin_ozet']}",
                key=f"gecmis_{kayit['id']}",
                use_container_width=True,
            ):
                st.session_state["secili_gecmis"] = kayit

# ── Ana içerik ───────────────────────────────────────────────────
st.markdown("# 🔍 VeritasAI")
st.markdown("##### 🧠 Yapay zeka destekli haber doğrulama platformu")
st.divider()

if st.session_state["secili_gecmis"]:
    kayit = st.session_state["secili_gecmis"]
    st.info(f"📂 Geçmiş kayıt gösteriliyor — {kayit['tarih']}")
    if st.button("✖️ Kapat"):
        st.session_state["secili_gecmis"] = None
        st.rerun()
    rapor_goster(kayit["rapor"])
    st.stop()

# ── Input ────────────────────────────────────────────────────────
# ── Video Analizi ─────────────────────────────────────────────────
st.markdown("### 🎥 Video Analizi")
video_url = st.text_input(
    "video_url",
    placeholder="🎥 YouTube linki yapıştır (opsiyonel)…",
    label_visibility="collapsed",
)

if video_url and ("youtube.com" in video_url or "youtu.be" in video_url):
    if st.button("▶️ Videoyu Analiz Et", use_container_width=False):
        with st.spinner("Transcript çekiliyor ve analiz yapılıyor..."):
            from services.video_analysis import video_analiz_et
            video_sonuc = video_analiz_et(video_url)
            st.session_state["video_sonuc"] = video_sonuc

    if st.session_state.get("video_sonuc"):
        vs = st.session_state["video_sonuc"]

        if vs.get("hata"):
            st.error(f"❌ {vs['hata']}")
        else:
            karar = vs.get("karar", "")
            skor = vs.get("guven_skoru", 0)

            # Renk kodu
            if karar == "Güvenilir":
                renk, ikon = "#4ade80", "✅"
            elif karar == "Şüpheli":
                renk, ikon = "#facc15", "⚠️"
            else:
                renk, ikon = "#f87171", "❌"

            st.markdown(f"""
<div style="background:#1e1b4b;border-radius:12px;padding:1rem;
border:2px solid {renk};margin-bottom:1rem">
<div style="color:{renk};font-size:1.2rem;font-weight:700">{ikon} {karar}</div>
<div style="color:#a855f7;font-size:0.85rem;margin-top:4px">
Güven Skoru: %{skor} · Dil: {vs.get('dil', '?')}</div>
<div style="color:#e2d9f3;font-size:0.85rem;margin-top:8px">
{vs.get('ana_bulgu', '')}</div>
</div>""", unsafe_allow_html=True)

            if vs.get("gerekceler"):
                st.markdown("**📌 Gerekçeler:**")
                for g in vs["gerekceler"]:
                    st.markdown(f"• {g}")

            if vs.get("ozet"):
                st.info(vs["ozet"])

            if vs.get("transcript_ozet"):
                with st.expander("📄 Transcript Önizleme"):
                    st.caption(f"Kullanılan dil: {vs.get('dil', '?')}")
                    st.write(vs["transcript_ozet"])

st.divider()

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📝 Haber Metni veya URL")

    # URL kutusu
    haber_url = st.text_input(
        "haber_url",
        placeholder="🔗 Haber URL'si yapıştır (opsiyonel) — metin otomatik dolar…",
        label_visibility="collapsed",
    )

    # Geçerli bir URL girilmişse butonu göster
    if haber_url and haber_url.startswith("http"):
        if st.button("🌐 URL'den Metni Çek"):
            with st.spinner("Sayfa indiriliyor ve temizleniyor..."):
                cekilen = url_den_metin_cek(haber_url)
            if cekilen.startswith("HATA:"):
                st.error(cekilen)
            else:
                st.session_state["url_metin"] = cekilen
                st.success(f"✅ {len(cekilen)} karakter çekildi.")
                st.rerun()  # text_area'yı hemen güncelle

    # Text area — URL'den metin çekildiyse otomatik dolu gelir
    news_text = st.text_area(
        "Haber metni",
        value=st.session_state.get("url_metin", ""),
        height=220,
        placeholder="Haberin tam metnini buraya yaz… ya da yukarıya URL yapıştır.",
        label_visibility="collapsed",
    )

    # url_metin kullanıldı, bir sonraki rerun'da temizle
    if st.session_state.get("url_metin_kullanildi"):
        st.session_state["url_metin"] = ""
        st.session_state["url_metin_kullanildi"] = False
    elif st.session_state.get("url_metin"):
        st.session_state["url_metin_kullanildi"] = True

with col2:
    st.markdown("### 🖼️ Görsel Analizi")
    uploaded_image = st.file_uploader(
        "Haber görseli",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_image:
        st.image(uploaded_image, caption="Yüklenen görsel", use_container_width=True)

        if st.button("🔬 Görseli Analiz Et", use_container_width=True):
            with st.spinner("Piksel analizi yapılıyor..."):
                from services.image_analysis import gorsel_analiz_et
                gorsel_bytes = uploaded_image.read()
                gorsel_sonuc = gorsel_analiz_et(gorsel_bytes, uploaded_image.name)
                st.session_state["gorsel_sonuc"] = gorsel_sonuc
                st.rerun()

        if st.session_state.get("gorsel_sonuc"):
            g = st.session_state["gorsel_sonuc"]
            karar = g.get("karar", "")
            risk = g.get("risk_seviyesi", "")

            # Renk kodu
            if "Gerçek" in karar:
                renk = "#4ade80"
                ikon = "✅"
            elif "AI" in karar:
                renk = "#f87171"
                ikon = "🤖"
            elif "Manipüle" in karar:
                renk = "#f87171"
                ikon = "⚠️"
            else:
                renk = "#facc15"
                ikon = "❓"

            st.markdown(f"""
<div style="background:#1e1b4b;border-radius:12px;padding:1rem;
border:2px solid {renk};margin-top:0.5rem">
<div style="color:{renk};font-size:1.1rem;font-weight:700">
{ikon} {karar}</div>
<div style="color:#a855f7;font-size:0.85rem;margin-top:4px">
Güven: %{g.get('guven_yuzdesi', 0)} · Risk: {risk}</div>
<div style="color:#e2d9f3;font-size:0.85rem;margin-top:8px">
{g.get('ana_sinyal', '')}</div>
</div>""", unsafe_allow_html=True)

            if g.get("detaylar"):
                st.markdown("**Detaylar:**")
                for d in g["detaylar"]:
                    st.markdown(f"• {d}")
# ── Hash ─────────────────────────────────────────────────────────
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
                with st.spinner("🤖 Çift aşamalı analiz yapılıyor... (1/2 ön analiz → 2/2 derin analiz)"):
                    report = analyze_news_text(
                        news_text_clean, language="tr", max_retries=1
                    )
                st.session_state["last_report"] = report
                st.session_state["last_hash"] = current_hash
                gecmise_ekle(news_text_clean, report)
                st.success("✅ Analiz tamamlandı!")
        except Exception as e:
            st.error(f"❌ API bağlantı hatası: {e}")

# ── Sonuç ────────────────────────────────────────────────────────
if (
    current_hash
    and st.session_state.get("last_report") is not None
    and st.session_state.get("last_hash") == current_hash
):
    st.divider()
    st.markdown("## 📊 Analiz Sonucu")
    rapor_goster(st.session_state["last_report"])

elif st.session_state.get("last_report") is not None and news_text_clean:
    st.info("ℹ️ Metin değişti. Yeniden 'Gerçeği Sorgula'ya bas.")