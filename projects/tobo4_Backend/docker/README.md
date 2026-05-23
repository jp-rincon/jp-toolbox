# Docker

## Qué resuelve

- Describe en 1–2 líneas qué problema resuelve este Dockerfile/compose.

## Build

```bash
# ejemplo
docker build -t <tag> .
```

## Run

```bash
# ejemplo
docker run --rm -it <tag> bash
```

## Smoke test

Incluye un test simple que valide lo “crítico” (p. ej. `wkhtmltopdf --version`).

