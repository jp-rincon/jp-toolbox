# Inventario y Rotación de Vaults en AWS S3 Glacier

Herramienta para solicitar el inventario de un Vault de AWS S3 Glacier, guardarlo localmente en JSON y eliminar masivamente sus archivos en paralelo (de una vez o por lotes), tanto para la **rotación semanal** como para el **desmonte de Vaults antiguos**.

---

## Mapa de Vaults y Estrategia ("Plan Maestro")

| Vault | Rol | Acción permitida en este script |
|---|---|---|
| **`tobo`** | Histórico principal ("Joya de la corona") | **PROTEGIDO** (Bloqueado en código contra borrado) |
| **`tobo4_x_mes`** | Backups mensuales de tablas particionadas ("Joya de la corona") | **PROTEGIDO** (Bloqueado en código contra borrado) |
| **`tobo4_1` .. `tobo4_4`** | Rotación semanal del último mes (4 semanas) | Vaciar archivos cada semana (`delete-archives`). **Nunca** borrar el Vault. |
| **`tobo4`** | Legado de backups completos semanales en partes de 4GB (1,265 archivos / ~4 TB) | Vaciar por lotes (`delete-archives --limit 100`) y al final eliminar el Vault (`delete-vault`). |

---

## Flujo 1: Rotación Semanal (`tobo4_1` a `tobo4_4`)

Abre PowerShell en la carpeta del proyecto:
```powershell
cd C:\Users\rinco\jp-toolbox\projects\aws_glacier
```

### 1. Solicitar el inventario del Vault de la semana
```powershell
python .\scripts\glacier_cleanup.py --vault tobo4_1 init
```
- Inicia el trabajo `inventory-retrieval` en AWS (tarda **entre 3 y 5 horas**).
- Guarda la referencia del trabajo en `output/job_tobo4_1.json`.

### 2. Descargar y guardar el inventario en `output/`
Pasadas las 3–5 horas (o al día siguiente):
```powershell
python .\scripts\glacier_cleanup.py --vault tobo4_1 status
```
- Descarga y guarda el inventario en `output/inventory_tobo4_1.json`.

### 3. Eliminar los archivos del Vault (vaciado para rotación)
```powershell
python .\scripts\glacier_cleanup.py --vault tobo4_1 delete-archives
```
- Elimina los ~22 archivos en pocos segundos y deja el Vault `tobo4_1` limpio para subir el backup de la nueva semana.

---

## Flujo 2: Limpieza por Lotes y Eliminación de `tobo4` (1,265 archivos)

Para el Vault legado `tobo4`, una vez descargado su inventario (`output/inventory_tobo4.json`), puedes ir borrando de a `N` archivos por ejecución sin tener que volver a pedir el inventario:

```powershell
# Borra un lote de 100 archivos y registra cuáles ya se borraron en output/deleted_tobo4.json
python .\scripts\glacier_cleanup.py --vault tobo4 delete-archives --limit 100
```
- Cada vez que vuelvas a correr ese mismo comando, **saltará automáticamente los archivos ya eliminados** y borrará los siguientes 100, mostrándote cuántos quedan pendientes.
- Cuando llegue a `0` restantes (y pasen 24h para que AWS actualice el conteo del Vault), podrás eliminar el Vault:
  ```powershell
  python .\scripts\glacier_cleanup.py --vault tobo4 delete-vault
  ```

---

## Estructura de Archivos

```text
projects/aws_glacier/
├── .env                       # Credenciales y configuración local (ignorado en git)
├── .env.example               # Plantilla de configuración
├── README.md                  # Guía de uso y Plan Maestro de Vaults
├── notes/
│   └── README.md              # Notas técnicas, permisos IAM y troubleshooting
├── output/                    # Inventarios y progreso de borrado (ignorado en git)
│   ├── job_<vault>.json       # Último Job ID solicitado
│   ├── inventory_<vault>.json # Inventario descargado de AWS
│   └── deleted_<vault>.json   # Registro de ArchiveIds ya borrados (para lotes --limit)
└── scripts/
    └── glacier_cleanup.py     # Script principal con bloqueo de seguridad para tobo y tobo4_x_mes
```
