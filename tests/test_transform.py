"""Pruebas de la limpieza y del modelo estrella."""
from etl import transform


def test_rellena_codigos_divipola(crudos_sucios):
    limpio = transform.limpiar(crudos_sucios)
    assert set(limpio["cod_dpto"]) == {"05"}
    assert "05001" in set(limpio["cod_mun"])
    assert limpio["cod_mun"].str.len().eq(5).all()


def test_suma_duplicados(crudos_sucios):
    limpio = transform.limpiar(crudos_sucios)
    medellin = limpio[(limpio["cod_mun"] == "05001") & (limpio["cod_eve"] == "210")]
    assert len(medellin) == 1
    assert medellin["conteo"].iloc[0] == 150


def test_corrige_santa_fe_de_antioquia(crudos_sucios):
    limpio = transform.limpiar(crudos_sucios)
    assert limpio.loc[limpio["cod_mun"] == "05042", "municipio"].iloc[0] == "SANTA FE DE ANTIOQUIA"


def test_marca_municipio_desconocido(crudos_sucios):
    limpio = transform.limpiar(crudos_sucios)
    desconocido = limpio[limpio["cod_mun"] == "05000"]
    assert desconocido["municipio_desconocido"].all()
    assert desconocido["municipio"].iloc[0] == "MUNICIPIO DESCONOCIDO"


def test_descarta_filas_invalidas(crudos_sucios):
    limpio = transform.limpiar(crudos_sucios)
    assert limpio["semana"].between(1, 53).all()
    assert (limpio["conteo"] > 0).all()
    # 8 filas: 1 duplicado sumado, 1 conteo no numérico, 1 semana 60, 1 conteo 0.
    assert len(limpio) == 4


def test_normaliza_textos(crudos_sucios):
    limpio = transform.limpiar(crudos_sucios)
    assert limpio.loc[limpio["cod_mun"] == "05045", "municipio"].iloc[0] == "APARTADO"


def test_modelo_estrella_sin_llaves_repetidas(crudos_sinteticos):
    tablas = transform.modelo_estrella(transform.limpiar(crudos_sinteticos))
    hechos = tablas["fact_casos"]
    assert not hechos.duplicated(["cod_evento", "cod_municipio", "ano", "semana"]).any()
    assert set(hechos["cod_municipio"]) <= set(tablas["dim_municipio"]["cod_municipio"])
    assert set(hechos["cod_evento"]) <= set(tablas["dim_evento"]["cod_evento"])
