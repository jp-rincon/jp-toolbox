import psycopg2

conn = psycopg2.connect('host=localhost port=5432 dbname=tobodb user=postgres password=bigBleu5')
cur = conn.cursor()

cols = ['id', 'name', 'location', 'display_name', 'country_code', 'client_id', 'color', 'icon', 'creation_user', 'created_at', 'update_user', 'updated_at', 'bbox', 'h3_cell7', 'h3_cell5', 'longitud', 'latitud']
cols_str = ', '.join(cols)

output_path = r'K:\geo_col_complemento_2026.sql'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('-- Dump de registros complementarios Colombia (creation_user = 5004)\n')
    f.write(f'COPY geo_col ({cols_str}) FROM stdin;\n')
    copy_sql = f"COPY (SELECT {cols_str} FROM geo_col WHERE creation_user = 5004) TO STDOUT WITH (FORMAT text, NULL '\\N')"
    cur.copy_expert(copy_sql, f)
    f.write('\\.\n')

print(f"Dump saved successfully to {output_path}")
