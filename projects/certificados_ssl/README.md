# Proyecto Certificados SSL - Automatización Let's Encrypt

Este proyecto contiene las herramientas para la generación, validación y despliegue automático de certificados SSL Let's Encrypt para servidores virtuales legacy (CentOS / Fedora / otros Linux) desde un entorno Windows.

## Estructura del Proyecto

```text
projects/certificados_ssl/
├── README.md             # Esta documentación
├── config.json           # Configuración de los servidores y dominios
├── renovar_ssl.ps1       # Script principal de PowerShell
└── output/               # Carpeta donde se guardan los certificados generados
```

## Requisitos en Windows

1. **`wacs.exe` (win-acme)**: Instalado en el sistema (ej. `C:\Program Files\win-acme` o agregado al PATH).
2. **OpenSSH Client**: Incluido por defecto en Windows 10/11 (`ssh.exe` y `scp.exe`).

## Configuración de Servidores (`config.json`)

Edita el archivo `config.json` para agregar o modificar los 6 servidores virtuales:

```json
{
  "WacsPath": "wacs.exe",
  "Servers": [
    {
      "Name": "GPS Teleint",
      "Domain": "gps.teleint.co",
      "SshUser": "TU_USUARIO",
      "SshHost": "IP_O_DOMINIO_SSH",
      "SshPort": 22,
      "WebRoot": "/var/www/tobo2",
      "RemoteCertDir": "/etc/httpd/ssl",
      "ReloadCommand": "service httpd reload"
    }
  ]
}
```

## Uso

Abre PowerShell en este directorio y ejecuta:

```powershell
# Para renovar un dominio específico:
.\renovar_ssl.ps1 -Domain "gps.teleint.co"

# Para procesar todos los dominios de config.json:
.\renovar_ssl.ps1 -All
```
