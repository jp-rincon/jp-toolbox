# jp-toolbox

Repo privado para utilidades pequeñas (Dockerfiles, `docker-compose`, scripts y notas) reutilizables entre proyectos.

Objetivo: que estas herramientas **no dependan del disco local** (se versionan en Bitbucket) y no “ensucien” los repos de aplicaciones.

## Quick start

1) Clona este repo:
```bash
git clone <bitbucket-url> jp-toolbox
cd jp-toolbox
```

2) Entra al proyecto que necesites, por ejemplo:
```bash
cd projects/gps_g/docker
```

3) Sigue el `README.md` de esa carpeta (build/run/smoke tests).

## Estructura

- `projects/<proyecto>/docker/`: Dockerfiles y compose del proyecto.
- `projects/<proyecto>/notes/`: notas cortas y troubleshooting.
- `snippets/`: piezas reutilizables (nginx, cron, scripts).
- `templates/`: plantillas base para iniciar rápido.

## Convenciones (resumen)

- **Nombres claros**: `Dockerfile.<stack>.<base>.<detalle>` (ej. `Dockerfile.php53.apache.ubuntu14.wkhtmltopdf`).
- **Nada sensible** en git: usa `.env` (ignorado) + `.env.example`.
- Cada carpeta importante tiene su `README.md` con:
  - build/run
  - pruebas rápidas
  - “qué problema resuelve”

Más detalle en `CONVENTIONS.md`.
