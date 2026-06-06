"""
╔══════════════════════════════════════════════════════════════════╗
║        VeritasAI × RAG From Scratch — CHUNK MODÜLÜ             ║
║        Part 1: Karakter tabanlı  |  Part 2: Token tabanlı       ║
╚══════════════════════════════════════════════════════════════════╝

Büyük bir metni LLM'e veremezsin — token limiti aşılır ve anlam kaybolur.
Çözüm: metni küçük, anlamlı parçalara (chunk) böl.

Bu modül iki yöntemi de birebir orijinal kodla sunar:
    - chunk_karakter()  → Part 1 yöntemi (hızlı, basit)
    - chunk_token()     → Part 2 yöntemi (LLM uyumlu, hassas)
    - chunk_otomatik()  → VeritasAI için hangisi uygunsa onu seçer
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# ══════════════════════════════════════════════════════════════════
# YÖNTEM 1 — Part 1: Karakter Tabanlı Parçalama
#
# chunk_size=1000  → her parça en fazla 1000 karakter
# chunk_overlap=200 → parçalar arasında 200 karakterlik örtüşme
#
# Neden örtüşme var?
#   "...cumhurbaşkanı açıkladı." / "Açıklamaya göre..." gibi
#   cümle sınırında anlam kopmalarını önler.
# ══════════════════════════════════════════════════════════════════

def chunk_karakter(docs: list, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
    """
    Part 1 yöntemi — karakter sayısına göre böler.

    Ne zaman kullan:
        - Haber metinleri kısa veya orta uzunluktaysa
        - Hız öncelikliyse
        - Token sayısı kritik değilse

    Args:
        docs: Document nesneleri listesi (WebBaseLoader çıktısı gibi)
        chunk_size: Parça başına maksimum karakter sayısı
        chunk_overlap: Parçalar arası örtüşen karakter sayısı

    Returns:
        Bölünmüş Document listesi
    """
    # ── Orijinal Part 1 kodu (değiştirilmedi) ────────────────────
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    splits = text_splitter.split_documents(docs)
    # ─────────────────────────────────────────────────────────────

    print(f"[chunk_karakter] {len(docs)} belge → {len(splits)} parça")
    print(f"  chunk_size={chunk_size} karakter | overlap={chunk_overlap} karakter")

    return splits


# ══════════════════════════════════════════════════════════════════
# YÖNTEM 2 — Part 2: Token Tabanlı Parçalama
#
# chunk_size=300  → her parça en fazla 300 token
# chunk_overlap=50 → parçalar arasında 50 tokenlik örtüşme
#
# Karakter vs Token farkı:
#   "merhaba" = 7 karakter ama 1-2 token
#   Token, LLM'in gerçekte gördüğü birimdir.
#   300 token ≈ 200-250 Türkçe kelime (kabaca)
# ══════════════════════════════════════════════════════════════════

def chunk_token(docs: list, chunk_size: int = 300, chunk_overlap: int = 50) -> list:
    """
    Part 2 yöntemi — token sayısına göre böler (tiktoken encoder kullanır).

    Ne zaman kullan:
        - Groq / LLM context limitine yaklaşıyorsan
        - Embedding modelinin max token sınırı varsa
        - Hassas ve tutarlı boyutlandırma gerekiyorsa

    Args:
        docs: Document nesneleri listesi
        chunk_size: Parça başına maksimum token sayısı
        chunk_overlap: Parçalar arası örtüşen token sayısı

    Returns:
        Bölünmüş Document listesi
    """
    # ── Orijinal Part 2 kodu (değiştirilmedi) ────────────────────
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    splits = text_splitter.split_documents(docs)
    # ─────────────────────────────────────────────────────────────

    print(f"[chunk_token] {len(docs)} belge → {len(splits)} parça")
    print(f"  chunk_size={chunk_size} token | overlap={chunk_overlap} token")

    return splits


# ══════════════════════════════════════════════════════════════════
# OTOMATİK SEÇİCİ — VeritasAI için
#
# Kullanıcı "haber metni" yapıştırır.
# Metin kısaysa karakter yöntemi yeterli.
# Metin uzunsa token yöntemi daha güvenli.
# ══════════════════════════════════════════════════════════════════

def chunk_otomatik(metin: str, kaynak_meta: dict = None) -> list:
    """
    Metnin uzunluğuna bakarak otomatik yöntem seçer.

    Kural:
        < 3000 karakter → chunk_karakter() (Part 1)
        >= 3000 karakter → chunk_token()   (Part 2)

    Args:
        metin: Ham haber metni (string)
        kaynak_meta: {'url': ..., 'kaynak': ...} gibi metadata

    Returns:
        Bölünmüş Document listesi
    """
    # String'i Document nesnesine çevir
    doc = Document(
        page_content=metin,
        metadata=kaynak_meta or {}
    )

    karakter_sayisi = len(metin)

    if karakter_sayisi < 3000:
        print(f"[chunk_otomatik] {karakter_sayisi} karakter → Part 1 (karakter tabanlı) seçildi")
        return chunk_karakter([doc])
    else:
        print(f"[chunk_otomatik] {karakter_sayisi} karakter → Part 2 (token tabanlı) seçildi")
        return chunk_token([doc])


# ══════════════════════════════════════════════════════════════════
# TEST — python chunk_module.py ile çalıştır
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  VeritasAI — Chunk Modülü Testi")
    print("=" * 55)

    # Örnek kısa haber
    kisa_haber = """
    Türkiye Büyük Millet Meclisi'nde bütçe görüşmeleri tamamlandı.
    Maliye Bakanlığı açıklamasına göre 2025 yılı bütçesi kabul edildi.
    Muhalefet partileri bütçeye ret oyu kullandı.
    """ * 3  # 3 kez tekrar → orta uzunluk

    uzun_haber = kisa_haber * 10  # Uzun metin simülasyonu

    print("\n📄 Test 1 — Kısa metin (chunk_otomatik)")
    splits_kisa = chunk_otomatik(kisa_haber, kaynak_meta={"kaynak": "test"})
    print(f"  Sonuç: {len(splits_kisa)} parça\n")

    print("📄 Test 2 — Uzun metin (chunk_otomatik)")
    splits_uzun = chunk_otomatik(uzun_haber)
    print(f"  Sonuç: {len(splits_uzun)} parça\n")

    print("📄 Test 3 — Doğrudan Part 1 (chunk_karakter)")
    doc = Document(page_content=kisa_haber)
    splits_p1 = chunk_karakter([doc], chunk_size=500, chunk_overlap=100)
    print(f"  Sonuç: {len(splits_p1)} parça\n")

    print("📄 Test 4 — Doğrudan Part 2 (chunk_token)")
    splits_p2 = chunk_token([doc], chunk_size=150, chunk_overlap=30)
    print(f"  Sonuç: {len(splits_p2)} parça\n")

    print("=" * 55)
    print("✅ Chunk modülü hazır.")
    print("   rag_overview.py'de kullanmak için:")
    print("   from rag.chunk_module import chunk_otomatik")