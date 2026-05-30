"""
VeritasAI — Topluluk Teyidi Sayfası
Kullanıcılar kanıt ekleyerek haberlerin doğruluk skorunu güncelleyebilir.
"""

import json
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

st.set_page_config(
    page_title="VeritasAI — Topluluk Teyidi",
    page_icon="🤝",
    layout="wide",
)

# ── Tema ─────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0d0d2b 0%, #1a0533 100%); }
h1, h2, h3 { color: #a855f7 !important; }
p, label, .stMarkdown { color: #e2d9f3 !important; }
.stButton > button {
    background: linear-gradient(90deg, #7c3aed, #4f46e5) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; font-weight: 700 !important;
}
.stTextArea textarea, .stTextInput input {
    background: #1e1b4b !important; color: #e2d9f3 !important;
    border: 1px solid #7c3aed !important; border-radius: 10px !important;
}
.kanit-kart {
    background: #1e1b4b; border-left: 4px solid #7c3aed;
    border-radius: 8px; padding: 1rem 1.2rem;
    margin: 0.5rem 0; color: #e2d9f3;
}
.skor-badge {
    display: inline-block; padding: 4px 14px;
    border-radius: 20px; font-weight: 700; font-size: 0.9rem;
}
[data-testid="stSidebar"] {
    background: #0d0d2b !important;
    border-right: 1px solid #4f46e5;
}
</style>
""", unsafe_allow_html=True)

# ── Geçmiş yükle ─────────────────────────────────────────────────
GECMIS_DOSYA = Path(__file__).resolve().parent.parent / "data" / "gecmis.json"

def gecmis_yukle():
    if GECMIS_DOSYA.exists():
        with open(GECMIS_DOSYA, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def gecmis_kaydet(gecmis):
    with open(GECMIS_DOSYA, "w", encoding="utf-8") as f:
        json.dump(gecmis, f, ensure_ascii=False, indent=2)

# ── Başlık ───────────────────────────────────────────────────────
st.markdown("# 🤝 Topluluk Teyidi")
st.markdown("##### Kanıt sunarak haberlerin doğruluk skorunu güncelle")
st.divider()

gecmis = gecmis_yukle()

if not gecmis:
    st.info("Henüz analiz edilmiş haber yok. Önce Ana Sayfa'dan bir haber analiz et.")
    st.stop()

# ── Haber seçimi ─────────────────────────────────────────────────
st.markdown("### 📰 Hangi haber için kanıt ekleyeceksin?")

secenekler = {}
for k in gecmis:
    skor = k["skor"]
    if skor >= 80:
        emoji = "🟢"
    elif skor >= 50:
        emoji = "🟡"
    else:
        emoji = "🔴"
    etiket = f"{emoji} %{skor} — {k['metin_ozet']}"
    secenekler[etiket] = k

secili_etiket = st.selectbox(
    "Haber seç",
    options=list(secenekler.keys()),
    label_visibility="collapsed",
)
secili_kayit = secenekler[secili_etiket]

# Seçili haberin mevcut skorunu göster
skor = secili_kayit["skor"]
if skor >= 80:
    skor_renk, skor_etiket = "#4ade80", "Güvenilir"
elif skor >= 50:
    skor_renk, skor_etiket = "#facc15", "Şüpheli"
else:
    skor_renk, skor_etiket = "#f87171", "Güvenilmez"

st.markdown(f"""
<div style="background:#1e1b4b;border-radius:12px;padding:1rem;
border:2px solid {skor_renk};margin:1rem 0;display:inline-block">
<span style="color:{skor_renk};font-weight:700;font-size:1.1rem">
{skor_etiket} · Mevcut Skor: %{skor}
</span>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Kanıt formu ──────────────────────────────────────────────────
st.markdown("### 📎 Kanıtını Ekle")
st.caption("Ne kadar çok kanıt türü eklersen analiz o kadar güçlü olur.")

# Geniş layout — 2 sütun
form_col1, form_col2 = st.columns([1, 1], gap="large")

with form_col1:
    st.markdown("#### 📝 Metin Açıklaması")
    kanit_metin = st.text_area(
        "Açıklama",
        placeholder="Bu haber doğru/yanlış çünkü...\nKanıtını detaylı açıkla.",
        height=160,
        label_visibility="collapsed",
    )

    st.markdown("#### 🔗 Kaynak URL")
    kanit_url = st.text_input(
        "Kaynak link",
        placeholder="https://güvenilir-kaynak.com/haber...",
        label_visibility="collapsed",
    )

with form_col2:
    st.markdown("#### 🖼️ Görsel Kanıt")
    kanit_gorsel = st.file_uploader(
        "Görsel yükle",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
        key="kanit_gorsel",
    )
    if kanit_gorsel:
        st.image(kanit_gorsel, caption="Yüklenen görsel kanıt", use_container_width=True)

    st.markdown("#### 🎥 Video Kanıt (YouTube)")
    kanit_video = st.text_input(
        "YouTube linki",
        placeholder="https://youtube.com/watch?v=...",
        label_visibility="collapsed",
        key="kanit_video",
    )
    if kanit_video and ("youtube.com" in kanit_video or "youtu.be" in kanit_video):
        # Video ID çıkar ve embed göster
        import re
        video_id_eslesme = re.search(
            r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
            kanit_video
        )
        if video_id_eslesme:
            vid = video_id_eslesme.group(1)
            st.markdown(f"""
<iframe width="100%" height="200"
src="https://www.youtube.com/embed/{vid}"
frameborder="0" allowfullscreen></iframe>
""", unsafe_allow_html=True)

st.divider()

# ── Gönder butonu ────────────────────────────────────────────────
gonder_col, _ = st.columns([1, 2])
with gonder_col:
    gonder = st.button("🔍 Kanıtı Gönder ve Skoru Güncelle", use_container_width=True)

if gonder:
    if not kanit_metin.strip():
        st.warning("⚠️ En az bir metin açıklaması zorunlu.")
    else:
        with st.spinner("🤖 AI kanıtı inceliyor ve skor güncelleniyor..."):
            try:
                from services.analysis import kanit_analiz

                kanit = {
                    "aciklama": kanit_metin,
                    "link": kanit_url or "Belirtilmedi",
                    "gorsel": kanit_gorsel.name if kanit_gorsel else "Yok",
                    "video": kanit_video or "Belirtilmedi",
                }

                sonuc = kanit_analiz(
                    secili_kayit["metin_ozet"],
                    kanit,
                    secili_kayit["skor"],
                )

                # Geçmişi güncelle
                gecmis = gecmis_yukle()
                for k in gecmis:
                    if k["id"] == secili_kayit["id"]:
                        eski_skor = k["skor"]
                        k["skor"] = sonuc["yeni_skor"]
                        if "kanitlar" not in k:
                            k["kanitlar"] = []
                        k["kanitlar"].append({
                            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M"),
                            "aciklama": kanit_metin,
                            "link": kanit_url,
                            "gorsel": kanit_gorsel.name if kanit_gorsel else None,
                            "video": kanit_video or None,
                            "karar": sonuc["karar"],
                            "degisim": sonuc["skor_degisimi"],
                            "ai_aciklama": sonuc["aciklama"],
                        })
                        break
                gecmis_kaydet(gecmis)

                # Sonucu göster
                karar = sonuc["karar"]
                if "Doğrular" in karar:
                    st.success(f"✅ {karar}")
                elif "Çürütür" in karar:
                    st.error(f"❌ {karar}")
                else:
                    st.warning(f"⚠️ {karar}")

                degisim = sonuc["skor_degisimi"]
                isaret = "+" if degisim >= 0 else ""

                st.markdown(f"""
<div class="kanit-kart">
<b>Kanıt Güvenilirliği:</b> {sonuc['kanit_guvenirligi']}<br>
<b>Skor Değişimi:</b> %{eski_skor} → %{sonuc['yeni_skor']}
<span style="color:{'#4ade80' if degisim >= 0 else '#f87171'}">
({isaret}{degisim})</span><br>
<b>AI Değerlendirmesi:</b> {sonuc['aciklama']}
</div>
""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Hata: {e}")

st.divider()

# ── Mevcut kanıtları göster ───────────────────────────────────────
mevcut_kanitlar = secili_kayit.get("kanitlar", [])
if mevcut_kanitlar:
    st.markdown(f"### 📋 Bu Habere Eklenen Kanıtlar ({len(mevcut_kanitlar)} adet)")
    for i, k in enumerate(reversed(mevcut_kanitlar), 1):
        degisim = k.get("degisim", 0)
        degisim_renk = "#4ade80" if degisim >= 0 else "#f87171"
        degisim_isaret = "+" if degisim >= 0 else ""
        with st.expander(f"Kanıt {i} — {k['tarih']} · {k['karar']}"):
            st.markdown(f"""
<div class="kanit-kart">
<b>Açıklama:</b> {k.get('aciklama', '—')}<br>
<b>Kaynak:</b> {k.get('link') or '—'}<br>
<b>Görsel:</b> {k.get('gorsel') or '—'}<br>
<b>Video:</b> {k.get('video') or '—'}<br>
<b>Skor Değişimi:</b>
<span style="color:{degisim_renk}">{degisim_isaret}{degisim}</span><br>
<b>AI Değerlendirmesi:</b> {k.get('ai_aciklama', '—')}
</div>
""", unsafe_allow_html=True)
else:
    st.info("Bu haber için henüz kanıt eklenmemiş. İlk kanıtı sen ekle!")