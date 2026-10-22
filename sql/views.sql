-- Vistas que simplifican el análisis y la conexión desde Power BI.

-- Hechos con los nombres ya unidos: lista para graficar.
CREATE VIEW v_casos AS
SELECT
    e.cod_evento,
    e.nombre_evento,
    m.cod_municipio,
    m.municipio,
    m.desconocido,
    f.ano,
    f.semana,
    f.casos
FROM fact_casos f
JOIN dim_evento    e ON e.cod_evento    = f.cod_evento
JOIN dim_municipio m ON m.cod_municipio = f.cod_municipio;

-- Totales anuales por evento y municipio.
CREATE VIEW v_casos_anuales AS
SELECT
    f.cod_evento,
    f.cod_municipio,
    f.ano,
    SUM(f.casos) AS casos
FROM fact_casos f
GROUP BY f.cod_evento, f.cod_municipio, f.ano;
