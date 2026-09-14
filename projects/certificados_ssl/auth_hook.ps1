param()

$domain = $env:CERTBOT_DOMAIN
$token = $env:CERTBOT_TOKEN
$validation = $env:CERTBOT_VALIDATION

Write-Host "[AUTH HOOK] Preparando validacion para $domain..." -ForegroundColor Cyan

# Cargar configuracion del servidor
$configFile = Join-Path $PSScriptRoot "config.json"
$config = Get-Content -Path $configFile | ConvertFrom-Json
$srv = $config.Servers | Where-Object { $_.Domain -eq $domain }

if (-not $srv) {
    Write-Error "No se encontro configuracion para $domain en config.json"
    exit 1
}

$sshPort = if ($srv.SshPort) { $srv.SshPort } else { 22 }

# Configurar SSH_ASKPASS con la contrasena
$askpassBat = Join-Path $env:TEMP "ssh_askpass.bat"
"@echo %SSH_PASS%" | Set-Content -Path $askpassBat -Force
$env:SSH_ASKPASS = $askpassBat
$env:SSH_ASKPASS_REQUIRE = "force"
$env:SSH_PASS = $srv.SshPassword

# Crear archivo de token local
$tempFile = Join-Path $env:TEMP $token
[System.IO.File]::WriteAllText($tempFile, $validation)

# Asegurar carpeta remota
Write-Host "    Asegurando directorio remoto en $domain (Puerto $sshPort)..." -ForegroundColor Gray
ssh -o StrictHostKeyChecking=no -p $sshPort "$($srv.SshUser)@$($srv.SshHost)" "mkdir -p '$($srv.WebRoot)/.well-known/acme-challenge'"

# Subir archivo via SCP
$remoteTarget = "$($srv.SshUser)@$($srv.SshHost):$($srv.WebRoot)/.well-known/acme-challenge/$token"
Write-Host "    Subiendo token a $remoteTarget ..." -ForegroundColor Yellow
scp -o StrictHostKeyChecking=no -P $sshPort "$tempFile" "$remoteTarget"

# Verificar publicamente antes de avisar a Let's Encrypt
$verifyUrl = "http://${domain}/.well-known/acme-challenge/$token"
Write-Host "    Verificando token en $verifyUrl ..." -ForegroundColor Cyan

$online = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri $verifyUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        $contentStr = if ($resp.Content -is [byte[]]) {
            [System.Text.Encoding]::UTF8.GetString($resp.Content)
        } else {
            [string]$resp.Content
        }
        if ($contentStr.Trim() -eq $validation.Trim()) {
            $online = $true
            Write-Host "[OK] Token verificado online correctamente (HTTP 200)!" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue

if (-not $online) {
    Write-Host "[X] Error: Token no respondio online en $verifyUrl tras 15 segundos." -ForegroundColor Red
    exit 1
}

exit 0
