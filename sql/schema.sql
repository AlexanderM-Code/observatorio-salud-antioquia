-- =====================================================================
-- Observatorio de Salud Pública de Antioquia — modelo estrella (MySQL 8)
-- Una tabla de hechos (casos por semana) y dos dimensiones.
-- =====================================================================

DROP VIEW IF EXISTS v_casos;
DROP VIEW IF EXISTS v_casos_anuales;
DROP TABLE IF EXISTS fact_casos;
DROP TABLE IF EXISTS dim_municipio;
DROP TABLE IF EXISTS dim_evento;

-- Eventos de interés en salud pública (dengue, malaria, varicela...).
CREATE TABLE dim_evento (
    cod_evento     VARCHAR(5)   NOT NULL,
    nombre_evento  VARCHAR(160) NOT NULL,
    PRIMARY KEY (cod_evento)
);

-- Municipios de Antioquia con código DIVIPOLA de 5 dígitos.
CREATE TABLE dim_municipio (
    cod_municipio    CHAR(5)      NOT NULL,
    municipio        VARCHAR(80)  NOT NULL,
    cod_departamento CHAR(2)      NOT NULL,
    desconocido      BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (cod_municipio)
);

-- Casos notificados por evento, municipio, año y semana epidemiológica.
CREATE TABLE fact_casos (
    cod_evento     VARCHAR(5)        NOT NULL,
    cod_municipio  CHAR(5)           NOT NULL,
    ano            SMALLINT UNSIGNED NOT NULL,
    semana         TINYINT UNSIGNED  NOT NULL,
    casos          INT UNSIGNED      NOT NULL,
    PRIMARY KEY (cod_evento, cod_municipio, ano, semana),
    CONSTRAINT fk_casos_evento    FOREIGN KEY (cod_evento)    REFERENCES dim_evento (cod_evento),
    CONSTRAINT fk_casos_municipio FOREIGN KEY (cod_municipio) REFERENCES dim_municipio (cod_municipio),
    CONSTRAINT ck_semana CHECK (semana BETWEEN 1 AND 53),
    -- Índice para las consultas más frecuentes: un evento a lo largo del tiempo.
    INDEX ix_evento_tiempo (cod_evento, ano, semana)
);
