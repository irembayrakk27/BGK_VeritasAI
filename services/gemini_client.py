from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model: str


def load_gemini_config() -> GeminiConfig:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY bulunamadı. Kök dizindeki `.env` dosyasına ekleyin "
            "(örn. GEMINI_API_KEY=...)."
        )

    model = (os.getenv("GEMINI_MODEL") or "gemini-1.5-pro").strip()
    return GeminiConfig(api_key=api_key, model=model)


def generate_text(prompt: str) -> str:
    """
    Tek noktadan Gemini çağrısı.

    Not: SDK seçimi `google-genai` (yeni) veya `google-generativeai` (eski) olabilir.
    Burada önce `google.genai` denenir; yoksa eski SDK ile fallback yapılır.
    """

    cfg = load_gemini_config()

    # 1) Yeni SDK (google-genai)
    try:
        from google import genai  # type: ignore

        client = genai.Client(api_key=cfg.api_key)
        resp = client.models.generate_content(model=cfg.model, contents=prompt)
        return (getattr(resp, "text", None) or "").strip()
    except ModuleNotFoundError:
        pass

    # 2) Eski SDK (google-generativeai)
    import google.generativeai as genai_old  # type: ignore

    genai_old.configure(api_key=cfg.api_key)
    model = genai_old.GenerativeModel(cfg.model)
    resp = model.generate_content(prompt)
    return (getattr(resp, "text", None) or "").strip()
