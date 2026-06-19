from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_csv_path() -> Path:
    return _project_root() / "data" / "table" / "WorldCupMatches.csv"


@lru_cache(maxsize=1)
def load_worldcup_matches(csv_path: str | None = None) -> pd.DataFrame:
    """
    Carga y normaliza la tabla de partidos del mundial.
    """
    path = Path(csv_path) if csv_path else _default_csv_path()
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de partidos: {path}")

    df = pd.read_csv(path).copy()
    df["Attendance"] = pd.to_numeric(df["Attendance"], errors="coerce")
    df["HomeTeamGoals"] = pd.to_numeric(df["HomeTeamGoals"], errors="coerce").fillna(0)
    df["AwayTeamGoals"] = pd.to_numeric(df["AwayTeamGoals"], errors="coerce").fillna(0)
    df["TotalGoals"] = df["HomeTeamGoals"] + df["AwayTeamGoals"]
    return df


def matches_by_year(year: int, csv_path: str | None = None) -> str:
    """
    Devuelve un resumen de partidos y goles para un anio.
    """
    df = load_worldcup_matches(csv_path)
    data = df[df["Year"] == year]
    if data.empty:
        return f"No hay partidos para el anio {year}."

    goals = int(data["TotalGoals"].sum())
    return f"Anio {year}: {len(data)} partidos, {goals} goles totales."


def top_attendance(n: int = 5, csv_path: str | None = None) -> str:
    """
    Lista los partidos con mayor asistencia.
    """
    if n <= 0:
        return "El valor de n debe ser mayor que 0."

    df = load_worldcup_matches(csv_path)
    top = (
        df.dropna(subset=["Attendance"])
        .sort_values("Attendance", ascending=False)
        .head(n)
    )
    if top.empty:
        return "No hay datos de asistencia disponibles."

    lines: list[str] = []
    for _, row in top.iterrows():
        lines.append(
            f"{int(row['Year'])}: "
            f"{row['HomeTeamName']} {int(row['HomeTeamGoals'])}-{int(row['AwayTeamGoals'])} {row['AwayTeamName']} "
            f"| Attendance={int(row['Attendance'])}"
        )
    return "\n".join(lines)


def avg_goals_by_stage(stage_keyword: str, csv_path: str | None = None) -> str:
    """
    Promedio de goles para etapas cuyo nombre contiene stage_keyword.
    """
    keyword = (stage_keyword or "").strip()
    if not keyword:
        return "Debes enviar una palabra clave para filtrar por etapa."

    df = load_worldcup_matches(csv_path)
    data = df[df["Stage"].str.contains(keyword, case=False, na=False)]
    if data.empty:
        return f"No encontre etapas con '{keyword}'."

    return f"Promedio de goles en '{keyword}': {data['TotalGoals'].mean():.2f}"


def get_worldcup_tools():
    """
    Retorna versiones decoradas como tools de LangChain.

    Si LangChain no esta instalado, retorna funciones Python normales.
    """
    try:
        from langchain_core.tools import tool
    except Exception:
        return [matches_by_year, top_attendance, avg_goals_by_stage]

    @tool
    def matches_by_year_tool(year: int) -> str:
        """Devuelve resumen de partidos para un anio del Mundial."""
        return matches_by_year(year)

    @tool
    def top_attendance_tool(n: int = 5) -> str:
        """Lista los partidos con mayor asistencia."""
        return top_attendance(n)

    @tool
    def avg_goals_by_stage_tool(stage_keyword: str) -> str:
        """Promedio de goles para etapas que contienen una palabra clave."""
        return avg_goals_by_stage(stage_keyword)

    return [matches_by_year_tool, top_attendance_tool, avg_goals_by_stage_tool]
