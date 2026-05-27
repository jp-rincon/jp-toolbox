<?php
/**
 * Script Temporal: Descarga Masiva de parámetros OBD
 * Genera un CSV consolidado de 2 días para todos los equipos de un cliente.
 */

require_once "../php/def_globales.inc";
require_once "../framework/clases/Conexion.php";

// --- CONFIGURACIÓN ---
$usuario_cliente = 'GARGOS'; // <--- Cambiar por el usuario del cliente
$dias_atras = 0;
set_time_limit(0); // Evitar timeout por volumen de datos
ini_set('memory_limit', '512M');

// Usamos directamente la conexión nativa de PostgreSQL definida en Conexion
// Esto evita la carga de Redis, ADOdb y el framework completo, eliminando errores de dependencias.
$conexion = Conexion::con();

if (!$conexion) {
    die("Error de conexión a la base de datos.");
}

// 0. Cargar Mapa de Labels para parámetros OBD y Sensores
$mapa_labels = array(
    'SkpTemperatura_Temp1' => 'Temperatura 1',
    'SkpTemperatura_Temp2' => 'Temperatura 2',
    'SkpTemperatura_Temp3' => 'Temperatura 3',
    'SkpTemperatura_Temp4' => 'Temperatura 4',
    'SkpHumedad_Hum1'      => 'Humedad 1',
    'SkpHumedad_Hum2'      => 'Humedad 2',
    'obd_odometer'         => 'Odómetro OBD',
    'obd_fuel_level'       => 'Nivel Combustible %',
    'obd_speed'            => 'Velocidad Computadora',
    'obd_engine_load'      => 'Carga Motor'
);

// Consultamos los nombres técnicos (PGN/SPN) desde la base de datos
$sql_labels = "SELECT 'obd_P' || pgn::text || '_S' || spn::text as var_name, spnname 
               FROM obd_pgn_spn";
$res_labels = pg_query($conexion, $sql_labels);
if ($res_labels) {
    while ($row_l = pg_fetch_assoc($res_labels)) {
        $mapa_labels[$row_l['var_name']] = $row_l['spnname'];
    }
    pg_free_result($res_labels);
}


// 1. Definir rango de fechas
$fechaf = date('Y-m-d 23:59:59');
$fechai = date('Y-m-d 00:00:00', strtotime("-$dias_atras days"));

// 2. Obtener todos los CPs del cliente (Lógica optimizada sin clase Generales)
$sql_equipos = "SELECT cp_placa.placa, cp_placa.cp, cp_placa.alias 
                FROM cp_placa, usr_id 
                WHERE cp_placa.cp = usr_id.id 
                AND usr_id.usr = '$usuario_cliente' 
                AND usr_id.estado = 'A'";

$res_equipos = pg_query($conexion, $sql_equipos);

if (!$res_equipos || pg_num_rows($res_equipos) == 0) {
    die("No se encontraron equipos activos para el usuario: $usuario_cliente");
}

// 3. Preparar cabeceras para la descarga CSV
header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename=reporte_obd_consolidado_' . $usuario_cliente . '.csv');

$output = fopen('php://output', 'w');
// Cabeceras del CSV
fputcsv($output, array('Placa', 'Alias', 'CP', 'Fecha GPS', 'Latitud', 'Longitud', 'Velocidad', 'Ignicion', 'Evento', 'Parametros OBD'));

// 4. Ciclo por cada equipo
while ($equipo = pg_fetch_assoc($res_equipos)) {
    $cp = $equipo['cp'];
    $placa = $equipo['placa'];
    $alias = $equipo['alias'];
    
    $sql = "SELECT 
                fecha_gps, 
                latitud, 
                longitud, 
                velocidad, 
                ignicion, 
                motivo,
                otros_datos 
            FROM gps_$cp 
            WHERE fecha_gps BETWEEN '$fechai' AND '$fechaf'
            AND otros_datos IS NOT NULL
            ORDER BY fecha_gps ASC";

    $res = pg_query($conexion, $sql);

    if ($res) {
        while ($row = pg_fetch_assoc($res)) {
            // Solo procesamos si hay datos OBD en el campo hstore/json 'otros_datos'
            if (!empty($row['otros_datos'])) {
                
                // Parseamos el hstore y reemplazamos llaves por labels legibles
                $raw_hstore = $row['otros_datos'];
                preg_match_all('/"([^"]+)"\s*=>\s*"([^"]*)"/', $raw_hstore, $matches, PREG_SET_ORDER);
                
                $elementos_legibles = array();
                foreach ($matches as $match) {
                    $key = $match[1];
                    $val = $match[2];
                    $label = isset($mapa_labels[$key]) ? $mapa_labels[$key] : $key;
                    $elementos_legibles[] = "$label: $val";
                }
                $obd_data = implode(" | ", $elementos_legibles);

                fputcsv($output, array(
                    $placa,
                    $alias,
                    $cp,
                    $row['fecha_gps'],
                    $row['latitud'],
                    $row['longitud'],
                    $row['velocidad'],
                    $row['ignicion'],
                    $row['motivo'],
                    $obd_data
                ));
            }
        }
        pg_free_result($res);
    }
}

pg_free_result($res_equipos);
fclose($output);
exit;
?>