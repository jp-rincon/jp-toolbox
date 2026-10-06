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

## Almacenamiento y Disco Externo (K:)

Dado que el disco principal `C:` tiene capacidad limitada, seguimos esta estrategia:

1. **Ubicación de datos de Docker Desktop**:
   - Todo el motor de Docker (imágenes, capas y named volumes) se configura para vivir en el disco externo en `Settings -> Resources -> Advanced -> Disk image location` apuntando a `K:\Docker\disk`.
   - **Bases de datos (PostgreSQL/MySQL)**: Usa siempre **Docker Named Volumes** (ej. `Tobo3PostgresData`, `DuePostgresData`, `citus_data_container`). Al estar dentro del disco virtual en `K:`, tienen soporte POSIX nativo de Linux (permisos `0700`, usuario `postgres`), evitando los errores de permisos que ocurren al hacer bind-mount directo en carpetas NTFS de Windows.

2. **Archivos masivos fuera de Docker (Dumps SQL, .osm.pbf, etc.)**:
   - Nunca guardes dumps ni datasets masivos dentro del repo en `C:`.
   - Parametriza en `docker-compose.yml` y `.env.example` una variable de ruta (ej. `GEO_DATA_PATH=K:/geo_centroamerica/data` o `BACKUP_DIR=K:/citus_data/backup`).
   - Usa barras diagonales (`/`) en las rutas de Windows en docker-compose (ej: `K:/carpeta/datos`).


