# VeritasAI

VeritasAI, dijital ortamda hızla yayılan bilgi kirliliğine karşı geliştirilen, yapay zeka destekli bir haber doğrulama ve dezenformasyon tespit platformudur.  
Uygulama, kullanıcıdan alınan haber metnini Streamlit tabanlı sade bir arayüzde analiz eder ve Gemini 1.5 Pro API desteğiyle güvenilirlik değerlendirmesi sunar.

## Proje Amacı

- Haber içeriklerinin doğruluk seviyesini standart bir ölçekte değerlendirmek
- Kullanıcıya şeffaf ve anlaşılır bir sonuç sunmak
- Topluluk katkısıyla teyit sürecini güçlendirmek

## Temel Özellikler

- **Güven Skoru (0-100):** Her haber için sayısal güven puanı üretir.
- **3 Gerekçeli Açıklama:** Skorun nedenini tam olarak 3 ayrı gerekçe ile açıklar.
- **Kaynak Karşılaştırması:** Reuters ve AP gibi güvenilir ajanslarla çapraz doğrulama yaklaşımını destekler.
- **Topluluk Teyidi:** Kullanıcıların kanıt ekleyerek doğrulama sürecine katkı vermesine imkan tanır.
- **İnsan Teyidi Etiketi:** Topluluktan gelen ve doğrulanan katkıları "İnsan Teyidi" etiketi ile işaretler.

## Teknoloji Yığını

- **Backend / Dil:** Python
- **Arayüz:** Streamlit
- **Yapay Zeka:** Groq Cloud (Llama-3.3-70b-Versatile)

## Kurulum

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Ortam Değişkenleri

- `.env.example` dosyasını `.env` olarak kopyalayın.
- `GROQ_API_KEY` değerini girin.

## Çalıştırma

```bash
streamlit run app.py
```

## Beklenen Çıktı Formatı

- `trust_score`: 0-100 arası güven skoru
- `reasons`: Tam 3 maddeden oluşan gerekçeler
- `references`: Reuters/AP öncelikli doğrulama referansları
- `community_verdict`: Topluluk Teyidi sonucu (varsa)

## Vizyon

VeritasAI, yalnızca bir skor üreten araç değil; insan ve yapay zekayı birlikte kullanarak kamusal bilgi kalitesini artırmayı hedefleyen bir doğrulama asistanıdır.


## n8n Otomasyon Akışı
Haber analizi sonuçları otomatik olarak e-posta ile iletilir.
Workflow dosyası: `n8n/veritasai_workflow.json`

##  Canlı Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://veritasai-bgk.streamlit.app/)

Uygulama Linki: [veritasai-bgk.streamlit.app](https://veritasai-bgk.streamlit.app/)

Demo Videosu:[OneDrive'da İzle](https://onedrive.live.com/?qt=allmyphotos&photosData=%2Fshare%2F5A8EC6E8C698F743%21sa4a0ce9b02ed44bb9b0329d66fae5656%3Fithint%3Dvideo%26e%3D3NqRaf%26migratedtospo%3Dtrue&cid=5A8EC6E8C698F743&id=5A8EC6E8C698F743%21sa4a0ce9b02ed44bb9b0329d66fae5656&redeem=aHR0cHM6Ly8xZHJ2Lm1zL3YvYy81YThlYzZlOGM2OThmNzQzL0lRQ2J6cUNrN1FLN1JKc0RLZFp2cmxaV0FhcGZvcXl1aTZTMHUybjNRdFVfLWNVP2U9M05xUmFm&v=photos)