# ==============================================================================
# Script PowerShell para descargar, importar y procesar OSM Panamá en Windows
# ==============================================================================

$ErrorActionPreference = "Stop"

$PbfUrl = "https://download.geofabrik.de/central-america/panama-latest.osm.pbf"
$DataDir = ".\data"
$PbfFile = "$DataDir\panama-latest.osm.pbf"
$DbName = "osm_panama"
$DbUser = "postgres"
$ContainerName = "osm_centroamerica_gis"

Write-Host "=== 1. Verificando contenedor Docker ===" -ForegroundColor Green
docker-compose up -d

Write-Host "=== Esperando inicio de PostgreSQL ===" -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 2
    $ready = docker exec $ContainerName pg_isready -U $DbUser 2>$null
} until ($LASTEXITCODE -eq 0)

Write-Host "=== 2. Descargando datos OSM de Panamá ===" -ForegroundColor Green
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir | Out-Null
}

if (-not (Test-Path $PbfFile)) {
    Write-Host "Descargando extracto PBF desde Geofabrik..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $PbfUrl -OutFile $PbfFile
} else {
    Write-Host "El archivo $PbfFile ya existe. Omitiendo descarga." -ForegroundColor Cyan
}

Write-Host "=== 3. Preparando base de datos y extensiones ===" -ForegroundColor Green
docker exec $ContainerName psql -U $DbUser -c "CREATE DATABASE $DbName;" 2>$null
Get-Content ../scripts/init_osm_panama.py | python

Write-Host "=== 4. Importando PBF con osm2pgsql ===" -ForegroundColor Green
docker exec -i $ContainerName osm2pgsql -d $DbName -U $DbUser --create --slim --hstore --multi-geometry /data/panama-latest.osm.pbf

Write-Host "=== 5. Ejecutando transformación de complemento (osm_calles_pa_complemento.sql) ===" -ForegroundColor Green
Get-Content ../scripts/osm_calles_pa_complemento.sql -Raw | docker exec -i $ContainerName psql -U $DbUser -d $DbName

Write-Host "=== 6. Transfiriendo a tobodb.geo_total ===" -ForegroundColor Green
python ../scripts/transferir_complemento_panama.py

Write-Host "=== PROCESO COMPLETADO EXITOSAMENTE ===" -ForegroundColor Green
