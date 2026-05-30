"""
VeritasAI — YouTube Video Analiz Modülü

Strateji: yt-dlp veya Whisper yerine youtube-transcript-api kullanıyoruz.
Neden? Streamlit Cloud'da ffmpeg yok, büyük dosya indirmek yavaş.
youtube-transcript-api direkt YouTube'un kendi altyazı sistemine bağlanır —
indirme yok, dönüştürme yok, 1-2 saniyede metin gelir.
"""

import json
import os
import re

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def video_id_cek(url: str) -> str | None:
    """
    YouTube URL'inden video ID'sini çıkarır.
    Desteklenen formatlar:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://youtube.com/shorts/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    """
    # Tüm YouTube URL formatlarını yakalayan regex
    pattern = r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
    eslesme = re.search(pattern, url)
    return eslesme.group(1) if eslesme else None


def transcript_cek(video_id: str) -> dict:
    """
    Verilen video ID için transcript çeker.
    Önce Türkçe dener, sonra İngilizce, sonra otomatik oluşturulmuş.
    
    Dönüş: {"metin": str, "dil": str, "hata": str | None}
    """
    try:
        # Mevcut transcript listesini al
        transcript_listesi = YouTubeTranscriptApi().list(video_id)
        
        transcript = None
        kullanilan_dil = ""

        # 1. Önce manuel Türkçe ara
        try:
            transcript = transcript_listesi.find_manually_created_transcript(["tr"])
            kullanilan_dil = "Türkçe (manuel)"
        except NoTranscriptFound:
            pass

        # 2. Manuel İngilizce dene
        if not transcript:
            try:
                transcript = transcript_listesi.find_manually_created_transcript(["en"])
                kullanilan_dil = "İngilizce (manuel)"
            except NoTranscriptFound:
                pass

        # 3. Otomatik oluşturulmuş Türkçe dene
        if not transcript:
            try:
                transcript = transcript_listesi.find_generated_transcript(["tr"])
                kullanilan_dil = "Türkçe (otomatik)"
            except NoTranscriptFound:
                pass

        # 4. Otomatik oluşturulmuş İngilizce dene
        if not transcript:
            try:
                transcript = transcript_listesi.find_generated_transcript(["en"])
                kullanilan_dil = "İngilizce (otomatik)"
            except NoTranscriptFound:
                pass

        if not transcript:
            return {
                "metin": "",
                "dil": "",
                "hata": "Bu videoda hiçbir dilde transcript bulunamadı."
            }

        # Transcript parçalarını birleştir
        # Her parça {"text": "...", "start": 0.0, "duration": 1.5} formatında
        parcalar = transcript.fetch()
        tam_metin = " ".join(
            parca.text.strip()
            for parca in parcalar
            if parca.text.strip()
     )

        # Groq token limitine karşı 4000 karakterde kes
        # (video analizi haber analizinden biraz daha uzun olabilir)
        return {
            "metin": tam_metin[:4000],
            "dil": kullanilan_dil,
            "hata": None,
            "toplam_karakter": len(tam_metin),
        }

    except TranscriptsDisabled:
        return {
            "metin": "",
            "dil": "",
            "hata": "Bu videoda altyazı devre dışı bırakılmış."
        }
    except VideoUnavailable:
        return {
            "metin": "",
            "dil": "",
            "hata": "Video bulunamadı veya erişime kapalı."
        }
    except Exception as e:
        return {
            "metin": "",
            "dil": "",
            "hata": f"Beklenmeyen hata: {str(e)}"
        }


def video_analiz_et(url: str) -> dict:
    """
    Ana fonksiyon. URL alır, transcript çeker, Groq ile analiz eder.
    
    Neden ayrı bir analiz fonksiyonu?
    Metin haberi analizi ile video analizi farklı — videoda konuşma dili,
    tekrar eden ifadeler, duygusal vurgu daha belirgin olabilir.
    Bu yüzden Groq'a özel bir prompt gönderiyoruz.
    """
    # 1. Video ID çıkar
    video_id = video_id_cek(url)
    if not video_id:
        return {
            "hata": "Geçerli bir YouTube linki değil. youtube.com veya youtu.be formatında olmalı.",
            "karar": "Hata",
        }

    # 2. Transcript çek
    transcript_sonuc = transcript_cek(video_id)
    if transcript_sonuc["hata"]:
        return {
            "hata": transcript_sonuc["hata"],
            "karar": "Transcript Bulunamadı",
            "video_id": video_id,
        }

    metin = transcript_sonuc["metin"]
    dil = transcript_sonuc["dil"]

    # 3. Groq ile analiz
    prompt = f"""Sen bir dezenformasyon analisti ve medya okuryazarlığı uzmanısın.
Sana bir YouTube videosunun transcript metni verildi.
Bu metni dezenformasyon, manipülasyon ve güvenilirlik açısından analiz et.

Transcript Dili: {dil}
Toplam Karakter: {transcript_sonuc.get('toplam_karakter', len(metin))}

Transcript Metni:
{metin}

Video içeriğini şu açılardan değerlendir:
- Duygusal dil ve manipülasyon teknikleri (korku, öfke, abartı)
- İddia edilen olguların doğrulanabilirliği
- Kaynak gösterimi — herhangi bir kaynak var mı?
- Tek taraflı anlatı veya propaganda unsurları
- Dezenformasyon kalıpları (yanlış bağlam, eksik bilgi, çarpıtma)

Yanıtını SADECE şu JSON formatında ver:
{{
  "karar": "Güvenilir" | "Şüpheli" | "Manipülatif" | "Dezenformasyon",
  "guven_skoru": 0-100,
  "manipulasyon_teknigi": "tespit edilen teknik veya Tespit edilmedi",
  "ana_bulgu": "tek cümle en önemli bulgu",
  "gerekceler": ["gerekçe 1", "gerekçe 2", "gerekçe 3"],
  "ozet": "2-3 cümle genel değerlendirme"
}}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        sonuc = json.loads(raw)

        # Transcript bilgisini de ekle — UI'da göstermek için
        sonuc["transcript_ozet"] = metin[:300] + "..." if len(metin) > 300 else metin
        sonuc["dil"] = dil
        sonuc["video_id"] = video_id
        return sonuc

    except json.JSONDecodeError:
        return {
            "karar": "Hata",
            "hata": "Groq yanıtı JSON formatında gelmedi.",
            "video_id": video_id,
        }
    except Exception as e:
        return {
            "karar": "Hata",
            "hata": f"API hatası: {str(e)}",
            "video_id": video_id,
        }