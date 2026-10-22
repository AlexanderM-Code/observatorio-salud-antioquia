-- =====================================================================
-- Preguntas de análisis sobre la vigilancia en salud pública de Antioquia
-- Cada consulta responde una pregunta concreta (MySQL 8).
-- =====================================================================

-- 1. ¿Cuáles son los eventos con más casos notificados en todo el periodo?
SELECT e.nombre_evento, SUM(f.casos) AS casos
FROM fact_casos f
JOIN dim_evento e USING (cod_evento)
GROUP BY e.nombre_evento
ORDER BY casos DESC
LIMIT 10;

-- 2. ¿Cómo cambió el dengue año a año? Variación porcentual frente al año anterior.
WITH anual AS (
    SELECT ano, SUM(casos) AS casos
    FROM fact_casos
    WHERE cod_evento = '210'
    GROUP BY ano
)
SELECT
    ano,
    casos,
    LAG(casos) OVER (ORDER BY ano) AS casos_anio_anterior,
    ROUND(100 * (casos - LAG(casos) OVER (ORDER BY ano)) / LAG(casos) OVER (ORDER BY ano), 1) AS variacion_pct
FROM anual
ORDER BY ano;

-- 3. ¿En qué semana llegó el pico de dengue cada año?
WITH semanal AS (
    SELECT ano, semana, SUM(casos) AS casos
    FROM fact_casos
    WHERE cod_evento = '210'
    GROUP BY ano, semana
),
ranking AS (
    SELECT ano, semana, casos,
           ROW_NUMBER() OVER (PARTITION BY ano ORDER BY casos DESC) AS puesto
    FROM semanal
)
SELECT ano, semana AS semana_pico, casos AS casos_en_el_pico
FROM ranking
WHERE puesto = 1
ORDER BY ano;

-- 4. ¿Qué proporción del dengue de Antioquia ocurre en Medellín?
SELECT
    ROUND(100 * SUM(CASE WHEN cod_municipio = '05001' THEN casos ELSE 0 END) / SUM(casos), 1) AS pct_medellin
FROM fact_casos
WHERE cod_evento = '210';

-- 5. ¿Cuáles son los 10 municipios con más casos de malaria vivax?
SELECT m.municipio, SUM(f.casos) AS casos
FROM fact_casos f
JOIN dim_municipio m USING (cod_municipio)
WHERE f.cod_evento = '490' AND m.desconocido = FALSE
GROUP BY m.municipio
ORDER BY casos DESC
LIMIT 10;

-- 6. Semanas epidémicas: semanas en las que el dengue superó en más de dos
--    desviaciones estándar el promedio de esa misma semana en los años anteriores
--    (una versión simple del "canal endémico" que usan las secretarías de salud).
WITH semanal AS (
    SELECT ano, semana, SUM(casos) AS casos
    FROM fact_casos
    WHERE cod_evento = '210'
    GROUP BY ano, semana
),
historico AS (
    SELECT
        a.ano, a.semana, a.casos,
        AVG(b.casos)        AS promedio_historico,
        STDDEV_SAMP(b.casos) AS desviacion_historica
    FROM semanal a
    JOIN semanal b ON b.semana = a.semana AND b.ano < a.ano
    GROUP BY a.ano, a.semana, a.casos
)
SELECT ano, semana, casos, ROUND(promedio_historico, 1) AS promedio_historico
FROM historico
WHERE desviacion_historica IS NOT NULL
  AND casos > promedio_historico + 2 * desviacion_historica
ORDER BY ano, semana;

-- 7. ¿Qué tan concentrados están los casos? Porcentaje que aportan los 5 municipios principales por evento.
WITH por_municipio AS (
    SELECT cod_evento, cod_municipio, SUM(casos) AS casos,
           ROW_NUMBER() OVER (PARTITION BY cod_evento ORDER BY SUM(casos) DESC) AS puesto
    FROM fact_casos
    GROUP BY cod_evento, cod_municipio
)
SELECT e.nombre_evento,
       ROUND(100 * SUM(CASE WHEN puesto <= 5 THEN casos ELSE 0 END) / SUM(casos), 1) AS pct_top5
FROM por_municipio p
JOIN dim_evento e USING (cod_evento)
GROUP BY e.nombre_evento
HAVING SUM(casos) > 5000
ORDER BY pct_top5 DESC;
