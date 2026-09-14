# Scripts de Automatización - Moodle Migration

Directorio reservado para scripts auxiliares (Bash y PowerShell) para agilizar tareas repetitivas durante la migración:

- `01_restore_base.sh` / `.ps1`: Script de restauración del dump SQL y permisos de moodledata.
- `02_snapshot_db.sh` / `.ps1`: Script para extraer un dump rápido de la base de datos entre cada hito.
- `03_run_collation.sh` / `.ps1`: Script para invocar el conversor `mysql_collation.php` dentro del contenedor.
- `04_run_upgrade.sh` / `.ps1`: Script para ejecutar el `upgrade.php` con flags desatendidos y registro de logs.
