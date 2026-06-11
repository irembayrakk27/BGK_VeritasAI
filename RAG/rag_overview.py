"""
╔══════════════════════════════════════════════════════════════════╗
║      VeritasAI × RAG From Scratch — PART 1: OVERVIEW           ║
║      Indexing → Retrieval → Generation (Groq + ChromaDB)        ║
╚══════════════════════════════════════════════════════════════════╝

Bu dosya, RAG From Scratch'in "Part 1 Overview" modülünü
VeritasAI'ye entegre eder.

Orijinaldeki değişiklikler:
    ❌ ChatOpenAI       → ✅ ChatGroq (llama-3.3-70b-versatile)
    ❌ OpenAIEmbeddings → ✅ HuggingFaceEmbeddings (çok dilli)
    ❌ Sabit web URL    → ✅ Tavily ile haber kaynağı + özel URL desteği
    ✅ Türkçe RAG prompt eklendi
    ✅ VeritasAI analiz pipeline'ına bağlantı noktası hazır
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ─── Ortam yükle ─────────────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
#                                        ↑
#                          RAG/ klasöründeyiz, bir üst dizin .env'in yeri

# ─── LangChain ───────────────────────────────────────────────────
import bs4
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

# ─── Groq ────────────────────────────────────────────────────────
from langchain_groq import ChatGroq

# ─── HuggingFace Embeddings ──────────────────────────────────────
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

# ─── RAG modülleri ───────────────────────────────────────────────
from RAG.chunk_module import chunk_otomatik
from RAG.vectorStore_module import haber_sorgula

# ══════════════════════════════════════════════════════════════════
# ADIM 1: LLM & EMBEDDING TANIMLA
# (environment_setup.py ile aynı modeller — tutarlılık için)
# ══════════════════════════════════════════════════════════════════

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=os.environ.get("GROQ_API_KEY"),
)

# Türkçe haberleri de iyi anlayan çok dilli model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


# ══════════════════════════════════════════════════════════════════
# ADIM 2: INDEXING (Belgeleri yükle → parçala → vektör veritabanına kaydet)
#
# Buradaki mantık:
#   Bir gazete haberini veya web sayfasını alıyoruz,
#   küçük parçalara bölüyoruz (chunk),
#   her parçayı sayısal vektöre çevirip ChromaDB'ye kaydediyoruz.
#   Soru geldiğinde ilgili parçaları geri çekebiliriz.
# ══════════════════════════════════════════════════════════════════

def index_url(url: str, collection_name: str = "veritasai_docs") -> Chroma:
    """
    Verilen URL'yi indeksler ve ChromaDB vektör veritabanına kaydeder.
    
    Args:
        url: İndekslenecek haber/kaynak URL'si
        collection_name: ChromaDB koleksiyon adı
    
    Returns:
        Sorgulamaya hazır ChromaDB vektör deposu
    
    Örnek:
        vs = index_url("https://www.bbc.com/turkce/haberler-...")
    """
    print(f"📥 Yükleniyor: {url}")

    # Loader: sayfanın sadece içerik kısmını çek (reklam/nav hariç)
    loader = WebBaseLoader(
        web_paths=(url,),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                # Yaygın haber sitesi CSS sınıfları — gerekirse ekle/çıkar
                class_=(
                    "post-content", "post-title", "post-header",
                    "article-body", "entry-content", "article__body",
                    "news-content", "haber-icerik",
                )
            )
        ),
    )
    docs = loader.load()

    if not docs:
        print("⚠️  CSS filtresi hiçbir içerik bulamadı, tüm sayfa yükleniyor...")
        loader = WebBaseLoader(web_paths=(url,))
        docs = loader.load()

    print(f"📄 {len(docs)} belge yüklendi")

    # Splitter: 1000 karakter parça, 200 karakter örtüşme
    # Türkçe metinler için iyi çalışır; gerekirse chunk_size'ı düşür
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    splits = splitter.split_documents(docs)
    print(f"✂️  {len(splits)} parçaya bölündü")

    # ChromaDB'ye kaydet
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory="./data/chroma_db",  # kalıcı depolama
    )
    print(f"✅ ChromaDB'ye kaydedildi → koleksiyon: {collection_name}")

    return vectorstore


def index_text(text: str, metadata: dict = None, collection_name: str = "veritasai_docs") -> Chroma:
    """
    Ham metin (haber içeriği) alır, doğrudan indeksler.
    VeritasAI'de kullanıcı metin yapıştırınca bu çağrılır.
    
    Args:
        text: Ham haber metni
        metadata: {'url': ..., 'tarih': ..., 'kaynak': ...} gibi ek bilgi
        collection_name: ChromaDB koleksiyon adı
    
    Returns:
        ChromaDB vektör deposu
    """
    from langchain_core.documents import Document

    doc = Document(
        page_content=text,
        metadata=metadata or {"kaynak": "kullanici_girisi"},
    )

    from RAG.chunk_module import chunk_otomatik

    splits = chunk_otomatik(text, kaynak_meta=metadata)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,   # Haberler kısa olabileceği için daha küçük
        chunk_overlap=150,
    )
    splits = splitter.split_documents([doc])

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory="./data/chroma_db",
    )
    return vectorstore


# ══════════════════════════════════════════════════════════════════
# ADIM 3: RETRIEVAL & GENERATION CHAIN'İ OLUŞTUR
#
# Orijinal RAG From Scratch prompt'u Türkçe'ye uyarlandı.
# Ayrıca VeritasAI'nin doğrulama amacı için özelleştirildi.
# ══════════════════════════════════════════════════════════════════

# ── Türkçe RAG Prompt ─────────────────────────────────────────────
VERITAS_RAG_PROMPT = ChatPromptTemplate.from_template("""
Sen VeritasAI'nin bilgi doğrulama asistanısın.
Aşağıdaki bağlam belgelerini kullanarak soruyu yanıtla.

KURALLAR:
- Sadece bağlamdaki bilgilere dayan. Tahmin yapma.
- Bilgi yoksa "Bu konuda bağlamda yeterli bilgi bulunamadı." de.
- Yanıtın Türkçe olsun.
- Haber doğrulama sorusuysa; iddia, kaynak ve güvenilirlik açısından değerlendir.

Bağlam:
{context}

Soru: {question}

Yanıt:
""")


def build_rag_chain(vectorstore: Chroma, k: int = 4):
    """
    Verilen vektör deposu üzerinden RAG zinciri kurar.
    
    Args:
        vectorstore: index_url() veya index_text() çıktısı
        k: Her sorguda kaç belge parçası getirilsin (varsayılan 4)
    
    Returns:
        LangChain LCEL zinciri (invoke() ile çalıştırılır)
    
    Örnek:
        chain = build_rag_chain(vs)
        cevap = chain.invoke("Bu haberde hangi iddialar var?")
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    def format_docs(docs):
        """Belgeleri tek metin bloğuna birleştir."""
        return "\n\n---\n\n".join(
            f"[Kaynak {i+1}]: {doc.page_content}"
            for i, doc in enumerate(docs)
        )

    # LCEL zinciri: Orijinal RAG From Scratch yapısıyla birebir aynı
    # Sadece prompt ve LLM değişti
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | VERITAS_RAG_PROMPT
        | llm
        | StrOutputParser()
    )

    return chain


# ══════════════════════════════════════════════════════════════════
# ADIM 4: VERİTASAI ENTEGRASYONu
# Mevcut analyze_news_text() fonksiyonuna RAG desteği ekleme noktası
# ══════════════════════════════════════════════════════════════════

def rag_destekli_analiz(
    haber_metni: str,
    kaynak_url: str = None,
    soru: str = "Bu haberdeki temel iddialar neler? Güvenilirlik açısından değerlendir.",
) -> dict:
    print("[RAg] rag_destekli_analiz çalıştı")
    """
    VeritasAI'nin mevcut analiz pipeline'ına RAG katmanı ekler.

    Nasıl çalışır:
        1. Haber metnini ChromaDB'ye indeksle
        2. Varsa kaynak URL'yi de indeksle (çapraz doğrulama)
        3. RAG chain ile soruyu yanıtla
        4. Sonucu VeritasAI rapor formatına uygun döndür

    Args:
        haber_metni: Kullanıcının yapıştırdığı haber
        kaynak_url: Opsiyonel — Tavily'den bulunan veya kullanıcının verdiği URL
        soru: RAG'a sorulacak soru (varsayılan: genel doğrulama sorusu)

    Returns:
        {"rag_cevap": str, "belge_sayisi": int, "koleksiyon": str}
    """
    import time
    # Her analiz için benzersiz koleksiyon adı (çakışma önleme)
    koleksiyon = f"veritas_{int(time.time())}"

    # Kullanıcı metnini indeksle
    vs = index_text(
        text=haber_metni,
        metadata={"tip": "kullanici_girisi", "url": kaynak_url or ""},
        collection_name=koleksiyon,
    )

    # Eğer kaynak URL varsa onu da aynı koleksiyona ekle
    if kaynak_url:
        try:
            print(f"🔗 Kaynak URL indeksleniyor: {kaynak_url}")
            extra_vs = index_url(url=kaynak_url, collection_name=koleksiyon)
        except Exception as e:
            print(f"⚠️  URL indeksleme başarısız: {e}")

    # RAG chain kur ve çalıştır
    print("[RAG] Chain invoke başlıyor")
    chain = build_rag_chain(vs, k=3)
    rag_cevap = chain.invoke(soru)

    return {
        "rag_cevap": rag_cevap,
        "koleksiyon": koleksiyon,
    }
    print("[RAG] Chain invoke tamamlandı")


# ══════════════════════════════════════════════════════════════════
# HIZLI TEST — python rag_overview.py ile çalıştır
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  VeritasAI × RAG From Scratch — Part 1 Test")
    print("=" * 55)

    # --- Test 1: URL indeksleme ---
    test_url = "https://lilianweng.github.io/posts/2023-06-23-agent/"
    print(f"\n📌 Test 1: URL İndeksleme\nURL: {test_url}\n")

    try:
        vs = index_url(test_url, collection_name="test_collection")
        chain = build_rag_chain(vs)
        soru = "Task Decomposition nedir? Kısaca açıkla."
        print(f"❓ Soru: {soru}")
        cevap = chain.invoke(soru)
        print(f"💬 Cevap:\n{cevap}\n")
    except Exception as e:
        print(f"❌ Test 1 başarısız: {e}\n")

    # --- Test 2: Ham metin indeksleme (VeritasAI senaryosu) ---
    print("📌 Test 2: Ham Metin → RAG Analiz\n")
    ornek_haber = """
    Türkiye'de asgari ücret 2025 yılında yüzde 30 oranında artırıldı.
    Çalışma Bakanlığı'nın açıklamasına göre yeni asgari ücret 25.000 TL olarak belirlendi.
    Muhalefet partileri bu rakamın yetersiz olduğunu savunuyor.
    """
    try:
        sonuc = rag_destekli_analiz(
            haber_metni=ornek_haber,
            soru="Bu haberdeki sayısal iddialar neler? Doğrulanabilir mi?",
        )
        print(f"💬 RAG Analiz:\n{sonuc['rag_cevap']}\n")
    except Exception as e:
        print(f"❌ Test 2 başarısız: {e}\n")

    print("=" * 55)
    print("✅ Part 1 Overview tamamlandı.")
    print("📂 Sonraki adım: query_translation.py (Multi-Query, HyDE...)")