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
