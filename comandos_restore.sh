# ==============================================================================
# GUÍA Y COMANDOS DE RESTAURACIÓN - TOBO3 (VM UBUNTU)
# ==============================================================================

# DATOS CLAVE IDENTIFICADOS:
# Placa: Z508083
# id_objeto: 152623
# Tabla seguimiento: dt_avl_152623
# Dump ID cfg_objeto: 339442 (archivo: 339442.dat.gz)
# Dump ID dt_avl_152623: 342420 (archivo: 342420.dat.gz)


# ------------------------------------------------------------------------------
# PASO 1: EXTRAER CATÁLOGO Y TABLA cfg_objeto
# ------------------------------------------------------------------------------
mkdir -p ~/carpeta_backups/dump_temp

tar -xf ~/carpeta_backups/tobo_cluster_02_v3_20260331_2028.tar -C ~/carpeta_backups/dump_temp --wildcards "*toc.dat" "*339442.dat.gz"
chmod -R 755 ~/carpeta_backups/dump_temp


# ------------------------------------------------------------------------------
# PASO 2: RESTAURAR cfg_objeto EN POSTGRES 10 (DOCKER)
# ------------------------------------------------------------------------------
docker exec -it tobo_restore_pg10 pg_restore -U postgres -d tobo_cluster_02_v3 -t cfg_objeto /backups/dump_temp/mnt/backup/tobo_cluster_02_v3_20260331_2028


# ------------------------------------------------------------------------------
# PASO 3: VERIFICAR COLUMNAS DE cfg_objeto (BUSCAR SI EXISTE base_datos)
# ------------------------------------------------------------------------------
# Ver todas las columnas:
docker exec -it tobo_restore_pg10 psql -U postgres -d tobo_cluster_02_v3 -c "\d cfg_objeto"

# Buscar específicamente columnas relacionadas con 'base':
docker exec -it tobo_restore_pg10 psql -U postgres -d tobo_cluster_02_v3 -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'cfg_objeto' AND column_name ILIKE '%base%';"


# ------------------------------------------------------------------------------
# PASO 4: CONSULTAR LA PLACA Z508083 EN LA TABLA cfg_objeto
# ------------------------------------------------------------------------------
docker exec -it tobo_restore_pg10 psql -U postgres -d tobo_cluster_02_v3 -c "SELECT id_objeto, codigo_objeto, nombre_objeto, id_cliente FROM cfg_objeto WHERE codigo_objeto = 'Z508083' OR nombre_objeto ILIKE '%Z508083%';"


# ------------------------------------------------------------------------------
# PASO 5: EXTRAER TABLA DE SEGUIMIENTO (dt_avl_152623 -> 342420.dat.gz)
# ------------------------------------------------------------------------------
tar -xf ~/carpeta_backups/tobo_cluster_02_v3_20260331_2028.tar -C ~/carpeta_backups/dump_temp --wildcards "*342420.dat.gz"
chmod -R 755 ~/carpeta_backups/dump_temp


# ------------------------------------------------------------------------------
# PASO 6: RESTAURAR dt_avl_152623 EN POSTGRES 10
# ------------------------------------------------------------------------------
docker exec -it tobo_restore_pg10 pg_restore -U postgres -d tobo_cluster_02_v3 -t dt_avl_152623 /backups/dump_temp/mnt/backup/tobo_cluster_02_v3_20260331_2028


# ------------------------------------------------------------------------------
# PASO 7: VALIDAR REGISTROS EN dt_avl_152623
# ------------------------------------------------------------------------------
docker exec -it tobo_restore_pg10 psql -U postgres -d tobo_cluster_02_v3 -c "\d dt_avl_152623"
docker exec -it tobo_restore_pg10 psql -U postgres -d tobo_cluster_02_v3 -c "SELECT COUNT(*) FROM dt_avl_152623;"


# ------------------------------------------------------------------------------
# PASO 8: EXTRAER Y RESTAURAR adm_cliente (ID: 339409)
# ------------------------------------------------------------------------------
tar -xf ~/carpeta_backups/tobo_cluster_02_v3_20260331_2028.tar -C ~/carpeta_backups/dump_temp --wildcards "*339409.dat.gz"
chmod -R 755 ~/carpeta_backups/dump_temp

docker exec -it tobo_restore_pg10 pg_restore -U postgres -d tobo_cluster_02_v3 -t adm_cliente /backups/dump_temp/mnt/backup/tobo_cluster_02_v3_20260331_2028


# ------------------------------------------------------------------------------
# AUDITORÍA HISTÓRICA CONFIRMADA (PERIODO 2023-01 A 2024-12)
# ------------------------------------------------------------------------------
# Archivo fuente verificado: tobo_master_v3_01Feb24.tar.gz
#
# Historial de cfg_objeto para Placa Z508083:
# - 2022-12-08: Creado originalmente con id_objeto: 152623 (IMEI temporal: 350317173346341)
# - 2023-01-18: Actualizada placa a Z508083 (VOLKSWAGEN METEOR 6X4 BLANCO 21) -> id_objeto: 152623
# - 2023-01-19: Asignado a cliente 3980 (FRESH FRUIT HOLDINGS) -> id_objeto: 152623
# - 2023-01-19: Renombrado a VW METEOR Z508083 -> id_objeto: 152623
#
# CONCLUSIÓN:
# El id_objeto NUNCA cambió. Siempre ha sido 152623.
#
# ASIGNACIÓN DE BODEGA / CLUSTER:
# - id_cliente 3980 -> id_bodega: bdg4 (según adm_cliente)
# - id_bodega bdg4  -> base_datos: tobo_cluster_02_v3 (según cfg_bodega)
#
# SOLICITUD DE BACKUPS A ING. MONTERO:
# - Base de datos requerida: tobo_cluster_02_v3
# - Periodo requerido: 2023-01 a 2024-12
# - Tabla específica a extraer de cada dump: dt_avl_152623

