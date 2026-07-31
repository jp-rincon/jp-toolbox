# ==============================================================================
# Script PowerShell para descargar, importar y procesar OSM México en Windows
# ==============================================================================

$ErrorActionPreference = "Stop"

$PbfUrl = "https://download.geofabrik.de/north-america/mexico-latest.osm.pbf"
$DataDir = ".\data"
$PbfFile = "$DataDir\mexico-latest.osm.pbf"
$KDataFile = "K:\docker_volumes\data\mexico-latest.osm.pbf"
$DbName = "osm_mexico"
$DbUser = "postgres"
$ContainerName = "osm_centroamerica_gis"
$ExportSql = "K:\gps_total_mexico.sql"
$DumpFile = "K:\docker_volumes\osm_mexico_full.dump"

Write-Host "=== 1. Recreando contenedor Docker ===" -ForegroundColor Green
docker-compose up -d --force-recreate

Write-Host "=== Esperando inicio de PostgreSQL ===" -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 2
    $ready = docker exec $ContainerName pg_isready -U $DbUser 2>$null
} until ($LASTEXITCODE -eq 0)

Write-Host "=== 2. Creando base de datos $DbName si no existe ===" -ForegroundColor Green
$dbExists = (docker exec -i $ContainerName psql -U $DbUser -tAc "SELECT 1 FROM pg_database WHERE datname='$DbName'" 2>$null)
if ($dbExists -and $dbExists.Trim() -eq "1") {
    Write-Host "La base de datos $DbName ya existe." -ForegroundColor Cyan
} else {
    docker exec -i $ContainerName psql -U $DbUser -c "CREATE DATABASE $DbName;"
}

Write-Host "=== 3. Verificando archivo PBF de México ===" -ForegroundColor Green
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir | Out-Null
}

if (-not (Test-Path $PbfFile)) {
    if (Test-Path $KDataFile) {
        Write-Host "Copiando $KDataFile a $PbfFile..." -ForegroundColor Yellow
        Copy-Item $KDataFile $PbfFile -Force
    } else {
        Write-Host "Descargando extracto PBF de México desde Geofabrik..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $PbfUrl -OutFile $PbfFile
    }
} else {
    Write-Host "El archivo $PbfFile ya existe. Omitiendo descarga." -ForegroundColor Cyan
}

Write-Host "=== 4. Habilitando extensiones y limpiando tablas previas ===" -ForegroundColor Green
"DROP TABLE IF EXISTS planet_osm_point, planet_osm_line, planet_osm_polygon, planet_osm_roads, planet_osm_nodes, planet_osm_ways, planet_osm_rels CASCADE; CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS hstore; CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS ""uuid-ossp""; CREATE EXTENSION IF NOT EXISTS h3;" | docker exec -i $ContainerName psql -U $DbUser -d $DbName

Write-Host "=== 5. Importando PBF con osm2pgsql ===" -ForegroundColor Green
docker exec -i $ContainerName osm2pgsql -d $DbName -U $DbUser --create --slim --hstore --multi-geometry /data/mexico-latest.osm.pbf

Write-Host "=== 6. Ejecutando transformación de georreferencias (osm_calles_mx.sql) ===" -ForegroundColor Green
docker exec -i $ContainerName psql -U $DbUser -d $DbName -f /scripts/osm_calles_mx.sql

Write-Host "=== 7. Exportando respaldos finales a disco K: ===" -ForegroundColor Green
Write-Host "Generando dump de tabla geo_total -> $ExportSql..." -ForegroundColor Yellow
docker exec $ContainerName pg_dump -U $DbUser -d $DbName -t geo_total --clean > $ExportSql

Write-Host "Generando dump completo de base de datos -> $DumpFile..." -ForegroundColor Yellow
docker exec $ContainerName pg_dump -U $DbUser -d $DbName -Fc -f /data/osm_mexico_full.dump
if (Test-Path "$DataDir\osm_mexico_full.dump") {
    Move-Item -Path "$DataDir\osm_mexico_full.dump" -Destination $DumpFile -Force
}

Write-Host "=== PROCESO COMPLETADO EXITOSAMENTE ===" -ForegroundColor Green
Write-Host "La tabla 'geo_total' ha sido poblada y respaldada en K:\" -ForegroundColor Cyan
