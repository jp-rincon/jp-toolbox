-- ============================================================================
-- SCRIPT DE PROCESAMIENTO DE GEORREFERENCIAS OSM PARA MÉXICO
-- Archivo: osm_calles_mx.sql
-- Objetivo: Procesar datos OSM de México para generar georreferencias 
--           digeribles y poblar la tabla geo_total (con soporte H3 y PostGIS).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PASO 0: INSTRUCCIONES PREVIAS DE DESCARGA E IMPORTACIÓN OSM
-- ----------------------------------------------------------------------------
-- 1. Descargar el extracto PBF de México desde Geofabrik:
--    wget https://download.geofabrik.de/north-america/mexico-latest.osm.pbf
--
-- 2. Importar a Postgres/PostGIS con osm2pgsql:
--    osm2pgsql -d osm_mexico -U postgres -H 127.0.0.1 -W --create --slim --hstore --multi-geometry mexico-latest.osm.pbf
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
DROP TABLE IF EXISTS base_vias_mx;

SELECT * 
INTO base_vias_mx 
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

CREATE INDEX idx_base_vias_mx_way ON base_vias_mx USING GIST(way);

-- ----------------------------------------------------------------------------
-- PASO 2: CÁLCULO UNIVERSAL DE INTERSECCIONES / CRUCES VIALES
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS cruces_base_mx;

WITH cruces AS (
  SELECT
    ST_Intersection(a.way, b.way) AS geom,
    a.name AS via1,
    b.name AS via2,
    a.tags->'alt_name' AS via1_alt,
    b.tags->'alt_name' AS via2_alt
  FROM base_vias_mx a
  JOIN base_vias_mx b 
    ON ST_Intersects(a.way, b.way) 
   AND a.name < b.name -- Evita auto-intersecciones y duplicados invertidos
)
SELECT * 
INTO cruces_base_mx
FROM cruces
WHERE GeometryType(geom) = 'POINT';

CREATE INDEX idx_cruces_base_mx_geom ON cruces_base_mx USING GIST(geom);

-- ----------------------------------------------------------------------------
-- PASO 3: EXTRACCIÓN DE LÍMITES ADMINISTRATIVOS (País, Estado/Entidad, Municipio/Alcaldía)
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
FROM cruces_base_mx c
LEFT JOIN municipios_osm m ON ST_Contains(m.way, c.geom)
LEFT JOIN departamentos_osm d ON ST_Contains(d.way, c.geom)
LEFT JOIN paises_osm p ON ST_Contains(p.way, c.geom);

-- Transformar columna de geometría a WGS84 EPSG:4326
ALTER TABLE intersecciones_raw 
  ALTER COLUMN geom TYPE geometry(Point, 4326) 
  USING ST_Transform(geom, 4326);

-- ----------------------------------------------------------------------------
-- PASO 5: FUNCIÓN DE NORMALIZACIÓN DE NOMENCLATURA VIAL Y GEOGRÁFICA DE MÉXICO
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION normalizar_via_mx(txt text)
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

                      -- PERIFÉRICO / PERIFERICO
                      '\m(PERIFERICO|PERIFERICA|PERIF\.?)\M', 'PERIF', 'g'
                    ),

                    -- VIADUCTO
                    '\m(VIADUCTO|VIAD\.?)\M', 'VIAD', 'g'
                  ),

                  -- PROLONGACIÓN
                  '\m(PROLONGACION|PROL\.?)\M', 'PROL', 'g'
                ),

                -- PRIVADA
                '\m(PRIVADA|PRV\.?)\M', 'PRV', 'g'
              ),

              -- CIRCUITO
              '\m(CIRCUITO|CIRC\.?)\M', 'CIRC', 'g'
            ),

            -- CAMINO
            '\m(CAMINO|CAM\.?)\M', 'CAM', 'g'
          ),

          -- PASEO / PASO
          '\m(PASEO|PASO|PSO\.?)\M', 'PSO', 'g'
        ),

        -- EJE VIAL
        '\m(EJE VIAL|EJE)\M', 'EJE', 'g'
      ),

      -- TRANSVERSAL / DIAGONAL / AUTOPISTA / RUTA
      '\m(TRANSVERSAL|TRV\.?|TV\.?)\M', 'TV', 'g'
    ),
    '\m(DIAGONAL|DG\.?)\M', 'DG', 'g'
  )
);
$$ LANGUAGE sql IMMUTABLE;

CREATE OR REPLACE FUNCTION abreviar_geografia_mx(txt text)
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
                    REGEXP_REPLACE(
                      REGEXP_REPLACE(
                        REGEXP_REPLACE(
                          REGEXP_REPLACE(txt,
                            '\m(Estado|Edo\.?)\M', 'Edo.', 'gi'),
                          '\m(Alcaldía|Alcaldia|Alc\.?)\M', 'Alc.', 'gi'),
                        '\m(Departamento|Depto\.?)\M', 'Depto.', 'gi'),
                      '\mdépartement\M', 'Depto.', 'gi'),
                    '\mdistrito\M', 'Dist.', 'gi'),
                  '\mprincipal\M', 'Ppal.', 'gi'),
                '\mprovincia\M', 'Prov.', 'gi'),
              '\mmunicipio\M', 'Mpio.', 'gi'),
            '\mcarretera\M', 'CRTR', 'gi'),
          '\mrepública\M', 'Rep.', 'gi'),
        '\mnacional\M', 'Nac.', 'gi'),
      '\murbanizaci[oó]n\M', 'Urb.', 'gi'),
    '\mresidencial\M', 'Res.', 'gi')
);
$$ LANGUAGE sql IMMUTABLE;

-- Aplicar normalización a vías
UPDATE intersecciones_raw 
SET via1 = normalizar_via_mx(via1),
    via2 = normalizar_via_mx(via2),
    via1_alt = normalizar_via_mx(via1_alt),
    via2_alt = normalizar_via_mx(via2_alt);

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

-- 2. Eliminar duplicados por misma vía1, vía2, municipio y estado/departamento
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
-- PASO 7: CREACIÓN Y POBLADO DE LA TABLA FINAL geo_total EN tobodb
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS geo_total CASCADE;

CREATE TABLE geo_total (
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
INSERT INTO geo_total (
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
    abreviar_geografia_mx(concat_ws(', ', 
        concat_ws(' con ', trim(via1), trim(via2)), 
        NULLIF(trim(via1_alt), ''), 
        NULLIF(trim(via2_alt), ''), 
        NULLIF(trim(municipio), ''), 
        NULLIF(trim(departamento), ''),
        NULLIF(trim(pais), '')
    )) AS name,
    abreviar_geografia_mx(concat_ws(', ', 
        concat_ws(' con ', trim(via1), trim(via2)), 
        NULLIF(trim(via1_alt), ''), 
        NULLIF(trim(via2_alt), ''), 
        NULLIF(trim(municipio), ''), 
        NULLIF(trim(departamento), ''),
        NULLIF(trim(pais), '')
    )) AS display_name,
    geom AS location,
    lat AS latitud,
    lon AS longitud,
    h3_latlng_to_cell(POINT(lon, lat), 5)::text AS h3_cell5,
    h3_latlng_to_cell(POINT(lon, lat), 7)::text AS h3_cell7,
    CASE 
        WHEN UPPER(pais) LIKE '%MEXICO%' OR UPPER(pais) LIKE '%MÉXICO%' THEN 'MEX'
        ELSE 'MEX'
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
CREATE INDEX idx_geo_total_location ON geo_total USING GIST(location);
CREATE INDEX idx_geo_total_h3_7 ON geo_total(h3_cell7);
CREATE INDEX idx_geo_total_h3_5 ON geo_total(h3_cell5);
CREATE INDEX idx_geo_total_country ON geo_total(country_code);

-- ----------------------------------------------------------------------------
-- FIN DEL SCRIPT
-- ----------------------------------------------------------------------------
