"""Configuración central del pipeline.

Todo lo que puede cambiar (fuente, rutas, conexión) vive aquí para no
repetir valores en los demás módulos.
"""
import os
from pathlib import Path

# --- Fuente de datos -------------------------------------------------------
# Datos de Vigilancia en Salud Pública de Colombia (SIVIGILA), publicados por
# el Instituto Nacional de Salud en el portal de datos abiertos del Estado.
# https://www.datos.gov.co/d/4hyg-wa9d  (licencia CC BY-SA 4.0)
DATASET_ID = "4hyg-wa9d"
API_URL = f"https://www.datos.gov.co/resource/{DATASET_ID}.json"

# En la fuente, el código de Antioquia viene sin el cero inicial ("5").
CODIGO_DEPARTAMENTO_FUENTE = "5"
CODIGO_DEPARTAMENTO = "05"

# Tamaño de cada página de la API (Socrata permite hasta 50.000 por solicitud).
TAMANO_PAGINA = 50_000

# Token opcional de datos.gov.co: aumenta el límite de solicitudes.
APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN", "")

# --- Rutas -----------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DATOS_CRUDOS = RAIZ / "data" / "raw" / "sivigila_antioquia.csv"
DATOS_PROCESADOS = RAIZ / "data" / "processed"
DATOS_WEB = RAIZ / "docs" / "data"
SQL_DIR = RAIZ / "sql"

# --- Base de datos ---------------------------------------------------------
# Se leen de variables de entorno para no dejar contraseñas en el código.
MYSQL_URL = os.getenv(
    "MYSQL_URL",
    "mysql+pymysql://observatorio:observatorio@localhost:3306/observatorio_salud",
)

# --- Eventos que se destacan en la página pública ---------------------------
# Enfermedades transmisibles con series largas y patrones claros.
EVENTOS_DESTACADOS = {
    "210": "Dengue",
    "490": "Malaria vivax",
    "470": "Malaria falciparum",
    "831": "Varicela",
    "820": "Tuberculosis pulmonar",
    "420": "Leishmaniasis cutánea",
}
