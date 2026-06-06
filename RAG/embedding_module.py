
# ── Orijinal import yapısının VeritasAI karşılığı ─────────────────
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_community.utils.math import cosine_similarity


# ══════════════════════════════════════════════════════════════════
# MODÜLÜN TANIMI

# VeritasAI: embd = HuggingFaceEmbeddings(model_name="...")

# ══════════════════════════════════════════════════════════════════

embd = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


# ══════════════════════════════════════════════════════════════════
# TEKİL METİNLERİN VEKTÖRLEŞTİRİLMESİ
# Orijinal Part 2:
#   query_result    = embd.embed_query(question)
#   document_result = embd.embed_query(document)
# ══════════════════════════════════════════════════════════════════

def embed_soru(soru: str) -> list:
    """
    Kullanıcı sorusunu vektöre çevirir.
    Orijinal: query_result = embd.embed_query(question)

    Args:
        soru: Kullanıcının sorduğu metin

    Returns:
        Sayı dizisi (float listesi) — boyut: 384
    """
    query_result = embd.embed_query(soru)
    return query_result


def embed_belge(belge: str) -> list:
    """
    Bir haber metnini / doküman parçasını vektöre çevirir.
    Orijinal: document_result = embd.embed_query(document)

    Args:
        belge: Chunk'a bölünmüş haber metni

    Returns:
        Sayı dizisi (float listesi) — boyut: 384
    """
    document_result = embd.embed_query(belge)
    return document_result


# ══════════════════════════════════════════════════════════════════
# BENZERLİK ÖLÇÜMÜ
# Orijinal kodun devamı: cosine_similarity ile iki vektör karşılaştırılır.
#
# Cosine similarity nedir?
#   İki vektörün "açısını" ölçer.
#   1.0  → tamamen aynı anlam
#   0.0  → hiç ilgisi yok
#   -1.0 → zıt anlam
# ══════════════════════════════════════════════════════════════════

def benzerlik_hesapla(vektor_1: list, vektor_2: list) -> float:
    """
    İki vektör arasındaki cosine similarity değerini döndürür.
    Orijinal: cosine_similarity([query_result], [document_result])

    Args:
        vektor_1: embed_soru() veya embed_belge() çıktısı
        vektor_2: embed_soru() veya embed_belge() çıktısı

    Returns:
        0.0 ile 1.0 arasında benzerlik skoru
    """
    skor = cosine_similarity([vektor_1], [vektor_2])
    return float(skor[0][0])


# ══════════════════════════════════════════════════════════════════
# VERİTASAI KULLANIM NOKTASI
# Kullanıcı sorusu ile haber parçaları arasındaki benzerliği ölç.
# En yüksek skorlu parça → en alakalı bağlam → LLM'e gönderilir.
# ══════════════════════════════════════════════════════════════════

def en_alakali_parcayi_bul(soru: str, parcalar: list) -> dict:
    """
    Bir soru ile birden fazla metin parçası arasındaki
    cosine similarity'yi ölçer, en yüksek skorlu parçayı döndürür.

    Args:
        soru: Kullanıcının sorduğu metin
        parcalar: chunk_module.py'den gelen string listesi

    Returns:
        {"parca": str, "skor": float, "index": int}
    """
    soru_vektor = embed_soru(soru)

    en_yuksek_skor = -1
    en_iyi_parca = None
    en_iyi_index = 0

    for i, parca in enumerate(parcalar):
        parca_vektor = embed_belge(parca)
        skor = benzerlik_hesapla(soru_vektor, parca_vektor)

        if skor > en_yuksek_skor:
            en_yuksek_skor = skor
            en_iyi_parca = parca
            en_iyi_index = i

    return {
        "parca": en_iyi_parca,
        "skor": round(en_yuksek_skor, 4),
        "index": en_iyi_index
    }


# ══════════════════════════════════════════════════════════════════
# TEST — python embedding_module.py ile çalıştır
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  VeritasAI — Embedding Modülü Testi")
    print("=" * 55)

    # ── Test 1: Tekil vektörleştirme ─────────────────────────────
    # Orijinal Part 2 mantığı:
    #   query_result    = embd.embed_query(question)
    #   document_result = embd.embed_query(document)

    soru  = "Bu haberde hangi iddia var?"
    belge = "Cumhurbaşkanı ekonomi paketini açıkladı, asgari ücret artışı bekleniyor."

    print("\n📌 Test 1 — Tekil Vektörleştirme")
    soru_vec  = embed_soru(soru)
    belge_vec = embed_belge(belge)

    print(f"  Soru  : '{soru}'")
    print(f"  Boyut : {len(soru_vec)} boyutlu vektör")
    print(f"  İlk 5 değer: {[round(x, 4) for x in soru_vec[:5]]}")

    print(f"\n  Belge : '{belge}'")
    print(f"  Boyut : {len(belge_vec)} boyutlu vektör")
    print(f"  İlk 5 değer: {[round(x, 4) for x in belge_vec[:5]]}")

    # ── Test 2: Cosine similarity ─────────────────────────────────
    print("\n📌 Test 2 — Benzerlik Ölçümü (Cosine Similarity)")

    skor = benzerlik_hesapla(soru_vec, belge_vec)
    print(f"  Soru ↔ Belge benzerliği : {skor}")

    alakasiz     = "Galatasaray dün gece 3-0 galip geldi."
    alakasiz_vec = embed_belge(alakasiz)
    skor_dusuk   = benzerlik_hesapla(soru_vec, alakasiz_vec)
    print(f"  Soru ↔ Alakasız metin  : {skor_dusuk}")
    print(f"  → Ekonomi haberi daha yakın mı? {'✅ Evet' if skor > skor_dusuk else '❌ Hayır'}")

    # ── Test 3: En alakalı parçayı bul ───────────────────────────
    print("\n📌 Test 3 — En Alakalı Parçayı Bul (VeritasAI senaryosu)")

    test_soru   = "Enflasyon oranı nedir?"
    test_parcalar = [
        "Galatasaray bu sezon şampiyonluk yolunda ilerliyor.",
        "Merkez Bankası faiz kararını açıkladı, enflasyonla mücadele sürüyor.",
        "Yeni telefon modeli tanıtıldı, özellikleri dikkat çekiyor.",
        "TÜFE verileri açıklandı, yıllık enflasyon yüzde 48'e geriledi.",
    ]

    sonuc = en_alakali_parcayi_bul(test_soru, test_parcalar)
    print(f"  Soru       : '{test_soru}'")
    print(f"  En alakalı : '{sonuc['parca']}'")
    print(f"  Benzerlik  : {sonuc['skor']}  (index: {sonuc['index']})")

    print("\n" + "=" * 55)
    print("✅ Embedding modülü hazır.")
    print("   Kullanım: from rag.embedding_module import embed_soru, benzerlik_hesapla")