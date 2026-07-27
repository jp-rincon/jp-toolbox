#!/usr/bin/env python3
"""
Script para poblar la tabla public.geo_total con todas las calles (highways) 
de un país específico de Centroamérica (ej: 'pa' para Panamá) extraídas de Nominatim.

Uso:
    wsl python3 populate_country_streets.py --country pa --password bigBleu5
"""

import sys
import uuid
import csv
import argparse
import logging
import subprocess
import psycopg2
from psycopg2.extras import execute_values

try:
    import h3
except ImportError:
    print("Error: La librería 'h3' no está instalada en WSL. Ejecuta: pip3 install h3 --break-system-packages")
    sys.exit(1)

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuraciones por defecto
DEFAULT_DB_CONFIG = {
    "dbname": "tobodb",
    "user": "postgres",
    "password": "bigBleu5",
    "host": "127.0.0.1",
    "port": 5432
}

def compute_h3(lat: float, lon: float, resolution: int) -> str:
    """Calcula el índice H3 de forma compatible con h3 v3.x y v4.x."""
    if hasattr(h3, 'latlng_to_cell'):
        return h3.latlng_to_cell(lat, lon, resolution)
    elif hasattr(h3, 'geo_to_h3'):
        return h3.geo_to_h3(lat, lon, resolution)
    else:
        raise RuntimeError("No se pudo encontrar la función H3 en la librería.")

def ensure_geo_total_table_exists(conn):
    """Crea la tabla geo_total y el enum si no existen en el PostgreSQL de destino."""
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

def fetch_streets_from_nominatim(country_code: str) -> list:
    """
    Ejecuta un comando COPY de PostgreSQL a través de docker exec para extraer 
    las calles y sus jerarquías de padres desde el contenedor Nominatim.
    """
    country_code = country_code.lower()
    
    # Consulta SQL estructurada para extraer calles y jerarquías
    sql_query = f"""
    COPY (
        SELECT 
            p.name->'name' as street, 
            (
                SELECT string_agg(parent.name->'name', ', ' ORDER BY parent.rank_address DESC) 
                FROM place_addressline a 
                JOIN placex parent ON a.address_place_id = parent.place_id 
                WHERE a.place_id = p.place_id 
                  AND parent.name->'name' IS NOT NULL 
                  AND a.isaddress = true 
                  AND parent.rank_address < p.rank_address
            ) as parents, 
            ST_Y(centroid) as lat, 
            ST_X(centroid) as lon 
        FROM placex p 
        WHERE p.country_code = '{country_code}' 
          AND p.name->'name' IS NOT NULL 
          AND p.class = 'highway'
    ) TO STDOUT WITH CSV HEADER;
    """
    
    cmd = [
        "docker", "exec", "-u", "postgres", "-i", "nominatim",
        "psql", "-d", "nominatim", "-c", sql_query
    ]
    
    logging.info(f"Iniciando extracción de calles para país '{country_code}' desde el contenedor Nominatim...")
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        return process
    except Exception as e:
        logging.error(f"Error ejecutando comando docker exec: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Poblar la tabla geo_total con las calles de un país desde Nominatim")
    parser.add_argument("--country", type=str, required=True, help="Código de país de dos letras (ej: pa, gt, cr, sv, hn, ni)")
    parser.add_argument("--dbname", type=str, default=DEFAULT_DB_CONFIG["dbname"], help="Nombre de la BD PostgreSQL")
    parser.add_argument("--user", type=str, default=DEFAULT_DB_CONFIG["user"], help="Usuario PostgreSQL")
    parser.add_argument("--password", type=str, default=DEFAULT_DB_CONFIG["password"], help="Contraseña PostgreSQL")
    parser.add_argument("--host", type=str, default=DEFAULT_DB_CONFIG["host"], help="Host PostgreSQL")
    parser.add_argument("--port", type=int, default=DEFAULT_DB_CONFIG["port"], help="Puerto PostgreSQL")
    
    args = parser.parse_args()
    
    # Conectar a la base de datos de destino (tobodb)
    try:
        conn = psycopg2.connect(
            dbname=args.dbname,
            user=args.user,
            password=args.password,
            host=args.host,
            port=args.port
        )
        logging.info(f"Conectado a la base de datos destino '{args.dbname}' en {args.host}.")
        ensure_geo_total_table_exists(conn)
    except Exception as e:
        logging.error(f"Error conectando a PostgreSQL de destino: {e}")
        sys.exit(1)
        
    # Iniciar flujo desde el contenedor Nominatim
    process = fetch_streets_from_nominatim(args.country)
    
    reader = csv.DictReader(process.stdout)
    batch = []
    batch_size = 1000
    total_processed = 0
    
    insert_query = """
        INSERT INTO public.geo_total (
            id, name, location, display_name, country_code,
            client_id, color, icon, creation_user, created_at,
            bbox, h3_cell7, h3_cell5, longitud, latitud
        ) VALUES %s
        ON CONFLICT (id) DO NOTHING;
    """
    
    try:
        for row in reader:
            street = row.get('street')
            parents = row.get('parents')
            
            # Formatear el nombre completo
            if parents:
                full_name = f"{street}, {parents}"
            else:
                full_name = street
                
            try:
                lat = float(row.get('lat'))
                lon = float(row.get('lon'))
            except (TypeError, ValueError):
                continue
                
            # Calcular celdas H3
            try:
                h3_7 = compute_h3(lat, lon, 7)
                h3_5 = compute_h3(lat, lon, 5)
            except Exception as e:
                logging.debug(f"No se pudo calcular H3 para {full_name}: {e}")
                continue
                
            record_id = str(uuid.uuid4())
            
            # Preparar tupla de inserción
            # location es una cadena WKT que PostGIS interpretará al insertar mediante el casting ::geometry
            location_wkt = f"SRID=4326;POINT({lon} {lat})"
            
            batch.append((
                record_id,
                full_name,
                location_wkt,
                full_name,
                "TOT",        # country_code 'TOT' como en los registros del ejemplo
                None,         # client_id
                "#bcbcbc",    # color
                "2",          # icon
                1,            # creation_user
                None,         # bbox
                h3_7,
                h3_5,
                lon,
                lat
            ))
            
            if len(batch) >= batch_size:
                with conn.cursor() as cur:
                    # Usamos psycopg2.extras.execute_values para un rendimiento ultra rápido
                    # casteamos el tercer parámetro como geometry
                    execute_values(
                        cur, 
                        insert_query.replace("VALUES %s", "VALUES %s"), 
                        batch, 
                        template="(%s, %s, %s::geometry, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)"
                    )
                conn.commit()
                total_processed += len(batch)
                logging.info(f"Insertados {total_processed} registros...")
                batch = []
                
        # Insertar remanente
        if batch:
            with conn.cursor() as cur:
                execute_values(
                    cur, 
                    insert_query, 
                    batch, 
                    template="(%s, %s, %s::geometry, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)"
                )
            conn.commit()
            total_processed += len(batch)
            
        logging.info(f"Finalizado. Se poblaron con éxito {total_processed} georreferencias de calles para '{args.country}'.")
        
    except Exception as e:
        logging.error(f"Error durante la inserción masiva: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
