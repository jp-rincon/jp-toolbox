-- ============================================================================
-- SCRIPT DE PROCESAMIENTO DE COMPLEMENTO DE GEORREFERENCIAS OSM PARA COLOMBIA
-- Archivo: osm_calles_co_complemento.sql
-- Objetivo: Rellenar ÚNICAMENTE las celdas H7 faltantes en Colombia sin alterar
--           ni sobreescribir los 477,512 registros existentes aprobados por clientes.
-- Creado por: Usuario 5004
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS hstore;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS h3;

-- ----------------------------------------------------------------------------
-- PASO 1: TABLA DE CELDAS EXISTENTES (PARA EXCLUSIÓN ESTRICTA)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS celdas_existentes_co (
    h3_cell7 TEXT PRIMARY KEY
);

TRUNCATE TABLE celdas_existentes_co;

COPY celdas_existentes_co (h3_cell7) 
FROM '/data/celdas_existentes_co.csv' 
WITH (FORMAT csv, HEADER true);

-- ----------------------------------------------------------------------------
-- PASO 2: SELECCIÓN Y FILTRADO DE LA RED VIAL COMPLETA DE COLOMBIA
-- (Incluye vías primarias, troncales, autopistas y secundarias que antes faltaban)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS base_vias_co;

SELECT 
    osm_id,
    name,
    highway,
    ref,
    tags->'alt_name' AS alt_name,
    way
INTO base_vias_co
FROM planet_osm_line
WHERE highway IS NOT NULL
  AND highway IN (
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
    'residential', 'unclassified', 'road', 'living_street',
    'motorway_link', 'trunk_link', 'primary_link', 'secondary_link'
  )
  AND name IS NOT NULL
  AND length(trim(name)) > 1;

CREATE INDEX idx_base_vias_co_way ON base_vias_co USING GIST(way);

-- ----------------------------------------------------------------------------
-- PASO 3: CÁLCULO UNIVERSAL DE INTERSECCIONES / CRUCES VIALES
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS cruces_base_co;

WITH cruces_raw AS (
  SELECT
    (ST_Dump(ST_Intersection(a.way, b.way))).geom AS geom_3857,
    a.name AS via1,
    b.name AS via2,
    a.alt_name AS via1_alt,
    b.alt_name AS via2_alt,
    1 AS prioridad -- Prioridad 1: Cruce de calles formal
  FROM base_vias_co a
  JOIN base_vias_co b
    ON ST_Intersects(a.way, b.way)
   AND a.name < b.name
)
SELECT 
    ST_Transform(geom_3857, 4326) AS geom,
    via1,
    via2,
    via1_alt,
    via2_alt,
    prioridad
INTO cruces_base_co
FROM cruces_raw
WHERE ST_GeometryType(geom_3857) = 'ST_Point';

CREATE INDEX idx_cruces_base_co_geom ON cruces_base_co USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 4: PEAJES Y PUNTOS DE CONTROL
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS peajes_co;

SELECT 
    ST_Transform(way, 4326) AS geom,
    COALESCE(name, 'Peaje') AS nombre_peaje,
    2 AS prioridad -- Prioridad 2: Peaje
INTO peajes_co
FROM planet_osm_point
WHERE barrier = 'toll_booth';

CREATE INDEX idx_peajes_co_geom ON peajes_co USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 5: CENTROS POBLADOS, CORREGIMIENTOS Y LOCALIDADES (OSM Places)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS localidades_co;

SELECT 
    ST_Transform(way, 4326) AS geom,
    CASE 
        WHEN place IN ('village', 'hamlet') THEN 'Corregimiento / Caserío ' || name
        WHEN place = 'town' THEN 'Población ' || name
        WHEN place = 'suburb' THEN 'Barrio ' || name
        ELSE name
    END AS nombre_localidad,
    3 AS prioridad -- Prioridad 3: Localidad / Centro poblado
INTO localidades_co
FROM planet_osm_point
WHERE place IN ('town', 'village', 'hamlet', 'suburb')
  AND name IS NOT NULL
  AND length(trim(name)) > 1;

CREATE INDEX idx_localidades_co_geom ON localidades_co USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 6: DENSIFICACIÓN EN CARRETERAS LARGAS (Puntos cada ~1.5 - 2 km)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS puntos_carreteras_co;

WITH vias_principales AS (
  SELECT 
    name,
    ref,
    way,
    ST_Length(way) AS longitud_m
  FROM base_vias_co
  WHERE highway IN ('motorway', 'trunk', 'primary', 'secondary')
    AND ST_Length(way) >= 1500
),
puntos_interpolados AS (
  SELECT 
    v.name,
    v.ref,
    ST_Transform(ST_LineInterpolatePoint(v.way, f.frac), 4326) AS geom,
    4 AS prioridad -- Prioridad 4: Tramo de carretera
  FROM vias_principales v,
  LATERAL (
    SELECT generate_series(0.05, 0.95, (1500.0 / v.longitud_m)::numeric) AS frac
  ) f
)
SELECT *
INTO puntos_carreteras_co
FROM puntos_interpolados;

CREATE INDEX idx_puntos_carreteras_co_geom ON puntos_carreteras_co USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 7: LÍMITES ADMINISTRATIVOS (Departamentos y Municipios en 4326)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS departamentos_osm;
SELECT name, ST_Transform(way, 4326) AS geom 
INTO departamentos_osm 
FROM planet_osm_polygon 
WHERE boundary = 'administrative' AND admin_level = '4';

DROP TABLE IF EXISTS municipios_osm;
SELECT name, ST_Transform(way, 4326) AS geom 
INTO municipios_osm 
FROM planet_osm_polygon 
WHERE boundary = 'administrative' AND admin_level = '6';

CREATE INDEX idx_deptos_osm_geom ON departamentos_osm USING GIST(geom);
CREATE INDEX idx_mpios_osm_geom ON municipios_osm USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 8: FUNCIÓN DE NORMALIZACIÓN DE NOMENCLATURA COLOMBIANA
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION normalizar_via_co(txt text)
RETURNS text AS $$
SELECT TRIM(
  REGEXP_REPLACE( 
    REGEXP_REPLACE(
      REGEXP_REPLACE(
        REGEXP_REPLACE(
          REGEXP_REPLACE(
            REGEXP_REPLACE(
              UPPER(unaccent(txt)),
              '\m(CARRERA|CRA\.?|CR\.?|KR\.?|KRA\.?)\M', 'KRA', 'g'
            ),
            '\m(CALLE|CLL\.?|CL\.?|C/)\M', 'CLL', 'g'
          ),
          '\m(AVENIDA|AVDA\.?|AV\.?)\M', 'AV', 'g'
        ),
        '\m(TRANSVERSAL|TRV\.?|TV\.?)\M', 'TV', 'g'
      ),
      '\m(DIAGONAL|DG\.?)\M', 'DG', 'g'
    ),
    '\m(AUTOPISTA\.?)\M', 'AUT', 'g'
  )
);
$$ LANGUAGE sql IMMUTABLE;

-- ----------------------------------------------------------------------------
-- PASO 9: UNIFICACIÓN DE CANDIDATOS Y ASOCIACIÓN POLÍTICO-ADMINISTRATIVA
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS candidatos_unificados;

CREATE TABLE candidatos_unificados AS
-- 1. Cruces de vías
SELECT 
    c.geom,
    concat_ws(' con ', normalizar_via_co(c.via1), normalizar_via_co(c.via2)) AS referencia,
    m.name AS municipio,
    d.name AS departamento,
    c.prioridad
FROM cruces_base_co c
LEFT JOIN municipios_osm m ON ST_Contains(m.geom, c.geom)
LEFT JOIN departamentos_osm d ON ST_Contains(d.geom, c.geom)

UNION ALL

-- 2. Peajes
SELECT 
    p.geom,
    'Peaje ' || p.nombre_peaje AS referencia,
    m.name AS municipio,
    d.name AS departamento,
    p.prioridad
FROM peajes_co p
LEFT JOIN municipios_osm m ON ST_Contains(m.geom, p.geom)
LEFT JOIN departamentos_osm d ON ST_Contains(d.geom, p.geom)

UNION ALL

-- 3. Localidades y Centros Poblados
SELECT 
    l.geom,
    l.nombre_localidad AS referencia,
    m.name AS municipio,
    d.name AS departamento,
    l.prioridad
FROM localidades_co l
LEFT JOIN municipios_osm m ON ST_Contains(m.geom, l.geom)
LEFT JOIN departamentos_osm d ON ST_Contains(d.geom, l.geom)

UNION ALL

-- 4. Tramos viales en carreteras
SELECT 
    pc.geom,
    CASE 
        WHEN pc.ref IS NOT NULL AND pc.ref <> '' THEN normalizar_via_co(pc.name) || ' (' || pc.ref || ')'
        ELSE normalizar_via_co(pc.name)
    END AS referencia,
    m.name AS municipio,
    d.name AS departamento,
    pc.prioridad
FROM puntos_carreteras_co pc
LEFT JOIN municipios_osm m ON ST_Contains(m.geom, pc.geom)
LEFT JOIN departamentos_osm d ON ST_Contains(d.geom, pc.geom);

CREATE INDEX idx_candidatos_geom ON candidatos_unificados USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 10: CÁLCULO H3 Y FILTRADO ESTRICTO DE CELDAS FALTANTES
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS complemento_final_co;

WITH calculo_h3 AS (
  SELECT 
    geom,
    referencia,
    COALESCE(municipio, 'Colombia') AS municipio,
    COALESCE(departamento, 'Colombia') AS departamento,
    prioridad,
    ST_Y(geom) AS latitud,
    ST_X(geom) AS longitud,
    -- POINT(longitud, latitud) en PostgreSQL POINT(x, y) para extensión H3
    h3_latlng_to_cell(POINT(ST_X(geom), ST_Y(geom)), 7)::text AS h3_cell7,
    h3_latlng_to_cell(POINT(ST_X(geom), ST_Y(geom)), 5)::text AS h3_cell5
  FROM candidatos_unificados
  WHERE geom IS NOT NULL
),
celdas_nuevas_unicas AS (
  -- Solo celdas H7 que NO existen en geo_col
  SELECT 
    c.*,
    ROW_NUMBER() OVER (
      PARTITION BY c.h3_cell7 
      ORDER BY c.prioridad ASC, c.referencia ASC
    ) AS rn
  FROM calculo_h3 c
  WHERE c.h3_cell7 NOT IN (SELECT h3_cell7 FROM celdas_existentes_co)
)
SELECT 
    uuid_generate_v4() AS id,
    concat_ws(', ', trim(referencia), trim(municipio), trim(departamento)) AS name,
    concat_ws(', ', trim(referencia), trim(municipio), trim(departamento)) AS display_name,
    geom AS location,
    country_code,
    client_id,
    color,
    icon,
    creation_user,
    created_at,
    update_user,
    updated_at,
    NULL::geometry(Polygon, 4326) AS bbox,
    h3_cell7,
    h3_cell5,
    longitud,
    latitud
INTO complemento_final_co
FROM (
  SELECT 
    geom,
    referencia,
    municipio,
    departamento,
    'CO'::text AS country_code,
    NULL::integer AS client_id,
    '#bcbcbc'::text AS color,
    '2'::georeference_icon_enum AS icon,
    5004::integer AS creation_user, -- Usuario 5004
    NOW() AS created_at,
    NULL::integer AS update_user,
    NULL::timestamp without time zone AS updated_at,
    h3_cell7,
    h3_cell5,
    longitud,
    latitud
  FROM celdas_nuevas_unicas
  WHERE rn = 1
) q;

CREATE INDEX idx_complemento_geom ON complemento_final_co USING GIST(location);
CREATE INDEX idx_complemento_h7 ON complemento_final_co(h3_cell7);
CREATE INDEX idx_complemento_h5 ON complemento_final_co(h3_cell5);

-- ----------------------------------------------------------------------------
-- ESTADÍSTICAS DEL RESULTADO
-- ----------------------------------------------------------------------------
SELECT count(*) AS total_nuevas_georreferencias, count(distinct h3_cell7) AS total_nuevas_celdas_h7 FROM complemento_final_co;
