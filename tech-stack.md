 🛠 VeritasAI Teknoloji Yığını (Tech Stack)

VeritasAI projesinin teknik altyapısı, bir Yazılım Mühendisliği öğrencisi olarak hız, doğruluk ve modern standartlar gözetilerek seçilmiştir.

---
 🏗 Seçilen Teknolojiler

| Bileşen | Seçilen Teknoloji | Neden Bu Teknolojiyi Seçtik? |
| :--- | :--- | :--- |
| **Programlama Dili** | **Python** | AI dünyasının standart dili. Okunması kolay ve Gemini SDK ile tam uyumlu. |
| **Arayüz (UI)** | **Streamlit** | Python tabanlı, veri odaklı ve hızlı web arayüzü geliştirme imkanı sunar. |
| **AI Motoru** | **Gemini 1.5 Pro** | Türkçe dil hakimiyeti ve dezenformasyon analizi yeteneği en yüksek Google AI modeli. |
| **Veri Yönetimi** | **JSON / CSV** | Başlangıç aşamasında, kullanıcı itirazlarını veritabanı karmaşası olmadan tutmak için idealdir. |

---

🚀 Adım Adım Kurulum Kılavuzu

Uygulamayı yerel ortamda çalıştırmak için aşağıdaki adımları takip edin:

1. Python Sanal Ortamını Hazırlama
Projeyi izole bir ortamda çalıştırmak için sanal ortam (venv) oluşturun:

```bash
#Proje ana dizinine gidin
cd BGK_VeritasAI

#Sanal ortam oluşturun
python -m venv .venv

#Sanal ortamı aktif edin (Windows)
.\.venv\Scripts\activate
```

2. Bağımlılıkları Kurma
Gerekli kütüphaneleri `requirements.txt` üzerinden yükleyin:

```bash
pip install -r requirements.txt
```

3. API Anahtarı Yapılandırması
1. `.env.example` dosyasının bir kopyasını oluşturun ve adını `.env` yapın.
2. [Google AI Studio](https://aistudio.google.com/) üzerinden aldığınız API anahtarını ilgili alana ekleyin:
   `GEMINI_API_KEY=API_ANAHTARINIZI_BURAYA_YAZIN`

4. Uygulamayı Başlatma
Streamlit sunucusunu ayağa kaldırın:

```bash
streamlit run app.py
```

---

💡 Neden Bu Mimari?

* **Geliştirme Hızı:** UI detaylarında kaybolmak yerine, Gemini'ye yazılacak "Analiz Promptu"nun kalitesine odaklanmayı sağlar.
* **Mühendislik Odaklılık:** İş mantığı Python katmanında kaldığı için, ileride React veya Django gibi daha karmaşık yapılara geçiş kolaydır.
* **Maliyet ve Verim:** Gemini 1.5 Pro'nun ücretsiz geliştirici kotası, proje prototipini oluşturmak için en verimli yoldur.
```

