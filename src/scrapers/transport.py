"""
Transport Mode Scraper: Scrapes Cambodia GDCE Monthly Transportation Statistics.
Endpoint: https://stats.customs.gov.kh/api/tradeByMot/all
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

try:
    from config import GDCE_API_TOKEN, GDCE_MOT_API_URL, RAW_DIR, REGIME_MAP
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
    GDCE_MOT_API_URL = "https://stats.customs.gov.kh/api/tradeByMot/all"
    GDCE_API_TOKEN = "fHs4RbfpSE57qfYM"
    REGIME_MAP = {"IM": "Import", "EX,RX": "Export"}

from .common import DEFAULT_HEADERS, create_session

logger = logging.getLogger(__name__)


def fetch_gdce_mot(
    year: int,
    month: int,
    regime_code: str,
    session: Optional[requests.Session] = None,
) -> List[Dict[str, Any]]:
    """Fetch transport mode data for a single year/month and trade regime from GDCE."""
    s = session or create_session()
    headers = {**DEFAULT_HEADERS, "x-api-token": GDCE_API_TOKEN}
    params = {
        "pageNo": 1,
        "pageSize": 250,
        "startYear": year,
        "endYear": year,
        "startMonth": month,
        "endMonth": month,
        "reportType": "PUBLIC_MOT_DATA",
        "regimes": regime_code,
    }

    resp = s.get(GDCE_MOT_API_URL, params=params, headers=headers, timeout=30, verify=False)
    resp.raise_for_status()
    payload = resp.json()

    if not payload.get("success", False):
        logger.warning("GDCE MOT API unsuccessful for %d-%02d (%s): %s", year, month, regime_code, payload.get("message"))
        return []

    return payload.get("data", {}).get("contents", [])


def scrape_transport_month(data_interval_start: str, data_interval_end: Optional[str] = None, session: Optional[requests.Session] = None) -> str:
    """Scrapes GDCE transport mode data for the month defined by data_interval_start."""
    os.makedirs(RAW_DIR, exist_ok=True)
    dt_start = pd.Timestamp(data_interval_start)
    year, month = dt_start.year, dt_start.month
    period = f"{year}-{month:02d}"

    logger.info("Scraping GDCE Transport Mode data for period %s...", period)
    s = session or create_session()
    raw_payload: Dict[str, Any] = {
        "period": period,
        "data_interval_start": data_interval_start,
        "data_interval_end": data_interval_end or str(dt_start + pd.offsets.MonthBegin(1).date()),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "regimes": {},
    }

    total_records = 0
    for regime_code, regime_name in REGIME_MAP.items():
        contents = fetch_gdce_mot(year, month, regime_code, session=s)
        raw_payload["regimes"][regime_name] = {
            "regime_code": regime_code,
            "count": len(contents),
            "contents": contents,
        }
        total_records += len(contents)

    out_path = os.path.join(RAW_DIR, f"{period}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2, ensure_ascii=False)

    logger.info("Saved raw GDCE Transport snapshot %s (%d records) -> %s", period, total_records, out_path)
    return out_path
