#!/usr/bin/env python3
"""
reversar_complemento_panama.py

Script de reversión segura (botón de pánico/deshacer):
Permite revertir automáticamente tanto en PostgreSQL (tobodb.geo_total) como en Redis
todos los registros complementarios creados para Panamá por el usuario 5004.

Uso:
    # 1. Modo Simulación (Dry-Run): Solo cuenta cuántos registros revertiría sin borrar nada
    python reversar_complemento_panama.py --dry-run

    # 2. Reversión solo en PostgreSQL
    python reversar_complemento_panama.py --confirm

    # 3. Reversión en PostgreSQL Y en Redis (producción)
    python reversar_complemento_panama.py --confirm --redis-host 127.0.0.1 --redis-port 6379 --redis-db 0
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
    parser = argparse.ArgumentParser(description="Revertir de forma segura el complemento de georreferencias de Panamá")
    parser.add_argument("--dry-run", action="store_true", help="Simula la reversión sin borrar nada")
    parser.add_argument("--confirm", action="store_true", help="Confirma la ejecución real del borrado")
    parser.add_argument("--user-id", type=int, default=5004, help="ID de usuario de creación (por defecto: 5004)")
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
    except Exception as e:
        logging.error(f"Error conectando a PostgreSQL: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    # 2. Consultar registros a revertir
    query_select = """
        SELECT id, h3_cell7, h3_cell5, name 
        FROM geo_total 
        WHERE country_code = 'PAN' 
          AND creation_user = %s;
    """
    cursor.execute(query_select, (args.user_id,))
    rows = cursor.fetchall()
    total_revertir = len(rows)

    logging.info(f"Registros encontrados para revertir en geo_total (PAN, usuario={args.user_id}): {total_revertir}")

    if total_revertir == 0:
        logging.info("No hay registros que coincidan con los criterios. Finalizando.")
        cursor.close()
        conn.close()
        return

    # 3. Modo Dry-Run
    if args.dry_run:
        logging.info("--- MODO SIMULACIÓN (DRY-RUN) ---")
        logging.info(f"Se eliminarían {total_revertir} registros de PostgreSQL en 'geo_total'.")
        logging.info(f"Ejemplo de registros a eliminar:")
        for r in rows[:5]:
            logging.info(f"  ID: {r[0]}, H7: {r[1]}, Ref: {r[3]}")
        if args.redis_host:
            logging.info(f"En Redis ({args.redis_host}:{args.redis_port}) se eliminarían las claves correspondientes.")
        logging.info("--- FIN SIMULACIÓN: No se realizaron cambios ---")
        cursor.close()
        conn.close()
        return

    # 4. Reversión en Redis (si se solicita)
    if args.redis_host:
        try:
            import redis
            r_client = redis.Redis(
                host=args.redis_host,
                port=args.redis_port,
                db=args.redis_db,
                password=args.redis_pass,
                decode_responses=True
            )
            r_client.ping()
            logging.info("Conexión exitosa a Redis. Limpiando celdas complementarias...")
            
            pipe = r_client.pipeline()
            redis_del_count = 0
            for row in rows:
                h7 = row[1]
                h5 = row[2]
                if h7:
                    pipe.delete(f"geo:h3:7:{h7}")
                    redis_del_count += 1
                if h5:
                    pipe.delete(f"geo:h3:5:{h5}")
            pipe.execute()
            logging.info(f"Comandos de eliminación enviados a Redis ({redis_del_count} claves H7).")
        except Exception as e:
            logging.error(f"Error operando en Redis: {e}")
            logging.warning("No se procederá con el borrado en PostgreSQL para evitar desincronización.")
            cursor.close()
            conn.close()
            sys.exit(1)

    # 5. Reversión en PostgreSQL
    logging.info(f"Procediendo a eliminar {total_revertir} registros de geo_total...")
    query_delete = """
        DELETE FROM geo_total 
        WHERE country_code = 'PAN' 
          AND creation_user = %s;
    """
    cursor.execute(query_delete, (args.user_id,))
    conn.commit()
    logging.info(f"Reversión completada exitosamente en PostgreSQL. Registros eliminados: {cursor.rowcount}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
