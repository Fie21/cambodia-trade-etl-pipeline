"""
Partner Country Scraper: Scrapes Cambodia GDCE Monthly Country Trade Statistics.
Endpoint: https://stats.customs.gov.kh/api/tradeByCountry/all
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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

RAW_COUNTRY_DIR = os.path.join(DATA_DIR, "raw", "country")
logger = logging.getLogger(__name__)

TRADE_REGIMES = {
    "Import": "IM",
    "Export": "EX,RX",
    "Domestic Export": "EX",
    "Re-Export": "RX",
}


def fetch_country_metadata(session: Optional[requests.Session] = None) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, Any]]]:
    """Fetches country master definitions, country groups, and group association mappings."""
    s = session or create_session()
    headers = {**DEFAULT_HEADERS, "x-api-token": GDCE_API_TOKEN}

    # 1. Groups
    groups_resp = s.get(f"{GDCE_BASE_URL}/api/countryGroup/getData", headers=headers, verify=False, timeout=15)
    groups_data = groups_resp.json().get("data", []) if groups_resp.status_code == 200 else []
    groups_map = {g["code"]: {"code": g["code"], "name": g["name"], "nameKh": g.get("nameKh")} for g in groups_data}

    # 2. Country to Group Mappings
    cg_resp = s.get(f"{GDCE_BASE_URL}/api/countryGroupCountry/getData", headers=headers, params={"pageNo": 1, "pageSize": 1000}, verify=False, timeout=15)
    cg_data = cg_resp.json().get("data", []) if cg_resp.status_code == 200 else []
    country_to_groups: Dict[str, List[Dict[str, Any]]] = {}
    for m in cg_data:
        c_code = m["countryCode"]
        g_code = m["countryGroupCode"]
        g_obj = groups_map.get(g_code, {"code": g_code, "name": g_code, "nameKh": None})
        country_to_groups.setdefault(c_code, []).append(g_obj)

    # 3. Country definitions
    c_resp = s.get(f"{GDCE_BASE_URL}/api/country/all", headers=headers, params={"pageNo": 1, "pageSize": 1000}, verify=False, timeout=15)
    c_contents = c_resp.json().get("data", {}).get("contents", []) if c_resp.status_code == 200 else []
    name_to_country: Dict[str, Dict[str, Any]] = {}
    for c in c_contents:
        if c.get("name"):
            name_to_country[c["name"].strip().lower()] = c
        if c.get("nameKh"):
            name_to_country[c["nameKh"].strip()] = c

    return groups_map, country_to_groups, name_to_country


def fetch_country_trade_month(year: int, month: int, regime_code: str, session: Optional[requests.Session] = None) -> List[Dict[str, Any]]:
    """Fetch raw trade by country records for a specific year, month, and regime."""
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

    resp = s.get(f"{GDCE_BASE_URL}/api/tradeByCountry/all", headers=headers, params=params, verify=False, timeout=25)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success", False):
        logger.warning("GDCE Country API unsuccessful for %d-%02d (%s): %s", year, month, regime_code, payload.get("message"))
        return []

    return payload.get("data", {}).get("contents", [])


def scrape_country_month(
    data_interval_start: str,
    data_interval_end: Optional[str] = None,
    session: Optional[requests.Session] = None,
    metadata: Optional[Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, Any]]]] = None,
) -> str:
    """Scrapes and enriches GDCE partner country trade data for a single month period."""
    os.makedirs(RAW_COUNTRY_DIR, exist_ok=True)
    dt = pd.Timestamp(data_interval_start)
    year, month = dt.year, dt.month
    period = f"{year}-{month:02d}"

    logger.info("Scraping GDCE Country Trade Data for period %s...", period)
    s = session or create_session()

    if metadata is None:
        _, country_to_groups, name_to_country = fetch_country_metadata(session=s)
    else:
        _, country_to_groups, name_to_country = metadata

    records: List[Dict[str, Any]] = []

    for type_name, regime_code in TRADE_REGIMES.items():
        contents = fetch_country_trade_month(year, month, regime_code, session=s)
        for item in contents:
            dsc_en = (item.get("dscEn") or "").strip()
            dsc_kh = (item.get("dscKh") or "").strip()
            c_meta = name_to_country.get(dsc_en.lower()) or name_to_country.get(dsc_kh) or {}

            c_code = c_meta.get("code")
            c_code3 = c_meta.get("code3")
            c_groups = country_to_groups.get(c_code, []) if c_code else []

            if regime_code == "IM":
                val_usd = float(item.get("imTotalValueUsd") or 0.0)
                val_khr = int(item.get("imTotalValueKhr") or 0)
            else:
                val_usd = float(item.get("exTotalValueUsd") or 0.0)
                val_khr = int(item.get("exTotalValueKhr") or 0)

            records.append({
                "period": period,
                "year": year,
                "month": month,
                "country_code": c_code,
                "country_code3": c_code3,
                "country_name_en": dsc_en,
                "country_name_kh": dsc_kh,
                "country_groups": c_groups,
                "trade_type": type_name,
                "regime_code": regime_code,
                "value_usd": round(val_usd, 2),
                "value_khr": val_khr,
            })

    out_path = os.path.join(RAW_COUNTRY_DIR, f"{period}.json")
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

    logger.info("Saved country trade snapshot %s (%d records) -> %s", period, len(records), out_path)
    return out_path
