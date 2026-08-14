# Este Script sirve para subir las georeferencias al redis de producción, haciendo port-forward al pod correspondiente.
# Se debe alterar la configuración en el archivo conf_v4.cfg apuntando al servidor y puerto correspondientes.
# Esto importa desde la base de postgres local, tabla geo_total la info correspondiente. (Se debe copiar el script a Backend/python-receiver/ para que encuentre la conf_v4.cfg).
import sys
import os
import time
import psycopg2
import psycopg2.extras
import redis

# Asegurar que el directorio de python-receiver esté en el sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from ProcesadorBaseDatos.ConexionMaster_v4 import ConectarBD
from ProcesadorVarios.leerConfigDB_v4 import LeerConfigDB


class ClassRedis:
    def __init__(self):
        try:
            self.ConDB = ConectarBD()
            self.ConnMaster = self.ConDB.HacerConexionGeoV1()
            if self.ConnMaster == -1:
                print("Error: No se pudo establecer conexión con PostgreSQL (ConnMaster).")
        except Exception as inst:
            print("Error al inicializar conexión Postgres (ConnMaster):", inst)
            self.ConnMaster = -1

        try:
            config = LeerConfigDB()
            config.LeerVariablesDB()
            host = getattr(config, 'ip_redis_geo', None) or getattr(config, 'ip_redis', None) or '127.0.0.1'
            port_val = getattr(config, 'puerto_redis_geo', None) or getattr(config, 'puerto_redis', None) or 6379
            try:
                port = int(str(port_val).strip().replace("'", ""))
            except Exception:
                port = 6379

            db_val = getattr(config, 'base_redis_geo', None) or getattr(config, 'base_redis', None) or 0
            try:
                db = int(str(db_val).strip().replace("'", ""))
            except Exception:
                db = 0

            pwd = getattr(config, 'clave_redis_geo', None) or getattr(config, 'clave_redis', None) or None
            if pwd:
                pwd = str(pwd).strip().replace("'", "")

            print(f"Conectando a Redis: {host}:{port} (db={db})...")
            self.Redis1 = redis.Redis(host=host, port=port, db=db, password=pwd if pwd else None)
            self.Redis1.ping()
            print(f"Conexión exitosa a Redis DB {db} ({host}:{port}).")
        except Exception as err:
            print("Error al conectar a Redis:", err)
            self.Redis1 = -1

    def cargarGeoRef_v1(self, batch_size=5000, max_records=None):
        print("--- Iniciando Carga de Georreferencias a Redis (Celdas H3) ---")
        start_time = time.time()

        if self.ConnMaster == -1 or self.Redis1 == -1:
            print("Error: Conexiones no inicializadas correctamente.")
            return -1

        try:
            cursor_activos = self.ConnMaster.cursor(
                cursor_factory=psycopg2.extras.NamedTupleCursor
            )
        except Exception as inst:
            print("Error al definir cursor de PostgreSQL:", inst)
            return -1

        try:
            sql_activos = """
                SELECT 
                    id || '|' || COALESCE(display_name, name, '') AS name, 
                    COALESCE(longitud, ST_X(location)) AS longitud, 
                    COALESCE(latitud, ST_Y(location)) AS latitud, 
                    'GEO5:' || h3_cell5 AS key5, 
                    'GEO7:' || h3_cell7 AS key7 
                FROM geo_total 
                WHERE client_id IS NULL 
                  AND h3_cell5 IS NOT NULL 
                  AND h3_cell7 IS NOT NULL 
                  AND (longitud IS NOT NULL OR location IS NOT NULL)
                ORDER BY h3_cell7;
            """
            print("Ejecutando consulta SQL en PostgreSQL...")
            cursor_activos.execute(sql_activos)

        except Exception as inst:
            print("Error al ejecutar SQL activos:", inst)
            return -1

        georef = cursor_activos.fetchall()
        total_rows = len(georef)
        print(f"Registros obtenidos de PostgreSQL: {total_rows}")

        if total_rows == 0:
            print("No se encontraron registros para cargar.")
            return 0

        # Pipelining para inserción de alta velocidad en Redis
        try:
            pipe = self.Redis1.pipeline(transaction=False)
            l = 0
            pipe_count = 0

            for cur in georef:
                if max_records and l >= max_records:
                    break

                try:
                    lon = float(cur.longitud)
                    lat = float(cur.latitud)
                    member = str(cur.name)

                    # Inserción en llave GEO5 y GEO7
                    pipe.geoadd(cur.key5, (lon, lat, member))
                    pipe.geoadd(cur.key7, (lon, lat, member))
                    pipe_count += 2
                    l += 1

                    # Ejecutar pipeline por lotes
                    if pipe_count >= batch_size:
                        pipe.execute()
                        pipe_count = 0
                        print(f"Cargados {l}/{total_rows} registros a Redis...")

                except Exception as row_err:
                    print(f"Error procesando registro {cur.name}: {row_err}")

            # Flush final del pipeline si quedan comandos pendientes
            if pipe_count > 0:
                pipe.execute()

            elapsed_time = time.time() - start_time
            rate = l / elapsed_time if elapsed_time > 0 else 0
            print(f"--- Carga Finalizada Exitosamente ---")
            print(f"Total procesados: {l} registros")
            print(f"Tiempo transcurrido: {elapsed_time:.2f} segundos")
            print(f"Velocidad: {rate:.2f} registros/segundo")

        except redis.RedisError as err:
            print("Error durante la inserción masiva a Redis:", err)
            return -1
        finally:
            cursor_activos.close()

        return 1

    def BorrarAllKeys(self):
        try:
            l = 0
            for key in self.Redis1.scan_iter('*'):
                if key.decode() != 'migrando':
                    self.Redis1.delete(key)
                    l += 1
            print("Borró", l, "Keys en Redis DB 4")
        except Exception as e:
            print("Error al borrar keys:", e)


if __name__ == "__main__":
    maneja_redis = ClassRedis()

    if maneja_redis.Redis1 == -1 or maneja_redis.ConnMaster == -1:
        print("Error al establecer conexiones a Base de Datos / Redis.")
    else:
        print("Conexiones verificadas correctamente.")
        # Opcional: Descomentar si se desea limpiar Redis DB 4 antes de la carga
        # maneja_redis.BorrarAllKeys()
        maneja_redis.cargarGeoRef_v1(batch_size=5000)
