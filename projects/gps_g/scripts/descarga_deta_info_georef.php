<?php
/**
 * Script de Consola: Descarga Masiva de Reporte Detalle Georeferenciado
 * Genera archivos CSV individuales por placa para el mes de Junio de 2026.
 *
 * Desarrollado para Antigravity.
 */

// Desactivar límites de tiempo y ajustar límites de memoria para procesamiento en lotes
set_time_limit(0);
ini_set('memory_limit', '1024M');

// Incluir archivos globales y clase de conexión
require_once __DIR__ . "/../php/def_globales.inc";
require_once __DIR__ . "/../framework/clases/Conexion.php";

echo "=========================================================\n";
echo "Script de Descarga Masiva - deta_info_georef\n";
echo "=========================================================\n\n";

// Conectar a la base de datos principal
$conexion = Conexion::con();
if (!$conexion) {
    die("Error: No se pudo establecer conexión con la base de datos de Skytrack.\n");
}

// Configurar zona horaria de la sesión
pg_query($conexion, "SET TIME ZONE 'America/Bogota'");

// Conectar a la base de datos de georeferencias (por si se requiere resolución local de coordenadas)
$conexion_geo = Conexion::conGeo();
if ($conexion_geo) {
    // Si Conexion::conGeo() funcionó, asignamos la variable global $conn2 para que georef() funcione
    $GLOBALS['conn2'] = $conexion_geo;
    echo "Conexión a Base de Datos Geográfica: OK\n";
} else {
    echo "Advertencia: No se pudo conectar a la base de datos geográfica (las coordenadas no se podrán resolver localmente si faltan precalculadas).\n";
}

// --- CONFIGURACIÓN DEL PROCESO ---
// Rango de fechas para el informe (Junio de 2026)
$fechai = '2026-06-01 00:00:00';
$fechaf = '2026-06-30 23:59:59';

// Directorio de salida
$output_dir = __DIR__ . '/descargas_junio_2026';
if (!file_exists($output_dir)) {
    if (!mkdir($output_dir, 0777, true)) {
        die("Error: No se pudo crear el directorio de salida: $output_dir\n");
    }
}

// Leer la lista de placas
$placas_file = __DIR__ . '/placas.txt';
$placas = array();

if (file_exists($placas_file)) {
    $lines = file($placas_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line !== '' && strpos($line, '#') !== 0) {
            $placas[] = strtoupper($line);
        }
    }
}

if (empty($placas)) {
    echo "Advertencia: El archivo 'placas.txt' está vacío o no existe.\n";
    echo "Por favor, coloque las placas (una por línea) en: $placas_file\n\n";
    echo "Ejemplo de uso de array de respaldo en código...\n";
    // Ejemplo de array de respaldo por si el usuario no tiene placas.txt
    // $placas = array('AAA111', 'BBB222');
    pg_close($conexion);
    if ($conexion_geo) pg_close($conexion_geo);
    exit;
}

$total_placas = count($placas);
echo "Se encontraron " . $total_placas . " placas para procesar.\n";
echo "Período: $fechai a $fechaf\n";
echo "Los archivos CSV se guardarán en: $output_dir\n";
echo "---------------------------------------------------------\n";

// Abrir archivo de log de resumen
$log_file = $output_dir . '/resumen_proceso.log';
$log_handle = fopen($log_file, 'w');
fwrite($log_handle, "Resumen de Descarga - deta_info_georef.php\n");
fwrite($log_handle, "Fecha de ejecución: " . date('Y-m-d H:i:s') . "\n");
fwrite($log_handle, "Período: $fechai a $fechaf\n");
fwrite($log_handle, "Total placas: $total_placas\n");
fwrite($log_handle, "---------------------------------------------------------\n\n");

// Validar idioma para la tabla de motivos con múltiples alternativas (fallbacks)
$candidate_tables = array();
if (isset($idioma) && $idioma !== '') {
    $candidate_tables[] = "motivos_$idioma";
    if ($idioma === 'es' && isset($getPais)) {
        $candidate_tables[] = "motivos_es_" . strtolower($getPais);
    }
}
$candidate_tables[] = "motivos_es_cr";
$candidate_tables[] = "motivos_es";
$candidate_tables[] = "motivos";

$motivos_table = "motivos";
foreach ($candidate_tables as $tbl) {
    $tbl_check = pg_query($conexion, "SELECT 1 FROM pg_tables WHERE tablename = '$tbl'");
    if ($tbl_check && pg_num_rows($tbl_check) > 0) {
        $motivos_table = $tbl;
        pg_free_result($tbl_check);
        break;
    }
    if ($tbl_check) pg_free_result($tbl_check);
}
echo "Usando tabla de motivos: $motivos_table\n";


$factor_velo = isset($factor_velo) ? $factor_velo : 1.85;

// Cargar georef.php por si se requiere georreferenciación local fallback
if (file_exists(__DIR__ . '/../georef.php')) {
    require_once __DIR__ . '/../georef.php';
}

$procesados = 0;
$errores = 0;

foreach ($placas as $index => $placa) {
    $num_actual = $index + 1;
    $placa_esc = pg_escape_string($conexion, $placa);
    
    echo "[$num_actual/$total_placas] Procesando placa: $placa... ";
    
    // 1. Obtener CP y alias para la placa
    $sql_cp = "SELECT cp, alias FROM cp_placa WHERE TRIM(placa) = '$placa_esc' LIMIT 1";
    $res_cp = pg_query($conexion, $sql_cp);
    
    if (!$res_cp || pg_num_rows($res_cp) == 0) {
        echo "ERROR (CP no encontrado)\n";
        fwrite($log_handle, "Placa: $placa | Estado: ERROR - CP no encontrado en cp_placa\n");
        $errores++;
        continue;
    }
    
    $row_cp = pg_fetch_assoc($res_cp);
    $cp = $row_cp['cp'];
    $alias = $row_cp['alias'];
    pg_free_result($res_cp);
    
    // 2. Verificar existencia de la tabla gps_$cp
    $sql_tbl_exists = "SELECT 1 FROM pg_tables WHERE tablename = 'gps_$cp'";
    $res_tbl = pg_query($conexion, $sql_tbl_exists);
    if (!$res_tbl || pg_num_rows($res_tbl) == 0) {
        echo "ERROR (Tabla gps_$cp no existe)\n";
        fwrite($log_handle, "Placa: $placa | CP: $cp | Estado: ERROR - Tabla gps_$cp no existe en la base de datos\n");
        $errores++;
        if ($res_tbl) pg_free_result($res_tbl);
        continue;
    }
    pg_free_result($res_tbl);
    
    // 3. Verificar si existe la columna 'geo' en la tabla gps_$cp
    $sql_geo_exists = "SELECT 1 FROM information_schema.columns 
                       WHERE table_name = 'gps_$cp' AND column_name = 'geo'";
    $res_geo = pg_query($conexion, $sql_geo_exists);
    $has_geo = false;
    if ($res_geo && pg_num_rows($res_geo) > 0) {
        $has_geo = true;
    }
    if ($res_geo) pg_free_result($res_geo);
    
    $geo_select = $has_geo ? "gps_cp.geo as georeferencia" : "NULL as georeferencia";
    
    // 4. Formular consulta de datos históricos (emulando deta_info_georef_excel.php)
    $sql_data = "SELECT 
                    gps_cp.fecha_gps, 
                    gps_cp.latitud, 
                    gps_cp.longitud, 
                    gps_cp.velocidad, 
                    (CASE WHEN gps_cp.ignicion = 0 THEN 'NO' WHEN gps_cp.ignicion = 1 THEN 'SI' ELSE gps_cp.ignicion::text END) as ignicion, 
                    gps_cp.motivo, 
                    motivos.des_motivo as evento, 
                    gps_cp.recorrido,
                    $geo_select
                 FROM gps_$cp gps_cp 
                 LEFT OUTER JOIN $motivos_table motivos ON (gps_cp.motivo = motivos.motivo)
                 WHERE gps_cp.fecha_gps BETWEEN '$fechai'::timestamp AND '$fechaf'::timestamp 
                   AND gps_cp.gps IN (1,3,4) 
                 ORDER BY gps_cp.fecha_gps ASC";
                 
    $res_data = pg_query($conexion, $sql_data);
    if (!$res_data) {
        echo "ERROR (Fallo en consulta de datos)\n";
        fwrite($log_handle, "Placa: $placa | CP: $cp | Estado: ERROR - Fallo al consultar datos de gps_$cp\n");
        $errores++;
        continue;
    }
    
    $num_registros = pg_num_rows($res_data);
    
    // 5. Escribir a archivo CSV
    $safe_placa = str_replace(array('/', '\\', '?', '*', ':', '|', '"', '<', '>'), '_', $placa);
    $csv_file = $output_dir . "/placa_" . $safe_placa . ".csv";
    $csv_handle = fopen($csv_file, 'w');
    
    // Escribir cabeceras del CSV
    fputcsv($csv_handle, array('Fecha GPS', 'Latitud', 'Longitud', 'Velocidad (km/h)', 'Ignición', 'Código Evento', 'Descripción Evento', 'Distancia Recorrida (m)', 'Georreferencia'));
    
    while ($row = pg_fetch_assoc($res_data)) {
        $georef_val = $row['georeferencia'];
        
        // Si no tiene georreferencia precalculada en la base de datos y la BD de georreferencias está activa,
        // intentamos resolverla usando la función georef() local
        if (empty($georef_val) && $conexion_geo && function_exists('georef')) {
            $georef_val = georef($row['latitud'], $row['longitud'], "", "", "");
            if ($georef_val === -1 || empty($georef_val)) {
                $georef_val = 'Sin georeferencia';
            }
        }
        
        $velocidad_kmh = $row['velocidad'] !== null ? round($row['velocidad'] * $factor_velo, 1) : 0;
        
        fputcsv($csv_handle, array(
            $row['fecha_gps'],
            $row['latitud'],
            $row['longitud'],
            $velocidad_kmh,
            $row['ignicion'],
            $row['motivo'],
            $row['evento'] ? $row['evento'] : 'Evento ' . $row['motivo'],
            $row['recorrido'] !== null ? round($row['recorrido'], 1) : 0,
            $georef_val ? $georef_val : 'Sin georeferencia'
        ));
    }
    
    fclose($csv_handle);
    pg_free_result($res_data);
    
    echo "OK ($num_registros registros guardados)\n";
    fwrite($log_handle, "Placa: $placa | CP: $cp | Alias: $alias | Registros: $num_registros | Archivo: placa_$safe_placa.csv | Estado: OK\n");
    $procesados++;
}

echo "\n---------------------------------------------------------\n";
echo "Proceso finalizado.\n";
echo "Placas procesadas con éxito: $procesados\n";
echo "Placas con error/omitidas: $errores\n";
echo "Consulte el log en: $log_file\n";
echo "---------------------------------------------------------\n";

fwrite($log_handle, "\n---------------------------------------------------------\n");
fwrite($log_handle, "Fin del proceso: " . date('Y-m-d H:i:s') . "\n");
fwrite($log_handle, "Placas procesadas con éxito: $procesados | Errores: $errores\n");
fclose($log_handle);

// Cerrar conexiones
pg_close($conexion);
if ($conexion_geo) pg_close($conexion_geo);
