"""Datos de prueba con la misma forma que la API de SIVIGILA (todo como texto)."""
import random

import pandas as pd
import pytest

MUNICIPIOS = [
    ("5001", "MEDELLIN"), ("5088", "BELLO"), ("5360", "ITAGUI"),
    ("5045", "APARTADO"), ("5042", "ANTIOQUIA"), ("5000", "* ANTIOQUIA. MUNICIPIO DESCONOCIDO"),
]
EVENTOS = [("210", "DENGUE"), ("490", "MALARIA VIVAX"), ("831", "VARICELA INDIVIDUAL")]


def _fila(evento, municipio, ano, semana, conteo):
    return {
        "cod_eve": evento[0], "nombre_evento": evento[1], "semana": str(semana), "ano": str(ano),
        "cod_dpto_o": "5", "cod_mun_o": municipio[0], "departamento_ocurrencia": "ANTIOQUIA",
        "municipio_ocurrencia": municipio[1], "conteo": str(conteo),
    }


@pytest.fixture
def crudos_sucios() -> pd.DataFrame:
    """Pocas filas con los problemas reales de la fuente."""
    filas = [
        _fila(EVENTOS[0], MUNICIPIOS[0], 2016, 27, 120),
        _fila(EVENTOS[0], MUNICIPIOS[0], 2016, 27, 30),             # duplicado: se suma
        _fila(EVENTOS[0], MUNICIPIOS[4], 2016, 27, 5),              # 05042 mal nombrado
        _fila(EVENTOS[0], MUNICIPIOS[5], 2016, 27, 2),              # municipio desconocido
        _fila(EVENTOS[1], ("5045", "  apartado "), 2010, 5, 40),   # espacios y minúsculas
        _fila(EVENTOS[1], MUNICIPIOS[3], 2010, 5, "abc"),           # conteo no numérico
        _fila(EVENTOS[2], MUNICIPIOS[1], 2019, 60, 3),              # semana inválida
        _fila(EVENTOS[2], MUNICIPIOS[1], 2019, 10, 0),              # conteo cero
    ]
    return pd.DataFrame(filas)


@pytest.fixture
def crudos_sinteticos() -> pd.DataFrame:
    """Varios años y semanas para probar la carga y las consultas SQL."""
    azar = random.Random(42)
    filas = []
    for ano in range(2014, 2019):
        for semana in range(1, 53):
            for evento in EVENTOS:
                for municipio in MUNICIPIOS:
                    base = 40 if municipio[0] == "5001" else 6
                    pico = 4 if (evento[0] == "210" and ano == 2016 and 20 <= semana <= 30) else 1
                    filas.append(_fila(evento, municipio, ano, semana, azar.randint(1, base) * pico))
    return pd.DataFrame(filas)
