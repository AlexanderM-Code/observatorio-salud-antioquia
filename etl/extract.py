"""Extracción: descarga los registros de Antioquia desde la API de datos.gov.co.

La API (Socrata) entrega como máximo 50.000 filas por solicitud, así que se
pagina con $limit y $offset, ordenando por el identificador interno :id para
que las páginas sean estables entre solicitudes.
"""
import logging
import time

import pandas as pd
import requests

from etl import config

log = logging.getLogger(__name__)

COLUMNAS = [
    "cod_eve", "nombre_evento", "semana", "ano",
    "cod_dpto_o", "cod_mun_o", "departamento_ocurrencia",
    "municipio_ocurrencia", "conteo",
]


def _pedir_pagina(sesion: requests.Session, offset: int, intentos: int = 4) -> list[dict]:
    """Pide una página a la API, con reintentos y espera creciente si falla."""
    params = {
        "$select": ",".join(COLUMNAS),
        "$where": f"cod_dpto_o='{config.CODIGO_DEPARTAMENTO_FUENTE}'",
        "$order": ":id",
        "$limit": config.TAMANO_PAGINA,
        "$offset": offset,
    }
    for intento in range(1, intentos + 1):
        try:
            respuesta = sesion.get(config.API_URL, params=params, timeout=120)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.RequestException as error:
            if intento == intentos:
                raise
            espera = 2 ** intento
            log.warning("Fallo la página %s (%s). Reintento en %s s.", offset, error, espera)
            time.sleep(espera)
    return []


def extraer() -> pd.DataFrame:
    """Descarga todas las páginas y las guarda en data/raw como CSV."""
    sesion = requests.Session()
    if config.APP_TOKEN:
        sesion.headers["X-App-Token"] = config.APP_TOKEN

    paginas, offset = [], 0
    while True:
        registros = _pedir_pagina(sesion, offset)
        if not registros:
            break
        paginas.append(pd.DataFrame.from_records(registros, columns=COLUMNAS))
        log.info("Página con offset %s: %s filas", offset, len(registros))
        if len(registros) < config.TAMANO_PAGINA:
            break
        offset += config.TAMANO_PAGINA

    if not paginas:
        raise RuntimeError("La API no devolvió registros para Antioquia.")

    crudos = pd.concat(paginas, ignore_index=True)
    config.DATOS_CRUDOS.parent.mkdir(parents=True, exist_ok=True)
    crudos.to_csv(config.DATOS_CRUDOS, index=False)
    log.info("Extracción completa: %s filas en %s", len(crudos), config.DATOS_CRUDOS)
    return crudos


def leer_crudos() -> pd.DataFrame:
    """Lee la última descarga guardada, sin volver a llamar a la API."""
    return pd.read_csv(config.DATOS_CRUDOS, dtype=str)
