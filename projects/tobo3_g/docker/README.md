# Docker - tobo3_g

## Run

1. Copia el archivo `.env.example` a `.env`.
2. Inicia los contenedores:

```bash
docker-compose up -d
```

## Smoke test

1. **Verificar Base de Datos**:
```bash
docker exec -it Tobo3Postgres psql -U postgres -c "SELECT version();"
```

2. **Verificar PHP 5.3**:
```bash
docker exec -it tobo3_php_apache php -v
```
Acceder a: `http://localhost:8082/tobo3_g`

> **Nota de almacenamiento:** La base de datos se guarda en el volumen `Tobo3PostgresData`. Al configurar Docker Desktop con su almacenamiento en el disco `K:`, los datos persistirán allí sin ocupar espacio en `C:`. Si vas a restaurar un dump grande (`tobo_master_v1...sql.zp`), asegúrate de guardarlo en `K:` antes de pasarlo al contenedor.

