#!/usr/bin/env python3
"""
aplicar_complemento_panama_postgres.py

Script para aplicar / insertar de forma controlada y segura el lote de 2,832 celdas
complementarias de Panamá en la tabla 'geo_total' de PostgreSQL (Producción / Staging).

Uso:
    # 1. Simulación (Dry-Run): Verifica conexión y valida los registros sin escribir nada
    python aplicar_complemento_panama_postgres.py --dry-run --pg-host 127.0.0.1 --pg-port 5432 --pg-db tobodb --pg-user postgres --pg-pass bigBleu5

    # 2. Inserción real con confirmación
    python aplicar_complemento_panama_postgres.py --confirm --pg-host <PROD_HOST> --pg-port 5432 --pg-db tobodb --pg-user postgres --pg-pass "<PROD_PASS>"

    # 3. Inserción permitiendo limpiar lote previo (si se reintenta):
    python aplicar_complemento_panama_postgres.py --confirm --clean-previous --pg-host <PROD_HOST> ...
"""

import sys
import os
import argparse
import logging
import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEFAULT_PG_CONFIG = {
    "dbname": "tobodb",
    "user": "postgres",
    "password": "bigBleu5",
    "host": "127.0.0.1",
    "port": 5432
}

DEFAULT_DUMP_PATH = r"K:\geo_pan_complemento_2026.sql"

def main():
    parser = argparse.ArgumentParser(description="Aplicar complemento de Panamá a PostgreSQL en producción")
    parser.add_argument("--dry-run", action="store_true", help="Simula la operación sin modificar la base de datos")
    parser.add_argument("--confirm", action="store_true", help="Confirma la inserción real en la base de datos")
    parser.add_argument("--clean-previous", action="store_true", help="Elimina registros previos con creation_user=5004 en PAN antes de insertar")
    parser.add_argument("--file", type=str, default=DEFAULT_DUMP_PATH, help=f"Ruta del archivo SQL dump (por defecto: {DEFAULT_DUMP_PATH})")
    parser.add_argument("--pg-host", type=str, default=DEFAULT_PG_CONFIG["host"])
    parser.add_argument("--pg-port", type=int, default=DEFAULT_PG_CONFIG["port"])
    parser.add_argument("--pg-db", type=str, default=DEFAULT_PG_CONFIG["dbname"])
    parser.add_argument("--pg-user", type=str, default=DEFAULT_PG_CONFIG["user"])
    parser.add_argument("--pg-pass", type=str, default=DEFAULT_PG_CONFIG["password"])

    args = parser.parse_args()

    if not args.dry_run and not args.confirm:
        logging.error("Debes especificar --dry-run para simular o --confirm para ejecutar la inserción.")
        sys.exit(1)

    # 1. Validar existencia del archivo de dump
    if not os.path.exists(args.file):
        logging.error(f"No se encontró el archivo de dump en: {args.file}")
        sys.exit(1)

    logging.info(f"Leyendo archivo de dump: {args.file}")
    with open(args.file, "r", encoding="utf-8") as f:
        dump_content = f.read()

    # Contar registros en el dump (líneas entre COPY y \.)
    lines = dump_content.splitlines()
    data_lines = [l for l in lines if l and not l.startswith('--') and not l.startswith('COPY') and l != '\\.']
    total_dump_records = len(data_lines)
    logging.info(f"Registros listos para insertar en el dump: {total_dump_records}")

    # 2. Conectar a PostgreSQL destino
    try:
        conn = psycopg2.connect(
            dbname=args.pg_db,
            user=args.pg_user,
            password=args.pg_pass,
            host=args.pg_host,
            port=args.pg_port
        )
        cur = conn.cursor()
        logging.info(f"Conexión exitosa a PostgreSQL ({args.pg_db}) en {args.pg_host}:{args.pg_port}")
    except Exception as e:
        logging.error(f"Error conectando a PostgreSQL destino: {e}")
        sys.exit(1)

    # 3. Diagnóstico previo en la tabla destino
    cur.execute("SELECT count(*) FROM geo_total WHERE country_code = 'PAN';")
    current_pan = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM geo_total WHERE country_code = 'PAN' AND creation_user = 5004;")
    current_5004 = cur.fetchone()[0]

    logging.info(f"Estado actual en destino: Total registros PAN={current_pan}, de los cuales con usuario 5004={current_5004}")

    # 4. Modo Simulación (Dry-Run)
    if args.dry_run:
        logging.info("--- MODO SIMULACIÓN (DRY-RUN) ---")
        logging.info(f"Se insertarían {total_dump_records} registros en 'geo_total' (country_code='PAN', creation_user=5004).")
        if current_5004 > 0:
            if args.clean_previous:
                logging.info(f"Se limpiarían los {current_5004} registros previos antes de insertar el nuevo lote.")
            else:
                logging.warning(f"Ya existen {current_5004} registros de usuario 5004 en destino. Si se reintenta, añade --clean-previous.")
        logging.info(f"Total estimado tras la operación: {current_pan - (current_5004 if args.clean_previous else 0) + total_dump_records} registros.")
        logging.info("--- FIN DE SIMULACIÓN EXITOSA: Ningún cambio fue aplicado ---")
        cur.close()
        conn.close()
        return

    # 5. Ejecución real controlada
    try:
        # Iniciar transacción explícita
        if args.clean_previous and current_5004 > 0:
            logging.info(f"Limpiando {current_5004} registros previos de usuario 5004 en PAN...")
            cur.execute("DELETE FROM geo_total WHERE country_code = 'PAN' AND creation_user = 5004;")
            logging.info(f"Eliminados: {cur.rowcount} registros.")

        logging.info("Ejecutando COPY de los registros complementarios...")
        import io
        cur.copy_expert(
            "COPY geo_total (id, name, location, display_name, country_code, client_id, color, icon, creation_user, created_at, update_user, updated_at, bbox, h3_cell7, h3_cell5, longitud, latitud) FROM stdin WITH (FORMAT text, NULL '\\N');",
            io.StringIO("\n".join(data_lines) + "\n")
        )

        conn.commit()
        logging.info("¡Transacción completada y confirmada exitosamente (COMMIT)!")
    except Exception as err:
        conn.rollback()
        logging.error(f"Error durante la inserción. Transacción revertida (ROLLBACK): {err}")
        cur.close()
        conn.close()
        sys.exit(1)

    # 6. Verificación post-inserción
    cur.execute("SELECT count(*) FROM geo_total WHERE country_code = 'PAN';")
    new_pan = cur.fetchone()[0]

    cur.execute("SELECT count(*), count(DISTINCT h3_cell7) FROM geo_total WHERE country_code = 'PAN' AND creation_user = 5004;")
    total_new_5004, distinct_h7 = cur.fetchone()

    logging.info("--- VERIFICACIÓN POST-INSERCIÓN ---")
    logging.info(f"Total de registros PAN en geo_total: {new_pan}")
    logging.info(f"Nuevos registros complementarios (usuario 5004): {total_new_5004} (en {distinct_h7} celdas H7 únicas)")
    logging.info("Proceso finalizado con éxito.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
