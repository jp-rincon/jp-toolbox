param (
    [string]$Domain,
    [switch]$All,
    [string]$ConfigFile = "$PSScriptRoot\config.json"
)

# Cargar configuración
if (-not (Test-Path $ConfigFile)) {
    Write-Error "No se encontró el archivo de configuración: $ConfigFile"
    exit 1
}

$config = Get-Content -Path $ConfigFile | ConvertFrom-Json

# Runner de Certbot sin restricción de administrador
$certbotRunner = Join-Path $PSScriptRoot "run_certbot.py"

# Helper para SSH_ASKPASS con contraseñas
$askpassBat = Join-Path $env:TEMP "ssh_askpass.bat"
"@echo %SSH_PASS%" | Set-Content -Path $askpassBat -Force

# Filtrar servidores a procesar
$targetServers = @()
if ($All) {
    $targetServers = $config.Servers
} elseif ($Domain) {
    $targetServers = $config.Servers | Where-Object { $_.Domain -eq $Domain }
    if ($targetServers.Count -eq 0) {
        Write-Error "No se encontró ningún servidor configurado para el dominio: $Domain"
        exit 1
    }
} else {
    Write-Host "Uso:" -ForegroundColor Yellow
    Write-Host "  .\renovar_ssl.ps1 -Domain 'gps.teleint.co'" -ForegroundColor Cyan
    Write-Host "  .\renovar_ssl.ps1 -All" -ForegroundColor Cyan
    exit 0
}

# Procesar cada servidor
foreach ($srv in $targetServers) {
    $sshPort = if ($srv.SshPort) { $srv.SshPort } else { 22 }

    # Configurar autenticación por contraseña vía SSH_ASKPASS
    if ($srv.SshPassword) {
        $env:SSH_ASKPASS         = $askpassBat
        $env:SSH_ASKPASS_REQUIRE = "force"
        $env:SSH_PASS            = $srv.SshPassword
    } else {
        $env:SSH_ASKPASS         = $null
        $env:SSH_ASKPASS_REQUIRE = $null
        $env:SSH_PASS            = $null
    }

    Write-Host "`n========================================================" -ForegroundColor Cyan
    Write-Host " PROCESANDO SSL PARA: $($srv.Name) ($($srv.Domain))" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Cyan

    $outputDir = Join-Path "$PSScriptRoot\output" $srv.Domain
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }

    # Resolver rutas remotas finales adecuadamente si son absolutas o relativas
    function Resolve-RemotePath ($baseDir, $specifiedFile, $defaultFile) {
        if ($specifiedFile) {
            if ($specifiedFile.StartsWith("/")) {
                return $specifiedFile
            } else {
                return "$baseDir/$specifiedFile"
            }
        }
        return "$baseDir/$defaultFile"
    }

    $remoteCertPath  = Resolve-RemotePath $srv.RemoteCertDir $srv.RemoteCertFile "certificate.crt"
    $remoteKeyPath   = Resolve-RemotePath $srv.RemoteCertDir $srv.RemoteKeyFile "private.key"
    $remoteChainPath = Resolve-RemotePath $srv.RemoteCertDir $srv.RemoteChainFile "ca-bundle.crt"

    Write-Host "[1/3] Generando y validando certificado con Certbot..." -ForegroundColor Cyan

    $authHookBat  = Join-Path $PSScriptRoot "run_auth_hook.bat"
    $cleanHookBat = Join-Path $PSScriptRoot "run_cleanup_hook.bat"
    $configDir    = Join-Path $PSScriptRoot "certbot\config"
    $workDir      = Join-Path $PSScriptRoot "certbot\work"
    $logsDir      = Join-Path $PSScriptRoot "certbot\logs"

    $certbotArgs = @(
        $certbotRunner,
        "certonly",
        "--manual",
        "--preferred-challenges", "http",
        "-d", $srv.Domain,
        "--manual-auth-hook", "`"$authHookBat`"",
        "--manual-cleanup-hook", "`"$cleanHookBat`"",
        "--config-dir", "`"$configDir`"",
        "--work-dir", "`"$workDir`"",
        "--logs-dir", "`"$logsDir`"",
        "--agree-tos",
        "-m", "rincon.juanpablo@gmail.com",
        "--non-interactive"
    )

    Write-Host "    Ejecutando: python $($certbotArgs -join ' ')" -ForegroundColor Gray
    $proc = Start-Process -FilePath "python" -ArgumentList $certbotArgs -Wait -NoNewWindow -PassThru

    $liveDir = Join-Path $configDir "live\$($srv.Domain)"
    $fullchainFile = Join-Path $liveDir "fullchain.pem"
    $privkeyFile   = Join-Path $liveDir "privkey.pem"
    $chainFile     = Join-Path $liveDir "chain.pem"

    if (Test-Path $fullchainFile) {
        Write-Host "`n[✓] ¡Certificado obtenido exitosamente por Certbot!" -ForegroundColor Green
        
        # Guardar copia en output local
        Copy-Item -Path $fullchainFile -Destination (Join-Path $outputDir "fullchain.pem") -Force
        Copy-Item -Path $privkeyFile -Destination (Join-Path $outputDir "privkey.pem") -Force
        if (Test-Path $chainFile) {
            Copy-Item -Path $chainFile -Destination (Join-Path $outputDir "chain.pem") -Force
        }

        # Despliegue remoto
        Write-Host "`n[2/3] Desplegando archivos de certificado a $($srv.SshHost) (Puerto $sshPort)..." -ForegroundColor Cyan
        
        $remoteCertFolder = [System.IO.Path]::GetDirectoryName($remoteCertPath).Replace('\','/')
        ssh -o StrictHostKeyChecking=no -p $sshPort "$($srv.SshUser)@$($srv.SshHost)" "mkdir -p '$remoteCertFolder'"

        Write-Host "    Subiendo certificado: fullchain.pem -> $remoteCertPath" -ForegroundColor Yellow
        scp -o StrictHostKeyChecking=no -P $sshPort "$fullchainFile" "$($srv.SshUser)@$($srv.SshHost):$remoteCertPath"

        Write-Host "    Subiendo llave privada: privkey.pem -> $remoteKeyPath" -ForegroundColor Yellow
        scp -o StrictHostKeyChecking=no -P $sshPort "$privkeyFile" "$($srv.SshUser)@$($srv.SshHost):$remoteKeyPath"

        if (Test-Path $chainFile) {
            Write-Host "    Subiendo cadena intermedia: chain.pem -> $remoteChainPath" -ForegroundColor Yellow
            scp -o StrictHostKeyChecking=no -P $sshPort "$chainFile" "$($srv.SshUser)@$($srv.SshHost):$remoteChainPath"
        }

        Write-Host "`n[3/3] Recargando servidor web remoto ($($srv.ReloadCommand))..." -ForegroundColor Cyan
        $reloadOutput = ssh -o StrictHostKeyChecking=no -p $sshPort "$($srv.SshUser)@$($srv.SshHost)" "$($srv.ReloadCommand)" 2>&1
        Write-Host "    Respuesta del servidor remoto:" -ForegroundColor Gray
        Write-Host "    $reloadOutput" -ForegroundColor White
        
        Write-Host "[✓] ¡Proceso completado exitosamente para $($srv.Domain)!" -ForegroundColor Green
    } else {
        Write-Host "`n[X] Error: Certbot no pudo generar el certificado. Código de salida: $($proc.ExitCode)" -ForegroundColor Red
    }
}
