# Notas Técnicas - simm_skt

## Inicialización de Base de Datos

### 1. Crear usuario
```sql
CREATE USER tobo_bdg1 WITH PASSWORD 't1o2b3o4_b5d6g718' SUPERUSER;
```

### 2. Restaurar Backup
1. Copiar el archivo al contenedor:
   ```bash
   docker cp bk_simm_gt.sql AdmsimPostgres:/tmp/
   ```
2. Entrar al contenedor y restaurar:
   ```bash
   docker exec -it AdmsimPostgres bash
   # Crear la DB si no existe
   createdb -U postgres simm
   # Restaurar
   psql -U postgres -d simm -v -f /tmp/bk_simm_gt.sql
   ```

## Troubleshooting
- El contenedor de PHP espera las librerías en `C:/Users/rinco/`.