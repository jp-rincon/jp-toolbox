# Resumen de Ubicación y Flujo de `llave_id` - Webservice ISI

Este documento detalla dónde se captura, procesa y almacena el campo `llave_id` dentro del sistema de monitoreo y auditoría del webservice **ISI**.

## 1. Captura Inicial
El dato es enviado por el cliente en el JSON de la solicitud dentro del array `datos_consulta`.
- **Archivo:** `c:\Users\rinco\laft_g\portal\isi\Due_v1.php`
- **Línea:** ~187

## 2. Almacenamiento de Auditoría (Permanente)
Cada consulta queda registrada para auditoría en la tabla **`accesos_ws`**. Debido a que es una estructura flexible, se utiliza el tipo de dato **`hstore`** de PostgreSQL.
- **Archivo:** `c:\Users\rinco\laft_g\portal\isi\fun_procesa_rest_v1.php` (Función `registrar_ip_ws`)
- **Tabla:** `public.accesos_ws`
- **Columna:** `bodega`
- **Ejemplo de consulta SQL:**
  ```sql
  SELECT * FROM accesos_ws WHERE bodega->'llave_id' = 'VALOR_DE_LA_LLAVE';
  ```

## 3. Almacenamiento de Proceso (Temporal)
Para poder generar la respuesta al cliente y vincularla con el sistema de monitoreo, la `llave_id` se almacena en tablas temporales durante la ejecución:

1. **`bd_cliente_comparar_0`**: Creada en `LlenarBd_cliente_cmp`. Guarda los datos originales de la consulta para cruzarlos con las listas.
2. **`respuesta_ws_due`**: Almacena los hallazgos encontrados en listas internacionales/noticias asociados a esa `llave_id`.
3. **`respuesta_ws_us`**: Almacena los hallazgos en listas locales (tipo Clinton) asociados a esa `llave_id`.

## 4. Relación con el Monitoreo
El sistema de monitoreo utiliza estos registros para:
1. Identificar qué usuarios consultaron un nombre específico en el pasado.
2. Notificar si llega una nueva noticia que coincida con una `llave_id` previamente consultada.

Además, existe una tabla denominada **`log_acceso_ws`** que registra los eventos específicos del motor de monitoreo cuando realiza sus validaciones periódicas.

---
*Nota: Para más detalles técnicos sobre el rastreo, consultar `c:\Users\rinco\laft_g\SEGUIMIENTO_LLAVE_ID.md`.*