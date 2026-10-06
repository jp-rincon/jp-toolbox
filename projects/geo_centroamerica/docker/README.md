# geo_centroamerica - PostgreSQL 16 + PostGIS + H3 Docker

## Qué resuelve

Contenedor PostgreSQL 16 con PostGIS, osm2pgsql y Uber H3 para procesamiento geográfico de Centroamérica y Colombia.

- La base de datos vive en el volumen Docker `osm_data` (en el disco externo K: si Docker Desktop está configurado para almacenar datos en K:).
- Los archivos `.osm.pbf` (que pesan varios GB) pueden ubicarse en el disco externo K: configurando `GEO_DATA_PATH` en el archivo `.env`.

## Configuración rápida

1. Copia `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
2. Si tienes archivos `.osm.pbf` en `K:\geo_centroamerica\data`, edita `.env`:
   ```env
   GEO_DATA_PATH=K:/geo_centroamerica/data
   ```

## Build & Run

```bash
docker compose up -d --build
```

## Logs & Stop

```bash
docker compose logs -f
docker compose down
```


