# wkhtmltopdf para `corvax19/php5.3.10-apache2.2.22-ubuntu14`

La imagen base es Ubuntu 14.04 (EOL). Por eso `apt-get update` suele fallar en 2025/2026 y hay que apuntar a `old-releases.ubuntu.com`.
En algunas variantes antiguas puede venir como Ubuntu 12.04 (precise); en ese caso los paquetes de fonts suelen llamarse `ttf-*` en vez de `fonts-*` (el Dockerfile ya contempla ambas opciones).

## Build

Desde la raíz del repo:

```bash
docker build --no-cache -f docker/Dockerfile.php53-wkhtmltopdf -t php5.3_apache_dtk_pdf:wkhtml .
```

## Run (equivalente a tu `docker run`)

```bash
docker run -d -p 8081:80 -v C:\\Users\\rinco\\gps_g:/var/www/gps_g -v C:\\Users\\rinco\\basura:/var/www/basura -v C:\\Users\\rinco\\tcpdf:/var/www/tcpdf --name php5.3_apache_dtk_pdf --hostname php5.3_apache_dtk_pdf php5.3_apache_dtk_pdf:wkhtml
```

## Pruebas rápidas dentro del contenedor

1) Ver versión:
```bash
docker exec -it php5.3_apache_dtk_pdf wkhtmltopdf --version
```

2) Generar un PDF mínimo (descarta problemas de tu app):
```bash
docker exec -it php5.3_apache_dtk_pdf bash -lc "wkhtmltopdf about:blank /tmp/test.pdf && ls -la /tmp/test.pdf"
```

Si `/tmp/test.pdf` existe y pesa > 0 bytes, `wkhtmltopdf` está ok y ya podés probar el export desde PHP.
