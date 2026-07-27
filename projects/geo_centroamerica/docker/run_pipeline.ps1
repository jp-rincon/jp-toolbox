# ==============================================================================
# Script PowerShell para descargar, importar y procesar OSM Centroamérica en Windows
# ==============================================================================

$ErrorActionPreference = "Stop"

$PbfUrl = "https://download.geofabrik.de/central-america-latest.osm.pbf"
$DataDir = ".\data"
$PbfFile = "$DataDir\central-america-latest.osm.pbf"
$DbName = "osm_centroamerica"
$DbUser = "postgres"
$ContainerName = "osm_centroamerica_gis"

Write-Host "=== 1. Levantando contenedor Docker ===" -ForegroundColor Green
docker-compose up -d --build

Write-Host "=== Esperando inicio de PostgreSQL ===" -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 2
    $ready = docker exec $ContainerName pg_isready -U $DbUser 2>$null
} until ($LASTEXITCODE -eq 0)

Write-Host "=== 2. Descargando datos OSM de Centroamérica ===" -ForegroundColor Green
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir | Out-Null
}

if (-not (Test-Path $PbfFile)) {
    Write-Host "Descargando extracto PBF desde Geofabrik..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $PbfUrl -OutFile $PbfFile
} else {
    Write-Host "El archivo $PbfFile ya existe. Omitiendo descarga." -ForegroundColor Cyan
}

Write-Host "=== 3. Habilitando extensiones y limpiando tablas previas ===" -ForegroundColor Green
"DROP TABLE IF EXISTS planet_osm_point, planet_osm_line, planet_osm_polygon, planet_osm_roads, planet_osm_nodes, planet_osm_ways, planet_osm_rels CASCADE; CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS hstore; CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS ""uuid-ossp""; CREATE EXTENSION IF NOT EXISTS h3;" | docker exec -i $ContainerName psql -U $DbUser -d $DbName

Write-Host "=== 4. Importando PBF con osm2pgsql ===" -ForegroundColor Green
docker exec -i $ContainerName osm2pgsql -d $DbName -U $DbUser --create --slim --hstore --multi-geometry /data/central-america-latest.osm.pbf

Write-Host "=== 5. Ejecutando transformación de georreferencias (osm_calles_ca.sql) ===" -ForegroundColor Green
docker exec -i $ContainerName psql -U $DbUser -d $DbName -f /scripts/osm_calles_ca.sql

Write-Host "=== PROCESO COMPLETADO EXITOSAMENTE ===" -ForegroundColor Green
Write-Host "La tabla 'gps_total' ha sido poblada con las georreferencias de Centroamérica." -ForegroundColor Cyan
