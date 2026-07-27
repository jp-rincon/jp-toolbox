#!/usr/bin/env python3
"""
Script para generar archivos GeoJSON y KML de las celdas H3 (res 5 y 7)
registradas en la tabla public.geo_total para su visualización.

Uso:
    wsl python3 generate_h3_coverage.py --password bigBleu5
"""

import sys
import json
import argparse
import logging
import psycopg2

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

def get_h3_boundary(h3_cell: str) -> list:
    """Retorna los vértices del hexágono como una lista de (lon, lat)."""
    try:
        if hasattr(h3, 'cell_to_boundary'):
            coords = h3.cell_to_boundary(h3_cell)
        elif hasattr(h3, 'h3_to_geo_boundary'):
            coords = h3.h3_to_geo_boundary(h3_cell)
        else:
            raise RuntimeError("No se encontró la función cell_to_boundary en h3.")
        
        # H3 devuelve (lat, lon), necesitamos (lon, lat) para GeoJSON/KML
        # Además, cerramos el anillo del polígono repitiendo el primer vértice al final
        coords_lon_lat = [(lon, lat) for lat, lon in coords]
        if coords_lon_lat:
            coords_lon_lat.append(coords_lon_lat[0])
        return coords_lon_lat
    except Exception as e:
        logging.debug(f"Error calculando límite para {h3_cell}: {e}")
        return []

def generate_geojson(cells: list, resolution: int, output_file: str):
    """Genera un archivo GeoJSON con los polígonos de las celdas H3."""
    features = []
    for cell in cells:
        boundary = get_h3_boundary(cell)
        if not boundary:
            continue
            
        features.append({
            "type": "Feature",
            "properties": {
                "h3_cell": cell,
                "resolution": resolution
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [boundary]
            }
        })
        
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)
    logging.info(f"Archivo GeoJSON creado: {output_file} ({len(features)} hexágonos)")

def generate_kml(cells: list, resolution: int, output_file: str):
    """Genera un archivo KML con los polígonos de las celdas H3 para Google Earth/My Maps."""
    kml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        f'    <name>Cobertura H3 Res {resolution}</name>',
        '    <Style id="h3_poly_style">',
        '      <LineStyle>',
        '        <color>ff0000ff</color>', # Borde rojo opaco
        '        <width>2</width>',
        '      </LineStyle>',
        '      <PolyStyle>',
        '        <color>330000ff</color>', # Relleno rojo semi-transparente
        '      </PolyStyle>',
        '    </Style>'
    ]
    
    count = 0
    for cell in cells:
        boundary = get_h3_boundary(cell)
        if not boundary:
            continue
            
        # Formatear coordenadas como: lon,lat,0 lon,lat,0 ...
        coords_str = " ".join([f"{lon},{lat},0" for lon, lat in boundary])
        
        kml_parts.append('    <Placemark>')
        kml_parts.append(f'      <name>{cell}</name>')
        kml_parts.append('      <styleUrl>#h3_poly_style</styleUrl>')
        kml_parts.append('      <Polygon>')
        kml_parts.append('        <outerBoundaryIs>')
        kml_parts.append('          <LinearRing>')
        kml_parts.append(f'            <coordinates>{coords_str}</coordinates>')
        kml_parts.append('          </LinearRing>')
        kml_parts.append('        </outerBoundaryIs>')
        kml_parts.append('      </Polygon>')
        kml_parts.append('    </Placemark>')
        count += 1
        
    kml_parts.append('  </Document>')
    kml_parts.append('</kml>')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(kml_parts))
    logging.info(f"Archivo KML creado: {output_file} ({count} hexágonos)")

def main():
    parser = argparse.ArgumentParser(description="Generar archivos de cobertura KML/GeoJSON de celdas H3")
    parser.add_argument("--dbname", type=str, default=DEFAULT_DB_CONFIG["dbname"], help="Nombre de la BD PostgreSQL")
    parser.add_argument("--user", type=str, default=DEFAULT_DB_CONFIG["user"], help="Usuario PostgreSQL")
    parser.add_argument("--password", type=str, default=DEFAULT_DB_CONFIG["password"], help="Contraseña PostgreSQL")
    parser.add_argument("--host", type=str, default=DEFAULT_DB_CONFIG["host"], help="Host PostgreSQL")
    parser.add_argument("--port", type=int, default=DEFAULT_DB_CONFIG["port"], help="Puerto PostgreSQL")
    
    args = parser.parse_args()
    
    try:
        conn = psycopg2.connect(
            dbname=args.dbname,
            user=args.user,
            password=args.password,
            host=args.host,
            port=args.port
        )
        cur = conn.cursor()
    except Exception as e:
        logging.error(f"Error conectando a la base de datos: {e}")
        sys.exit(1)
        
    # 1. Procesar Resolución 5
    logging.info("Consultando celdas H3 Resolución 5 únicas...")
    cur.execute("SELECT DISTINCT h3_cell5 FROM public.geo_total WHERE h3_cell5 IS NOT NULL")
    cells_5 = [row[0] for row in cur.fetchall()]
    
    if cells_5:
        generate_geojson(cells_5, 5, "cobertura_h3_res5.geojson")
        generate_kml(cells_5, 5, "cobertura_h3_res5.kml")
    else:
        logging.warning("No se encontraron celdas H3 Resolución 5 en la tabla.")
        
    # 2. Procesar Resolución 7
    logging.info("Consultando celdas H3 Resolución 7 únicas...")
    cur.execute("SELECT DISTINCT h3_cell7 FROM public.geo_total WHERE h3_cell7 IS NOT NULL")
    cells_7 = [row[0] for row in cur.fetchall()]
    
    if cells_7:
        generate_geojson(cells_7, 7, "cobertura_h3_res7.geojson")
        generate_kml(cells_7, 7, "cobertura_h3_res7.kml")
    else:
        logging.warning("No se encontraron celdas H3 Resolución 7 en la tabla.")
        
    conn.close()
    logging.info("Proceso finalizado con éxito.")

if __name__ == "__main__":
    main()
