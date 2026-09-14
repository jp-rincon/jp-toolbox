# Docker - Moodle Migration

Entorno contenerizado para el ciclo completo de migración de Moodle.

## Qué resuelve
Permite correr entornos heterogéneos y aislados de PHP (desde 5.6 hasta 8.2) y MySQL (desde 5.5 hasta 8.0) sin conflictos en la máquina anfitriona, facilitando la restauración local, auditoría y saltos controlados de versiones.

---

## 1. Fase Inicial: Réplica Moodle 2.8.2 (Línea Base)

Esta fase levanta la versión exacta que tiene el cliente para validar el backup `.sql` y la carpeta `moodledata`.

### Configuración rápida (30 segundos)

1. Crear el archivo local de variables copiando el ejemplo:
   ```bash
   cp .env.example .env
   ```
2. Colocar el dump SQL en la carpeta de inicialización o importarlo una vez arriba:
   - Directorio sugerido: `data/backup.sql`
   - Directorio de moodledata: `data/moodledata/`
3. Construir y levantar el compose de la versión 2.8.2:
   ```bash
   docker compose -f compose.base28.yml up -d --build
   ```
4. Ver logs:
   ```bash
   docker compose -f compose.base28.yml logs -f
   ```

### URLs y Puertos (por defecto)
- **Moodle Web:** `http://localhost:8080`
- **MySQL 5.5:** `localhost:33066` (Usuario: `root` / Pass: definido en `.env`)

---

## Smoke Test (Línea Base)
Para verificar que el contenedor de PHP 5.6 y MySQL 5.5 están operativos y comunicándose:

```bash
docker compose -f compose.base28.yml exec web php -v
docker compose -f compose.base28.yml exec db mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "STATUS;"
```
