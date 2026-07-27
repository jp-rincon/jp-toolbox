#!/usr/bin/env bash
# ==============================================================================
# Script de automatización para descargar, importar y procesar OSM Centroamérica
# ==============================================================================

set -e

PBF_URL="https://download.geofabrik.de/central-america-latest.osm.pbf"
PBF_FILE="./data/central-america-latest.osm.pbf"
DB_NAME="osm_centroamerica"
DB_USER="postgres"
CONTAINER_NAME="osm_centroamerica_gis"

echo "=== 1. Levantando contenedor Docker ==="
docker-compose up -d --build

echo "=== Esperando inicio de PostgreSQL ==="
until docker exec $CONTAINER_NAME pg_isready -U $DB_USER; do
  sleep 2
done

echo "=== 2. Descargando datos OSM de Centroamérica ==="
mkdir -p ./data
if [ ! -f "$PBF_FILE" ]; then
    wget -O "$PBF_FILE" "$PBF_URL"
else
    echo "Archivo $PBF_FILE ya existe. Omitiendo descarga."
fi

echo "=== 3. Habilitando extensiones y limpiando tablas previas ==="
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
  DROP TABLE IF EXISTS planet_osm_point, planet_osm_line, planet_osm_polygon, planet_osm_roads, planet_osm_nodes, planet_osm_ways, planet_osm_rels CASCADE;
  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE EXTENSION IF NOT EXISTS hstore;
  CREATE EXTENSION IF NOT EXISTS unaccent;
  CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
  CREATE EXTENSION IF NOT EXISTS h3;
"

echo "=== 4. Importando PBF con osm2pgsql ==="
docker exec -i $CONTAINER_NAME osm2pgsql \
    -d $DB_NAME \
    -U $DB_USER \
    --create \
    --slim \
    --hstore \
    --multi-geometry \
    /data/central-america-latest.osm.pbf

echo "=== 5. Ejecutando transformación de georreferencias (osm_calles_ca.sql) ==="
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /scripts/osm_calles_ca.sql

echo "=== PROCESO COMPLETADO EXITOSAMENTE ==="
echo "La tabla 'gps_total' ha sido poblada con las georreferencias de Centroamérica."
