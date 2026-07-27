<?php
/**
 * Script: Descarga Masiva OBD - Detallado OBD
 * ============================================
 * Equivalente al informe_obd.php con opcion=Detallado%20OBD
 * pero ejecutado para TODAS las placas de un usuario en un rango de fechas.
 *
 * Genera un CSV consolidado con las columnas:
 *   Placa | Alias | CP | PGN | Nombre PGN | SPN | Nombre SPN | Dato | Rango/Desc | Fecha GPS
 *
 * CONFIGURACIÓN: Ajustar las variables de la sección "CONFIGURACIÓN" antes de ejecutar.
 */

require_once "../php/def_globales.inc";
require_once "../framework/clases/Conexion.php";

// =====================================================================
// --- CONFIGURACIÓN ---
// =====================================================================
$usuario_cliente = 'GARGOS';          // <--- Usuario del cliente
$fecha_ini       = '2026-06-27 00:00:00';     // <--- Fecha inicio  (YYYY-MM-DD), por defecto hoy
$fecha_fin       = '2026-07-26 00:00:00';     // <--- Fecha fin     (YYYY-MM-DD), por defecto hoy
// =====================================================================

set_time_limit(0);          // Sin timeout (puede haber mucho volumen)
ini_set('memory_limit', '512M');

// Conexión nativa PostgreSQL (evita dependencias de Redis/ADOdb)
$conexion = Conexion::con();

if (!$conexion) {
    die("Error de conexión a la base de datos.");
}

/**
 * Función para verificar y reconectar a PostgreSQL si la conexión se cae
 */
function asegurar_conexion(&$conexion) {
    if (!$conexion || @pg_ping($conexion) === false) {
        if ($conexion) {
            @pg_close($conexion);
        }
        $conexion = Conexion::con();
    }
    return $conexion ? true : false;
}

// -----------------------------------------------------------------
// 1. Obtener todos los equipos activos del cliente
// -----------------------------------------------------------------
#(Bloque de línea 43 se aplica cuando solo se van a consulta algunas placas...)
$sql_equipos = "SELECT cp_placa.placa, cp_placa.cp, cp_placa.alias
                FROM cp_placa
                JOIN usr_id ON cp_placa.cp = usr_id.id
                WHERE usr_id.usr   = '$usuario_cliente'
                  AND usr_id.estado = 'A'
                  AND cp_placa.placa IN (
                    'JYX369',
                    'JYX268',
                    'JYX269',
                    'JYW616',
                    'JYW615',
                    'JYX371',
                    'JYX370',
                    'JYX267',
                    'JYX270',
                    'JYX271',
                    'JYX272',
                    'JYX368',
                    'JYW613',
                    'JYW614',
                    'JYW617',
                    'JYW618',
                    'JYW619',
                    'JYW786',
                    'JYW609',
                    'JYW610',
                    'JYW612',
                    'JYW787',
                    'JYW788',
                    'JYX025',
                    'JYX026')
                ORDER BY cp_placa.placa";

$res_equipos = pg_query($conexion, $sql_equipos);

if (!$res_equipos || pg_num_rows($res_equipos) == 0) {
    die("No se encontraron equipos activos para el usuario: $usuario_cliente");
}

// -----------------------------------------------------------------
// 2. Obtener los DSN de cada equipo (para conversión de odómetro)
// -----------------------------------------------------------------
$mapa_dsn = array();
$res_dsn = pg_query($conexion, "SELECT id, dsn FROM bd_cp");
if ($res_dsn) {
    while ($row_dsn = pg_fetch_assoc($res_dsn)) {
        $mapa_dsn[$row_dsn['id']] = $row_dsn['dsn'];
    }
    pg_free_result($res_dsn);
}

// -----------------------------------------------------------------
// 3. Configuración de Directorio de Salida
// -----------------------------------------------------------------
$clean_ini = preg_replace('/[^0-9]/', '', $fecha_ini);
$clean_fin = preg_replace('/[^0-9]/', '', $fecha_fin);

$nombre_carpeta = 'reportes_obd_' . $usuario_cliente . '_' . $clean_ini . '_' . $clean_fin;
$dir_salida = __DIR__ . '/../../basura/' . $nombre_carpeta;

if (!is_dir($dir_salida)) {
    if (!mkdir($dir_salida, 0777, true)) {
        die("Error: No se pudo crear el directorio de salida: $dir_salida\n");
    }
}

// Configurar tipo de contenido a texto plano si se ejecuta en navegador para visualizar progreso
if (php_sapi_name() !== 'cli') {
    header('Content-Type: text/plain; charset=utf-8');
}

echo "=====================================================================\n";
echo "PROCESO DE DESCARGA MASIVA OBD POR PLACA (POR CHUNKS DIARIOS)\n";
echo "=====================================================================\n";
echo "Usuario Cliente     : $usuario_cliente\n";
echo "Rango de Fechas     : $fecha_ini a $fecha_fin\n";
echo "Directorio Salida   : $dir_salida\n";
echo "=====================================================================\n\n";
flush();

// -----------------------------------------------------------------
// 4. Ciclo por cada equipo (Procesamiento por chunks diarios)
// -----------------------------------------------------------------
$placas_procesadas = 0;
$total_equipos     = pg_num_rows($res_equipos);
$equipo_index      = 0;

while ($equipo = pg_fetch_assoc($res_equipos)) {
    $equipo_index++;
    $cp    = $equipo['cp'];
    $placa = $equipo['placa'];
    $alias = $equipo['alias'];
    $dsn   = isset($mapa_dsn[$cp]) ? $mapa_dsn[$cp] : '';

    echo "[$equipo_index/$total_equipos] Procesando placa: $placa (CP: $cp)...\n";
    flush();

    // Crear/sobrescribir el archivo CSV para esta placa
    $archivo_placa = $dir_salida . '/' . $placa . '.csv';
    $output = fopen($archivo_placa, 'w');
    if (!$output) {
        echo "   ERROR: No se pudo crear el archivo CSV ($archivo_placa)\n\n";
        flush();
        continue;
    }

    // BOM para que Excel abra correctamente el UTF-8
    fwrite($output, "\xEF\xBB\xBF");

    // Cabecera del CSV
    fputcsv($output, array(
        'CP',
        'Placa',
        'Alias',
        'PGN (Hex)',
        'PGN (Dec)',
        'Nombre PGN',
        'SPN',
        'Nombre SPN',
        'Dato',
        'Rango / Descripción',
        'Fecha GPS'
    ));

    $ts_actual   = strtotime($fecha_ini);
    $ts_fin      = strtotime($fecha_fin);
    $total_placa = 0;

    // Iterar día a día para evitar sobrecargar PostgreSQL
    while ($ts_actual < $ts_fin) {
        $ts_siguiente = strtotime('+1 day', $ts_actual);
        if ($ts_siguiente > $ts_fin) {
            $ts_siguiente = $ts_fin;
        }

        $sub_ini_str = date('Y-m-d H:i:s', $ts_actual);
        $sub_fin_str = date('Y-m-d H:i:s', $ts_siguiente);
        $dia_label   = date('Y-m-d', $ts_actual);

        // Asegurar que la conexión PostgreSQL siga viva
        if (!asegurar_conexion($conexion)) {
            echo "   -> Chunk [$dia_label]: ERROR (No se pudo reconectar a PostgreSQL)\n";
            $ts_actual = $ts_siguiente;
            continue;
        }

        // Consulta en fragmento de 1 día
        $sql = "
            SELECT
                sub.pgnhx,
                sub.pgn_dec,
                sub.spn_dec,
                obd_pgn.pgn_name,
                obd_pgn_spn.spnname,
                sub.dato,
                obd_pgn_spn.descrange,
                sub.fecha_gps
            FROM (
                SELECT
                    to_hex(CAST(replace(key_split.p2, 'P', '') AS bigint)) AS pgnhx,
                    CAST(replace(key_split.p2, 'P', '') AS bigint)          AS pgn_dec,
                    CAST(replace(key_split.p3, 'S', '') AS bigint)          AS spn_dec,
                    key_split.dato,
                    key_split.fecha_gps
                FROM (
                    SELECT
                        split_part(skeys(otros_datos), '_', 2) AS p2,
                        split_part(skeys(otros_datos), '_', 3) AS p3,
                        skeys(otros_datos) AS raw_key,
                        svals(otros_datos) AS dato,
                        fecha_gps
                    FROM gps_{$cp}
                    WHERE otros_datos::text ILIKE '%obd%'
                      AND fecha_gps >= '{$sub_ini_str}' AND fecha_gps < '{$sub_fin_str}'
                ) key_split
                WHERE key_split.raw_key ~ '^obd_P[0-9]+_S[0-9]+$'
            ) sub
            LEFT JOIN obd_pgn_spn ON (sub.spn_dec = obd_pgn_spn.spn)
            LEFT JOIN obd_pgn     ON (obd_pgn_spn.pgn = obd_pgn.pgn)
            WHERE sub.dato IS NOT NULL AND sub.dato <> ''
            ORDER BY sub.fecha_gps ASC, obd_pgn.pgn_name, obd_pgn_spn.spnname
        ";

        $res = @pg_query($conexion, $sql);

        if (!$res) {
            // Reintentar 1 vez si hubo desconexión previa
            if (asegurar_conexion($conexion)) {
                $res = @pg_query($conexion, $sql);
            }
        }

        if (!$res) {
            echo "   -> Día [$dia_label]: ERROR en consulta o tabla no existe\n";
            $ts_actual = $ts_siguiente;
            continue;
        }

        $contador_chunk = 0;
        while ($row = pg_fetch_assoc($res)) {
            $dato = $row['dato'];

            // Conversión de odómetro: si el dato empieza con 'H' (Hectomillas → Km)
            if (isset($dato[0]) && $dato[0] === 'H') {
                $dato = str_replace('H', '', $dato);
                if ($dsn !== 'galileo') {
                    $dato = $dato / 10;
                }
            }

            fputcsv($output, array(
                $cp,
                $placa,
                $alias,
                strtoupper($row['pgnhx']),
                $row['pgn_dec'],
                isset($row['pgn_name'])  ? $row['pgn_name']  : '',
                $row['spn_dec'],
                isset($row['spnname'])   ? $row['spnname']   : '',
                $dato,
                isset($row['descrange']) ? $row['descrange'] : '',
                $row['fecha_gps']
            ));
            $contador_chunk++;
        }

        pg_free_result($res);

        if ($contador_chunk > 0) {
            echo "   -> Día [$dia_label]: $contador_chunk registros\n";
        }

        $total_placa += $contador_chunk;
        $ts_actual = $ts_siguiente;
        flush();
    }

    fclose($output);

    if ($total_placa === 0) {
        echo "   -> Resultado: SIN REGISTROS en el rango de fechas.\n\n";
    } else {
        echo "   -> Resultado: OK! Total $total_placa registros guardados en " . basename($archivo_placa) . "\n\n";
        $placas_procesadas++;
    }
    flush();
}

pg_free_result($res_equipos);

echo "=====================================================================\n";
echo "PROCESO COMPLETADO\n";
echo "Placas procesadas con éxito: $placas_procesadas / $total_equipos\n";
echo "Los archivos CSV se encuentran en: $dir_salida\n";
echo "=====================================================================\n";
exit;
?>
