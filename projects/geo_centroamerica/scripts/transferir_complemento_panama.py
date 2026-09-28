import psycopg2
from psycopg2.extras import execute_batch

print('Connecting to osm_panama (port 5434)...')
conn_src = psycopg2.connect('host=localhost port=5434 dbname=osm_panama user=postgres password=postgrespassword')
cur_src = conn_src.cursor()

print('Connecting to tobodb (port 5432)...')
conn_dst = psycopg2.connect('host=localhost port=5432 dbname=tobodb user=postgres password=bigBleu5')
cur_dst = conn_dst.cursor()

# 1. Ensure any previous 5004 test records for PAN are cleaned up
cur_dst.execute("DELETE FROM geo_total WHERE country_code = 'PAN' AND creation_user = 5004;")
del_count = cur_dst.rowcount
print(f"Cleaned up {del_count} previous 5004 PAN records if any.")

# 2. Fetch new clean 2,832 records from osm_panama
cur_src.execute('''
    SELECT id, name, location, display_name, country_code, client_id, color, icon, 
           creation_user, created_at, update_user, updated_at, bbox, h3_cell7, h3_cell5, 
           longitud, latitud
    FROM complemento_final_pa;
''')
rows = cur_src.fetchall()
print(f'Fetched {len(rows)} clean complement records from osm_panama.')

# 3. Insert into tobodb.geo_total
insert_sql = '''
    INSERT INTO geo_total (
        id, name, location, display_name, country_code, client_id, color, icon, 
        creation_user, created_at, update_user, updated_at, bbox, h3_cell7, h3_cell5, 
        longitud, latitud
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, 
        %s, %s, %s, %s, %s, %s, %s, 
        %s, %s
    );
'''
print('Inserting into tobodb.geo_total...')
execute_batch(cur_dst, insert_sql, rows, page_size=1000)
conn_dst.commit()
print('Insertion committed successfully!')

# 4. Strict verification in tobodb
cur_dst.execute("SELECT count(*) FROM geo_total WHERE country_code = 'PAN' AND creation_user = 5004;")
total_5004 = cur_dst.fetchone()[0]

cur_dst.execute('''
    SELECT count(*) 
    FROM geo_total c
    WHERE c.country_code = 'PAN' AND c.creation_user = 5004
      AND EXISTS (
          SELECT 1 
          FROM geo_total_pan_backup_pre_complemento b 
          WHERE b.h3_cell7 = c.h3_cell7
      );
''')
overlap = cur_dst.fetchone()[0]

print(f'Verification: Total new 5004 PAN records in geo_total: {total_5004}')
print(f'Verification: Overlap with existing historical client cells: {overlap}')
