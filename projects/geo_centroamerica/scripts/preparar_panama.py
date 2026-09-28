import psycopg2

conn = psycopg2.connect('host=localhost port=5432 dbname=tobodb user=postgres password=bigBleu5')
cur = conn.cursor()

print('Creating backup table in tobodb...')
cur.execute('DROP TABLE IF EXISTS geo_total_pan_backup_pre_complemento;')
cur.execute("""
    CREATE TABLE geo_total_pan_backup_pre_complemento AS 
    SELECT * FROM geo_total WHERE country_code = 'PAN';
""")
conn.commit()

cur.execute('SELECT count(*), count(DISTINCT h3_cell7) FROM geo_total_pan_backup_pre_complemento;')
cnt, h7_cnt = cur.fetchone()
print(f'Backup created successfully: {cnt} records, {h7_cnt} distinct H7 cells.')

# Export existing H7 cells to CSV for exclusion
csv_path = r'K:\docker_volumes\data\celdas_existentes_pa.csv'
with open(csv_path, 'w', encoding='utf-8') as f:
    f.write('h3_cell7\n')
    cur.execute("""
        SELECT DISTINCT h3_cell7 
        FROM geo_total 
        WHERE country_code = 'PAN' AND h3_cell7 IS NOT NULL;
    """)
    rows = cur.fetchall()
    for row in rows:
        f.write(f'{row[0]}\n')

print(f'Exported {len(rows)} existing H7 cells to {csv_path}')
