param (
    [string]$Token,
    [string]$Content,
    [string]$HostName,
    [string]$SshUser,
    [string]$SshHost,
    [string]$WebRoot
)

Write-Host "[+] Desafío HTTP-01 generado para $HostName" -ForegroundColor Cyan
Write-Host "    Token: $Token" -ForegroundColor Gray

# Crear directorio remoto .well-known/acme-challenge/ si no existe
$remoteDir = "$WebRoot/.well-known/acme-challenge"
$mkdirCmd = "mkdir -p $remoteDir"
Write-Host "    Asegurando directorio remoto: $remoteDir" -ForegroundColor Gray
ssh -o StrictHostKeyChecking=no -p 22 "$SshUser@$SshHost" "$mkdirCmd"

# Crear archivo temporal local con el contenido del token
$tempFile = [System.IO.Path]::GetTempFileName()
Set-Content -Path $tempFile -Value $Content -NoNewline

# Subir archivo vía SCP
$remoteTarget = "$SshUser@${SshHost}:${remoteDir}/${Token}"
Write-Host "    Subiendo desafío por SCP a $remoteTarget ..." -ForegroundColor Yellow
scp -o StrictHostKeyChecking=no "$tempFile" "$remoteTarget"

# Eliminar archivo temporal local
Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue

Write-Host "[✓] Desafío subido con éxito al servidor remoto." -ForegroundColor Green
