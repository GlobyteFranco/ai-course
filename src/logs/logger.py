from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent
LOG_FILE = LOG_DIR / "worldcup_bot.log"


def get_logger(name: str = "worldcup_bot") -> logging.Logger:
    """
    Retorna un logger configurado para escribir en src/logs/worldcup_bot.log.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def short_text(text: str, limit: int = 180) -> str:
    clean = (text or "").replace("\n", " ").strip()
    if len(clean) <= limit:
        return clean
    return clean[:limit] + "..."
