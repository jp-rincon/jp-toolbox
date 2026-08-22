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
$wacsBin = $config.WacsPath

# Verificar wacs.exe
if (-not (Get-Command $wacsBin -ErrorAction SilentlyContinue)) {
    $commonPaths = @(
        "C:\win-acme\wacs.exe",
        "C:\Program Files\win-acme\wacs.exe",
        "$env:LOCALAPPDATA\win-acme\wacs.exe"
    )
    $found = $false
    foreach ($p in $commonPaths) {
        if (Test-Path $p) {
            $wacsBin = $p
            $found = $true
            break
        }
    }
    if (-not $found) {
        Write-Host "[!] ADVERTENCIA: No se encontró 'wacs.exe' automáticamente." -ForegroundColor Yellow
        Write-Host "    Asegúrate de configurar la ruta correcta de 'wacs.exe' en config.json" -ForegroundColor Gray
    }
}

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

    # Carpeta temporal local para validación filesystem
    $tempChallengeRoot = Join-Path $PSScriptRoot "temp_challenge"
    $acmeChallengeDir  = Join-Path $tempChallengeRoot ".well-known\acme-challenge"
    if (-not (Test-Path $acmeChallengeDir)) {
        New-Item -ItemType Directory -Path $acmeChallengeDir -Force | Out-Null
    }

    Write-Host "[1/4] Activando monitor de subida SCP automática..." -ForegroundColor Cyan
    
    # Configurar FileSystemWatcher para subir automáticamente el token cuando wacs lo cree
    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $acmeChallengeDir
    $watcher.Filter = "*.*"
    $watcher.IncludeSubdirectories = $false
    $watcher.EnableRaisingEvents = $true

    $action = {
        $filePath = $Event.SourceEventArgs.FullPath
        $fileName = $Event.SourceEventArgs.Name
        $msgData  = $Event.MessageData

        Write-Host "`n[+] Token de desafío detectado: $fileName" -ForegroundColor Yellow
        Write-Host "    Asegurando directorio remoto en puerto $($msgData.Port)..." -ForegroundColor Gray
        ssh -o StrictHostKeyChecking=no -p $msgData.Port "$($msgData.User)@$($msgData.Host)" "mkdir -p '$($msgData.WebRoot)/.well-known/acme-challenge'"

        Write-Host "    Subiendo token por SCP a $($msgData.Host):$($msgData.WebRoot)/.well-known/acme-challenge/$fileName ..." -ForegroundColor Yellow
        scp -o StrictHostKeyChecking=no -P $msgData.Port "$filePath" "$($msgData.User)@$($msgData.Host):$($msgData.WebRoot)/.well-known/acme-challenge/$fileName"
        Write-Host "[✓] Token subido con éxito al servidor remoto!" -ForegroundColor Green
    }

    $eventData = @{
        Port    = $sshPort
        User    = $srv.SshUser
        Host    = $srv.SshHost
        WebRoot = $srv.WebRoot
    }

    $eventSub = Register-ObjectEvent $watcher Created -Action $action -MessageData $eventData

    Write-Host "[2/4] Solicitando certificado a Let's Encrypt vía wacs.exe ..." -ForegroundColor Cyan

    $wacsArgs = @(
        "--target", "manual",
        "--host", $srv.Domain,
        "--validation", "filesystem",
        "--webroot", "$tempChallengeRoot",
        "--store", "pemfiles",
        "--pemfilespath", "$outputDir",
        "--accepttos"
    )

    Write-Host "    Comando: $wacsBin $($wacsArgs -join ' ')" -ForegroundColor Gray

    # Ejecutar wacs
    $proc = Start-Process -FilePath $wacsBin -ArgumentList $wacsArgs -Wait -NoNewWindow -PassThru

    # Limpiar monitor de eventos
    Unregister-Event -SourceIdentifier $eventSub.Name -ErrorAction SilentlyContinue
    $watcher.Dispose()

    if ($proc.ExitCode -eq 0 -or (Test-Path "$outputDir\*key*.pem") -or (Test-Path "$outputDir\*.crt") -or (Test-Path "$outputDir\*.pem")) {
        Write-Host "`n[✓] Certificado obtenido correctamente en $outputDir" -ForegroundColor Green
    } else {
        Write-Host "`n[!] ADVERTENCIA: wacs.exe finalizó con código $($proc.ExitCode)." -ForegroundColor Yellow
    }

    # Despliegue remoto si existen archivos en outputDir
    Write-Host "`n[3/4] Desplegando archivos de certificado a $($srv.SshHost) (Puerto $sshPort)..." -ForegroundColor Cyan
    
    $crtFile   = Get-ChildItem -Path $outputDir -Include "*-crt.pem","*.crt" -Recurse | Select-Object -First 1
    $keyFile   = Get-ChildItem -Path $outputDir -Include "*-key.pem","*.key" -Recurse | Select-Object -First 1
    $chainFile = Get-ChildItem -Path $outputDir -Include "*-chain.pem","ca-bundle.crt" -Recurse | Select-Object -First 1

    if ($crtFile -and $keyFile) {
        # Asegurar directorio remoto de destino
        $remoteCertFolder = [System.IO.Path]::GetDirectoryName($remoteCertPath).Replace('\','/')
        ssh -o StrictHostKeyChecking=no -p $sshPort "$($srv.SshUser)@$($srv.SshHost)" "mkdir -p '$remoteCertFolder'"

        Write-Host "    Subiendo certificado: $($crtFile.Name) -> $remoteCertPath" -ForegroundColor Yellow
        scp -o StrictHostKeyChecking=no -P $sshPort "$($crtFile.FullName)" "$($srv.SshUser)@$($srv.SshHost):$remoteCertPath"

        Write-Host "    Subiendo llave privada: $($keyFile.Name) -> $remoteKeyPath" -ForegroundColor Yellow
        scp -o StrictHostKeyChecking=no -P $sshPort "$($keyFile.FullName)" "$($srv.SshUser)@$($srv.SshHost):$remoteKeyPath"

        if ($chainFile) {
            Write-Host "    Subiendo cadena intermedia: $($chainFile.Name) -> $remoteChainPath" -ForegroundColor Yellow
            scp -o StrictHostKeyChecking=no -P $sshPort "$($chainFile.FullName)" "$($srv.SshUser)@$($srv.SshHost):$remoteChainPath"
        }

        Write-Host "`n[4/4] Recargando servidor web remoto ($($srv.ReloadCommand))..." -ForegroundColor Cyan
        $reloadOutput = ssh -o StrictHostKeyChecking=no -p $sshPort "$($srv.SshUser)@$($srv.SshHost)" "$($srv.ReloadCommand)" 2>&1
        Write-Host "    Respuesta del servidor remoto:" -ForegroundColor Gray
        Write-Host "    $reloadOutput" -ForegroundColor White
        
        Write-Host "[✓] ¡Proceso completado exitosamente para $($srv.Domain)!" -ForegroundColor Green
    } else {
        Write-Host "[X] No se encontraron los archivos de certificado en $outputDir para transferir." -ForegroundColor Red
    }
}
