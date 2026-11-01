# Observatorio de Salud Pública de Antioquia

Pipeline de datos, API y dashboards sobre los **casos notificados al SIVIGILA en Antioquia entre 2007 y 2022**: dengue, malaria, varicela, tuberculosis, leishmaniasis y decenas de eventos de interés en salud pública.

**[Ver el observatorio en vivo](https://alexanderm-code.github.io/observatorio-salud-antioquia/)** · **[Tablero interactivo en Data Studio](https://datastudio.google.com/reporting/fa318396-d03e-4a63-96a4-4c17ff79d889)**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=flat-square&logo=powerbi&logoColor=black)

---

## Hallazgos

| Pregunta | Respuesta |
| :-- | :-- |
| ¿Cuántos casos hay en el periodo? | **1.185.468** casos notificados en Antioquia, 2007–2022. |
| ¿El dengue es constante? | No: llega en olas. La mayoría de años hay entre 1.000 y 7.000 casos, pero en **2010 (25.804)** y **2016 (27.628)** hubo epidemias. |
| ¿Cuándo llega el pico? | En 2016, en la **semana epidemiológica 27** (inicios de julio), con 905 casos. |
| ¿Dónde se concentra el dengue? | **Medellín** aporta el 51 % de los casos del departamento. |
| ¿Cómo evolucionó la malaria? | La malaria vivax cayó **casi 90 %**: de 36.768 casos en 2010 a 3.748 en 2017. |
| ¿Dónde está la malaria? | En el Bajo Cauca: **El Bagre, Cáceres y Zaragoza** suman el 49 % de los casos de malaria vivax. |
| ¿Qué pasó en la pandemia? | La varicela cayó 69 % en 2020, el año en que cerraron los colegios. |

> Los datos son casos **notificados** al sistema de vigilancia, no la totalidad de casos ocurridos.

## Arquitectura

```
 datos.gov.co (API SIVIGILA)
          │  extract.py: descarga paginada con reintentos
          ▼
   data/raw/*.csv
          │  transform.py: limpieza, validación y modelo estrella
          ▼
 data/processed/*.csv ──────────► Power BI / Looker Studio
          │  load.py                    
          ▼                             
   MySQL (esquema estrella) ──► FastAPI (/docs con Swagger)
          │
          │  export_web.py
          ▼
   docs/data/*.json ──► Página pública en GitHub Pages

 GitHub Actions: pruebas en cada push y actualización mensual de los datos
```

## Calidad de datos: problemas encontrados y cómo se resolvieron

| Problema en la fuente | Solución |
| :-- | :-- |
| Códigos DIVIPOLA sin ceros iniciales (`5`, `5001`) | Relleno a 2 y 5 dígitos (`05`, `05001`) |
| Todos los campos llegan como texto, incluido el conteo | Conversión a enteros y descarte de valores no numéricos |
| Registros de "municipio desconocido" (`05000`) | Se conservan, pero se marcan para excluirlos de rankings y mapas |
| El código `05042` aparece como "ANTIOQUIA" | Se corrige a **Santa Fe de Antioquia** |
| Semanas fuera de 1–53, conteos en cero o filas repetidas | Se descartan o se suman, con registro en el log |

## Estructura

```
etl/            Pipeline: extracción, limpieza, carga y exportación
sql/            schema.sql (modelo estrella), views.sql y analisis.sql (7 preguntas)
api/            API de solo lectura en FastAPI
docs/           Página pública (HTML, CSS y JavaScript, gráficas en SVG propio)
powerbi/        Guía y archivo del dashboard de Power BI
tests/          Pruebas con pytest (limpieza, carga en MySQL y API)
.github/        Pruebas automáticas y actualización mensual de datos
```

## Ejecutarlo

### Con Docker (recomendado)

```bash
cp .env.example .env          # y cambia las contraseñas
docker compose up -d db
docker compose run --rm etl   # descarga, limpia y carga ~300.000 registros
docker compose up -d api      # API en http://localhost:8000/docs
```

### Sin Docker

```bash
python -m venv .venv && source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m etl.pipeline --sin-mysql     # solo descarga, limpia y exporta
python -m etl.pipeline                 # también carga en MySQL (usa MYSQL_URL)
uvicorn api.main:app --reload
pytest -v
```

## Consultas SQL de análisis

`sql/analisis.sql` responde 7 preguntas con CTEs y funciones de ventana (`LAG`, `ROW_NUMBER`, `STDDEV_SAMP`), entre ellas una versión simple del **canal endémico**: semanas en que el dengue superó en más de dos desviaciones estándar el promedio histórico de esa misma semana.

## API

| Endpoint | Descripción |
| :-- | :-- |
| `GET /eventos` | Eventos con su total de casos |
| `GET /municipios` | Municipios de Antioquia |
| `GET /eventos/{codigo}/anual?cod_municipio=05001` | Serie anual del evento, del departamento o de un municipio |
| `GET /eventos/{codigo}/semanal?ano=2016` | Curva semanal de un año |
| `GET /eventos/{codigo}/top-municipios?limite=10` | Municipios con más casos |

## Dashboards

- **Power BI:** ver `powerbi/` (guía paso a paso y medidas DAX).
- **Data Studio (antes Looker Studio):** [tablero público](https://datastudio.google.com/reporting/fa318396-d03e-4a63-96a4-4c17ff79d889) con filtros por evento y año, casos por año, curva semanal y los 10 municipios con más casos. Usa `powerbi/looker_casos_antioquia.csv`, un archivo único con los nombres ya unidos.

## Fuente y licencia

Datos: [Datos de Vigilancia en Salud Pública de Colombia](https://www.datos.gov.co/d/4hyg-wa9d), Instituto Nacional de Salud, licencia CC BY-SA 4.0.

## Autor

**Alexander Mejía Ospina**, estudiante de Ingeniería de Software, Medellín.
[Portafolio](https://alexanderm-code.github.io/) · [LinkedIn](https://www.linkedin.com/in/alexander-mejia-ospina) · [GitHub](https://github.com/AlexanderM-Code)
