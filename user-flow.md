🌊 VeritasAI Kullanıcı Akışı (User Flow)
1. Karşılama ve Giriş (Home Screen)
Görür: Sade ve güven veren bir arayüz. Ortada büyük bir metin alanı (Text Area) ve üzerinde "Analiz Edilecek Haberi Buraya Yapıştırın" talimatı.

Yapar: Şüphelendiği haber metnini veya sosyal medya paylaşımını kutucuğa yapıştırır.

Aksiyon: "Gerçeği Sorgula" butonuna tıklar.

2. Analiz Süreci (Processing)
Görür: Ekranda şık bir yükleme animasyonu (Spinner) ve "Gemini 1.5 Pro haberi dezenformasyon kriterlerine göre inceliyor..." mesajı.

AI Ne Yapar: * Metni dilsel manipülasyon açısından tarar.

İddiaları ayrıştırıp Google Search (Grounding) üzerinden güvenilir ajanslarla karşılaştırır.

Veritabanında bu habere dair daha önce yapılmış bir "İnsan Teyidi" (itiraz) olup olmadığını kontrol eder.

3. Rapor Paneli (Results & Report)
Görür: * Güven Skoru: (Örn: %35 - Kırmızı) Büyük bir görsel kart.

Nedenler: "Kaynak belirtilmemiş", "Duygusal tetikleyiciler yoğun", "Başlık ile içerik uyumsuz" gibi 3 net gerekçe.

Benzer Kaynaklar: Eğer haber gerçekse veya benzerleri varsa, Reuters, AA veya AP gibi kurumlardan doğrudan linkler.

Etiket: Eğer topluluktan itiraz gelmişse, "⚠️ Topluluk Teyidi: Kullanıcılar bu habere kanıt ekledi" uyarısı.

4. Etkileşim ve Geri Bildirim (Feedback Loop)
Yapar: Eğer kullanıcı skoru hatalı bulursa veya elinde ek bir bilgi varsa "Hatalı mı? Kanıt Ekle" butonuna basar.

Görür: Bir form açılır. Buraya güvenilir bir URL ve kısa bir not ekler.

Sonuç: Gönderilen veri sisteme (JSON/CSV) kaydedilir ve aynı haberi sorgulayan bir sonraki kişiye "İnsan Teyidi" olarak gösterilir.
