from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg2
from psycopg2.extensions import connection as PgConnection

from src.API.config import get_database_settings


@contextmanager
def get_connection() -> Iterator[PgConnection]:
    """Abre y cierra una conexion PostgreSQL por uso."""
    settings = get_database_settings()
    conn = psycopg2.connect(
        host=settings.host,
        database=settings.database,
        user=settings.user,
        password=settings.password,
        port=settings.port,
    )
    try:
        yield conn
    finally:
        conn.close()
