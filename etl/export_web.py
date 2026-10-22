"""Exportación: genera los JSON pequeños que lee la página pública.

La página no consulta la base de datos: lee estos archivos estáticos, así se
puede publicar gratis en GitHub Pages y carga rápido en cualquier celular.
"""
import json
import logging
from datetime import datetime, timezone

import pandas as pd

from etl import config

log = logging.getLogger(__name__)


def _escribir(nombre: str, contenido) -> None:
    config.DATOS_WEB.mkdir(parents=True, exist_ok=True)
    ruta = config.DATOS_WEB / f"{nombre}.json"
    ruta.write_text(json.dumps(contenido, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("Exportado %s", ruta.name)


def exportar(limpio: pd.DataFrame) -> None:
    anios = sorted(limpio["ano"].unique().tolist())

    # 1. Resumen general.
    _escribir("resumen", {
        "actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "fuente": "SIVIGILA, Instituto Nacional de Salud (datos.gov.co, 4hyg-wa9d)",
        "anio_inicio": int(anios[0]),
        "anio_fin": int(anios[-1]),
        "casos": int(limpio["conteo"].sum()),
        "registros": int(len(limpio)),
        "eventos": int(limpio["cod_eve"].nunique()),
        "municipios": int(limpio.loc[~limpio["municipio_desconocido"], "cod_mun"].nunique()),
    })

    # 2. Casos por año de cada evento destacado.
    destacados = limpio[limpio["cod_eve"].isin(config.EVENTOS_DESTACADOS)]
    por_anio = destacados.groupby(["cod_eve", "ano"])["conteo"].sum()
    _escribir("eventos_por_anio", {
        "anios": [int(a) for a in anios],
        "eventos": [
            {
                "codigo": codigo,
                "nombre": nombre,
                "casos": [int(por_anio.get((codigo, a), 0)) for a in anios],
            }
            for codigo, nombre in config.EVENTOS_DESTACADOS.items()
        ],
    })

    # 3. Curva semanal de cada evento destacado, año por año.
    semanal = destacados.groupby(["cod_eve", "ano", "semana"])["conteo"].sum()
    _escribir("semanal", {
        codigo: {
            str(a): [int(semanal.get((codigo, a, s), 0)) for s in range(1, 54)]
            for a in anios
        }
        for codigo in config.EVENTOS_DESTACADOS
    })

    # 4. Municipios con más casos por evento destacado (sin "desconocido").
    conocidos = destacados[~destacados["municipio_desconocido"]]
    top = {}
    for codigo in config.EVENTOS_DESTACADOS:
        tabla = (
            conocidos[conocidos["cod_eve"] == codigo]
            .groupby(["cod_mun", "municipio"], as_index=False)["conteo"].sum()
            .sort_values("conteo", ascending=False)
            .head(10)
        )
        top[codigo] = [
            {"codigo": r.cod_mun, "municipio": r.municipio.title(), "casos": int(r.conteo)}
            for r in tabla.itertuples()
        ]
    _escribir("top_municipios", top)
