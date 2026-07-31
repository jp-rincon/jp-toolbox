#!/usr/bin/env python3
"""
Script para generar archivos KML de cobertura H3 (Resolución 5 y Resolución 7)
seccionados por país o globales a partir de la tabla public.geo_total en tobodb.

Uso:
    # Generar KMLs divididos por país (Resolución 7)
    wsl python3 export_h3_kml.py --res 7 --split-countries --out-dir /mnt/k/kml_centroamerica/

    # Generar KML de un país específico (ej: Costa Rica 'CRI')
    wsl python3 export_h3_kml.py --res 7 --country CRI --out /mnt/k/kml_costa_rica_res7.kml
"""

import sys
import os
import argparse
import logging
import psycopg2

try:
    import h3
except ImportError:
    print("Error: La librería 'h3' no está instalada. Ejecuta: pip3 install h3")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEFAULT_DB_CONFIG = {
    "dbname": "tobodb",
    "user": "postgres",
    "password": "postgrespassword",
    "host": "127.0.0.1",
    "port": 5432
}

PAIS_NOMBRES = {
    "GTM": "Guatemala",
    "SLV": "El Salvador",
    "HND": "Honduras",
    "NIC": "Nicaragua",
    "CRI": "Costa Rica",
    "PAN": "Panamá",
    "BLZ": "Belice",
    "CUB": "Cuba",
    "DOM": "República Dominicana",
    "TTO": "Trinidad y Tobago",
    "JAM": "Jamaica",
    "HTI": "Haití",
    "BHS": "Bahamas",
    "CA": "Centroamérica y Caribe"
}

def get_h3_boundary(cell_id: str):
    """Obtiene los vértices del polígono H3 como lista de (lon, lat)."""
    try:
        if hasattr(h3, 'cell_to_boundary'):
            coords = h3.cell_to_boundary(cell_id)
        elif hasattr(h3, 'h3_to_geo_boundary'):
            coords = h3.h3_to_geo_boundary(cell_id)
        else:
            return None

        kml_coords = []
        for point in coords:
            lat, lon = point[0], point[1]
            kml_coords.append(f"{lon},{lat},0")
        
        if kml_coords:
            kml_coords.append(kml_coords[0])
            
        return " ".join(kml_coords)
    except Exception as e:
        logging.warning(f"No se pudo obtener el límite para la celda {cell_id}: {e}")
        return None

def generate_kml_for_query(res: int, country_code: str, output_file: str, db_config: dict):
    """Genera un archivo KML filtrado por país (o global si country_code es None)."""
    column_name = f"h3_cell{res}"
    
    try:
        conn = psycopg2.connect(**db_config)
    except Exception:
        db_config['password'] = 'bigBleu5'
        conn = psycopg2.connect(**db_config)
        
    cursor = conn.cursor()
    
    where_clause = f"WHERE {column_name} IS NOT NULL AND {column_name} <> ''"
    if country_code:
        where_clause += f" AND country_code = '{country_code}'"
        
    query = f"""
        SELECT 
            {column_name} AS cell_id,
            COUNT(*) AS total_pois,
            STRING_AGG(DISTINCT country_code, ', ') AS paises,
            MODE() WITHIN GROUP (ORDER BY name) AS muestra_nombre
        FROM geo_total
        {where_clause}
        GROUP BY 1
        ORDER BY 2 DESC;
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        logging.info(f"No se encontraron datos para {country_code or 'Global'} en H3-{res}.")
        cursor.close()
        conn.close()
        return

    pais_nombre = PAIS_NOMBRES.get(country_code, country_code) if country_code else "Global"
    logging.info(f"Generando KML para {pais_nombre} (H3-{res}): {len(rows)} celdas...")
    
    kml_header = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Cobertura H3 Res-{res} - {pais_nombre}</name>
    <description>Cobertura de Georreferencias H3 Resolucion {res} en {pais_nombre}</description>
    
    <Style id="h3_high_density">
      <LineStyle><color>ff00aa00</color><width>1.5</width></LineStyle>
      <PolyStyle><color>7700ff00</color></PolyStyle>
    </Style>

    <Style id="h3_mid_density">
      <LineStyle><color>ff00aaff</color><width>1.2</width></LineStyle>
      <PolyStyle><color>7700ffff</color></PolyStyle>
    </Style>

    <Style id="h3_low_density">
      <LineStyle><color>ff0055ff</color><width>1.0</width></LineStyle>
      <PolyStyle><color>6600aaff</color></PolyStyle>
    </Style>
"""
    
    kml_body = []
    max_count = max([r[1] for r in rows]) if rows else 1
    
    for row in rows:
        cell_id, count, paises, muestra = row[0], row[1], row[2], row[3]
        
        coordinates_str = get_h3_boundary(cell_id)
        if not coordinates_str:
            continue
            
        if count > (max_count * 0.2):
            style_id = "#h3_high_density"
        elif count > (max_count * 0.05):
            style_id = "#h3_mid_density"
        else:
            style_id = "#h3_low_density"
            
        name_esc = (muestra or cell_id).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        paises_esc = (paises or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        placemark = f"""
    <Placemark>
      <name>{cell_id} ({count} POIs)</name>
      <styleUrl>{style_id}</styleUrl>
      <ExtendedData>
        <Data name="Celda_H3"><value>{cell_id}</value></Data>
        <Data name="Total_Georreferencias"><value>{count}</value></Data>
        <Data name="Paises"><value>{paises_esc}</value></Data>
        <Data name="Ejemplo_Nombre"><value>{name_esc}</value></Data>
      </ExtendedData>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>{coordinates_str}</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>"""
        kml_body.append(placemark)
        
    kml_footer = """
  </Document>
</kml>"""
    
    full_kml = kml_header + "".join(kml_body) + kml_footer
    
    out_dir = os.path.dirname(output_file)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_kml)
        
    logging.info(f"KML generado exitosamente en: {output_file}")
    cursor.close()
    conn.close()

def process_all_countries(res: int, out_dir: str, db_config: dict):
    """Obtiene todos los country_code distintos de geo_total y genera un KML individual por país."""
    try:
        conn = psycopg2.connect(**db_config)
    except Exception:
        db_config['password'] = 'bigBleu5'
        conn = psycopg2.connect(**db_config)
        
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT country_code FROM geo_total WHERE country_code IS NOT NULL AND country_code <> '' ORDER BY 1;")
    countries = [r[0] for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    os.makedirs(out_dir, exist_ok=True)
    
    logging.info(f"Se encontraron {len(countries)} países/territorios en geo_total: {', '.join(countries)}")
    
    for code in countries:
        nombre = PAIS_NOMBRES.get(code, code).replace(" ", "_")
        filename = f"cobertura_{code}_{nombre}_res{res}.kml"
        output_path = os.path.join(out_dir, filename)
        generate_kml_for_query(res, code, output_path, db_config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generar KMLs de celdas H3 por país o globales")
    parser.add_argument("--res", type=int, choices=[5, 7], default=7, help="Resolución H3 (5 o 7)")
    parser.add_argument("--country", type=str, help="Código de país (ej: GTM, CRI, PAN, SLV, HND, NIC, BLZ)")
    parser.add_argument("--split-countries", action="store_true", help="Generar un KML individual por cada país en geo_total")
    parser.add_argument("--out", type=str, help="Ruta del archivo KML de salida (si se especifica un único país o global)")
    parser.add_argument("--out-dir", type=str, default="/mnt/k/kml_por_pais/", help="Directorio para guardar KMLs divididos por país")
    parser.add_argument("--host", type=str, default=DEFAULT_DB_CONFIG["host"])
    parser.add_argument("--port", type=int, default=DEFAULT_DB_CONFIG["port"])
    parser.add_argument("--dbname", type=str, default=DEFAULT_DB_CONFIG["dbname"])
    parser.add_argument("--user", type=str, default=DEFAULT_DB_CONFIG["user"])
    parser.add_argument("--password", type=str, default=DEFAULT_DB_CONFIG["password"])
    
    args = parser.parse_args()
    
    config = {
        "dbname": args.dbname,
        "user": args.user,
        "password": args.password,
        "host": args.host,
        "port": args.port
    }
    
    if args.split_countries:
        process_all_countries(args.res, args.out_dir, config)
    else:
        out_file = args.out or f"/mnt/k/h3_cobertura_{args.country or 'global'}_res{args.res}.kml"
        generate_kml_for_query(args.res, args.country, out_file, config)
