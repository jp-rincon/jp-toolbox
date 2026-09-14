# Plan Técnico de Migración: Moodle 2.8.2 a Moodle 4.x LTS y MySQL 8

## 1. Información General
- **Origen:** Moodle 2.8.2 | PHP 5.6 | MySQL 5.5
- **Destino:** Moodle 4.x LTS (4.5 / 4.4) | PHP 8.2 | MySQL 8.0+
- **Modalidad:** Preproducción aislada en Docker con migración escalonada.

## 2. Ruta Obligatoria de Hitos (Stepping Stones)

```text
[ Moodle 2.8.2 ]  -->  [ Moodle 3.2.9 ]  -->  [ Moodle 3.9 LTS ]
 (PHP 5.6 / 5.5)        (PHP 7.0 / 7.1)        (PHP 7.4 / 5.7)
       |
       v
[ Moodle 4.1 LTS ]  -->  [ Moodle 4.x LTS (Meta Final) ]
 (PHP 8.1 / 8.0)          (PHP 8.2 / MySQL 8.0+)
```

| Hito | Versión Moodle | PHP | MySQL | Objetivo Principal |
|---|---|---|---|---|
| **Línea Base** | 2.8.2+ | PHP 5.6 | MySQL 5.5 | Restauración del backup actual y validación de datos |
| **Hito 1** | 3.2.9 | PHP 7.0/7.1 | MySQL 5.6/5.7 | Salto puente inicial; migración de tablas base del core |
| **Hito 2** | 3.9.x LTS | PHP 7.4 | MySQL 5.7 | Conversión obligatoria a `utf8mb4` e InnoDB Barracuda |
| **Hito 3** | 4.1.x LTS | PHP 8.1 | MySQL 8.0 | Transición a la arquitectura moderna y tema Boost |
| **Hito 4** | 4.5.x LTS | PHP 8.2 | MySQL 8.0+ | Versión definitiva con soporte a largo plazo |

## 3. Puntos Críticos y Mitigaciones
1. **Codificación de Base de Datos:**
   - En Moodle 3.x se debe correr el conversor:
     ```bash
     php admin/cli/mysql_collation.php --collation=utf8mb4_unicode_ci
     ```
2. **Desactivación de Plugins Obsoletos:**
   - Auditar antes de saltar a 3.x. Desactivar plugins huérfanos sin versión para Moodle 4.
3. **Temas Gráficos:**
   - Cambiar temas antiguos (Clean, Canvas) a temas estándar compatibles antes del salto a Moodle 4.
4. **Ejecución CLI:**
   - Siempre correr: `php admin/cli/upgrade.php --non-interactive`.
