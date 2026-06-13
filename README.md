# 🛡️ VeritasAI – Multi-Modal AI Disinformation Detection Platform

<div align="center">

[![Live Demo](https://img.shields.io/badge/🚀_Canlı_Demo-veritasai--bgk.streamlit.app-FF4B4B?style=for-the-badge&logo=streamlit)](https://veritasai-bgk.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-RAG_v2-1C3C3C?style=for-the-badge&logo=chainlink)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange?style=for-the-badge)](https://trychroma.com)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-f55036?style=for-the-badge)](https://groq.com)
[![OWASP](https://img.shields.io/badge/OWASP_LLM-Top_10_Protected-red?style=for-the-badge)](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

**Türkçe haber içeriklerini metin, görsel ve video boyutlarında analiz eden,**
**RAG v2 + Hibrit Retrieval + Explainable AI + OWASP LLM güvenlik katmanlı dezenformasyon tespit platformu.**

</div>

---

## 📌 Neden VeritasAI?

Çoğu haber doğrulama aracı ya sadece LLM tahminlerine dayanır (hallucination riski yüksek) ya da kural tabanlı çalışır (bağlamı anlamaz). VeritasAI üç katmanı birden kullanır:

| Yaklaşım | Geleneksel Araçlar | VeritasAI |
|---|---|---|
| Analiz kaynağı | LLM eğitim verisi | Hibrit RAG (ChromaDB + Canlı Tavily) |
| Görsel analiz | ❌ | ✅ EXIF + piksel + Groq Vision |
| Video analiz | ❌ | ✅ YouTube transcript |
| Güvenlik katmanı | ❌ | ✅ OWASP LLM Top 10 |
| Açıklanabilirlik | ❌ | ✅ 4 bileşenli XAI skoru |
| Retrieval stratejisi | Tek sorgu | Multi-Query + HyDE + RRF |

---

## ⚙️ Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────┐
│                     KULLANICI GİRDİSİ                           │
│          Metin / URL / Görsel (.jpg .png) / YouTube             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  🛡️  ETAP 1 – AI GÜVENLİK KATMANI  (security.py)               │
│                                                                 │
│  Pre-compiled Regex  → Prompt Injection Tarama (24 kalıp)       │
│  Adversarial Input   → Token Flooding / Unicode Saldırısı       │
│  Anomali Dedektörü   → Karakter dağılımı / URL yoğunluğu        │
│                                                                 │
│         TEMİZ ──────────────────────────────────────►           │
│         ŞÜPHELİ → [ BLOKE + GÜVENLİK RAPORU ]                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  🔍  ETAP 2 – RAG PIPELINE v2  (rag_pipeline.py)                │
│                                                                 │
│  [Routing]       konu_tespit_et() → siyaset/ekonomi/sağlık...   │
│                                                                 │
│  [Indexing]      Tavily API (canlı haber, son 30 gün)           │
│                  → RecursiveCharacterTextSplitter               │
│                    chunk_size=500, overlap=50                   │
│                  → HuggingFace Embeddings (all-MiniLM-L6-v2)    │
│                  → ChromaDB persist (kalıcı veri birikimi)       │
│                                                                 │
│  [Query          multi_query_uret() → 3 semantik sorgu          │
│   Translation]   hyde_sorgu_uret()  → varsayımsal belge         │
│                                                                 │
│  [Hibrit         1. ChromaDB'de ara (cosine similarity ≥ 0.30)  │
│   Retrieval]     2. Skor yetersizse → Tavily canlı web ekle     │
│                  3. Reciprocal Rank Fusion: Σ 1/(60 + rank)     │
│                  → En alakalı 5 belge                           │
│                                                                 │
│  [Generation]    Groq Llama-3.3-70b + Hallucination Guard       │
│                  → JSON yapılandırılmış doğrulama raporu        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  📊  ETAP 3 – XAI SKORU  (security.py)                          │
│                                                                 │
│  Güven Skoru = 0.30 × Dil_Analizi                               │
│              + 0.25 × Kaynak_Kalitesi                           │
│              + 0.25 × RAG_Uzlaşması                             │
│              + 0.20 × Tutarlılık                                │
│                                                                 │
│  Çıktı: Karar | Güven Skoru | Kaynak Linkleri | Bileşen Raporu  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Özellikler

### 🔗 Çoklu Girdi Desteği
- **Metin**: Doğrudan haber metni yapıştırma
- **URL**: `requests + BeautifulSoup` ile otomatik scraping
- **Görsel**: EXIF metadata analizi + piksel istatistikleri → Groq Vision yorumu → AI/gerçek fotoğraf kararı
- **YouTube**: `youtube-transcript-api` ile altyazı çekimi → dezenformasyon analizi

### 🔍 Hibrit RAG v2 Pipeline
- **Multi-Query Retrieval**: Tek sorguda kaçırılan semantik varyantları 3 farklı açıdan aratır
- **HyDE**: Varsayımsal yanıt oluşturup vektörleştirir, cosine similarity'yi artırır
- **Hibrit Retrieval**: ChromaDB (kalıcı veri) → skor yetersizse Tavily canlı web devreye girer
- **Reciprocal Rank Fusion**: Birden fazla sorgu listesini `1/(k+rank)` formülüyle birleştirir
- **Hallucination Guard**: Prompt'ta açıkça "yalnızca verilen kaynaklara dayan" kısıtı

### 🛡️ AI Güvenlik Katmanı (OWASP LLM Top 10)
- **LLM01 – Prompt Injection**: 24 adet pre-compiled regex kalıbı, O(1) tarama
- **LLM02 – Adversarial Input**: Karakter tekrarı, Unicode yönlendirme, base64 payload tespiti
- **Anomali tespiti**: Token flooding (>8000 karakter), URL yoğunluğu, harf oranı analizi

### 📊 Explainable AI (XAI)
LIME/SHAP'ın kural tabanlı deterministik versiyonu — her skor bileşeni ayrı kartlarda gösterilir:

```
Güven Skoru = 0.30 × Dil_Analizi
            + 0.25 × Kaynak_Kalitesi
            + 0.25 × RAG_Uzlaşması
            + 0.20 × Tutarlılık
```

---

## 📂 Proje Yapısı
'''
BGK_VeritasAI/
│
├── app.py                    # Streamlit ana kontrolör, multi-page routing
│
├── services/
│   ├── analysis.py           # Groq tabanlı ön_analiz + derin_analiz pipeline
│   ├── rag_pipeline.py       # RAG v2: Hibrit Retrieval, Multi-Query, HyDE, RRF
│   ├── security.py           # OWASP LLM: Prompt injection + adversarial + XAI
│   ├── image_analysis.py     # EXIF metadata + piksel anomali + Groq vision
│   └── video_analysis.py     # youtube-transcript-api + dezenformasyon analizi
│
├── pages/
│   ├── 2_Otomasyon.py        # n8n webhook entegrasyonu
│   └── 3_Topluluk_Teyidi.py  # Kanıt tabanlı topluluk doğrulama
│
├── RAG/
│   ├── chunk_module.py       # RecursiveCharacterTextSplitter 
wrapper
│   ├── embedding_module.py   # HuggingFace embeddings + cosine 
similarity
│   ├── vectorStore_module.py # ChromaDB oluşturma, yükleme, hibrit 
sorgulama
│   └── rag_overview.py       # LangChain RAG chain builder
│
├── data/
│   ├── gecmis.json           # Analiz geçmişi (local persistence)
│   └── chroma_db/            # ChromaDB vektör veritabanı (otomatik 
oluşur)
├── requirements.txt
└── .env.example
'''
---

## 📖 Modül Referansı

### `services/security.py`

```python
guvenlik_tara(metin: str) -> dict
# Prompt injection + adversarial + anomali taraması
# Returns: {tehdit_tipi, seviye, renk, ikon, bulgular, guvenli_mi, ...}

skor_acikla(metin: str, analiz_raporu: dict, rag_sonuc: dict | None) -> dict
# 4 bileşenli XAI skor açıklaması
# Returns: {aciklanabilir_skor, bilesenler: [{ad, skor, renk, notlar}, ...]}
```

### `services/rag_pipeline.py`

```python
capraz_kaynak_dogrula(haber_metni: str) -> dict
# Hibrit RAG pipeline: Routing → Indexing → Translation → Hibrit Retrieval → Generation
# Returns: {karar, kaynak_uzlasmasi, ana_bulgu, chroma_kaynak_sayisi,
#           tavily_canli_sayisi, kaynak_linkleri, kullanilan_sorgular, ...}

konu_tespit_et(metin: str) -> str
# Zero-shot konu sınıflandırma (siyaset/ekonomi/sağlık/teknoloji/spor/genel)

haberleri_indeksle(ham_metin: str) -> dict
# Tavily → TextSplitter → HF Embeddings → ChromaDB (kalıcı)
# Returns: {eklenen, makale_sayisi, kaynaklar, konu}

retrieval_yap(sorgular, hyde_metin, konu) -> list
# Hibrit: ChromaDB (skor ≥ 0.30) + Tavily fallback + RRF birleştirme
```

### `services/analysis.py`

```python
analyze_news_text(text: str, language: str = "tr") -> dict
# İki aşamalı Groq analizi: ön_analiz + derin_analiz
# Returns: {skor, guven_etiketi, manipulasyon, kaynak_kalitesi, gerekceler, ozet}
```

### `services/image_analysis.py`

```python
gorsel_analiz_et(gorsel_bytes: bytes, dosya_adi: str = "") -> dict
# EXIF metadata çıkarımı + piksel istatistikleri + Groq yorumu
# Returns: {karar, guven_yuzdesi, ana_sinyal, detaylar, risk_seviyesi, exif_sonuc}
```

### `services/video_analysis.py`

```python
video_analiz_et(url: str) -> dict
# YouTube transcript çekimi + dezenformasyon analizi
# Returns: {karar, guven_skoru, manipulasyon_teknigi, gerekceler, transcript_ozet}
```

---

## ⚙️ Kurulum

```bash
# 1. Repoyu klonla
git clone https://github.com/irembayrakk27/BGK_VeritasAI.git
cd BGK_VeritasAI

# 2. Sanal ortam oluştur
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Linux/macOS

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Ortam değişkenlerini tanımla
cp .env.example .env
# .env içine API anahtarlarını ekle

# 5. Uygulamayı başlat
streamlit run app.py
```

### `.env` Yapısı

```env
GROQ_API_KEY=gsk_your_key_here
TAVILY_API_KEY=tvly_your_key_here
USER_AGENT=VeritasAI/1.0
```

> `.env` dosyası `.gitignore` kapsamındadır. Streamlit Cloud'da **Settings → Secrets** üzerinden enjekte edilir.

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji | Kullanım Amacı |
|---|---|---|
| **LLM** | Groq (Llama-3.3-70b-versatile) | Haber analizi, RAG generation, görsel yorum |
| **RAG Orchestration** | LangChain v0.3 | Pipeline yönetimi, prompt şablonları |
| **Vector Store** | ChromaDB | Kalıcı embedding indeksleme ve semantic search |
| **Embeddings** | HuggingFace all-MiniLM-L6-v2 | Metin vektörleştirme (CPU, ücretsiz) |
| **Web Retrieval** | Tavily API | Canlı haber indexleme + hibrit fallback |
| **Scraping** | requests + BeautifulSoup4 | URL tabanlı metin çekimi |
| **Görsel İşleme** | PIL / Pillow | EXIF metadata + piksel analizi |
| **Video** | youtube-transcript-api | Altyazı tabanlı video analizi |
| **Otomasyon** | n8n | Webhook tabanlı asenkron iş akışı |
| **UI** | Streamlit | Multi-page web arayüzü |
| **Güvenlik** | Custom OWASP LLM layer | Prompt injection + adversarial koruma |

---

## 🔒 Güvenlik Notları

Bu proje **OWASP LLM Top 10** tehdit listesindeki riskleri ele almaktadır:

- **LLM01 (Prompt Injection)**: Pre-compiled regex ile pre-model filtreleme — LLM'e ulaşmadan bloklanır
- **LLM02 (Insecure Output Handling)**: JSON parse ile yapılandırılmış çıktı, raw string eval yok
- **LLM09 (Misinformation)**: RAG pipeline + hallucination guard prompt ile azaltılmış
- **Secrets Management**: API anahtarları env değişkenlerinde, kaynak kodda hiç yok

---

## 👩‍💻 Geliştirici

**İrem Bayrak** — AI Security & RAG Architecture  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-irem--bayrak--275--bay-0077B5?style=flat&logo=linkedin)](https://linkedin.com/in/irem-bayrak-275-bay)
[![GitHub](https://img.shields.io/badge/GitHub-irembayrakk27-181717?style=flat&logo=github)](https://github.com/irembayrakk27)