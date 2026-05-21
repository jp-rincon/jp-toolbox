# Docker (gps_g)

## Imagen PHP 5.3 + Apache + wkhtmltopdf

Este build está pensado para una base antigua tipo `corvax19/php5.3.10-apache2.2.22-ubuntu14` (Ubuntu EOL).
El Dockerfile ajusta los repos a `old-releases.ubuntu.com` e instala `wkhtmltopdf` + fonts/libs.

Archivos relacionados:
- `Dockerfile.php53.apache.ubuntu14.wkhtmltopdf` (recomendado)
- `Dockerfile.php53-wkhtmltopdf.legacy` (copia del Dockerfile original con nombre anterior)
- `README-wkhtmltopdf.legacy.md` (copia del README original con instrucciones de build/run)

### Build

```bash
docker build --no-cache -f Dockerfile.php53.apache.ubuntu14.wkhtmltopdf -t gps_g:php53-wkhtml .
```

### Run (ejemplo)

```bash
docker run -d -p 8081:80 \
  -v C:\\Users\\rinco\\gps_g:/var/www/gps_g \
  --name gps_g_php53 \
  gps_g:php53-wkhtml
```

### Smoke test (wkhtmltopdf)

```bash
docker exec -it gps_g_php53 bash -lc "wkhtmltopdf about:blank /tmp/test.pdf && ls -la /tmp/test.pdf"
```
