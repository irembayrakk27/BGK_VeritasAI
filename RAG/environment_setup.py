"""
╔══════════════════════════════════════════════════════════════════╗
║         VeritasAI × RAG From Scratch — ENVIRONMENT SETUP        ║
║         Groq API (Llama-3.3-70b) + ChromaDB + LangSmith         ║
╚══════════════════════════════════════════════════════════════════╝

Bu dosya projenin kurulum ortamını hazırlar.
OpenAI KULLANILMAZ — her şey Groq + HuggingFace üzerinden çalışır.
"""

# ─────────────────────────────────────────────────────────────────
# (1) PAKET KURULUMU
# ─────────────────────────────────────────────────────────────────
# Terminal'de bir kez çalıştır, sonra yorum satırına al:

# pip install langchain langchain-community langchain-groq
# pip install chromadb sentence-transformers
# pip install langchain-huggingface
# pip install tiktoken beautifulsoup4 tavily-python
# pip install python-dotenv streamlit

# NOT: langchain-openai KURMA — projede kullanılmıyor.


# ─────────────────────────────────────────────────────────────────
# (2) LANGSMITH (opsiyonel ama şiddetle tavsiye edilir)
#     Chain'lerin her adımını görsel olarak takip etmeni sağlar.
#     https://smith.langchain.com → "New Project" → API key al
# ─────────────────────────────────────────────────────────────────

import os

def setup_langsmith(api_key: str, project_name: str = "veritasai-rag"):
    """
    LangSmith tracing'i aktif eder.
    
    Kullanım:
        setup_langsmith(api_key="ls__xxx...")
    
    Devre dışı bırakmak için:
        os.environ['LANGCHAIN_TRACING_V2'] = 'false'
    """
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = project_name
    print(f"✅ LangSmith aktif → proje: {project_name}")


# ─────────────────────────────────────────────────────────────────
# (3) API KEY'LER
#     .env dosyana yaz, asla koda gömme!
# ─────────────────────────────────────────────────────────────────

from dotenv import load_dotenv
from pathlib import Path

def load_veritas_env():
    """
    Proje kök dizinindeki .env dosyasını yükler.
    
    .env içeriği şöyle olmalı:
        GROQ_API_KEY=gsk_xxx...
        TAVILY_API_KEY=tvly-xxx...
        LANGCHAIN_API_KEY=ls__xxx...   (opsiyonel)
    """
    env_path = Path(__file__).resolve().parent / ".env"
    loaded = load_dotenv(env_path)

    if not loaded:
        print("⚠️  .env dosyası bulunamadı! Lütfen proje kökünde .env oluştur.")
        return False

    # Kritik key'leri kontrol et
    missing = []
    for key in ["GROQ_API_KEY", "TAVILY_API_KEY"]:
        if not os.environ.get(key):
            missing.append(key)

    if missing:
        print(f"❌ Eksik API key'ler: {missing}")
        return False

    print("✅ .env yüklendi — GROQ_API_KEY ve TAVILY_API_KEY hazır")
    return True


# ─────────────────────────────────────────────────────────────────
# (4) TEMEL CLIENT'LARI BAŞLAT
#     Projenin her yerinde import edebileceğin hazır nesneler.
# ─────────────────────────────────────────────────────────────────

def get_llm(model: str = "llama-3.3-70b-versatile", temperature: float = 0):
    """
    VeritasAI'nin kullandığı LLM'i döndürür.
    Orijinal projende ne varsa burada da aynı model.
    
    RAG From Scratch'te gpt-3.5-turbo kullanan yerler
    artık bu fonksiyon üzerinden Groq'a yönlenir.
    """
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=model,
        temperature=temperature,
        groq_api_key=os.environ.get("GROQ_API_KEY"),
    )


def get_embeddings(model: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    OpenAIEmbeddings yerine HuggingFace embedding modeli.
    
    Seçenekler (Türkçe için öneriler):
        - "sentence-transformers/all-MiniLM-L6-v2"   → hızlı, genel
        - "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" → çok dilli
        - "BAAI/bge-m3"  → en güçlü ama ağır
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=model)


def get_tavily():
    """Tavily arama client'ı — kaynak doğrulama için."""
    from tavily import TavilyClient
    return TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


# ─────────────────────────────────────────────────────────────────
# (5) DOĞRULAMA — her şey çalışıyor mu?
# ─────────────────────────────────────────────────────────────────

def verify_setup():
    """Kurulumun doğru çalıştığını test eder."""
    print("\n🔍 VeritasAI RAG Kurulum Doğrulaması")
    print("=" * 45)

    # Env yükle
    if not load_veritas_env():
        return

    # LLM testi
    try:
        llm = get_llm()
        resp = llm.invoke("Merhaba, tek kelimeyle cevap ver: aktif misin?")
        print(f"✅ Groq LLM aktif → {resp.content.strip()[:50]}")
    except Exception as e:
        print(f"❌ Groq LLM hatası: {e}")

    # Embedding testi
    try:
        emb = get_embeddings()
        vec = emb.embed_query("test")
        print(f"✅ Embeddings aktif → boyut: {len(vec)}")
    except Exception as e:
        print(f"❌ Embedding hatası: {e}")

    # ChromaDB testi
    try:
        import chromadb
        client = chromadb.Client()
        print(f"✅ ChromaDB aktif → versiyon: {chromadb.__version__}")
    except Exception as e:
        print(f"❌ ChromaDB hatası: {e}")

    print("=" * 45)
    print("🚀 Kurulum tamamlandı! rag_overview.py'yi çalıştırabilirsin.\n")


# ─────────────────────────────────────────────────────────────────
# ÇALIŞTIRMA
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    verify_setup()