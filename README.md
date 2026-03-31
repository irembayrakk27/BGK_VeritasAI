# 🔍 VeritasAI

> Yapay zeka destekli haber doğrulama ve dezenformasyon tespit platformu

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://veritasai-bgk.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📖 Proje Hikayesi

Dijital ortamda hızla yayılan bilgi kirliliğine karşı geliştirilen VeritasAI, kullanıcıların haber metinlerini yapay zeka ile analiz etmesini sağlar. Uygulama yalnızca bir skor üretmekle kalmaz; insan ve yapay zekayı birlikte kullanarak kamusal bilgi kalitesini artırmayı hedefler.

---

## 🎯 Proje Amacı

- Haber içeriklerinin doğruluk seviyesini standart bir ölçekte değerlendirmek
- Kullanıcıya şeffaf ve anlaşılır bir sonuç sunmak
- Topluluk katkısıyla teyit sürecini güçlendirmek
- Türkçe dilini doğru kullanan bir AI motoru oluşturmak

---

## ✨ Temel Özellikler

| Özellik | Açıklama |
|--------|----------|
| 🎯 Güven Skoru | Her haber için 0-100 arası sayısal güven puanı |
| 📌 3 Gerekçeli Açıklama | Skorun nedenini 3 ayrı gerekçe ile açıklar |
| ⚠️ Manipülasyon Tespiti | Duygusal dil, abartı, eksik bağlam tespiti |
| 🔗 Gerçek Kaynak Gösterimi | Tavily API ile web'den gerçek kaynaklar çeker |
| 🤝 Topluluk Teyidi | Kullanıcılar kanıt ekleyerek skoru güncelleyebilir |
| 🕒 Analiz Geçmişi | Tüm analizler JSON olarak kalıcı kaydedilir |
| 🤖 n8n Otomasyonu | Analiz sonuçları otomatik e-posta ile iletilir |
| 🔄 Çift Aşamalı Analiz | İki ayrı AI çağrısı ile çapraz doğrulama |

---

## 📸 Ekran Görüntüleri

### Ana Analiz Ekranı
![Analiz Sonucu](assets/screenshots/analiz_sonucu.png)

### Topluluk Teyidi
![Topluluk Teyidi](assets/screenshots/topluluk_teyidi.png)

### Otomasyon Sayfası
![Otomasyon](assets/screenshots/otomasyon.png)

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Dil | Python 3.11 |
| Arayüz | Streamlit |
| AI Motoru | Groq Cloud (Llama-3.3-70b-Versatile) |
| Web Arama | Tavily API |
| Otomasyon | n8n |
| Versiyon Kontrolü | Git & GitHub |

---

## 🚀 Kurulum
```bash
# Repoyu klonla
git clone https://github.com/irembayrakk27/BGK_VeritasAI.git
cd BGK_VeritasAI

# Sanal ortam oluştur
python -m venv .venv
.\.venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

## ⚙️ Ortam Değişkenleri

`.env` dosyası oluştur ve şunları ekle:
```
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

## ▶️ Çalıştırma
```bash
streamlit run app.py
```

---

## 🤖 n8n Otomasyon Akışı
```
Haber Metni Gir → Webhook Tetiklenir → Groq AI Analiz Eder → Gmail'e Sonuç Gönderilir
```

Workflow dosyası: `n8n/veritasai_workflow.json`

---

## 🌐 Canlı Demo

🔗 **Uygulama:** [veritasai-bgk.streamlit.app](https://veritasai-bgk.streamlit.app/)

🎥 **Demo Videosu:** [OneDrive'da İzle](https://onedrive.live.com/?qt=allmyphotos&photosData=%2Fshare%2F5A8EC6E8C698F743%21sa4a0ce9b02ed44bb9b0329d66fae5656%3Fithint%3Dvideo%26e%3D3NqRaf%26migratedtospo%3Dtrue&cid=5A8EC6E8C698F743&id=5A8EC6E8C698F743%21sa4a0ce9b02ed44bb9b0329d66fae5656&redeem=aHR0cHM6Ly8xZHJ2Lm1zL3YvYy81YThlYzZlOGM2OThmNzQzL0lRQ2J6cUNrN1FLN1JKc0RLZFp2cmxaV0FhcGZvcXl1aTZTMHUybjNRdFVfLWNVP2U9M05xUmFm&v=photos)

---

## 💡 Vizyon

VeritasAI, yalnızca bir skor üreten araç değil; insan ve yapay zekayı birlikte kullanarak kamusal bilgi kalitesini artırmayı hedefleyen bir doğrulama asistanıdır.