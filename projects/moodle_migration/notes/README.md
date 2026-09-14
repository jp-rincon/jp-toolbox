# Notas y Bitácora - Moodle Migration

Este directorio almacena la documentación técnica, registro de decisiones y bitácora de incidencias durante la migración de Moodle 2.8.2 a Moodle 4.x LTS.

## Documentos Disponibles

- [plan_migracion.md](plan_migracion.md): Plan de migración detallado con hitos, tablas de compatibilidad y estrategia.
- `Propuesta_Tecnica_Migracion_Moodle.pdf`: Documento formal en PDF preparado para el cliente.

## Bitácora de Decisiones y Troubleshooting

### Decisión 1: Estrategia de migración local con Docker
- **Motivo:** Evitar cualquier impacto en la infraestructura productiva actual y solventar incompatibilidades radicales entre PHP 5.6 y PHP 8.2 en la máquina anfitriona.
- **Resultado:** Aislamiento total en contenedores modulares por cada versión de salto.

### Decisión 2: Actualizaciones mediante CLI
- **Motivo:** Prevenir timeouts HTTP (código 504 / max execution time) durante las modificaciones masivas del esquema de base de datos.
- **Comando estándar:** `php admin/cli/upgrade.php --non-interactive`.

### Registro de Hallazgos y Plugins
*(Se irá completando una vez restaurado el backup y auditadas las tablas `mdl_config_plugins` y `mdl_course`)*
