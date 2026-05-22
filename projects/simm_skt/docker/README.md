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