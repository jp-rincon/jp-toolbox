FROM citusdata/citus:12.1

# Instalar PostGIS y dependencias geoespaciales para PostgreSQL 16
RUN apt-get update && \
    apt-get install -y postgresql-16-postgis-3 && \
    rm -rf /var/lib/apt/lists/*
