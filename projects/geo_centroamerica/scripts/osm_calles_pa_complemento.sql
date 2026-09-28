-- ============================================================================
-- SCRIPT DE PROCESAMIENTO DE COMPLEMENTO DE GEORREFERENCIAS OSM PARA PANAMÁ
-- Archivo: osm_calles_pa_complemento.sql
-- Objetivo: Rellenar ÚNICAMENTE las celdas H7 faltantes en Panamá (especialmente
--           zonas no metropolitanas, corredores viales, carreteras secundarias y poblados)
--           sin alterar ni sobreescribir los 12,383 registros existentes (605 celdas H7).
-- Creado por: Usuario 5004
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS hstore;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS h3;

DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'georeference_icon_enum') THEN 
        CREATE TYPE georeference_icon_enum AS ENUM ('0', '1', '2'); 
    END IF; 
END $$;

-- ----------------------------------------------------------------------------
-- PASO 1: TABLA DE CELDAS EXISTENTES (PARA EXCLUSIÓN ESTRICTA)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS celdas_existentes_pa (
    h3_cell7 TEXT PRIMARY KEY
);

TRUNCATE TABLE celdas_existentes_pa;

COPY celdas_existentes_pa (h3_cell7) 
FROM '/data/celdas_existentes_pa.csv' 
WITH (FORMAT csv, HEADER true);

-- ----------------------------------------------------------------------------
-- PASO 2: CAPAS ADMINISTRATIVAS (PROVINCIAS Y DISTRITOS/CORREGIMIENTOS)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS provincias_osm;
SELECT 
    osm_id,
    TRIM(REGEXP_REPLACE(name, '^(Provincia de |Comarca )\s*', '', 'i')) AS provincia,
    way
INTO provincias_osm
FROM planet_osm_polygon
WHERE boundary = 'administrative' 
  AND admin_level = '4'
  AND name IS NOT NULL;

CREATE INDEX idx_provincias_way ON provincias_osm USING GIST(way);

DROP TABLE IF EXISTS distritos_osm;
SELECT 
    osm_id,
    TRIM(REGEXP_REPLACE(name, '^(Distrito de |Corregimiento de )\s*', '', 'i')) AS distrito,
    way
INTO distritos_osm
FROM planet_osm_polygon
WHERE boundary = 'administrative' 
  AND admin_level IN ('6', '8')
  AND name IS NOT NULL;

CREATE INDEX idx_distritos_way ON distritos_osm USING GIST(way);

-- ----------------------------------------------------------------------------
-- PASO 3: SELECCIÓN Y ESTANDARIZACIÓN DE LA RED VIAL DE PANAMÁ
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS base_vias_pa;

SELECT 
    osm_id,
    highway,
    ref,
    tags->'alt_name' AS alt_name,
    UPPER(TRIM(
      REGEXP_REPLACE(
        REGEXP_REPLACE(
          REGEXP_REPLACE(
            REGEXP_REPLACE(
              REGEXP_REPLACE(
                REGEXP_REPLACE(
                  REGEXP_REPLACE(name, '^Carretera\s+', 'CRTR ', 'i'),
                  '^Avenida\s+', 'AV ', 'i'),
                '^Calle\s+', 'CLL ', 'i'),
              '^Autopista\s+', 'AUT ', 'i'),
            '^Corredor\s+', 'CORR ', 'i'),
          '^Vía\s+', 'VIA ', 'i'),
        '^Camino\s+', 'CMN ', 'i')
    )) AS name,
    way
INTO base_vias_pa
FROM planet_osm_line
WHERE highway IS NOT NULL
  AND highway IN (
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
    'residential', 'unclassified', 'road', 'living_street', 'track',
    'motorway_link', 'trunk_link', 'primary_link', 'secondary_link'
  )
  AND name IS NOT NULL
  AND length(trim(name)) > 1;

CREATE INDEX idx_base_vias_pa_way ON base_vias_pa USING GIST(way);

-- ----------------------------------------------------------------------------
-- PASO 4: FUENTE 1 - PEAJES Y PUNTOS DE CONTROL (PRIORIDAD 1)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS peajes_pa;

WITH peajes_puntos AS (
  SELECT 
    ST_Transform(way, 4326) AS geom,
    COALESCE(
      name, 
      tags->'name', 
      tags->'description', 
      'Estación de Peaje'
    ) AS nombre_peaje
  FROM planet_osm_point
  WHERE barrier = 'toll_booth' 
     OR highway = 'toll_gantry'
     OR tags->'barrier' = 'toll_booth'
)
SELECT 
  geom,
  UPPER(TRIM(
    CASE 
      WHEN nombre_peaje ILIKE 'PEAJE%' THEN nombre_peaje
      ELSE 'PEAJE ' || nombre_peaje 
    END
  )) AS referencia,
  1 AS prioridad
INTO peajes_pa
FROM peajes_puntos
WHERE geom IS NOT NULL;

-- ----------------------------------------------------------------------------
-- PASO 5: FUENTE 2 - CRUCES E INTERSECCIONES VIALES (PRIORIDAD 2)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS cruces_base_pa;

WITH intersecciones_raw AS (
  SELECT
    ST_Transform((ST_Dump(ST_Intersection(a.way, b.way))).geom, 4326) AS geom,
    a.name AS via1,
    b.name AS via2
  FROM base_vias_pa a
  JOIN base_vias_pa b 
    ON ST_Intersects(a.way, b.way)
   AND a.name < b.name
)
SELECT 
  geom,
  via1 || ' con ' || via2 AS referencia,
  2 AS prioridad
INTO cruces_base_pa
FROM intersecciones_raw
WHERE ST_GeometryType(geom) = 'ST_Point';

CREATE INDEX idx_cruces_pa_geom ON cruces_base_pa USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 6: FUENTE 3 - LOCALIDADES, CIUDADES Y ALDEAS (PRIORIDAD 3)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS localidades_pa;

WITH loc_raw AS (
  SELECT 
    ST_Transform(way, 4326) AS geom,
    name,
    place
  FROM planet_osm_point
  WHERE place IN ('city', 'town', 'village', 'hamlet', 'suburb', 'neighbourhood')
    AND name IS NOT NULL
    AND length(trim(name)) > 1
)
SELECT 
  geom,
  UPPER(TRIM(
    CASE 
      WHEN place = 'city' THEN 'CIUDAD ' || name
      WHEN place = 'town' THEN 'POBLADO ' || name
      WHEN place = 'village' THEN 'ALDEA ' || name
      WHEN place = 'hamlet' THEN 'CASERIO ' || name
      ELSE 'LOCALIDAD ' || name
    END
  )) AS referencia,
  3 AS prioridad
INTO localidades_pa
FROM loc_raw
WHERE geom IS NOT NULL;

CREATE INDEX idx_localidades_pa_geom ON localidades_pa USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 7: FUENTE 4 - MUESTREO DE CARRETERAS EN TRAMOS LARGOS (PRIORIDAD 4)
-- Segmentación cada ~3 km en vías troncales, primarias y secundarias
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS puntos_carreteras_pa;

WITH carreteras_principales AS (
  SELECT 
    osm_id,
    name,
    ref,
    highway,
    ST_Length(ST_Transform(way, 3857)) AS longitud_metros,
    way
  FROM base_vias_pa
  WHERE highway IN ('motorway', 'trunk', 'primary', 'secondary', 'unclassified', 'track')
    AND ST_Length(ST_Transform(way, 3857)) >= 2000
),
puntos_fraccion AS (
  SELECT 
    c.osm_id,
    c.name,
    c.ref,
    c.highway,
    c.longitud_metros,
    step.f AS fraccion,
    ST_Transform(ST_LineInterpolatePoint(c.way, step.f), 4326) AS geom
  FROM carreteras_principales c
  CROSS JOIN LATERAL (
    SELECT generate_series(0.05::numeric, 0.95::numeric, 
      GREATEST(0.05::numeric, LEAST(0.5::numeric, (2500.0 / GREATEST(c.longitud_metros, 2500.0))::numeric))
    ) AS f
  ) step
)
SELECT 
  geom,
  UPPER(TRIM(
    CASE 
      WHEN ref IS NOT NULL AND ref != '' AND name IS NOT NULL AND name != '' THEN 'KM ' || ROUND((longitud_metros * fraccion / 1000.0)::numeric, 0)::text || ' ' || ref || ' - ' || name
      WHEN ref IS NOT NULL AND ref != '' THEN 'KM ' || ROUND((longitud_metros * fraccion / 1000.0)::numeric, 0)::text || ' ' || ref
      ELSE 'KM ' || ROUND((longitud_metros * fraccion / 1000.0)::numeric, 0)::text || ' ' || name
    END
  )) AS referencia,
  4 AS prioridad
INTO puntos_carreteras_pa
FROM puntos_fraccion
WHERE geom IS NOT NULL;

CREATE INDEX idx_carreteras_pa_geom ON puntos_carreteras_pa USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 8: UNIFICACIÓN Y ASIGNACIÓN TERRITORIAL (DISTRITO Y PROVINCIA)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS candidatos_unificados;

WITH universo_candidatos AS (
  SELECT geom, referencia, prioridad FROM peajes_pa
  UNION ALL
  SELECT geom, referencia, prioridad FROM cruces_base_pa
  UNION ALL
  SELECT geom, referencia, prioridad FROM localidades_pa
  UNION ALL
  SELECT geom, referencia, prioridad FROM puntos_carreteras_pa
)
SELECT 
  u.geom,
  u.referencia,
  u.prioridad,
  COALESCE(d.distrito, 'Panamá') AS distrito,
  COALESCE(p.provincia, 'Panamá') AS provincia
INTO candidatos_unificados
FROM universo_candidatos u
LEFT JOIN LATERAL (
  SELECT d.distrito 
  FROM distritos_osm d 
  WHERE ST_Intersects(d.way, ST_Transform(u.geom, 3857))
  LIMIT 1
) d ON true
LEFT JOIN LATERAL (
  SELECT p.provincia 
  FROM provincias_osm p 
  WHERE ST_Intersects(p.way, ST_Transform(u.geom, 3857))
  LIMIT 1
) p ON true;

CREATE INDEX idx_candidatos_pa_geom ON candidatos_unificados USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 9: CÁLCULO H3 (ORDEN ESTRICTO lon, lat) Y EXCLUSIÓN DE CELDAS PREVIAS
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS complemento_final_pa;

WITH calculo_h3 AS (
  SELECT 
    geom,
    referencia,
    distrito,
    provincia,
    prioridad,
    ST_Y(geom) AS latitud,
    ST_X(geom) AS longitud,
    -- NOTA CRÍTICA: POINT(longitud, latitud) en PostgreSQL POINT(x, y)
    h3_latlng_to_cell(POINT(ST_X(geom), ST_Y(geom)), 7)::text AS h3_cell7,
    h3_latlng_to_cell(POINT(ST_X(geom), ST_Y(geom)), 5)::text AS h3_cell5
  FROM candidatos_unificados
  WHERE geom IS NOT NULL
),
celdas_nuevas_unicas AS (
  SELECT 
    c.*,
    ROW_NUMBER() OVER (
      PARTITION BY c.h3_cell7 
      ORDER BY c.prioridad ASC, c.referencia ASC
    ) AS rn
  FROM calculo_h3 c
  -- EXCLUSIÓN ESTRICTA: ninguna celda existente puede ser incluida
  WHERE c.h3_cell7 NOT IN (SELECT h3_cell7 FROM celdas_existentes_pa)
)
SELECT 
    uuid_generate_v4() AS id,
    concat_ws(', ', trim(referencia), trim(distrito), trim(provincia), 'Panamá') AS name,
    concat_ws(', ', trim(referencia), trim(distrito), trim(provincia), 'Panamá') AS display_name,
    geom AS location,
    'PAN'::text AS country_code,
    NULL::integer AS client_id,
    '#bcbcbc'::text AS color,
    '2'::georeference_icon_enum AS icon,
    5004::integer AS creation_user,
    NOW() AS created_at,
    NULL::integer AS update_user,
    NULL::timestamp without time zone AS updated_at,
    NULL::geometry(Polygon, 4326) AS bbox,
    h3_cell7,
    h3_cell5,
    longitud,
    latitud
INTO complemento_final_pa
FROM celdas_nuevas_unicas
WHERE rn = 1;

CREATE INDEX idx_complemento_pa_geom ON complemento_final_pa USING GIST(location);
CREATE INDEX idx_complemento_pa_h7 ON complemento_final_pa(h3_cell7);
CREATE INDEX idx_complemento_pa_h5 ON complemento_final_pa(h3_cell5);

-- Resumen estadístico
SELECT 
    count(*) AS total_nuevas_georreferencias, 
    count(distinct h3_cell7) AS total_nuevas_celdas_h7, 
    count(distinct h3_cell5) AS total_nuevas_celdas_h5 
FROM complemento_final_pa;
