import psycopg2

conn = psycopg2.connect('host=localhost port=5434 dbname=osm_panama user=postgres password=postgrespassword')
cur = conn.cursor()
for ext in ['postgis', 'hstore', 'unaccent', 'uuid-ossp', 'h3']:
    cur.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}";')
conn.commit()
print('Extensions postgis, hstore, unaccent, uuid-ossp, h3 enabled successfully in osm_panama!')
