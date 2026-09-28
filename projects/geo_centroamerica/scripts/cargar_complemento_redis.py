#!/usr/bin/env python3
"""
cargar_complemento_redis.py

Script para cargar a Redis ÚNICAMENTE el lote de georreferencias complementarias
de Colombia creadas por el usuario 5004 a partir de la fecha de corte.

Uso:
    # 1. Simular carga (ver cuántos registros y celdas se cargarían sin escribir a Redis)
    python cargar_complemento_redis.py --dry-run

    # 2. Cargar directamente a Redis local
    python cargar_complemento_redis.py --redis-host 127.0.0.1 --redis-port 6379 --redis-db 0

    # 3. Cargar hacia pod de producción (vía port-forward)
    python cargar_complemento_redis.py --redis-host 127.0.0.1 --redis-port 6379 --redis-pass "mi_clave"
"""

import sys
import time
import argparse
import logging
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEFAULT_PG_CONFIG = {
    "dbname": "tobodb",
    "user": "postgres",
    "password": "bigBleu5",
    "host": "127.0.0.1",
    "port": 5432
}

def main():
    parser = argparse.ArgumentParser(description="Cargar lote de complemento de Colombia a Redis")
    parser.add_argument("--dry-run", action="store_true", help="Simula la carga sin escribir en Redis")
    parser.add_argument("--user-id", type=int, default=5004, help="ID de usuario creador (por defecto: 5004)")
    parser.add_argument("--date", type=str, default="2026-09-16", help="Fecha mínima de creación (YYYY-MM-DD)")
    parser.add_argument("--batch-size", type=int, default=5000, help="Tamaño de lote para el pipeline de Redis")
    parser.add_argument("--pg-host", type=str, default=DEFAULT_PG_CONFIG["host"])
    parser.add_argument("--pg-port", type=int, default=DEFAULT_PG_CONFIG["port"])
    parser.add_argument("--pg-db", type=str, default=DEFAULT_PG_CONFIG["dbname"])
    parser.add_argument("--pg-user", type=str, default=DEFAULT_PG_CONFIG["user"])
    parser.add_argument("--pg-pass", type=str, default=DEFAULT_PG_CONFIG["password"])
    parser.add_argument("--redis-host", type=str, default="127.0.0.1")
    parser.add_argument("--redis-port", type=int, default=6379)
    parser.add_argument("--redis-db", type=int, default=0)
    parser.add_argument("--redis-pass", type=str, default=None)

    args = parser.parse_args()

    # 1. Conexión a PostgreSQL
    try:
        conn = psycopg2.connect(
            dbname=args.pg_db,
            user=args.pg_user,
            password=args.pg_pass,
            host=args.pg_host,
            port=args.pg_port
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        logging.info(f"Conectado a PostgreSQL ({args.pg_db}) en {args.pg_host}:{args.pg_port}")
    except Exception as e:
        logging.error(f"Error al conectar con PostgreSQL: {e}")
        sys.exit(1)

    # 2. Consultar registros del complemento
    sql = """
        SELECT 
            id || '|' || COALESCE(display_name, name, '') AS name,
            COALESCE(longitud, ST_X(location)) AS longitud,
            COALESCE(latitud, ST_Y(location)) AS latitud,
            'GEO5:' || h3_cell5 AS key5,
            'GEO7:' || h3_cell7 AS key7,
            h3_cell7
        FROM geo_col
        WHERE creation_user = %s
          AND created_at >= %s
          AND h3_cell5 IS NOT NULL
          AND h3_cell7 IS NOT NULL
          AND (longitud IS NOT NULL OR location IS NOT NULL)
        ORDER BY h3_cell7;
    """
    logging.info("Consultando registros en PostgreSQL...")
    cur.execute(sql, (args.user_id, args.date))
    records = cur.fetchall()
    total = len(records)

    celdas_h7_unicas = len(set(r['h3_cell7'] for r in records))
    logging.info(f"Total registros encontrados: {total} distribuidos en {celdas_h7_unicas} celdas H7 únicas.")

    if total == 0:
        logging.warning("No hay registros que coincidan con los criterios de búsqueda.")
        sys.exit(0)

    if args.dry_run:
        logging.info(f"[SIMULACIÓN EXITOSA] Se cargarían {total} puntos en {celdas_h7_unicas} celdas H7 a Redis.")
        sys.exit(0)

    # 3. Conexión a Redis
    try:
        import redis
        r = redis.Redis(
            host=args.redis_host,
            port=args.redis_port,
            db=args.redis_db,
            password=args.redis_pass
        )
        r.ping()
        logging.info(f"Conectado exitosamente a Redis ({args.redis_host}:{args.redis_port}, DB {args.redis_db}).")
    except Exception as e:
        logging.error(f"Error conectando a Redis: {e}")
        sys.exit(1)

    # 4. Inserción con Pipeline
    start_time = time.time()
    pipe = r.pipeline(transaction=False)
    pipe_count = 0
    cargados = 0

    for row in records:
        try:
            lon = float(row['longitud'])
            lat = float(row['latitud'])
            member = str(row['name'])

            pipe.geoadd(row['key5'], (lon, lat, member))
            pipe.geoadd(row['key7'], (lon, lat, member))
            pipe_count += 2
            cargados += 1

            if pipe_count >= args.batch_size:
                pipe.execute()
                pipe_count = 0
                logging.info(f"Cargados {cargados}/{total} registros...")
        except Exception as row_err:
            logging.error(f"Error en fila {row['name']}: {row_err}")

    if pipe_count > 0:
        pipe.execute()

    elapsed = time.time() - start_time
    rate = cargados / elapsed if elapsed > 0 else 0
    logging.info("--- CARGA FINALIZADA CON ÉXITO ---")
    logging.info(f"Total registros inyectados a Redis: {cargados}")
    logging.info(f"Tiempo transcurrido: {elapsed:.2f} s ({rate:.1f} registros/s)")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
