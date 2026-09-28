"""
SITC Industry Sector Scraper: Scrapes Cambodia GDCE Monthly Trade by SITC Division.
Endpoint: https://stats.customs.gov.kh/api/tradeBySitc/all
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

try:
    from config import DATA_DIR, GDCE_API_TOKEN, GDCE_BASE_URL
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    GDCE_BASE_URL = "https://stats.customs.gov.kh"
    GDCE_API_TOKEN = "fHs4RbfpSE57qfYM"

from .common import DEFAULT_HEADERS, create_session

RAW_SITC_DIR = os.path.join(DATA_DIR, "raw", "sitc")
logger = logging.getLogger(__name__)

TRADE_REGIMES = {
    "Import": "IM",
    "Export": "EX,RX",
    "Domestic Export": "EX",
    "Re-Export": "RX",
}


def fetch_sitc_month(year: int, month: int, regime_code: str, session: Optional[requests.Session] = None) -> List[Dict[str, Any]]:
    """Fetch trade by SITC division for a specific year, month, and regime."""
    s = session or create_session()
    headers = {**DEFAULT_HEADERS, "x-api-token": GDCE_API_TOKEN}
    params = {
        "pageNo": 1,
        "pageSize": 1000,
        "startYear": year,
        "endYear": year,
        "startMonth": month,
        "endMonth": month,
        "regimes": regime_code,
    }

    resp = s.get(f"{GDCE_BASE_URL}/api/tradeBySitc/all", headers=headers, params=params, verify=False, timeout=25)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success", False):
        logger.warning("GDCE SITC API unsuccessful for %d-%02d (%s): %s", year, month, regime_code, payload.get("message"))
        return []

    return payload.get("data", {}).get("contents", [])


def scrape_sitc_month(
    data_interval_start: str,
    data_interval_end: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> str:
    """Scrapes GDCE SITC trade data for a single month period."""
    os.makedirs(RAW_SITC_DIR, exist_ok=True)
    dt = pd.Timestamp(data_interval_start)
    year, month = dt.year, dt.month
    period = f"{year}-{month:02d}"

    logger.info("Scraping GDCE SITC Sector Data for period %s...", period)
    s = session or create_session()
    records: List[Dict[str, Any]] = []

    for type_name, regime_code in TRADE_REGIMES.items():
        contents = fetch_sitc_month(year, month, regime_code, session=s)
        for item in contents:
            val_usd = float(item.get("imTotalValueUsd") if regime_code == "IM" else item.get("exTotalValueUsd") or 0.0)
            val_khr = int(item.get("imTotalValueKhr") if regime_code == "IM" else item.get("exTotalValueKhr") or 0)
            records.append({
                "period": period,
                "year": year,
                "month": month,
                "sitc_code": item.get("code"),
                "description_en": (item.get("dscEn") or "").strip(),
                "description_kh": (item.get("dscKh") or "").strip(),
                "trade_type": type_name,
                "regime_code": regime_code,
                "value_usd": round(val_usd, 2),
                "value_khr": val_khr,
            })

    out_path = os.path.join(RAW_SITC_DIR, f"{period}.json")
    payload = {
        "period": period,
        "year": year,
        "month": month,
        "data_interval_start": data_interval_start,
        "data_interval_end": data_interval_end or str(dt + pd.offsets.MonthBegin(1).date()),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(records),
        "records": records,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    logger.info("Saved SITC trade snapshot %s (%d records) -> %s", period, len(records), out_path)
    return out_path
