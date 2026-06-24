# WorldCup FastAPI

API para consultar la tabla `world_cup_matches_raw` en PostgreSQL.

## Variables de entorno

```bash
export DB_HOST=localhost
export DB_NAME=WorldCup
export DB_USER=guane
export DB_PASSWORD=tu_password
export DB_PORT=5432
```

## Ejecutar

```bash
uvicorn src.API.main:app --reload
```

## Endpoints

- `GET /`: estado base y enlace a docs.
- `GET /health`: valida conectividad con base de datos.
- `GET /matches?limit=10&offset=0`: lista partidos paginados.
- `GET /matches/year/{year}`: lista partidos por anio.
- `GET /stats/matches-by-year`: cantidad de partidos por anio.
