# Docker - laft_g

## Run

1. Copia el archivo `.env.example` a `.env`.
2. Inicia los contenedores:

```bash
docker-compose up -d
```

## Smoke test

1. **Verificar Base de Datos**:
```bash
docker exec -it DuePostgres psql -U postgres -c "SELECT version();"
```

2. **Verificar PHP Apache**:
```bash
docker exec -it due_php_apache php -v
```
Acceder a: `http://localhost:8081/laft_g`

> **Nota de almacenamiento:** La base de datos se guarda en el volumen `DuePostgresData`. Al configurar Docker Desktop con su almacenamiento en el disco `K:`, los datos persistirán allí sin ocupar espacio en `C:`.