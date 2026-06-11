"""
VeritasAI — RAG Pipeline v2: Çapraz Kaynak Doğrulama
=====================================================

Katmanlar (RAG From Scratch serisiyle birebir örtüşür):

  KATMAN 1 — INDEXING
    NewsAPI'den haber çek → RecursiveCharacterTextSplitter ile böl
    → HuggingFace Embeddings → ChromaDB'ye kaydet

  KATMAN 2 — QUERY TRANSLATION
    Multi-Query: kullanıcı metninden 3 farklı sorgu üret
    HyDE (Hypothetical Document Embedding): varsayımsal belge üret,
    onu da vektöre çevir → daha iyi semantic match

  KATMAN 3 — ROUTING + QUERY CONSTRUCTION
    Konu tespiti: siyaset / ekonomi / sağlık / spor / genel
    Konuya göre NewsAPI parametrelerini ayarla (routing)
    Metadata filtresi: tarihe göre ChromaDB'yi filtrele

  KATMAN 4 — RETRIEVAL + RAG FUSION
    Her sorgu için ChromaDB'de ara
    Reciprocal Rank Fusion ile sonuçları birleştir

  KATMAN 5 — GENERATION
    Groq LLM ile çapraz kaynak doğrulama raporu üret
    Hallucination guard: sadece bulunan kaynaklara dayan
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# ── LangChain — güncel importlar ─────────────────────────────────
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document                     # langchain.schema değil
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from RAG.rag_overview import build_rag_chain, index_url, index_text


from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ── Sabitler ──────────────────────────────────────────────────────
CHROMA_PATH   = str(Path(__file__).resolve().parent.parent / "data" / "chroma_db")
EMBED_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL    = "llama-3.3-70b-versatile"
MAX_HABERLER  = 20
TOP_K         = 5
MQ_SAYI       = 3    # Multi-Query sorgu sayısı

# Konu → NewsAPI anahtar kelime eşlemesi (Routing tablosu)
KONU_ROUTING = {
    "siyaset":  ["siyaset", "meclis", "hükümet", "cumhurbaşkanı", "seçim", "parti"],
    "ekonomi":  ["ekonomi", "enflasyon", "faiz", "döviz", "borsa", "bütçe", "TL"],
    "sağlık":   ["sağlık", "hastane", "ilaç", "pandemi", "doktor", "tedavi"],
    "spor":     ["futbol", "basketbol", "olimpiyat", "şampiyona", "transfer"],
    "teknoloji":["yapay zeka", "yazılım", "siber", "uzay", "teknoloji"],
}


# ═══════════════════════════════════════════════════════════════════
# YARDIMCI: Model yükleyici (singleton)
# ═══════════════════════════════════════════════════════════════════

_embed_model = None

def embed_yukle() -> HuggingFaceEmbeddings:
    """
    HuggingFace embedding modelini bir kez yükler, sonra cache'den döner.
    all-MiniLM-L6-v2: ~90MB, hızlı, Türkçe dahil çok dilli.
    normalize_embeddings=True → cosine similarity için optimize.
    """
    global _embed_model
    if _embed_model is None:
        _embed_model = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embed_model


def chroma_ac() -> Chroma:
    """ChromaDB'yi açar veya yoksa oluşturur."""
    Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name="veritas_haberler",
        embedding_function=embed_yukle(),
        persist_directory=CHROMA_PATH,
    )


def llm_ac(temperature: float = 0.1) -> ChatGroq:
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=os.environ.get("GROQ_API_KEY"),
        temperature=temperature,
    )


# ═══════════════════════════════════════════════════════════════════
# KATMAN 3 — ROUTING + QUERY CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════

def konu_tespit_et(metin: str) -> str:
    """
    Routing: Metnin konusunu tespit eder.
    Bu bilgiyi NewsAPI parametrelerini optimize etmek için kullanıyoruz.
    Eşleşme yoksa "genel" döner.
    """
    metin_kucuk = metin.lower()
    for konu, anahtar_kelimeler in KONU_ROUTING.items():
        if any(k in metin_kucuk for k in anahtar_kelimeler):
            return konu
    return "genel"


def newsapi_sorgu_olustur(konu: str, ham_metin: str) -> dict:
    """
    Query Construction: Konuya göre NewsAPI parametrelerini ayarlar.
    
    Routing tablosundan gelen konuya bakarak:
    - Siyaset haberleri için Türkçe kaynakları önceliklendir
    - Ekonomi için finansal kaynakları ekle
    - Genel için geniş arama yap
    """
    # Temel parametreler
    params = {
        "sort_by": "relevancy",
        "page_size": MAX_HABERLER,
    }

    # İlk 20 kelimeden arama sorgusu oluştur
    temel_sorgu = " ".join(ham_metin.split()[:20])

    # Konuya özgü routing
    if konu == "ekonomi":
        params["q"] = f"{temel_sorgu} ekonomi"
        params["sort_by"] = "popularity"   # Ekonomide popüler kaynaklar
    elif konu == "siyaset":
        params["q"] = temel_sorgu
        params["sort_by"] = "publishedAt"  # Siyasette güncellik önemli
    elif konu == "sağlık":
        params["q"] = f"{temel_sorgu} sağlık"
    else:
        params["q"] = temel_sorgu

    return params


# ═══════════════════════════════════════════════════════════════════
# KATMAN 1 — INDEXING
# ═══════════════════════════════════════════════════════════════════

def haberleri_indeksle(ham_metin: str) -> dict:
    """
    Indexing pipeline — Tavily ile:
    1. Konuyu tespit et (routing)
    2. topic="news" + days=30 → güncel haber çek
    3. Fallback: genel arama
    4. ChromaDB'ye kaydet
    """
    try:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return {"hata": "TAVILY_API_KEY bulunamadı.", "eklenen": 0}

        tavily = TavilyClient(api_key=api_key)
        konu   = konu_tespit_et(ham_metin)
        sorgu  = " ".join(ham_metin.split()[:25])

        # Önce haber araması — topic="news", days=30
        try:
            yanit = tavily.search(
                query=sorgu,
                search_depth="basic",   # advanced yerine basic — token tasarrufu
                topic="news",
                days=30,                # son 30 gün
                max_results=8,
            )
            sonuclar = yanit.get("results", [])
        except Exception:
            sonuclar = []

        # Haber bulunamazsa genel arama
        if len(sonuclar) < 3:
            try:
                yanit2 = tavily.search(
                    query=sorgu,
                    search_depth="basic",
                    topic="general",
                    time_range="month",
                    max_results=8,
                )
                sonuclar.extend(yanit2.get("results", []))
            except Exception:
                pass

        if not sonuclar:
            return {"hata": "Bu konuda haber bulunamadı.", "eklenen": 0, "konu": konu}

        # Text Splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " "],
        )

        belgeler   = []
        eklenen_idler = set()

        for sonuc in sonuclar:
            if not sonuc.get("title"):
                continue

            belge_id = hashlib.md5(sonuc["title"].encode()).hexdigest()
            if belge_id in eklenen_idler:
                continue
            eklenen_idler.add(belge_id)

            url = sonuc.get("url", "")
            try:
                from urllib.parse import urlparse
                kaynak_adi = urlparse(url).netloc.replace("www.", "")
            except Exception:
                kaynak_adi = "Bilinmiyor"

            tam_icerik = "\n".join(filter(None, [
                f"Başlık: {sonuc.get('title', '')}",
                f"Kaynak: {kaynak_adi}",
                f"İçerik: {sonuc.get('content', '')[:800]}",
            ]))

            for parca in splitter.split_text(tam_icerik):
                belgeler.append(Document(
                    page_content=parca,
                    metadata={
                        "kaynak":   kaynak_adi,
                        "tarih":    "",
                        "url":      url,
                        "baslik":   sonuc["title"][:120],
                        "konu":     konu,
                        "belge_id": belge_id,
                    }
                ))

        if not belgeler:
            return {"hata": "Geçerli makale bulunamadı.", "eklenen": 0}

        chroma_ac().add_documents(belgeler)

        return {
            "eklenen":       len(belgeler),
            "makale_sayisi": len(eklenen_idler),
            "hata":          None,
            "konu":          konu,
            "kaynaklar":     list({b.metadata["kaynak"] for b in belgeler})[:8],
        }

    except Exception as e:
        return {"hata": str(e), "eklenen": 0}


# ═══════════════════════════════════════════════════════════════════
# KATMAN 2 — QUERY TRANSLATION
# ═══════════════════════════════════════════════════════════════════

def multi_query_uret(metin: str) -> list[str]:
    """
    RAG From Scratch — Notebook 5: Multi-Query Retrieval
    
    Tek sorgu neden yetmez?
    Kullanıcı metni "Merkez Bankası faiz kararı" diyorsa,
    ChromaDB'de "TCMB politika faizi", "enflasyonla mücadele",
    "para politikası" da aynı konuyu anlatan belgeler olabilir.
    Multi-Query bu varyasyonları otomatik üretir.
    """
    prompt = ChatPromptTemplate.from_template("""
Sen bir haber araştırma asistanısın.
Verilen haber metninden {n} farklı arama sorgusu üret.
Her sorgu konuyu farklı kelimeler ve açılardan ele almalı.
Sadece sorguları yaz, her birini yeni satıra koy, numara ekleme.

Haber metni (ilk kısım):
{metin}

{n} farklı arama sorgusu:""")

    zincir = prompt | llm_ac(temperature=0.4) | StrOutputParser()
    raw = zincir.invoke({"metin": metin[:400], "n": MQ_SAYI})
    sorgular = [s.strip() for s in raw.strip().split("\n") if s.strip()]
    return sorgular[:MQ_SAYI]


def hyde_sorgu_uret(metin: str) -> str:
    """
    RAG From Scratch — Notebook 7: HyDE (Hypothetical Document Embedding)
    
    Fikir: Kullanıcı metnini doğrudan arama yapmak yerine,
    "Bu konuda nasıl bir haber yazılmış olabilir?" diye LLM'e sor.
    O varsayımsal belgeyi de vektöre çevir ve ara.
    
    Neden işe yarıyor?
    LLM'in ürettiği metin, gerçek haber dilindeki ifadelere benziyor.
    Bu yüzden ChromaDB'de daha iyi eşleşme buluyor.
    """
    prompt = ChatPromptTemplate.from_template("""
Aşağıdaki haber konusunu ele alan kısa ve tarafsız bir haber özeti yaz (2-3 cümle).
Sanki bağımsız bir haber ajansı bu konuyu aktarıyor gibi yaz.

Konu:
{metin}

Haber özeti:""")

    zincir = prompt | llm_ac(temperature=0.2) | StrOutputParser()
    return zincir.invoke({"metin": metin[:400]}).strip()


# ═══════════════════════════════════════════════════════════════════
# KATMAN 4 — RETRIEVAL + RAG FUSION
# ═══════════════════════════════════════════════════════════════════

def reciprocal_rank_fusion(sonuc_listeleri: list[list], k: int = 60) -> list:
    """
    RAG From Scratch — Notebook 6: RAG Fusion / RRF
    
    Birden fazla sorgunun sonuçlarını birleştirir.
    Formül: score(d) = Σ 1/(k + rank(d,q))
    
    Bir belge birden fazla sorguda çıkıyorsa skoru artar.
    k=60: küçük sıralama farklarını yumuşatır (standart değer).
    """
    skor_tablosu: dict[str, dict] = {}

    for sonuclar in sonuc_listeleri:
        for siralama, belge in enumerate(sonuclar):
            anahtar = belge.page_content[:80]
            if anahtar not in skor_tablosu:
                skor_tablosu[anahtar] = {"belge": belge, "skor": 0.0}
            skor_tablosu[anahtar]["skor"] += 1.0 / (k + siralama + 1)

    sirali = sorted(skor_tablosu.values(), key=lambda x: x["skor"], reverse=True)
    return [item["belge"] for item in sirali[:TOP_K]]


def retrieval_yap(sorgular: list[str], hyde_metin: str) -> list:
    """
    Tüm sorgularla ChromaDB'de arama yapar:
    - Multi-Query sorgular (MQ_SAYI adet)
    - HyDE sorgusu (1 adet)
    RRF ile birleştirir.
    """
    vectorstore = chroma_ac()
    retriever   = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    tum_sonuclar = []

    # Multi-Query retrieval
    for sorgu in sorgular:
        try:
            tum_sonuclar.append(retriever.invoke(sorgu))
        except Exception:
            continue

    # HyDE retrieval
    try:
        tum_sonuclar.append(retriever.invoke(hyde_metin))
    except Exception:
        pass

    return reciprocal_rank_fusion(tum_sonuclar)


# ═══════════════════════════════════════════════════════════════════
# KATMAN 5 — GENERATION (Hallucination Guard dahil)
# ═══════════════════════════════════════════════════════════════════

def rapor_uret(haber_metni: str, belgeler: list, indeks_bilgi: dict) -> dict:
    """
    Groq LLM ile çapraz kaynak doğrulama raporu üretir.
    
    Hallucination Guard:
    Prompt'ta açıkça "sadece verilen kaynaklara dayan" diyoruz.
    LLM kendi eğitim verisinden bilgi eklememeli.
    Bu RAG'ın temel güvenlik katmanı.
    """
    kaynak_metinleri = []
    for i, belge in enumerate(belgeler, 1):
        kaynak_metinleri.append(
            f"[Kaynak {i}] {belge.metadata.get('kaynak','?')} "
            f"({belge.metadata.get('tarih','?')}):\n{belge.page_content}"
        )
    kaynaklar_str = "\n\n".join(kaynak_metinleri)

    prompt = ChatPromptTemplate.from_template("""
Sen bir haber doğrulama uzmanısın.
SADECE aşağıdaki kaynaklarda bulunan bilgileri kullan.
Kendi bilginden hiçbir şey ekleme — bu bir hallucination guard kuralıdır.

ANALİZ EDİLECEK HABER:
{haber}

BULUNAN KAYNAKLAR ({kaynak_sayisi} adet):
{kaynaklar}

Değerlendir:
1. Kaynaklar haberi doğruluyor mu, çürütüyor mu, yoksa farklı bakış açısı mı sunuyor?
2. Kaynaklar arasında çelişki var mı?
3. Haberde kaynaklarda olmayan iddialar var mı? (Sadece kaynaklara göre değerlendir)
4. Kaynak çeşitliliği ve güvenilirliği nasıl?

SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{{
  "karar": "Doğrulandı" | "Kısmen Doğrulandı" | "Çelişkili" | "Doğrulanamadı" | "Çürütüldü",
  "kaynak_uzlasmasi": 0-100,
  "ana_bulgu": "tek cümle en önemli bulgu",
  "destekleyen_kaynaklar": ["kaynak adı 1", "kaynak adı 2"],
  "celen_kaynaklar": ["kaynak adı"],
  "eksik_bilgiler": ["haberde olup kaynaklarda olmayan iddia"],
  "ozet": "2-3 cümle genel değerlendirme",
  "guvenirlilk_etkisi": -20 ile +20 arası tam sayı
}}""")

    zincir = prompt | llm_ac(temperature=0.1) | StrOutputParser()
    raw = zincir.invoke({
        "haber":        haber_metni[:1000],
        "kaynaklar":    kaynaklar_str[:3500],
        "kaynak_sayisi": len(belgeler),
    })

    raw = raw.replace("```json", "").replace("```", "").strip()
    sonuc = json.loads(raw)

    # Kaynak linklerini ekle
    sonuc["kaynak_linkleri"] = [
        {
            "baslik":  b.metadata.get("baslik", "")[:80],
            "kaynak":  b.metadata.get("kaynak", ""),
            "url":     b.metadata.get("url", ""),
            "tarih":   b.metadata.get("tarih", ""),
        }
        for b in belgeler if b.metadata.get("url")
    ]
    sonuc["bulunan_kaynak_sayisi"] = len(belgeler)
    sonuc["indekslenen_haber"]     = indeks_bilgi.get("makale_sayisi", 0)
    sonuc["tespit_edilen_konu"]    = indeks_bilgi.get("konu", "genel")

    return sonuc


# ═══════════════════════════════════════════════════════════════════
# ANA PIPELINE
# ═══════════════════════════════════════════════════════════════════

def capraz_kaynak_dogrula(haber_metni: str) -> dict:
    """
    Tüm katmanları sırasıyla çalıştırır:
    Indexing → Query Translation → Routing → Retrieval → Generation
    """
    try:
        # KATMAN 1: Indexing
        indeks = haberleri_indeksle(haber_metni)
        if indeks["hata"] and indeks["eklenen"] == 0:
            return {"karar": "Kaynak Bulunamadı", "hata": indeks["hata"]}

        # KATMAN 2: Query Translation
        mq_sorgular = multi_query_uret(haber_metni)        # Multi-Query
        hyde_metin  = hyde_sorgu_uret(haber_metni)         # HyDE

        # KATMAN 4: Retrieval + RRF
        en_iyi_belgeler = retrieval_yap(mq_sorgular, hyde_metin)
        if not en_iyi_belgeler:
            return {"karar": "Yetersiz Kaynak", "hata": "Benzer haber bulunamadı."}

        # KATMAN 5: Generation
        sonuc = rapor_uret(haber_metni, en_iyi_belgeler, indeks)

        # Pipeline meta bilgisi — portfolyo için görünür kılıyoruz
        sonuc["kullanilan_sorgular"] = mq_sorgular
        sonuc["hyde_sorgu"]          = hyde_metin[:150] + "..."
        sonuc["indekslenen_kaynaklar"] = indeks.get("kaynaklar", [])

        return sonuc

    except json.JSONDecodeError:
        return {"karar": "Hata", "hata": "Groq yanıtı JSON formatında gelmedi."}
    except Exception as e:
        return {"karar": "Hata", "hata": str(e)}

def rag_destekli_analiz(
    haber_metni: str,
    kaynak_url: str = None,
    soru: str = "Bu haberdeki temel iddialar neler? Güvenilirlik açısından değerlendir.",
) -> dict:
    import time

    koleksiyon = f"veritas_{int(time.time())}"

    vs = index_text(
        text=haber_metni,
        metadata={
            "tip": "kullanici_girisi",
            "url": kaynak_url or "",
        },
        collection_name=koleksiyon,
    )

    if kaynak_url:
        try:
            print(f"Kaynak URL indeksleniyor: {kaynak_url}")
            index_url(
                url=kaynak_url,
                collection_name=koleksiyon
            )
        except Exception as e:
            print(f"URL indeksleme başarısız: {e}")

    chain = build_rag_chain(vs, k=3)

    rag_cevap = chain.invoke(soru)

    return {
        "rag_cevap": rag_cevap,
        "koleksiyon": koleksiyon,
    }