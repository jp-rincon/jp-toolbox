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
$fecha_ini       = '2026-05-22 08:00:00';     // <--- Fecha inicio  (YYYY-MM-DD), por defecto hoy
$fecha_fin       = '2026-05-22 10:00:00';     // <--- Fecha fin     (YYYY-MM-DD), por defecto hoy
// =====================================================================

set_time_limit(0);          // Sin timeout (puede haber mucho volumen)
ini_set('memory_limit', '512M');

// Conexión nativa PostgreSQL (evita dependencias de Redis/ADOdb)
$conexion = Conexion::con();

if (!$conexion) {
    die("Error de conexión a la base de datos.");
}

// -----------------------------------------------------------------
// 1. Obtener todos los equipos activos del cliente
// -----------------------------------------------------------------
$sql_equipos = "SELECT cp_placa.placa, cp_placa.cp, cp_placa.alias
                FROM cp_placa
                JOIN usr_id ON cp_placa.cp = usr_id.id
                WHERE usr_id.usr   = '$usuario_cliente'
                  AND usr_id.estado = 'A'
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
// 3. Cabeceras HTTP → descarga CSV
// -----------------------------------------------------------------
$clean_ini = preg_replace('/[^0-9]/', '', $fecha_ini);
$clean_fin = preg_replace('/[^0-9]/', '', $fecha_fin);
$nombre_archivo = 'reporte_obd_detallado_' . $usuario_cliente
                  . '_' . $clean_ini
                  . '_' . $clean_fin
                  . '.csv';

header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $nombre_archivo . '"');

// BOM para que Excel abra correctamente el UTF-8
echo "\xEF\xBB\xBF";

$output = fopen('php://output', 'w');

// Cabecera del CSV (idéntica a las columnas de informe_obd.php)
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

// -----------------------------------------------------------------
// 4. Ciclo por cada equipo
// -----------------------------------------------------------------
while ($equipo = pg_fetch_assoc($res_equipos)) {

    $cp    = $equipo['cp'];
    $placa = $equipo['placa'];
    $alias = $equipo['alias'];
    $dsn   = isset($mapa_dsn[$cp]) ? $mapa_dsn[$cp] : '';

    // Consulta equivalente a lo que hace function_obd.php (caso generaltemp)
    // + el JOIN de informe_obd.php para obtener nombres PGN/SPN y descrange
    // Nota: to_hex() es la función nativa de PostgreSQL para convertir a hexadecimal
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
                  AND fecha_gps BETWEEN '{$fecha_ini}' AND '{$fecha_fin}'
            ) key_split
            WHERE key_split.raw_key ~ '^obd_P[0-9]+_S[0-9]+$'
        ) sub
        LEFT JOIN obd_pgn_spn ON (sub.spn_dec = obd_pgn_spn.spn)
        LEFT JOIN obd_pgn     ON (obd_pgn_spn.pgn = obd_pgn.pgn)
        WHERE sub.dato IS NOT NULL AND sub.dato <> ''
        ORDER BY sub.fecha_gps ASC, obd_pgn.pgn_name, obd_pgn_spn.spnname
    ";

    $res = pg_query($conexion, $sql);

    if (!$res) {
        // Si la tabla no existe o hay error, saltamos este equipo
        continue;
    }

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
            strtoupper($row['pgnhx']),                                    // PGN en hexadecimal
            $row['pgn_dec'],                                               // PGN decimal
            isset($row['pgn_name'])  ? $row['pgn_name']  : '',            // Nombre del PGN
            $row['spn_dec'],                                               // SPN decimal
            isset($row['spnname'])   ? $row['spnname']   : '',            // Nombre del SPN
            $dato,                                                         // Valor del parametro
            isset($row['descrange']) ? $row['descrange'] : '',            // Rango / descripcion
            $row['fecha_gps']                                              // Fecha y hora GPS
        ));
    }

    pg_free_result($res);
}

pg_free_result($res_equipos);
fclose($output);
exit;
?>
