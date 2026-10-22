"""Prueba de integración: carga en MySQL y ejecuta todas las consultas de análisis.

Se omite si no hay una base de datos disponible (MYSQL_URL).
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from etl import config, load, transform


@pytest.fixture
def motor():
    try:
        motor = create_engine(config.MYSQL_URL)
        with motor.connect():
            pass
    except OperationalError:
        pytest.skip("MySQL no disponible")
    return motor


def test_carga_y_consultas(motor, crudos_sinteticos):
    tablas = transform.modelo_estrella(transform.limpiar(crudos_sinteticos))
    load.cargar(tablas)

    with motor.connect() as conexion:
        total = conexion.execute(text("SELECT SUM(casos) FROM fact_casos")).scalar()
        assert int(total) == int(tablas["fact_casos"]["casos"].sum())

        vista = conexion.execute(text("SELECT COUNT(*) FROM v_casos")).scalar()
        assert vista == len(tablas["fact_casos"])

        # Cada consulta del archivo de análisis debe ejecutarse sin errores y devolver filas.
        lineas = [l for l in (config.SQL_DIR / "analisis.sql").read_text(encoding="utf-8").splitlines()
                  if not l.strip().startswith("--")]
        consultas = [c.strip() for c in "\n".join(lineas).split(";") if c.strip()]
        assert len(consultas) == 7
        for consulta in consultas:
            filas = conexion.execute(text(consulta)).fetchall()
            assert filas, f"La consulta no devolvió filas:\n{consulta[:120]}"

        # El pico sintético de 2016 debe aparecer como semana epidémica.
        epidemicas = conexion.execute(text(consultas[5])).fetchall()
        assert any(fila.ano == 2016 for fila in epidemicas)
