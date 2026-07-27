-- ============================================================================
-- SCRIPT DE PROCESAMIENTO DE GEORREFERENCIAS OSM PARA CENTROAMÉRICA
-- Archivo: osm_calles_ca.sql
-- Objetivo: Procesar datos OSM de Centroamérica para generar georreferencias 
--           digeribles y poblar la tabla gps_total (con soporte H3 y PostGIS).
-- Países incluidos: Guatemala, Belice, El Salvador, Honduras, Nicaragua, Costa Rica, Panamá.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PASO 0: INSTRUCCIONES PREVIAS DE DESCARGA E IMPORTACIÓN OSM
-- ----------------------------------------------------------------------------
-- 1. Descargar el extracto PBF de Centroamérica desde Geofabrik:
--    wget https://download.geofabrik.de/central-america-latest.osm.pbf
--
-- 2. Importar a Postgres/PostGIS con osm2pgsql:
--    osm2pgsql -d osm_centroamerica -U postgres -H 127.0.0.1 -W --create --slim --hstore --multi-geometry central-america-latest.osm.pbf
-- ----------------------------------------------------------------------------

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS hstore;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS h3;

-- ----------------------------------------------------------------------------
-- PASO 1: SELECCIÓN Y FILTRADO DE LA RED VIAL BASE
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS base_vias_ca;

SELECT * 
INTO base_vias_ca 
FROM planet_osm_line 
WHERE highway IS NOT NULL 
  AND highway IN (
    'residential', 
    'road', 
    'secondary', 
    'tertiary', 
    'trunk', 
    'primary', 
    'motorway', 
    'track'
  ) 
  AND name IS NOT NULL 
  AND length(trim(name)) > 1;

CREATE INDEX idx_base_vias_ca_way ON base_vias_ca USING GIST(way);

-- ----------------------------------------------------------------------------
-- PASO 2: CÁLCULO UNIVERSAL DE INTERSECCIONES / CRUCES VIALES
-- (Adaptación para Centroamérica: Intersección entre cualquier par de vías distintas)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS cruces_base_ca;

WITH cruces AS (
  SELECT
    ST_Intersection(a.way, b.way) AS geom,
    a.name AS via1,
    b.name AS via2,
    a.tags->'alt_name' AS via1_alt,
    b.tags->'alt_name' AS via2_alt
  FROM base_vias_ca a
  JOIN base_vias_ca b 
    ON ST_Intersects(a.way, b.way) 
   AND a.name < b.name -- Evita auto-intersecciones y duplicados invertidos (A con B vs B con A)
)
SELECT * 
INTO cruces_base_ca
FROM cruces
WHERE GeometryType(geom) = 'POINT';

CREATE INDEX idx_cruces_base_ca_geom ON cruces_base_ca USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 3: EXTRACCIÓN DE LÍMITES ADMINISTRATIVOS (País, Departamento/Provincia, Municipio/Cantón)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS paises_osm;
SELECT name, way 
INTO paises_osm 
FROM planet_osm_polygon 
WHERE boundary = 'administrative' AND admin_level = '2';

DROP TABLE IF EXISTS departamentos_osm;
SELECT name, way 
INTO departamentos_osm 
FROM planet_osm_polygon 
WHERE boundary = 'administrative' AND admin_level = '4';

DROP TABLE IF EXISTS municipios_osm;
SELECT name, way 
INTO municipios_osm 
FROM planet_osm_polygon 
WHERE boundary = 'administrative' AND admin_level IN ('6', '8');

CREATE INDEX idx_paises_osm_way ON paises_osm USING GIST(way);
CREATE INDEX idx_departamentos_osm_way ON departamentos_osm USING GIST(way);
CREATE INDEX idx_municipios_osm_way ON municipios_osm USING GIST(way);

-- ----------------------------------------------------------------------------
-- PASO 4: ASOCIACIÓN ESPACIAL DE CRUCES CON DIVISIONES POLÍTICAS
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS intersecciones_raw;

CREATE TABLE intersecciones_raw AS
SELECT
  c.geom,
  c.via1,
  c.via2,
  c.via1_alt,
  c.via2_alt,
  m.name AS municipio,
  d.name AS departamento,
  p.name AS pais,
  ST_Y(ST_Transform(c.geom, 4326)) AS lat,
  ST_X(ST_Transform(c.geom, 4326)) AS lon,
  ROW_NUMBER() OVER () AS id
FROM cruces_base_ca c
LEFT JOIN municipios_osm m ON ST_Contains(m.way, c.geom)
LEFT JOIN departamentos_osm d ON ST_Contains(d.way, c.geom)
LEFT JOIN paises_osm p ON ST_Contains(p.way, c.geom);

-- Transformar columna de geometría a WGS84 EPSG:4326
ALTER TABLE intersecciones_raw 
  ALTER COLUMN geom TYPE geometry(Point, 4326) 
  USING ST_Transform(geom, 4326);

-- ----------------------------------------------------------------------------
-- PASO 5: FUNCIÓN DE NORMALIZACIÓN DE NOMENCLATURA VIAL
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION normalizar_via_ca(txt text)
RETURNS text AS $$
SELECT TRIM(
  REGEXP_REPLACE(
    REGEXP_REPLACE(
      REGEXP_REPLACE(
        REGEXP_REPLACE(
          REGEXP_REPLACE(
            REGEXP_REPLACE(
              REGEXP_REPLACE(
                REGEXP_REPLACE(
                  REGEXP_REPLACE(
                    UPPER(unaccent(txt)),

                    -- AVENIDA
                    '\m(AVENIDA|AVDA\.?|AV\.?)\M', 'AV', 'g'
                  ),

                  -- CALLE
                  '\m(CALLE|CLL\.?|CL\.?|C/)\M', 'CLL', 'g'
                ),

                -- BULEVAR / BOULEVARD
                '\m(BULEVAR|BOULEVARD|BLVD\.?|BLV\.?)\M', 'BLVD', 'g'
              ),

              -- CALZADA
              '\m(CALZADA|CLZD\.?|CZD\.?)\M', 'CLZD', 'g'
            ),

            -- CARRETERA
            '\m(CARRETERA|CRTR\.?|CARR\.?)\M', 'CRTR', 'g'
          ),

          -- TRANSVERSAL
          '\m(TRANSVERSAL|TRV\.?|TV\.?)\M', 'TV', 'g'
        ),

        -- DIAGONAL
        '\m(DIAGONAL|DG\.?)\M', 'DG', 'g'
      ),

      -- AUTOPISTA
      '\m(AUTOPISTA|AUT\.?)\M', 'AUT', 'g'
    ),

    -- RUTA
    '\m(RUTA|RT\.?)\M', 'RT', 'g'
  )
);
$$ LANGUAGE sql IMMUTABLE;

-- Aplicar normalización a vías
UPDATE intersecciones_raw 
SET via1 = normalizar_via_ca(via1),
    via2 = normalizar_via_ca(via2),
    via1_alt = normalizar_via_ca(via1_alt),
    via2_alt = normalizar_via_ca(via2_alt);

-- ----------------------------------------------------------------------------
-- PASO 6: DEPURACIÓN Y ELIMINACIÓN DE DUPLICADOS
-- ----------------------------------------------------------------------------

-- 1. Eliminar duplicados por misma latitud y longitud exacta
DELETE FROM intersecciones_raw
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY lat, lon
                   ORDER BY id
               ) AS rn
        FROM intersecciones_raw
    ) t
    WHERE rn > 1
);

-- 2. Eliminar duplicados por misma vía1, vía2, municipio y departamento
DELETE FROM intersecciones_raw
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY COALESCE(pais, ''), COALESCE(departamento, ''), COALESCE(municipio, ''), via1, via2
                   ORDER BY id
               ) AS rn
        FROM intersecciones_raw
    ) t
    WHERE rn > 1
);

-- ----------------------------------------------------------------------------
-- PASO 7: CREACIÓN Y POBLADO DE LA TABLA FINAL gps_total EN tobodb
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS gps_total CASCADE;

CREATE TABLE gps_total (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    latitud DOUBLE PRECISION,
    longitud DOUBLE PRECISION,
    h3_cell5 TEXT,
    h3_cell7 TEXT,
    country_code VARCHAR(3),
    pais TEXT,
    departamento TEXT,
    municipio TEXT,
    color TEXT DEFAULT '#bcbcbc',
    icon VARCHAR(10) DEFAULT '2',
    bbox GEOMETRY(Geometry, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inserción de datos transformados y formateados
INSERT INTO gps_total (
    id,
    name,
    display_name,
    location,
    latitud,
    longitud,
    h3_cell5,
    h3_cell7,
    country_code,
    pais,
    departamento,
    municipio,
    color,
    icon,
    bbox,
    created_at
)
SELECT 
    uuid_generate_v4() AS id,
    concat_ws(', ', 
        concat_ws(' con ', trim(via1), trim(via2)), 
        NULLIF(trim(via1_alt), ''), 
        NULLIF(trim(via2_alt), ''), 
        NULLIF(trim(municipio), ''), 
        NULLIF(trim(departamento), ''),
        NULLIF(trim(pais), '')
    ) AS name,
    concat_ws(', ', 
        concat_ws(' con ', trim(via1), trim(via2)), 
        NULLIF(trim(via1_alt), ''), 
        NULLIF(trim(via2_alt), ''), 
        NULLIF(trim(municipio), ''), 
        NULLIF(trim(departamento), ''),
        NULLIF(trim(pais), '')
    ) AS display_name,
    geom AS location,
    lat AS latitud,
    lon AS longitud,
    h3_latlng_to_cell(POINT(lon, lat), 5)::text AS h3_cell5,
    h3_latlng_to_cell(POINT(lon, lat), 7)::text AS h3_cell7,
    CASE 
        WHEN UPPER(pais) LIKE '%GUATEMALA%' THEN 'GTM'
        WHEN UPPER(pais) LIKE '%EL SALVADOR%' THEN 'SLV'
        WHEN UPPER(pais) LIKE '%HONDURAS%' THEN 'HND'
        WHEN UPPER(pais) LIKE '%NICARAGUA%' THEN 'NIC'
        WHEN UPPER(pais) LIKE '%COSTA RICA%' THEN 'CRI'
        WHEN UPPER(pais) LIKE '%PANAMA%' OR UPPER(pais) LIKE '%PANAMÁ%' THEN 'PAN'
        WHEN UPPER(pais) LIKE '%BELIZE%' OR UPPER(pais) LIKE '%BELICE%' 
             OR municipio IN ('Toledo', 'Cayo', 'Orange Walk', 'Corozal', 'Stann Creek', 'Belize') THEN 'BLZ'
        WHEN UPPER(pais) LIKE '%CUBA%' THEN 'CUB'
        WHEN UPPER(pais) LIKE '%DOMINICANA%' THEN 'DOM'
        WHEN UPPER(pais) LIKE '%JAMAICA%' THEN 'JAM'
        WHEN UPPER(pais) LIKE '%HAITI%' OR UPPER(pais) LIKE '%AYITI%' THEN 'HTI'
        WHEN UPPER(pais) LIKE '%BAHAMAS%' THEN 'BHS'
        WHEN UPPER(pais) LIKE '%TRINIDAD%' THEN 'TTO'
        ELSE 'CA'
    END AS country_code,
    pais,
    departamento,
    municipio,
    '#bcbcbc' AS color,
    '2' AS icon,
    ST_Envelope(geom) AS bbox,
    NOW() AS created_at
FROM intersecciones_raw;

-- ----------------------------------------------------------------------------
-- PASO 8: ÍNDICES DE ALTO RENDIMIENTO
-- ----------------------------------------------------------------------------
CREATE INDEX idx_gps_total_location ON gps_total USING GIST(location);
CREATE INDEX idx_gps_total_h3_7 ON gps_total(h3_cell7);
CREATE INDEX idx_gps_total_h3_5 ON gps_total(h3_cell5);
CREATE INDEX idx_gps_total_country ON gps_total(country_code);

-- ----------------------------------------------------------------------------
-- FIN DEL SCRIPT
-- ----------------------------------------------------------------------------
