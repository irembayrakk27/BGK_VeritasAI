"""
VeritasAI — Görsel AI/Manipülasyon Tespit Modülü
EXIF metadata analizi + piksel istatistikleri + Groq yorumu.
"""

import io
import json
import os
import statistics

from PIL import Image, ImageFilter
from PIL.ExifTags import TAGS
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def _exif_cek(img: Image.Image) -> dict:
    """
    Görselin EXIF metadata'sını çeker.
    Gerçek fotoğraflarda kamera bilgisi, tarih, lens vb. bulunur.
    AI üretimi görsellerde bunlar genelde boştur.
    """
    exif_bilgi = {}
    try:
        raw_exif = img._getexif()
        if raw_exif:
            for tag_id, deger in raw_exif.items():
                tag_adi = TAGS.get(tag_id, tag_id)
                # Sadece metin/sayı olarak okunabilenleri al
                if isinstance(deger, (str, int, float, tuple)):
                    exif_bilgi[str(tag_adi)] = str(deger)[:100]
    except Exception:
        pass  # EXIF okuma desteklenmiyor (PNG gibi)
    return exif_bilgi


def _exif_skoru(exif: dict) -> dict:
    """
    EXIF içeriğine bakarak AI olasılık skoru üretir.
    Ne kadar çok kamera bilgisi varsa o kadar gerçek fotoğraf.
    """
    gercek_sinyaller = []
    ai_sinyaller = []

    # Gerçek fotoğraf sinyalleri
    if exif.get("Make"):
        gercek_sinyaller.append(f"Kamera markası mevcut: {exif['Make']}")
    if exif.get("Model"):
        gercek_sinyaller.append(f"Kamera modeli mevcut: {exif['Model']}")
    if exif.get("DateTime") or exif.get("DateTimeOriginal"):
        tarih = exif.get("DateTimeOriginal") or exif.get("DateTime")
        gercek_sinyaller.append(f"Çekim tarihi mevcut: {tarih}")
    if exif.get("LensModel") or exif.get("LensInfo"):
        gercek_sinyaller.append("Lens bilgisi mevcut")
    if exif.get("GPSInfo"):
        gercek_sinyaller.append("GPS konum verisi mevcut")
    if exif.get("ExposureTime"):
        gercek_sinyaller.append(f"Pozlama süresi: {exif['ExposureTime']}")
    if exif.get("ISOSpeedRatings"):
        gercek_sinyaller.append(f"ISO değeri: {exif['ISOSpeedRatings']}")

    # AI üretimi sinyalleri
    if not exif:
        ai_sinyaller.append("EXIF verisi tamamen yok — AI veya web'den alınmış olabilir")
    if exif.get("Software") and any(
        k in str(exif.get("Software", "")).lower()
        for k in ["photoshop", "gimp", "midjourney", "stable", "dall", "adobe"]
    ):
        ai_sinyaller.append(f"Düzenleme yazılımı tespit edildi: {exif['Software']}")
    if not exif.get("Make") and not exif.get("Model"):
        ai_sinyaller.append("Kamera bilgisi yok")

    # Skor hesapla (0-100, yüksek = gerçek fotoğraf)
    max_puan = 7
    puan = len(gercek_sinyaller)
    gerceklik_yuzdesi = min(100, int((puan / max_puan) * 100))

    return {
        "gercek_sinyaller": gercek_sinyaller,
        "ai_sinyaller": ai_sinyaller,
        "gerceklik_yuzdesi": gerceklik_yuzdesi,
        "exif_dolu_mu": len(exif) > 0,
    }


def _piksel_ozellikleri(img: Image.Image) -> dict:
    """
    Piksel seviyesinde istatistiksel analiz.
    AI görsellerde gürültü düşük, renk dengesi aşırı mükemmel olur.
    """
    rgb = img.convert("RGB")
    genislik, yukseklik = rgb.size
    piksel_sayisi = genislik * yukseklik
    ornekleme = max(1, piksel_sayisi // 10000)

    piksel_listesi = list(rgb.getdata())
    ornekler = piksel_listesi[::ornekleme]

    r_vals = [p[0] for p in ornekler]
    g_vals = [p[1] for p in ornekler]
    b_vals = [p[2] for p in ornekler]

    r_ort = sum(r_vals) / len(r_vals)
    g_ort = sum(g_vals) / len(g_vals)
    b_ort = sum(b_vals) / len(b_vals)
    r_std = statistics.stdev(r_vals) if len(r_vals) > 1 else 0
    g_std = statistics.stdev(g_vals) if len(g_vals) > 1 else 0
    b_std = statistics.stdev(b_vals) if len(b_vals) > 1 else 0

    renk_dengesi = abs(r_ort - g_ort) + abs(g_ort - b_ort) + abs(r_ort - b_ort)

    gri = img.convert("L")
    kenarlar = gri.filter(ImageFilter.FIND_EDGES)
    kenar_piksel = list(kenarlar.getdata())
    kenar_yogunlugu = sum(kenar_piksel) / len(kenar_piksel)

    gurultu = gri.filter(ImageFilter.SMOOTH_MORE)
    orijinal_piksel = list(gri.getdata())
    yumusak_piksel = list(gurultu.getdata())
    gurultu_fark = statistics.mean(
        abs(int(a) - int(b))
        for a, b in zip(
            orijinal_piksel[::ornekleme],
            yumusak_piksel[::ornekleme]
        )
    )

    return {
        "genislik": genislik,
        "yukseklik": yukseklik,
        "format": img.format or "Bilinmiyor",
        "r_std": round(r_std, 1),
        "g_std": round(g_std, 1),
        "b_std": round(b_std, 1),
        "renk_dengesi": round(renk_dengesi, 1),
        "kenar_yogunlugu": round(kenar_yogunlugu, 1),
        "gurultu_seviyesi": round(gurultu_fark, 2),
    }


def gorsel_analiz_et(gorsel_bytes: bytes, dosya_adi: str = "") -> dict:
    """
    Ana fonksiyon: EXIF + piksel analizi → Groq yorumu → sonuç.
    """
    try:
        img = Image.open(io.BytesIO(gorsel_bytes))

        # İki katman analiz
        exif_ham = _exif_cek(img)
        exif_sonuc = _exif_skoru(exif_ham)
        piksel = _piksel_ozellikleri(img)

        # Groq'a gönderilecek özet
        teknik_ozet = f"""
EXIF Metadata Analizi:
- EXIF verisi mevcut mu: {exif_sonuc['exif_dolu_mu']}
- Gerçeklik sinyalleri: {', '.join(exif_sonuc['gercek_sinyaller']) or 'Hiçbiri'}
- AI/Düzenleme sinyalleri: {', '.join(exif_sonuc['ai_sinyaller']) or 'Hiçbiri'}
- EXIF bazlı gerçeklik skoru: %{exif_sonuc['gerceklik_yuzdesi']}

Piksel İstatistikleri:
- Boyut: {piksel['genislik']}x{piksel['yukseklik']} | Format: {piksel['format']}
- RGB Standart Sapmaları: R={piksel['r_std']} G={piksel['g_std']} B={piksel['b_std']}
- Renk kanalları dengesi: {piksel['renk_dengesi']} (düşük = yapay dengeli)
- Kenar yoğunluğu: {piksel['kenar_yogunlugu']} (yüksek = aşırı keskin)
- Gürültü seviyesi: {piksel['gurultu_seviyesi']} (çok düşük = AI sinyali)
- Dosya adı: {dosya_adi or 'belirtilmedi'}
"""

        prompt = f"""Sen bir dijital adli görsel analiz uzmanısın.
Sana bir görselin hem EXIF metadata hem de piksel istatistikleri verildi.
Bu verilere dayanarak görselin AI üretimi mi, manipüle mi, yoksa gerçek fotoğraf mı 
olduğunu belirle.

{teknik_ozet}

Önemli kurallar:
- EXIF boşsa ve kamera bilgisi yoksa bu güçlü bir AI/web görseli sinyalidir
- Gürültü seviyesi < 1.0 ise AI üretimi kuvvetle muhtemeldir
- Photoshop/GIMP yazılımı tespit edildiyse manipülasyon düşünülmeli
- Gerçek basın fotoğraflarında genelde kamera markası ve tarih bulunur

Yanıtını SADECE şu JSON formatında ver:
{{
  "karar": "Gerçek Fotoğraf" | "Muhtemelen AI Üretimi" | "Manipüle Edilmiş" | "Şüpheli",
  "guven_yuzdesi": 0-100,
  "ana_sinyal": "tek cümle en güçlü gerekçe",
  "detaylar": ["gerekçe 1", "gerekçe 2", "gerekçe 3"],
  "risk_seviyesi": "Düşük" | "Orta" | "Yüksek"
}}"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        sonuc = json.loads(raw)
        sonuc["exif_sonuc"] = exif_sonuc
        sonuc["piksel"] = piksel
        return sonuc

    except Exception as e:
        return {
            "karar": "Analiz Hatası",
            "guven_yuzdesi": 0,
            "ana_sinyal": str(e),
            "detaylar": ["Görsel okunamadı veya API hatası"],
            "risk_seviyesi": "Bilinmiyor",
            "exif_sonuc": {},
            "piksel": {},
        }