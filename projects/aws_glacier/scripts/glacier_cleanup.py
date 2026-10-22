#!/usr/bin/env python3
"""
Herramienta para inventariar, vaciar y eliminar un Vault de AWS S3 Glacier.
Parte de jp-toolbox (projects/aws_glacier).

Lee automáticamente la configuración desde el archivo .env en la carpeta del proyecto,
o bien permite sobreescribir cualquier valor por línea de comandos (ej. --vault).
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "output"

# Candado de seguridad: Estos Vaults contienen los backups históricos críticos ("joya de la corona")
# y NUNCA deben ser vaciados ni eliminados por este script.
PROTECTED_VAULTS = {"tobo", "tobo4_x_mes"}


def load_dotenv_file(env_path: Path):
    """Carga variables de un archivo .env de forma nativa sin requerir librerías externas."""
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            if key and key not in os.environ and val != "":
                os.environ[key] = val


def get_client(region: str, profile: str = None):
    if not region:
        print("[!] Error: Debes especificar la región (--region o AWS_REGION en .env).", file=sys.stderr)
        sys.exit(1)

    session_kwargs = {"region_name": region}
    if profile:
        session_kwargs["profile_name"] = profile
    elif os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        session_kwargs["aws_access_key_id"] = os.environ["AWS_ACCESS_KEY_ID"]
        session_kwargs["aws_secret_access_key"] = os.environ["AWS_SECRET_ACCESS_KEY"]
        if os.environ.get("AWS_SESSION_TOKEN"):
            session_kwargs["aws_session_token"] = os.environ["AWS_SESSION_TOKEN"]

    session = boto3.Session(**session_kwargs)
    return session.client("glacier")


def require_vault(vault_name: str, destructive: bool = False):
    if not vault_name:
        print("[!] Error: Debes especificar el nombre del Vault (--vault o GLACIER_VAULT en .env).", file=sys.stderr)
        sys.exit(1)
    if destructive and vault_name in PROTECTED_VAULTS:
        print(
            f"[!] BLOQUEO DE SEGURIDAD: El vault '{vault_name}' está en la lista de vaults protegidos "
            f"({', '.join(sorted(PROTECTED_VAULTS))}). Operación destructiva cancelada.",
            file=sys.stderr,
        )
        sys.exit(1)


def get_inventory_path(vault_name: str, custom_path: Path = None) -> Path:
    if custom_path:
        return custom_path
    return DEFAULT_OUTPUT_DIR / f"inventory_{vault_name}.json"


def get_deleted_log_path(vault_name: str) -> Path:
    return DEFAULT_OUTPUT_DIR / f"deleted_{vault_name}.json"


def find_latest_inventory_job(client, vault_name: str) -> dict | None:
    """Busca el trabajo de inventario más reciente (en progreso o completado) en el Vault."""
    response = client.list_jobs(vaultName=vault_name)
    jobs = [j for j in response.get("JobList", []) if j.get("Action") == "InventoryRetrieval"]
    if not jobs:
        return None
    jobs.sort(key=lambda x: x.get("CreationDate", ""), reverse=True)
    return jobs[0]


def list_vaults(client):
    print("[*] Consultando Vaults en la región...")
    try:
        response = client.list_vaults()
        vaults = response.get("VaultList", [])
        if not vaults:
            print("[i] No se encontraron Vaults en esta región.")
            return
        print(f"\n{'Nombre del Vault':<25} {'Estado':<14} {'Archivos':<10} {'Tamaño (MB)':<15} {'Último Inventario'}")
        print("-" * 95)
        for v in vaults:
            name = v["VaultName"]
            status_tag = "[PROTEGIDO]" if name in PROTECTED_VAULTS else ""
            size_mb = v.get("SizeInBytes", 0) / (1024 * 1024)
            last_inv = v.get("LastInventoryDate", "Nunca")
            print(f"{name:<25} {status_tag:<14} {v.get('NumberOfArchives', 0):<10} {size_mb:<15.2f} {last_inv}")
    except ClientError as e:
        print(f"[!] Error al listar vaults: {e}", file=sys.stderr)
        sys.exit(1)


def list_jobs(client, vault_name: str):
    require_vault(vault_name)
    print(f"[*] Consultando trabajos (jobs) recientes en el vault '{vault_name}'...")
    try:
        response = client.list_jobs(vaultName=vault_name)
        jobs = response.get("JobList", [])
        if not jobs:
            print("[i] No hay trabajos activos o recientes para este vault.")
            return
        for j in jobs:
            print(f"- JobId: {j['JobId']}")
            print(f"  Acción: {j.get('Action')} | Estado: {j.get('StatusCode')} | Completado: {j.get('Completed')}")
            print(f"  Creado: {j.get('CreationDate')} | Finalizado: {j.get('CompletionDate', 'Pendiente')}\n")
    except ClientError as e:
        print(f"[!] Error al listar trabajos: {e}", file=sys.stderr)
        sys.exit(1)


def init_inventory(client, vault_name: str) -> str:
    require_vault(vault_name)
    print(f"[*] Solicitando inventario para el vault '{vault_name}'...")
    try:
        response = client.initiate_job(
            vaultName=vault_name,
            jobParameters={"Type": "inventory-retrieval"},
        )
        job_id = response["jobId"]
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        job_meta_file = DEFAULT_OUTPUT_DIR / f"job_{vault_name}.json"
        with open(job_meta_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "VaultName": vault_name,
                    "JobId": job_id,
                    "RequestedAt": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )
        print("[+] Trabajo de inventario iniciado con éxito.")
        print(f"\n    Job ID: {job_id}")
        print(f"    Guardado en: {job_meta_file}\n")
        print("[i] AWS Glacier tarda entre 3 y 5 horas en generar el inventario.")
        print("[i] Nota: Cuando ejecutes 'status', el script detectará este Job ID automáticamente.")
        return job_id
    except ClientError as e:
        print(f"[!] Error al iniciar el inventario: {e}", file=sys.stderr)
        sys.exit(1)


def check_and_download(client, vault_name: str, job_id: str, output_file: Path) -> bool:
    require_vault(vault_name)
    try:
        if not job_id:
            print(f"[*] Buscando el trabajo de inventario más reciente en '{vault_name}'...")
            latest = find_latest_inventory_job(client, vault_name)
            if not latest:
                print("[!] No se encontró ningún trabajo de inventario para este Vault. Ejecuta 'init' primero.", file=sys.stderr)
                sys.exit(1)
            job_id = latest["JobId"]
            print(f"    Job ID detectado automáticamente: {job_id}")

        print(f"[*] Consultando estado del Job en el vault '{vault_name}'...")
        desc = client.describe_job(vaultName=vault_name, jobId=job_id)
        status = desc["StatusCode"]  # InProgress, Succeeded, Failed
        completed = desc["Completed"]

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"    [{now_str}] Estado actual: {status} (Completado: {completed})")

        if status == "Succeeded" and completed:
            print("[*] Descargando resultados del inventario...")
            output = client.get_job_output(vaultName=vault_name, jobId=job_id)
            inventory_data = json.loads(output["body"].read().decode("utf-8"))

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(inventory_data, f, indent=2)

            # Si se descarga un inventario nuevo, reiniciamos el registro de borrados previos de ese vault
            deleted_log = get_deleted_log_path(vault_name)
            if deleted_log.exists():
                deleted_log.unlink()

            archive_count = len(inventory_data.get("ArchiveList", []))
            print(f"[+] Inventario guardado en: {output_file}")
            print(f"[+] Total de archivos encontrados: {archive_count}")
            return True
        elif status == "InProgress":
            print("[i] El trabajo sigue en progreso. AWS suele tardar de 3 a 5 horas.")
            return False
        else:
            print(f"[!] El trabajo terminó con estado: {status} - {desc.get('StatusMessage', '')}", file=sys.stderr)
            sys.exit(1)
    except ClientError as e:
        print(f"[!] Error al consultar/descargar el trabajo: {e}", file=sys.stderr)
        sys.exit(1)


def delete_single_archive(client, vault_name: str, archive_id: str) -> tuple[str, bool, str]:
    try:
        client.delete_archive(vaultName=vault_name, archiveId=archive_id)
        return archive_id, True, ""
    except ClientError as e:
        return archive_id, False, str(e)


def delete_archives(client, vault_name: str, inventory_file: Path, workers: int, limit: int = None):
    require_vault(vault_name, destructive=True)
    if not inventory_file.exists():
        print(f"[!] No existe el archivo de inventario: {inventory_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(inventory_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error leyendo '{inventory_file}': {e}", file=sys.stderr)
        sys.exit(1)

    all_archives = data.get("ArchiveList", [])
    total_inventory = len(all_archives)

    if total_inventory == 0:
        print("[i] El inventario no contiene archivos para eliminar.")
        return

    # Cargar progreso previo por si se está borrando por lotes (--limit)
    deleted_log_path = get_deleted_log_path(vault_name)
    already_deleted = set()
    if deleted_log_path.exists():
        try:
            with open(deleted_log_path, "r", encoding="utf-8") as f:
                already_deleted = set(json.load(f))
        except Exception:
            already_deleted = set()

    pending_archives = [item for item in all_archives if item["ArchiveId"] not in already_deleted]

    if not pending_archives:
        print(f"[i] Todos los {total_inventory} archivos de este inventario ya fueron eliminados previamente.")
        return

    batch = pending_archives[:limit] if (limit and limit > 0) else pending_archives
    total_batch = len(batch)

    print(
        f"[*] Vault '{vault_name}': {total_inventory} en inventario | "
        f"{len(already_deleted)} ya borrados | {len(pending_archives)} pendientes."
    )
    print(f"[*] Eliminando lote de {total_batch} archivos usando {workers} hilos en paralelo...")

    deleted = 0
    failed = 0
    failed_ids = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(delete_single_archive, client, vault_name, item["ArchiveId"]): item["ArchiveId"]
            for item in batch
        }

        for idx, future in enumerate(as_completed(futures), start=1):
            archive_id, ok, err = future.result()
            if ok:
                deleted += 1
                already_deleted.add(archive_id)
            else:
                failed += 1
                failed_ids.append({"ArchiveId": archive_id, "Error": err})

            if idx % 25 == 0 or idx == total_batch:
                print(f"    Progreso del lote: {idx}/{total_batch} (Eliminados: {deleted}, Fallidos: {failed})")

    # Guardar registro actualizado de archivos ya borrados para poder continuar por lotes
    deleted_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(deleted_log_path, "w", encoding="utf-8") as f:
        json.dump(list(already_deleted), f, indent=2)

    remaining = total_inventory - len(already_deleted)
    print(f"\n[+] Lote finalizado. Eliminados ahora: {deleted} | Fallidos: {failed}")
    print(f"[+] Total acumulado eliminado: {len(already_deleted)}/{total_inventory} (Restantes en el Vault: {remaining})")

    if failed_ids:
        err_file = inventory_file.with_suffix(".errors.json")
        with open(err_file, "w", encoding="utf-8") as f:
            json.dump(failed_ids, f, indent=2)
        print(f"[!] Se guardó el detalle de los errores en: {err_file}")


def auto_empty_vault(client, vault_name: str, output_file: Path, workers: int, interval_minutes: int):
    require_vault(vault_name, destructive=True)
    latest = find_latest_inventory_job(client, vault_name)
    if latest and latest.get("StatusCode") in ("InProgress", "Succeeded"):
        job_id = latest["JobId"]
        print(f"[*] Se encontró un trabajo de inventario existente ({latest.get('StatusCode')}): {job_id}")
    else:
        job_id = init_inventory(client, vault_name)

    while True:
        ready = check_and_download(client, vault_name, job_id, output_file)
        if ready:
            break
        print(f"[*] Esperando {interval_minutes} minutos para la siguiente verificación (Ctrl+C para salir sin cancelar el Job en AWS)...")
        time.sleep(interval_minutes * 60)

    delete_archives(client, vault_name, output_file, workers)


def delete_vault(client, vault_name: str):
    require_vault(vault_name, destructive=True)
    print(f"[*] Intentando eliminar el vault '{vault_name}'...")
    try:
        client.delete_vault(vaultName=vault_name)
        print(f"[+] Vault '{vault_name}' eliminado exitosamente.")
    except ClientError as e:
        print(f"[!] Error al eliminar el vault: {e}", file=sys.stderr)
        print("[i] Nota: AWS Glacier actualiza el conteo interno del vault cada ~24 horas.")
        print("    Si acabas de borrar los archivos, debes esperar a que AWS actualice el estado del vault.")
        sys.exit(1)


def main():
    load_dotenv_file(PROJECT_DIR / ".env")

    default_region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    default_vault = os.environ.get("GLACIER_VAULT")
    default_profile = os.environ.get("AWS_PROFILE")
    default_job_id = os.environ.get("GLACIER_JOB_ID")
    default_workers = int(os.environ.get("GLACIER_WORKERS", "15"))

    parser = argparse.ArgumentParser(description="Gestión de inventario y limpieza de Vaults en AWS S3 Glacier")
    parser.add_argument("--region", default=default_region, help="Región de AWS (por defecto lee AWS_REGION de .env)")
    parser.add_argument("--vault", default=default_vault, help="Nombre del Vault (por defecto lee GLACIER_VAULT de .env)")
    parser.add_argument("--profile", default=default_profile, help="Perfil de AWS CLI (opcional)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 0. Listar vaults y jobs
    subparsers.add_parser("list-vaults", help="Lista todos los Vaults en la región y su cantidad de archivos")
    subparsers.add_parser("list-jobs", help="Lista los trabajos activos o recientes del Vault")

    # 1. Iniciar inventario
    subparsers.add_parser("init", help="Inicia el trabajo de recuperación de inventario (tarda 3-5h)")

    # 2. Estado / Descarga
    status_parser = subparsers.add_parser("status", help="Verifica el estado del trabajo y descarga el inventario")
    status_parser.add_argument("--job-id", default=default_job_id, help="Job ID (opcional, si se omite busca el más reciente del Vault)")
    status_parser.add_argument("--output", type=Path, default=None, help="Ruta donde guardar el JSON")

    # 3. Eliminar archivos (con soporte para lotes --limit)
    del_parser = subparsers.add_parser("delete-archives", help="Elimina archivos listados en el inventario (todos o por lotes)")
    del_parser.add_argument("--inventory", type=Path, default=None, help="Ruta al archivo JSON del inventario")
    del_parser.add_argument("--workers", type=int, default=default_workers, help="Hilos en paralelo (por defecto: 15)")
    del_parser.add_argument("--limit", type=int, default=None, help="Cantidad máxima de archivos a borrar en esta ejecución (ej. 100)")

    # 4. Flujo automático completo (init + espera + descarga + delete-archives)
    auto_parser = subparsers.add_parser("auto-empty", help="Inicia o retoma el inventario, espera a que esté listo y borra todos los archivos")
    auto_parser.add_argument("--workers", type=int, default=default_workers, help="Hilos en paralelo (por defecto: 15)")
    auto_parser.add_argument("--interval", type=int, default=15, help="Minutos entre cada consulta a AWS (por defecto: 15)")

    # 5. Eliminar vault
    subparsers.add_parser("delete-vault", help="Elimina el vault vacío")

    args = parser.parse_args()
    client = get_client(args.region, args.profile)

    if args.command == "list-vaults":
        list_vaults(client)
    elif args.command == "list-jobs":
        list_jobs(client, args.vault)
    elif args.command == "init":
        init_inventory(client, args.vault)
    elif args.command == "status":
        out_path = get_inventory_path(args.vault, args.output)
        check_and_download(client, args.vault, args.job_id, out_path)
    elif args.command == "delete-archives":
        inv_path = get_inventory_path(args.vault, args.inventory)
        delete_archives(client, args.vault, inv_path, args.workers, args.limit)
    elif args.command == "auto-empty":
        out_path = get_inventory_path(args.vault)
        auto_empty_vault(client, args.vault, out_path, args.workers, args.interval)
    elif args.command == "delete-vault":
        delete_vault(client, args.vault)


if __name__ == "__main__":
    main()
