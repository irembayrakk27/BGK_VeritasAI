import os
import re
from groq import Groq
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY bulunamadı. .env dosyasını kontrol et.")

client = Groq(api_key=API_KEY)

# ── Sistem Mesajı ─────────────────────────────────────────────────
SISTEM_MESAJI = """
Sen VeritasAI'ın baş analiz motorusun. 10 yıllık gazetecilik ve 
dezenformasyon araştırması deneyimine sahip bir uzman olarak görev yapıyorsun.

Görevin:
- Haber metinlerini tarafsız ve bilimsel bir yaklaşımla analiz etmek
- Manipülasyon tekniklerini tespit etmek (duygusal dil, abartı, eksik bağlam vb.)
- Kaynak güvenilirliğini değerlendirmek
- 0-100 arası net bir güvenilirlik skoru vermek

Kuralların:
- Her zaman Türkçe yanıt ver
- Tarafsız ve objektif ol, siyasi görüş belirtme
- Sadece metinde olan bilgileri değerlendir, tahmin yürütme
- Yanıtını SADECE belirtilen formatta ver, fazladan açıklama ekleme
"""

# ── Yardımcı: parse ───────────────────────────────────────────────
def parse(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""

# ── 1. Çağrı: Hızlı Ön Analiz ────────────────────────────────────
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

# ── 2. Çağrı: Derin Doğrulama ────────────────────────────────────
def derin_analiz(text: str, on_sonuc: dict) -> dict:
    prompt = f"""Bir meslektaşın bu haberi analiz etti ve şu sonuçlara ulaştı:
- Güvenilirlik Skoru: %{on_sonuc['skor']}
- Manipülasyon: {on_sonuc['manipulasyon']}
- Kaynak Kalitesi: {on_sonuc['kaynak_kalitesi']}
- Ön Yorum: {on_sonuc['on_yorum']}

Şimdi sen bu haberi bağımsız olarak daha derinlemesine analiz et.
Meslektaşının bulgularını göz önünde bulundur ama kendi bağımsız değerlendirmeni yap.
SADECE şu formatta yanıt ver:

SKOR: [0-100 arası tek bir sayı]
GÜVEN_ETİKETİ: [Güvenilir / Şüpheli / Güvenilmez]
MANIPÜLASYON: [Tespit edilen manipülasyon tekniği, yoksa "Tespit edilmedi"]
KAYNAK_KALİTESİ: [Güçlü / Orta / Zayıf / Kaynak yok]
GEREKÇE_1: [Birinci gerekçe, 3-4 cümle]
GEREKÇE_2: [İkinci gerekçe, 3-4 cümle]
GEREKÇE_3: [Üçüncü gerekçe, 3-4 cümle]
ÖZET: [Genel değerlendirme, 4-5 cümle]

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
        "ham": raw,
    }

# ── Ana Fonksiyon: İki Çağrıyı Birleştir ─────────────────────────
def analyze_news_text(text: str, language: str = "tr", max_retries: int = 1) -> dict:
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            # 1. Çağrı
            on_sonuc = on_analiz(text)

            # 2. Çağrı
            derin_sonuc = derin_analiz(text, on_sonuc)

            # İki skoru ortala
            final_skor = round((on_sonuc["skor"] + derin_sonuc["skor"]) / 2)

            return {
                "skor": final_skor,
                "guven_etiketi": derin_sonuc["guven_etiketi"],
                "manipulasyon": derin_sonuc["manipulasyon"],
                "kaynak_kalitesi": derin_sonuc["kaynak_kalitesi"],
                "gerekceler": derin_sonuc["gerekceler"],
                "ozet": derin_sonuc["ozet"],
                "on_analiz": on_sonuc,   # UI'da göstermek için
            }

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue

    raise RuntimeError(f"Groq API hatası: {last_error}")