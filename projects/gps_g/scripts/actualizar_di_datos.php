<?php

$conn = ConectarDb();

#$sqlConductor = "SELECT driverid FROM conductor WHERE driverid != '' AND length(driverid) > 15 AND id_conductor NOT IN (968,  78,  82, 197, 970, 305,1139, 964, 504) limit 1";
$sqlConductor = "SELECT driverid FROM conductor WHERE driverid != '' AND length(driverid) > 15 ";

$resultado1	= pg_query($conn, $sqlConductor);
$list_conductor	= pg_fetch_all($resultado1) ;
$num_conductor	= count($list_conductor);

echo "\nTotal Conductores: ". $num_conductor."\n";

$sqlTablas 	= "SELECT tablename FROM pg_catalog.pg_tables where substring(tablename,1,4) = 'gps_' AND tablename != 'gps_ultimo' ";
#$sqlTablas 	= "SELECT tablename FROM pg_catalog.pg_tables where tablename = 'gps_193505' ";

$resultado2 	= pg_query($conn, $sqlTablas);
$lista_tablas 	= pg_fetch_all($resultado2) ;
$num_tablas	= count($lista_tablas);

echo "\nTotal Tablas: ". $num_tablas."\n";

for ($c=0; $c < $num_conductor; $c++ ) {

	if (!$conn) {
		$conn = ConectarDb();
	}

	$driverid = $list_conductor[$c]['driverid'];

	for($k=0; $k < $num_tablas; $k++) {

		$tabla_gps = $lista_tablas[$k]['tablename'];

		if ($tabla_gps === 'gps_' OR $tabla_gps === "gps_0") {
			continue;
		}

		$cp_placa = explode("_", $tabla_gps);
		$cp = $cp_placa[1];

		$placa    = BuscarPlaca($conn, $cp);

		if ($placa === 'NN') {
			continue;
		}

		$sqlDatos = "SELECT g.otros_datos->'TAG' AS driverid, g.id AS cp, '$placa' AS placa, g.latitud, g.longitud, '' AS usuario, g.fecha_grab, g.fecha_gps, g.gps, g.motivo, g.otros_datos->'idEvento' AS evento FROM gps_$cp g INNER JOIN motivos_es me ON g.motivo = me.motivo WHERE g.fecha_gps-'5 hour'::interval < '2023-12-12 00:00:00' g.otros_datos->'TAG' = '$driverid' ORDER BY fecha_grab "; 

		$resultado3 = pg_query($conn, $sqlDatos);
		$datos_gps	= pg_fetch_all($resultado3) ;

		if (empty($datos_gps)) {
			$reg = 0;
		}
		else {
			$reg = count($datos_gps);
		}

		$reg_ok = 0;
		$reg_error = 0;

		for ($i=0; $i < $reg; $i++ ){
			
			$driverid	= $datos_gps[$i]['driverid'];
			$cp			= $datos_gps[$i]['cp'];
			$placa		= $datos_gps[$i]['placa'];
			$latitud	= $datos_gps[$i]['latitud'];
			$longitud	= $datos_gps[$i]['longitud'];
			$usuario	= $datos_gps[$i]['usuario'];
			$fecha_ing	= $datos_gps[$i]['fecha_grab'];
			$fecha_gps	= $datos_gps[$i]['fecha_gps'];
			$gps		= $datos_gps[$i]['gps'];
			$motivo		= $datos_gps[$i]['motivo'];
			$evento		= $datos_gps[$i]['evento'];

			$sqlInsert = "INSERT INTO di_datos_bk (driverid, cp, placa, latitud, longitud, usuario, fecha_ing , fecha_gps, gps, motivo, evento) VALUES ('$driverid', '$cp', '$placa', '$latitud', '$longitud', '$usuario', '$fecha_ing' , '$fecha_gps', '$gps', '$motivo', '$evento') "; 

			$ok = pg_query($conn, $sqlInsert);
			if (pg_affected_rows($ok) > 0){
				$reg_ok++;
			}
			else {
				$reg_error++;
				echo "\nError al instertar Registros $sqlInsert \n";
			}
		}

		echo "\n$k de $num_tablas -- Tabla: gps_$cp Registros Ok: $reg_ok Registros Error: $reg_error \n";

	}
}

function BuscarPlaca($conn, $cp) {
	$sql = "SELECT placa FROM cp_placa where cp = '$cp' ";

	$resultado = pg_query($conn, $sql);
	$datos = pg_fetch_all($resultado) ;

	if (empty($datos)) {
		return 'NN';
	}

	return $datos[0]['placa'];
}

function ConectarDb() {

	$port	= 5432;
	$ipdb	= "10.0.0.54";
	$base 	= "basegps1";
	$usrdb	= "internet";
	$pwddb	= "101"; 
	
	$conn= pg_connect("host = $ipdb port = $port dbname = $base user = $usrdb password = $pwddb");

	return $conn;

}

?>
