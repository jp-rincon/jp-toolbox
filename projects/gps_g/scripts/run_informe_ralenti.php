<?php
/**
 * Runner CLI para validar InformeRalenti en un rango específico.
 *
 * Uso:
 *   php scripts/run_informe_ralenti.php --placa=M214771 --desde="2026-05-09 00:00:00" --hasta="2026-05-09 23:59:59" --usuario=ilc
 *
 * Opcionales:
 *   --grupo=...            (default: "")
 *   --tipoConsulta=...     (default: "franja") valores típicos: completo | franja | continuo
 *   --tipoDetencion=...    (default: "NO")
 *   --tiempoDetencion=...  (default: 5) minutos
 *   --modo=...             (default: "resumen") valores: resumen | detalle | raw
 *   --cp=...               (solo para modo=detalle)
 */

if (php_sapi_name() !== 'cli') {
    fwrite(STDERR, "Este script es solo para CLI.\n");
    exit(1);
}

$opts = getopt('', array(
    'placa:',
    'desde:',
    'hasta:',
    'usuario:',
    'grupo::',
    'tipoConsulta::',
    'tipoDetencion::',
    'tiempoDetencion::',
    'modo::',
    'cp::',
    'usarOperacion::',
));

$placa = isset($opts['placa']) ? $opts['placa'] : '';
$desde = isset($opts['desde']) ? $opts['desde'] : '';
$hasta = isset($opts['hasta']) ? $opts['hasta'] : '';
$usuarioLogin = isset($opts['usuario']) ? $opts['usuario'] : '';

if ($placa === '' || $desde === '' || $hasta === '' || $usuarioLogin === '') {
    fwrite(STDERR, "Faltan parámetros obligatorios.\n");
    fwrite(STDERR, "Ejemplo: php scripts/run_informe_ralenti.php --placa=M214771 --desde=\"2026-05-09 00:00:00\" --hasta=\"2026-05-09 23:59:59\" --usuario=ilc\n");
    exit(2);
}

$grupo = isset($opts['grupo']) ? $opts['grupo'] : '*';
if ($grupo === '') {
    $grupo = '*';
}
$tipoConsulta = isset($opts['tipoConsulta']) ? $opts['tipoConsulta'] : 'franja';
$tipoDetencion = isset($opts['tipoDetencion']) ? $opts['tipoDetencion'] : 'NO';
$tiempoDetencion = isset($opts['tiempoDetencion']) ? (int)$opts['tiempoDetencion'] : 5;
$modo = isset($opts['modo']) ? $opts['modo'] : 'resumen';
$cp = isset($opts['cp']) ? $opts['cp'] : '';

// Bootstrap mínimo del framework (evita includes no compatibles con PHP moderno, como algunas librerías Excel).
$frameworkPath = __DIR__ . '/../framework/';
$rootPath = __DIR__ . '/../';

// Variables globales requeridas por el framework
$basePath = $frameworkPath;
require_once($frameworkPath . '../php/def_globales.inc');
global $servidor, $idioma;
$servidorOriginal = $servidor;
require_once($frameworkPath . '../php/labels_gps.' . $idioma);
$servidor = $servidorOriginal;

require_once($frameworkPath . 'includes/etiquetas.php');
require_once($frameworkPath . '../adodb/adodb.inc.php');

// Stub mínimo para evitar fatal si Predis no está instalado en el entorno CLI.
// (El informe de ralentí no requiere Redis; el framework intenta inicializarlo en `Conexion::conRedis()`).
if (!class_exists('Predis\\Client')) {
    // PHP 5.3 compatible (namespaces soportados)
    eval('namespace Predis; class Client { public function __construct($parameters = null, $options = null) {} }');
}

require_once($frameworkPath . 'clases/Conexion.php');
require_once($frameworkPath . 'clases/Generales.php');
require_once($frameworkPath . 'clases/InformeRalenti.php');

$general = new Generales();
$ralenti = new InformeRalenti($general);

$usarOperacion = isset($opts['usarOperacion']) ? (int)$opts['usarOperacion'] : 0;
$usuarioOperacion = $usuarioLogin;
if ($usarOperacion === 1) {
    // En web se usa para traducir usuario->padre en ciertos clientes; en CLI es opcional.
    $usuarioOperacion = $general->usuarioOperacion($usuarioLogin);
}

if ($modo === 'detalle') {
    if ($cp === '') {
        // Intentar resolver cp por placa
        $resCp = @pg_query($general->con('gps'), "SELECT cp FROM cp_placa WHERE placa='" . addslashes($placa) . "' LIMIT 1");
        if ($resCp && pg_num_rows($resCp) > 0) {
            $rowCp = pg_fetch_assoc($resCp);
            $cp = $rowCp['cp'];
        } else {
            fwrite(STDERR, "Para --modo=detalle debes enviar --cp=... (no se pudo resolver cp por placa)\n");
            exit(3);
        }
    }
    $data = $ralenti->detalleRalenti($cp, $placa, $desde, $hasta, $general, $usuarioOperacion, $tipoDetencion, $tiempoDetencion);
    echo json_encode(array(
        'modo' => 'detalle',
        'cp' => $cp,
        'placa' => $placa,
        'desde' => $desde,
        'hasta' => $hasta,
        'tipoDetencion' => $tipoDetencion,
        'tiempoDetencion' => $tiempoDetencion,
        'rows' => $data,
    ));
    exit(0);
}

$modoRaw = ($modo === 'raw');
if ($modoRaw) {
    if ($cp === '') {
        $resCp = @pg_query($general->con('gps'), "SELECT cp FROM cp_placa WHERE placa='" . addslashes($placa) . "' LIMIT 1");
        if ($resCp && pg_num_rows($resCp) > 0) {
            $rowCp = pg_fetch_assoc($resCp);
            $cp = $rowCp['cp'];
        } else {
            fwrite(STDERR, "Para --modo=raw no se pudo resolver cp por placa. Pasa --cp=...\n");
            exit(4);
        }
    }
    $eventos = $ralenti->eventosRalentiPoliticas($cp, $desde, $hasta, $general);
    $segTotal = 0;
    foreach ($eventos as $ev) {
        $segTotal += (int)$ev[2];
    }
    echo json_encode(array(
        'modo' => 'raw',
        'cp' => $cp,
        'placa' => $placa,
        'desde' => $desde,
        'hasta' => $hasta,
        'paradas' => count($eventos),
        'segundos' => $segTotal,
        'tiempo' => $general->segundosTiempo($segTotal),
        'eventos' => $eventos,
    ));
    exit(0);
}

$data = $ralenti->informeRalenti($grupo, $placa, $desde, $hasta, $tipoConsulta, $usuarioOperacion, $general, $tipoDetencion, $tiempoDetencion);

echo json_encode(array(
    'modo' => 'resumen',
    'grupo' => $grupo,
    'placa' => $placa,
    'desde' => $desde,
    'hasta' => $hasta,
    'tipoConsulta' => $tipoConsulta,
    'tipoDetencion' => $tipoDetencion,
    'tiempoDetencion' => $tiempoDetencion,
    'rows' => $data,
));
