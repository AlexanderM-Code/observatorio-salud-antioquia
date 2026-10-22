"""Pruebas de la API contra la base cargada con datos sintéticos."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from etl import config, load, transform


@pytest.fixture
def cliente(crudos_sinteticos):
    try:
        with create_engine(config.MYSQL_URL).connect():
            pass
    except OperationalError:
        pytest.skip("MySQL no disponible")
    load.cargar(transform.modelo_estrella(transform.limpiar(crudos_sinteticos)))
    from api.main import app
    return TestClient(app)


def test_salud(cliente):
    assert cliente.get("/salud").json() == {"estado": "ok"}


def test_eventos(cliente):
    eventos = cliente.get("/eventos").json()
    assert {e["cod_evento"] for e in eventos} == {"210", "490", "831"}


def test_serie_anual_y_municipio(cliente):
    total = cliente.get("/eventos/210/anual").json()
    medellin = cliente.get("/eventos/210/anual", params={"cod_municipio": "05001"}).json()
    assert [f["ano"] for f in total] == list(range(2014, 2019))
    assert all(m["casos"] < t["casos"] for m, t in zip(medellin, total))


def test_serie_semanal(cliente):
    semanas = cliente.get("/eventos/210/semanal", params={"ano": 2016}).json()
    assert len(semanas) == 52


def test_top_municipios_excluye_desconocido(cliente):
    top = cliente.get("/eventos/210/top-municipios", params={"limite": 10}).json()
    assert top[0]["cod_municipio"] == "05001"
    assert all(f["cod_municipio"] != "05000" for f in top)


def test_evento_inexistente(cliente):
    assert cliente.get("/eventos/999/anual").status_code == 404
