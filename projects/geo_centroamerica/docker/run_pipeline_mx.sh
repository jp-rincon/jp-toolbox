#!/usr/bin/env bash
# ==============================================================================
# Script de automatización para descargar, importar y procesar OSM México (Disco K:)
# ==============================================================================

set -e

PBF_URL="https://download.geofabrik.de/north-america/mexico-latest.osm.pbf"
DATA_DIR="/mnt/k/docker_volumes/data"
PBF_FILE="$DATA_DIR/mexico-latest.osm.pbf"
DB_NAME="osm_mexico"
DB_USER="postgres"
CONTAINER_NAME="osm_centroamerica_gis"
EXPORT_SQL="/mnt/k/gps_total_mexico.sql"
DUMP_FILE="/mnt/k/docker_volumes/osm_mexico_full.dump"

echo "=== 1. Levantando contenedor Docker ==="
docker-compose up -d

echo "=== Esperando inicio de PostgreSQL ==="
until docker exec $CONTAINER_NAME pg_isready -U $DB_USER; do
  sleep 2
done

echo "=== 2. Creando base de datos $DB_NAME si no existe ==="
docker exec -i $CONTAINER_NAME psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;" || true

echo "=== 3. Descargando datos OSM de México en $DATA_DIR ==="
mkdir -p "$DATA_DIR"
if [ ! -f "$PBF_FILE" ]; then
    wget -O "$PBF_FILE" "$PBF_URL"
else
    echo "Archivo $PBF_FILE ya existe. Omitiendo descarga."
fi

echo "=== 4. Habilitando extensiones y limpiando tablas previas ==="
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
  DROP TABLE IF EXISTS planet_osm_point, planet_osm_line, planet_osm_polygon, planet_osm_roads, planet_osm_nodes, planet_osm_ways, planet_osm_rels CASCADE;
  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE EXTENSION IF NOT EXISTS hstore;
  CREATE EXTENSION IF NOT EXISTS unaccent;
  CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
  CREATE EXTENSION IF NOT EXISTS h3;
"

echo "=== 5. Importando PBF con osm2pgsql ==="
docker exec -i $CONTAINER_NAME osm2pgsql \
    -d $DB_NAME \
    -U $DB_USER \
    --create \
    --slim \
    --hstore \
    --multi-geometry \
    /data/mexico-latest.osm.pbf

echo "=== 6. Ejecutando transformación de georreferencias (osm_calles_mx.sql) ==="
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /scripts/osm_calles_mx.sql

echo "=== 7. Exportando respaldos a disco K: ==="
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME -t geo_total --clean > "$EXPORT_SQL"
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME -Fc -f /data/../osm_mexico_full.dump

echo "=== PROCESO COMPLETADO EXITOSAMENTE ==="
echo "La tabla 'geo_total' ha sido poblada y respaldada en $EXPORT_SQL"
