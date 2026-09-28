#!/usr/bin/env python3
"""
reversar_complemento_colombia.py

Script de reversión segura (botón de pánico/deshacer):
Permite revertir automáticamente tanto en PostgreSQL (tobodb.geo_col) como en Redis
todos los registros complementarios creados para Colombia por el usuario 5004.

Uso:
    # 1. Modo Simulación (Dry-Run): Solo cuenta cuántos registros revertiría sin borrar nada
    python reversar_complemento_colombia.py --dry-run

    # 2. Reversión solo en PostgreSQL
    python reversar_complemento_colombia.py --confirm

    # 3. Reversión en PostgreSQL Y en Redis (producción)
    python reversar_complemento_colombia.py --confirm --redis-host 127.0.0.1 --redis-port 6379 --redis-db 0
"""

import sys
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
    parser = argparse.ArgumentParser(description="Revertir de forma segura el complemento de georreferencias de Colombia")
    parser.add_argument("--dry-run", action="store_true", help="Simula la reversión sin borrar nada")
    parser.add_argument("--confirm", action="store_true", help="Confirma la ejecución real del borrado")
    parser.add_argument("--user-id", type=int, default=5004, help="ID de usuario de creación (por defecto: 5004)")
    parser.add_argument("--date", type=str, default="2026-09-16", help="Fecha mínima de creación (YYYY-MM-DD)")
    parser.add_argument("--pg-host", type=str, default=DEFAULT_PG_CONFIG["host"])
    parser.add_argument("--pg-port", type=int, default=DEFAULT_PG_CONFIG["port"])
    parser.add_argument("--pg-db", type=str, default=DEFAULT_PG_CONFIG["dbname"])
    parser.add_argument("--pg-user", type=str, default=DEFAULT_PG_CONFIG["user"])
    parser.add_argument("--pg-pass", type=str, default=DEFAULT_PG_CONFIG["password"])
    parser.add_argument("--redis-host", type=str, default=None, help="Host de Redis si también se desea limpiar Redis")
    parser.add_argument("--redis-port", type=int, default=6379)
    parser.add_argument("--redis-db", type=int, default=0)
    parser.add_argument("--redis-pass", type=str, default=None)

    args = parser.parse_args()

    if not args.dry_run and not args.confirm:
        logging.error("Debes especificar --dry-run para simular o --confirm para ejecutar la reversión.")
        sys.exit(1)

    # 1. Conectar a PostgreSQL
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
        logging.error(f"Error conectando a PostgreSQL: {e}")
        sys.exit(1)

    # 2. Consultar registros a revertir
    select_sql = """
        SELECT id, COALESCE(display_name, name, '') AS name, h3_cell5, h3_cell7
        FROM geo_col
        WHERE creation_user = %s
          AND created_at >= %s;
    """
    cur.execute(select_sql, (args.user_id, args.date))
    records = cur.fetchall()
    total = len(records)

    logging.info(f"Registros encontrados para revertir (User: {args.user_id}, Fecha >= {args.date}): {total}")

    if total == 0:
        logging.info("No hay registros que cumplan las condiciones para revertir.")
        sys.exit(0)

    if args.dry_run:
        logging.info(f"[SIMULACIÓN] Se eliminarían {total} registros en PostgreSQL y sus llaves correspondientes en Redis.")
        sys.exit(0)

    # 3. Limpiar en Redis si se especificó host
    if args.redis_host:
        try:
            import redis
            r = redis.Redis(host=args.redis_host, port=args.redis_port, db=args.redis_db, password=args.redis_pass)
            r.ping()
            logging.info(f"Conectado a Redis en {args.redis_host}:{args.redis_port} (DB {args.redis_db})")

            pipe = r.pipeline(transaction=False)
            deleted_keys = set()
            count = 0

            for row in records:
                member = f"{row['id']}|{row['name']}"
                key5 = f"GEO5:{row['h3_cell5']}"
                key7 = f"GEO7:{row['h3_cell7']}"

                # Eliminar miembro de GEO5
                pipe.zrem(key5, member)
                # Eliminar miembro o llave completa de GEO7
                pipe.zrem(key7, member)
                deleted_keys.add(key7)

                count += 1
                if count % 2000 == 0:
                    pipe.execute()

            # También eliminar llaves GEO7 que quedaron vacías
            for k in deleted_keys:
                pipe.delete(k)

            pipe.execute()
            logging.info(f"Limpieza en Redis completada para {total} registros.")
        except Exception as e:
            logging.error(f"Error limpiando en Redis: {e}")
            sys.exit(1)

    # 4. Eliminar en PostgreSQL
    delete_sql = """
        DELETE FROM geo_col
        WHERE creation_user = %s
          AND created_at >= %s;
    """
    cur.execute(delete_sql, (args.user_id, args.date))
    conn.commit()
    logging.info(f"Éxito: Se eliminaron {cur.rowcount} registros de tobodb.geo_col.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
