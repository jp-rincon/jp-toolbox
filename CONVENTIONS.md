# Convenciones (jp-toolbox)

## Estructura mínima por proyecto

Cada proyecto vive en `projects/<proyecto>/` y debería tener:

- `docker/README.md` (cómo usar lo de Docker en 30s)
- `notes/README.md` (troubleshooting / decisiones)

## Nombres

- Dockerfiles: `Dockerfile.<stack>.<base>.<detalle>`
  - Ej: `Dockerfile.php53.apache.ubuntu14.wkhtmltopdf`
- Composes: `compose.<detalle>.yml` o `docker-compose.<detalle>.yml`
- Notas: `notes/<tema>.md` cuando el `README.md` crezca demasiado.

## Secrets

- Nunca subas passwords/tokens.
- Usa `.env` local (ignorado) + `.env.example` versionado.
- Si un Dockerfile necesita variables: documéntalas en el `README.md` y referencia el `.env.example`.

## Versionado (tags)

Tags sugeridos (ligeros, para volver atrás rápido):

- `vYYYY.MM.DD` (ej. `v2026.05.21`) para “snapshot” estable del toolbox.
- Opcional: `gps_g-vYYYY.MM.DD` si querés marcar cambios puntuales por proyecto.

Regla práctica:
- tagea cuando algo “ya está probado” localmente y no querés volver a romperlo.

