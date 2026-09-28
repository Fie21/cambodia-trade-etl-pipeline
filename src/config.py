"""
Shared configuration for the Cambodia GDCE Transportation ETL pipeline.

Data source: General Department of Customs and Excise of Cambodia (GDCE / GDDE)
Website: https://stats.customs.gov.kh/en/data-search/by-transport-mode
API Endpoint: https://stats.customs.gov.kh/api/tradeByMot/all
"""
import os

# --- GDCE Data Source --------------------------------------------------------
GDCE_BASE_URL = os.environ.get(
    "GDCE_BASE_URL", "https://stats.customs.gov.kh"
)
GDCE_MOT_API_URL = f"{GDCE_BASE_URL}/api/tradeByMot/all"
GDCE_API_TOKEN = os.environ.get("GDCE_API_TOKEN", "fHs4RbfpSE57qfYM")

# Earliest available historical data for transport modes in GDCE
BACKFILL_START = "2016-01-01"

# Trade regimes to extract
# 'IM' = Import, 'EX,RX' = Total Export (Domestic Export + Re-export)
REGIME_MAP = {
    "IM": "Import",
    "EX,RX": "Export",
}

# Standard transport mode descriptions
TRANSPORT_MODES = [
    "Air transport",
    "Inland waterways transport",
    "Postal Transport",
    "Rail transport",
    "Road transport",
    "Sea transport",
    "Transport on fixed installation",
]

# --- Storage paths (inside containers or local workspace) -------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_DIR = "/opt/airflow/data" if os.path.exists("/opt/airflow") else os.path.join(BASE_DIR, "data")
DATA_DIR = os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)
RAW_DIR = f"{DATA_DIR}/raw"
PROCESSED_DIR = f"{DATA_DIR}/processed"

# --- Database ----------------------------------------------------------------
DW_CONN_STR = os.environ.get(
    "DW_CONN_STR",
    "postgresql+psycopg2://airflow:airflow@postgres:5432/transport_dw",
)

