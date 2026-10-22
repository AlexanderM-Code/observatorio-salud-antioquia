"""Prueba de la exportación de los JSON de la página."""
import json

from etl import config, export_web, transform


def test_exporta_json_validos(crudos_sinteticos, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATOS_WEB", tmp_path)
    export_web.exportar(transform.limpiar(crudos_sinteticos))

    resumen = json.loads((tmp_path / "resumen.json").read_text(encoding="utf-8"))
    assert resumen["anio_inicio"] == 2014 and resumen["anio_fin"] == 2018
    assert resumen["municipios"] == 5  # el desconocido no cuenta

    por_anio = json.loads((tmp_path / "eventos_por_anio.json").read_text(encoding="utf-8"))
    dengue = next(e for e in por_anio["eventos"] if e["codigo"] == "210")
    assert len(dengue["casos"]) == len(por_anio["anios"]) == 5
    assert max(dengue["casos"]) == dengue["casos"][2]  # el pico sintético es 2016

    semanal = json.loads((tmp_path / "semanal.json").read_text(encoding="utf-8"))
    assert len(semanal["210"]["2016"]) == 53

    top = json.loads((tmp_path / "top_municipios.json").read_text(encoding="utf-8"))
    assert top["210"][0]["municipio"] == "Medellin"
    assert all(m["codigo"] != "05000" for m in top["210"])
