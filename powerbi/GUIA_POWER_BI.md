# Guía: dashboard en Power BI y versión pública en Looker Studio

Tiempo estimado: 30 a 45 minutos. Solo necesitas Power BI Desktop (gratis en la Microsoft Store) y tu cuenta de Google.

## 1. Conseguir los datos limpios

Los archivos ya limpios están en `data/processed/` del repositorio:

| Archivo | Qué contiene |
| :-- | :-- |
| `fact_casos.csv` | Casos por evento, municipio, año y semana (tabla de hechos) |
| `dim_evento.csv` | Código y nombre de cada evento |
| `dim_municipio.csv` | Código DIVIPOLA y nombre de cada municipio |

Descárgalos desde GitHub (botón *Code → Download ZIP*) o, si ya ejecutaste el pipeline con MySQL, conéctate directamente a la base (paso 2B).

## 2A. Cargar los CSV en Power BI

1. Abre Power BI Desktop → **Obtener datos → Texto/CSV**.
2. Carga los tres archivos. En cada uno, revisa que:
   - `cod_evento` y `cod_municipio` sean **Texto** (si Power BI los vuelve número, se pierden los ceros de `05001`).
   - `ano`, `semana` y `casos` sean **Número entero**.
3. Haz clic en **Cargar**.

## 2B. (Alternativa) Conectar a MySQL

**Obtener datos → Base de datos MySQL** → servidor `localhost`, base `observatorio_salud`. Elige las tablas `fact_casos`, `dim_evento` y `dim_municipio`. Si Power BI pide un conector, instala el *MySQL Connector/NET*.

## 3. Relaciones (modelo estrella)

En la vista **Modelo**, verifica que existan estas dos relaciones (de varios a uno):

- `fact_casos[cod_evento]` → `dim_evento[cod_evento]`
- `fact_casos[cod_municipio]` → `dim_municipio[cod_municipio]`

## 4. Medidas DAX

En `fact_casos`, crea estas medidas (**Nueva medida**):

```DAX
Casos = SUM ( fact_casos[casos] )

Casos año anterior =
VAR anio = MAX ( fact_casos[ano] )
RETURN CALCULATE ( [Casos], fact_casos[ano] = anio - 1 )

Variación % =
DIVIDE ( [Casos] - [Casos año anterior], [Casos año anterior] )

% del departamento =
DIVIDE ( [Casos], CALCULATE ( [Casos], ALL ( dim_municipio ) ) )

Semana pico =
VAR tabla = ADDCOLUMNS ( VALUES ( fact_casos[semana] ), "c", [Casos] )
RETURN MAXX ( TOPN ( 1, tabla, [c], DESC ), fact_casos[semana] )
```

## 5. Página del dashboard

Una sola página con este orden:

1. **Segmentadores** arriba: `dim_evento[nombre_evento]` (selección única) y `fact_casos[ano]` (rango).
2. **Tarjetas**: `Casos`, `Variación %` y `Semana pico`.
3. **Gráfico de columnas**: eje X `ano`, valor `Casos`.
4. **Gráfico de líneas**: eje X `semana`, valor `Casos`, leyenda `ano` (filtra a 3 o 4 años para comparar).
5. **Gráfico de barras**: `dim_municipio[municipio]` con `Casos`, Top 10 (filtro de nivel visual) y excluyendo `desconocido = Verdadero`.
6. **Mapa** (opcional): `dim_municipio[municipio]` + "Antioquia, Colombia" como ubicación.

Colores sugeridos para que coincida con tu marca: fondo `#0F2027`, tarjetas `#172E37`, acento `#4FC3F7`.

Guarda el archivo como `powerbi/observatorio_salud_antioquia.pbix` y toma 2 capturas para el README (`docs/img/powerbi-1.png`, `powerbi-2.png`).

## 6. Versión pública en Looker Studio

Power BI necesita cuenta empresarial para publicar en la web; Looker Studio no.

1. Sube `fact_casos.csv`, `dim_evento.csv` y `dim_municipio.csv` a Google Sheets (o usa la API: no hace falta).
2. En [lookerstudio.google.com](https://lookerstudio.google.com) → **Crear → Informe** → conector **Google Sheets**.
3. Agrega las tres hojas y crea una **combinación de datos** (Blend) uniendo por `cod_evento` y `cod_municipio`.
4. Repite los gráficos del paso 5.
5. **Compartir → Gestionar acceso → Cualquier persona con el enlace puede ver**.
6. Pega el enlace en el README (sección *Dashboards*) y en tu portafolio.

## 7. Qué decir en la entrevista

- *"Los datos venían con códigos DIVIPOLA sin ceros y conteos como texto; los limpié en Python antes de cargarlos."*
- *"Modelé un esquema estrella para que Power BI filtrara rápido por evento y municipio."*
- *"El dengue en Antioquia tiene epidemias en 2010 y 2016, y en 2016 el pico fue en la semana 27."*
