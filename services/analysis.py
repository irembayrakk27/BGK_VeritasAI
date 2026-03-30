import os
import re
from groq import Groq
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
def get_api_key():
    try:
        import streamlit as st
        return os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
    except:
        return os.getenv("GROQ_API_KEY", "")

API_KEY = get_api_key()
if not API_KEY:
    raise ValueError("GROQ_API_KEY bulunamadı. .env dosyasını kontrol et.")

client = Groq(api_key=API_KEY)

SISTEM_MESAJI = """
Sen VeritasAI'ın baş analiz motorusun. 10 yıllık gazetecilik ve
dezenformasyon araştırması deneyimine sahip bir Türk dil uzmanısın.

Görevin:
- Haber metinlerini tarafsız ve bilimsel bir yaklaşımla analiz etmek
- Manipülasyon tekniklerini tespit etmek
- Kaynak güvenilirliğini değerlendirmek
- 0-100 arası net bir güvenilirlik skoru vermek

DİL KURALLARI — KESİNLİKLE UYULMASI ZORUNLU:
- Yanıtlarını SADECE ve SADECE Türkçe yaz
- Hiçbir İngilizce kelime kullanma (numerous, claim, bias, fake gibi kelimeler yasak)
- Türkçe karşılıkları kullan: çok sayıda, iddia, önyargı, sahte
- Türkçe dilbilgisi kurallarına tam uy
- Akademik ve profesyonel bir Türkçe kullan

GENEL KURALLAR:
- Tarafsız ve objektif ol, siyasi görüş belirtme
- Sadece metinde olan bilgileri değerlendir
- Yanıtını SADECE belirtilen formatta ver, fazladan açıklama ekleme
"""

def parse(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""

def on_analiz(text: str) -> dict:
    prompt = f"""Aşağıdaki haber metnini hızlıca ön analiz et. SADECE şu formatta yanıt ver:

SKOR: [0-100 arası tek bir sayı]
GÜVEN_ETİKETİ: [Güvenilir / Şüpheli / Güvenilmez]
MANIPÜLASYON: [Tespit edilen manipülasyon tekniği, yoksa "Tespit edilmedi"]
KAYNAK_KALİTESİ: [Güçlü / Orta / Zayıf / Kaynak yok]
ÖN_YORUM: [1-2 cümle kısa değerlendirme]

Metin:
{text}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SISTEM_MESAJI},
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        temperature=0.2,
    )
    raw = response.choices[0].message.content
    skor_str = parse(r"SKOR:\s*(\d+)", raw)
    skor = max(0, min(100, int(skor_str))) if skor_str else 50

    return {
        "skor": skor,
        "guven_etiketi": parse(r"GÜVEN_ETİKETİ:\s*(.+)", raw),
        "manipulasyon": parse(r"MANIPÜLASYON:\s*(.+)", raw),
        "kaynak_kalitesi": parse(r"KAYNAK_KALİTESİ:\s*(.+)", raw),
        "on_yorum": parse(r"ÖN_YORUM:\s*(.+)", raw),
        "ham": raw,
    }

def derin_analiz(text: str, on_sonuc: dict) -> dict:
    prompt = f"""Bir meslektaşın bu haberi analiz etti ve şu sonuçlara ulaştı:
- Güvenilirlik Skoru: %{on_sonuc['skor']}
- Manipülasyon: {on_sonuc['manipulasyon']}
- Kaynak Kalitesi: {on_sonuc['kaynak_kalitesi']}
- Ön Yorum: {on_sonuc['on_yorum']}

Şimdi sen bu haberi bağımsız olarak daha derinlemesine analiz et.
SADECE şu formatta yanıt ver:

SKOR: [0-100 arası tek bir sayı]
GÜVEN_ETİKETİ: [Güvenilir / Şüpheli / Güvenilmez]
MANIPÜLASYON: [Tespit edilen manipülasyon tekniği, yoksa "Tespit edilmedi"]
KAYNAK_KALİTESİ: [Güçlü / Orta / Zayıf / Kaynak yok]
GEREKÇE_1: [Birinci gerekçe, 3-4 cümle, detaylı açıkla]
GEREKÇE_2: [İkinci gerekçe, 3-4 cümle, detaylı açıkla]
GEREKÇE_3: [Üçüncü gerekçe, 3-4 cümle, detaylı açıkla]
ÖZET: [Genel değerlendirme, 4-5 cümle, kapsamlı değerlendir]

Analiz edilecek metin:
{text}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SISTEM_MESAJI},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
        temperature=0.2,
    )
    raw = response.choices[0].message.content
    skor_str = parse(r"SKOR:\s*(\d+)", raw)
    skor = max(0, min(100, int(skor_str))) if skor_str else 50

    gerekceler = []
    for i in range(1, 4):
        g = parse(rf"GEREKÇE_{i}:\s*(.+)", raw)
        if g:
            gerekceler.append(g)

    return {
        "skor": skor,
        "guven_etiketi": parse(r"GÜVEN_ETİKETİ:\s*(.+)", raw),
        "manipulasyon": parse(r"MANIPÜLASYON:\s*(.+)", raw),
        "kaynak_kalitesi": parse(r"KAYNAK_KALİTESİ:\s*(.+)", raw),
        "gerekceler": gerekceler,
        "ozet": parse(r"ÖZET:\s*(.+)", raw),
        "kaynaklar": kaynak_ara(text[:200]),
        "ham": raw,
    }

def analyze_news_text(text: str, language: str = "tr", max_retries: int = 1) -> dict:
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            on_sonuc = on_analiz(text)
            derin_sonuc = derin_analiz(text, on_sonuc)
            final_skor = round((on_sonuc["skor"] + derin_sonuc["skor"]) / 2)

            return {
                "skor": final_skor,
                "guven_etiketi": derin_sonuc["guven_etiketi"],
                "manipulasyon": derin_sonuc["manipulasyon"],
                "kaynak_kalitesi": derin_sonuc["kaynak_kalitesi"],
                "gerekceler": derin_sonuc["gerekceler"],
                "ozet": derin_sonuc["ozet"],
                "kaynaklar": derin_sonuc.get("kaynaklar", []),
                "on_analiz": on_sonuc,
            }
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue
    raise RuntimeError(f"Groq API hatası: {last_error}")

def kanit_analiz(haber_metni: str, kanit: dict, mevcut_skor: int) -> dict:
    kanit_metni = f"""
Kanıt Açıklaması: {kanit.get('aciklama', '')}
Kanıt Linki: {kanit.get('link', 'Belirtilmedi')}
Dosya Eki: {kanit.get('dosya_adi', 'Yok')}
"""
    prompt = f"""Bir kullanıcı aşağıdaki haber için kanıt sundu.
Mevcut güvenilirlik skoru: %{mevcut_skor}

HABER METNİ:
{haber_metni}

KULLANICI KANITI:
{kanit_metni}

SADECE şu formatta yanıt ver:

KARAR: [Doğrular / Çürütür / Kısmen Doğrular / Yetersiz Kanıt]
SKOR_DEĞİŞİMİ: [+5 ile +20 arası sayı veya -5 ile -20 arası sayı veya 0]
YENİ_SKOR: [0-100 arası yeni skor]
KANIT_GÜVENİLİRLİĞİ: [Güçlü / Orta / Zayıf]
AÇIKLAMA: [Kanıtı neden bu şekilde değerlendirdin, 2-3 cümle]"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SISTEM_MESAJI},
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        temperature=0.2,
    )
    raw = response.choices[0].message.content
    skor_str = parse(r"YENİ_SKOR:\s*(\d+)", raw)
    yeni_skor = max(0, min(100, int(skor_str))) if skor_str else mevcut_skor
    degisim_str = parse(r"SKOR_DEĞİŞİMİ:\s*([+-]?\d+)", raw)
    degisim = int(degisim_str) if degisim_str else 0

    return {
        "karar": parse(r"KARAR:\s*(.+)", raw),
        "skor_degisimi": degisim,
        "yeni_skor": yeni_skor,
        "kanit_guvenirligi": parse(r"KANIT_GÜVENİLİRLİĞİ:\s*(.+)", raw),
        "aciklama": parse(r"AÇIKLAMA:\s*(.+)", raw),
        "ham": raw,
    }
# ── Tavily Web Arama ──────────────────────────────────────────────
def kaynak_ara(sorgu: str) -> list:
    try:
        from tavily import TavilyClient
        TAVILY_KEY = os.getenv("TAVILY_API_KEY") or st.secrets.get("TAVILY_API_KEY", "")
        if not TAVILY_KEY:
            print("TAVILY_API_KEY bulunamadı!")
            return []
        tavily = TavilyClient(api_key=TAVILY_KEY)
        sonuclar = tavily.search(
            query=sorgu,
            max_results=3,
            search_depth="basic",
        )
        return sonuclar.get("results", [])
    except Exception as e:
        print(f"Tavily hatası: {e}")
        return []