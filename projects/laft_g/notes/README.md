# Notas Técnicas - laft_g

## Inicialización de Base de Datos

### 1. Crear usuario
Ejecutar dentro de la consola de psql:
```sql
CREATE USER tobo_bdg1 WITH PASSWORD 't1o2b3o4_b5d6g718' SUPERUSER;
```

### 2. Restaurar Backup
1. Copiar el archivo al contenedor:
   ```bash
   docker cp bk_duediligence_03Ene2024.sql DuePostgres:/tmp/
   ```
2. Entrar al contenedor y restaurar:
   ```bash
   docker exec -it DuePostgres bash
   psql -U postgres -d duediligence -f /tmp/bk_duediligence_03Ene2024.sql
   ```

## Troubleshooting
- Si el disco externo no está conectado, el servicio `db` fallará al iniciar.
- El contenedor de PHP espera las librerías en `C:/Users/rinco/`, verificar que los paths existan en el host.