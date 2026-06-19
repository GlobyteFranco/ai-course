from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from src.logs import get_logger

logger = get_logger("langsmith_setup")


def configure_langsmith() -> bool:
    """
    Carga .env y normaliza variables para habilitar tracing en LangSmith.
    Retorna True si queda activado, False en caso contrario.
    """
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env", override=False)

    # Soporta nombres nuevos y legacy.
    if os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_API_KEY"] = os.environ["LANGSMITH_API_KEY"]

    if os.getenv("LANGSMITH_TRACING") and not os.getenv("LANGCHAIN_TRACING_V2"):
        os.environ["LANGCHAIN_TRACING_V2"] = os.environ["LANGSMITH_TRACING"]

    if os.getenv("LANGSMITH_ENDPOINT") and not os.getenv("LANGCHAIN_ENDPOINT"):
        os.environ["LANGCHAIN_ENDPOINT"] = os.environ["LANGSMITH_ENDPOINT"]

    tracing_flag = os.getenv("LANGCHAIN_TRACING_V2", "").strip().lower()
    enabled = tracing_flag in {"1", "true", "yes", "on"}
    has_key = bool(os.getenv("LANGCHAIN_API_KEY"))
    configured = enabled and has_key

    logger.info(
        "LangSmith configured=%s | tracing=%s | has_api_key=%s",
        configured,
        tracing_flag or "unset",
        has_key,
    )
    return configured
