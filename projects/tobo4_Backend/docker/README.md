# tobo4_Backend - Stack Completo Docker (Citus, Redis, RabbitMQ, TCP Relay)

## Qué resuelve

Levanta el stack completo de soporte para Tobo4 Backend:
1. **Citus / PostgreSQL (`citusdata/citus:12.1`)**: Base de datos principal `tobodb` con extensión Citus.
2. **Redis (`redis:7-alpine`)**: Caché y mensajería en memoria en el puerto `6379`.
3. **RabbitMQ (`rabbitmq:3.8-management`)**: Broker de colas en el puerto `5672` (Panel web: `http://localhost:15672`).
4. **WebSocket TCP Relay (`cloudamqp/websocket-tcp-relay`)**: Relay de websockets a RabbitMQ en el puerto `15670`.

- **Almacenamiento en disco externo (K:)**: Todos los datos vivos residen en Docker Named Volumes (`citus_data_container`, `redis_data`, `rabbitmq_data`), los cuales están ubicados dentro del disco virtual en `K:\Docker\disk\DockerDesktopWSL\disk\docker_data.vhdx`, protegiendo el espacio del disco `C:`.
- **Dumps y backups**: Se leen desde el disco externo `K:\citus_data\backup`, montado dentro del contenedor en `/backup_dir`.

## Configuración rápida

1. Copia `.env.example` a `.env` (o usa el ya generado):
   ```bash
   cp .env.example .env
   ```
2. Asegúrate de tener conectado el disco externo `K:`.

## Comandos

### Iniciar el stack
```bash
docker compose up -d
```

### Ver estado y logs
```bash
docker compose ps
docker compose logs -f
docker compose logs -f citus
```

### Detener el stack
```bash
docker compose down
```

## Restauración de Backup en PostgreSQL (tobodb)

El archivo de backup `bk_tobodb_co_2026_07_parcial.tar.gz` en `K:\citus_data\backup` se encuentra montado en `/backup_dir/`.

Para restaurar en la base de datos `tobodb`:

```bash
# 1. Crear la base tobodb (si no existe)
docker exec -i citus_postgres psql -U postgres -c "CREATE DATABASE tobodb;"

# 2. Habilitar extensión citus
docker exec -i citus_postgres psql -U postgres -d tobodb -c "CREATE EXTENSION IF NOT EXISTS citus;"

# 3. Restaurar según formato del dump:
# Si es formato directorio comprimido:
docker exec -i citus_postgres bash -c "tar -xzf /backup_dir/bk_tobodb_co_2026_07_parcial.tar.gz -C /tmp && pg_restore -U postgres -d tobodb -v /tmp/bk_tobodb_co_2026_07_parcial"
```
