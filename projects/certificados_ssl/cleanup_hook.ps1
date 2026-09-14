param()

$domain = $env:CERTBOT_DOMAIN
$token = $env:CERTBOT_TOKEN

$configFile = Join-Path $PSScriptRoot "config.json"
$config = Get-Content -Path $configFile | ConvertFrom-Json
$srv = $config.Servers | Where-Object { $_.Domain -eq $domain }

if ($srv) {
    $sshPort = if ($srv.SshPort) { $srv.SshPort } else { 22 }
    $askpassBat = Join-Path $env:TEMP "ssh_askpass.bat"
    $env:SSH_ASKPASS = $askpassBat
    $env:SSH_ASKPASS_REQUIRE = "force"
    $env:SSH_PASS = $srv.SshPassword

    ssh -o StrictHostKeyChecking=no -p $sshPort "$($srv.SshUser)@$($srv.SshHost)" "rm -f '$($srv.WebRoot)/.well-known/acme-challenge/$token'" 2>&1 | Out-Null
}

exit 0
