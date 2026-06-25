from __future__ import annotations

import os
import re
from pathlib import Path

import chromadb
import psycopg2
from fastmcp import FastMCP
from langchain_ollama import ChatOllama, OllamaEmbeddings

mcp = FastMCP("World Cup Hybrid MCP")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_DB_PATH = PROJECT_ROOT / "data" / "vector_db_2"
COLLECTION_NAME = "mundiales_football"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
TEXT2SQL_MODEL = os.getenv("TEXT2SQL_MODEL", "llama3.2:3b")

TEXT2SQL_PROMPT = """
Convierte la pregunta del usuario en UNA consulta SQL valida para PostgreSQL.

Restricciones estrictas:
- Responde solo SQL, sin markdown ni explicaciones.
- Solo SELECT.
- Usa solo esta tabla: world_cup_matches_raw.
- Si aplica, usa LIMIT 10 por defecto.

Columnas utiles:
year, datetime, stage, stadium, city,
hometeamname, hometeamgoals, awayteamgoals, awayteamname,
attendance, referee
""".strip()


def _detect_year(text: str):
    match = re.search(r"(19|20)\d{2}", text or "")
    return int(match.group(0)) if match else None


def _build_sql_fallback(question: str) -> str:
    year = _detect_year(question)
    if year is not None:
        return (
            "SELECT year, datetime, hometeamname, hometeamgoals, awayteamgoals, awayteamname "
            "FROM world_cup_matches_raw "
            f"WHERE year = '{year}' ORDER BY datetime LIMIT 10"
        )
    return (
        "SELECT year, datetime, hometeamname, hometeamgoals, awayteamgoals, awayteamname "
        "FROM world_cup_matches_raw ORDER BY year, datetime LIMIT 10"
    )


def _text2sql(question: str) -> str:
    llm = ChatOllama(model=TEXT2SQL_MODEL, temperature=0)
    raw_sql = llm.invoke(f"{TEXT2SQL_PROMPT}\n\nPregunta: {question}\nSQL:").content.strip()
    sql = raw_sql.replace("```sql", "").replace("```", "").strip()
    low = sql.lower()

    blocked = ["insert", "update", "delete", "drop", "alter", "truncate", "create"]
    if any(token in low for token in blocked):
        return _build_sql_fallback(question)
    if not low.startswith("select") or "world_cup_matches_raw" not in low:
        return _build_sql_fallback(question)
    if "limit" not in low:
        sql = f"{sql.rstrip(';')} LIMIT 10"
    return sql


def _get_sql_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "WorldCup"),
        user=os.getenv("DB_USER", "guane"),
        password=os.getenv("DB_PASSWORD", "tu_password"),
        port=os.getenv("DB_PORT", "5432"),
    )


def _vector_search(question: str, n_results: int = 3):
    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
    collection = client.get_collection(COLLECTION_NAME)
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    query_embedding = embeddings.embed_query(question)
    result = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    return [
        {"rank": i + 1, "text": doc, "metadata": meta or {}}
        for i, (doc, meta) in enumerate(zip(docs, metas))
    ]


@mcp.tool()
def mcp_sql_tool(query: str):
    """Consulta estructurada de partidos/resultados en PostgreSQL usando text2sql."""
    sql_query = _text2sql(query)

    conn = _get_sql_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        return {"sql_query": sql_query, "rows": data}
    except Exception as exc:
        conn.rollback()
        safe_sql = _build_sql_fallback(query)
        try:
            with conn.cursor() as cursor:
                cursor.execute(safe_sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            data = [dict(zip(columns, row)) for row in rows]
            return {"sql_query": safe_sql, "rows": data, "warning": f"Fallback SQL por error: {exc}"}
        except Exception as exc2:
            conn.rollback()
            return {
                "sql_query": safe_sql,
                "rows": [],
                "warning": f"No se pudo ejecutar SQL generado ({exc}) ni fallback ({exc2})",
            }
    finally:
        conn.close()


@mcp.tool()
def mcp_vector_tool(query: str, n_results: int = 3):
    """Busqueda semantica en ChromaDB para contexto/historia del Mundial."""
    return _vector_search(question=query, n_results=n_results)


if __name__ == "__main__":
    mcp.run()