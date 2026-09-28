#!/bin/bash
# Creates the transport_dw database (alongside the default "airflow" metadata
# database) the first time the postgres container's data volume is initialized.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE transport_dw;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "transport_dw" \
    -f /sql/init_warehouse.sql

