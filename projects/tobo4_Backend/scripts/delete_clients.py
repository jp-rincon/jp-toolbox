import csv
import time
import argparse
import sys
import logging
import os
import re
from datetime import datetime
import requests

# Configuración del registro (logging)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"delete_clients_log_{timestamp}.log"
results_csv_filename = f"delete_clients_results_{timestamp}.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_processed_clients(skip_csv_path: str):
    """Carga los client_id que ya fueron eliminados exitosamente en ejecuciones anteriores."""
    successful_ids = set()
    if not skip_csv_path or not os.path.exists(skip_csv_path):
        return successful_ids

    try:
        with open(skip_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "SUCCESS":
                    c_id = row.get("client_id")
                    if c_id:
                        successful_ids.add(c_id.strip())
        logging.info(f"Se cargaron {len(successful_ids)} clientes previamente eliminados de '{skip_csv_path}'. Serán omitidos.")
    except Exception as e:
        logging.warning(f"No se pudo leer el archivo de salto '{skip_csv_path}': {e}")
    
    return successful_ids

def run_deletion(csv_file_path: str, base_url: str, token: str, delay: float, batch_size: int, batch_pause: float, timeout: int, max_retries: int, skip_csv: str, start_row: int):
    base_url = base_url.rstrip("/")
    
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Cargar IDs a ignorar si se provee un CSV de resultados previo
    already_deleted_ids = load_processed_clients(skip_csv)

    logging.info(f"============================================================")
    logging.info(f"INICIANDO PROCESO DE ELIMINACIÓN SEGURA MASIVA")
    logging.info(f"Archivo de entrada: {csv_file_path}")
    logging.info(f"URL Base API: {base_url}")
    logging.info(f"Fila de inicio: {start_row}")
    logging.info(f"Pausa entre peticiones (delay): {delay}s")
    logging.info(f"Descanso por lote: {batch_pause}s cada {batch_size} peticiones")
    logging.info(f"Timeout por petición: {timeout}s | Max reintentos: {max_retries}")
    logging.info(f"============================================================")

    # Leer CSV de clientes
    raw_clients_to_delete = []
    try:
        with open(csv_file_path, mode="r", encoding="utf-8-sig") as f:
            content = f.read()
            if not content.strip():
                logging.error("El archivo CSV está vacío.")
                sys.exit(1)

            sample = content[:4096]
            delimiter = ','
            if ';' in sample and sample.count(';') >= sample.count(','):
                delimiter = ';'
            elif '|' in sample and sample.count('|') >= sample.count(','):
                delimiter = '|'
            elif '\t' in sample and sample.count('\t') >= sample.count(','):
                delimiter = '\t'

            f_lines = content.splitlines()
            reader = list(csv.reader(f_lines, delimiter=delimiter))

            if not reader:
                logging.error("El archivo CSV no contiene líneas de datos.")
                sys.exit(1)

            first_row = [field.strip() for field in reader[0]]

            first_field_clean = re.sub(r'["\']', '', first_row[0]) if first_row else ""
            has_header = not first_field_clean.isdigit()

            id_idx = 0
            account_id_idx = 1 if len(first_row) > 1 else 0

            if has_header:
                clean_headers = [h.lower().replace('"', '').replace("'", "") for h in first_row]

                for idx, h in enumerate(clean_headers):
                    if h in ("id", "client_id", "clientid", "id_cliente"):
                        id_idx = idx
                    elif h in ("account_id", "accountid", "id_account", "account"):
                        account_id_idx = idx
                
                rows_to_process = reader[1:]
            else:
                rows_to_process = reader

            for row_idx, row in enumerate(rows_to_process, start=1):
                if not row or not any(field.strip() for field in row):
                    continue
                
                c_id = row[id_idx].strip() if id_idx < len(row) else ""
                a_id = row[account_id_idx].strip() if account_id_idx < len(row) else ""

                if c_id and a_id:
                    raw_clients_to_delete.append({
                        "original_row": row_idx,
                        "id": c_id,
                        "account_id": a_id
                    })
                else:
                    logging.warning(f"Fila {row_idx} omitida por valores vacíos: {row}")

    except Exception as e:
        logging.error(f"Error al leer el archivo CSV '{csv_file_path}': {e}")
        sys.exit(1)

    total_raw = len(raw_clients_to_delete)
    if total_raw == 0:
        logging.info("No se encontraron registros válidos para procesar en el archivo CSV.")
        sys.exit(0)

    # Filtrar según start_row e IDs procesados previamente
    clients_to_delete = []
    skipped_by_offset = 0

    for client in raw_clients_to_delete:
        if client["original_row"] < start_row:
            skipped_by_offset += 1
            continue
        if client["id"] in already_deleted_ids:
            continue
        clients_to_delete.append(client)

    total_clients = len(clients_to_delete)
    if total_clients == 0:
        logging.info(f"Todos los registros (a partir de la fila {start_row}) ya fueron procesados o eliminados.")
        sys.exit(0)

    logging.info(f"Registros omitidos por inicio en fila {start_row}: {skipped_by_offset}")
    logging.info(f"Total de registros a procesar en esta tanda: {total_clients} (de un total de {total_raw} en el CSV)")

    success_count = 0
    fail_count = 0
    skipped_count = len(already_deleted_ids) + skipped_by_offset

    # Preparar archivo CSV de resultados
    with open(results_csv_filename, mode="w", newline="", encoding="utf-8") as res_file:
        res_writer = csv.writer(res_file)
        res_writer.writerow(["client_id", "account_id", "status", "http_code", "response_message"])

        for idx, client in enumerate(clients_to_delete, start=1):
            c_id = client["id"]
            a_id = client["account_id"]
            orig_row = client["original_row"]
            
            url = f"{base_url}/client?id={c_id}&accountId={a_id}"
            
            logging.info(f"[{idx}/{total_clients}] [Fila original #{orig_row}] Eliminando Cliente ID: {c_id} (AccountId: {a_id})...")

            response_ok = False
            for attempt in range(1, max_retries + 1):
                try:
                    response = requests.delete(url, headers=headers, timeout=timeout)
                    status_code = response.status_code

                    if status_code in (200, 204):
                        logging.info(f" -> ✅ [EXITO] Cliente {c_id} eliminado correctamente. Code: {status_code}")
                        res_writer.writerow([c_id, a_id, "SUCCESS", status_code, "Eliminado exitosamente"])
                        success_count += 1
                        response_ok = True

                    elif status_code == 404:
                        logging.warning(f" -> ⚠️ [NO ENCONTRADO] Cliente {c_id} no existe en la BD o ya fue eliminado (Code 404).")
                        res_writer.writerow([c_id, a_id, "NOT_FOUND", 404, response.text])
                        fail_count += 1
                        response_ok = True

                    elif status_code == 401:
                        logging.error(f" -> ❌ [ERROR AUTH 401] Token expirado o inválido. Respuesta: {response.text}. Deteniendo script.")
                        res_writer.writerow([c_id, a_id, "UNAUTHORIZED", 401, response.text])
                        fail_count += 1
                        response_ok = True
                        sys.exit(1)

                    elif status_code == 403:
                        logging.warning(f" -> ⚠️ [FORBIDDEN 403] Permisos insuficientes para eliminar usuario del cliente {c_id}. Respuesta: {response.text}")
                        res_writer.writerow([c_id, a_id, "FORBIDDEN", 403, response.text])
                        fail_count += 1
                        response_ok = True

                    else:
                        logging.error(f" -> ❌ [ERROR HTTP {status_code}] Falló cliente {c_id}. Respuesta: {response.text}")
                        if attempt < max_retries:
                            logging.info(f"    Intentando nuevamente ({attempt}/{max_retries}) en 5 segundos...")
                            time.sleep(5)
                            continue
                        res_writer.writerow([c_id, a_id, "FAILED", status_code, response.text])
                        fail_count += 1

                except requests.exceptions.RequestException as req_err:
                    logging.error(f" -> ❌ [NETWORK EXCEPTION] Intento {attempt}/{max_retries} falló para cliente {c_id}: {req_err}")
                    if attempt < max_retries:
                        time.sleep(5)
                        continue
                    res_writer.writerow([c_id, a_id, "NETWORK_ERROR", 0, str(req_err)])
                    fail_count += 1

                break # Salir del bucle de reintentos si ya se procesó

            # Pausa breve entre cada cliente individual
            if delay > 0 and idx < total_clients:
                time.sleep(delay)

            # Pausa de lote (Batch Pause) para dejar respirar al servidor y base de datos
            if batch_size > 0 and idx % batch_size == 0 and idx < total_clients:
                logging.info(f"--- ⏸️ Lote de {batch_size} clientes completado. Pausa de descanso del servidor por {batch_pause}s ---")
                time.sleep(batch_pause)

    logging.info("=" * 60)
    logging.info("PROCESO FINALIZADO")
    logging.info(f"Exitosos: {success_count} | Omitidos previos/offset: {skipped_count} | Fallidos: {fail_count} | Procesados en tanda: {total_clients}")
    logging.info(f"Log detallado: {log_filename}")
    logging.info(f"CSV de resultados: {results_csv_filename}")
    logging.info("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para eliminar clientes de manera segura y controlada vía API Backend.")
    parser.add_argument("--csv", required=True, help="Ruta al archivo CSV con las columnas 'id' y 'account_id'")
    parser.add_argument("--url", required=True, help="URL base de la API Backend (ej: https://appv2.huntertrack.com.do/api/core)")
    parser.add_argument("--token", required=True, help="Bearer Token JWT de un usuario con permisos (ACCOUNT_ADM o SU)")
    parser.add_argument("--delay", type=float, default=2.0, help="Pausa en segundos entre cada cliente individual (default: 2.0s)")
    parser.add_argument("--batch-size", type=int, default=20, help="Número de clientes por lote antes de hacer una pausa más larga (default: 20)")
    parser.add_argument("--batch-pause", type=float, default=10.0, help="Tiempo de descanso en segundos entre lotes (default: 10.0s)")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout de la petición HTTP en segundos (default: 60s)")
    parser.add_argument("--max-retries", type=int, default=2, help="Número de reintentos por cliente si falla la conexión (default: 2)")
    parser.add_argument("--skip-results", type=str, default="", help="Ruta a un CSV de resultados anterior para omitir los clientes que ya fueron eliminados con éxito (status SUCCESS)")
    parser.add_argument("--start-row", type=int, default=1, help="Número de fila inicial desde la cual comenzar a procesar (default: 1)")

    args = parser.parse_args()
    run_deletion(
        csv_file_path=args.csv,
        base_url=args.url,
        token=args.token,
        delay=args.delay,
        batch_size=args.batch_size,
        batch_pause=args.batch_pause,
        timeout=args.timeout,
        max_retries=args.max_retries,
        skip_csv=args.skip_results,
        start_row=args.start_row
    )
