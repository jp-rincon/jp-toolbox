# Notas - AWS S3 Glacier Cleanup (Rotación Semanal)

## Estrategia de Rotación (`tobo4_1` .. `tobo4_4`)

- Se mantienen 4 Vaults (`tobo4_1`, `tobo4_2`, `tobo4_3`, `tobo4_4`) para conservar las 4 semanas del último mes.
- Cada semana se rota uno de los Vaults:
  1. Se solicita el inventario (`init`).
  2. Se descarga y guarda el JSON en `projects/aws_glacier/output/inventory_<vault>.json` (`status`).
  3. Se borran los archivos contenidos en ese inventario (`delete-archives`).
- **Importante:** Los Vaults **no se eliminan**, solo se vacían sus archivos (`ArchiveId`) para reutilizar el mismo Vault en el ciclo semanal.

## Tiempos de AWS S3 Glacier

1. **Generación de Inventario (`init` -> `status`)**:
   - AWS tarda **entre 3 y 5 horas** en completar el Job `inventory-retrieval`.
   - Una vez que el Job pasa a estado `Succeeded`, AWS conserva ese resultado listo para descargar durante **24 horas**, por lo que se puede lanzar `init` en la tarde y ejecutar `status` + `delete-archives` a la mañana siguiente sin problema.

2. **Refresco visual de `list-vaults` (~24h)**:
   - El conteo `NumberOfArchives` y `SizeInBytes` que muestra `list-vaults` es actualizado por AWS una vez cada ~24 horas.
   - Si acabas de ejecutar `delete-archives` con éxito, los archivos ya están eliminados, aunque `list-vaults` siga mostrando el número anterior hasta el día siguiente.

## Permisos IAM Mínimos Requeridos

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glacier:ListVaults",
        "glacier:DescribeVault",
        "glacier:InitiateJob",
        "glacier:DescribeJob",
        "glacier:ListJobs",
        "glacier:GetJobOutput",
        "glacier:DeleteArchive"
      ],
      "Resource": "*"
    }
  ]
}
```
