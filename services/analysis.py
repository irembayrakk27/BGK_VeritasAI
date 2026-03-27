import os
import re
from groq import Groq
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY bulunamadı. .env dosyasını kontrol et.")

client = Groq(api_key=API_KEY)

# ── Sistem Mesajı (AI Personası) ─────────────────────────────────
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

# ── Prompt Şablonu ────────────────────────────────────────────────
def prompt_olustur(text: str) -> str:
    return f"""Aşağıdaki haber metnini analiz et ve SADECE şu formatta yanıt ver:

SKOR: [0-100 arası tek bir sayı]
GÜVEN_ETİKETİ: [Güvenilir / Şüpheli / Güvenilmez]
MANIPÜLASYON: [Tespit edilen manipülasyon tekniği, yoksa "Tespit edilmedi"]
KAYNAK_KALİTESİ: [Güçlü / Orta / Zayıf / Kaynak yok]
GEREKÇE_1: [Birinci gerekçe, 1-2 cümle]
GEREKÇE_2: [İkinci gerekçe, 1-2 cümle]
GEREKÇE_3: [Üçüncü gerekçe, 1-2 cümle]
ÖZET: [Genel değerlendirme, 2-3 cümle]

Analiz edilecek metin:
{text}"""


def analyze_news_text(text: str, language: str = "tr", max_retries: int = 1) -> dict:
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SISTEM_MESAJI},
                    {"role": "user", "content": prompt_olustur(text)},
                ],
                max_tokens=1024,
                temperature=0.2,  # Düşük = daha tutarlı, az yaratıcı
            )
            raw = response.choices[0].message.content

            # ── Parse et ─────────────────────────────────────────
            def parse(pattern):
                m = re.search(pattern, raw, re.IGNORECASE)
                return m.group(1).strip() if m else ""

            skor_str = parse(r"SKOR:\s*(\d+)")
            skor = max(0, min(100, int(skor_str))) if skor_str else 50

            gerekceler = []
            for i in range(1, 4):
                g = parse(rf"GEREKÇE_{i}:\s*(.+)")
                if g:
                    gerekceler.append(g)

            return {
                "skor": skor,
                "guven_etiketi": parse(r"GÜVEN_ETİKETİ:\s*(.+)"),
                "manipulasyon": parse(r"MANIPÜLASYON:\s*(.+)"),
                "kaynak_kalitesi": parse(r"KAYNAK_KALİTESİ:\s*(.+)"),
                "gerekceler": gerekceler,
                "ozet": parse(r"ÖZET:\s*(.+)"),
                "ham": raw,
            }

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue

    raise RuntimeError(f"Groq API hatası: {last_error}")