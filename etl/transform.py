"""Transformación: limpia los datos crudos y los organiza en un modelo estrella.

Problemas de calidad encontrados en la fuente y cómo se resuelven aquí:

1. Los códigos DIVIPOLA vienen sin ceros iniciales ("5" y "5001" en lugar de
   "05" y "05001"). Se rellenan con ceros para respetar el estándar del DANE.
2. Todos los campos llegan como texto, incluido el conteo de casos.
   Se convierten a enteros y se descartan filas con valores no numéricos.
3. Existen registros de "municipio desconocido" (código 05000). Se conservan
   para no perder casos, pero se marcan para poder excluirlos de los mapas.
4. El código 05042 aparece con el nombre "ANTIOQUIA", que en realidad es el
   municipio de Santa Fe de Antioquia. Se corrige el nombre.
5. Puede haber filas repetidas para la misma combinación evento, municipio,
   año y semana. Se agregan sumando el conteo.
"""
import logging

import pandas as pd

from etl import config

log = logging.getLogger(__name__)

CORRECCIONES_MUNICIPIO = {
    "05042": "SANTA FE DE ANTIOQUIA",
}


def limpiar(crudos: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una tabla limpia con una fila por evento, municipio, año y semana."""
    df = crudos.copy()
    filas_iniciales = len(df)

    # Textos sin espacios sobrantes y en mayúscula sostenida.
    for columna in ["nombre_evento", "municipio_ocurrencia", "departamento_ocurrencia"]:
        df[columna] = df[columna].astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True)

    # Tipos numéricos; lo que no se pueda convertir queda como NaN y se descarta.
    for columna in ["ano", "semana", "conteo"]:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    invalidas = df[["ano", "semana", "conteo"]].isna().any(axis=1)
    if invalidas.any():
        log.warning("Se descartan %s filas con año, semana o conteo no numérico.", int(invalidas.sum()))
    df = df[~invalidas]
    df[["ano", "semana", "conteo"]] = df[["ano", "semana", "conteo"]].astype(int)

    # Semanas epidemiológicas válidas (1 a 53) y conteos positivos.
    fuera_de_rango = ~df["semana"].between(1, 53) | (df["conteo"] <= 0)
    if fuera_de_rango.any():
        log.warning("Se descartan %s filas con semana fuera de 1-53 o conteo <= 0.", int(fuera_de_rango.sum()))
    df = df[~fuera_de_rango]

    # Códigos DIVIPOLA con ceros iniciales.
    df["cod_eve"] = df["cod_eve"].astype(str).str.strip()
    df["cod_dpto"] = df["cod_dpto_o"].astype(str).str.strip().str.zfill(2)
    df["cod_mun"] = df["cod_mun_o"].astype(str).str.strip().str.zfill(5)

    # Un solo nombre por código: si la fuente escribe un municipio de varias
    # formas, se usa la más frecuente para ese código.
    nombre_por_codigo = (
        df.groupby("cod_mun")["municipio_ocurrencia"]
        .agg(lambda nombres: nombres.value_counts().idxmax())
    )
    df["municipio"] = df["cod_mun"].map(nombre_por_codigo)
    df["nombre_evento"] = df["cod_eve"].map(
        df.groupby("cod_eve")["nombre_evento"].agg(lambda nombres: nombres.value_counts().idxmax())
    )

    # Nombres de municipio corregidos y marca de municipio desconocido.
    for codigo, nombre in CORRECCIONES_MUNICIPIO.items():
        df.loc[df["cod_mun"] == codigo, "municipio"] = nombre
    df["municipio_desconocido"] = df["cod_mun"].str.endswith("000") | df["municipio"].str.startswith("*")
    df.loc[df["municipio_desconocido"], "municipio"] = "MUNICIPIO DESCONOCIDO"

    # Una sola fila por combinación (suma de duplicados).
    limpio = (
        df.groupby(
            ["cod_eve", "nombre_evento", "cod_dpto", "cod_mun", "municipio",
             "municipio_desconocido", "ano", "semana"],
            as_index=False,
        )["conteo"].sum()
    )

    log.info("Limpieza: %s filas crudas -> %s filas limpias.", filas_iniciales, len(limpio))
    return limpio


def modelo_estrella(limpio: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Separa la tabla limpia en dimensiones y una tabla de hechos."""
    dim_evento = (
        limpio.groupby("cod_eve", as_index=False)["nombre_evento"].first()
        .rename(columns={"cod_eve": "cod_evento"})
        .sort_values("cod_evento")
    )
    dim_municipio = (
        limpio.groupby("cod_mun", as_index=False)
        .agg(municipio=("municipio", "first"), cod_dpto=("cod_dpto", "first"),
             desconocido=("municipio_desconocido", "first"))
        .rename(columns={"cod_mun": "cod_municipio", "cod_dpto": "cod_departamento"})
        .sort_values("cod_municipio")
    )
    hechos = (
        limpio[["cod_eve", "cod_mun", "ano", "semana", "conteo"]]
        .rename(columns={"cod_eve": "cod_evento", "cod_mun": "cod_municipio", "conteo": "casos"})
        .sort_values(["cod_evento", "cod_municipio", "ano", "semana"])
    )
    return {"dim_evento": dim_evento, "dim_municipio": dim_municipio, "fact_casos": hechos}


def guardar(tablas: dict[str, pd.DataFrame]) -> None:
    """Guarda cada tabla como CSV en data/processed (insumo para MySQL y Power BI)."""
    config.DATOS_PROCESADOS.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in tablas.items():
        ruta = config.DATOS_PROCESADOS / f"{nombre}.csv"
        tabla.to_csv(ruta, index=False)
        log.info("Guardado %s (%s filas).", ruta.name, len(tabla))
