#!/usr/bin/env python3
"""
populate_georeferences.py

Este script consulta una instancia local de Nominatim (corriendo en Docker),
obtiene georreferencias (coordenadas y polígonos/bounding box), calcula los índices
hexagonales H3 (resoluciones 5 y 7) utilizando la librería oficial de Uber (`h3`),
y los inserta en la tabla `public.geo_total` de la base de datos PostgreSQL (`tobodb`).

Uso:
    python populate_georeferences.py --address "Ciudad de Guatemala, Guatemala"
    python populate_georeferences.py --file lista_direcciones.txt
"""

import sys
import uuid
import argparse
import logging
import requests
import psycopg2

try:
    import h3
except ImportError:
    print("Error: La librería 'h3' no está instalada. Ejecuta: pip install h3")
    sys.exit(1)

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuraciones por defecto
DEFAULT_NOMINATIM_URL = "http://localhost:8080/search"
DEFAULT_DB_CONFIG = {
    "dbname": "tobodb",
    "user": "postgres",
    "password": "",
    "host": "localhost",
    "port": 5432
}

def compute_h3(lat: float, lon: float, resolution: int) -> str:
    """Calcula el índice H3 compatible con h3 v3.x y v4.x."""
    if hasattr(h3, 'latlng_to_cell'):
        return h3.latlng_to_cell(lat, lon, resolution)
    elif hasattr(h3, 'geo_to_h3'):
        return h3.geo_to_h3(lat, lon, resolution)
    else:
        raise RuntimeError("No se pudo encontrar una función válida en la librería h3.")

def geocode_address(address: str, url: str = DEFAULT_NOMINATIM_URL) -> dict:
    """Consulta la API de Nominatim para obtener la georreferencia de una dirección."""
    params = {
        'q': address,
        'format': 'json',
        'addressdetails': 1,
        'limit': 1
    }
    headers = {'User-Agent': 'GeoTotalPopulator/1.0'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        if results and len(results) > 0:
            return results[0]
        else:
            logging.warning(f"No se encontraron resultados para: '{address}'")
            return None
    except requests.RequestException as e:
        logging.error(f"Error consultando Nominatim para '{address}': {e}")
        return None

def ensure_geo_total_table_exists(conn):
    """Crea la extensión PostGIS, la tabla public.geo_total y el enum georeference_icon_enum si no existen."""
    sql = """
    CREATE EXTENSION IF NOT EXISTS postgis;

    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'georeference_icon_enum') THEN
            CREATE TYPE georeference_icon_enum AS ENUM ('1', '2', '3', '4', '5');
        END IF;
    END $$;

    CREATE TABLE IF NOT EXISTS public.geo_total (
        id uuid NOT NULL PRIMARY KEY,
        name text,
        location geometry(Point, 4326),
        display_name text,
        country_code text,
        client_id integer,
        color text,
        icon georeference_icon_enum,
        creation_user integer,
        created_at timestamp without time zone,
        update_user integer,
        updated_at timestamp without time zone,
        bbox geometry(Polygon, 4326),
        h3_cell7 text,
        h3_cell5 text,
        longitud double precision,
        latitud double precision
    );
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()

def insert_georeference(conn, geodata: dict, original_name: str, client_id=None, creation_user: int = 1) -> bool:
    """Inserta la georreferencia procesada en la tabla public.geo_total."""
    try:
        lat = float(geodata['lat'])
        lon = float(geodata['lon'])
        
        # Calcular celdas H3
        h3_cell7 = compute_h3(lat, lon, 7)
        h3_cell5 = compute_h3(lat, lon, 5)
        
        # Procesar Bounding Box si existe: Nominatim devuelve [lat_min, lat_max, lon_min, lon_max]
        bbox_raw = geodata.get('boundingbox')
        bbox_sql_fragment = "NULL"
        bbox_params = []
        
        if bbox_raw and len(bbox_raw) == 4:
            lat_min, lat_max, lon_min, lon_max = map(float, bbox_raw)
            bbox_sql_fragment = "ST_SetSRID(ST_MakeEnvelope(%s, %s, %s, %s), 4326)"
            bbox_params = [lon_min, lat_min, lon_max, lat_max]
        
        # Extraer código de país
        country_code = 'TOT'
        if 'address' in geodata and 'country_code' in geodata['address']:
            country_code = geodata['address']['country_code'].upper()
        
        record_id = str(uuid.uuid4())
        display_name = geodata.get('display_name', original_name)
        
        query = f"""
            INSERT INTO public.geo_total (
                id, name, location, display_name, country_code,
                client_id, color, icon, creation_user, created_at,
                bbox, h3_cell7, h3_cell5, longitud, latitud
            ) VALUES (
                %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s,
                %s, %s, %s, %s, CURRENT_TIMESTAMP,
                {bbox_sql_fragment}, %s, %s, %s, %s
            )
        """
        
        queryParams = [
            record_id,
            original_name,
            lon, lat,
            display_name,
            country_code,
            client_id,
            '#bcbcbc', # color por defecto
            '2',       # icon por defecto
            creation_user
        ] + bbox_params + [
            h3_cell7,
            h3_cell5,
            lon,
            lat
        ]
        
        with conn.cursor() as cur:
            cur.execute(query, queryParams)
        conn.commit()
        logging.info(f" Insertado exitosamente: {original_name} -> Lat: {lat}, Lon: {lon} (H3_7: {h3_cell7})")
        return True

    except Exception as e:
        conn.rollback()
        logging.error(f"Error insertando en base de datos para '{original_name}': {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Poblar la tabla geo_total desde Nominatim y H3")
    parser.add_argument("--address", type=str, help="Dirección o lugar único a georreferenciar")
    parser.add_argument("--file", type=str, help="Ruta a archivo TXT con lista de direcciones (una por línea)")
    parser.add_argument("--url", type=str, default=DEFAULT_NOMINATIM_URL, help="URL del servicio Nominatim")
    parser.add_argument("--dbname", type=str, default=DEFAULT_DB_CONFIG["dbname"], help="Nombre de la BD PostgreSQL")
    parser.add_argument("--user", type=str, default=DEFAULT_DB_CONFIG["user"], help="Usuario PostgreSQL")
    parser.add_argument("--password", type=str, default=DEFAULT_DB_CONFIG["password"], help="Contraseña PostgreSQL")
    parser.add_argument("--host", type=str, default=DEFAULT_DB_CONFIG["host"], help="Host PostgreSQL")
    parser.add_argument("--port", type=int, default=DEFAULT_DB_CONFIG["port"], help="Puerto PostgreSQL")
    
    args = parser.parse_args()
    
    addresses = []
    if args.address:
        addresses.append(args.address)
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                addresses = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logging.error(f"No se pudo leer el archivo {args.file}: {e}")
            sys.exit(1)
    else:
        # Direcciones de prueba por defecto en Centroamérica
        addresses = [
            "Ciudad de Guatemala, Guatemala",
            "San José, Costa Rica",
            "San Salvador, El Salvador",
            "Tegucigalpa, Honduras",
            "Managua, Nicaragua",
            "Ciudad de Panamá, Panamá"
        ]
        logging.info("No se especificó dirección ni archivo. Procesando lista de prueba predeterminada de Centroamérica.")

    # Conectar a PostgreSQL
    try:
        conn = psycopg2.connect(
            dbname=args.dbname,
            user=args.user,
            password=args.password,
            host=args.host,
            port=args.port
        )
        logging.info(f"Conectado exitosamente a PostgreSQL ({args.dbname}@{args.host})")
        ensure_geo_total_table_exists(conn)
    except Exception as e:
        logging.error(f"Error de conexión a PostgreSQL: {e}")
        sys.exit(1)

    try:
        for addr in addresses:
            geodata = geocode_address(addr, url=args.url)
            if geodata:
                insert_georeference(conn, geodata, addr)
    finally:
        conn.close()
        logging.info("Conexión a base de datos cerrada.")

if __name__ == "__main__":
    main()
