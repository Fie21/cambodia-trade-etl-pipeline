-- Runs against the transport_dw database to initialize schemas, staging tables, and fact tables.
-- Four main pillars:
--   1. warehouse.fact_transportation_stats (Mode of transport: Sea, Air, Road, etc.)
--   2. warehouse.fact_country_trade        (Partner country trade: USA, China, Vietnam, etc.)
--   3. warehouse.fact_trade_by_sitc        (SITC sector trade: Apparel, Machinery, Cereals, etc.)
--   4. warehouse.fact_trade_by_hs          (HS product chapters: HS 61, HS 85, HS 10, etc.)

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS warehouse;

-- --- 1. TRANSPORT MODE TABLES ------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.raw_transportation_stats (
    date            DATE PRIMARY KEY,
    period          TEXT NOT NULL,
    raw_payload     JSONB NOT NULL,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS warehouse.fact_transportation_stats (
    date            DATE              NOT NULL,
    period          TEXT              NOT NULL,
    regime          TEXT              NOT NULL,
    description     TEXT              NOT NULL,
    description_kh  TEXT,
    net_weight_ton  DOUBLE PRECISION,
    net_weight_kg   DOUBLE PRECISION,
    value_usd       DOUBLE PRECISION,
    value_khr       BIGINT,
    loaded_at       TIMESTAMPTZ       NOT NULL DEFAULT now(),
    PRIMARY KEY (date, regime, description)
);

CREATE INDEX IF NOT EXISTS idx_fact_transport_date ON warehouse.fact_transportation_stats (date);
CREATE INDEX IF NOT EXISTS idx_fact_transport_period ON warehouse.fact_transportation_stats (period);
CREATE INDEX IF NOT EXISTS idx_fact_transport_regime ON warehouse.fact_transportation_stats (regime);
CREATE INDEX IF NOT EXISTS idx_fact_transport_desc ON warehouse.fact_transportation_stats (description);


-- --- 2. PARTNER COUNTRY TABLES -----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.raw_country_trade (
    date            DATE PRIMARY KEY,
    period          TEXT NOT NULL,
    raw_payload     JSONB NOT NULL,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS warehouse.fact_country_trade (
    date            DATE              NOT NULL,
    period          TEXT              NOT NULL,
    year            INTEGER           NOT NULL,
    month           INTEGER           NOT NULL,
    country_code    TEXT,
    country_code3   TEXT,
    country_name_en TEXT              NOT NULL,
    country_name_kh TEXT,
    country_groups  TEXT,
    trade_type      TEXT              NOT NULL,
    regime_code     TEXT              NOT NULL,
    value_usd       DOUBLE PRECISION  DEFAULT 0.0,
    value_khr       BIGINT            DEFAULT 0,
    loaded_at       TIMESTAMPTZ       NOT NULL DEFAULT now(),
    PRIMARY KEY (date, trade_type, country_name_en)
);

CREATE INDEX IF NOT EXISTS idx_fact_country_date ON warehouse.fact_country_trade (date);
CREATE INDEX IF NOT EXISTS idx_fact_country_period ON warehouse.fact_country_trade (period);
CREATE INDEX IF NOT EXISTS idx_fact_country_type ON warehouse.fact_country_trade (trade_type);
CREATE INDEX IF NOT EXISTS idx_fact_country_code ON warehouse.fact_country_trade (country_code);
CREATE INDEX IF NOT EXISTS idx_fact_country_name ON warehouse.fact_country_trade (country_name_en);


-- --- 3. SITC SECTOR TABLES ---------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.raw_sitc_trade (
    date            DATE PRIMARY KEY,
    period          TEXT NOT NULL,
    raw_payload     JSONB NOT NULL,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS warehouse.fact_trade_by_sitc (
    date            DATE              NOT NULL,
    period          TEXT              NOT NULL,
    year            INTEGER           NOT NULL,
    month           INTEGER           NOT NULL,
    sitc_code       TEXT              NOT NULL,
    description_en  TEXT              NOT NULL,
    description_kh  TEXT,
    trade_type      TEXT              NOT NULL,
    regime_code     TEXT              NOT NULL,
    value_usd       DOUBLE PRECISION  DEFAULT 0.0,
    value_khr       BIGINT            DEFAULT 0,
    loaded_at       TIMESTAMPTZ       NOT NULL DEFAULT now(),
    PRIMARY KEY (date, trade_type, sitc_code)
);

CREATE INDEX IF NOT EXISTS idx_fact_sitc_date ON warehouse.fact_trade_by_sitc (date);
CREATE INDEX IF NOT EXISTS idx_fact_sitc_period ON warehouse.fact_trade_by_sitc (period);
CREATE INDEX IF NOT EXISTS idx_fact_sitc_type ON warehouse.fact_trade_by_sitc (trade_type);
CREATE INDEX IF NOT EXISTS idx_fact_sitc_code ON warehouse.fact_trade_by_sitc (sitc_code);


-- --- 4. HS CHAPTER TABLES ----------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.raw_hs_trade (
    date            DATE PRIMARY KEY,
    period          TEXT NOT NULL,
    raw_payload     JSONB NOT NULL,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS warehouse.fact_trade_by_hs (
    date            DATE              NOT NULL,
    period          TEXT              NOT NULL,
    year            INTEGER           NOT NULL,
    month           INTEGER           NOT NULL,
    hs_chapter      TEXT              NOT NULL,
    description_en  TEXT              NOT NULL,
    description_kh  TEXT,
    trade_type      TEXT              NOT NULL,
    regime_code     TEXT              NOT NULL,
    value_usd       DOUBLE PRECISION  DEFAULT 0.0,
    value_khr       BIGINT            DEFAULT 0,
    loaded_at       TIMESTAMPTZ       NOT NULL DEFAULT now(),
    PRIMARY KEY (date, trade_type, hs_chapter)
);

CREATE INDEX IF NOT EXISTS idx_fact_hs_date ON warehouse.fact_trade_by_hs (date);
CREATE INDEX IF NOT EXISTS idx_fact_hs_period ON warehouse.fact_trade_by_hs (period);
CREATE INDEX IF NOT EXISTS idx_fact_hs_type ON warehouse.fact_trade_by_hs (trade_type);
CREATE INDEX IF NOT EXISTS idx_fact_hs_chapter ON warehouse.fact_trade_by_hs (hs_chapter);


-- --- ETL RUN LOG -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouse.etl_run_log (
    id                  SERIAL PRIMARY KEY,
    dataset             TEXT DEFAULT 'transport',
    dag_run_id          TEXT,
    data_interval_start DATE,
    data_interval_end   DATE,
    rows_loaded         INTEGER,
    status              TEXT,
    error_message       TEXT,
    logged_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- --- SCRAPE LOG (HTTP Attempt Tracking) --------------------------------------
CREATE TABLE IF NOT EXISTS warehouse.scrape_log (
    id              SERIAL PRIMARY KEY,
    stream          TEXT NOT NULL,           -- transport, country, sitc, hs
    period          TEXT NOT NULL,           -- YYYY-MM
    endpoint_url    TEXT,
    http_status     INTEGER,                -- 200, 403, 404, 500, 503, etc.
    status_label    TEXT,                   -- 200 OK, 403 Forbidden, etc.
    is_success      BOOLEAN NOT NULL DEFAULT TRUE,
    error_message   TEXT,
    response_bytes  INTEGER,
    duration_ms     INTEGER,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scrape_log_stream ON warehouse.scrape_log (stream);
CREATE INDEX IF NOT EXISTS idx_scrape_log_period ON warehouse.scrape_log (period);
CREATE INDEX IF NOT EXISTS idx_scrape_log_status ON warehouse.scrape_log (http_status);
CREATE INDEX IF NOT EXISTS idx_scrape_log_scraped ON warehouse.scrape_log (scraped_at);

