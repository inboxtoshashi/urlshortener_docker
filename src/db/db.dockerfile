FROM mysql:8.0

# Remove hardcoded credentials - use docker-compose env vars instead
COPY init.sql /docker-entrypoint-initdb.d/

# Healthcheck
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
    CMD mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} || exit 1


