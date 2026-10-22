param (
    [Parameter(Mandatory=$true)]
    [string]$Domain
)

$certbotRunner = Join-Path $PSScriptRoot "run_certbot.py"
$configDir    = Join-Path $PSScriptRoot "certbot\config"
$workDir      = Join-Path $PSScriptRoot "certbot\work"
$logsDir      = Join-Path $PSScriptRoot "certbot\logs"
$outputDir    = Join-Path $PSScriptRoot "output\$Domain"

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " SOLICITUD SSL VIA DNS PARA: $Domain" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "1. Certbot te mostrara en pantalla un registro TXT." -ForegroundColor Yellow
Write-Host "2. Agrega ese registro en cPanel (Zone Editor)." -ForegroundColor Yellow
Write-Host "3. Espera unos 30-60 segundos para propagacion y luego presiona Enter aqui.`n" -ForegroundColor Yellow

# Ejecutar Certbot de forma interactiva
python $certbotRunner certonly --manual --preferred-challenges dns -d $Domain --config-dir "$configDir" --work-dir "$workDir" --logs-dir "$logsDir" --agree-tos

$liveDir = Join-Path $configDir "live\$Domain"
$fullchainFile = Join-Path $liveDir "fullchain.pem"
$privkeyFile   = Join-Path $liveDir "privkey.pem"

if (Test-Path $fullchainFile) {
    Copy-Item -Path $fullchainFile -Destination (Join-Path $outputDir "fullchain.pem") -Force
    Copy-Item -Path $privkeyFile -Destination (Join-Path $outputDir "privkey.pem") -Force
    
    Write-Host "`n[OK] Certificado generado exitosamente!" -ForegroundColor Green
    Write-Host "Archivos listos en: $outputDir" -ForegroundColor Cyan
    Write-Host "  - fullchain.pem  (Para ssl_certificate en nginx)" -ForegroundColor White
    Write-Host "  - privkey.pem    (Para ssl_certificate_key en nginx)" -ForegroundColor White
    Write-Host "`nAbriendo carpeta en el Explorador para copiar por RDP..." -ForegroundColor Gray
    
    explorer.exe "$outputDir"
} else {
    Write-Host "`n[X] No se completo la generacion del certificado." -ForegroundColor Red
}
