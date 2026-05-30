<?php
/**
 * Runner CLI para descargar el informe de Calificación de Conductores en un rango.
 *
 * Nota:
 * - El frontend "ng-reporte-calificacion-conductores" consume la misma lógica del informe que
 *   `framework/modulos/CalificacionConductores/InformeCalificacion/informe-json.php`.
 *
 * Uso:
 *   php scripts/run_informe_calificacion_conductores.php --usuario=C0A284 --desde="2026-03-01 00:00:00" --hasta="2026-03-31 23:59:59" --tipo=actividad --formato=csv --csvDelimiter=";" --csvMetaLine=0 --chunkDays=1 --queryTimeout=120 --skipChunksFile=/tmp/marzo2026_done.txt --out=/tmp/info_calificacion_Marzo2026.csv 2>/tmp/marzo2026_progress.log
 *
 * Opcionales:
 *   --tipo=actividad|calificacion (default: "actividad")
 *   --grupo=...              (default: "*")
 *   --placa=...              (default: "*")
 *   --base=...               (default: "*")
 *   --conductor=...          (default: "*")
 *   --distanciaMinima=...    (default: 5)
 *   --usarOperacion=0|1      (default: 1) usa `Generales::usuarioOperacion()`
 *   --fuente=auto|etl|online (default: "auto")
 *   --formato=json|csv       (default: "json")
 *   --incluirMeta=0|1        (default: 0) si 1, agrega un bloque "meta" en JSON
 *   --encoder=services|native (default: "services") para JSON: emula al endpoint (Services_JSON)
 *   --csvDelimiter=","       (default: ",") útil para Excel en ES: ";"
 *   --csvMetaLine=0|1        (default: 0) si 1, escribe una primera línea con metadata (comentario)
 *   --out=/ruta/archivo      (default: stdout)
 *
 * Opciones de resiliencia (nuevas):
 *   --chunkDays=N            (default: 1) procesa N días por lote; escribe al --out parcialmente
 *                            para no perder trabajo si se interrumpe. Recomendado: 1.
 *   --queryTimeout=N         (default: 120) segundos máx. que puede durar UNA query SQL en el
 *                            servidor antes de cancelarse. Evita que validaExcesoVelocidad()
 *                            paguine indefinidamente. 0 = sin límite.
 *   --skipChunksFile=archivo (default: "") path a un archivo de texto con fechas "YYYY-MM-DD"
 *                            ya procesadas (una por línea); se omiten automáticamente. Útil
 *                            para reanudar ejecuciones interrumpidas.
 */

// ---------------------------------------------------------------------------
// Función de progreso: escribe a STDERR con timestamp y tiempo transcurrido
// ---------------------------------------------------------------------------
$_scriptStart = microtime(true);
function progress($msg) {
    global $_scriptStart;
    $elapsed = microtime(true) - $_scriptStart;
    $ts = date('H:i:s');
    fwrite(STDERR, sprintf("[%s +%6.1fs] %s\n", $ts, $elapsed, $msg));
}

// ---------------------------------------------------------------------------
// Validación de entorno CLI
// ---------------------------------------------------------------------------
if (php_sapi_name() !== 'cli') {
    fwrite(STDERR, "Este script es solo para CLI.\n");
    exit(1);
}

// ---------------------------------------------------------------------------
// Parseo de argumentos
// ---------------------------------------------------------------------------
$opts = getopt('', array(
    'usuario:',
    'desde:',
    'hasta:',
    'tipo::',
    'grupo::',
    'placa::',
    'base::',
    'conductor::',
    'distanciaMinima::',
    'usarOperacion::',
    'fuente::',
    'formato::',
    'incluirMeta::',
    'encoder::',
    'csvDelimiter::',
    'csvMetaLine::',
    'out::',
    // --- nuevos ---
    'chunkDays::',
    'queryTimeout::',
    'skipChunksFile::',
));

$usuarioLogin = isset($opts['usuario']) ? trim($opts['usuario']) : '';
$desde        = isset($opts['desde'])   ? trim($opts['desde'])   : '';
$hasta        = isset($opts['hasta'])   ? trim($opts['hasta'])   : '';

$tipo = isset($opts['tipo']) ? strtolower(trim((string)$opts['tipo'])) : 'actividad';
if ($tipo === '') $tipo = 'actividad';
if (!in_array($tipo, array('actividad', 'calificacion'), true)) {
    fwrite(STDERR, "--tipo debe ser actividad|calificacion.\n");
    exit(9);
}

if ($usuarioLogin === '' || $desde === '' || $hasta === '') {
    fwrite(STDERR, "Faltan parámetros obligatorios.\n");
    fwrite(STDERR, "Ejemplo: php scripts/run_informe_calificacion_conductores.php --usuario=ilc --desde=\"2026-05-01 00:00:00\" --hasta=\"2026-05-07 23:59:59\"\n");
    exit(2);
}

$grupo      = isset($opts['grupo'])     ? (string)$opts['grupo']     : '*';
if (trim($grupo) === '')     $grupo     = '*';
$placa      = isset($opts['placa'])     ? (string)$opts['placa']     : '*';
if (trim($placa) === '')     $placa     = '*';
$baseFiltro = isset($opts['base'])      ? (string)$opts['base']      : '*';
if (trim($baseFiltro) === '') $baseFiltro = '*';
$conductor  = isset($opts['conductor']) ? (string)$opts['conductor'] : '*';
if (trim($conductor) === '') $conductor = '*';

$distanciaMinima = 5;
if (isset($opts['distanciaMinima']) && $opts['distanciaMinima'] !== '') {
    if (!is_numeric($opts['distanciaMinima'])) {
        fwrite(STDERR, "--distanciaMinima debe ser numérico.\n");
        exit(3);
    }
    $distanciaMinima = (float)$opts['distanciaMinima'];
}

$usarOperacion = isset($opts['usarOperacion']) ? (int)$opts['usarOperacion'] : 1;
$fuente        = isset($opts['fuente'])        ? strtolower(trim((string)$opts['fuente'])) : 'auto';
if ($fuente === '') $fuente = 'auto';
if (!in_array($fuente, array('auto','etl','online'), true)) {
    fwrite(STDERR, "--fuente debe ser auto|etl|online.\n");
    exit(4);
}

$formato = isset($opts['formato']) ? strtolower(trim((string)$opts['formato'])) : 'json';
if ($formato === '') $formato = 'json';
if (!in_array($formato, array('json','csv'), true)) {
    fwrite(STDERR, "--formato debe ser json|csv.\n");
    exit(5);
}

$out        = isset($opts['out'])        ? (string)$opts['out']        : '';
$incluirMeta = isset($opts['incluirMeta']) ? (int)$opts['incluirMeta'] : 0;
$encoder    = isset($opts['encoder'])    ? strtolower(trim((string)$opts['encoder'])) : 'services';
if ($encoder === '') $encoder = 'services';
if (!in_array($encoder, array('services','native'), true)) {
    fwrite(STDERR, "--encoder debe ser services|native.\n");
    exit(8);
}

$csvDelimiter = isset($opts['csvDelimiter']) ? (string)$opts['csvDelimiter'] : ',';
if ($csvDelimiter === '') $csvDelimiter = ',';
$csvMetaLine = isset($opts['csvMetaLine']) ? (int)$opts['csvMetaLine'] : 0;

// --- Nuevos parámetros de resiliencia ---
$chunkDays = isset($opts['chunkDays']) ? max(1, (int)$opts['chunkDays']) : 1;

$queryTimeout = 120; // segundos
if (isset($opts['queryTimeout']) && $opts['queryTimeout'] !== '') {
    if (!is_numeric($opts['queryTimeout'])) {
        fwrite(STDERR, "--queryTimeout debe ser numérico (segundos).\n");
        exit(11);
    }
    $queryTimeout = (int)$opts['queryTimeout'];
}

$skipChunksFile = isset($opts['skipChunksFile']) ? trim((string)$opts['skipChunksFile']) : '';
$skipDates = array();
if ($skipChunksFile !== '' && file_exists($skipChunksFile)) {
    $lines = file($skipChunksFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $l) {
        $skipDates[trim($l)] = true;
    }
    progress("Reanudando: " . count($skipDates) . " día(s) ya procesados en $skipChunksFile");
}

// ---------------------------------------------------------------------------
// Bootstrap mínimo del framework
// ---------------------------------------------------------------------------
$frameworkPath = __DIR__ . '/../framework/';
$basePath = $frameworkPath;
require_once($frameworkPath . '../php/def_globales.inc');
global $servidor, $idioma, $fecha_ini_etl_cc;
$servidorOriginal = $servidor;
require_once($frameworkPath . '../php/labels_gps.' . $idioma);
$servidor = $servidorOriginal;

require_once($frameworkPath . 'includes/etiquetas.php');

// Polyfill each() para PHP 8+
if (!function_exists('each')) {
    function each(&$array) {
        if (!is_array($array)) return false;
        $key = key($array);
        if ($key === null) return false;
        $value = current($array);
        next($array);
        return array(1 => $value, 'value' => $value, 0 => $key, 'key' => $key);
    }
}

require_once($frameworkPath . '../adodb/adodb.inc.php');

// Stub Predis para CLI
if (!class_exists('Predis\\Client')) {
    eval('namespace Predis; class Client { public function __construct($parameters = null, $options = null) {} }');
}

require_once($frameworkPath . 'clases/Conexion.php');
require_once($frameworkPath . 'clases/Generales.php');
require_once($frameworkPath . 'clases/Etiqueta.php');
require_once($frameworkPath . 'clases/CalificacionConductores.php');
require_once($frameworkPath . 'includes/json.php');

progress("Iniciando conexión a PostgreSQL...");
$general = new Generales();

$connTest = @$general->con('gps');
if (!$connTest) {
    fwrite(STDERR, "No se pudo conectar a PostgreSQL (revisa host/puerto/firewall y variables en `php/def_globales.inc`).\n");
    exit(10);
}
progress("Conexión OK.");

// ---------------------------------------------------------------------------
// Aplicar statement_timeout a la conexión GPS (previene queries infinitas)
// ---------------------------------------------------------------------------
if ($queryTimeout > 0) {
    $timeoutMs = $queryTimeout * 1000;
    @pg_query($connTest, "SET statement_timeout = {$timeoutMs}");
    progress("statement_timeout configurado: {$queryTimeout}s por query.");
} else {
    progress("statement_timeout: sin límite (--queryTimeout=0).");
}

$cc = new CalificacionConductores($general);

$usuarioOperacion = $usuarioLogin;
if ($usarOperacion === 1) {
    $usuarioOperacion = $general->usuarioOperacion($usuarioLogin);
}
progress("Usuario: $usuarioLogin → operación: $usuarioOperacion");

// ---------------------------------------------------------------------------
// Normalización de fechas del rango global
// ---------------------------------------------------------------------------
function normalizaFechaStr($str, $esInicio) {
    $str = trim($str);
    if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $str))
        return $str . ($esInicio ? ' 00:00:00' : ' 23:59:59');
    if (preg_match('/^(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}$/', $str))
        return $str . ':00';
    return $str;
}

$desdeNorm = normalizaFechaStr($desde, true);
$hastaNorm = normalizaFechaStr($hasta, false);

try { $dtDesde = new DateTime($desdeNorm); } catch (Exception $e) {
    fwrite(STDERR, "Fecha --desde inválida: $desde\n"); exit(12);
}
try { $dtHasta = new DateTime($hastaNorm); } catch (Exception $e) {
    fwrite(STDERR, "Fecha --hasta inválida: $hasta\n"); exit(13);
}

// ---------------------------------------------------------------------------
// Construir lista de chunks (bloques de chunkDays días)
// ---------------------------------------------------------------------------
$chunks = array();
$cur = clone $dtDesde;
$cur->setTime(0, 0, 0);
$endDay = clone $dtHasta;
$endDay->setTime(23, 59, 59);

while ($cur <= $endDay) {
    $chunkStart = clone $cur;
    $chunkStart->setTime(0, 0, 0);
    // Avanzar chunkDays días
    $chunkEnd = clone $cur;
    $chunkEnd->modify('+' . ($chunkDays - 1) . ' days');
    $chunkEnd->setTime(23, 59, 59);
    // No pasar del rango global
    if ($chunkEnd > $endDay) $chunkEnd = clone $endDay;

    // Respetar hora exacta si el primer chunk empieza en mitad del día
    if ($chunkStart->format('Y-m-d') === $dtDesde->format('Y-m-d')) {
        $chunkStart = clone $dtDesde;
    }
    // Idem para el último chunk
    if ($chunkEnd->format('Y-m-d') === $dtHasta->format('Y-m-d')) {
        $chunkEnd = clone $dtHasta;
    }

    $chunks[] = array(
        'desde' => $chunkStart->format('Y-m-d H:i:s'),
        'hasta' => $chunkEnd->format('Y-m-d H:i:s'),
        'label' => $chunkStart->format('Y-m-d') .
                   ($chunkDays > 1 ? ' → ' . $chunkEnd->format('Y-m-d') : ''),
        'dateKey' => $chunkStart->format('Y-m-d'),
    );

    $cur->modify('+' . $chunkDays . ' days');
}

$totalChunks = count($chunks);
progress("Rango: $desdeNorm → $hastaNorm | Chunks: $totalChunks (chunkDays=$chunkDays)");

// ---------------------------------------------------------------------------
// Mapa de columnas CSV para tipo=actividad
// ---------------------------------------------------------------------------
$csvMap = array(
    'Fecha'                  => 'fecha_ini',
    'Hora inicio'            => 'hora_ini',
    'Hora fin'               => 'hora_fin',
    'Placa'                  => 'placa',
    'Conductor'              => 'conductor',
    'Identificacion conductor' => 'identificacion',
    'Odometro KM'            => 'odometro',
    'Tiempo actividad'       => 'tiempo_actividad',
    'Ralenti'                => 'ralenti',
    'Velocidad prom'         => 'velocidad_promedio',
    'Velocidad max'          => 'velocidad_maxima',
    'Frenada fuerte'         => 'frenadas_fuerte',
    'Exceso velocidad'       => 'execesos_velocidad',
    'Tiempo exceso vel (seg)' => 'tiempo_exceso_vel',
);

// ---------------------------------------------------------------------------
// Para JSON acumulamos todo en memoria (no hay escritura parcial en JSON)
// ---------------------------------------------------------------------------
$allDatos = array();
$totalRows = 0;
$chunkErrors = array();

// ---------------------------------------------------------------------------
// Apertura del archivo de salida (modo escritura para CSV parcial)
// ---------------------------------------------------------------------------
$fhOut = null;
$headerWritten = false;

if ($formato === 'csv') {
    if ($out !== '') {
        $fhOut = @fopen($out, 'wb');
        if ($fhOut === false) {
            fwrite(STDERR, "No se pudo abrir --out=$out\n");
            exit(7);
        }
    } else {
        $fhOut = STDOUT;
    }
    // Línea de metadata al inicio
    if ($csvMetaLine === 1) {
        $metaInfo = array(
            'usuario'  => $usuarioLogin,
            'desde'    => $desdeNorm,
            'hasta'    => $hastaNorm,
            'tipo'     => $tipo,
            'generado' => date('Y-m-d H:i:s'),
            'chunks'   => $totalChunks,
        );
        fwrite($fhOut, "# " . json_encode($metaInfo) . "\n");
    }
    // Escribir cabecera CSV ahora (antes de los chunks)
    if ($tipo === 'actividad') {
        fputcsv($fhOut, array_keys($csvMap), $csvDelimiter);
    }
    $headerWritten = true;
}

// ---------------------------------------------------------------------------
// Procesamiento chunk por chunk
// ---------------------------------------------------------------------------
foreach ($chunks as $chunkIdx => $chunk) {
    $chunkNum = $chunkIdx + 1;
    $label    = $chunk['label'];
    $dateKey  = $chunk['dateKey'];

    // ¿Ya fue procesado? (modo reanudación)
    if (isset($skipDates[$dateKey])) {
        progress("[$chunkNum/$totalChunks] OMITIDO (ya procesado): $label");
        continue;
    }

    progress("[$chunkNum/$totalChunks] Procesando: $label ...");
    $chunkStart = microtime(true);

    $datos = array();
    $chunkError = null;

    try {
        if ($tipo === 'actividad') {
            $raw = $cc->getConductoresInicio($usuarioOperacion, $chunk['desde'], $chunk['hasta']);
            if (is_array($raw)) {
                foreach ($raw as $row) {
                    $datos[] = $row;
                }
            }
        } else if ($fuente === 'online') {
            $datos = $cc->getCalificacionConductores($general, $chunk['desde'], $chunk['hasta'], $grupo, $placa, $baseFiltro, $conductor, $distanciaMinima, $usuarioOperacion);
        } else if ($fuente === 'etl') {
            $datos = $cc->getCalificacionConductoresFromEtl($general, $chunk['desde'], $chunk['hasta'], $grupo, $placa, $baseFiltro, $conductor, $distanciaMinima, $usuarioOperacion);
        } else {
            // auto
            $fechaActual = date('Y-m-d');
            $f1 = substr($chunk['desde'], 0, 10);
            $f2 = substr($chunk['hasta'], 0, 10);
            $etStart = (isset($fecha_ini_etl_cc) && $fecha_ini_etl_cc) ? $fecha_ini_etl_cc : null;
            if ($f1 === $fechaActual && $f2 === $fechaActual) {
                $datos = $cc->getCalificacionConductores($general, $chunk['desde'], $chunk['hasta'], $grupo, $placa, $baseFiltro, $conductor, $distanciaMinima, $usuarioOperacion);
            } else if ($etStart !== null && $f1 < $fechaActual && $f2 < $fechaActual && $f1 >= $etStart && $f2 >= $etStart) {
                $datos = $cc->getCalificacionConductoresFromEtl($general, $chunk['desde'], $chunk['hasta'], $grupo, $placa, $baseFiltro, $conductor, $distanciaMinima, $usuarioOperacion);
            } else if ($etStart !== null && $f1 < $fechaActual && $f2 === $fechaActual && $f1 >= $etStart) {
                $datos = $cc->getCalificacionConductoresFromEtl_fecAct($general, $chunk['desde'], $chunk['hasta'], $grupo, $placa, $baseFiltro, $conductor, $distanciaMinima, $usuarioOperacion);
            } else if ($f2 < $fechaActual) {
                $datos = $cc->getCalificacionConductoresFromEtl($general, $chunk['desde'], $chunk['hasta'], $grupo, $placa, $baseFiltro, $conductor, $distanciaMinima, $usuarioOperacion);
            } else {
                $datos = $cc->getCalificacionConductores($general, $chunk['desde'], $chunk['hasta'], $grupo, $placa, $baseFiltro, $conductor, $distanciaMinima, $usuarioOperacion);
            }
        }
    } catch (Exception $e) {
        $chunkError = $e->getMessage();
    }

    // Detectar error de PostgreSQL (statement_timeout u otro)
    $pgError = pg_last_error($connTest);
    if ($pgError !== '' && $pgError !== false) {
        $chunkError = $pgError;
        // Re-conectar / limpiar el estado de error de la conexión
        @pg_query($connTest, "ROLLBACK");
        if ($queryTimeout > 0) {
            @pg_query($connTest, "SET statement_timeout = " . ($queryTimeout * 1000));
        }
    }

    $chunkElapsed = microtime(true) - $chunkStart;
    $rowsInChunk  = is_array($datos) ? count($datos) : 0;

    if ($chunkError !== null) {
        progress("[$chunkNum/$totalChunks] ⚠ ERROR en $label: $chunkError (se continúa con el siguiente chunk)");
        $chunkErrors[] = array('chunk' => $label, 'error' => $chunkError);
    } else {
        progress("[$chunkNum/$totalChunks] ✓ $label → $rowsInChunk fila(s) en " . round($chunkElapsed, 1) . "s");
    }

    $totalRows += $rowsInChunk;

    // --- Escritura parcial ---
    if ($formato === 'csv' && $rowsInChunk > 0) {
        if ($tipo === 'actividad') {
            foreach ($datos as $row) {
                $outRow = array();
                foreach ($csvMap as $label_col => $key) {
                    $outRow[] = (is_array($row) && isset($row[$key])) ? $row[$key] : '';
                }
                fputcsv($fhOut, $outRow, $csvDelimiter);
            }
        } else {
            // Para calificacion: columnas dinámicas (misma lógica que antes)
            if (!$headerWritten && $rowsInChunk > 0) {
                $first = $datos[0];
                $cols  = 0;
                if (is_array($first)) foreach ($first as $k => $v) { $cols++; }
                $header = array();
                for ($i = 0; $i < $cols; $i++) $header[] = 'col' . $i;
                fputcsv($fhOut, $header, $csvDelimiter);
                $headerWritten = true;
            }
            foreach ($datos as $row) {
                if (!is_array($row)) { fputcsv($fhOut, array($row), $csvDelimiter); continue; }
                $outRow = array();
                $first  = $datos[0];
                $cols   = 0;
                if (is_array($first)) foreach ($first as $k => $v) { $cols++; }
                for ($i = 0; $i < $cols; $i++) $outRow[] = isset($row[$i]) ? $row[$i] : '';
                fputcsv($fhOut, $outRow, $csvDelimiter);
            }
        }
        // Flush al disco para que el archivo sea legible aunque se interrumpa
        if ($fhOut !== STDOUT) fflush($fhOut);
    } else if ($formato === 'json') {
        // Para JSON acumulamos en memoria
        foreach ($datos as $row) $allDatos[] = $row;
    }

    // Registrar fecha procesada en skipChunksFile
    if ($skipChunksFile !== '' && $chunkError === null) {
        file_put_contents($skipChunksFile, $dateKey . "\n", FILE_APPEND | LOCK_EX);
    }

    unset($datos); // liberar memoria del chunk
}

// ---------------------------------------------------------------------------
// Resumen final
// ---------------------------------------------------------------------------
$totalElapsed = microtime(true) - $_scriptStart;
progress("─────────────────────────────────────────────");
progress("TOTAL filas: $totalRows | Tiempo total: " . round($totalElapsed, 1) . "s");
if (count($chunkErrors) > 0) {
    progress("⚠ Chunks con error (" . count($chunkErrors) . "):");
    foreach ($chunkErrors as $ce) {
        progress("  · " . $ce['chunk'] . " → " . $ce['error']);
    }
} else {
    progress("✓ Sin errores.");
}

// ---------------------------------------------------------------------------
// Salida JSON (acumulado en memoria, no es incremental)
// ---------------------------------------------------------------------------
if ($formato === 'json') {
    $meta = array(
        'tipo'              => $tipo,
        'usuario'           => $usuarioLogin,
        'usuarioOperacion'  => $usuarioOperacion,
        'desde'             => $desdeNorm,
        'hasta'             => $hastaNorm,
        'grupo'             => $grupo,
        'placa'             => $placa,
        'base'              => $baseFiltro,
        'conductor'         => $conductor,
        'distanciaMinima'   => $distanciaMinima,
        'fuente'            => $fuente,
        'rows'              => $totalRows,
        'chunksConError'    => count($chunkErrors),
    );
    $payload = array('aaData' => $allDatos);
    if ($incluirMeta === 1) $payload['meta'] = $meta;

    if ($encoder === 'services') {
        $old = error_reporting();
        @error_reporting($old & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING);
        $jsonEnc = new Services_JSON(SERVICES_JSON_LOOSE_TYPE);
        $json = $jsonEnc->encode($payload);
        @error_reporting($old);
    } else {
        $json = json_encode($payload);
    }

    if ($out !== '') {
        $ok = @file_put_contents($out, $json);
        if ($ok === false) {
            fwrite(STDERR, "No se pudo escribir en --out=$out\n");
            exit(6);
        }
        progress("OK: escrito $out");
    } else {
        echo $json;
    }
}

// ---------------------------------------------------------------------------
// Cierre de archivo CSV
// ---------------------------------------------------------------------------
if ($formato === 'csv') {
    if ($totalRows === 0 && $tipo === 'actividad') {
        // Ya se escribió el header; no hace falta hacer nada extra.
        progress("Advertencia: 0 filas encontradas en el rango.");
    }
    if ($fhOut !== STDOUT && $fhOut !== null) {
        fclose($fhOut);
        progress("Archivo escrito: $out");
    }
}

exit(count($chunkErrors) > 0 ? 20 : 0);
