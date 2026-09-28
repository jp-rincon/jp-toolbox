# ==============================================================================
# Script PowerShell para descargar, importar y procesar complemento de Colombia
# Archivo: run_pipeline_co.ps1
# Creado para: Usuario 5004 - Relleno seguro de celdas H7 sin sobreescritura
# ==============================================================================

$ErrorActionPreference = "Stop"

$PbfUrl = "https://download.geofabrik.de/south-america/colombia-latest.osm.pbf"
$DataDir = ".\data"
$PbfFile = "$DataDir\colombia-latest.osm.pbf"
$KDataFile = "K:\docker_volumes\data\colombia-latest.osm.pbf"
$CeldasCsv = "$DataDir\celdas_existentes_co.csv"
$DbName = "osm_colombia"
$DbUser = "postgres"
$ContainerName = "osm_centroamerica_gis"
$ExportSql = "K:\geo_col_complemento_2026.sql"

Write-Host "=== 1. Verificando contenedor Docker GIS ($ContainerName) ===" -ForegroundColor Green
docker-compose up -d

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

Write-Host "=== 3. Verificando archivo PBF de Colombia en disco K: ===" -ForegroundColor Green
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir | Out-Null
}

if (-not (Test-Path $PbfFile)) {
    if (Test-Path $KDataFile) {
        Write-Host "Copiando archivo existente desde $KDataFile..." -ForegroundColor Yellow
        Copy-Item $KDataFile $PbfFile -Force
    } else {
        Write-Host "Descargando extracto PBF de Colombia desde Geofabrik a $KDataFile..." -ForegroundColor Yellow
        if (-not (Test-Path "K:\docker_volumes\data")) {
            New-Item -ItemType Directory -Path "K:\docker_volumes\data" | Out-Null
        }
        # Descarga directa en K: y copia local
        curl.exe -L -o $KDataFile $PbfUrl
        Copy-Item $KDataFile $PbfFile -Force
    }
} else {
    Write-Host "El archivo $PbfFile ya existe en data/. Omitiendo descarga." -ForegroundColor Cyan
}

Write-Host "=== 4. Habilitando extensiones y limpiando tablas intermedias ===" -ForegroundColor Green
"DROP TABLE IF EXISTS planet_osm_point, planet_osm_line, planet_osm_polygon, planet_osm_roads, planet_osm_nodes, planet_osm_ways, planet_osm_rels CASCADE; CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS hstore; CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS ""uuid-ossp""; CREATE EXTENSION IF NOT EXISTS h3;" | docker exec -i $ContainerName psql -U $DbUser -d $DbName

Write-Host "=== 5. Importando PBF con osm2pgsql ===" -ForegroundColor Green
docker exec -i $ContainerName osm2pgsql -d $DbName -U $DbUser --create --slim --hstore --multi-geometry /data/colombia-latest.osm.pbf

Write-Host "=== 6. Ejecutando transformación y filtrado de vacíos (osm_calles_co_complemento.sql) ===" -ForegroundColor Green
docker exec -i $ContainerName psql -U $DbUser -d $DbName -f /scripts/osm_calles_co_complemento.sql

Write-Host "=== 7. Exportando respaldo del complemento a disco K: ($ExportSql) ===" -ForegroundColor Green
docker exec -i $ContainerName pg_dump -U $DbUser -d $DbName -t complemento_final_co --data-only --column-inserts > $ExportSql

Write-Host "=== 8. Inyectando registros complementarios en citus_postgres (tobodb.geo_col) ===" -ForegroundColor Green
# Insertar desde complemento_final_co hacia citus_postgres.tobodb.geo_col
$copyCmd = "COPY complemento_final_co TO STDOUT WITH (FORMAT binary);"
$pasteCmd = "COPY geo_col (id, name, display_name, location, country_code, client_id, color, icon, creation_user, created_at, update_user, updated_at, bbox, h3_cell7, h3_cell5, longitud, latitud) FROM STDIN WITH (FORMAT binary);"

docker exec -i $ContainerName psql -U $DbUser -d $DbName -c "$copyCmd" | docker exec -i citus_postgres psql -U postgres -d tobodb -c "$pasteCmd"

Write-Host "=== PROCESO COMPLETADO EXITOSAMENTE ===" -ForegroundColor Green
Write-Host "Reporte final de celdas H7 en tobodb.geo_col:" -ForegroundColor Cyan
docker exec -i citus_postgres psql -U postgres -d tobodb -c "SELECT country_code, creation_user, count(*) AS total_registros, count(distinct h3_cell7) AS total_celdas_h7 FROM geo_col GROUP BY country_code, creation_user ORDER BY 1, 2;"
