# Docker - simm_skt

## Run

1. Copia el archivo `.env.example` a `.env`.
2. Inicia los contenedores:

```bash
docker-compose up -d
```

## Smoke test

1. **Verificar Base de Datos**:
```bash
docker exec -it AdmsimPostgres psql -U postgres -c "SELECT version();"
```

2. **Verificar PHP**:
```bash
docker exec -it admsim_php_apache php -v
```

> **Nota de almacenamiento:** La base de datos se guarda en el volumen `AdmsimPostgresData`. Al configurar Docker Desktop con su almacenamiento en el disco `K:`, los datos persistirán allí sin ocupar espacio en `C:`. Si vas a restaurar un dump grande (`bk_simm_gt.sql`), consérvalo en `K:` antes de cargarlo al contenedor.