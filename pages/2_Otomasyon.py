
"""
VeritasAI — Manuel ReAct Agent (LangChain bağımlılığı yok)
===========================================================
Python 3.14 uyumlu. Groq API ile sıfırdan ReAct döngüsü.
Yeni: URL'den metin çekme, Video analiz (YouTube), Görsel analiz
"""

import os
import re
import json
import base64
import tempfile
import html
from pathlib import Path
from io import BytesIO

import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

st.set_page_config(
    page_title="VeritasAI — ReAct Agent",
    page_icon="🤖",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

.stApp { background: linear-gradient(135deg, #0d0d2b 0%, #1a0533 100%); }
h1, h2, h3 { color: #c084fc !important; font-family: 'Syne', sans-serif !important; }
p, label, .stMarkdown { color: #e2d9f3 !important; }
.stButton > button {
    background: linear-gradient(90deg, #7c3aed, #4f46e5) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; font-weight: 700 !important;
    font-family: 'Syne', sans-serif !important;
}
.stTextArea textarea, .stTextInput input {
    background: #1e1b4b !important; color: #e2d9f3 !important;
    border: 1px solid #7c3aed !important; border-radius: 10px !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.dusunce {
    background: #12103a; border-left: 4px solid #7c3aed;
    border-radius: 8px; padding: 0.7rem 1rem; margin: 0.3rem 0;
    color: #c4b5fd; font-size: 0.88rem;
}
.tool-cagri {
    background: #1a1035; border-left: 4px solid #4f46e5;
    border-radius: 8px; padding: 0.7rem 1rem; margin: 0.3rem 0;
    color: #a78bfa; font-size: 0.85rem; font-family: 'JetBrains Mono', monospace;
}
.gozlem {
    background: #0f1a10; border-left: 4px solid #22c55e;
    border-radius: 8px; padding: 0.7rem 1rem; margin: 0.3rem 0;
    color: #86efac; font-size: 0.85rem;
}
.sonuc-kutu {
    background: linear-gradient(160deg, #0f0c29 0%, #1a0533 50%, #0d1b2a 100%);
    border-radius: 16px; padding: 0rem;
    border: 1px solid #4f46e5;
    margin-top: 1rem;
    overflow: hidden;
    box-shadow: 0 0 40px rgba(124,58,237,0.15), 0 0 80px rgba(79,70,229,0.08);
}
.rapor-header {
    background: linear-gradient(90deg, #7c3aed22, #4f46e511);
    border-bottom: 1px solid #4f46e560;
    padding: 1rem 1.5rem;
    display: flex; align-items: center; gap: 0.7rem;
}
.rapor-body { padding: 1.5rem; }
.rapor-satir {
    display: flex; align-items: flex-start; gap: 0.8rem;
    padding: 0.75rem 1rem; border-radius: 10px;
    margin-bottom: 0.5rem; line-height: 1.6;
    transition: background 0.2s;
}
.rapor-satir:hover { background: #ffffff08; }
.rapor-satir.guvensiz {
    background: #2d0a0a; border-left: 3px solid #ef4444;
    box-shadow: inset 0 0 20px #ef444410;
}
.rapor-satir.guvenilir {
    background: #0a2d0f; border-left: 3px solid #22c55e;
    box-shadow: inset 0 0 20px #22c55e10;
}
.rapor-satir.uyari {
    background: #2d1f0a; border-left: 3px solid #f59e0b;
    box-shadow: inset 0 0 20px #f59e0b10;
}
.rapor-satir.bilgi {
    background: #0a1a2d; border-left: 3px solid #3b82f6;
    box-shadow: inset 0 0 20px #3b82f610;
}
.skor-badge {
    display: inline-block; font-size: 1.8rem; font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    padding: 0.3rem 1rem; border-radius: 10px;
    background: #1e1b4b; border: 2px solid #7c3aed;
    color: #c084fc; letter-spacing: -1px;
    text-shadow: 0 0 20px #7c3aed80;
}
.verdict-chip {
    display: inline-block; padding: 0.3rem 1.2rem;
    border-radius: 999px; font-weight: 700; font-size: 0.9rem;
    font-family: 'Syne', sans-serif; letter-spacing: 0.05em;
}
.verdict-false { background: #ef444420; color: #fca5a5; border: 1px solid #ef4444; }
.verdict-true  { background: #22c55e20; color: #86efac; border: 1px solid #22c55e; }
.verdict-mix   { background: #f59e0b20; color: #fcd34d; border: 1px solid #f59e0b; }
.input-tab {
    background: #12103a; border-radius: 12px; padding: 1.2rem 1.5rem;
    border: 1px solid #4f46e5; margin-bottom: 1rem;
}
.badge {
    display: inline-block; padding: 0.2rem 0.7rem;
    border-radius: 999px; font-size: 0.75rem; font-weight: 700;
    font-family: 'JetBrains Mono', monospace; margin-right: 0.4rem;
}
.badge-url  { background: #1e3a5f; color: #60a5fa; border: 1px solid #3b82f6; }
.badge-vid  { background: #2d1a0e; color: #fb923c; border: 1px solid #f97316; }
.badge-img  { background: #1a1035; color: #c084fc; border: 1px solid #9333ea; }
.badge-txt  { background: #0f1a10; color: #4ade80; border: 1px solid #22c55e; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🤖 ReAct Agent — Otomatik Haber Doğrulama")
st.markdown("##### Groq LLM + VeritasAI Araçları ile Çok Adımlı Akıl Yürütme")

st.markdown("""
<div style="background:#12103a;border-radius:12px;padding:1rem 1.5rem;
border:1px solid #4f46e5;margin-bottom:1rem">
<p style="color:#a78bfa;margin:0;font-size:0.9rem">
<b>⚙️ ReAct Döngüsü:</b> Düşün → Araç Seç → Çalıştır → Gözlemle → Tekrar Düşün → Final Rapor<br>
<span class="badge badge-url">🔗 URL</span>
<span class="badge badge-vid">🎥 Video</span>
<span class="badge badge-img">🖼️ Görsel</span>
<span class="badge badge-txt">📝 Metin</span>
Tüm girdi türleri desteklenir.
</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Yardımcı: URL → Metin ─────────────────────────────────────────

def url_den_metin_cek(url: str) -> str:
    """BeautifulSoup ile URL'den temiz metin çeker."""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Gereksiz tagları temizle
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        # Önce <article>, yoksa <main>, yoksa <body>
        container = (
            soup.find("article")
            or soup.find("main")
            or soup.find("body")
        )
        text = container.get_text(separator="\n", strip=True) if container else soup.get_text()

        # Çok fazla boş satırı temizle
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(lines[:300])  # max 300 satır

    except ImportError:
        return "HATA: requests veya beautifulsoup4 yüklü değil. `pip install requests beautifulsoup4`"
    except Exception as e:
        return f"URL çekme hatası: {e}"


# ── Yardımcı: YouTube → Transcript ───────────────────────────────

def youtube_transcript_cek(url: str) -> str:
    """youtube_transcript_api ile Türkçe/İngilizce transcript çeker."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # Video ID çıkar
        vid_id = None
        patterns = [
            r"(?:v=|youtu\.be/)([A-Za-z0-9_\-]{11})",
            r"(?:embed/)([A-Za-z0-9_\-]{11})",
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                vid_id = m.group(1)
                break

        if not vid_id:
            return f"Geçerli YouTube URL'si bulunamadı: {url}"

        # Önce Türkçe, sonra İngilizce dene
        transcript = None
        for lang in [["tr"], ["en"], None]:
            try:
                if lang:
                    transcript = YouTubeTranscriptApi.get_transcript(vid_id, languages=lang)
                else:
                    transcript = YouTubeTranscriptApi.get_transcript(vid_id)
                break
            except Exception:
                continue

        if not transcript:
            return "Transcript bulunamadı (video kapalı altyazı içermiyor olabilir)."

        # Metni birleştir
        full = " ".join(chunk["text"] for chunk in transcript)
        return full[:4000]  # max 4000 karakter

    except ImportError:
        return "HATA: youtube_transcript_api yüklü değil. `pip install youtube-transcript-api`"
    except Exception as e:
        return f"YouTube transcript hatası: {e}"


# ── Yardımcı: Görsel → Base64 ─────────────────────────────────────

def gorsel_base64_al(uploaded_file) -> tuple[str, str]:
    """Yüklenen görseli base64'e çevirir. (base64_str, media_type) döner."""
    ext = uploaded_file.name.lower().split(".")[-1]
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "gif": "image/gif", "webp": "image/webp",
    }
    media_type = mime_map.get(ext, "image/jpeg")
    data = base64.standard_b64encode(uploaded_file.read()).decode("utf-8")
    return data, media_type

# ── Yardımcı: Rapor HTML Oluşturucu ─────────────────────────────────
def rapor_html_olustur(metin: str) -> str:
    """Ham rapor metnini renkli, yapılandırılmış HTML'e çevirir."""
    temiz_metin = (metin or "").replace("```html", "").replace("```", "")
    satirlar = temiz_metin.strip().splitlines()
    html_parts = []

    # Anahtar kelime → stil eşleşmesi
    guvensiz_kw = ["yanlış", "sahte", "dezenformasyon", "manipülasyon", "tehlikeli",
                   "injection", "adversarial", "güvensiz", "false", "risk"]
    guvenilir_kw = ["güvenilir", "doğrulandı", "temiz", "gerçek", "onaylandı",
                    "doğru", "kaynak kalitesi", "verified", "true"]
    uyari_kw = ["dikkat", "belirsiz", "doğrulanamadı", "kısmen", "şüpheli",
                "uyarı", "mixed", "karışık"]
    bilgi_kw = ["skor:", "kaynak:", "özet:", "analiz:", "rapor:", "sonuç:", "%"]

    # Başlık satırını ayır
    baslik = satirlar[0] if satirlar else "Analiz Raporu"
    baslik = html.escape(baslik)
    govde_satirlar = satirlar[1:] if len(satirlar) > 1 else satirlar

    # Header
    html_parts.append(f"""
    <div class="rapor-header">
        <span style="font-size:1.3rem">📊</span>
        <span style="font-family:'Syne',sans-serif;font-weight:700;color:#c084fc;font-size:1.05rem">
            {baslik[:120]}
        </span>
    </div>
    <div class="rapor-body">
    """)

    for satir in govde_satirlar:
        s = satir.strip()
        if not s:
            html_parts.append('<div style="height:0.4rem"></div>')
            continue

        s_escaped = html.escape(s)
        sl = s.lower()
        css_cls = ""
        ikon = "▸"

        if any(k in sl for k in guvensiz_kw):
            css_cls = "guvensiz"; ikon = "⚠️"
        elif any(k in sl for k in guvenilir_kw):
            css_cls = "guvenilir"; ikon = "✅"
        elif any(k in sl for k in uyari_kw):
            css_cls = "uyari"; ikon = "🔶"
        elif any(k in sl for k in bilgi_kw):
            css_cls = "bilgi"; ikon = "ℹ️"

        # Skor tespiti → badge
        skor_match = re.search(r"(\d{2,3})\s*[/|%]?\s*100|güven\s*skoru[:\s]+(\d+)", sl)
        if skor_match:
            skor_val = skor_match.group(1) or skor_match.group(2)
            skor_int = int(skor_val)
            renk = "#22c55e" if skor_int >= 70 else ("#f59e0b" if skor_int >= 40 else "#ef4444")
            s_escaped = re.sub(
                r"(\d{2,3})\s*[/|%]?\s*100",
                f'<span class="skor-badge" style="color:{renk};border-color:{renk}">{skor_val}/100</span>',
                s_escaped, count=1
            )

        # Verdict tespiti
        if "yanlış" in sl or "false" in sl or "sahte" in sl:
            s_escaped += ' <span class="verdict-chip verdict-false">YANLIŞ</span>'
        elif "doğrulandı" in sl or "gerçek" in sl and "değil" not in sl:
            s_escaped += ' <span class="verdict-chip verdict-true">DOĞRULANDI</span>'

        row_cls = f'rapor-satir {css_cls}' if css_cls else 'rapor-satir'
        html_parts.append(f'<div class="{row_cls}"><span>{ikon}</span><span style="color:#e2d9f3">{s_escaped}</span></div>')

    html_parts.append("</div>")  # rapor-body kapat
    return "\n".join(html_parts)

# ── Tool Fonksiyonları ────────────────────────────────────────────

def tool_guvenlik_tara(metin: str) -> str:
    try:
        from services.security import guvenlik_tara
        r = guvenlik_tara(metin)
        return (
            f"Güvenlik Durumu: {r['seviye']} | "
            f"Injection: {r['injection_sayisi']} | "
            f"Adversarial: {r['adversarial_sayisi']} | "
            f"{r['oneri']}"
        )
    except Exception as e:
        return f"Güvenlik tarama hatası: {e}"


def tool_haber_analiz(metin: str) -> str:
    try:
        from services.analysis import analyze_news_text
        r = analyze_news_text(metin[:2000])
        return (
            f"Güven Skoru: {r.get('skor')} | "
            f"Karar: {r.get('guven_etiketi')} | "
            f"Manipülasyon: {r.get('manipulasyon')} | "
            f"Kaynak Kalitesi: {r.get('kaynak_kalitesi')} | "
            f"Özet: {r.get('ozet', '')[:200]}"
        )
    except Exception as e:
        return f"Analiz hatası: {e}"


def tool_kaynak_dogrula(metin: str) -> str:
    try:
        from services.rag_pipeline import capraz_kaynak_dogrula
        r = capraz_kaynak_dogrula(metin[:1000])
        if r.get("hata"):
            return f"RAG hatası: {r['hata']}"
        return (
            f"Karar: {r.get('karar')} | "
            f"Uzlaşma: %{r.get('kaynak_uzlasmasi')} | "
            f"Ana Bulgu: {r.get('ana_bulgu', '')[:150]} | "
            f"Özet: {r.get('ozet', '')[:150]}"
        )
    except Exception as e:
        return f"RAG hatası: {e}"


def tool_url_icerik(url: str) -> str:
    """URL'den web sayfası içeriğini çeker ve döner."""
    if not url.startswith("http"):
        return "Geçersiz URL formatı. https:// ile başlamalı."
    icerik = url_den_metin_cek(url)
    if icerik.startswith("HATA") or icerik.startswith("URL çekme"):
        return icerik
    # Session state'e kaydet — metin analizi için kullanılacak
    st.session_state["extracted_text"] = icerik
    return f"URL başarıyla çekildi. Karakter sayısı: {len(icerik)}. İlk 300 karakter: {icerik[:300]}"


def tool_video_analiz(url: str) -> str:
    """YouTube video transcript'ini çeker ve içerik özeti döner."""
    transcript = youtube_transcript_cek(url)
    if transcript.startswith("HATA") or transcript.startswith("Geçersiz") or transcript.startswith("Transcript"):
        return transcript
    st.session_state["extracted_text"] = transcript
    # Groq ile kısa özet
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        ozet_yanit = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": (
                    f"Aşağıdaki YouTube video transkriptini Türkçe olarak 3-4 cümleyle özetle. "
                    f"İçerik doğrulama açısından önemli iddiaları vurgula:\n\n{transcript[:3000]}"
                )
            }],
            temperature=0.2,
            max_tokens=300,
        )
        ozet = ozet_yanit.choices[0].message.content.strip()
    except Exception as e:
        ozet = f"Özet oluşturulamadı: {e}"
    return f"Video transkripti alındı ({len(transcript)} karakter). Özet: {ozet}"


def tool_gorsel_analiz(placeholder: str = "") -> str:
    """
    Session state'teki görsel verisini Groq Vision ile analiz eder.
    Görsel daha önce yüklenmiş olmalı (st.session_state['gorsel_b64']).
    """
    gorsel_data = st.session_state.get("gorsel_b64")
    gorsel_mime = st.session_state.get("gorsel_mime", "image/jpeg")

    if not gorsel_data:
        return "Görsel bulunamadı. Lütfen önce 'Görsel Analiz' sekmesinden görsel yükleyin."

    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        yanit = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{gorsel_mime};base64,{gorsel_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "Bu görseli haber doğrulama perspektifinden analiz et. "
                            "Türkçe olarak yanıtla:\n"
                            "1. Görselde ne görülüyor?\n"
                            "2. Manipülasyon veya deepfake belirtisi var mı?\n"
                            "3. Metadata veya bağlam tutarsızlığı?\n"
                            "4. Genel güvenilirlik değerlendirmesi (0-100 skor)"
                        )
                    }
                ]
            }],
            temperature=0.1,
            max_tokens=500,
        )
        return yanit.choices[0].message.content.strip()
    except Exception as e:
        return f"Görsel analiz hatası: {e}"


TOOLS = {
    "guvenlik_tara": {
        "func": tool_guvenlik_tara,
        "desc": "OWASP LLM güvenlik taraması. Prompt injection ve adversarial input tespiti.",
        "ikon": "🛡️",
        "renk": "#f87171",
        "arguman": "haber_metni",
    },
    "haber_analiz": {
        "func": tool_haber_analiz,
        "desc": "Çift aşamalı Groq analizi. Güven skoru, manipülasyon, kaynak kalitesi.",
        "ikon": "🔍",
        "renk": "#a78bfa",
        "arguman": "haber_metni",
    },
    "kaynak_dogrula": {
        "func": tool_kaynak_dogrula,
        "desc": "RAG pipeline. Tavily + ChromaDB ile çapraz kaynak doğrulama.",
        "ikon": "🔗",
        "renk": "#60a5fa",
        "arguman": "haber_metni",
    },
    "url_icerik": {
        "func": tool_url_icerik,
        "desc": "URL'den web sayfası metnini çeker (BeautifulSoup). Haber sitelerini scrape eder.",
        "ikon": "🌐",
        "renk": "#34d399",
        "arguman": "url",
    },
    "video_analiz": {
        "func": tool_video_analiz,
        "desc": "YouTube video transcript'ini çeker ve Groq ile özetler. Video haberler için kullan.",
        "ikon": "🎥",
        "renk": "#fb923c",
        "arguman": "youtube_url",
    },
    "gorsel_analiz": {
        "func": tool_gorsel_analiz,
        "desc": "Groq Vision ile yüklenen görseli analiz eder. Manipülasyon ve deepfake tespiti.",
        "ikon": "🖼️",
        "renk": "#e879f9",
        "arguman": "yok (önceden yüklenen görsel kullanılır)",
    },
}

TOOL_LISTESI = "\n".join(
    f"- {name}: {info['desc']}"
    for name, info in TOOLS.items()
)

SISTEM_PROMPTU = f"""Sen VeritasAI'nin haber doğrulama agentısın.
Sana bir haber metni, URL, YouTube linki veya görsel analizi sonucu verilecek.

KULLANILABILIR ARAÇLAR:
{TOOL_LISTESI}

KURALLAR:
1. Giriş bir URL ise → önce url_icerik çalıştır, dönen metni haber_analiz'e ver
2. Giriş bir YouTube URL'si ise → video_analiz çalıştır, dönen özeti haber_analiz'e ver
3. Görsel yüklendiyse → gorsel_analiz çalıştır
4. Her zaman guvenlik_tara çalıştır
5. Sonra haber_analiz çalıştır
6. Son olarak kaynak_dogrula çalıştır
7. Tüm sonuçları birleştirip kapsamlı Türkçe rapor yaz

YANIT FORMATI:
Thought: [Ne yapacağını açıkla]
Action: [tool_adı]
Action Input: [argüman]

Tüm araçları çalıştırdıktan sonra:
Thought: Tüm analizleri tamamladım
Final Answer: [Kapsamlı Türkçe rapor]"""


def react_dongusu(girdi: str, adim_placeholder, gorsel_var: bool = False):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    kullanici_mesaji = f"Analiz edilecek içerik: {girdi}"
    if gorsel_var:
        kullanici_mesaji += "\nNot: Kullanıcı bir görsel de yükledi, gorsel_analiz tool'unu mutlaka çalıştır."

    mesajlar = [
        {"role": "system", "content": SISTEM_PROMPTU},
        {"role": "user", "content": kullanici_mesaji},
    ]

    adimlar_html = ""
    max_iter = 10

    def guncelle():
        adim_placeholder.markdown(adimlar_html, unsafe_allow_html=True)

    for _ in range(max_iter):
        yanit = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mesajlar,
            temperature=0.1,
            max_tokens=1200,
        )
        icerik = yanit.choices[0].message.content.strip()
        mesajlar.append({"role": "assistant", "content": icerik})

        if "Final Answer:" in icerik:
            final = icerik.split("Final Answer:")[-1].strip()
            return final

        thought = re.search(r"Thought:\s*(.+?)(?=Action:|$)", icerik, re.DOTALL)
        if thought:
            adimlar_html += f'<div class="dusunce">💭 <b>Düşünce:</b> {thought.group(1).strip()[:300]}</div>'
            guncelle()

        action = re.search(r"Action:\s*(\w+)", icerik)
        if not action:
            break

        tool_adi = action.group(1).strip()
        action_input_match = re.search(r"Action Input:\s*(.+?)(?=Thought:|Action:|Observation:|$)", icerik, re.DOTALL)
        action_input = action_input_match.group(1).strip() if action_input_match else girdi

        if tool_adi not in TOOLS:
            gozlem = f"Bilinmeyen araç: {tool_adi}"
        else:
            info = TOOLS[tool_adi]
            adimlar_html += (
                f'<div class="tool-cagri">'
                f'{info["ikon"]} <b style="color:{info["renk"]}">{tool_adi}</b> çalıştırılıyor...'
                f'<span style="color:#6b7280;font-size:0.8rem"> → {action_input[:80]}</span>'
                f'</div>'
            )
            guncelle()

            # gorsel_analiz argüman almaz
            if tool_adi == "gorsel_analiz":
                gozlem = info["func"]()
            else:
                gozlem = info["func"](action_input)

            adimlar_html += f'<div class="gozlem">✅ <b>Sonuç:</b> {gozlem[:400]}</div>'
            guncelle()

        mesajlar.append({
            "role": "user",
            "content": f"Observation: {gozlem}\n\nDevam et."
        })

    return "Agent maksimum adım sayısına ulaştı."


# ── UI ────────────────────────────────────────────────────────────

st.markdown("### 🛠️ Analiz Kaynağı Seç")

sekme = st.radio(
    "girdi_turu",
    ["📝 Metin", "🔗 URL", "🎥 YouTube Video", "🖼️ Görsel Analiz"],
    horizontal=True,
    label_visibility="collapsed",
)

haber = ""
gorsel_var = False

# ── Metin girişi ──────────────────────────────────────────────────
if sekme == "📝 Metin":
    st.markdown('<div class="input-tab">', unsafe_allow_html=True)
    st.markdown("#### 📝 Haber Metni Analizi")
    haber = st.text_area(
        "metin_input",
        height=180,
        placeholder="Haberin tam metnini buraya yapıştır...",
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ── URL girişi ────────────────────────────────────────────────────
elif sekme == "🔗 URL":
    st.markdown('<div class="input-tab">', unsafe_allow_html=True)
    st.markdown("#### 🌐 Haber URL Analizi")
    st.markdown(
        "<p style='color:#94a3b8;font-size:0.85rem'>Haber sitesinin URL'sini girin. "
        "Agent önce sayfayı çekip metni analiz eder.</p>",
        unsafe_allow_html=True,
    )
    url_input = st.text_input(
        "url_input",
        placeholder="https://www.haberler.com/gundem/cumhurbaskani-erdogan-son-dakika-aciklamasi-5421973.html",
        label_visibility="collapsed",
    )
    if url_input:
        haber = url_input  # Agent url_icerik tool'unu kullanacak
    st.markdown('</div>', unsafe_allow_html=True)

# ── YouTube Video ─────────────────────────────────────────────────
elif sekme == "🎥 YouTube Video":
    st.markdown('<div class="input-tab">', unsafe_allow_html=True)
    st.markdown("#### 🎥 Video Analizi")
    st.markdown(
        "<p style='color:#94a3b8;font-size:0.85rem'>YouTube video bağlantısını girin. "
        "Agent transkripti çekip haber doğrulama analizi yapar. "
        "<b style='color:#fb923c'>Altyazısı olan videolar için çalışır.</b></p>",
        unsafe_allow_html=True,
    )
    yt_url = st.text_input(
        "yt_input",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed",
    )
    if yt_url:
        haber = yt_url
    st.markdown('</div>', unsafe_allow_html=True)

# ── Görsel Analiz ─────────────────────────────────────────────────
elif sekme == "🖼️ Görsel Analiz":
    st.markdown('<div class="input-tab">', unsafe_allow_html=True)
    st.markdown("#### 🖼️ Görsel Analizi + İsteğe Bağlı Metin")
    st.markdown(
        "<p style='color:#94a3b8;font-size:0.85rem'>"
        "Görsel yükleyin (ekran görüntüsü, haber fotoğrafı, infografik vb.). "
        "Agent <b style='color:#e879f9'>Groq Vision (llama-3.2-90b)</b> ile analiz edecek.</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        yuklenen = st.file_uploader(
            "Görsel Yükle",
            type=["jpg", "jpeg", "png", "webp", "gif"],
            label_visibility="visible",
        )
        if yuklenen:
            b64, mime = gorsel_base64_al(yuklenen)
            st.session_state["gorsel_b64"] = b64
            st.session_state["gorsel_mime"] = mime
            gorsel_var = True
            st.success(f"✅ Görsel yüklendi: {yuklenen.name} ({yuklenen.size // 1024} KB)")

    with col2:
        if yuklenen:
            # Önizleme
            yuklenen.seek(0)
            st.image(yuklenen, caption="Yüklenen Görsel", use_container_width=True)

    ek_metin = st.text_area(
        "gorsel_ek_metin",
        height=80,
        placeholder="İsteğe bağlı: Görselle ilgili bağlam veya metin (haber başlığı vb.)",
        label_visibility="collapsed",
    )
    haber = ek_metin if ek_metin else "Yüklenen görseli analiz et."
    st.markdown('</div>', unsafe_allow_html=True)

# ── Çalıştır Butonu ───────────────────────────────────────────────
baslat_disabled = not bool(haber.strip()) and not gorsel_var
baslat = st.button(
    "🚀 Agent'ı Çalıştır",
    type="primary",
    disabled=baslat_disabled,
)

st.divider()

if baslat and (haber.strip() or gorsel_var):
    st.markdown("### 🧠 Agent Düşünce Akışı")
    adim_placeholder = st.empty()

    with st.spinner("Agent çalışıyor, ReAct döngüsü yürütülüyor..."):
        try:
            final = react_dongusu(haber, adim_placeholder, gorsel_var=gorsel_var)
            st.session_state["agent_sonuc"] = final
        except Exception as e:
            st.error(f"❌ Agent hatası: {e}")
            st.stop()

    st.divider()
    st.markdown("### 📋 Agent Final Raporu")
    rapor_html = rapor_html_olustur(st.session_state.get("agent_sonuc", ""))
    st.markdown(
        '<div class="sonuc-kutu">' + rapor_html + "</div>",
        unsafe_allow_html=True
    )

elif st.session_state.get("agent_sonuc"):
    st.markdown("### 📋 Son Agent Raporu")
    rapor_html = rapor_html_olustur(st.session_state["agent_sonuc"])
    st.markdown(
        '<div class="sonuc-kutu">' + rapor_html + "</div>",
        unsafe_allow_html=True
    )

st.divider()
st.markdown("### 🏗️ Sistem Nasıl Çalışır?")
st.markdown("""
<div style="background:#12103a;border-radius:12px;padding:1.2rem 1.5rem;border:1px solid #4f46e5">
<p style="color:#e2d9f3;margin:0">
<b style="color:#f87171">1. 🛡️ Güvenlik Taraması</b> — OWASP LLM Top 10: prompt injection + adversarial input<br><br>
<b style="color:#a78bfa">2. 🔍 Haber Analizi</b> — Çift aşamalı Groq pipeline: güven skoru + manipülasyon tespiti<br><br>
<b style="color:#60a5fa">3. 🔗 Kaynak Doğrulama</b> — RAG: Tavily + ChromaDB + Multi-Query + HyDE + RRF<br><br>
<b style="color:#34d399">4. 🌐 URL → Metin</b> — BeautifulSoup ile haber sitelerini scrape eder<br><br>
<b style="color:#fb923c">5. 🎥 Video Analiz</b> — YouTube transcript API + Groq özetleme<br><br>
<b style="color:#e879f9">6. 🖼️ Görsel Analiz</b> — Groq Vision (llama-3.2-90b): deepfake + manipülasyon tespiti<br><br>
<b style="color:#4ade80">7. 📊 Final Rapor</b> — Agent tüm sonuçları birleştirip kapsamlı Türkçe rapor üretir
</p>
</div>
""", unsafe_allow_html=True)