 Con tags:

Nivel	            admin_level
País	            2
Departamento	    4
Municipio	        6
Localidad/Barrio	8–10
 
 
wget https://download.geofabrik.de/south-america/colombia-latest.osm.pbf

 osm2pgsql   -d osm_colombia  -U jairovd  -H 127.0.0.1   -W  --create --slim   --hstore  --multi-geometry  colombia-latest.osm.pbf

SELECT * FROM planet_osm_line WHERE highway IS NOT NULL   AND (     name ILIKE 'calle %'     OR name ILIKE 'cra %' OR name ILIKE 'carrera %' OR name ILIKE 'cl %'  );
 
SELECT distinct name FROM planet_osm_line WHERE highway IS NOT NULL;


SELECT * into base1 FROM planet_osm_line WHERE highway IS NOT NULL and highway in ('residential','road','secondary','tertiary', 'trunk', 'track') AND  name is not null  ;

select name , highway, tags, ST_X( ST_Transform (ST_Centroid(way), 4326) ) lon  from base1 where length(name) > 1 and name not ilike '%carre%' and name not ilike '%call%' order by name ;


select name , highway from base1 where length(name) > 1 and name not ilike '%carre%' and name not ilike '%call%' order by name ;


select * into vias_carreras  from base1 where length(name) > 1 and (name ilike '%carrera%' or name ilike '%transver%' ); (ok)

select * into vias_calles  from base1 where length(name) > 1 and not (name ilike '%carrera%' or name ilike '%transver%' );  (ok)


SELECT  ST_Intersection(a.way, b.way) AS geom,  a.name AS calle,  b.name AS carrera FROM calles a JOIN vias_carreras b ON ST_Intersects(a.way, b.way);

ST_Transform
SELECT  ST_Intersection(a.way, b.way) AS geom, ST_X(ST_Intersection(a.way, b.way)) log, a.name AS calle,  b.name AS carrera FROM vias_calles  a JOIN vias_carreras b ON ST_Intersects(a.way, b.way) limit 30;

SELECT  ST_Intersection(a.way, b.way) AS geom, ST_X( ST_Transform (ST_Intersection(a.way, b.way), 4326)) log, ST_Y( ST_Transform (ST_Intersection(a.way, b.way), 4326)) lat, a.name AS calle,  b.name AS carrera FROM vias_calles  a JOIN vias_carreras b ON ST_Intersects(a.way, b.way) limit 30;


WITH cruces AS (
SELECT
ST_Intersection(a.way, b.way) AS geom,
a.name AS calle,
b.name AS carrera,
a.tags->'alt_name' AS cl_alt_name,
b.tags->'alt_name' AS cr_alt_name
FROM vias_calles a
JOIN vias_carreras b
ON ST_Intersects(a.way, b.way)
)
SELECT * into cruces_uno
FROM cruces
WHERE GeometryType(geom) = 'POINT';

CREATE TABLE intersecciones_final2 AS
SELECT
  c.geom,
  c.calle,
  c.carrera,
  m.name AS municipio,
  d.name AS departamento
FROM cruces_uno c
LEFT JOIN municipios m
  ON ST_Contains(m.way, c.geom)
LEFT JOIN departamentos d
  ON ST_Contains(d.way, c.geom);

SELECT departamento, municipio, count(*)  from intersecciones_final2 group by departamento, municipio order by municipio , 3 desc ;

elect departamento, municipio, calle, carrera, ST_Y( ST_Transform ( geom , 4326)) lat  , ST_X( ST_Transform ( geom , 4326)) lon from  intersecciones_final2 where municipio = 'Puerto Nariño' and   calle='Calle 7' order
 by 1,2,3,4  ;

-- V2
 SELECT c.geom, c.calle, c.carrera, m.name AS municipio FROM cruces c LEFT JOIN municipios m ON ST_Intersects(m.way, ST_Transform(ST_Buffer(ST_Transform(c.geom, 3857), 5), 4326 ));

CREATE TABLE intersecciones_final3 AS
SELECT
  c.geom,
  c.calle,
  c.carrera,
  c.cl_alt_name,
  c.cr_alt_name,
  m.name AS municipio,
  d.name AS departamento
FROM cruces_uno c
LEFT JOIN municipios m
  ON ST_Intersects(m.way, ST_Transform(ST_Buffer(ST_Transform(c.geom, 3857), 5), 4326 ))
LEFT JOIN departamentos d
  ON ST_Contains(d.way, c.geom);


-- OK
DROP TABLE intersecciones_final4 ;
CREATE TABLE intersecciones_final4 AS
SELECT
  c.geom,
  c.calle,
  c.carrera,
  c.cl_alt_name,
  c.cr_alt_name,
  m.name AS municipio,
  d.name AS departamento,
  ST_Y( ST_Transform ( c.geom , 4326)) lat,
  ST_X( ST_Transform ( c.geom , 4326)) lon,
  ROW_NUMBER() OVER () as id
FROM cruces_uno c
LEFT JOIN municipios m
  ON ST_Contains(m.way, c.geom)
LEFT JOIN departamentos d
  ON ST_Contains(d.way, c.geom);

intersecciones_final4
  
Column    
-------------- 
 geom         
 calle         
 carrera       
 cl_alt_name  
 cr_alt_name  
 municipio    
 departamento 
 lat          
 lon          
 id           

ALTER TABLE intersecciones_final4  ALTER COLUMN geom TYPE geometry(Point,4326) USING ST_Transform(geom,4326);

para borrar duplicado 
select departamento, municipio, calle, carrera, id  from intersecciones_final4 where id in(SELECT id
FROM (
    SELECT id, lat, lon,
           ROW_NUMBER() OVER (
               PARTITION BY lat, lon
               ORDER BY id
           ) AS rn
    FROM intersecciones_final4
) t
WHERE rn > 1 ) order by 1, 2, 3, 4 ;

DELETE FROM intersecciones_final4
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY lat, lon
                   ORDER BY id
               ) AS rn
        FROM intersecciones_final4
    ) t
    WHERE rn > 1
);


select departamento, municipio, calle, carrera, id  from intersecciones_final4 where id in(SELECT id
FROM (
    SELECT id, departamento, municipio, calle, carrera,
           ROW_NUMBER() OVER (
               PARTITION BY departamento, municipio, calle, carrera
               ORDER BY id
           ) AS rn
    FROM intersecciones_final4
) t
WHERE rn > 1 ) order by 1, 2, 3, 4 ;

DELETE FROM intersecciones_final4
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY departamento, municipio, calle, carrera
                   ORDER BY id
               ) AS rn
        FROM intersecciones_final4
    ) t
    WHERE rn > 1
);

CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE OR REPLACE FUNCTION normalizar_via(txt text)
RETURNS text AS $$
SELECT TRIM(
  REGEXP_REPLACE( 
    REGEXP_REPLACE( -- limpiar espacios dobles
      REGEXP_REPLACE(
        REGEXP_REPLACE(
          REGEXP_REPLACE(
            REGEXP_REPLACE(
              UPPER(unaccent(txt)),

              -- CARRERA
              '\m(CARRERA|CRA\.?|CR\.?|KR\.?|KRA\.?)\M', 'KRA', 'g'

            ),

            -- CALLE
            '\m(CALLE|CLL\.?|CL\.?|C/)\M', 'CLL', 'g'
          ),

          -- AVENIDA
          '\m(AVENIDA|AVDA\.?|AV\.?)\M', 'AV', 'g'
        ),

        -- TRANSVERSAL
        '\m(TRANSVERSAL|TRV\.?|TV\.?)\M', 'TV', 'g'
      ),

      -- DIAGONAL
      '\m(DIAGONAL|DG\.?)\M', 'DG', 'g'
    ),
    '\m(AUTOPISTA\.?)\M', 'AUT', 'g'
       
  )
);
$$ LANGUAGE sql IMMUTABLE;



UPDATE intersecciones_final4 SET   calle = normalizar_via(calle),   carrera = normalizar_via(carrera),   cl_alt_name = normalizar_via(cl_alt_name),   cr_alt_name = normalizar_via(cr_alt_name); 


UPDATE intersecciones_final4 SET  municipio ='El Difìcil' WHERE municipio = 'Ariguaní (El Difìcil)';
UPDATE intersecciones_final4 SET  municipio ='Bogotá' WHERE municipio = 'Bogotá Distrito Capital - Municipio';
UPDATE intersecciones_final4 SET  municipio ='Manaure' WHERE municipio= 'Manaure Balcón del Cesar';
UPDATE intersecciones_final4 SET  municipio ='Bocas de Satinga' WHERE municipio = 'Olaya Herrera (Bocas de Satinga)';
UPDATE intersecciones_final4 SET  municipio ='La Hormiga' WHERE municipio = 'Valle del Guamuez (La Hormiga)';
UPDATE intersecciones_final4 SET  municipio ='Punta de Piedras' WHERE municipio = 'Zapayán (Punta de Piedras)';
UPDATE intersecciones_final4 SET  municipio ='Sevilla' WHERE municipio = 'Zona Bananera (Prado Sevilla)';
delete from intersecciones_final4  where trim(calle)||trim(carrera) = trim(carrera) ||trim(calle) ;

SELECT e.enumlabel AS valor FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typname = 'georeference_icon_enum'  ORDER BY e.enumsortorder;

CREATE TYPE georeference_icon_enum AS ENUM ('0', '1', '2');

select ST_Distance(i4.geom, g.location) ddd, ST_Y( ST_Transform ( i4.geom , 4326)) lat  , ST_X( ST_Transform ( i4.geom , 4326)) lon,  ST_Distance ( ST_Transform(i4.geom,4326 ) , g.location), ST_Y( ST_Transform ( g.location , 4326)) lat2  , ST_X( ST_Transform ( g.location , 4326)) lon2 , ST_Distance ( ST_Transform(i4.geom,4326 ) , g.location)::float *111000 from  intersecciones_final4 i4 , georeference g where ST_Distance ( ST_Transform(i4.geom,4326 ) , g.location)::float *111000 < 20 limit 3;

select count(*) from  intersecciones_final4 i4 , georeference g where ST_Distance ( ST_Transform(i4.geom,4326 ) , g.location)::float *111000 < 20 limit 3;

CREATE INDEX idx_inter4_geom ON intersecciones_final4 USING GIST(geom);

CREATE INDEX idx_georeference_location ON georeference USING GIST(location);


select min(ST_Y( ST_Transform ( i4.geom , 4326)) ) min_lat, max(ST_Y( ST_Transform ( i4.geom , 4326)) ) max_lat,  min(ST_X( ST_Transform ( i4.geom , 4326))) min_lon , max(ST_X( ST_Transform ( i4.geom , 4326))) max_lon,   from  intersecciones_final4 i4 ;


ALTER TABLE intersecciones_final4 ALTER COLUMN geom TYPE geometry(Point,4326) USING ST_SetSRID(geom,4326);

select  ST_Transform( ST_SetSRID(i4.geom,3116), 4326 ), ST_Y( ST_Transform ( i4.geom , 4326)) lat  , ST_X( ST_Transform ( i4.geom , 4326)) lon,  ST_Distance ( ST_Transform(i4.geom,4326 ) , g.location) d, ST_Y( ST_Transform ( g.location , 4326)) lat2  , ST_X( ST_Transform ( g.location , 4326)) lon2 from  intersecciones_final4 i4 , georeference g  limit 3;


ST_Transform( ST_SetSRID(i4.geom,3116), 4326 )

SELECT
  ST_AsText(
    ST_Transform(
      ST_SetSRID(geom,3116),
      4326
    )
  )
FROM intersecciones_final4
LIMIT 5;

ALTER TABLE cruces_uno_test  ALTER COLUMN geom TYPE geometry(Point,4326) USING ST_Transform(geom,4326);

select ST_X( ST_Transform ( i4.geom , 4326)) lon from  cruces_uno_test ;


select *, ST_Y( ST_Transform ( c.geom , 4326)) lat, ST_X( ST_Transform ( c.geom , 4326)) lon from cruces_uno where carrera c ilike '%52 ESTE%' limit 100 ;

select ST_Distance(i4.geom, g.location)*111000 Distance, ST_Y( ST_Transform ( i4.geom , 4326)) lat  , ST_X( ST_Transform ( i4.geom , 4326)) lon, ST_Y( ST_Transform ( g.location , 4326)) lat2  , ST_X( ST_Transform ( g.location , 4326)) lon2, calle, carrera, municipio, display_name from  intersecciones_final4 i4 , georeference g  where ST_DWithin(i4.geom, g.location , 0.0001) limit 3;

select count(*) from  intersecciones_final4 i4 , georeference g  where ST_DWithin(i4.geom, g.location , 0.0001) ;

SELECT uuid_generate_v4() AS id, concat_ws(',', concat_ws(' con ', trim(calle), trim(carrera)), trim(cl_alt_name), trim(cr_alt_name), trim(municipio), trim(departamento)  ) AS name , geom  as location , concat_ws(',', concat_ws(' con ', trim(calle), trim(carrera)), trim(cl_alt_name), trim(cr_alt_name), trim(municipio), trim(departamento)  ) AS display_name, 'TOT' AS country_code, NULL AS client_id, '#bcbcbc'::text AS color , '2'::georeference_icon_enum  AS icon , 1 AS creation_user, NOW() AS created_at , NULL AS update_user , NULL updated_at  FROM intersecciones_final4 LIMIT 1;

 alter table geo_total  ADD COLUMN bbox geometry(Polygon,4326);
UPDATE geo_total SET bbox = ST_Envelope(geom);


apt update
apt install postgresql-server-dev-all gcc make pgxnclient
pgxn install h3

pgxn load -d osm_colombia h3

pgxn load -d osm_colombia h3 -U jairovd

apt install -y cmake make gcc postgresql-server-dev-17 libtool
git clone https://github.com/zachasme/h3-pg.git 

curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc |   gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc


sudo apt install curl ca-certificates
sudo install -d /usr/share/postgresql-common/pgdg
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc |   gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc

sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt update



SELECT h3_latlng_to_cell(POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))), 7) AS celda_h3, count(*) AS total_puntos FROM geo_total GROUP BY 1 ORDER BY total_puntos DESC;


CREATE OR REPLACE VIEW v_osm_h3_grid AS 
SELECT h3_latlng_to_cell(POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))), 7) AS celda_id, h3_cell_to_boundary_geometry( h3_latlng_to_cell(POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))), 7))::geometry(Polygon, 4324) AS geom,  count(*) AS cantidad_pois  FROM geo_total  GROUP BY 1, 2;


CREATE OR REPLACE VIEW v_osm_h3_grid AS
SELECT 
    h3_latlng_to_cell(POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))), 7) AS celda_id,

    ST_SetSRID(h3_cell_to_boundary_geometry(h3_latlng_to_cell(POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))), 7)), 4326) AS geom,
    count(*) AS cantidad_pois
FROM 
    geo_total
GROUP BY 
    1, 2;

    h3_latlng_to_cell(POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))), 7) 

update geo_total set h3_cell7 = h3_latlng_to_cell(POINT( ST_X( ST_Transform (location , 4326)) , ST_Y( ST_Transform (location , 4326))), 7) ;
update geo_total set h3_cell5 = h3_latlng_to_cell(POINT( ST_X( ST_Transform (location , 4326)) , ST_Y( ST_Transform (location , 4326))), 5) ;

Aquí tienes una referencia rápida de qué esperar con cada valor:
Resolución	  Tamaño de la celda (aprox.)	  Uso típico
0	            4.2 millones de km2               Continentes enteros
3	            12,392 km2                        Departamentos (ej. Huila o Sucre)
5	            252 km2                           Áreas metropolitanas (ej. todo Bogotá)
7	            5.16 km2                          Localidades o zonas rurales extensas
9	            0.10 km2 (10 hectáreas)	          Barrios o micro-zonas urbanas
12	          307  M2                           Edificios o manzanas pequeñas
15	          0.9 M2                            Precisión centimétrica (objetos individuales)


select h3_latlng_to_cell(POINT(  6.729296, -75.685439), 7) ;

select h3_latlng_to_cell(POINT(  -75.685439, 6.729296), 7) ;


select h3_latlng_to_cell(POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))), 7) , POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))) ,  h3_lat_lng_to_cell (ST_MakePoint( -75.685439, 6.729296), 7 )  ,  h3_latlng_to_cell( location , 7)  from geo_total limit 1;

select h3_latlng_to_cell(POINT(latitud, longitud ), 7) , POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))) ,  h3_lat_lng_to_cell (ST_MakePoint( -75.685439, 6.729296), 7 )  ,  h3_latlng_to_cell( point(latitud, longitud) , 7)  from geo_total limit 1;
 
select h3_latlng_to_cell(POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))), 7)  , POINT( ST_Y( ST_Transform (location , 4326)) , ST_X( ST_Transform (location , 4326))) ,  h3_lat_lng_to_cell (ST_MakePoint( -75.685439, 6.729296), 7 )  ,  h3_latlng_to_cell( location , 7)  from geo_total limit 1;


update georeference_rd set longitud = ST_X( ST_Transform (location , 4326));
update georeference_rd set latitud = ST_Y( ST_Transform (location , 4326));
update georeference_rd set h3_cell7 = h3_latlng_to_cell(POINT( ST_X( ST_Transform (location , 4326)) , ST_Y( ST_Transform (location , 4326))), 7) ;
update georeference_rd set h3_cell5 = h3_latlng_to_cell(POINT( ST_X( ST_Transform (location , 4326)) , ST_Y( ST_Transform (location , 4326))), 5) ;



