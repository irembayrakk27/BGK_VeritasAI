import os
import re
from groq import Groq
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY bulunamadı. .env dosyasını kontrol et.")

client = Groq(api_key=API_KEY)

def analyze_news_text(text: str, language: str = "tr", max_retries: int = 1) -> dict:
    prompt = (
        "Aşağıdaki haber metnini analiz et ve SADECE şu formatta yanıt ver:\n\n"
        "SKOR: [0-100 arası sayı]\n"
        "GEREKÇE_1: [birinci gerekçe]\n"
        "GEREKÇE_2: [ikinci gerekçe]\n"
        "GEREKÇE_3: [üçüncü gerekçe]\n"
        "ÖZET: [2-3 cümlelik genel değerlendirme]\n\n"
        f"Metin: {text}"
    )
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            raw = response.choices[0].message.content

            # Skoru parse et
            skor_match = re.search(r"SKOR:\s*(\d+)", raw)
            skor = int(skor_match.group(1)) if skor_match else 50

            gerekceler = []
            for i in range(1, 4):
                m = re.search(rf"GEREKÇE_{i}:\s*(.+)", raw)
                if m:
                    gerekceler.append(m.group(1).strip())

            ozet_match = re.search(r"ÖZET:\s*(.+)", raw, re.DOTALL)
            ozet = ozet_match.group(1).strip() if ozet_match else raw

            return {
                "skor": skor,
                "gerekceler": gerekceler,
                "ozet": ozet,
                "ham": raw,
            }
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue
    raise RuntimeError(f"Groq API hatası: {last_error}")