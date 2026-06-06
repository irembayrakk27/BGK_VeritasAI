"""
╔══════════════════════════════════════════════════════════════════╗
║     VeritasAI × RAG From Scratch — VECTOR DATABASE MODÜLÜ      ║
║     Vektör Kaydetme + Retrieval (Arama Motoru)                  ║
╚══════════════════════════════════════════════════════════════════╝

Orijinal kodda OpenAI kullanılıyordu:
    vectorstore = Chroma.from_documents(documents=splits,
                                        embedding=OpenAIEmbeddings())

VeritasAI karşılığı:
    vectorstore = Chroma.from_documents(documents=splits,
                                        embedding=embd)
    → embd = embedding_module.py'deki HuggingFaceEmbeddings nesnesi

İş akışı (birebir orijinal):
    splits (chunk_module.py)
        ↓
    Chroma.from_documents() → vektöre çevir + veritabanına kaydet
        ↓
    vectorstore.as_retriever(search_kwargs={"k": ...})
        ↓
    retriever.get_relevant_documents(soru)
        ↓
    docs → LLM'e gönderilmeye hazır parçalar
"""

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from embedding_module import embd
from embedding_module import embed_soru, benzerlik_hesapla

# ══════════════════════════════════════════════════════════════════
# BÖLÜM 1 — VEKTÖRLERİ KAYDET (VectorStore Oluşturma)
#
# Orijinal Part 1, 2, 3:
#   vectorstore = Chroma.from_documents(documents=splits,
#                                       embedding=OpenAIEmbeddings())
# ══════════════════════════════════════════════════════════════════

def _tavily_ara(soru: str) -> list:
    """
    ChromaDB skoru eşiğin altında kalınca Tavily ile web araması yapar.
    Sonuçları Document formatına çevirir — zincirin geri kalanı değişmez.
    """
    import os
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    results = client.search(query=soru, max_results=3)

    tavily_docs = [
        Document(
            page_content=r.get("content", ""),
            metadata={"url": r.get("url", ""), "kaynak": "tavily"}
        )
        for r in results.get("results", [])
    ]

    print(f"[_tavily_ara] {len(tavily_docs)} web sonucu getirildi")
    return tavily_docs


def vectorstore_olustur(splits: list, koleksiyon: str = "veritasai_docs") -> Chroma:
    """
    Chunk'lara bölünmüş belgeleri alır, vektöre çevirir ve
    Chroma veritabanına kaydeder.

    Orijinal:
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=OpenAIEmbeddings()
        )

    Args:
        splits: chunk_module.py çıktısı — Document nesneleri listesi
        koleksiyon: ChromaDB koleksiyon adı

    Returns:
        Chroma vectorstore nesnesi — tüm vektör haritası burada
    """
    # ── Orijinal mantık (sadece embedding değişti) ────────────────
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embd,
        collection_name=koleksiyon,
        persist_directory="./data/chroma_db",
    )
    # ─────────────────────────────────────────────────────────────

    print(f"[vectorstore_olustur] {len(splits)} parça ChromaDB'ye kaydedildi")
    print(f"  koleksiyon: {koleksiyon}")

    return vectorstore


def vectorstore_yukle(koleksiyon: str = "veritasai_docs") -> Chroma:
    """
    Daha önce kaydedilmiş bir ChromaDB koleksiyonunu diskten yükler.
    Aynı haberi tekrar indekslemek zorunda kalmamak için kullanılır.

    Args:
        koleksiyon: Yüklenecek koleksiyon adı

    Returns:
        Chroma vectorstore nesnesi
    """
    vectorstore = Chroma(
        collection_name=koleksiyon,
        embedding_function=embd,
        persist_directory="./data/chroma_db",
    )

    print(f"[vectorstore_yukle] Koleksiyon diskten yüklendi: {koleksiyon}")
    return vectorstore


# ══════════════════════════════════════════════════════════════════
# BÖLÜM 2 — RETRIEVAL (Arama Motoru)
#
# Orijinal:
#   retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
#   docs      = retriever.get_relevant_documents("What is Task Decomposition?")
#   len(docs)
# ══════════════════════════════════════════════════════════════════

def retriever_olustur(vectorstore: Chroma, k: int = 1):
    """
    Statik ChromaDB veritabanını dinamik bir arama motoruna dönüştürür.

    Orijinal:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

    k parametresi ne yapar?
        k=1 → sorguya en yakın 1 parça getirilir
        k=3 → en yakın 3 parça getirilir
        k=4 → rag_overview.py varsayılanı (daha fazla bağlam)

    VeritasAI için önerilen k değerleri:
        Kısa haber analizi  → k=1 veya k=2
        Kaynak çapraz doğrulama → k=3 veya k=4

    Args:
        vectorstore: vectorstore_olustur() çıktısı
        k: Kaç parça getirilsin

    Returns:
        LangChain retriever nesnesi
    """
    # ── Orijinal satır (birebir) ──────────────────────────────────
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    # ─────────────────────────────────────────────────────────────

    print(f"[retriever_olustur] Arama motoru hazır → k={k}")
    return retriever


def ilgili_belgeleri_getir(retriever, soru: str) -> list:
    """
    Arama motorunu çalıştırır, sorguya en yakın belge parçalarını döndürür.

    Arka planda şu adımlar çalışır (orijinal açıklamayla birebir):
        1. Soru alınır, embedding modeli ile vektöre dönüştürülür
        2. Bu vektör, ChromaDB'deki tüm parça vektörleriyle karşılaştırılır
        3. En yüksek cosine similarity skoruna sahip k adet parça seçilir
        4. Seçilen parçalar docs listesi olarak döndürülür

    Orijinal:
        docs = retriever.get_relevant_documents("What is Task Decomposition?")
        len(docs)

    Args:
        retriever: retriever_olustur() çıktısı
        soru: Kullanıcı sorusu veya VeritasAI analiz sorusu

    Returns:
        Document nesneleri listesi — LLM'e gönderilmeye hazır
    """
    # ── Orijinal satır (birebir) ──────────────────────────────────
    docs = retriever.invoke(soru)
    # ─────────────────────────────────────────────────────────────
    

    print(f"[ilgili_belgeleri_getir] Getirilen parça sayısı: {len(docs)}")

    return docs

        

# ══════════════════════════════════════════════════════════════════
# VERİTASAI KULLANIM NOKTASI
# Tüm adımları tek fonksiyonda birleştir:
#   splits → vectorstore → retriever → docs
# ══════════════════════════════════════════════════════════════════



def haber_sorgula(splits: list, soru: str, k: int = 1) -> list:
    """
    chunk_module.py çıktısından başlayarak tam retrieval pipeline'ını çalıştırır.

    Adımlar (orijinal iş akışı):
        splits gelir
            ↓ Chroma.from_documents()
        vectorstore oluşur
            ↓ as_retriever(k=k)
        retriever hazırlanır
            ↓ get_relevant_documents(soru)
        docs döner

    Args:
        splits: chunk_module.py'den gelen Document listesi
        soru: Kullanıcının sorusu veya analiz sorusu
        k: Kaç parça getirilsin (varsayılan 1 — orijinalle aynı)

    Returns:
        En alakalı k adet Document parçası
    """
    import time
    koleksiyon = f"veritas_{int(time.time())}"
    vectorstore = vectorstore_olustur(splits, koleksiyon)
    retriever   = retriever_olustur(vectorstore, k=k)
    docs        = ilgili_belgeleri_getir(retriever, soru)
    
    if not docs:
        print("[haber_sorgula] ChromaDB sonuç döndürmedi → Tavily'e geçiliyor")
        docs = _tavily_ara(soru)
    else:
        soru_vec = embed_soru(soru)
        en_yuksek_skor = max(
            benzerlik_hesapla(soru_vec, embed_soru(d.page_content))
            for d in docs
        )

        ESIK = 0.25

        if en_yuksek_skor < ESIK:
            print(f"[haber_sorgula] Skor {en_yuksek_skor:.2f} < {ESIK} → Tavily'e geçiliyor")
            docs = _tavily_ara(soru)
        else:
            print(f"[haber_sorgula] Skor {en_yuksek_skor:.2f} ≥ {ESIK} → ChromaDB kullanılıyor")

    return docs    




# ══════════════════════════════════════════════════════════════════
# TEST — python vectorstore_module.py ile çalıştır
# ════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  VeritasAI — VectorStore & Retrieval Modülü Testi")
    print("=" * 55)

    # Örnek splits — normalde chunk_module.py'den gelir
    ornek_splits = [
        Document(page_content="Merkez Bankası faiz oranını yüzde 45'te sabit tuttu.",
                 metadata={"kaynak": "test"}),
        Document(page_content="Galatasaray şampiyonluk maçına çıkıyor.",
                 metadata={"kaynak": "test"}),
        Document(page_content="TÜFE verileri açıklandı, yıllık enflasyon yüzde 48.",
                 metadata={"kaynak": "test"}),
        Document(page_content="Döviz kurunda dolar 38 TL'ye geriledi.",
                 metadata={"kaynak": "test"}),
    ]

    test_soru = "Enflasyon ve faiz oranı hakkında ne söyleniyor?"

    # ── Test 1: k=1 (orijinal varsayılan) ────────────────────────
    print(f"\n📌 Test 1 — k=1 (en yakın 1 parça)")
    print(f"  Soru: '{test_soru}'")
    docs_1 = haber_sorgula(ornek_splits, test_soru, k=1)
    print(f"  Getirilen parça sayısı (len(docs)): {len(docs_1)}")
    print(f"  İçerik: '{docs_1[0].page_content}'")

    # ── Test 2: k=2 ──────────────────────────────────────────────
    print(f"\n📌 Test 2 — k=2 (en yakın 2 parça)")
    docs_2 = haber_sorgula(ornek_splits, test_soru, k=2)
    print(f"  Getirilen parça sayısı (len(docs)): {len(docs_2)}")
    for i, d in enumerate(docs_2):
        print(f"  [{i+1}] '{d.page_content}'")

    # ── Test 3: Adım adım (ayrı fonksiyonlarla) ──────────────────
    print(f"\n📌 Test 3 — Adım Adım Pipeline")
    vs  = vectorstore_olustur(ornek_splits, koleksiyon="test_koleksiyon")
    ret = retriever_olustur(vs, k=1)
    doc = ilgili_belgeleri_getir(ret, "Dolar kuru ne oldu?")
    print(f"  Dolar sorusu için en alakalı: '{doc[0].page_content}'")

    print("\n" + "=" * 55)
    print("✅ VectorStore & Retrieval modülü hazır.")
    print("   Kullanım: from rag.vectorstore_module import haber_sorgula")