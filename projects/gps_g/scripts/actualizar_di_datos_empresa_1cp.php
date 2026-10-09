<?php

$conn = ConectarDb();

$sqlConductor = "SELECT DISTINCT usuario, driverid FROM usuario, conductor, usr_id WHERE usuario.usuario='corpojfca' AND usuario.id_empresa = conductor.empresa AND usuario.usuario = usr_id.usr AND id_empresa is not null and id_empresa != 0 AND conductor.driverid != '' AND length(driverid) > 5 ";
//echo $sqlConductor; exit;
// $sqlConductor = "SELECT DISTINCT usuario, driverid FROM usuario, conductor, usr_id WHERE usuario.id_empresa = conductor.empresa AND usuario.usuario = usr_id.usr AND id_empresa is not null and id_empresa != 0 AND conductor.driverid != '' AND length(driverid) > 5  AND driverid = '01314AC91200001C' ";

$resultado1	= pg_query($conn, $sqlConductor);
$list_conductor	= pg_fetch_all($resultado1) ;
$num_conductor	= count($list_conductor);

$fecha_ini = "2026-01-22 09:11:50";
$fecha_fin = "2026-02-02 13:49:19";

echo "\nTotal Conductores: ". $num_conductor." Fecha Inicio ".date("Y-m-d H:i:s") ."\n";
$fechaHoraIni = date("Y-m-d H:i:s");

for ($c=0; $c < $num_conductor; $c++ ) {

	if (!$conn) {
		$conn = ConectarDb();
	}

    $driverid = $list_conductor[$c]['driverid'];
    $userId   = $list_conductor[$c]['usuario'];

    //$sqlTablas = "SELECT id, placa FROM usr_id, cp_placa WHERE usr_id.id = cp_placa.cp AND usr = '$userId' ";
    $sqlTablas = "SELECT id, placa FROM usr_id, cp_placa WHERE usr_id.id = cp_placa.cp AND usr = '$userId' AND id='300542' ";   //CP individual

    $listaCps 	    = pg_query($conn, $sqlTablas);
    $lista_tablas 	= pg_fetch_all($listaCps) ;
    $num_tablas	    = count($lista_tablas);
    
    echo "\nTotal Tablas Usuario: ". $num_tablas."\n";
    
	for($k=0; $k < $num_tablas; $k++) {

		$cp     = $lista_tablas[$k]['id'];
		$placa  = $lista_tablas[$k]['placa'];

		$sqlDatos = "SELECT '$driverid' AS driverid, g.id AS cp, '$placa' AS placa, g.latitud, g.longitud, '' AS usuario, g.fecha_grab, g.fecha_gps, g.gps, g.motivo FROM gps_$cp g WHERE (g.otros_datos->'TAG' = '$driverid' /*OR motivo = 4006*/) AND date(fecha_gps) BETWEEN '$fecha_ini' AND '$fecha_fin' ORDER BY fecha_grab "; 
        
		$resultado3 = pg_query($conn, $sqlDatos);
		$datos_gps  = pg_fetch_all($resultado3) ;

		if (empty($datos_gps)) {
			$reg = 0;
		}
		else {
			$reg = count($datos_gps);
            $fecha_ini = $datos_gps[0]['fecha_gps'];
		}

		$reg_ok = 0;
		$reg_error = 0;
        $inicio = true;
        $segundos = 200;
        $okOn = 0;

		for ($i=0; $i < $reg; $i++ ) {
			
    		$cp		    = $datos_gps[$i]['cp'];
			$placa		= $datos_gps[$i]['placa'];
			$latitud	= $datos_gps[$i]['latitud'];
			$longitud	= $datos_gps[$i]['longitud'];
			$usuario	= $datos_gps[$i]['usuario'];
			$fecha_ing	= $datos_gps[$i]['fecha_grab'];
			$fecha_gps	= $datos_gps[$i]['fecha_gps'];
			$fecha_on	= $datos_gps[$i]['fecha_gps'];
			$gps		= $datos_gps[$i]['gps'];
			$motivo		= $datos_gps[$i]['motivo'];

             if ($motivo === '4006') {
                
                if ($inicio === false) {

                    $date1 = new DateTime("$fecha_gps");
                    $date2 = new DateTime("$fecha_ini");

                    $diff = $date1->diff($date2);
                    $segundos = ( ($diff->days * 24 ) * 60 ) + ( $diff->i * 60 ) + $diff->s ;

                }

                if ($segundos > 180 ) {

			        $sqlInsert = "INSERT INTO di_datos_bk (driverid, cp, placa, latitud, longitud, usuario, fecha_ing , fecha_gps, gps, motivo, evento) VALUES ('$driverid', '$cp', '$placa', '$latitud', '$longitud', '$usuario', '$fecha_ing' , '$fecha_gps', '$gps', '$motivo', '1') "; 
 
			        $ok = pg_query($conn, $sqlInsert);
                    $inicio = false;
                    $segundos = 0;
                    $okOn = pg_affected_rows($ok);

                    if($okOn == 0) {
                        echo "\nError al instertar Registros ON $sqlInsert \n";
                    }
                }
                else {
                    $okOn = 0;
                    $fecha_ini = $fecha_gps;
                }

            }

			if ($okOn > 0) {

                $reg_ok++;

                $sqlOff = "SELECT '$driverid' AS driverid, g.id AS cp, '$placa' AS placa, g.latitud, g.longitud, '' AS usuario, g.fecha_grab, g.fecha_gps, g.gps, g.motivo FROM gps_$cp g WHERE (g.motivo = 13 OR motivo = 7186) AND g.fecha_gps > '$fecha_gps'::timestamp ORDER BY fecha_grab LIMIT 1 "; 

                $resOff     = pg_query($conn, $sqlOff);
                $datos_off  = pg_fetch_all($resOff) ;

                if (empty($datos_off)) {
                    $reg = 0;
                    $cp		    = $datos_gps[$i]['cp'];
                    $placa		= $datos_gps[$i]['placa'];
                    $latitud	= $datos_gps[$i]['latitud'];
                    $longitud	= $datos_gps[$i]['longitud'];
                    $usuario	= $datos_gps[$i]['usuario'];
                    $fecha_ing	= $datos_gps[$i]['fecha_grab'];
                    $fecha_gps	= $datos_gps[$i]['fecha_gps'];
                    $gps		= $datos_gps[$i]['gps'];
                    $motivo		= $datos_gps[$i]['motivo'];

                    $fecha_gps = strtotime ( '+1 minute' , strtotime ( $fecha_on ) ) ;

                    $sqlInsert = "INSERT INTO di_datos_bk (driverid, cp, placa, latitud, longitud, usuario, fecha_ing , fecha_gps, gps, motivo, evento) VALUES ('$driverid', '$cp', '$placa', '$latitud', '$longitud', '$usuario', '$fecha_ing' , '$fecha_gps', '$gps', '13', '2') "; 

                    $okOff = pg_query($conn, $sqlInsert);

                    if (pg_affected_rows($okOff) > 0) {
                        $reg_ok++;
                    }
                    else {
                        $reg_error++;
                        echo "\nError al instertar Registros Off $sqlInsert \n";
                    }
                }
                else {
                    $cp		    = $datos_off[0]['cp'];
                    $placa		= $datos_off[0]['placa'];
                    $latitud	= $datos_off[0]['latitud'];
                    $longitud	= $datos_off[0]['longitud'];
                    $usuario	= $datos_off[0]['usuario'];
                    $fecha_ing	= $datos_off[0]['fecha_grab'];
                    $fecha_gps	= $datos_off[0]['fecha_gps'];
                    $gps		= $datos_off[0]['gps'];
                    $motivo		= $datos_off[0]['motivo'];

                    if ($fecha_on > $fecha_gps ) {
                        $fecha_gps = strtotime ( '+1 minute' , strtotime ( $fecha_on ) ) ;
                    }

                    $sqlInsert = "INSERT INTO di_datos_bk (driverid, cp, placa, latitud, longitud, usuario, fecha_ing , fecha_gps, gps, motivo, evento) VALUES ('$driverid', '$cp', '$placa', '$latitud', '$longitud', '$usuario', '$fecha_ing' , '$fecha_gps', '$gps', '$motivo', '2') "; 

                    $okOff = pg_query($conn, $sqlInsert);

                    if (pg_affected_rows($okOff) > 0) {
                        $reg_ok++;
                    }
                    else {
                        $reg_error++;
                        echo "\nError al instertar Registros Off $sqlInsert \n";
                    }
                }

                $fecha_ini = $fecha_gps;

			}
		}

		echo "\n$c de $num_conductor Conductores -- $k de $num_tablas -- Tabla: gps_$cp DriverId: $driverid  Registros Ok: $reg_ok Registros Error: $reg_error \n";
	}
}

echo "\nFecha Hora Inicio: $fechaHoraIni  Fecha Hora Fin: ".date("Y-m-d H:i:s") ."\n";

function ConectarDb() {

	$port	= 5432;
	//  $ipdb = "172.17.0.1";
    $ipdb   = "192.168.1.3";
	$base 	= "basegps1_ve";
	$usrdb	= "internet";
	$pwddb	= "101"; 
	
	$conn= pg_connect("host = $ipdb port = $port dbname = $base user = $usrdb password = $pwddb");

	return $conn;
}

?>
