# Moodle Migration: v2.8.2 -> v4.x LTS (Modernización)

Proyecto dedicado a la migración y modernización de la plataforma Moodle institucional desde la versión **2.8.2** (PHP 5.6 / MySQL 5.5) a la versión moderna **Moodle 4.x LTS** (PHP 8.2 / MySQL 8.0+).

## Contexto y Arquitectura
- **Origen:** Moodle 2.8.2 (2015), PHP 5.6, MySQL 5.5.
- **Destino:** Moodle 4.x LTS, PHP 8.2, MySQL 8.0+ (servidor nuevo).
- **Estrategia:** Réplica local en Docker $\rightarrow$ Migración escalonada por hitos (*stepping stones*) $\rightarrow$ Auditoría de consistencia $\rightarrow$ Despliegue en producción.

## Estructura del Proyecto

```text
projects/moodle_migration/
├── docs/               # Documentación formal y entregables (Propuesta técnica, PDF, HTML)
├── docker/             # Dockerfiles, docker-compose por hito y variables de entorno
├── notes/              # Bitácora interna, troubleshooting y plan técnico
├── scripts/            # Scripts de automatización (upgrade CLI, compilación PDF, dumps)
└── README.md           # Este archivo
```

## Ruta de Hitos
1. **Línea Base (v2.8.2):** Restauración local y validación del backup actual (PHP 5.6 + MySQL 5.5).
2. **Hito 1 (v3.2.9):** Salto puente inicial (PHP 7.0/7.1 + MySQL 5.6).
3. **Hito 2 (v3.9 LTS):** Conversión obligatoria a `utf8mb4` e InnoDB Barracuda (PHP 7.4 + MySQL 5.7).
4. **Hito 3 (v4.1 LTS):** Migración a la nueva arquitectura y tema Boost (PHP 8.1 + MySQL 8.0).
5. **Hito 4 (Meta v4.x LTS):** Salto final a versión definitiva (PHP 8.2 + MySQL 8.0+).

Consulte `notes/README.md` y `notes/plan_migracion.md` para más detalles.
