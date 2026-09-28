import psycopg2

conn = psycopg2.connect('host=localhost port=5432 dbname=tobodb user=postgres password=bigBleu5')
cur = conn.cursor()

cur.execute("SELECT count(*), count(DISTINCT h3_cell7), count(DISTINCT h3_cell5) FROM geo_total WHERE country_code = 'PAN';")
row = cur.fetchone()
print('Total PAN records:', row[0])
print('Distinct H7:', row[1])
print('Distinct H5:', row[2])

cur.execute("SELECT id, name, display_name, latitud, longitud, h3_cell7, h3_cell5, creation_user, created_at FROM geo_total WHERE country_code = 'PAN' LIMIT 5;")
print('Sample records:')
for r in cur.fetchall():
    print(r)

# Check columns of geo_total
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'geo_total';")
print('Columns of geo_total:')
for col in cur.fetchall():
    print(f"  {col[0]}: {col[1]}")
