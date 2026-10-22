"""Punto de entrada del pipeline.

Uso:
    python -m etl.pipeline                 # descarga, limpia, exporta y carga a MySQL
    python -m etl.pipeline --sin-mysql     # todo menos la carga (lo que corre en GitHub Actions)
    python -m etl.pipeline --sin-descarga  # reutiliza la última descarga en data/raw
"""
import argparse
import logging

from etl import export_web, extract, load, transform


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline del Observatorio de Salud Pública de Antioquia")
    parser.add_argument("--sin-descarga", action="store_true", help="usar data/raw en lugar de la API")
    parser.add_argument("--sin-mysql", action="store_true", help="no cargar en MySQL")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    crudos = extract.leer_crudos() if args.sin_descarga else extract.extraer()
    limpio = transform.limpiar(crudos)
    tablas = transform.modelo_estrella(limpio)
    transform.guardar(tablas)
    export_web.exportar(limpio)

    if not args.sin_mysql:
        load.cargar(tablas)


if __name__ == "__main__":
    main()
