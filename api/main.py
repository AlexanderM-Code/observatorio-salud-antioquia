"""API de solo lectura del Observatorio de Salud Pública de Antioquia.

Documentación interactiva (Swagger) en /docs al ejecutarla:
    uvicorn api.main:app --reload
"""
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from etl import config

motor = create_engine(config.MYSQL_URL, pool_pre_ping=True)

app = FastAPI(
    title="Observatorio de Salud Pública de Antioquia",
    description="Casos notificados al SIVIGILA en Antioquia por evento, municipio, año y semana epidemiológica.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])


def conexion():
    with motor.connect() as con:
        yield con


def _filas(con: Connection, sql: str, **params) -> list[dict]:
    return [dict(fila._mapping) for fila in con.execute(text(sql), params)]


@app.get("/salud", tags=["Estado"])
def salud(con: Connection = Depends(conexion)):
    """Comprueba que la API y la base de datos responden."""
    con.execute(text("SELECT 1"))
    return {"estado": "ok"}


@app.get("/eventos", tags=["Catálogos"])
def eventos(con: Connection = Depends(conexion)):
    """Eventos de salud pública con su total de casos."""
    return _filas(con, """
        SELECT e.cod_evento, e.nombre_evento, COALESCE(SUM(f.casos), 0) AS casos
        FROM dim_evento e LEFT JOIN fact_casos f USING (cod_evento)
        GROUP BY e.cod_evento, e.nombre_evento
        ORDER BY casos DESC
    """)


@app.get("/municipios", tags=["Catálogos"])
def municipios(con: Connection = Depends(conexion)):
    """Municipios de Antioquia (sin el registro de municipio desconocido)."""
    return _filas(con, """
        SELECT cod_municipio, municipio FROM dim_municipio
        WHERE desconocido = FALSE ORDER BY municipio
    """)


@app.get("/eventos/{cod_evento}/anual", tags=["Series"])
def serie_anual(
    cod_evento: str,
    cod_municipio: str | None = Query(None, min_length=5, max_length=5, description="Código DIVIPOLA, p. ej. 05001"),
    con: Connection = Depends(conexion),
):
    """Casos por año de un evento, para todo Antioquia o para un municipio."""
    filas = _filas(con, """
        SELECT ano, SUM(casos) AS casos
        FROM fact_casos
        WHERE cod_evento = :evento AND (:municipio IS NULL OR cod_municipio = :municipio)
        GROUP BY ano ORDER BY ano
    """, evento=cod_evento, municipio=cod_municipio)
    if not filas:
        raise HTTPException(404, "No hay casos para ese evento o municipio.")
    return filas


@app.get("/eventos/{cod_evento}/semanal", tags=["Series"])
def serie_semanal(cod_evento: str, ano: int = Query(..., ge=2007, le=2100), con: Connection = Depends(conexion)):
    """Curva semanal de un evento en un año (para ver cuándo llega el pico)."""
    filas = _filas(con, """
        SELECT semana, SUM(casos) AS casos
        FROM fact_casos
        WHERE cod_evento = :evento AND ano = :ano
        GROUP BY semana ORDER BY semana
    """, evento=cod_evento, ano=ano)
    if not filas:
        raise HTTPException(404, "No hay casos para ese evento en ese año.")
    return filas


@app.get("/eventos/{cod_evento}/top-municipios", tags=["Rankings"])
def top_municipios(
    cod_evento: str,
    limite: int = Query(10, ge=1, le=50),
    ano: int | None = Query(None, ge=2007, le=2100),
    con: Connection = Depends(conexion),
):
    """Municipios con más casos de un evento, en todo el periodo o en un año."""
    return _filas(con, """
        SELECT m.cod_municipio, m.municipio, SUM(f.casos) AS casos
        FROM fact_casos f JOIN dim_municipio m USING (cod_municipio)
        WHERE f.cod_evento = :evento AND m.desconocido = FALSE
          AND (:ano IS NULL OR f.ano = :ano)
        GROUP BY m.cod_municipio, m.municipio
        ORDER BY casos DESC
        LIMIT :limite
    """, evento=cod_evento, ano=ano, limite=limite)
