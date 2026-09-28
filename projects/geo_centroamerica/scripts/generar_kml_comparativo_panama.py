#!/usr/bin/env python3
"""
generar_kml_comparativo_panama.py
Genera un KML interactivo para presentación en Google Earth Pro con dos capas:
1. Capa Azul/Ámbar: Celdas Existentes Previas (605 celdas)
2. Capa Verde/Esmeralda: Celdas Nuevas Complementarias (2,832 celdas)
"""

import psycopg2
import h3
import os
import xml.sax.saxutils as saxutils

conn = psycopg2.connect("host=localhost port=5432 dbname=tobodb user=postgres password=bigBleu5")
cur = conn.cursor()

def get_h3_coords(cell_id):
    try:
        coords = h3.cell_to_boundary(cell_id) if hasattr(h3, 'cell_to_boundary') else h3.h3_to_geo_boundary(cell_id)
        pts = [f"{pt[1]},{pt[0]},0" for pt in coords]
        if pts:
            pts.append(pts[0])
            return " ".join(pts)
    except Exception:
        pass
    return None

# 1. Celdas existentes (605)
cur.execute("""
    SELECT h3_cell7, count(*), MODE() WITHIN GROUP (ORDER BY name)
    FROM geo_total_pan_backup_pre_complemento
    WHERE h3_cell7 IS NOT NULL
    GROUP BY h3_cell7
    ORDER BY 2 DESC;
""")
existentes = cur.fetchall()

# 2. Celdas nuevas complementarias (2832)
cur.execute("""
    SELECT h3_cell7, count(*), MODE() WITHIN GROUP (ORDER BY name)
    FROM geo_total
    WHERE country_code = 'PAN' AND creation_user = 5004
    GROUP BY h3_cell7
    ORDER BY 2 DESC;
""")
nuevas = cur.fetchall()

kml = ["""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Panamá: Comparativa de Cobertura H3 (Antes vs Después)</name>
    <description>Presentación de Densificación de Georreferencias H3-7 en Panamá</description>
    
    <!-- Estilo Capa Existente: Naranja / Ámbar -->
    <Style id="estilo_existente">
      <LineStyle><color>ff00aaff</color><width>2.0</width></LineStyle>
      <PolyStyle><color>5500aaff</color></PolyStyle>
    </Style>

    <!-- Estilo Capa Nueva: Verde Esmeralda -->
    <Style id="estilo_nueva">
      <LineStyle><color>ff00ff55</color><width>2.0</width></LineStyle>
      <PolyStyle><color>6600ff55</color></PolyStyle>
    </Style>
"""]

# Carpeta 1: Existentes
kml.append(f"""    <Folder>
      <name>1. Celdas Existentes Previas ({len(existentes)} celdas)</name>
      <open>1</open>
      <description>Cobertura histórica aprobada por clientes (concentrada en zonas urbanas)</description>
""")
for cell, count, sample_name in existentes:
    coords = get_h3_coords(cell)
    if not coords:
        continue
    esc_name = saxutils.escape(sample_name or cell)
    kml.append(f"""      <Placemark>
        <name>{cell} ({count} refs)</name>
        <styleUrl>#estilo_existente</styleUrl>
        <ExtendedData>
          <Data name="Tipo"><value>Existente Previa</value></Data>
          <Data name="H3_Cell7"><value>{cell}</value></Data>
          <Data name="Total_POIs"><value>{count}</value></Data>
          <Data name="Referencia"><value>{esc_name}</value></Data>
        </ExtendedData>
        <Polygon>
          <outerBoundaryIs><LinearRing><coordinates>{coords}</coordinates></LinearRing></outerBoundaryIs>
        </Polygon>
      </Placemark>""")
kml.append("    </Folder>\n")

# Carpeta 2: Nuevas Complementarias
kml.append(f"""    <Folder>
      <name>2. Celdas Nuevas Complementarias ({len(nuevas)} celdas)</name>
      <open>1</open>
      <description>Celdas densificadas (zonas no metropolitanas, carreteras, poblados y peajes)</description>
""")
for cell, count, sample_name in nuevas:
    coords = get_h3_coords(cell)
    if not coords:
        continue
    esc_name = saxutils.escape(sample_name or cell)
    kml.append(f"""      <Placemark>
        <name>{cell}</name>
        <styleUrl>#estilo_nueva</styleUrl>
        <ExtendedData>
          <Data name="Tipo"><value>Nueva Complementaria (Usuario 5004)</value></Data>
          <Data name="H3_Cell7"><value>{cell}</value></Data>
          <Data name="Referencia"><value>{esc_name}</value></Data>
        </ExtendedData>
        <Polygon>
          <outerBoundaryIs><LinearRing><coordinates>{coords}</coordinates></LinearRing></outerBoundaryIs>
        </Polygon>
      </Placemark>""")
kml.append("    </Folder>\n")

kml.append("""  </Document>
</kml>""")

output_path = r"K:\kml_por_pais\panama_comparativa_antes_y_despues_h7.kml"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("".join(kml))

print(f"KML comparativo generado exitosamente en: {output_path}")
cur.close()
conn.close()
