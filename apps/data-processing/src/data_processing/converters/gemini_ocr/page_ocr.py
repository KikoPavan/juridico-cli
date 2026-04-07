"""
Single-page OCR via Gemini.
Converts a page image (JPEG/PNG path) to transcribed text.
"""

import os
from pathlib import Path

from markitdown import MarkItDown

from .adapter import GeminiClientAdapter

DEFAULT_MODEL = "gemini-2.5-flash"

_PROMPT = (
    "Transcreva EXATAMENTE todo o texto desta página de documento jurídico. "
    "Comece IMEDIATAMENTE com o texto, sem escrever 'Description' ou 'Aqui está.' "
    "Preserve negritos com **texto**, itálicos com *texto*. "
    "Se houver texto invertido ou ilegível, escreva [TEXTO ILEGÍVEL]. "
    "Mantenha números de processo, CPFs, RGs e datas exatamente como aparecem."
)


def ocr_page(image_path: Path, *, api_key: str | None = None, model: str = DEFAULT_MODEL) -> str:
    """
    Transcribe a single page image using Gemini.

    Args:
        image_path: Path to the JPEG/PNG image of the page.
        api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.
        model: Gemini model name.

    Returns:
        Transcribed text for the page.

    Raises:
        RuntimeError: If GEMINI_API_KEY is not set and api_key is not provided.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY não encontrada. "
            "Defina a variável de ambiente ou passe api_key= explicitamente."
        )

    adapter = GeminiClientAdapter(api_key=key, model_name=model)
    md = MarkItDown(llm_client=adapter, llm_model=model, llm_prompt=_PROMPT)
    result = md.convert(str(image_path))
    return (getattr(result, "text_content", None) or str(result)).strip()
