"""Carga: crea el esquema en MySQL e inserta las tablas del modelo estrella."""
import logging

import pandas as pd
from sqlalchemy import create_engine, text

from etl import config

log = logging.getLogger(__name__)

ORDEN_CARGA = ["dim_evento", "dim_municipio", "fact_casos"]


def _ejecutar_script(conexion, ruta) -> None:
    """Ejecuta un archivo .sql sentencia por sentencia (separadas por ';')."""
    lineas = [l for l in ruta.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("--")]
    sentencias = [s.strip() for s in "\n".join(lineas).split(";") if s.strip()]
    for sentencia in sentencias:
        conexion.execute(text(sentencia))


def cargar(tablas: dict[str, pd.DataFrame], url: str | None = None) -> None:
    """Recrea las tablas y carga los datos dentro de una sola transacción."""
    motor = create_engine(url or config.MYSQL_URL, pool_pre_ping=True)
    with motor.begin() as conexion:
        _ejecutar_script(conexion, config.SQL_DIR / "schema.sql")
        for nombre in ORDEN_CARGA:
            tablas[nombre].to_sql(nombre, conexion, if_exists="append", index=False,
                                  chunksize=10_000, method="multi")
            log.info("Cargadas %s filas en %s.", len(tablas[nombre]), nombre)
        _ejecutar_script(conexion, config.SQL_DIR / "views.sql")
    log.info("Carga en MySQL completa.")
