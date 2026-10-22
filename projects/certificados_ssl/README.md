# Gestor y Renovador de Certificados SSL (Let's Encrypt)

Herramienta centralizada para generar, renovar y desplegar certificados SSL Let's Encrypt tanto en servidores Linux (automáticos vía SSH/SCP) como en servidores Windows (semi-automáticos vía DNS y RDP).

---

## Modos de Operación

| Servidor / Dominio | Sistema Operativo | Servidor Web | Tipo de Validación | Despliegue |
|---|---|---|---|---|
| `gps.teleint.co` | Linux (Legacy) | Apache | HTTP-01 (Automático vía SCP) | Automático (SSH + reload) |
| `keyro.honshutech.com` | Linux (Legacy) | Apache | HTTP-01 (Automático vía SCP) | Automático (SSH + reload) |
| `ecolab.net.co` | Linux (Legacy) | Apache | HTTP-01 (Automático vía SCP) | Automático (SSH + reload) |
| `video.teiko.com.co` | Windows | Nginx | DNS-01 (TXT en cPanel) | Manual (Copiar por RDP + `nginx -s reload`) |

---

## Comandos de Uso

Abre PowerShell en esta carpeta (`projects/certificados_ssl/`) y ejecuta:

### 1. Renovar un dominio específico
```powershell
# Para servidores Linux automáticos:
.\renovar_ssl.ps1 -Domain "gps.teleint.co"
.\renovar_ssl.ps1 -Domain "keyro.honshutech.com"
.\renovar_ssl.ps1 -Domain "ecolab.net.co"

# Para servidor Windows (DNS manual):
.\renovar_ssl.ps1 -Domain "video.teiko.com.co"
```

### 2. Procesar todos los servidores configurados
```powershell
.\renovar_ssl.ps1 -All
```

---

## Guía Paso a Paso: `video.teiko.com.co` (Windows / Nginx)

Cuando llegue la fecha de vencimiento (cada 3 meses), el proceso es el siguiente:

1. **Ejecuta en PowerShell:**
   ```powershell
   .\renovar_ssl.ps1 -Domain "video.teiko.com.co"
   ```
2. **Certbot pausará la pantalla** y te mostrará el valor del registro TXT, por ejemplo:
   - Nombre: `_acme-challenge.video.teiko.com.co.`
   - Valor TXT: `(cadena alfanumérica única)`
   > *No presiones Enter aún.*
3. **En cPanel:**
   - Ve a **Zone Editor** (Editor de Zona DNS) para el dominio `teiko.com.co`.
   - Edita el registro TXT existente `_acme-challenge.video.teiko.com.co` o crea uno nuevo con el valor proporcionado por Certbot.
   - Guarda los cambios y espera unos 30-45 segundos a que propague.
4. **Vuelve a la consola de PowerShell y presiona Enter:**
   - Certbot validará el registro ante Let's Encrypt.
   - El script abrirá automáticamente la carpeta del Explorador de Windows:
     `projects/certificados_ssl/output/video.teiko.com.co/`
     con los archivos:
     - `fullchain.pem`
     - `privkey.pem`
5. **En el servidor Windows (por Escritorio Remoto / RDP):**
   - Conéctate por RDP.
   - Copia y pega ambos archivos en la carpeta de certificados de Nginx (donde apunten `ssl_certificate` y `ssl_certificate_key`).
   - Abre un Command Prompt (cmd) o PowerShell en el servidor Windows y ejecuta:
     ```cmd
     nginx -s reload
     ```
   ¡Listo! El sitio web quedará renovado por otros 90 días.

---

## Estructura de Archivos

```text
projects/certificados_ssl/
├── config.json              # Configuración de todos los servidores y credenciales
├── config.json.example      # Plantilla de ejemplo sin contraseñas
├── renovar_ssl.ps1          # Orquestador principal (maneja tanto HTTP como DNS)
├── solicitar_ssl_dns.ps1    # Sub-script interactivo para validación DNS-01
├── run_certbot.py           # Runner de Certbot con parches de permisos Windows
├── auth_hook.ps1            # Hook de subida SCP para HTTP-01
├── cleanup_hook.ps1         # Hook de limpieza para HTTP-01
└── output/                  # Carpeta donde quedan las copias de los certificados
```
