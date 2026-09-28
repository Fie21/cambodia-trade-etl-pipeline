"""
Transform step: Convert raw Cambodia GDCE JSON payloads into tidy, normalized CSVs
ready for database ingestion:
  1. Transport Mode (data/processed/<period>.csv)
  2. Partner Country (data/processed/country/<period>.csv)
  3. SITC Sectors (data/processed/sitc/<period>.csv)
  4. HS-2 Chapters (data/processed/hs2/<period>.csv)
"""
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import pandas as pd

try:
    from config import PROCESSED_DIR, DATA_DIR
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

PROCESSED_COUNTRY_DIR = os.path.join(DATA_DIR, "processed", "country")
PROCESSED_SITC_DIR = os.path.join(DATA_DIR, "processed", "sitc")
PROCESSED_HS_DIR = os.path.join(DATA_DIR, "processed", "hs2")

logger = logging.getLogger(__name__)


def clean_float(val: Any) -> float:
    """Safely converts numeric or string values into float."""
    if val is None or pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    try:
        cleaned = str(val).replace(",", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def clean_int(val: Any) -> int:
    """Safely converts numeric or string values into int."""
    if val is None or pd.isna(val):
        return 0
    if isinstance(val, int):
        return val
    try:
        cleaned = str(val).replace(",", "").strip()
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


# --- 1. TRANSPORT MODE TRANSFORM ---------------------------------------------

def transform_transport_month(raw_json_path: str) -> str:
    """Transforms raw GDCE Transport JSON snapshot into a normalized CSV."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    filename = os.path.basename(raw_json_path)
    base_name = os.path.splitext(filename)[0]
    out_path = os.path.join(PROCESSED_DIR, f"{base_name}.csv")

    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    period = raw_data.get("period", base_name)
    date_str = f"{period}-01" if "-" in period else f"{period}-01-01"

    records: List[Dict[str, Any]] = []
    regimes_data = raw_data.get("regimes", {})

    for regime_name, regime_info in regimes_data.items():
        contents = regime_info.get("contents", [])
        is_import = regime_name.lower().startswith("import")

        for item in contents:
            desc_en = (item.get("dscEn") or "").strip()
            desc_kh = (item.get("dscKh") or "").strip()

            if not desc_en:
                continue

            if is_import:
                weight_kg = clean_float(item.get("imNetWeight"))
                val_usd = clean_float(item.get("imTotalValueUsd"))
                val_khr = clean_int(item.get("imTotalValueKhr"))
            else:
                weight_kg = clean_float(item.get("exNetWeight"))
                val_usd = clean_float(item.get("exTotalValueUsd"))
                val_khr = clean_int(item.get("exTotalValueKhr"))

            weight_ton = round(weight_kg / 1000.0, 4) if weight_kg else 0.0

            records.append({
                "date": date_str,
                "period": period,
                "regime": regime_name,
                "description": desc_en,
                "description_kh": desc_kh,
                "net_weight_ton": weight_ton,
                "net_weight_kg": round(weight_kg, 2),
                "value_usd": round(val_usd, 2),
                "value_khr": val_khr,
            })

    columns = [
        "date", "period", "regime", "description", "description_kh",
        "net_weight_ton", "net_weight_kg", "value_usd", "value_khr"
    ]

    df = pd.DataFrame(records, columns=columns) if records else pd.DataFrame(columns=columns)
    if not df.empty:
        df = df.drop_duplicates(subset=["date", "regime", "description"], keep="last")

    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("Transformed %d transport records for %s -> %s", len(df), period, out_path)
    return out_path


# For backward compatibility
transform_month = transform_transport_month


# --- 2. PARTNER COUNTRY TRANSFORM --------------------------------------------

def transform_country_month(raw_json_path: str) -> str:
    """Transforms raw Country JSON into normalized processed CSV."""
    os.makedirs(PROCESSED_COUNTRY_DIR, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(raw_json_path))[0]
    out_path = os.path.join(PROCESSED_COUNTRY_DIR, f"{base_name}.csv")

    with open(raw_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    period = data.get("period", base_name)
    records = []
    for r in data.get("records", []):
        groups_str = "; ".join([g["name"] for g in r.get("country_groups", []) if isinstance(g, dict) and "name" in g])
        records.append({
            "date": f"{period}-01",
            "period": period,
            "year": r.get("year"),
            "month": r.get("month"),
            "country_code": r.get("country_code"),
            "country_code3": r.get("country_code3"),
            "country_name_en": r.get("country_name_en"),
            "country_name_kh": r.get("country_name_kh"),
            "country_groups": groups_str,
            "trade_type": r.get("trade_type"),
            "regime_code": r.get("regime_code"),
            "value_usd": clean_float(r.get("value_usd")),
            "value_khr": clean_int(r.get("value_khr")),
        })

    df = pd.DataFrame(records)
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("Transformed %d country trade records for %s -> %s", len(df), period, out_path)
    return out_path


# --- 3. SITC SECTOR TRANSFORM ------------------------------------------------

def transform_sitc_month(raw_json_path: str) -> str:
    """Transforms raw SITC JSON into normalized processed CSV."""
    os.makedirs(PROCESSED_SITC_DIR, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(raw_json_path))[0]
    out_path = os.path.join(PROCESSED_SITC_DIR, f"{base_name}.csv")

    with open(raw_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    period = data.get("period", base_name)
    records = []
    for r in data.get("records", []):
        records.append({
            "date": f"{period}-01",
            "period": period,
            "year": r.get("year"),
            "month": r.get("month"),
            "sitc_code": r.get("sitc_code"),
            "description_en": r.get("description_en"),
            "description_kh": r.get("description_kh"),
            "trade_type": r.get("trade_type"),
            "regime_code": r.get("regime_code"),
            "value_usd": clean_float(r.get("value_usd")),
            "value_khr": clean_int(r.get("value_khr")),
        })

    df = pd.DataFrame(records)
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("Transformed %d SITC records for %s -> %s", len(df), period, out_path)
    return out_path


# --- 4. HS CHAPTER TRANSFORM -------------------------------------------------

def transform_hs_month(raw_json_path: str) -> str:
    """Transforms raw HS-2 chapter JSON into normalized processed CSV."""
    os.makedirs(PROCESSED_HS_DIR, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(raw_json_path))[0]
    out_path = os.path.join(PROCESSED_HS_DIR, f"{base_name}.csv")

    with open(raw_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    period = data.get("period", base_name)
    records = []
    for r in data.get("records", []):
        records.append({
            "date": f"{period}-01",
            "period": period,
            "year": r.get("year"),
            "month": r.get("month"),
            "hs_chapter": r.get("hs_chapter"),
            "description_en": r.get("description_en"),
            "description_kh": r.get("description_kh"),
            "trade_type": r.get("trade_type"),
            "regime_code": r.get("regime_code"),
            "value_usd": clean_float(r.get("value_usd")),
            "value_khr": clean_int(r.get("value_khr")),
        })

    df = pd.DataFrame(records)
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("Transformed %d HS chapter records for %s -> %s", len(df), period, out_path)
    return out_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_path = sys.argv[1] if len(sys.argv) >= 2 else os.path.join(DATA_DIR, "raw", "2024-01.json")
    transform_month(sample_path)
