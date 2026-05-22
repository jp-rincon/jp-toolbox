# Notas Técnicas - tobo3_g

## Inicialización de Base de Datos

### Restaurar Backup

El backup viene comprimido (`.zp`).

1. Copiar el archivo al contenedor (usa el ID o nombre):
   ```bash
   docker cp tobo_master_v1_20230625_res.sql.zp Tobo3Postgres:/tmp/
   ```

2. Entrar al contenedor y restaurar:
   ```bash
   docker exec -it Tobo3Postgres bash
   # Crear la base si no existe
   createdb -U postgres tobo_master_v1
   # Restaurar
   pg_restore -U postgres -d tobo_master_v1 -v /tmp/tobo_master_v1_20230625_res.sql.zp
   ```
