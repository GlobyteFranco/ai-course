from fastmcp import FastMCP
import requests
import re

mcp = FastMCP("World Cup")

@mcp.tool()
def get_matches(query: str):
    match = re.search(r"(19|20)\d{2}", query or "")
    if not match:
        return {
            "error": "No encontre un anio en la consulta. Ejemplo: 'partidos de 1930'."
        }

    year = int(match.group(0))
    response = requests.get(
        f"http://localhost:8000/matches/year/{year}",
        timeout=15,
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    mcp.run()