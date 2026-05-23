# Registro y Seguimiento de llave_id en Webservices LAFT_G

## Descripción General
El parámetro `llave_id` en los webservices (como `@portal/isi/Due_v1.php`) se utiliza para **identificar y rastrear consultas específicas** del usuario en el sistema, facilitando el seguimiento y el monitoreo de transacciones.

---

## 📍 Flujo de Captura y Registro del `llave_id`

### 1. **CAPTURA DEL PARÁMETRO** 
**Ubicación:** [portal/isi/Due_v1.php](portal/isi/Due_v1.php#L187)

```php
// Línea 187 en Due_v1.php
$llave_id = isset($llave['llave_id']) ? $llave['llave_id'] : '';

// Validación - requiere obligatoriamente
if ($llave_id === '' || $nombres === '') {
    return array('error' => array(
        'code' => 'REQ_MISSING_FIELDS', 
        'message' => 'Cada item de datos_consulta requiere al menos llave_id y nombres'
    ));
}
```

El `llave_id` viene en cada item del array `datos_consulta` del JSON de entrada:
```json
{
  "datos_usuario": {
    "cod_emp": "...",
    "usuario": "...",
    "password": "..."
  },
  "datos_consulta": [
    {
      "llave_id": "TRX-2025-001",
      "nombres": "Juan",
      "apellidos": "García",
      "identificacion": "1234567",
      "division": "PERSONAL",
      "alias": ""
    }
  ]
}
```

---

## 📊 TABLA 1: REGISTRO EN `accesos_ws` (ISI)

**Ubicación:** [portal/isi/fun_procesa_rest_v1.php](portal/isi/fun_procesa_rest_v1.php#L307-L360)

### Función que registra:
```php
function registrar_ip_ws($ip, $msg_ws, $cod_emp, $usuario, $conexionPgsql, $DatosWsDue, $fecha_inicio)
```

### Estructura del registro:

| Campo | Descripción | Tipo |
|-------|-------------|------|
| **cod_emp** | Código de empresa | VARCHAR |
| **ip** | IP del cliente que hace la consulta | VARCHAR |
| **msg_ws** | Mensaje descriptivo (ej: "Clave OK") | VARCHAR |
| **usuario_ws** | Usuario que efectúa la consulta | VARCHAR |
| **fecha_reg** | Fecha y hora del registro | TIMESTAMP |
| **bodega** | Campo **hstore** con los datos completos | hstore |

### Contenido del campo `bodega` (hstore):
```
'cod_emp' => '...',
'nombres' => 'Juan',
'apellidos' => 'García',
'llave_id' => 'TRX-2025-001',        ← AQUÍ SE REGISTRA
'usuario' => 'jgarcia',
'identificacion' => '1234567',
'division' => 'PERSONAL',
'fecha_inicio' => '2025-05-14 10:30:00'
```

### Consulta del registro:
```sql
INSERT INTO accesos_ws (cod_emp, ip, msg_ws, usuario_ws, fecha_reg, bodega) 
VALUES (:cod_emp, :ip, :msg_ws, :usuario, now(), 
        hstore(ARRAY[:h0, :h1, :h2, :h3, :h4, :h5, :h6, :h7, :h8]))
```

---

## 📊 TABLA 2: REGISTRO EN `log_acceso_ws` (MONITOREO)

**Ubicación:** [portal/monitoreo/fun_procesa_monitoreo_v1.php](portal/monitoreo/fun_procesa_monitoreo_v1.php#L7-L24)

### Función que registra:
```php
function registrar_ip_ws($ip, $mensaje, $cod_emp, $usuario, $conexion, $log_data, $fecha)
```

### Estructura del registro:

| Campo | Descripción | Tipo |
|-------|-------------|------|
| **ip** | IP del cliente | VARCHAR |
| **mensaje** | Mensaje de la acción (ej: "Acceso Monitoreo OK") | VARCHAR |
| **cod_emp** | Código de empresa | VARCHAR |
| **usuario** | Usuario que accede | VARCHAR |
| **fecha** | Fecha del evento | TIMESTAMP |
| **nombres** | Nombres del cliente buscado | VARCHAR |
| **apellidos** | Apellidos del cliente buscado | VARCHAR |
| **identificacion** | Identificación del cliente | VARCHAR |
| **llave_id** | **Identificador único de la transacción** | VARCHAR |

### Registro específico en Monitoreo:
```php
$log_data = array(
    'nombres' => 'SISTEMA',
    'apellidos' => 'MONITOREO',
    'llave_id' => 'MON-LOG',          ← Valor fijo para logs de monitoreo
    'identificacion' => 'N/A',
    'division' => ''
);
registrar_ip_ws($ip_local, 'Acceso Monitoreo OK', $cod_emp, $usuario, $conexion, $log_data, $fecha_inicio);
```

**Ubicación en código:** [portal/monitoreo/Monitoreo_v1.php](portal/monitoreo/Monitoreo_v1.php#L56-L71)

---

## 🔍 CONSULTAS DE SEGUIMIENTO POR `llave_id`

### Consulta 1: Accesos ISI por `llave_id`
```sql
SELECT 
    a.bodega->'llave_id' as llave_id,
    a.bodega->'nombres' as nombres,
    a.bodega->'apellidos' as apellidos,
    a.bodega->'identificacion' as identificacion,
    a.bodega->'division' as division,
    a.usuario_ws as usuario,
    a.ip,
    a.fecha_reg as fecha_consulta,
    a.msg_ws as estado
FROM accesos_ws a
WHERE a.bodega->'llave_id' = 'TRX-2025-001'
ORDER BY a.fecha_reg DESC;
```

### Consulta 2: Accesos de Monitoreo por empresa/fecha
**Ubicación:** [portal/data/procesosConsultaVarias.php](portal/data/procesosConsultaVarias.php#L391-L410)
```sql
SELECT 
    b.id_usuario, 
    c.id_empresa, 
    b.usuario, 
    b.nombre_usuario, 
    c.nombre_empresa,
    COALESCE(NULLIF(a.bodega->'identificacion', ''), 
             TRIM((a.bodega->'nombres') || ' ' || (a.bodega->'apellidos'))) as dato_buscado, 
    100 as porcentaje, 
    a.fecha_reg as fecha_consulta,
    a.bodega::text as resultados          ← Incluye todos los datos incluyendo llave_id
FROM accesos_ws a
JOIN empresa c ON a.cod_emp = c.cod_emp
JOIN usuario b ON a.usuario_ws = b.usuario AND b.id_empresa = c.id_empresa
WHERE date(a.fecha_reg) BETWEEN :fecha_ini AND :fecha_fin
ORDER BY fecha_consulta DESC;
```

---

## 🔄 Flujo Completo de Seguimiento

```
┌─────────────────────────────────────┐
│ 1. Cliente envía JSON con llave_id  │
│    (portal/isi/Due_v1.php)          │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 2. Validación de credenciales       │
│    - cod_emp, usuario, password     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 3. Registro en accesos_ws           │
│    - Llama registrar_ip_ws()        │
│    - Guarda en bodega (hstore)      │
│    - Incluye llave_id               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 4. Procesamiento de consulta        │
│    - Busca en lista_due             │
│    - Genera tablas temporales       │
│    - Retorna resultados             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 5. Disponible para consultas de     │
│    seguimiento y monitoreo          │
│    - Filtrar por llave_id           │
│    - Rastrear transacciones         │
└─────────────────────────────────────┘
```

---

## 📝 Archivos Involucrados en el Registro

### ISI (Webservice DUE):
- [portal/isi/Due_v1.php](portal/isi/Due_v1.php) - Punto de entrada, captura y valida llave_id
- [portal/isi/fun_procesa_rest_v1.php](portal/isi/fun_procesa_rest_v1.php) - Función `registrar_ip_ws()` que registra en accesos_ws
- [portal/isi/DueRestHandler_v1.php](portal/isi/DueRestHandler_v1.php) - Manejador REST que procesa la solicitud

### MONITOREO:
- [portal/monitoreo/Monitoreo_v1.php](portal/monitoreo/Monitoreo_v1.php) - Entrada a acciones de monitoreo
- [portal/monitoreo/fun_procesa_monitoreo_v1.php](portal/monitoreo/fun_procesa_monitoreo_v1.php) - Registro en log_acceso_ws
- [portal/monitoreo/SuspenderMonitoreo_v1.php](portal/monitoreo/SuspenderMonitoreo_v1.php) - Suspensión con llave_id = 'SUSP-MON-LOG'

### CONSULTAS DE SEGUIMIENTO:
- [portal/data/procesosConsultaVarias.php](portal/data/procesosConsultaVarias.php) - Reportes de consultas (línea 391)

---

## 🛠️ Variantes en Otros Módulos

El sistema de `llave_id` se replica en otros módulos:

| Módulo | Ubicación | Tabla |
|--------|-----------|-------|
| **ISI** | `portal/isi/` | `accesos_ws` (bodega hstore) |
| **Ecredit** | `portal/ecredit/` | `accesos_ws` |
| **Zona Franca** | `portal/zonafranca/` | `accesos_ws` |
| **WS v4** | `portal/wsversion4/` | `accesos_ws` |
| **REST** | `portal/rest/` | `accesos_ws` |
| **WS v2** | `portal/ws2/` | `accesos_ws` |
| **Monitoreo** | `portal/monitoreo/` | `log_acceso_ws` |

---

## 💡 Recomendaciones para Seguimiento

1. **Crear índice en `accesos_ws`** para mejorar búsquedas por llave_id:
```sql
CREATE INDEX idx_accesos_ws_llave_id ON accesos_ws USING GIN(bodega);
-- O específicamente:
CREATE INDEX idx_accesos_ws_bodega_llave_id ON accesos_ws ((bodega->'llave_id'));
```

2. **Crear vista para facilitar consultas**:
```sql
CREATE VIEW v_accesos_ws_tracking AS
SELECT 
    (bodega->'llave_id')::text as llave_id,
    (bodega->'nombres')::text || ' ' || (bodega->'apellidos')::text as nombre_cliente,
    (bodega->'identificacion')::text as identificacion,
    (bodega->'division')::text as division,
    usuario_ws,
    ip,
    fecha_reg,
    cod_emp,
    msg_ws
FROM accesos_ws
WHERE bodega ? 'llave_id';
```

3. **Para reportes de monitoreo**, usar `log_acceso_ws` que tiene campos desnormalizados:
```sql
SELECT 
    llave_id,
    nombres,
    apellidos,
    identificacion,
    usuario,
    ip,
    fecha,
    mensaje
FROM log_acceso_ws
WHERE llave_id != 'MON-LOG'
ORDER BY fecha DESC;
```

---

## 📌 Conclusión

El `llave_id` es un **identificador único de transacción** que se registra en dos niveles:

1. **`accesos_ws`** (ISI y otros webservices) - En el campo `bodega` como hstore con todos los detalles
2. **`log_acceso_ws`** (Monitoreo) - En un campo específico para seguimiento de monitoreo

Esto permite un **rastreo completo** de cada consulta desde su origen hasta su resultado, facilitando auditorías y seguimiento en el proceso de monitoreo.
