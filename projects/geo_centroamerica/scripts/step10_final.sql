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
    5004::integer AS creation_user,
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

SELECT count(*) AS total_nuevas_georreferencias, count(distinct h3_cell7) AS total_nuevas_celdas_h7, count(distinct h3_cell5) AS total_nuevas_celdas_h5 FROM complemento_final_co;
