"""
Load step: Bulk ingests raw JSON into staging schemas and upserts normalized
processed CSVs into PostgreSQL data warehouse fact tables:
  1. warehouse.fact_transportation_stats
  2. warehouse.fact_country_trade
  3. warehouse.fact_trade_by_sitc
  4. warehouse.fact_trade_by_hs

Maintains full idempotency and logs run statuses to warehouse.etl_run_log.
"""
import glob
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import create_engine, text

try:
    from config import DW_CONN_STR
except ImportError:
    DW_CONN_STR = os.environ.get(
        "DW_CONN_STR",
        "postgresql+psycopg2://airflow:airflow@localhost:5432/transport_dw",
    )

logger = logging.getLogger(__name__)

# --- SQL UPSERT DEFINITIONS --------------------------------------------------

STAGING_TRANSPORT_SQL = text(
    """
    INSERT INTO staging.raw_transportation_stats (date, period, raw_payload, scraped_at)
    VALUES (:date, :period, CAST(:raw_payload AS JSONB), now())
    ON CONFLICT (date) DO UPDATE SET
        raw_payload = EXCLUDED.raw_payload,
        period = EXCLUDED.period,
        scraped_at = now();
    """
)

FACT_TRANSPORT_SQL = text(
    """
    INSERT INTO warehouse.fact_transportation_stats
        (date, period, regime, description, description_kh, net_weight_ton, net_weight_kg, value_usd, value_khr, loaded_at)
    VALUES
        (:date, :period, :regime, :description, :description_kh, :net_weight_ton, :net_weight_kg, :value_usd, :value_khr, now())
    ON CONFLICT (date, regime, description) DO UPDATE SET
        description_kh = EXCLUDED.description_kh,
        net_weight_ton = EXCLUDED.net_weight_ton,
        net_weight_kg = EXCLUDED.net_weight_kg,
        value_usd = EXCLUDED.value_usd,
        value_khr = EXCLUDED.value_khr,
        loaded_at = now();
    """
)

STAGING_COUNTRY_SQL = text(
    """
    INSERT INTO staging.raw_country_trade (date, period, raw_payload, scraped_at)
    VALUES (:date, :period, CAST(:raw_payload AS JSONB), now())
    ON CONFLICT (date) DO UPDATE SET
        raw_payload = EXCLUDED.raw_payload,
        period = EXCLUDED.period,
        scraped_at = now();
    """
)

FACT_COUNTRY_SQL = text(
    """
    INSERT INTO warehouse.fact_country_trade
        (date, period, year, month, country_code, country_code3, country_name_en, country_name_kh,
         country_groups, trade_type, regime_code, value_usd, value_khr, loaded_at)
    VALUES
        (:date, :period, :year, :month, :country_code, :country_code3, :country_name_en, :country_name_kh,
         :country_groups, :trade_type, :regime_code, :value_usd, :value_khr, now())
    ON CONFLICT (date, trade_type, country_name_en) DO UPDATE SET
        country_code = EXCLUDED.country_code,
        country_code3 = EXCLUDED.country_code3,
        country_name_kh = EXCLUDED.country_name_kh,
        country_groups = EXCLUDED.country_groups,
        regime_code = EXCLUDED.regime_code,
        value_usd = EXCLUDED.value_usd,
        value_khr = EXCLUDED.value_khr,
        loaded_at = now();
    """
)

STAGING_SITC_SQL = text(
    """
    INSERT INTO staging.raw_sitc_trade (date, period, raw_payload, scraped_at)
    VALUES (:date, :period, CAST(:raw_payload AS JSONB), now())
    ON CONFLICT (date) DO UPDATE SET
        raw_payload = EXCLUDED.raw_payload,
        period = EXCLUDED.period,
        scraped_at = now();
    """
)

FACT_SITC_SQL = text(
    """
    INSERT INTO warehouse.fact_trade_by_sitc
        (date, period, year, month, sitc_code, description_en, description_kh, trade_type, regime_code, value_usd, value_khr, loaded_at)
    VALUES
        (:date, :period, :year, :month, :sitc_code, :description_en, :description_kh, :trade_type, :regime_code, :value_usd, :value_khr, now())
    ON CONFLICT (date, trade_type, sitc_code) DO UPDATE SET
        description_en = EXCLUDED.description_en,
        description_kh = EXCLUDED.description_kh,
        regime_code = EXCLUDED.regime_code,
        value_usd = EXCLUDED.value_usd,
        value_khr = EXCLUDED.value_khr,
        loaded_at = now();
    """
)

STAGING_HS_SQL = text(
    """
    INSERT INTO staging.raw_hs_trade (date, period, raw_payload, scraped_at)
    VALUES (:date, :period, CAST(:raw_payload AS JSONB), now())
    ON CONFLICT (date) DO UPDATE SET
        raw_payload = EXCLUDED.raw_payload,
        period = EXCLUDED.period,
        scraped_at = now();
    """
)

FACT_HS_SQL = text(
    """
    INSERT INTO warehouse.fact_trade_by_hs
        (date, period, year, month, hs_chapter, description_en, description_kh, trade_type, regime_code, value_usd, value_khr, loaded_at)
    VALUES
        (:date, :period, :year, :month, :hs_chapter, :description_en, :description_kh, :trade_type, :regime_code, :value_usd, :value_khr, now())
    ON CONFLICT (date, trade_type, hs_chapter) DO UPDATE SET
        description_en = EXCLUDED.description_en,
        description_kh = EXCLUDED.description_kh,
        regime_code = EXCLUDED.regime_code,
        value_usd = EXCLUDED.value_usd,
        value_khr = EXCLUDED.value_khr,
        loaded_at = now();
    """
)

LOG_SQL = text(
    """
    INSERT INTO warehouse.etl_run_log
        (dataset, dag_run_id, data_interval_start, data_interval_end, rows_loaded, status, error_message, logged_at)
    VALUES (:dataset, :dag_run_id, :start, :end, :rows, :status, :error_message, now());
    """
)

def get_db_engine(engine=None):
    if engine:
        return engine
    conn_str = DW_CONN_STR
    # Fallback to localhost if host is postgres and running outside docker
    if "postgres:5432" in conn_str and not os.path.exists("/opt/airflow"):
        conn_str = conn_str.replace("postgres:5432", "localhost:5432")
    return create_engine(conn_str)


def load_transport_month(
    processed_csv_path: str,
    raw_json_path: Optional[str] = None,
    dag_run_id: str = "manual",
    data_interval_start: str = "2024-01-01",
    data_interval_end: str = "2024-02-01",
    engine=None,
) -> int:
    """Loads a single month of transport mode statistics into the warehouse."""
    df = pd.read_csv(processed_csv_path) if os.path.exists(processed_csv_path) else pd.DataFrame()
    db_engine = get_db_engine(engine)

    if not raw_json_path:
        candidate_raw = processed_csv_path.replace("/processed/", "/raw/").replace(".csv", ".json")
        if os.path.exists(candidate_raw):
            raw_json_path = candidate_raw

    rows_loaded = 0
    with db_engine.begin() as conn:
        if raw_json_path and os.path.exists(raw_json_path):
            try:
                with open(raw_json_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                period = raw_data.get("period", os.path.splitext(os.path.basename(raw_json_path))[0])
                date_str = f"{period}-01" if "-" in period else f"{period}-01-01"
                conn.execute(STAGING_TRANSPORT_SQL, {
                    "date": date_str,
                    "period": period,
                    "raw_payload": json.dumps(raw_data, ensure_ascii=False),
                })
            except Exception as e:
                logger.warning("Could not stage raw transport snapshot: %s", e)

        if not df.empty:
            df_clean = df.where(pd.notnull(df), None)
            records = df_clean.to_dict(orient="records")
            conn.execute(FACT_TRANSPORT_SQL, records)
            rows_loaded = len(records)

        conn.execute(LOG_SQL, {
            "dataset": "transport",
            "dag_run_id": dag_run_id,
            "start": data_interval_start,
            "end": data_interval_end,
            "rows": rows_loaded,
            "status": "success",
            "error_message": None,
        })
    return rows_loaded


# For backward compatibility
load_month = load_transport_month


def load_country_month(processed_csv_path: str, raw_json_path: Optional[str] = None, engine=None) -> int:
    """Loads a single month of country trade data into warehouse.fact_country_trade."""
    df = pd.read_csv(processed_csv_path) if os.path.exists(processed_csv_path) else pd.DataFrame()
    db_engine = get_db_engine(engine)

    if not raw_json_path:
        candidate = processed_csv_path.replace("/processed/country/", "/raw/country/").replace(".csv", ".json")
        if os.path.exists(candidate):
            raw_json_path = candidate

    rows_loaded = 0
    with db_engine.begin() as conn:
        if raw_json_path and os.path.exists(raw_json_path):
            try:
                with open(raw_json_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                period = raw_data.get("period", os.path.splitext(os.path.basename(raw_json_path))[0])
                conn.execute(STAGING_COUNTRY_SQL, {
                    "date": f"{period}-01",
                    "period": period,
                    "raw_payload": json.dumps(raw_data, ensure_ascii=False),
                })
            except Exception as e:
                logger.warning("Could not stage country snapshot: %s", e)

        if not df.empty:
            df_clean = df.where(pd.notnull(df), None)
            records = df_clean.to_dict(orient="records")
            conn.execute(FACT_COUNTRY_SQL, records)
            rows_loaded = len(records)
    return rows_loaded


def load_sitc_month(processed_csv_path: str, raw_json_path: Optional[str] = None, engine=None) -> int:
    """Loads a single month of SITC trade data into warehouse.fact_trade_by_sitc."""
    df = pd.read_csv(processed_csv_path) if os.path.exists(processed_csv_path) else pd.DataFrame()
    db_engine = get_db_engine(engine)

    if not raw_json_path:
        candidate = processed_csv_path.replace("/processed/sitc/", "/raw/sitc/").replace(".csv", ".json")
        if os.path.exists(candidate):
            raw_json_path = candidate

    rows_loaded = 0
    with db_engine.begin() as conn:
        if raw_json_path and os.path.exists(raw_json_path):
            try:
                with open(raw_json_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                period = raw_data.get("period", os.path.splitext(os.path.basename(raw_json_path))[0])
                conn.execute(STAGING_SITC_SQL, {
                    "date": f"{period}-01",
                    "period": period,
                    "raw_payload": json.dumps(raw_data, ensure_ascii=False),
                })
            except Exception as e:
                logger.warning("Could not stage SITC snapshot: %s", e)

        if not df.empty:
            df_clean = df.where(pd.notnull(df), None)
            records = df_clean.to_dict(orient="records")
            conn.execute(FACT_SITC_SQL, records)
            rows_loaded = len(records)
    return rows_loaded


def load_hs_month(processed_csv_path: str, raw_json_path: Optional[str] = None, engine=None) -> int:
    """Loads a single month of HS-2 chapter trade data into warehouse.fact_trade_by_hs."""
    df = pd.read_csv(processed_csv_path) if os.path.exists(processed_csv_path) else pd.DataFrame()
    db_engine = get_db_engine(engine)

    if not raw_json_path:
        candidate = processed_csv_path.replace("/processed/hs2/", "/raw/hs2/").replace(".csv", ".json")
        if os.path.exists(candidate):
            raw_json_path = candidate

    rows_loaded = 0
    with db_engine.begin() as conn:
        if raw_json_path and os.path.exists(raw_json_path):
            try:
                with open(raw_json_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                period = raw_data.get("period", os.path.splitext(os.path.basename(raw_json_path))[0])
                conn.execute(STAGING_HS_SQL, {
                    "date": f"{period}-01",
                    "period": period,
                    "raw_payload": json.dumps(raw_data, ensure_ascii=False),
                })
            except Exception as e:
                logger.warning("Could not stage HS snapshot: %s", e)

        if not df.empty:
            df_clean = df.where(pd.notnull(df), None)
            records = df_clean.to_dict(orient="records")
            conn.execute(FACT_HS_SQL, records)
            rows_loaded = len(records)
    return rows_loaded


def load_all_datasets(data_dir: str = "data", engine=None) -> Dict[str, Tuple[int, int, List[str]]]:
    """
    Bulk loads all historical processed CSV files and raw JSON snapshots for all 4 datasets
    into the PostgreSQL data warehouse.
    """
    db_engine = get_db_engine(engine)
    results = {}

    datasets = [
        ("Transport Mode", "data/processed/*.csv", "data/raw/*.json", FACT_TRANSPORT_SQL, STAGING_TRANSPORT_SQL, "transport"),
        ("Partner Country", "data/processed/country/*.csv", "data/raw/country/*.json", FACT_COUNTRY_SQL, STAGING_COUNTRY_SQL, "country"),
        ("SITC Sectors", "data/processed/sitc/*.csv", "data/raw/sitc/*.json", FACT_SITC_SQL, STAGING_SITC_SQL, "sitc"),
        ("HS-2 Chapters", "data/processed/hs2/*.csv", "data/raw/hs2/*.json", FACT_HS_SQL, STAGING_HS_SQL, "hs"),
    ]

    for name, csv_glob, raw_glob, fact_sql, staging_sql, dataset_code in datasets:
        csv_files = sorted(glob.glob(os.path.join(data_dir, "..", csv_glob) if not os.path.exists(csv_glob.split("*")[0]) else csv_glob))
        if not csv_files:
            csv_files = sorted(glob.glob(os.path.join(os.getcwd(), csv_glob)))
            
        total_rows = 0
        file_count = 0
        errors = []

        logger.info("Loading %s (%d files)...", name, len(csv_files))
        start_t = time.time()

        for fpath in csv_files:
            try:
                df = pd.read_csv(fpath)
                if df.empty:
                    continue
                period = os.path.splitext(os.path.basename(fpath))[0]
                raw_path = fpath.replace("/processed/", "/raw/").replace(".csv", ".json")

                with db_engine.begin() as conn:
                    # 1. Staging
                    if os.path.exists(raw_path):
                        try:
                            with open(raw_path, "r", encoding="utf-8") as rf:
                                raw_json = json.load(rf)
                            conn.execute(staging_sql, {
                                "date": f"{period}-01",
                                "period": period,
                                "raw_payload": json.dumps(raw_json, ensure_ascii=False),
                            })
                        except Exception as se:
                            errors.append(f"Staging error {period} ({name}): {se}")

                    # 2. Fact Upsert
                    df_clean = df.where(pd.notnull(df), None)
                    records = df_clean.to_dict(orient="records")
                    conn.execute(fact_sql, records)
                    total_rows += len(records)
                    file_count += 1
            except Exception as e:
                errors.append(f"Fact load error {fpath}: {e}")

        # Log completion
        try:
            with db_engine.begin() as conn:
                conn.execute(LOG_SQL, {
                    "dataset": dataset_code,
                    "dag_run_id": "bulk_initial_load",
                    "start": "2016-01-01",
                    "end": "2026-08-01",
                    "rows": total_rows,
                    "status": "success" if not errors else "partial_error",
                    "error_message": "; ".join(errors[:5]) if errors else None,
                })
        except Exception as le:
            logger.warning("Could not log bulk load status: %s", le)

        duration = time.time() - start_t
        logger.info("Loaded %s: %d files, %d rows in %.2fs (errors: %d)", name, file_count, total_rows, duration, len(errors))
        results[name] = (file_count, total_rows, errors)

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Starting bulk load of all datasets into PostgreSQL warehouse...")
    res = load_all_datasets()
    print("\n=== BULK LOAD SUMMARY ===")
    for ds, (fc, rc, errs) in res.items():
        print(f"{ds:15} | Files: {fc:3d} | Rows: {rc:6,d} | Errors: {len(errs)}")
        if errs:
            for err in errs[:3]:
                print(f"  -> Error: {err}")
