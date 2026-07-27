# Dockerfile para entorno de procesamiento OSM con PostGIS + H3
FROM postgres:16-bookworm

LABEL maintainer="GPS Platform Team"
LABEL description="PostgreSQL 16 con PostGIS, osm2pgsql y extensión Uber H3 para procesamiento geográfico"

# Instalar dependencias del sistema, osm2pgsql, herramientas de compilación y postgresql-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    git \
    cmake \
    make \
    gcc \
    g++ \
    osm2pgsql \
    postgis \
    postgresql-16-postgis-3 \
    postgresql-server-dev-16 \
    libtool \
    pgxnclient \
    && rm -rf /var/lib/apt/lists/*

# Instalar extensión Uber H3 PostgreSQL desde fuente (h3-pg)
RUN git clone --depth 1 https://github.com/zachasme/h3-pg.git /tmp/h3-pg \
    && cd /tmp/h3-pg \
    && make \
    && make install \
    && rm -rf /tmp/h3-pg

EXPOSE 5432
