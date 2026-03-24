📝 VeritasAI: Ürün Gereksinim Belgesi (PRD)
1. Ürün Vizyonu ve Tanımı
VeritasAI, dijital dünyadaki bilgi kirliliğine (dezenformasyon) karşı geliştirilmiş, yapay zeka analizi ile topluluk teyidini birleştiren şeffaf bir doğrulama ekosistemidir. Kullanıcılar şüpheli buldukları haberleri analiz ettirirken, aynı zamanda kanıt sunarak doğruluk skoruna katkıda bulunabilirler.

2. Kullanıcı Hedefleri
Haberlerin doğruluk payını saniyeler içinde bilimsel bir skorla görmek.

Haberin neden şüpheli olduğunu (dil kullanımı, kaynak eksikliği vb.) şeffafça anlamak.

Yalan haberlere karşı somut kanıtlar sunarak toplumsal bilgi kirliliğini önlemek.

3. Temel Özellikler (MVP+)
3.1. Yapay Zeka Analiz Motoru (Gemini API)
Metin Tarama: Haber metnindeki manipülatif dil, clickbait başlıklar ve mantık hatalarını tespit eder.

Güven Skoru: Habere 0-100 arası dinamik bir puan atar.

Gerekçelendirme: Skoru belirleyen 3 ana sebebi (Örn: "Kaynak belirsiz", "Aşırı duygusal dil") listeler.

3.2. Kaynak Doğrulama ve Benzer Haberler (Yeni)
Otomatik Kaynak Tarama: AI, haberdeki iddiaları internet üzerindeki güvenilir haber ajanslarıyla (Reuters, AP, AA vb.) çapraz sorgular.

Referans Linkleri: Kullanıcıya, konuyla ilgili doğrulanmış haber linklerini "Benzer Kaynaklar" olarak sunar.

3.3. Topluluk Teyit Paneli (Fark Yaratan Özellik)
Kanıt Sunma Formu: Kullanıcılar, AI'ın verdiği skoru hatalı bulursa güvenilir bir kaynak linki paylaşarak itiraz edebilir.

Şeffaf Düzeltme: Sunulan kanıtlar sistemde loglanır ve haberin nihai güvenilirliğine "İnsan Teyidi" etiketi ekler.

4. Kullanıcı Ekranları (UI/UX)
Ana Panel: Büyük bir metin giriş alanı ve "Gerçeği Sorgula" butonu.

Rapor Paneli: * Görsel Skor: Renkli (Yeşil/Sarı/Kırmızı) büyük bir puan kartı.

Analiz Detayları: AI'ın nedenleri ve benzer haber linkleri.

İtiraz Butonu: "Bu skoru hatalı mı buldunuz? Kanıt ekleyin" butonu ve açılan form penceresi.

5. Teknik Altyapı (Tech Stack)
Backend & Frontend: Streamlit (Hızlı prototipleme ve temiz UI için).

Yapay Zeka Beyni: Google Gemini 1.5 Pro API.

Veri Depolama: Başlangıç aşamasında topluluk itirazları için JSON veya CSV tabanlı yerel veritabanı.

6. Başarı Kriterleri
Türkçe haber analizinde %80 ve üzeri isabet oranı.

Analiz raporunun 10 saniyenin altında oluşturulması.

180 kişilik yarışmada "Topluluk Katılımı" özelliğiyle özgünlük ödülü/derecesi almak.
