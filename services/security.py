"""
VeritasAI — AI Güvenlik & Açıklanabilirlik Modülü
==================================================

KATMAN 1 — PROMPT INJECTION & ADVERSARIAL INPUT TESPİTİ
  Regex tabanlı, compile edilmiş kalıplar (performanslı).
  Her çağrıda yeniden derlenmez — modül yüklenince bir kez derlenir.

KATMAN 2 — GÜVEN SKORU AÇIKLANABİLİRLİĞİ
  analyze_news_text'in gerçek dönüş yapısına göre yazıldı:
  skor, guven_etiketi, manipulasyon, kaynak_kalitesi, gerekceler, ozet
  
  4 bileşen × ağırlık = açıklanabilir toplam skor
  LIME/SHAP'ın kural tabanlı yazılım versiyonu.
"""

import re

# ═══════════════════════════════════════════════════════════════════
# KATMAN 1 — GÜVENLİK TESPİTİ
# ═══════════════════════════════════════════════════════════════════

# Compile time'da bir kez derlenir — her çağrıda yeniden derlenmez
_INJECTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"ignore\s+(previous|all|prior)\s+instructions?",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+(a|an)\s+\w+",
    r"act\s+as\s+(a|an|if)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"roleplay\s+as",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"görevini\s+unut",
    r"önceki\s+talimatları?\s+unut",
    r"artık\s+sen\s+bir",
    r"sistem\s+talimatlarını?\s+yoksay",
    r"talimatlarını?\s+geçersiz\s+kıl",
    r"show\s+(me\s+)?(your\s+)?(system\s+prompt|instructions?)",
    r"repeat\s+(your\s+)?(system|initial)\s+(prompt|instructions?)",
    r"sistem\s+promptunu?\s+(göster|paylaş|yaz)",
    r"always\s+(say|respond|answer|output)",
    r"never\s+(say|respond|refuse)",
    r"must\s+(say|output|respond)\s+(that|this)",
    r"say\s+that\s+(this|the)\s+(news\s+is|article\s+is)",
    r"bu\s+haberin?\s+(güvenilir|doğru|yanlış)\s+olduğunu\s+söyle",
    r"<script",
    r"javascript:",
    r"__import__",
]]

_ADVERSARIAL_PATTERNS = [re.compile(p, re.UNICODE) for p in [
    r"(.)\1{50,}",           # Aynı karakter 50+ kez tekrar
    r"(\w+\s+)\1{20,}",      # Aynı kelime 20+ kez tekrar
    r"[\u202e\u200f\u200e]", # Sağdan sola yönlendirme karakterleri
    r"[A-Za-z0-9+/]{150,}={0,2}",  # Uzun base64 payload
]]

_SEVIYE = {
    "injection":   {"seviye": "YÜKSEK",  "renk": "#f87171", "ikon": "🔴"},
    "adversarial": {"seviye": "ORTA",    "renk": "#facc15", "ikon": "🟡"},
    "anomali":     {"seviye": "DÜŞÜK",   "renk": "#60a5fa", "ikon": "🔵"},
    "temiz":       {"seviye": "TEMİZ",   "renk": "#4ade80", "ikon": "🟢"},
}


def guvenlik_tara(metin: str) -> dict:
    """
    Kullanıcı girdisini güvenlik açısından tarar.
    Prompt injection, adversarial input ve anomali tespiti yapar.
    """
    bulgular    = []
    tehdit_tipi = "temiz"

    # 1. Prompt Injection taraması
    for pattern in _INJECTION_PATTERNS:
        m = pattern.search(metin)
        if m:
            bulgular.append({
                "tip":     "Prompt Injection",
                "bulunan": m.group(0)[:60],
                "ikon":    "🔴",
            })
            tehdit_tipi = "injection"

    # 2. Adversarial input taraması
    for pattern in _ADVERSARIAL_PATTERNS:
        m = pattern.search(metin)
        if m:
            bulgular.append({
                "tip":     "Adversarial Input",
                "bulunan": str(m.group(0))[:40],
                "ikon":    "🟡",
            })
            if tehdit_tipi == "temiz":
                tehdit_tipi = "adversarial"

    # 3. Anomali kontrolleri
    anomaliler = []

    if len(metin) > 8000:
        anomaliler.append(f"Aşırı uzun girdi: {len(metin)} karakter (limit: 8000)")
        if tehdit_tipi == "temiz":
            tehdit_tipi = "anomali"

    url_sayisi = len(re.findall(r"https?://", metin))
    if url_sayisi > 5:
        anomaliler.append(f"Çok sayıda URL: {url_sayisi} adet")
        if tehdit_tipi == "temiz":
            tehdit_tipi = "anomali"

    if len(metin) > 100:
        harf_orani = sum(c.isalpha() for c in metin) / len(metin)
        if harf_orani < 0.30:
            anomaliler.append(f"Düşük harf oranı: %{harf_orani*100:.0f} — sembol yoğun girdi")
            if tehdit_tipi == "temiz":
                tehdit_tipi = "anomali"

    bilgi = _SEVIYE[tehdit_tipi]

    return {
        "tehdit_tipi":        tehdit_tipi,
        "seviye":             bilgi["seviye"],
        "renk":               bilgi["renk"],
        "ikon":               bilgi["ikon"],
        "injection_sayisi":   sum(1 for b in bulgular if b["tip"] == "Prompt Injection"),
        "adversarial_sayisi": sum(1 for b in bulgular if b["tip"] == "Adversarial Input"),
        "anomaliler":         anomaliler,
        "bulgular":           bulgular[:5],
        "guvenli_mi":         tehdit_tipi == "temiz",
        "karakter_sayisi":    len(metin),
        "token_tahmini":      len(metin.split()),
        "oneri": (
            "Girdi güvenli görünüyor."
            if tehdit_tipi == "temiz"
            else "Şüpheli kalıplar tespit edildi. Analiz sonuçlarını dikkatli değerlendirin."
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# KATMAN 2 — AÇIKLANABİLİRLİK: SKOR BİLEŞENLERİ
# ═══════════════════════════════════════════════════════════════════

_DUYGUSAL_KELIMELER = {
    "şok", "inanılmaz", "skandal", "rezalet", "dehşet",
    "korkunç", "utanç", "ihanet", "yalan", "sahte",
    "shocking", "outrageous", "scandal", "disgrace", "bombshell",
}

_GUVENILIR_KAYNAKLAR = {
    "reuters", "bbc", "apnews", "theguardian", "aa.com.tr",
    "ntv", "bloomberg", "ft.com", "economist", "hurriyet",
}


def skor_acikla(
    metin: str,
    analiz_raporu: dict,
    rag_sonuc: dict | None = None,
) -> dict:
    """
    Güven skorunu 4 bileşene ayırarak açıklar.
    
    analiz_raporu, analyze_news_text'in döndürdüğü dict:
      - skor           : int (0-100)
      - guven_etiketi  : str
      - manipulasyon   : str
      - kaynak_kalitesi: str
      - gerekceler     : list[str]
      - ozet           : str

    Ağırlıklar:
      Dil Analizi      30%  — manipülatif dil, duygusal yükleme
      Kaynak Kalitesi  25%  — RAG kaynak sayısı ve güvenilirliği
      RAG Uzlaşması    25%  — kaynakların doğrulama oranı
      Tutarlılık       20%  — iç tutarlılık, kaynak atıfı
    """

    # ── Bileşen 1: Dil Analizi (%30) ────────────────────────────
    dil_skoru  = 85
    dil_notlar = []

    manipulasyon = analiz_raporu.get("manipulasyon", "") or ""
    if manipulasyon and manipulasyon.lower() not in {"tespit edilmedi", "yok", "none", ""}:
        dil_skoru -= 25
        dil_notlar.append(f"🔴 Manipülasyon: {manipulasyon}")
    else:
        dil_notlar.append("🟢 Manipülatif dil kalıbı tespit edilmedi")

    metin_kucuk = metin.lower()
    bulunan_duygusal = [k for k in _DUYGUSAL_KELIMELER if k in metin_kucuk]
    if len(bulunan_duygusal) >= 3:
        dil_skoru -= 20
        dil_notlar.append(f"🔴 Yüksek duygusal yükleme: {', '.join(bulunan_duygusal[:3])}")
    elif len(bulunan_duygusal) >= 1:
        dil_skoru -= 10
        dil_notlar.append(f"🟡 Duygusal yükleme: {', '.join(bulunan_duygusal)}")
    else:
        dil_notlar.append("🟢 Dengeli dil kullanımı")

    # Gerçek analizden gelen skoru da dahil et
    analiz_skoru = analiz_raporu.get("skor", 70)
    dil_skoru = round((dil_skoru + analiz_skoru) / 2)
    dil_skoru = max(0, min(100, dil_skoru))

    # ── Bileşen 2: Kaynak Kalitesi (%25) ────────────────────────
    kaynak_skoru  = 50
    kaynak_notlar = []

    kaynak_kalitesi = analiz_raporu.get("kaynak_kalitesi", "") or ""

    if rag_sonuc and not rag_sonuc.get("hata"):
        taranan = rag_sonuc.get("bulunan_kaynak_sayisi", 0)
        indeks  = rag_sonuc.get("indekslenen_haber", 0)

        if taranan >= 4:
            kaynak_skoru = 90
            kaynak_notlar.append(f"🟢 {taranan} bağımsız kaynak tarandı")
        elif taranan >= 2:
            kaynak_skoru = 65
            kaynak_notlar.append(f"🟡 {taranan} kaynak tarandı")
        else:
            kaynak_skoru = 35
            kaynak_notlar.append(f"🔴 Yalnızca {taranan} kaynak bulundu")

        kaynak_listesi = [
            k.lower() for k in rag_sonuc.get("indekslenen_kaynaklar", [])
        ]
        guvenilir_sayisi = sum(
            1 for k in kaynak_listesi
            if any(g in k for g in _GUVENILIR_KAYNAKLAR)
        )
        if guvenilir_sayisi:
            kaynak_skoru = min(100, kaynak_skoru + 10)
            kaynak_notlar.append(f"🟢 {guvenilir_sayisi} ana akım kaynak")

        kaynak_notlar.append(f"🔵 {indeks} haber indekslendi")
    else:
        kaynak_notlar.append("🔵 Çapraz kaynak doğrulama henüz yapılmadı")

    if "güçlü" in kaynak_kalitesi.lower():
        kaynak_skoru = min(100, kaynak_skoru + 10)
        kaynak_notlar.append("🟢 Kaynak kalitesi: Güçlü")
    elif "zayıf" in kaynak_kalitesi.lower():
        kaynak_skoru = max(0, kaynak_skoru - 15)
        kaynak_notlar.append("🔴 Kaynak kalitesi: Zayıf")

    kaynak_skoru = max(0, min(100, kaynak_skoru))

    # ── Bileşen 3: RAG Uzlaşması (%25) ──────────────────────────
    rag_skoru  = 50
    rag_notlar = []

    if rag_sonuc and not rag_sonuc.get("hata"):
        uzlasma = rag_sonuc.get("kaynak_uzlasmasi", 50)
        karar   = rag_sonuc.get("karar", "")
        rag_skoru = uzlasma

        emoji = "🟢" if uzlasma >= 70 else "🟡" if uzlasma >= 40 else "🔴"
        rag_notlar.append(f"{emoji} Kaynak uzlaşması: %{uzlasma}")

        karar_map = {
            "Doğrulandı":         (0,   "🟢 Kaynaklar doğruluyor"),
            "Kısmen Doğrulandı":  (0,   "🟡 Kaynaklar kısmen doğruluyor"),
            "Çelişkili":          (-15, "🟡 Kaynaklar arasında çelişki"),
            "Çürütüldü":          (-30, "🔴 Kaynaklar çürütüyor"),
        }
        if karar in karar_map:
            delta, mesaj = karar_map[karar]
            rag_skoru = max(0, rag_skoru + delta)
            rag_notlar.append(mesaj)

        eksik = rag_sonuc.get("eksik_bilgiler", [])
        if eksik:
            rag_skoru = max(0, rag_skoru - len(eksik) * 5)
            rag_notlar.append(f"🟡 {len(eksik)} doğrulanamayan iddia")
    else:
        rag_notlar.append("🔵 RAG analizi yapılmadı")

    rag_skoru = max(0, min(100, rag_skoru))

    # ── Bileşen 4: Tutarlılık (%20) ──────────────────────────────
    tutarlilik_skoru  = 75
    tutarlilik_notlar = []

    cumle_sayisi = len([c for c in re.split(r"[.!?]+", metin) if c.strip()])
    if cumle_sayisi >= 5:
        tutarlilik_notlar.append(f"🟢 {cumle_sayisi} cümle — yeterli içerik")
    elif cumle_sayisi >= 2:
        tutarlilik_notlar.append(f"🟡 {cumle_sayisi} cümle — kısa metin")
        tutarlilik_skoru -= 10
    else:
        tutarlilik_notlar.append("🔴 Çok kısa — analiz için yetersiz")
        tutarlilik_skoru -= 25

    kaynak_atif = re.findall(
        r"\b(göre|according|kaynak[a-z]*|söyledi|açıkladı|belirtti|reported|said)\b",
        metin, re.IGNORECASE
    )
    if len(kaynak_atif) >= 3:
        tutarlilik_skoru = min(100, tutarlilik_skoru + 10)
        tutarlilik_notlar.append(f"🟢 {len(kaynak_atif)} kaynak atıfı")
    elif len(kaynak_atif) >= 1:
        tutarlilik_notlar.append(f"🟡 {len(kaynak_atif)} kaynak atıfı")
    else:
        tutarlilik_skoru -= 10
        tutarlilik_notlar.append("🔴 Kaynak atıfı yok")

    # Gerekceler varsa tutarlılık sinyali
    gerekceler = analiz_raporu.get("gerekceler", [])
    if len(gerekceler) >= 3:
        tutarlilik_skoru = min(100, tutarlilik_skoru + 5)
        tutarlilik_notlar.append("🟢 Detaylı gerekçe mevcut")

    tutarlilik_skoru = max(0, min(100, tutarlilik_skoru))

    # ── Ağırlıklı Toplam ────────────────────────────────────────
    toplam = round(
        dil_skoru        * 0.30 +
        kaynak_skoru     * 0.25 +
        rag_skoru        * 0.25 +
        tutarlilik_skoru * 0.20
    )

    def _renk(s):
        return "#4ade80" if s >= 70 else "#facc15" if s >= 40 else "#f87171"

    return {
        "aciklanabilir_skor": toplam,
        "bilesenler": [
            {
                "ad": "Dil Analizi",       "ikon": "🗣️",
                "agirlik": "30%",          "skor": dil_skoru,
                "renk": _renk(dil_skoru),  "notlar": dil_notlar,
            },
            {
                "ad": "Kaynak Kalitesi",        "ikon": "📰",
                "agirlik": "25%",               "skor": kaynak_skoru,
                "renk": _renk(kaynak_skoru),    "notlar": kaynak_notlar,
            },
            {
                "ad": "RAG Uzlaşması",      "ikon": "🔗",
                "agirlik": "25%",           "skor": rag_skoru,
                "renk": _renk(rag_skoru),   "notlar": rag_notlar,
            },
            {
                "ad": "Tutarlılık",               "ikon": "🔍",
                "agirlik": "20%",                 "skor": tutarlilik_skoru,
                "renk": _renk(tutarlilik_skoru),  "notlar": tutarlilik_notlar,
            },
        ],
    }