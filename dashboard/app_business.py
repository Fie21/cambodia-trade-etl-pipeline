"""
Streamlit Business Analytics BI Dashboard for Cambodia GDCE Trade & Transport.
Audience: Economists, Port Operators (PAS/PPAP), Policy Makers, Supply Chain Planners.
Runs on Port 8501 (http://localhost:8501)
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

import importlib.util

# Ensure project root and src/ are in sys.path regardless of execution working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _p in [str(PROJECT_ROOT), str(PROJECT_ROOT / "src"), str(Path.cwd()), str(Path.cwd() / "src")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

forecast_monthly_series = None
evaluate_model_tournament = None
_forecast_import_err = None

# Method 1: Standard package import
try:
    from src.forecast import forecast_monthly_series as _fms, evaluate_model_tournament as _emt
    forecast_monthly_series = _fms
    evaluate_model_tournament = _emt
except Exception as _e1:
    try:
        from forecast import forecast_monthly_series as _fms, evaluate_model_tournament as _emt
        forecast_monthly_series = _fms
        evaluate_model_tournament = _emt
    except Exception as _e2:
        _forecast_import_err = f"{_e1} | {_e2}"

# Method 2: Direct file path loading via importlib (100% immune to cwd / sys.path discrepancies)
if forecast_monthly_series is None or evaluate_model_tournament is None:
    candidate_paths = [
        Path(__file__).resolve().parent / "forecast.py",
        PROJECT_ROOT / "src" / "forecast.py",
        Path(__file__).resolve().parent.parent / "src" / "forecast.py",
        Path.cwd() / "src" / "forecast.py",
        Path.cwd() / "forecast.py",
        Path.cwd().parent / "src" / "forecast.py",
        Path("/app/src/forecast.py"),
        Path("/app/forecast.py"),
        Path("/Users/soupichchomrong/transport-etl-pipeline/src/forecast.py"),
    ]
    for _path in candidate_paths:
        if _path.is_file():
            try:
                _spec = importlib.util.spec_from_file_location("dynamic_forecast_module", str(_path))
                if _spec and _spec.loader:
                    _mod = importlib.util.module_from_spec(_spec)
                    _spec.loader.exec_module(_mod)
                    if forecast_monthly_series is None:
                        forecast_monthly_series = getattr(_mod, "forecast_monthly_series", None)
                    if evaluate_model_tournament is None:
                        evaluate_model_tournament = getattr(_mod, "evaluate_model_tournament", None)
                    if forecast_monthly_series is not None:
                        _forecast_import_err = None
                        break
            except Exception as _load_err:
                _forecast_import_err = f"Error loading {_path}: {_load_err}"

# Support Streamlit Cloud Secrets, environment variables, or local Docker defaults
DW_CONN_STR = os.environ.get(
    "DW_CONN_STR",
    "postgresql+psycopg2://airflow:airflow@postgres:5432/transport_dw",
)
try:
    if hasattr(st, "secrets") and "DW_CONN_STR" in st.secrets:
        DW_CONN_STR = st.secrets["DW_CONN_STR"]
except Exception:
    pass

DATA_DIR = Path(__file__).resolve().parent / "data"

st.set_page_config(
    page_title="Cambodia GDCE International Trade Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_engine():
    try:
        engine = create_engine(DW_CONN_STR, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            pass
        return engine
    except Exception:
        try:
            localhost_str = DW_CONN_STR.replace("@postgres:", "@localhost:")
            engine = create_engine(localhost_str, connect_args={"connect_timeout": 3})
            with engine.connect() as conn:
                pass
            return engine
        except Exception:
            return None


@st.cache_data(ttl=300)
def load_transport_data() -> pd.DataFrame:
    engine = get_engine()
    if engine is not None:
        try:
            query = """
                SELECT
                    date, period, regime, description, description_kh,
                    net_weight_ton, net_weight_kg, value_usd, value_khr, loaded_at
                FROM warehouse.fact_transportation_stats
                ORDER BY date ASC, regime ASC, description ASC
            """
            return pd.read_sql(query, engine, parse_dates=["date"])
        except Exception:
            pass
    # Offline Parquet Fallback (for zero-config Streamlit Cloud deployment)
    p_path = DATA_DIR / "fact_transportation_stats.parquet"
    if p_path.is_file():
        df = pd.read_parquet(p_path)
        df["date"] = pd.to_datetime(df["date"])
        return df
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_country_data() -> pd.DataFrame:
    engine = get_engine()
    if engine is not None:
        try:
            query = """
                SELECT
                    date, period, year, month, country_code, country_code3,
                    country_name_en, country_name_kh, country_groups,
                    trade_type, regime_code, value_usd, value_khr, loaded_at
                FROM warehouse.fact_country_trade
                ORDER BY date ASC, trade_type ASC, value_usd DESC
            """
            return pd.read_sql(query, engine, parse_dates=["date"])
        except Exception:
            pass
    # Offline Parquet Fallback
    p_path = DATA_DIR / "fact_country_trade.parquet"
    if p_path.is_file():
        df = pd.read_parquet(p_path)
        df["date"] = pd.to_datetime(df["date"])
        return df
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_sitc_data() -> pd.DataFrame:
    engine = get_engine()
    if engine is not None:
        try:
            query = """
                SELECT
                    date, period, year, month, sitc_code, description_en,
                    description_kh, trade_type, regime_code, value_usd, value_khr, loaded_at
                FROM warehouse.fact_trade_by_sitc
                ORDER BY date ASC, trade_type ASC, value_usd DESC
            """
            return pd.read_sql(query, engine, parse_dates=["date"])
        except Exception:
            pass
    # Offline Parquet Fallback
    p_path = DATA_DIR / "fact_trade_by_sitc.parquet"
    if p_path.is_file():
        df = pd.read_parquet(p_path)
        df["date"] = pd.to_datetime(df["date"])
        return df
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_hs_data() -> pd.DataFrame:
    engine = get_engine()
    if engine is not None:
        try:
            query = """
                SELECT
                    date, period, year, month, hs_chapter, description_en,
                    description_kh, trade_type, regime_code, value_usd, value_khr, loaded_at
                FROM warehouse.fact_trade_by_hs
                ORDER BY date ASC, trade_type ASC, value_usd DESC
            """
            return pd.read_sql(query, engine, parse_dates=["date"])
        except Exception:
            pass
    # Offline Parquet Fallback
    p_path = DATA_DIR / "fact_trade_by_hs.parquet"
    if p_path.is_file():
        df = pd.read_parquet(p_path)
        df["date"] = pd.to_datetime(df["date"])
        return df
    return pd.DataFrame()


# --- Main Dashboard ---
st.title("📊 Cambodia International Trade & Transport Analytics")
st.caption("Official Statistics from General Department of Customs and Excise of Cambodia (GDCE)")

df_transport = load_transport_data()
df_country = load_country_data()
df_sitc = load_sitc_data()
df_hs = load_hs_data()

if df_transport.empty:
    st.warning("Data Warehouse is currently empty or offline. Run the Airflow ETL pipeline or check data snapshots.")
    st.stop()

# ==========================================
# 🧭 SIDEBAR: ANALYTICS CONTROL HUB
# ==========================================
st.sidebar.markdown("## 🧭 Analytics Control Hub")
st.sidebar.caption("Executive Suite for Investors, Economists & Policy Makers")
if get_engine() is not None:
    st.sidebar.success("🟢 Live DW Connected (PostgreSQL)", icon="📡")
else:
    st.sidebar.info("📦 GDCE Verified Snapshot Active", icon="💾")

# 1. Geopolitical & FTA Economic Blocs
st.sidebar.markdown("### 🌐 Trade Corridor / FTA Bloc")
ECONOMIC_BLOCS = {
    "🌐 Global (All Trading Partners)": None,
    "🌏 RCEP Corridor (15 Asia-Pacific)": [
        "China", "Japan", "Korea", "Australia", "New Zealand",
        "Viet Nam", "Vietnam", "Thailand", "Singapore", "Malaysia",
        "Indonesia", "Philippines", "Myanmar", "Laos", "Lao", "Brunei"
    ],
    "🤝 ASEAN Single Market (10 Nations)": [
        "Viet Nam", "Vietnam", "Thailand", "Singapore", "Malaysia",
        "Indonesia", "Philippines", "Myanmar", "Laos", "Lao", "Brunei"
    ],
    "🇪🇺 European Union (EBA Preference)": [
        "Germany", "France", "Netherlands", "Italy", "Spain", "Belgium",
        "Poland", "Sweden", "Austria", "Denmark", "Ireland", "Portugal", "Finland"
    ],
    "🇺🇸 United States (GSP & Major Market)": ["United States", "USA", "U.S.A."],
    "🇨🇳 China (CCFTA Bilateral Corridor)": ["China", "Hong Kong", "Taiwan"],
    "🇯🇵 Japan & Korea (Bilateral FTAs)": ["Japan", "Korea", "Republic of Korea", "South Korea"],
}
selected_bloc_name = st.sidebar.selectbox("Economic Partnership", list(ECONOMIC_BLOCS.keys()), index=0)
selected_bloc_countries = ECONOMIC_BLOCS[selected_bloc_name]

# 2. Strategic Industry & Commodity Focus
st.sidebar.markdown("### 🏭 Strategic Industry Focus")
COMMODITY_PILLARS = {
    "📦 All Commodity Sectors": None,
    "🧵 Garments, Footwear & Travel Goods (GFT)": ["61", "62", "63", "64", "42"],
    "⚡ Electrical Machinery & Solar Panels (HS 85)": ["85"],
    "🌾 Agriculture & Agri-Food (HS 01–24, 40)": [f"{i:02d}" for i in range(1, 25)] + ["40"],
    "🚗 Automotive & Transport Vehicles (HS 87)": ["87"],
    "🏗️ Construction Materials & Steel (HS 72, 73, 25)": ["72", "73", "25", "68", "69"],
    "🧪 Plastics & Chemicals (HS 28–39)": [f"{i:02d}" for i in range(28, 40)],
}
selected_sector_name = st.sidebar.selectbox("Pillar Sector Focus", list(COMMODITY_PILLARS.keys()), index=0)
selected_sector_chapters = COMMODITY_PILLARS[selected_sector_name]

# 3. Global Date Range
st.sidebar.markdown("### 📅 Reporting Period")
min_date = df_transport["date"].min().date()
max_date = df_transport["date"].max().date()
date_selection = st.sidebar.date_input(
    "Date Range Window",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_selection, (tuple, list)) and len(date_selection) == 2:
    start_dt, end_dt = pd.Timestamp(date_selection[0]), pd.Timestamp(date_selection[1])
else:
    start_dt, end_dt = pd.Timestamp(min_date), pd.Timestamp(max_date)

# 4. Currency & Scaling
st.sidebar.markdown("### 💱 Currency & Scale")
c_col1, c_col2 = st.sidebar.columns(2)
with c_col1:
    currency = st.selectbox("Currency", ["USD ($)", "KHR (៛)"], index=0)
with c_col2:
    num_scale = st.selectbox("Scale Unit", ["Auto Smart", "Billions", "Millions", "Exact"], index=0)

val_col = "value_usd" if "USD" in currency else "value_khr"
curr_symbol = "$" if "USD" in currency else "៛"

# 5. Data Pipeline & Warehouse Diagnostics Badge
st.sidebar.markdown("---")
st.sidebar.markdown("### 🟢 Data Lineage & Status")
total_records = len(df_transport) + len(df_country) + len(df_sitc) + len(df_hs)
months_count = df_country["date"].nunique()

st.sidebar.markdown(
    f"""
    <div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(128,128,128,0.2); border-radius: 8px; padding: 10px; font-size: 0.8rem; margin-bottom: 10px;">
        <div><b>Warehouse:</b> PostgreSQL 16 (Tier-2)</div>
        <div><b>Coverage:</b> {min_date.strftime('%b %Y')} – {max_date.strftime('%b %Y')} ({months_count}M)</div>
        <div><b>Transactions:</b> {total_records:,.0f} rows loaded</div>
        <div style="color: #10b981; font-weight: 600; margin-top: 4px;">● Live ETL Synced</div>
    </div>
    """,
    unsafe_allow_html=True,
)

b_col1, b_col2 = st.sidebar.columns(2)
with b_col1:
    if st.button("🔄 Flush Cache", use_container_width=True, help="Clear Streamlit memory cache"):
        st.cache_data.clear()
        st.rerun()

# Apply Filters
f_transport = df_transport[(df_transport["date"] >= start_dt) & (df_transport["date"] <= end_dt)]
f_country = df_country[(df_country["date"] >= start_dt) & (df_country["date"] <= end_dt)]
f_sitc = df_sitc[(df_sitc["date"] >= start_dt) & (df_sitc["date"] <= end_dt)]
f_hs = df_hs[(df_hs["date"] >= start_dt) & (df_hs["date"] <= end_dt)]

# Apply Economic Bloc Filter to Country dataset
if selected_bloc_countries is not None:
    bloc_regex = "|".join(selected_bloc_countries)
    f_country = f_country[f_country["country_name_en"].str.contains(bloc_regex, case=False, na=False)]

# Apply Sector Filter to HS / SITC dataset
if selected_sector_chapters is not None:
    f_hs = f_hs[f_hs["hs_chapter"].astype(str).str.zfill(2).isin(selected_sector_chapters)]

with b_col2:
    csv_exp = f_country.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export CSV",
        data=csv_exp,
        file_name=f"cambodia_gdce_trade_data_{start_dt.strftime('%Y%m')}_{end_dt.strftime('%Y%m')}.csv",
        mime="text/csv",
        use_container_width=True,
        help="Download filtered trade dataset",
    )

tab1, tab2, tab3, tab4 = st.tabs([
    "🏛️ Macro & Trade Balance",
    "🚢 Freight & Transport Modes",
    "📦 Commodity Sectors (SITC & HS)",
    "🔮 Predictive Forecasting",
])

def format_currency_smart(val: float, curr_sym: str = "$", scale_mode: str = "Auto Smart"):
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    full = f"{sign}{curr_sym} {abs_val:,.0f}"

    if scale_mode == "Billions":
        compact = f"{sign}{curr_sym} {abs_val / 1e9:,.2f} B"
    elif scale_mode == "Millions":
        compact = f"{sign}{curr_sym} {abs_val / 1e6:,.2f} M"
    elif scale_mode == "Exact":
        compact = full
    else:  # Auto Smart
        if abs_val >= 1e12:
            compact = f"{sign}{curr_sym} {abs_val / 1e12:,.2f} T"
        elif abs_val >= 1e9:
            compact = f"{sign}{curr_sym} {abs_val / 1e9:,.2f} B"
        elif abs_val >= 1e6:
            compact = f"{sign}{curr_sym} {abs_val / 1e6:,.2f} M"
        elif abs_val >= 1e3:
            compact = f"{sign}{curr_sym} {abs_val / 1e3:,.2f} K"
        else:
            compact = f"{sign}{curr_sym} {abs_val:,.0f}"

    return compact, full


format_number = format_currency_smart


def render_kpi_card(
    title: str,
    compact_val: str,
    full_val: str,
    badge_text: str,
    accent_color: str,
    icon: str,
    delta_text: str = None,
    delta_positive: bool = True,
):
    delta_html = ""
    if delta_text:
        d_color = "#10b981" if delta_positive else "#ef4444"
        d_arrow = "▲" if delta_positive else "▼"
        delta_html = f'<div style="font-size: 0.78rem; font-weight: 600; color: {d_color}; margin-top: 2px;">{d_arrow} {delta_text}</div>'

    card_html = (
        f'<div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(128, 128, 128, 0.2); '
        f'border-left: 5px solid {accent_color}; border-radius: 10px; padding: 14px 16px; '
        f'box-shadow: 0 2px 6px rgba(0,0,0,0.06); margin-bottom: 12px; min-height: 130px; '
        f'display: flex; flex-direction: column; justify-content: space-between;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
        f'<span style="font-size: 0.82rem; font-weight: 600; opacity: 0.75; text-transform: uppercase; letter-spacing: 0.5px;">{icon} {title}</span>'
        f'<span style="font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 9999px; background-color: {accent_color}25; color: {accent_color}; border: 1px solid {accent_color}40;">{badge_text}</span>'
        f'</div>'
        f'<div>'
        f'<div style="font-size: 1.55rem; font-weight: 700; line-height: 1.2; margin-bottom: 2px;">{compact_val}</div>'
        f'{delta_html}'
        f'</div>'
        f'<div style="font-size: 0.76rem; opacity: 0.6; font-family: monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 4px;" title="{full_val}">{full_val}</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


# Design System Color Palette (Unified across Cards, Charts & Legends)
COLOR_EXPORT = "#10b981"      # Emerald Green for Exports Card & Export Bars
COLOR_IMPORT = "#f59e0b"      # Amber / Warm Gold for Imports Card & Import Bars
COLOR_TRADE_VOL = "#3b82f6"   # Royal Blue for Total Trade Volume Card & Net Balance Line
COLOR_SURPLUS = "#10b981"     # Emerald Green for Trade Surplus
COLOR_DEFICIT = "#ef4444"     # Rose Red for Trade Deficit

# Transport Mode Icons, Labels, and Theme Palette
TRANSPORT_MODE_MAPPINGS = {
    "Sea transport": {
        "icon": "🚢",
        "label": "🚢 Sea Freight (Maritime)",
        "short": "🚢 Sea",
        "color": "#0284c7",
    },
    "Road transport": {
        "icon": "🚚",
        "label": "🚚 Road Transport (Trucking)",
        "short": "🚚 Road",
        "color": "#f59e0b",
    },
    "Inland waterways transport": {
        "icon": "⛴️",
        "label": "⛴️ Inland Waterways (River Barge)",
        "short": "⛴️ River",
        "color": "#06b6d4",
    },
    "Air transport": {
        "icon": "✈️",
        "label": "✈️ Air Cargo (Aviation)",
        "short": "✈️ Air",
        "color": "#8b5cf6",
    },
    "Rail transport": {
        "icon": "🚆",
        "label": "🚆 Rail Transport (Railway)",
        "short": "🚆 Rail",
        "color": "#10b981",
    },
    "Postal Transport": {
        "icon": "📮",
        "label": "📮 Postal & Express Consignment",
        "short": "📮 Postal",
        "color": "#ec4899",
    },
    "Transport on fixed installation": {
        "icon": "⚡",
        "label": "⚡ Fixed Installation / Grid",
        "short": "⚡ Fixed",
        "color": "#64748b",
    },
}


def get_transport_mode_meta(description: str):
    """Returns (label, icon, color, short_label) for any transport mode description."""
    desc_str = str(description).strip()
    for key, meta in TRANSPORT_MODE_MAPPINGS.items():
        if key.lower() == desc_str.lower():
            return meta["label"], meta["icon"], meta["color"], meta["short"]
    for key, meta in TRANSPORT_MODE_MAPPINGS.items():
        if key.lower() in desc_str.lower() or desc_str.lower() in key.lower():
            return meta["label"], meta["icon"], meta["color"], meta["short"]
    if "sea" in desc_str.lower() or "marine" in desc_str.lower():
        return f"🚢 {desc_str}", "🚢", "#0284c7", "🚢 Sea"
    elif "road" in desc_str.lower() or "land" in desc_str.lower() or "vehicle" in desc_str.lower():
        return f"🚚 {desc_str}", "🚚", "#f59e0b", "🚚 Road"
    elif "waterway" in desc_str.lower() or "river" in desc_str.lower() or "barge" in desc_str.lower():
        return f"⛴️ {desc_str}", "⛴️", "#06b6d4", "⛴️ River"
    elif "air" in desc_str.lower() or "aviation" in desc_str.lower():
        return f"✈️ {desc_str}", "✈️", "#8b5cf6", "✈️ Air"
    elif "rail" in desc_str.lower() or "train" in desc_str.lower():
        return f"🚆 {desc_str}", "🚆", "#10b981", "🚆 Rail"
    elif "post" in desc_str.lower() or "mail" in desc_str.lower() or "courier" in desc_str.lower():
        return f"📮 {desc_str}", "📮", "#ec4899", "📮 Post"
    return f"📦 {desc_str}", "📦", "#64748b", f"📦 {desc_str[:12]}"


# Geographic Coordinates for Bilateral Flow Map (ISO-3, ISO-2, & Standard English Names)
CAMBODIA_GEO = {"lat": 12.5657, "lon": 104.9910, "name": "Cambodia (Phnom Penh Hub)"}

COUNTRY_GEO = {
    "USA": (37.0902, -95.7129, "United States"),
    "UNITED STATES": (37.0902, -95.7129, "United States"),
    "CHN": (35.8617, 104.1954, "China"),
    "CHINA": (35.8617, 104.1954, "China"),
    "VNM": (14.0583, 108.2772, "Vietnam"),
    "VIET NAM": (14.0583, 108.2772, "Vietnam"),
    "VIETNAM": (14.0583, 108.2772, "Vietnam"),
    "THA": (15.8700, 100.9925, "Thailand"),
    "THAILAND": (15.8700, 100.9925, "Thailand"),
    "JPN": (36.2048, 138.2529, "Japan"),
    "JAPAN": (36.2048, 138.2529, "Japan"),
    "DEU": (51.1657, 10.4515, "Germany"),
    "GERMANY": (51.1657, 10.4515, "Germany"),
    "CAN": (56.1304, -106.3468, "Canada"),
    "CANADA": (56.1304, -106.3468, "Canada"),
    "GBR": (55.3781, -3.4360, "United Kingdom"),
    "UNITED KINGDOM": (55.3781, -3.4360, "United Kingdom"),
    "GREAT BRITAIN": (55.3781, -3.4360, "United Kingdom"),
    "UK": (55.3781, -3.4360, "United Kingdom"),
    "SGP": (1.3521, 103.8198, "Singapore"),
    "SINGAPORE": (1.3521, 103.8198, "Singapore"),
    "MYS": (4.2105, 101.9758, "Malaysia"),
    "MALAYSIA": (4.2105, 101.9758, "Malaysia"),
    "IDN": (-0.7893, 113.9213, "Indonesia"),
    "INDONESIA": (-0.7893, 113.9213, "Indonesia"),
    "PHL": (12.8797, 121.7740, "Philippines"),
    "PHILIPPINES": (12.8797, 121.7740, "Philippines"),
    "NLD": (52.1326, 5.2913, "Netherlands"),
    "NETHERLANDS": (52.1326, 5.2913, "Netherlands"),
    "FRA": (46.2276, 2.2137, "France"),
    "FRANCE": (46.2276, 2.2137, "France"),
    "ITA": (41.8719, 12.5674, "Italy"),
    "ITALY": (41.8719, 12.5674, "Italy"),
    "ESP": (40.4637, -3.7492, "Spain"),
    "SPAIN": (40.4637, -3.7492, "Spain"),
    "BEL": (50.5039, 4.4699, "Belgium"),
    "BELGIUM": (50.5039, 4.4699, "Belgium"),
    "KOR": (35.9078, 127.7669, "South Korea"),
    "KOREA": (35.9078, 127.7669, "South Korea"),
    "SOUTH KOREA": (35.9078, 127.7669, "South Korea"),
    "REPUBLIC OF KOREA": (35.9078, 127.7669, "South Korea"),
    "AUS": (-25.2744, 133.7751, "Australia"),
    "AUSTRALIA": (-25.2744, 133.7751, "Australia"),
    "NZL": (-40.9006, 174.8860, "New Zealand"),
    "NEW ZEALAND": (-40.9006, 174.8860, "New Zealand"),
    "CHE": (46.8182, 8.2275, "Switzerland"),
    "SWITZERLAND": (46.8182, 8.2275, "Switzerland"),
    "IND": (20.5937, 78.9629, "India"),
    "INDIA": (20.5937, 78.9629, "India"),
    "HKG": (22.3193, 114.1694, "Hong Kong"),
    "HONG KONG": (22.3193, 114.1694, "Hong Kong"),
    "TWN": (23.6978, 120.9605, "Taiwan"),
    "TAIWAN": (23.6978, 120.9605, "Taiwan"),
    "POL": (51.9194, 19.1451, "Poland"),
    "POLAND": (51.9194, 19.1451, "Poland"),
    "SWE": (60.1282, 18.6435, "Sweden"),
    "SWEDEN": (60.1282, 18.6435, "Sweden"),
    "AUT": (47.5162, 14.5501, "Austria"),
    "AUSTRIA": (47.5162, 14.5501, "Austria"),
    "DNK": (56.2639, 9.5018, "Denmark"),
    "DENMARK": (56.2639, 9.5018, "Denmark"),
    "IRL": (53.1424, -7.6921, "Ireland"),
    "IRELAND": (53.1424, -7.6921, "Ireland"),
    "PRT": (39.3999, -8.2245, "Portugal"),
    "PORTUGAL": (39.3999, -8.2245, "Portugal"),
    "FIN": (61.9241, 25.7482, "Finland"),
    "FINLAND": (61.9241, 25.7482, "Finland"),
    "MEX": (23.6345, -102.5528, "Mexico"),
    "MEXICO": (23.6345, -102.5528, "Mexico"),
    "BRA": (-14.2350, -51.9253, "Brazil"),
    "BRAZIL": (-14.2350, -51.9253, "Brazil"),
    "ARE": (23.4241, 53.8478, "UAE"),
    "UAE": (23.4241, 53.8478, "UAE"),
    "UNITED ARAB EMIRATES": (23.4241, 53.8478, "UAE"),
    "SAU": (23.8859, 45.0792, "Saudi Arabia"),
    "SAUDI ARABIA": (23.8859, 45.0792, "Saudi Arabia"),
    "TUR": (38.9637, 35.2433, "Turkey"),
    "TURKEY": (38.9637, 35.2433, "Turkey"),
    "RUS": (61.5240, 105.3188, "Russia"),
    "RUSSIA": (61.5240, 105.3188, "Russia"),
    "RUSSIAN FEDERATION": (61.5240, 105.3188, "Russia"),
    "NOR": (60.4720, 8.4689, "Norway"),
    "NORWAY": (60.4720, 8.4689, "Norway"),
    "ISR": (31.0461, 34.8516, "Israel"),
    "ISRAEL": (31.0461, 34.8516, "Israel"),
    "MMR": (21.9162, 95.9560, "Myanmar"),
    "MYANMAR": (21.9162, 95.9560, "Myanmar"),
    "BURMA": (21.9162, 95.9560, "Myanmar"),
    "LAO": (19.8563, 102.4955, "Laos"),
    "LAOS": (19.8563, 102.4955, "Laos"),
    "BGD": (23.6850, 90.3563, "Bangladesh"),
    "BANGLADESH": (23.6850, 90.3563, "Bangladesh"),
    "LKA": (7.8731, 80.7718, "Sri Lanka"),
    "SRI LANKA": (7.8731, 80.7718, "Sri Lanka"),
    "PAK": (30.3753, 69.3451, "Pakistan"),
    "PAKISTAN": (30.3753, 69.3451, "Pakistan"),
    "ZAF": (-30.5595, 22.9375, "South Africa"),
    "SOUTH AFRICA": (-30.5595, 22.9375, "South Africa"),
    "EGY": (26.8206, 30.8025, "Egypt"),
    "EGYPT": (26.8206, 30.8025, "Egypt"),
    "CHL": (-35.6751, -71.5430, "Chile"),
    "CHILE": (-35.6751, -71.5430, "Chile"),
    "ARG": (-38.4161, -63.6167, "Argentina"),
    "ARGENTINA": (-38.4161, -63.6167, "Argentina"),
    "COL": (4.5709, -74.2973, "Colombia"),
    "COLOMBIA": (4.5709, -74.2973, "Colombia"),
    "PER": (-9.1900, -75.0152, "Peru"),
    "PERU": (-9.1900, -75.0152, "Peru"),
    "CZE": (49.8175, 15.4730, "Czechia"),
    "CZECH REPUBLIC": (49.8175, 15.4730, "Czechia"),
    "HUN": (47.1625, 19.5033, "Hungary"),
    "HUNGARY": (47.1625, 19.5033, "Hungary"),
    "ROU": (45.9432, 24.9668, "Romania"),
    "ROMANIA": (45.9432, 24.9668, "Romania"),
    "BGR": (42.7339, 25.4858, "Bulgaria"),
    "BULGARIA": (42.7339, 25.4858, "Bulgaria"),
    "GRC": (39.0742, 21.8243, "Greece"),
    "GREECE": (39.0742, 21.8243, "Greece"),
}


def lookup_country_geo(name: str = None, code3: str = None):
    """Look up latitude, longitude and canonical name for a country."""
    if code3 and str(code3).strip().upper() in COUNTRY_GEO:
        return COUNTRY_GEO[str(code3).strip().upper()]
    if name:
        clean_name = str(name).strip().upper()
        if clean_name in COUNTRY_GEO:
            return COUNTRY_GEO[clean_name]
        # Partial / alias match
        for k, v in COUNTRY_GEO.items():
            if len(k) > 3 and (k in clean_name or clean_name in k):
                return v
    return None


def render_powerbi_macro_canvas(
    f_tab1_macro: pd.DataFrame,
    f_tab1_country: pd.DataFrame,
    df_transport: pd.DataFrame,
    df_hs: pd.DataFrame,
    t_start: pd.Timestamp,
    t_end: pd.Timestamp,
    is_yearly_view: bool,
    min_dw_date: pd.Timestamp,
    max_dw_date: pd.Timestamp,
    period_info: str,
    sector_title_suffix: str,
    selected_sector_chapters: Optional[list],
    val_col: str,
    currency: str,
    curr_symbol: str,
    num_scale: str,
    bal_color: str,
):
    """
    Renders the unified, single-page Microsoft Power BI-style Executive Dashboard Canvas.
    Merges all 5 macro and trade balance visuals into a synchronized, non-scrolling 2-row grid:
      - Row 1 (60% / 40%): Macro Trade Trajectory & Net Balance Dynamics + Global Bilateral Corridors Hub Map (with Trade Flow Button)
      - Row 2 (33% / 33% / 34%): Top Trading Partners + Freight Modal Split + Strategic Commodity Pillars
      - Row 3: Collapsible Drawer with detailed drill-down data tables
    """
    f_tab1_transport = df_transport[(df_transport["date"] >= t_start) & (df_transport["date"] <= t_end)]
    f_tab1_hs = df_hs[(df_hs["date"] >= t_start) & (df_hs["date"] <= t_end)]
    if selected_sector_chapters is not None:
        f_tab1_hs = f_tab1_hs[f_tab1_hs["hs_chapter"].astype(str).str.zfill(2).isin(selected_sector_chapters)]

    # Compute baseline bilateral partner aggregations across all flows
    map_agg = f_tab1_country.groupby(["country_name_en", "country_code3", "trade_type"])[val_col].sum().reset_index()
    partner_totals = map_agg.groupby("country_name_en")[val_col].sum().nlargest(8)
    top_partner_names = partner_totals.index.tolist()
    total_flow_val = map_agg[val_col].sum() if not map_agg.empty else 1.0
    max_val_top = partner_totals.max() if not partner_totals.empty else 1.0

    # =========================================================================
    # ROW 1: MACRO DYNAMICS & GLOBAL BILATERAL CORRIDORS (60% / 40%)
    # =========================================================================
    r1_col1, r1_col2 = st.columns([1.38, 1.0])

    with r1_col1:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                <span style="font-size: 0.95rem; font-weight: 700; color: #1e293b;">📊 Trade Trajectory & Net Balance Dynamics</span>
                <span style="font-size: 0.74rem; color: #64748b; font-weight: 500;">{period_info.split('(')[-1].replace(')', '') if '(' in period_info else period_info}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig_macro_pbi = go.Figure()
        if is_yearly_view:
            yearly_temp = f_tab1_macro.copy()
            yearly_temp["year"] = yearly_temp["date"].dt.year
            yearly_trade = yearly_temp.groupby(["year", "trade_type"])[val_col].sum().reset_index()
            yearly_piv = yearly_trade.pivot(index="year", columns="trade_type", values=val_col).fillna(0)
            yearly_piv["Trade Balance"] = yearly_piv.get("Export", 0) - yearly_piv.get("Import", 0)
            if "Export" in yearly_piv:
                fig_macro_pbi.add_trace(go.Bar(x=yearly_piv.index, y=yearly_piv["Export"], name="Annual Exports", marker_color=COLOR_EXPORT))
            if "Import" in yearly_piv:
                fig_macro_pbi.add_trace(go.Bar(x=yearly_piv.index, y=yearly_piv["Import"], name="Annual Imports", marker_color=COLOR_IMPORT))
            if "Trade Balance" in yearly_piv:
                fig_macro_pbi.add_trace(go.Scatter(x=yearly_piv.index, y=yearly_piv["Trade Balance"], name="Net Trade Balance", line=dict(color=bal_color, width=3.2), mode="lines+markers", marker=dict(size=7)))
            fig_macro_pbi.update_layout(
                barmode="group",
                xaxis=dict(tickmode="linear", dtick=1, showgrid=False),
                yaxis=dict(title=f"Value ({currency})", showgrid=True, gridcolor="rgba(128,128,128,0.15)"),
                hovermode="x unified",
                height=335,
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center", font=dict(size=10)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
        else:
            monthly_trade = f_tab1_macro.groupby(["date", "trade_type"])[val_col].sum().reset_index()
            monthly_piv = monthly_trade.pivot(index="date", columns="trade_type", values=val_col).fillna(0)
            if "Export" in monthly_piv and "Import" in monthly_piv:
                monthly_piv["Trade Balance"] = monthly_piv["Export"] - monthly_piv["Import"]
            if "Export" in monthly_piv:
                fig_macro_pbi.add_trace(go.Bar(x=monthly_piv.index, y=monthly_piv["Export"], name="Exports", marker_color=COLOR_EXPORT))
            if "Import" in monthly_piv:
                fig_macro_pbi.add_trace(go.Bar(x=monthly_piv.index, y=monthly_piv["Import"], name="Imports", marker_color=COLOR_IMPORT))
            if "Trade Balance" in monthly_piv:
                fig_macro_pbi.add_trace(go.Scatter(x=monthly_piv.index, y=monthly_piv["Trade Balance"], name="Net Balance", line=dict(color=bal_color, width=2.8), mode="lines+markers", marker=dict(size=5)))
            fig_macro_pbi.update_layout(
                barmode="group",
                xaxis=dict(showgrid=False),
                yaxis=dict(title=f"Value ({currency})", showgrid=True, gridcolor="rgba(128,128,128,0.15)"),
                hovermode="x unified",
                height=335,
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center", font=dict(size=10)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
        st.plotly_chart(fig_macro_pbi, use_container_width=True)

    with r1_col2:
        pbi_map_hcol1, pbi_map_hcol2, pbi_map_hcol3 = st.columns([1.22, 1.35, 0.85])
        with pbi_map_hcol1:
            st.markdown(
                """
                <div style="font-size: 0.93rem; font-weight: 700; color: #1e293b; margin-top: 4px; white-space: nowrap;">
                    🌐 Global Bilateral Corridors
                </div>
                """,
                unsafe_allow_html=True,
            )
        with pbi_map_hcol2:
            pbi_corridor_flow = st.radio(
                "Corridor Flow",
                ["🟢 Export", "🟡 Import", "🔄 Both"],
                horizontal=True,
                key="pbi_corridor_flow_select",
                label_visibility="collapsed",
            )
        with pbi_map_hcol3:
            pbi_map_proj = st.selectbox(
                "Map View",
                ["🌍 3D Globe", "🗺️ 2D Flat"],
                key="pbi_map_proj_selector",
                label_visibility="collapsed",
            )

        # Reactive corridor flow filtering based on user button selection
        is_exp_corridor = "Export" in pbi_corridor_flow
        is_imp_corridor = "Import" in pbi_corridor_flow

        if is_exp_corridor:
            flow_sub = map_agg[map_agg["trade_type"] == "Export"]
            corridor_partner_totals = flow_sub.groupby("country_name_en")[val_col].sum().nlargest(8)
        elif is_imp_corridor:
            flow_sub = map_agg[map_agg["trade_type"] == "Import"]
            corridor_partner_totals = flow_sub.groupby("country_name_en")[val_col].sum().nlargest(8)
        else:
            corridor_partner_totals = partner_totals.copy()

        map_top_partner_names = corridor_partner_totals.index.tolist()
        max_corridor_val = corridor_partner_totals.max() if not corridor_partner_totals.empty else 1.0

        fig_pbi_map = go.Figure()
        p_lats, p_lons, p_names_p, p_sizes, p_colors, p_texts = [], [], [], [], [], []

        for p_name in map_top_partner_names:
            p_data = map_agg[map_agg["country_name_en"] == p_name]
            p_code = p_data["country_code3"].iloc[0] if not p_data.empty and "country_code3" in p_data else None
            geo = lookup_country_geo(p_name, p_code)
            if not geo:
                continue
            p_lat, p_lon, canonical_name = geo
            p_tot = corridor_partner_totals[p_name]
            p_compact, _ = format_currency_smart(p_tot, curr_symbol, num_scale)
            p_exp = p_data[p_data["trade_type"] == "Export"][val_col].sum() if "Export" in p_data["trade_type"].values else 0
            p_imp = p_data[p_data["trade_type"] == "Import"][val_col].sum() if "Import" in p_data["trade_type"].values else 0

            if is_exp_corridor:
                line_color = COLOR_EXPORT
                flow_label = "Outbound Export Corridor (Cambodia ➔ Market)"
                hover_txt = f"<b>{canonical_name}</b><br>{flow_label}<br>Exports: {format_currency_smart(p_exp, curr_symbol, num_scale)[0]}"
            elif is_imp_corridor:
                line_color = COLOR_IMPORT
                flow_label = "Inbound Import Corridor (Market ➔ Cambodia)"
                hover_txt = f"<b>{canonical_name}</b><br>{flow_label}<br>Imports: {format_currency_smart(p_imp, curr_symbol, num_scale)[0]}"
            else:
                line_color = COLOR_EXPORT if p_exp >= p_imp else COLOR_IMPORT
                hover_txt = f"<b>{canonical_name}</b><br>Total Trade: {p_compact}<br>Exports: {format_currency_smart(p_exp, curr_symbol, num_scale)[0]} | Imports: {format_currency_smart(p_imp, curr_symbol, num_scale)[0]}"

            line_w = max(1.5, min(5.0, (p_tot / max_corridor_val) * 5.0))

            fig_pbi_map.add_trace(go.Scattergeo(
                locationmode="country names",
                lon=[CAMBODIA_GEO["lon"], p_lon],
                lat=[CAMBODIA_GEO["lat"], p_lat],
                mode="lines",
                line=dict(width=line_w, color=line_color),
                opacity=0.75,
                hoverinfo="text",
                text=hover_txt,
                showlegend=False,
            ))
            p_lons.append(p_lon)
            p_lats.append(p_lat)
            p_names_p.append(canonical_name)
            p_sizes.append(max(6, min(18, (p_tot / max_corridor_val) * 18)))
            p_colors.append(line_color)
            p_texts.append(f"<b>{canonical_name}</b>: {p_compact}")

        if p_lats:
            fig_pbi_map.add_trace(go.Scattergeo(
                lon=p_lons, lat=p_lats,
                mode="markers+text",
                marker=dict(size=p_sizes, color=p_colors, opacity=0.9, line=dict(width=1, color="#ffffff")),
                text=p_names_p,
                textposition="top center",
                textfont=dict(size=9, color="#0f172a"),
                hoverinfo="text", hovertext=p_texts,
                showlegend=False,
            ))

        fig_pbi_map.add_trace(go.Scattergeo(
            lon=[CAMBODIA_GEO["lon"]], lat=[CAMBODIA_GEO["lat"]],
            mode="markers+text",
            marker=dict(size=13, color="#ef4444", symbol="star", line=dict(width=1.5, color="#b91c1c")),
            text=["🇰🇭 Hub"], textposition="bottom center",
            textfont=dict(size=10, color="#b91c1c"),
            hoverinfo="text", hovertext="<b>🇰🇭 Cambodia (Phnom Penh Hub)</b>",
            showlegend=False,
        ))

        if "3D" in pbi_map_proj:
            geo_cfg = dict(
                projection_type="orthographic",
                projection_rotation=dict(lon=105, lat=13, roll=0),
                showland=True, landcolor="#f8fafc",
                showocean=True, oceancolor="#e0f2fe",
                showcountries=True, countrycolor="#cbd5e1",
                showcoastlines=True, coastlinecolor="#94a3b8",
                bgcolor="rgba(0,0,0,0)",
            )
        else:
            geo_cfg = dict(
                projection_type="natural earth",
                center=dict(lat=20, lon=105),
                projection_scale=1.35,
                showland=True, landcolor="#f8fafc",
                showocean=True, oceancolor="#e0f2fe",
                showcountries=True, countrycolor="#cbd5e1",
                showcoastlines=True, coastlinecolor="#94a3b8",
                bgcolor="rgba(0,0,0,0)",
            )

        fig_pbi_map.update_layout(
            geo=geo_cfg,
            margin=dict(l=5, r=5, t=10, b=5),
            height=335,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_pbi_map, use_container_width=True)

    # =========================================================================
    # ROW 2: 3-PILLAR OPERATIONAL VISUALS (33% / 33% / 34%)
    # =========================================================================
    r2_col1, r2_col2, r2_col3 = st.columns([1.0, 1.0, 1.0])

    with r2_col1:
        pbi_ptn_hcol1, pbi_ptn_hcol2 = st.columns([1.15, 1.85])
        with pbi_ptn_hcol1:
            st.markdown(
                """
                <div style="font-size: 0.92rem; font-weight: 700; color: #1e293b; margin-top: 4px; white-space: nowrap;">
                    🏆 Top Partners
                </div>
                """,
                unsafe_allow_html=True,
            )
        with pbi_ptn_hcol2:
            pbi_ptn_flow = st.radio(
                "Partner Flow",
                ["🟢 Export", "🟡 Import", "🔄 Both"],
                horizontal=True,
                key="pbi_ptn_flow_select",
                label_visibility="collapsed",
            )

        is_ptn_exp = "Export" in pbi_ptn_flow
        is_ptn_imp = "Import" in pbi_ptn_flow

        if is_ptn_exp:
            ptn_sub = map_agg[map_agg["trade_type"] == "Export"]
            ptn_totals = ptn_sub.groupby("country_name_en")[val_col].sum().nlargest(8)
            ptn_names = ptn_totals.index.tolist()
            ptn_colors = [COLOR_EXPORT] * len(ptn_names)
            ptn_hover_suffix = "Exports"
        elif is_ptn_imp:
            ptn_sub = map_agg[map_agg["trade_type"] == "Import"]
            ptn_totals = ptn_sub.groupby("country_name_en")[val_col].sum().nlargest(8)
            ptn_names = ptn_totals.index.tolist()
            ptn_colors = [COLOR_IMPORT] * len(ptn_names)
            ptn_hover_suffix = "Imports"
        else:
            ptn_totals = partner_totals.copy()
            ptn_names = ptn_totals.index.tolist()
            ptn_colors = [
                COLOR_EXPORT if map_agg[(map_agg["country_name_en"] == c) & (map_agg["trade_type"] == "Export")][val_col].sum() >= map_agg[(map_agg["country_name_en"] == c) & (map_agg["trade_type"] == "Import")][val_col].sum() else COLOR_IMPORT
                for c in ptn_names
            ]
            ptn_hover_suffix = "Total Trade"

        if not ptn_totals.empty:
            df_mini_pbi = pd.DataFrame({
                "Country": ptn_names[::-1],
                "Value": [ptn_totals[c] for c in ptn_names][::-1],
                "Color": ptn_colors[::-1],
            })
            fig_pbi_partners = go.Figure(go.Bar(
                x=df_mini_pbi["Value"],
                y=df_mini_pbi["Country"],
                orientation="h",
                marker_color=df_mini_pbi["Color"],
                text=[format_currency_smart(v, curr_symbol, num_scale)[0] for v in df_mini_pbi["Value"]],
                textposition="auto",
                hovertemplate=f"<b>%{{y}}</b>: %{{x:$,.2f}} ({ptn_hover_suffix})<extra></extra>",
            ))
            fig_pbi_partners.update_layout(
                margin=dict(l=0, r=10, t=15, b=10),
                height=295,
                xaxis=dict(showticklabels=False, showgrid=False),
                yaxis=dict(showgrid=False, tickfont=dict(size=10)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pbi_partners, use_container_width=True)
        else:
            st.info("No partner trade records for this flow.")

    with r2_col2:
        pbi_tm_hcol1, pbi_tm_hcol2 = st.columns([1.4, 1.6])
        with pbi_tm_hcol1:
            st.markdown(
                """
                <div style="font-size: 0.92rem; font-weight: 700; color: #1e293b; margin-top: 4px;">
                    🚢 Transport Modes
                </div>
                """,
                unsafe_allow_html=True,
            )
        with pbi_tm_hcol2:
            pbi_tm_flow = st.radio("TM Flow", ["🟢 Export", "🟡 Import"], horizontal=True, key="pbi_tm_flow_select", label_visibility="collapsed")

        pbi_regime = "Export" if "Export" in pbi_tm_flow else "Import"
        PRIMARY_TRANSPORT_MODES = ["Inland waterways transport", "Sea transport", "Road transport", "Air transport"]
        f_tm_clean = f_tab1_transport[(f_tab1_transport["regime"] == pbi_regime) & (f_tab1_transport["description"].isin(PRIMARY_TRANSPORT_MODES)) & (f_tab1_transport["net_weight_ton"] > 0)].copy()

        if not f_tm_clean.empty:
            modal_agg = f_tm_clean.groupby("description")["net_weight_ton"].sum().reset_index()
            modal_agg = modal_agg.sort_values(by="net_weight_ton", ascending=False)
            modal_agg["label"] = modal_agg["description"].apply(lambda d: get_transport_mode_meta(d)[0])
            modal_agg["icon"] = modal_agg["description"].apply(lambda d: get_transport_mode_meta(d)[1])
            modal_agg["color"] = modal_agg["description"].apply(lambda d: get_transport_mode_meta(d)[2])
            tot_w = modal_agg["net_weight_ton"].sum()
            modal_agg["pct"] = (modal_agg["net_weight_ton"] / tot_w * 100) if tot_w > 0 else 0
            modal_agg["txt"] = modal_agg.apply(
                lambda r: f"<b>{r['net_weight_ton']/1e6:.1f}M MT</b><br>({r['pct']:.0f}%)" if r["net_weight_ton"] >= 1e6
                else f"<b>{r['net_weight_ton']/1e3:.0f}K MT</b><br>({r['pct']:.0f}%)" if r["net_weight_ton"] >= 1e3
                else f"<b>{r['net_weight_ton']:.0f} MT</b><br>({r['pct']:.0f}%)", axis=1
            )
            fig_pbi_tm = go.Figure(go.Bar(
                x=modal_agg["icon"],
                y=modal_agg["net_weight_ton"],
                marker=dict(color=modal_agg["color"], cornerradius=6),
                text=modal_agg["txt"],
                textposition="outside",
                hovertemplate="<b>%{x}</b>: %{y:,.0f} Metric Tons<extra></extra>",
            ))
            max_tm_y = modal_agg["net_weight_ton"].max() * 1.25 if not modal_agg.empty else 100
            fig_pbi_tm.update_layout(
                xaxis=dict(tickfont=dict(size=26), showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.15)", range=[0, max_tm_y], tickfont=dict(size=9)),
                margin=dict(l=10, r=10, t=15, b=10),
                height=295,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pbi_tm, use_container_width=True)
        else:
            st.info("No modal transport records for this period.")

    with r2_col3:
        pbi_hs_hcol1, pbi_hs_hcol2 = st.columns([1.4, 1.6])
        with pbi_hs_hcol1:
            st.markdown(
                """
                <div style="font-size: 0.92rem; font-weight: 700; color: #1e293b; margin-top: 4px;">
                    📦 Strategic Commodities
                </div>
                """,
                unsafe_allow_html=True,
            )
        with pbi_hs_hcol2:
            pbi_hs_flow = st.radio("HS Flow", ["🟢 Exports", "🟡 Imports"], horizontal=True, key="pbi_hs_flow_select", label_visibility="collapsed")

        hs_type = "Export" if "Export" in pbi_hs_flow else "Import"
        f_hs_sub = f_tab1_hs[f_tab1_hs["trade_type"] == hs_type].groupby(["hs_chapter", "description_en"])[val_col].sum().reset_index()
        hs_top_pbi = f_hs_sub.nlargest(6, val_col).copy()

        if not hs_top_pbi.empty:
            hs_top_pbi["label"] = "Ch." + hs_top_pbi["hs_chapter"] + " " + hs_top_pbi["description_en"].str[:22]
            fig_pbi_hs = go.Figure(go.Bar(
                x=hs_top_pbi[val_col],
                y=hs_top_pbi["label"],
                orientation="h",
                marker_color=COLOR_EXPORT if hs_type == "Export" else COLOR_IMPORT,
                text=[format_currency_smart(v, curr_symbol, num_scale)[0] for v in hs_top_pbi[val_col]],
                textposition="auto",
            ))
            fig_pbi_hs.update_layout(
                margin=dict(l=0, r=10, t=15, b=10),
                height=295,
                xaxis=dict(showticklabels=False, showgrid=False),
                yaxis=dict(categoryorder="total ascending", showgrid=False, tickfont=dict(size=9.5)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pbi_hs, use_container_width=True)
        else:
            st.info("No commodity records for this period.")

    # =========================================================================
    # ROW 3: COLLAPSIBLE DEEP-DIVE AUDIT TABLES (BOTTOM DRAWER)
    # =========================================================================
    with st.expander("📋 Click to Expand Comprehensive Bilateral, Modal & Commodity Tables", expanded=False):
        pbi_tbl1, pbi_tbl2, pbi_tbl3 = st.tabs([
            "🌐 Bilateral Trading Partners Table",
            "🚢 Freight Transport Logistics Table",
            "📦 Strategic HS Commodities Directory",
        ])
        with pbi_tbl1:
            leaderboard_data = []
            for rank, p_name in enumerate(top_partner_names, 1):
                p_data = map_agg[map_agg["country_name_en"] == p_name]
                p_tot = partner_totals[p_name]
                pct_share = (p_tot / total_flow_val) * 100 if total_flow_val > 0 else 0
                p_exp = float(p_data[p_data["trade_type"] == "Export"][val_col].sum()) if "Export" in p_data["trade_type"].values else 0.0
                p_imp = float(p_data[p_data["trade_type"] == "Import"][val_col].sum()) if "Import" in p_data["trade_type"].values else 0.0
                p_bal = p_exp - p_imp
                c_exp_str, _ = format_currency_smart(p_exp, curr_symbol, num_scale)
                c_imp_str, _ = format_currency_smart(p_imp, curr_symbol, num_scale)
                c_tot_str, _ = format_currency_smart(p_tot, curr_symbol, num_scale)
                c_bal_str, _ = format_currency_smart(abs(p_bal), curr_symbol, num_scale)
                leaderboard_data.append({
                    "Rank": f"#{rank}", "Partner Country": p_name,
                    f"Total Trade ({currency})": c_tot_str, f"Exports ({currency})": c_exp_str,
                    f"Imports ({currency})": c_imp_str, f"Net Balance ({currency})": f"{'+' if p_bal >= 0 else '-'}{c_bal_str}",
                    "Share": f"{pct_share:.2f}%", "Flow": "🟢 Export" if p_exp >= p_imp else "🟡 Import"
                })
            df_leaderboard = pd.DataFrame(leaderboard_data)
            st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)
            st.download_button("📥 Export Partners CSV", df_leaderboard.to_csv(index=False).encode("utf-8"), "bilateral_partners.csv", "text/csv")

        with pbi_tbl2:
            if not f_tab1_transport.empty:
                df_modal_tbl = f_tab1_transport.groupby(["regime", "description"])["net_weight_ton"].sum().reset_index()
                st.dataframe(df_modal_tbl, use_container_width=True, hide_index=True)
                st.download_button("📥 Export Modal Logistics CSV", df_modal_tbl.to_csv(index=False).encode("utf-8"), "transport_modal_logistics.csv", "text/csv")

        with pbi_tbl3:
            if not f_tab1_hs.empty:
                df_hs_tbl = f_tab1_hs.groupby(["trade_type", "hs_chapter", "description_en"])[val_col].sum().reset_index()
                st.dataframe(df_hs_tbl, use_container_width=True, hide_index=True)
                st.download_button("📥 Export Commodities Directory CSV", df_hs_tbl.to_csv(index=False).encode("utf-8"), "hs_commodities.csv", "text/csv")


with tab1:
    tab1_head_col1, tab1_head_col2 = st.columns([2.5, 1.5])
    with tab1_head_col1:
        st.subheader("🏛️ National Trade Performance & Balance")
    with tab1_head_col2:
        tab1_canvas_mode = st.radio(
            "Canvas Layout Mode:",
            ["🎛️ PowerBI Unified Canvas (One Page)", "📑 Multi-Section Deep-Dive"],
            index=0,
            horizontal=True,
            key="tab1_canvas_layout_mode",
            label_visibility="collapsed",
        )

    # Time Horizon Quick Filter
    time_preset = st.radio(
        "⏳ Select Horizon / View Aggregation:",
        [
            "⚡ Last 3 Months (L3M)",
            "⚡ Last 6 Months (L6M)",
            "⚡ Last 12 Months (1 Year)",
            "📅 Annual Overview (All Years 2016–2026)",
            "🌐 All Monthly History (2016–2026)",
            "🎛️ Custom Range (from Sidebar)",
        ],
        index=0,
        horizontal=True,
    )

    max_dw_date = df_country["date"].max()
    min_dw_date = df_country["date"].min()

    # Base country dataset considering any sidebar Economic Bloc filter
    if selected_bloc_countries is not None:
        bloc_regex = "|".join(selected_bloc_countries)
        base_country_df = df_country[df_country["country_name_en"].str.contains(bloc_regex, case=False, na=False)]
    else:
        base_country_df = df_country

    # Determine base dataset for Macro Monthly Dynamics & Executive KPIs:
    # If a Pillar Sector Focus is selected, calculate monthly dynamics from the HS chapter dataset.
    # Otherwise, use national merchandise trade data (with economic bloc filter if applied).
    if selected_sector_chapters is not None:
        base_macro_df = df_hs[df_hs["hs_chapter"].astype(str).str.zfill(2).isin(selected_sector_chapters)]
    elif selected_bloc_countries is not None:
        base_macro_df = base_country_df
    else:
        base_macro_df = df_country

    # Calculate current and prior comparison date windows
    prior_df = None
    period_info = ""
    is_yearly_view = "Annual Overview" in time_preset

    if "3 Months" in time_preset:
        t_start = max_dw_date - pd.DateOffset(months=2)
        t_end = max_dw_date
        p_end = t_start - pd.DateOffset(months=1)
        p_start = p_end - pd.DateOffset(months=2)
        prior_df = base_macro_df[(base_macro_df["date"] >= p_start) & (base_macro_df["date"] <= p_end)]
        period_info = f"Showing Last 3 Months ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')}) vs. Prior 3 Months ({p_start.strftime('%b %Y')} – {p_end.strftime('%b %Y')})"
    elif "6 Months" in time_preset:
        t_start = max_dw_date - pd.DateOffset(months=5)
        t_end = max_dw_date
        p_end = t_start - pd.DateOffset(months=1)
        p_start = p_end - pd.DateOffset(months=5)
        prior_df = base_macro_df[(base_macro_df["date"] >= p_start) & (base_macro_df["date"] <= p_end)]
        period_info = f"Showing Last 6 Months ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')}) vs. Prior 6 Months ({p_start.strftime('%b %Y')} – {p_end.strftime('%b %Y')})"
    elif "12 Months" in time_preset:
        t_start = max_dw_date - pd.DateOffset(months=11)
        t_end = max_dw_date
        p_end = t_start - pd.DateOffset(months=1)
        p_start = p_end - pd.DateOffset(months=11)
        prior_df = base_macro_df[(base_macro_df["date"] >= p_start) & (base_macro_df["date"] <= p_end)]
        period_info = f"Showing Last 12 Months ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')}) vs. Prior 12 Months ({p_start.strftime('%b %Y')} – {p_end.strftime('%b %Y')})"
    elif is_yearly_view:
        t_start = min_dw_date
        t_end = max_dw_date
        period_info = f"Showing Annual Aggregation across all recorded calendar years ({min_dw_date.year} – {max_dw_date.year})"
    elif "All Monthly" in time_preset:
        t_start = min_dw_date
        t_end = max_dw_date
        period_info = f"Showing Full Monthly Historical Dataset ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')})"
    else:  # Custom from sidebar
        t_start = start_dt
        t_end = end_dt
        period_info = f"Showing Custom Selection ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')})"

    f_tab1_macro = base_macro_df[(base_macro_df["date"] >= t_start) & (base_macro_df["date"] <= t_end)]
    f_tab1_country = base_country_df[(base_country_df["date"] >= t_start) & (base_country_df["date"] <= t_end)]

    if selected_sector_chapters is not None:
        st.info(f"🎯 **Pillar Sector Focus Active ({selected_sector_name}):** Monthly & annual trade dynamics, KPIs, and product breakdowns below are dynamically filtered for HS chapters **{', '.join(selected_sector_chapters)}**.")

    st.caption(f"🗓️ **Active View:** {period_info}")

    # Compute current KPIs from macro dataset
    macro_summary = f_tab1_macro.groupby("trade_type")[val_col].sum()
    total_exp = float(macro_summary.get("Export", 0.0))
    total_imp = float(macro_summary.get("Import", 0.0))
    trade_balance = total_exp - total_imp
    total_trade = total_exp + total_imp

    exp_share = (total_exp / total_trade * 100) if total_trade > 0 else 0.0
    imp_share = (total_imp / total_trade * 100) if total_trade > 0 else 0.0

    # Compute Period-over-Period Deltas if prior baseline exists
    delta_trade_str, delta_exp_str, delta_imp_str, delta_bal_str = None, None, None, None
    delta_trade_pos, delta_exp_pos, delta_imp_pos, delta_bal_pos = True, True, True, True

    if prior_df is not None and not prior_df.empty:
        p_summary = prior_df.groupby("trade_type")[val_col].sum()
        p_exp = float(p_summary.get("Export", 0.0))
        p_imp = float(p_summary.get("Import", 0.0))
        p_trade = p_exp + p_imp
        p_bal = p_exp - p_imp

        if p_trade > 0:
            pct_trade = ((total_trade - p_trade) / p_trade) * 100
            delta_trade_str = f"{pct_trade:+.1f}% vs prior period"
            delta_trade_pos = pct_trade >= 0

        if p_exp > 0:
            pct_exp = ((total_exp - p_exp) / p_exp) * 100
            delta_exp_str = f"{pct_exp:+.1f}% vs prior period"
            delta_exp_pos = pct_exp >= 0

        if p_imp > 0:
            pct_imp = ((total_imp - p_imp) / p_imp) * 100
            delta_imp_str = f"{pct_imp:+.1f}% vs prior period"
            delta_imp_pos = pct_imp >= 0

        bal_diff = trade_balance - p_bal
        c_bdiff, _ = format_currency_smart(abs(bal_diff), curr_symbol, scale_mode=num_scale)
        delta_bal_str = f"{'+' if bal_diff >= 0 else '-'}{c_bdiff} vs prior period"
        delta_bal_pos = bal_diff >= 0

    c_tot, f_tot = format_currency_smart(total_trade, curr_symbol, scale_mode=num_scale)
    c_exp, f_exp = format_currency_smart(total_exp, curr_symbol, scale_mode=num_scale)
    c_imp, f_imp = format_currency_smart(total_imp, curr_symbol, scale_mode=num_scale)
    c_bal, f_bal = format_currency_smart(trade_balance, curr_symbol, scale_mode=num_scale)

    bal_badge = "Trade Surplus (+)" if trade_balance >= 0 else "Trade Deficit (-)"
    bal_color = COLOR_SURPLUS if trade_balance >= 0 else COLOR_DEFICIT
    bal_icon = "📈" if trade_balance >= 0 else "📉"

    sector_badge_suffix = f" ({selected_sector_name.split()[0]})" if selected_sector_chapters is not None else ""

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        render_kpi_card("Total Trade Volume", c_tot, f_tot, f"Exports + Imports{sector_badge_suffix}", COLOR_TRADE_VOL, "🌐", delta_trade_str, delta_trade_pos)
    with kpi2:
        render_kpi_card("Total Exports", c_exp, f_exp, f"{exp_share:.1f}% of Trade", COLOR_EXPORT, "🚢", delta_exp_str, delta_exp_pos)
    with kpi3:
        render_kpi_card("Total Imports", c_imp, f_imp, f"{imp_share:.1f}% of Trade", COLOR_IMPORT, "📥", delta_imp_str, delta_imp_pos)
    with kpi4:
        render_kpi_card("Net Trade Balance", c_bal, f_bal, bal_badge, bal_color, bal_icon, delta_bal_str, delta_bal_pos)

    st.markdown("---")

    sector_title_suffix = f" — {selected_sector_name}" if selected_sector_chapters is not None else ""
    if tab1_canvas_mode == "🎛️ PowerBI Unified Canvas (One Page)":
        render_powerbi_macro_canvas(
            f_tab1_macro=f_tab1_macro,
            f_tab1_country=f_tab1_country,
            df_transport=df_transport,
            df_hs=df_hs,
            t_start=t_start,
            t_end=t_end,
            is_yearly_view=is_yearly_view,
            min_dw_date=min_dw_date,
            max_dw_date=max_dw_date,
            period_info=period_info,
            sector_title_suffix=sector_title_suffix,
            selected_sector_chapters=selected_sector_chapters,
            val_col=val_col,
            currency=currency,
            curr_symbol=curr_symbol,
            num_scale=num_scale,
            bal_color=bal_color,
        )
    else:

        if is_yearly_view:
            # Yearly Aggregated View
            yearly_temp = f_tab1_macro.copy()
            yearly_temp["year"] = yearly_temp["date"].dt.year
            yearly_trade = yearly_temp.groupby(["year", "trade_type"])[val_col].sum().reset_index()
            yearly_piv = yearly_trade.pivot(index="year", columns="trade_type", values=val_col).fillna(0)
            yearly_piv["Trade Balance"] = yearly_piv.get("Export", 0) - yearly_piv.get("Import", 0)
            yearly_piv["Total Trade"] = yearly_piv.get("Export", 0) + yearly_piv.get("Import", 0)

            fig_macro = go.Figure()
            if "Export" in yearly_piv:
                fig_macro.add_trace(go.Bar(x=yearly_piv.index, y=yearly_piv["Export"], name="Annual Exports", marker_color=COLOR_EXPORT))
            if "Import" in yearly_piv:
                fig_macro.add_trace(go.Bar(x=yearly_piv.index, y=yearly_piv["Import"], name="Annual Imports", marker_color=COLOR_IMPORT))
            if "Trade Balance" in yearly_piv:
                fig_macro.add_trace(go.Scatter(x=yearly_piv.index, y=yearly_piv["Trade Balance"], name="Annual Net Trade Balance", line=dict(color=bal_color, width=3.5), mode="lines+markers", marker=dict(size=8)))

            fig_macro.update_layout(
                title=f"📊 Annual Trade Performance by Calendar Year{sector_title_suffix} ({min_dw_date.year} – {max_dw_date.year})",
                barmode="group",
                xaxis=dict(title="Calendar Year", tickmode="linear", dtick=1),
                yaxis_title=f"Value ({currency})",
                hovermode="x unified",
                height=480,
                margin=dict(l=0, r=0, t=40, b=10),
            )
            st.plotly_chart(fig_macro, use_container_width=True)
        else:
            # Monthly Granular View
            monthly_trade = f_tab1_macro.groupby(["date", "trade_type"])[val_col].sum().reset_index()
            monthly_piv = monthly_trade.pivot(index="date", columns="trade_type", values=val_col).fillna(0)
            if "Export" in monthly_piv and "Import" in monthly_piv:
                monthly_piv["Trade Balance"] = monthly_piv["Export"] - monthly_piv["Import"]

            fig_macro = go.Figure()
            if "Export" in monthly_piv:
                fig_macro.add_trace(go.Bar(x=monthly_piv.index, y=monthly_piv["Export"], name="Exports", marker_color=COLOR_EXPORT))
            if "Import" in monthly_piv:
                fig_macro.add_trace(go.Bar(x=monthly_piv.index, y=monthly_piv["Import"], name="Imports", marker_color=COLOR_IMPORT))
            if "Trade Balance" in monthly_piv:
                fig_macro.add_trace(go.Scatter(x=monthly_piv.index, y=monthly_piv["Trade Balance"], name="Net Trade Balance", line=dict(color=bal_color, width=3), mode="lines+markers", marker=dict(size=6)))

            fig_macro.update_layout(
                title=f"Monthly Trade Dynamics{sector_title_suffix} ({t_start.strftime('%b %Y')} to {t_end.strftime('%b %Y')})",
                barmode="group",
                xaxis_title="Period",
                yaxis_title=f"Value ({currency})",
                hovermode="x unified",
                height=480,
                margin=dict(l=0, r=0, t=40, b=10),
            )
            st.plotly_chart(fig_macro, use_container_width=True)

        # =========================================================================
        # 🚢 FREIGHT LOGISTICS BY TRANSPORT MODE (CARGO WEIGHT IN METRIC TONS)
        # =========================================================================
        st.markdown("---")
        st.markdown("### 🚢 Transport Mode Cargo Weight")
        st.caption("Cargo tonnage distribution by transport mode.")

        # Filter data for selected regime
        flow_option = st.radio(
            "Select Flow Direction:",
            options=["🟢 Export", "🟡 Import"],
            horizontal=True,
            key="tm_flow_filter",
        )

        selected_regime = "Export" if "Export" in flow_option else "Import"
        f_tab1_transport = df_transport[df_transport["regime"] == selected_regime].copy()

        # 4 Primary High-Weight Transport Modes (Inland Waterways, Sea, Road, Air)
        PRIMARY_TRANSPORT_MODES = [
            "Inland waterways transport",
            "Sea transport",
            "Road transport",
            "Air transport",
        ]
        f_tab1_transport_clean = f_tab1_transport[
            (f_tab1_transport["description"].isin(PRIMARY_TRANSPORT_MODES)) & (f_tab1_transport["net_weight_ton"] > 0)
        ].copy()

        if not f_tab1_transport_clean.empty:
            # Aggregate total weight by transport mode sorted descending
            modal_agg = f_tab1_transport_clean.groupby("description")["net_weight_ton"].sum().reset_index()
            modal_agg = modal_agg[modal_agg["net_weight_ton"] > 0]
            modal_agg = modal_agg.sort_values(by="net_weight_ton", ascending=False)

            modal_agg["label"] = modal_agg["description"].apply(lambda d: get_transport_mode_meta(d)[0])
            modal_agg["icon"] = modal_agg["description"].apply(lambda d: get_transport_mode_meta(d)[1])
            modal_agg["color"] = modal_agg["description"].apply(lambda d: get_transport_mode_meta(d)[2])
            modal_agg["short"] = modal_agg["description"].apply(lambda d: get_transport_mode_meta(d)[3])

            total_modal_weight = modal_agg["net_weight_ton"].sum()
            modal_agg["share_pct"] = (modal_agg["net_weight_ton"] / total_modal_weight) * 100 if total_modal_weight > 0 else 0
            modal_agg["text_display"] = modal_agg.apply(
                lambda r: f"<b>{r['net_weight_ton']/1e6:,.2f}M MT</b><br>({r['share_pct']:.1f}%)" if r["net_weight_ton"] >= 1e6
                else f"<b>{r['net_weight_ton']/1e3:,.1f}K MT</b><br>({r['share_pct']:.1f}%)" if r["net_weight_ton"] >= 1e3
                else f"<b>{r['net_weight_ton']:,.0f} MT</b><br>({r['share_pct']:.1f}%)",
                axis=1
            )

            # Total Weight KPI Card
            total_compact = f"{total_modal_weight/1e6:,.2f}M MT" if total_modal_weight >= 1e6 else f"{total_modal_weight/1e3:,.1f}K MT" if total_modal_weight >= 1e3 else f"{total_modal_weight:,.0f} MT"
            total_full = f"{total_modal_weight:,.2f} Metric Tons"
            accent_color = COLOR_EXPORT if selected_regime == "Export" else COLOR_IMPORT
            top_mode = modal_agg.iloc[0]

            card_col1, card_col2 = st.columns([1.2, 1.2])
            with card_col1:
                render_kpi_card(
                    title=f"Total {selected_regime} Cargo Weight",
                    compact_val=total_compact,
                    full_val=total_full,
                    badge_text=f"Total {selected_regime} Tonnage",
                    accent_color=accent_color,
                    icon="⚖️",
                )
            with card_col2:
                top_compact = f"{top_mode['net_weight_ton']/1e6:,.2f}M MT" if top_mode['net_weight_ton'] >= 1e6 else f"{top_mode['net_weight_ton']/1e3:,.1f}K MT" if top_mode['net_weight_ton'] >= 1e3 else f"{top_mode['net_weight_ton']:,.0f} MT"
                render_kpi_card(
                    title=f"Top Mode: {top_mode['short']}",
                    compact_val=top_compact,
                    full_val=f"{top_mode['net_weight_ton']:,.2f} Metric Tons",
                    badge_text=f"{top_mode['share_pct']:.1f}% Share",
                    accent_color=top_mode["color"],
                    icon=top_mode["icon"],
                )

            fig_tm = go.Figure()
            fig_tm.add_trace(go.Bar(
                x=modal_agg["icon"],
                y=modal_agg["net_weight_ton"],
                marker=dict(
                    color=modal_agg["color"],
                    line=dict(color="rgba(255, 255, 255, 0.2)", width=1.5),
                    cornerradius=8,
                ),
                text=modal_agg["text_display"],
                textposition="outside",
                customdata=list(zip(modal_agg["label"], modal_agg["share_pct"], modal_agg["short"])),
                hovertemplate="<b>%{customdata[0]}</b><br>● Cargo Weight: <b>%{y:,.1f} Metric Tons</b><br>● Share: <b>%{customdata[1]:.1f}%</b><extra></extra>",
            ))

            max_y = modal_agg["net_weight_ton"].max() * 1.22 if not modal_agg.empty else 100

            fig_tm.update_layout(
                title=f"Transport Mode — {selected_regime} Cargo Weight",
                xaxis=dict(
                    tickfont=dict(size=36),
                    showgrid=False,
                    title="",
                ),
                yaxis=dict(
                    title="Cargo Weight (Metric Tons)",
                    range=[0, max_y],
                    showgrid=True,
                    gridcolor="rgba(128,128,128,0.15)",
                ),
                hovermode="closest",
                height=430,
                margin=dict(l=20, r=20, t=50, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
            )

            st.plotly_chart(fig_tm, use_container_width=True)
        else:
            st.info("No modal cargo weight records available for this selected date range and flow filter.")

        # =========================================================================
        # 🌐 GLOBAL BILATERAL TRADE FLOW MAP (CAMBODIA ➔ WORLD HUB)
        # =========================================================================
        st.markdown("---")
        st.markdown(f"### 🌐 Global Trade Flow Corridors ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')})")
        st.caption(f"Geodesic Great-Circle trade routes linking the Cambodia hub (Phnom Penh) to bilateral trading partners dynamically filtered for **{period_info}**.")

        if selected_sector_name != "📦 All Commodity Sectors":
            st.info(f"💡 **Pillar Sector Filter Active ({selected_sector_name}):** Global bilateral routes below reflect total merchandise trade with trading partners during the active horizon. Detailed HS chapter breakdowns ({', '.join(selected_sector_chapters)}) are available in Tab 4 (Commodity Sectors) and Tab 5 (Predictive Forecasting).")

        map_ctrl1, map_ctrl2 = st.columns(2)
        with map_ctrl1:
            flow_mode = st.selectbox(
                "Trade Flow Corridor",
                [
                    "🟢 Outbound Export Corridors (Cambodia ➔ World)",
                    "🟡 Inbound Import Supply Chains (World ➔ Cambodia)",
                    "🔄 Combined Bilateral Flows",
                ],
                index=0,
                key="tab1_flow_mode",
            )
        with map_ctrl2:
            proj_mode = st.selectbox(
                "Map Projection View",
                [
                    "🌍 3D Interactive Globe (Orthographic)",
                    "🗺️ 2D Flat World Map (Natural Earth)",
                    "🌐 Equirectangular (Cylindrical)",
                ],
                index=0,
                key="tab1_proj_mode",
            )
        map_top_n = 10

        # Determine flow data
        if "Export" in flow_mode:
            flow_types = ["Export"]
        elif "Import" in flow_mode:
            flow_types = ["Import"]
        else:
            flow_types = ["Export", "Import"]

        f_map_country = f_tab1_country[f_tab1_country["trade_type"].isin(flow_types)]
        map_agg = f_map_country.groupby(["country_name_en", "country_code3", "trade_type"])[val_col].sum().reset_index()
        partner_totals = map_agg.groupby("country_name_en")[val_col].sum().nlargest(map_top_n)
        top_partner_names = partner_totals.index.tolist()
        total_flow_val = map_agg[val_col].sum() if not map_agg.empty else 1.0

        proj_type_map = {
            "🌍 3D Interactive Globe (Orthographic)": "orthographic",
            "🗺️ 2D Flat World Map (Natural Earth)": "natural earth",
            "🌐 Equirectangular (Cylindrical)": "equirectangular",
        }
        proj_type = proj_type_map.get(proj_mode, "orthographic")

        fig_flow = go.Figure()

        partner_lats = []
        partner_lons = []
        partner_texts = []
        partner_sizes = []
        partner_colors = []
        partner_names_plotted = []

        max_val_top = partner_totals.max() if not partner_totals.empty else 1.0

        for p_name in top_partner_names:
            p_data = map_agg[map_agg["country_name_en"] == p_name]
            p_code = p_data["country_code3"].iloc[0] if not p_data.empty and "country_code3" in p_data else None
            geo = lookup_country_geo(p_name, p_code)
            if not geo:
                continue
            p_lat, p_lon, canonical_name = geo

            p_tot = partner_totals[p_name]
            pct_share = (p_tot / total_flow_val) * 100 if total_flow_val > 0 else 0
            p_compact, p_full = format_currency_smart(p_tot, curr_symbol, num_scale)

            p_exp = p_data[p_data["trade_type"] == "Export"][val_col].sum() if "Export" in p_data["trade_type"].values else 0
            p_imp = p_data[p_data["trade_type"] == "Import"][val_col].sum() if "Import" in p_data["trade_type"].values else 0

            if p_exp > p_imp:
                line_color = COLOR_EXPORT
                flow_direction_label = "Cambodia ➔ " + canonical_name
            else:
                line_color = COLOR_IMPORT
                flow_direction_label = canonical_name + " ➔ Cambodia"

            line_width = max(1.5, min(6.5, (p_tot / max_val_top) * 6.5))

            hover_info = (
                f"<b>{canonical_name}</b> ({flow_direction_label})<br>"
                f"● Period: <b>{t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')}</b><br>"
                f"● Total Volume: <b>{p_compact}</b> ({p_full})<br>"
                f"● Active Share: <b>{pct_share:.2f}%</b><br>"
                f"● Exports: <b>{format_currency_smart(p_exp, curr_symbol, num_scale)[0]}</b> | Imports: <b>{format_currency_smart(p_imp, curr_symbol, num_scale)[0]}</b>"
            )

            fig_flow.add_trace(
                go.Scattergeo(
                    locationmode="country names",
                    lon=[CAMBODIA_GEO["lon"], p_lon],
                    lat=[CAMBODIA_GEO["lat"], p_lat],
                    mode="lines",
                    line=dict(width=line_width, color=line_color),
                    opacity=0.75,
                    hoverinfo="text",
                    text=hover_info,
                    name=canonical_name,
                    showlegend=False,
                )
            )

            partner_lons.append(p_lon)
            partner_lats.append(p_lat)
            partner_names_plotted.append(canonical_name)
            partner_sizes.append(max(8, min(24, (p_tot / max_val_top) * 24)))
            partner_colors.append(line_color)
            partner_texts.append(hover_info)

        if partner_lats:
            fig_flow.add_trace(
                go.Scattergeo(
                    lon=partner_lons,
                    lat=partner_lats,
                    mode="markers+text",
                    marker=dict(
                        size=partner_sizes,
                        color=partner_colors,
                        symbol="circle",
                        opacity=0.9,
                        line=dict(width=1.5, color="#ffffff"),
                    ),
                    text=partner_names_plotted,
                    textposition="top center",
                    textfont=dict(size=10, color="#0f172a", family="sans-serif"),
                    hoverinfo="text",
                    hovertext=partner_texts,
                    name="Trading Partners",
                    showlegend=False,
                )
            )

        cambodia_tot_exp = f_tab1_macro[f_tab1_macro["trade_type"] == "Export"][val_col].sum()
        cambodia_tot_imp = f_tab1_macro[f_tab1_macro["trade_type"] == "Import"][val_col].sum()
        kh_exp_fmt = format_currency_smart(cambodia_tot_exp, curr_symbol, num_scale)[0]
        kh_imp_fmt = format_currency_smart(cambodia_tot_imp, curr_symbol, num_scale)[0]

        kh_hover = (
            f"<b>🇰🇭 Cambodia (National Hub)</b><br>"
            f"Phnom Penh (12.57°N, 104.99°E)<br>"
            f"● Period: <b>{t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')}</b><br>"
            f"● Total Exports: <b>{kh_exp_fmt}</b><br>"
            f"● Total Imports: <b>{kh_imp_fmt}</b>"
        )

        fig_flow.add_trace(
            go.Scattergeo(
                lon=[CAMBODIA_GEO["lon"]],
                lat=[CAMBODIA_GEO["lat"]],
                mode="markers+text",
                marker=dict(
                    size=16,
                    color="#ef4444",
                    symbol="star",
                    line=dict(width=2, color="#b91c1c"),
                ),
                text=["🇰🇭 Cambodia Hub"],
                textposition="bottom center",
                textfont=dict(size=12, color="#b91c1c", family="sans-serif"),
                hoverinfo="text",
                hovertext=kh_hover,
                name="Cambodia Hub",
                showlegend=False,
            )
        )

        geo_dict = dict(
            showland=True,
            landcolor="#f8fafc",
            showocean=True,
            oceancolor="#e0f2fe",
            showlakes=True,
            lakecolor="#e0f2fe",
            showcountries=True,
            countrycolor="#cbd5e1",
            showcoastlines=True,
            coastlinecolor="#94a3b8",
            projection_type=proj_type,
            bgcolor="rgba(0,0,0,0)",
        )

        if proj_type == "orthographic":
            geo_dict["projection_rotation"] = dict(lon=105, lat=15, roll=0)
        else:
            geo_dict["center"] = dict(lat=15, lon=105)
            geo_dict["projection_scale"] = 1.35

        fig_flow.update_layout(
            title=f"🌐 Bilateral Trade Corridors — Top {len(partner_lats)} Active Partners ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')})",
            geo=geo_dict,
            margin=dict(l=0, r=0, t=40, b=0),
            height=620,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        # Side-by-side layout: Map on Left (68%), Top Country Ranking Chart on Right (32%)
        col_map, col_top_countries = st.columns([2.1, 1.0])

        with col_map:
            st.plotly_chart(fig_flow, use_container_width=True)
            st.markdown(
                f"""
                <div style="display: flex; gap: 20px; font-size: 0.8rem; margin-top: -10px; margin-bottom: 10px; opacity: 0.85;">
                    <div><span style="color: {COLOR_EXPORT}; font-weight: bold;">■</span> Outbound Export Corridors (Cambodia ➔ Market)</div>
                    <div><span style="color: {COLOR_IMPORT}; font-weight: bold;">■</span> Inbound Import Supply Chains (Market ➔ Cambodia)</div>
                    <div><span style="color: #ef4444; font-weight: bold;">★</span> Central Hub: Phnom Penh, Cambodia</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_top_countries:
            st.markdown(f"#### 🏆 Top {len(top_partner_names)} Market Ranking")
            st.caption(f"Volume & dominant flow ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')}).")

            # Full-height horizontal comparative bar chart on the right
            df_mini = pd.DataFrame({
                "Country": top_partner_names[::-1],
                "Value": [partner_totals[c] for c in top_partner_names][::-1],
                "Color": [
                    COLOR_EXPORT if map_agg[(map_agg["country_name_en"] == c) & (map_agg["trade_type"] == "Export")][val_col].sum() >= map_agg[(map_agg["country_name_en"] == c) & (map_agg["trade_type"] == "Import")][val_col].sum() else COLOR_IMPORT
                    for c in top_partner_names
                ][::-1]
            })
            fig_mini = go.Figure(go.Bar(
                x=df_mini["Value"],
                y=df_mini["Country"],
                orientation="h",
                marker_color=df_mini["Color"],
                text=[format_currency_smart(v, curr_symbol, num_scale)[0] for v in df_mini["Value"]],
                textposition="auto",
            ))
            fig_mini.update_layout(
                margin=dict(l=0, r=0, t=10, b=10),
                height=580,
                xaxis=dict(showticklabels=False, showgrid=False),
                yaxis=dict(showgrid=False),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_mini, use_container_width=True)

        # =========================================================================
        # 📋 TOP PARTNER TRADE BREAKDOWN TABLE (BELOW THE MAP)
        # =========================================================================
        leaderboard_data = []
        for rank, p_name in enumerate(top_partner_names, 1):
            p_data = map_agg[map_agg["country_name_en"] == p_name]
            p_tot = partner_totals[p_name]
            pct_share = (p_tot / total_flow_val) * 100 if total_flow_val > 0 else 0
            p_exp = float(p_data[p_data["trade_type"] == "Export"][val_col].sum()) if "Export" in p_data["trade_type"].values else 0.0
            p_imp = float(p_data[p_data["trade_type"] == "Import"][val_col].sum()) if "Import" in p_data["trade_type"].values else 0.0
            p_bal = p_exp - p_imp

            c_exp_str, _ = format_currency_smart(p_exp, curr_symbol, num_scale)
            c_imp_str, _ = format_currency_smart(p_imp, curr_symbol, num_scale)
            c_tot_str, _ = format_currency_smart(p_tot, curr_symbol, num_scale)
            c_bal_str, _ = format_currency_smart(abs(p_bal), curr_symbol, num_scale)
            bal_display = f"{'+' if p_bal >= 0 else '-'}{c_bal_str}"
            flow_tag = "🟢 Outbound Export" if p_exp >= p_imp else "🟡 Inbound Import"

            leaderboard_data.append({
                "Rank": f"#{rank}",
                "Partner Country": p_name,
                f"Total Trade ({currency})": c_tot_str,
                f"Exports ({currency})": c_exp_str,
                f"Imports ({currency})": c_imp_str,
                f"Net Balance ({currency})": bal_display,
                "Global Share": f"{pct_share:.2f}%",
                "Dominant Flow": flow_tag,
            })
        df_leaderboard = pd.DataFrame(leaderboard_data)

        with st.expander(f"📋 Click to View Top Trading Partners Detailed Breakdown Table ({len(df_leaderboard)} Countries)", expanded=False):
            st.caption(f"Comprehensive bilateral statistics for the top {len(top_partner_names)} active partner nations during **{period_info}**.")
            st.dataframe(
                df_leaderboard,
                use_container_width=True,
                hide_index=True,
                height=min(450, 45 + len(df_leaderboard) * 35),
            )

        # =========================================================================
        # 📦 TOP EXPORTED & IMPORTED PRODUCTS & COMMODITIES (HS CHAPTERS)
        # =========================================================================
        st.markdown("---")
        st.markdown(f"### 📦 Strategic Goods & Products Trade ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')})")
        st.caption(f"Top exported commodities and imported supply chain categories ranked by trade value for **{period_info}**.")

        # Slice HS data to active time horizon
        f_tab1_hs = df_hs[(df_hs["date"] >= t_start) & (df_hs["date"] <= t_end)]
        if selected_sector_chapters is not None:
            f_tab1_hs = f_tab1_hs[f_tab1_hs["hs_chapter"].astype(str).str.zfill(2).isin(selected_sector_chapters)]

        prod_top_n = st.slider("Top Product Chapters to Display", min_value=5, max_value=20, value=10, key="tab1_prod_top_n")

        hs_exp = f_tab1_hs[f_tab1_hs["trade_type"] == "Export"].groupby(["hs_chapter", "description_en"])[val_col].sum().reset_index()
        hs_imp = f_tab1_hs[f_tab1_hs["trade_type"] == "Import"].groupby(["hs_chapter", "description_en"])[val_col].sum().reset_index()

        hs_exp_top = hs_exp.nlargest(prod_top_n, val_col).copy()
        hs_imp_top = hs_imp.nlargest(prod_top_n, val_col).copy()

        hs_exp_top["label"] = "Ch." + hs_exp_top["hs_chapter"] + " - " + hs_exp_top["description_en"].str[:30]
        hs_imp_top["label"] = "Ch." + hs_imp_top["hs_chapter"] + " - " + hs_imp_top["description_en"].str[:30]

        prod_col1, prod_col2 = st.columns(2)

        with prod_col1:
            st.markdown(f"#### 🚢 Top {len(hs_exp_top)} Exported Commodities (Outbound)")
            fig_prod_exp = px.bar(
                hs_exp_top,
                x=val_col,
                y="label",
                orientation="h",
                color_discrete_sequence=[COLOR_EXPORT],
                labels={val_col: currency, "label": "Product / HS Chapter"},
            )
            fig_prod_exp.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=0, r=0, t=10, b=10),
                height=380,
                xaxis_title=currency,
                yaxis_title="Commodity Category",
            )
            st.plotly_chart(fig_prod_exp, use_container_width=True)

        with prod_col2:
            st.markdown(f"#### 📥 Top {len(hs_imp_top)} Imported Commodities (Inbound)")
            fig_prod_imp = px.bar(
                hs_imp_top,
                x=val_col,
                y="label",
                orientation="h",
                color_discrete_sequence=[COLOR_IMPORT],
                labels={val_col: currency, "label": "Product / HS Chapter"},
            )
            fig_prod_imp.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=0, r=0, t=10, b=10),
                height=380,
                xaxis_title=currency,
                yaxis_title="Commodity Category",
            )
            st.plotly_chart(fig_prod_imp, use_container_width=True)

        # Detailed Combined Product Table
        prod_table_rows = []
        tot_exp_val = f_tab1_hs[f_tab1_hs["trade_type"] == "Export"][val_col].sum()
        tot_imp_val = f_tab1_hs[f_tab1_hs["trade_type"] == "Import"][val_col].sum()

        for r_idx, (_, row) in enumerate(hs_exp_top.iterrows(), 1):
            v = row[val_col]
            fmt_v, _ = format_currency_smart(v, curr_symbol, num_scale)
            pct = (v / tot_exp_val * 100) if tot_exp_val > 0 else 0
            prod_table_rows.append({
                "Rank": f"#{r_idx}",
                "HS Chapter": f"Chapter {row['hs_chapter']}",
                "Commodity / Good Description": row["description_en"],
                "Flow Direction": "🟢 Export (Outbound)",
                f"Trade Value ({currency})": fmt_v,
                "Category Share": f"{pct:.2f}% of Exports",
            })

        for r_idx, (_, row) in enumerate(hs_imp_top.iterrows(), 1):
            v = row[val_col]
            fmt_v, _ = format_currency_smart(v, curr_symbol, num_scale)
            pct = (v / tot_imp_val * 100) if tot_imp_val > 0 else 0
            prod_table_rows.append({
                "Rank": f"#{r_idx}",
                "HS Chapter": f"Chapter {row['hs_chapter']}",
                "Commodity / Good Description": row["description_en"],
                "Flow Direction": "🟡 Import (Inbound)",
                f"Trade Value ({currency})": fmt_v,
                "Category Share": f"{pct:.2f}% of Imports",
            })

        df_prod_table = pd.DataFrame(prod_table_rows)

        with st.expander(f"📋 Click to View Top Traded Goods & Commodities Breakdown Table ({len(df_prod_table)} Categories)", expanded=False):
            st.caption(f"Detailed commodity and chapter-level statistics for **{period_info}**.")
            st.dataframe(
                df_prod_table,
                use_container_width=True,
                hide_index=True,
                height=min(450, 45 + len(df_prod_table) * 35),
            )

with tab2:
    st.subheader("🚢 Freight Logistics & Modal Share (Port Authority & Forwarders)")
    mode_metric = st.radio("Logistics Metric", ["Net Weight (Metric Tons)", f"Trade Value ({currency})"], horizontal=True, key="tab2_modal_metric_choice")
    metric_col = "net_weight_ton" if "Weight" in mode_metric else val_col

    # Clean dataset with mapped icon labels
    f_transport_tab2 = f_transport.copy()
    known_modes = list(TRANSPORT_MODE_MAPPINGS.keys())
    f_transport_tab2 = f_transport_tab2[
        f_transport_tab2["description"].isin(known_modes) | (f_transport_tab2["net_weight_ton"] > 0)
    ].copy()
    f_transport_tab2["mode_label"] = f_transport_tab2["description"].apply(lambda d: get_transport_mode_meta(d)[0])
    f_transport_tab2["mode_color"] = f_transport_tab2["description"].apply(lambda d: get_transport_mode_meta(d)[2])

    color_map = {row["mode_label"]: row["mode_color"] for _, row in f_transport_tab2.drop_duplicates(subset=["mode_label"]).iterrows()}

    t_col1, t_col2 = st.columns([1.75, 1.25])
    with t_col1:
        fig_modes = px.line(
            f_transport_tab2,
            x="date",
            y=metric_col,
            color="mode_label",
            facet_row="regime",
            title=f"📈 Freight Dynamics by Transport Mode ({mode_metric})",
            labels={metric_col: mode_metric, "mode_label": "Transport Mode"},
            color_discrete_map=color_map,
        )
        fig_modes.update_layout(height=500, hovermode="x unified")
        st.plotly_chart(fig_modes, use_container_width=True)

    with t_col2:
        st.markdown("#### Modal Share Breakdown")
        share_df = f_transport_tab2.groupby(["mode_label", "description"])[metric_col].sum().reset_index()
        share_df["color"] = share_df["description"].apply(lambda d: get_transport_mode_meta(d)[2])
        fig_pie = px.pie(
            share_df,
            names="mode_label",
            values=metric_col,
            hole=0.45,
            title=f"Total Modal Distribution ({mode_metric})",
            color="mode_label",
            color_discrete_map={row["mode_label"]: row["color"] for _, row in share_df.iterrows()},
        )
        fig_pie.update_layout(height=500, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### 🚢 Port Throughput & Maritime Focus (PAS & PPAP Sea/River Hubs)")
    sea_df = f_transport_tab2[f_transport_tab2["description"].str.contains("Sea|Marine|Port|waterway", case=False, na=False)]
    if not sea_df.empty:
        sea_piv = sea_df.pivot_table(index="date", columns="regime", values=metric_col, aggfunc="sum").fillna(0)
        fig_sea = px.bar(
            sea_piv.reset_index(),
            x="date",
            y=[c for c in sea_piv.columns],
            title=f"Maritime & River Cargo Volume — Imports vs Exports ({mode_metric})",
            barmode="group",
            color_discrete_map={"Export": COLOR_EXPORT, "Import": COLOR_IMPORT},
        )
        fig_sea.update_layout(height=420)
        st.plotly_chart(fig_sea, use_container_width=True)

with tab3:
    st.subheader("📦 Product & Commodity Classification (SITC & HS Chapters)")
    st.caption("Macroeconomic and customs analysis of Cambodia's trade structure, comparative advantage, and product categories.")

    # 1. 📘 Customs Classification Explanatory Guide
    with st.expander("📘 Economist's Guide: Understanding SITC vs. HS Codes vs. BEC", expanded=False):
        st.markdown(
            """
            International trade economics analyzes commodities through three complementary frameworks:
            
            | Framework | Governance | Economic Focus | How Economists Use It |
            |---|---|---|---|
            | **⚖️ Trade Balance Specialization** | Net Trade ($X - M$) | **Comparative Advantage & Vulnerability** | Identifies sectors earning foreign currency (surplus) vs. structural import dependencies (deficit) |
            | **🏭 UN BEC (Stage of Processing)** | United Nations | **Value-Chain Position** | Distinguishes primary commodities, intermediate factory inputs, capital machinery, and final consumer goods |
            | **📦 HS Chapters (2-Digit)** | World Customs Org (WCO) | **Detailed Tariff Nomenclature** | Official customs tariff lines (97 chapters) for bilateral trade agreements and duty schedules |
            | **🌐 SITC Sections (1-Digit)** | United Nations | **Broad Macroeconomic Sectors** | Standard 10-sector macroeconomic accounting for national GDP and input-output modeling |

            ---
            💡 **Cambodia's Trade Model:**
            - **Export Specialization:** Finished Consumer Goods (Garments, Footwear, Bicycles) and Agricultural Produce (Milled Rice, Raw Rubber, Bananas).
            - **Import Dependency:** Intermediate Inputs (Yarn, Knitted Fabrics, Plastics), Energy (Refined Petroleum), and Capital Equipment (Industrial Machinery, Motor Vehicles).
            """
        )

    # 2. 🏭 Strategic Industry Pillar Summary Cards
    st.markdown("#### 🏭 Cambodia Key Strategic Industry Pillars")
    
    # Calculate Pillar Aggregates from df_hs for active date range
    pillar_data = []
    for p_name, p_chaps in COMMODITY_PILLARS.items():
        if p_chaps is None:
            continue
        p_df = f_hs[f_hs["hs_chapter"].astype(str).str.zfill(2).isin(p_chaps)]
        p_exp = float(p_df[p_df["trade_type"] == "Export"][val_col].sum())
        p_imp = float(p_df[p_df["trade_type"] == "Import"][val_col].sum())
        p_tot = p_exp + p_imp
        p_bal = p_exp - p_imp
        pillar_data.append({
            "Pillar": p_name,
            "Export": p_exp,
            "Import": p_imp,
            "Total": p_tot,
            "Balance": p_bal,
        })
    
    df_pillars = pd.DataFrame(pillar_data).sort_values(by="Total", ascending=False)
    
    # Render top 4 pillars as cards
    p_cols = st.columns(min(4, len(df_pillars)))
    for idx, (p_col, (_, p_row)) in enumerate(zip(p_cols, df_pillars.iterrows())):
        p_name_clean = p_row["Pillar"].split("(")[0].strip()
        p_icon = p_row["Pillar"].split()[0] if p_row["Pillar"] else "📦"
        p_compact, p_full = format_currency_smart(p_row["Total"], curr_symbol, scale_mode=num_scale)
        p_bal_compact, _ = format_currency_smart(abs(p_row["Balance"]), curr_symbol, scale_mode=num_scale)
        bal_status = f"{'+' if p_row['Balance'] >= 0 else '-'}{p_bal_compact}"
        bal_color = COLOR_EXPORT if p_row["Balance"] >= 0 else COLOR_IMPORT
        
        with p_col:
            render_kpi_card(
                title=p_name_clean[:22],
                compact_val=p_compact,
                full_val=p_full,
                badge_text=f"Net: {bal_status}",
                accent_color=bal_color,
                icon=p_icon,
            )

    st.markdown("---")

    # 3. Four Specialized Economic Perspectives via Sub-Tabs
    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
        "⚖️ Trade Balance Specialization (Surplus vs Deficit)",
        "🏭 Stages of Processing (UN BEC)",
        "📊 Top Product Code Rankings (HS & SITC)",
        "📋 Comprehensive Product Directory",
    ])

    # =========================================================================
    # SUB-TAB 1: DIVERGING NET TRADE BALANCE (REVEALED SPECIALIZATION)
    # =========================================================================
    with sub_tab1:
        st.markdown("#### ⚖️ Revealed Net Trade Balance by Product Chapter")
        st.caption("Diverging economic balance showing net foreign currency earners (Surplus) vs. structural import dependencies (Deficit).")

        # Aggregate HS by Export vs Import
        hs_bal_exp = f_hs[f_hs["trade_type"] == "Export"].groupby(["hs_chapter", "description_en"])[val_col].sum().reset_index().rename(columns={val_col: "Export_Val"})
        hs_bal_imp = f_hs[f_hs["trade_type"] == "Import"].groupby(["hs_chapter", "description_en"])[val_col].sum().reset_index().rename(columns={val_col: "Import_Val"})
        
        hs_bal_merged = pd.merge(hs_bal_exp, hs_bal_imp, on=["hs_chapter", "description_en"], how="outer").fillna(0.0)
        hs_bal_merged["Net_Balance"] = hs_bal_merged["Export_Val"] - hs_bal_merged["Import_Val"]
        hs_bal_merged["Total_Trade"] = hs_bal_merged["Export_Val"] + hs_bal_merged["Import_Val"]
        hs_bal_merged["chapter_label"] = "Ch." + hs_bal_merged["hs_chapter"].astype(str).str.zfill(2) + " - " + hs_bal_merged["description_en"].str[:26]

        # Top 8 Surpluses & Top 8 Deficits
        top_surpluses = hs_bal_merged[hs_bal_merged["Net_Balance"] > 0].nlargest(8, "Net_Balance")
        top_deficits = hs_bal_merged[hs_bal_merged["Net_Balance"] < 0].nsmallest(8, "Net_Balance")
        diverging_df = pd.concat([top_deficits, top_surpluses]).sort_values(by="Net_Balance", ascending=True)

        diverging_df["Color"] = diverging_df["Net_Balance"].apply(lambda b: COLOR_EXPORT if b >= 0 else COLOR_IMPORT)
        diverging_df["Text_Val"] = diverging_df["Net_Balance"].apply(
            lambda b: f"{'+' if b>=0 else '-'}{format_currency_smart(abs(b), curr_symbol, scale_mode=num_scale)[0]}"
        )

        fig_diverging = go.Figure()
        fig_diverging.add_trace(go.Bar(
            y=diverging_df["chapter_label"],
            x=diverging_df["Net_Balance"],
            orientation="h",
            marker_color=diverging_df["Color"],
            text=diverging_df["Text_Val"],
            textposition="outside",
            customdata=list(zip(diverging_df["Export_Val"], diverging_df["Import_Val"], diverging_df["description_en"])),
            hovertemplate="<b>%{customdata[2]}</b><br>● Net Trade Balance: <b>%{x:,.0f} " + curr_symbol + "</b><br>● Exports: %{customdata[0]:,.0f}<br>● Imports: %{customdata[1]:,.0f}<extra></extra>",
        ))

        fig_diverging.update_layout(
            title=f"Net Trade Balance (Exports Minus Imports) by Key Product Chapter ({curr_symbol})",
            xaxis=dict(title=f"Net Balance ({currency})", zeroline=True, zerolinewidth=2, zerolinecolor="rgba(128,128,128,0.5)"),
            yaxis=dict(title=""),
            height=540,
            margin=dict(l=10, r=20, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_diverging, use_container_width=True)

        # Economic Interpretation
        tot_surplus_val = top_surpluses["Net_Balance"].sum()
        tot_deficit_val = abs(top_deficits["Net_Balance"].sum())
        c_surp_str, _ = format_currency_smart(tot_surplus_val, curr_symbol, scale_mode=num_scale)
        c_def_str, _ = format_currency_smart(tot_deficit_val, curr_symbol, scale_mode=num_scale)
        
        st.info(
            f"💡 **Economic Balance Insight:** "
            f"Cambodia generates its largest trade surpluses (**+{c_surp_str}**) in **Apparel (Ch. 61 & 62)**, **Footwear (Ch. 64)**, **Solar & Electronics (Ch. 85)**, and **Cereals (Ch. 10)**. "
            f"These earnings offset structural deficits (**-{c_def_str}**) in **Mineral Fuels (Ch. 27)**, **Vehicles (Ch. 87)**, **Knitted Fabric Inputs (Ch. 60)**, and **Industrial Machinery (Ch. 84)**."
        )

    # =========================================================================
    # SUB-TAB 2: ECONOMIC STAGES OF PROCESSING (UN BEC FRAMEWORK)
    # =========================================================================
    with sub_tab2:
        st.markdown("#### 🏭 Trade by Stage of Economic Processing (UN BEC Framework)")
        st.caption("Classifies trade into raw commodities, factory inputs, capital machinery, and finished goods to reveal value-chain positioning.")

        def classify_bec_stage(hs_ch_str: str) -> str:
            try:
                ch = int(hs_ch_str)
            except:
                return "📦 Other Commodities"
            
            if ch in [61, 62, 64, 65, 66, 42, 94, 95, 96, 91, 92, 97]:
                return "👗 Final Consumer Goods"
            elif (50 <= ch <= 60) or (28 <= ch <= 40) or (72 <= ch <= 83) or ch in [41, 43, 47, 48, 68, 69, 70]:
                return "🧵 Intermediate Factory Inputs"
            elif ch in [84, 85, 90]:
                return "⚙️ Capital Goods & Machinery"
            elif (1 <= ch <= 24) or ch in [25, 26, 27]:
                return "🌾 Primary Commodities & Energy"
            elif ch in [86, 87, 88, 89]:
                return "🚗 Transport Vehicles & Equipment"
            return "📦 Other Commodities"

        f_hs_bec = f_hs.copy()
        f_hs_bec["bec_stage"] = f_hs_bec["hs_chapter"].apply(classify_bec_stage)

        bec_agg = f_hs_bec.groupby(["bec_stage", "trade_type"])[val_col].sum().unstack(fill_value=0.0).reset_index()
        if "Export" not in bec_agg.columns: bec_agg["Export"] = 0.0
        if "Import" not in bec_agg.columns: bec_agg["Import"] = 0.0
        bec_agg["Total"] = bec_agg["Export"] + bec_agg["Import"]
        bec_agg["Balance"] = bec_agg["Export"] - bec_agg["Import"]
        bec_agg = bec_agg.sort_values(by="Total", ascending=False)

        # 4 Stage Summary Cards
        bec_cols = st.columns(min(4, len(bec_agg)))
        for idx, (b_col, (_, b_row)) in enumerate(zip(bec_cols, bec_agg.iterrows())):
            b_compact, b_full = format_currency_smart(b_row["Total"], curr_symbol, scale_mode=num_scale)
            b_bal_compact, _ = format_currency_smart(abs(b_row["Balance"]), curr_symbol, scale_mode=num_scale)
            b_bal_status = f"{'+' if b_row['Balance'] >= 0 else '-'}{b_bal_compact}"
            b_accent = COLOR_EXPORT if b_row["Balance"] >= 0 else COLOR_IMPORT
            
            with b_col:
                render_kpi_card(
                    title=b_row["bec_stage"][:22],
                    compact_val=b_compact,
                    full_val=b_full,
                    badge_text=f"Net: {b_bal_status}",
                    accent_color=b_accent,
                    icon=b_row["bec_stage"].split()[0],
                )

        # Comparative Bar Chart
        fig_bec = go.Figure()
        fig_bec.add_trace(go.Bar(
            y=bec_agg["bec_stage"],
            x=bec_agg["Export"],
            name="🟢 Outbound Exports",
            orientation="h",
            marker_color=COLOR_EXPORT,
            text=[format_currency_smart(v, curr_symbol, scale_mode=num_scale)[0] for v in bec_agg["Export"]],
            textposition="auto",
        ))
        fig_bec.add_trace(go.Bar(
            y=bec_agg["bec_stage"],
            x=bec_agg["Import"],
            name="🟡 Inbound Imports",
            orientation="h",
            marker_color=COLOR_IMPORT,
            text=[format_currency_smart(v, curr_symbol, scale_mode=num_scale)[0] for v in bec_agg["Import"]],
            textposition="auto",
        ))
        fig_bec.update_layout(
            title=f"Exports vs. Imports across Economic Stages of Processing ({curr_symbol})",
            barmode="group",
            yaxis=dict(title="", categoryorder="total ascending"),
            xaxis=dict(title=f"Trade Value ({currency})"),
            height=430,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_bec, use_container_width=True)

    # =========================================================================
    # SUB-TAB 3: TOP PRODUCT CODE RANKINGS (BAR CHARTS)
    # =========================================================================
    with sub_tab3:
        comm_ctrl1, comm_ctrl2 = st.columns([1.5, 1.0])
        with comm_ctrl1:
            comm_flow = st.radio(
                "Select Flow Direction:",
                options=["🟢 Outbound Exports", "🟡 Inbound Imports", "🔄 Combined (Total Trade)"],
                horizontal=True,
                key="tab3_comm_flow_sub3",
            )
        with comm_ctrl2:
            top_n_codes = st.slider("Top Codes to Display:", min_value=5, max_value=25, value=10, key="tab3_top_n_codes_sub3")

        if "Exports" in comm_flow:
            tab3_flow_types = ["Export"]
        elif "Imports" in comm_flow:
            tab3_flow_types = ["Import"]
        else:
            tab3_flow_types = ["Export", "Import"]

        f_tab3_hs = f_hs[f_hs["trade_type"].isin(tab3_flow_types)].copy()
        f_tab3_sitc = f_sitc[f_sitc["trade_type"].isin(tab3_flow_types)].copy()

        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.markdown(f"#### 📦 Top {top_n_codes} HS-2 Product Chapters")
            st.caption("Detailed 2-digit tariff chapters ranked by trade value.")
            hs_top = f_tab3_hs.groupby(["hs_chapter", "description_en", "trade_type"])[val_col].sum().reset_index()
            hs_top_total = hs_top.groupby("hs_chapter")[val_col].sum().nlargest(top_n_codes).index
            hs_filtered = hs_top[hs_top["hs_chapter"].isin(hs_top_total)].copy()
            hs_filtered["chapter_label"] = "Ch." + hs_filtered["hs_chapter"].astype(str).str.zfill(2) + " - " + hs_filtered["description_en"].str[:26]
            
            order_totals = hs_filtered.groupby("chapter_label")[val_col].sum().sort_values(ascending=True)
            
            fig_hs = px.bar(
                hs_filtered,
                x=val_col,
                y="chapter_label",
                color="trade_type",
                orientation="h",
                barmode="group",
                title=f"Top {top_n_codes} HS Chapters ({curr_symbol})",
                color_discrete_map={"Export": COLOR_EXPORT, "Import": COLOR_IMPORT},
                category_orders={"chapter_label": order_totals.index.tolist()},
            )
            fig_hs.update_layout(
                yaxis={"title": ""},
                xaxis={"title": f"Trade Value ({currency})"},
                height=max(480, top_n_codes * 34),
                margin=dict(l=10, r=10, t=35, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_hs, use_container_width=True)

        with s_col2:
            st.markdown("#### 🌐 SITC Broad Economic Sectors")
            st.caption("Macroeconomic classification across 1-digit UN SITC sections.")
            sitc_agg = f_tab3_sitc.groupby(["description_en", "trade_type"])[val_col].sum().reset_index()
            sitc_agg["short_name"] = sitc_agg["description_en"].apply(lambda d: d.split("(")[0].strip()[:32])
            
            sitc_order = sitc_agg.groupby("short_name")[val_col].sum().sort_values(ascending=True)
            
            fig_sitc = px.bar(
                sitc_agg,
                x=val_col,
                y="short_name",
                color="trade_type",
                orientation="h",
                barmode="group",
                title=f"SITC Sector Ranking ({curr_symbol})",
                color_discrete_map={"Export": COLOR_EXPORT, "Import": COLOR_IMPORT},
                category_orders={"short_name": sitc_order.index.tolist()},
            )
            fig_sitc.update_layout(
                yaxis={"title": ""},
                xaxis={"title": f"Trade Value ({currency})"},
                height=max(480, top_n_codes * 34),
                margin=dict(l=10, r=10, t=35, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_sitc, use_container_width=True)

    # =========================================================================
    # SUB-TAB 4: COMPREHENSIVE PRODUCT DIRECTORY TABLE
    # =========================================================================
    with sub_tab4:
        st.markdown("#### 📋 Comprehensive HS Product Directory")
        st.caption("Full directory of Harmonized System commodity chapters with bilateral flows and net balances.")
        
        hs_full_exp = f_hs[f_hs["trade_type"] == "Export"].groupby(["hs_chapter", "description_en"])[val_col].sum().reset_index().rename(columns={val_col: "Export_Val"})
        hs_full_imp = f_hs[f_hs["trade_type"] == "Import"].groupby(["hs_chapter", "description_en"])[val_col].sum().reset_index().rename(columns={val_col: "Import_Val"})
        
        hs_merged = pd.merge(hs_full_exp, hs_full_imp, on=["hs_chapter", "description_en"], how="outer").fillna(0.0)
        hs_merged["Total_Val"] = hs_merged["Export_Val"] + hs_merged["Import_Val"]
        hs_merged["Net_Balance"] = hs_merged["Export_Val"] - hs_merged["Import_Val"]
        hs_merged = hs_merged.sort_values(by="Total_Val", ascending=False)
        
        tot_all_hs = hs_merged["Total_Val"].sum() if not hs_merged.empty else 1.0
        
        table_rows = []
        for _, r in hs_merged.iterrows():
            c_exp, _ = format_currency_smart(r["Export_Val"], curr_symbol, scale_mode=num_scale)
            c_imp, _ = format_currency_smart(r["Import_Val"], curr_symbol, scale_mode=num_scale)
            c_tot, _ = format_currency_smart(r["Total_Val"], curr_symbol, scale_mode=num_scale)
            c_bal, _ = format_currency_smart(abs(r["Net_Balance"]), curr_symbol, scale_mode=num_scale)
            bal_str = f"{'+' if r['Net_Balance'] >= 0 else '-'}{c_bal}"
            share_pct = (r["Total_Val"] / tot_all_hs) * 100
            flow_badge = "🟢 Export Surplus" if r["Net_Balance"] >= 0 else "🟡 Import Deficit"
            
            table_rows.append({
                "HS Chapter": f"Ch. {str(r['hs_chapter']).zfill(2)}",
                "Product Description": r["description_en"],
                f"Total Trade ({currency})": c_tot,
                f"Exports ({currency})": c_exp,
                f"Imports ({currency})": c_imp,
                f"Net Balance ({currency})": bal_str,
                "Share (%)": f"{share_pct:.2f}%",
                "Flow Orientation": flow_badge,
            })
        
        df_product_dir = pd.DataFrame(table_rows)
        st.dataframe(
            df_product_dir,
            use_container_width=True,
            hide_index=True,
            height=480,
        )



with tab4:
    st.subheader("🔮 Macroeconomic Forecasting & Port Capacity Planning (Holt-Winters Production Engine)")
    st.caption("Production macroeconomic forecasting suite calibrated across 128 months of GDCE customs declarations (2016–2026). Exclusively powered by the Tournament Champion **Holt-Winters Triple Exponential Smoothing** model with calibrated **95% Confidence Intervals** (±1.96σ).")

    fc_col1, fc_col2, fc_col3, fc_col4 = st.columns([1.4, 1.1, 1.3, 1.2])
    with fc_col1:
        target_series = st.selectbox(
            "Forecast Target Metric",
            [
                "📈 National Merchandise Total Exports (Trade Value)",
                "📉 National Merchandise Total Imports (Trade Value)",
            ],
            index=0,
            key="tab4_target_series_select",
        )
    with fc_col2:
        forecast_horizon = st.slider(
            "Forecast Horizon (Months)",
            min_value=3,
            max_value=24,
            value=12,
            step=1,
            key="tab4_horizon_slider",
        )
    with fc_col3:
        timeline_scope = st.radio(
            "Historical Timeline Display",
            ["Recent 36-Month Zoom (Seasonal Wave Focus)", "Full 10-Year History (2016 to Present)"],
            index=0,
            horizontal=True,
            key="tab4_timeline_scope",
        )
    with fc_col4:
        apply_hampel = st.checkbox(
            "🛡️ Apply Hampel Outlier Filter",
            value=True,
            help="Replaces extreme pandemic and declaration shocks (e.g. 2020 COVID) using rolling MAD bounds.",
            key="tab4_hampel_check",
        )
        st.markdown(
            """<div style='background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 4px 8px; font-size: 0.8rem; color: #166534;'>
            🏆 <b>Production Model:</b> Holt-Winters (Additive 12M)<br>
            🎯 <b>Uncertainty Ribbon:</b> 95% CI (±1.96σ)
            </div>""",
            unsafe_allow_html=True,
        )

    # Build target dataset
    try:
        if forecast_monthly_series is None:
            st.error(f"Forecasting module could not be loaded. Details: {_forecast_import_err or 'Module not found'}")
            st.stop()

        if "Exports" in target_series:
            if selected_sector_chapters is not None:
                sub_df = df_hs[(df_hs["trade_type"] == "Export") & (df_hs["hs_chapter"].astype(str).str.zfill(2).isin(selected_sector_chapters))]
                metric_label = f"Exports — {selected_sector_name} ({currency})"
            else:
                sub_df = df_country[df_country["trade_type"] == "Export"]
                metric_label = f"National Merchandise Total Exports ({currency})"
            sub_agg = sub_df.groupby("date")[val_col].sum().reset_index().rename(columns={val_col: "value"})
            y_unit = f"{currency}"
        else:
            if selected_sector_chapters is not None:
                sub_df = df_hs[(df_hs["trade_type"] == "Import") & (df_hs["hs_chapter"].astype(str).str.zfill(2).isin(selected_sector_chapters))]
                metric_label = f"Imports — {selected_sector_name} ({currency})"
            else:
                sub_df = df_country[df_country["trade_type"] == "Import"]
                metric_label = f"National Merchandise Total Imports ({currency})"
            sub_agg = sub_df.groupby("date")[val_col].sum().reset_index().rename(columns={val_col: "value"})
            y_unit = f"{currency}"

        # Dedicated Champion Holt-Winters Execution with Calibrated 95% Confidence Interval
        hist_df, fc_df, fc_metrics = forecast_monthly_series(
            sub_agg,
            date_col="date",
            value_col="value",
            horizon=forecast_horizon,
            model_type="Holt-Winters",
            confidence_level=0.95,
            apply_outlier_treatment=apply_hampel,
        )

        # Timeline Zoom Filter if requested
        if "Recent 36-Month" in timeline_scope and len(hist_df) > 36:
            plot_hist_df = hist_df.iloc[-36:].copy()
        else:
            plot_hist_df = hist_df.copy()

        # KPI Metrics
        c_proj_tot, f_proj_tot = format_currency_smart(fc_metrics['forecast_horizon_total'], curr_symbol, num_scale)
        c_peak, f_peak = format_currency_smart(fc_metrics['peak_value'], curr_symbol, num_scale)
        proj_growth = fc_metrics['projected_growth_rate_pct']
        outliers_cnt = fc_metrics.get("outliers_detected", 0)

        m1, m2, m3 = st.columns(3)
        with m1:
            render_kpi_card(
                "Active Champion Model",
                "Holt-Winters (Additive)",
                "Triple Exp. Smoothing (12M)",
                "Tournament Champion",
                "#16a34a",
                "🏆",
            )
        with m2:
            render_kpi_card(
                f"Projected {forecast_horizon}M Total",
                c_proj_tot,
                f_proj_tot,
                f"Expected Point Sum (Peak: {fc_metrics['peak_month']})",
                "#e67e22",
                "📈",
                f"{proj_growth:+.1f}% YoY",
                proj_growth >= 0,
            )
        with m3:
            render_kpi_card(
                "Projected YoY Growth",
                f"{proj_growth:+.1f}%",
                f"Trajectory vs Prior {forecast_horizon}M",
                "Macro Growth",
                "#10b981" if proj_growth >= 0 else "#ef4444",
                "🚀",
                f"{proj_growth:+.1f}% YoY",
                proj_growth >= 0,
            )

        st.markdown("---")

        # Interactive Forecast Plotly Chart
        fig_fc = go.Figure()

        # Historical Observed Line
        fig_fc.add_trace(go.Scatter(
            x=plot_hist_df["date"],
            y=plot_hist_df["actual"],
            name="Observed Historical Actuals",
            mode="lines",
            line=dict(color="#1e3a8a", width=2.5),
            hovertemplate="<b>Date:</b> %{x|%Y-%m}<br><b>Actual:</b> %{y:$,.2f}<extra></extra>",
        ))

        # Show Hampel cleaned baseline if filter applied and outliers existed
        if apply_hampel and "cleaned" in plot_hist_df.columns:
            cleaned_differs = bool(np.any(np.abs(plot_hist_df["actual"] - plot_hist_df["cleaned"]) > 1e-4))
            if cleaned_differs:
                fig_fc.add_trace(go.Scatter(
                    x=plot_hist_df["date"],
                    y=plot_hist_df["cleaned"],
                    name="Hampel Immunized Baseline",
                    mode="lines",
                    line=dict(color="#059669", width=1.8, dash="dot"),
                    hovertemplate="<b>Date:</b> %{x|%Y-%m}<br><b>Cleaned Baseline:</b> %{y:$,.2f}<extra></extra>",
                ))

        cutoff_date = plot_hist_df["date"].max()
        last_val = plot_hist_df["actual"].iloc[-1]

        # Seamless continuity: anchor forecast line and confidence cone directly to the last observed historical actual
        fc_dates_conn = pd.concat([pd.Series([cutoff_date]), fc_df["date"]]).reset_index(drop=True)
        fc_vals_conn = pd.concat([pd.Series([last_val]), fc_df["forecast"]]).reset_index(drop=True)
        fc_upper_conn = pd.concat([pd.Series([last_val]), fc_df["upper_bound"]]).reset_index(drop=True)
        fc_lower_conn = pd.concat([pd.Series([last_val]), fc_df["lower_bound"]]).reset_index(drop=True)

        # 95% Confidence Interval Ribbon (Expanding cone starting from cutoff)
        fig_fc.add_trace(go.Scatter(
            x=fc_dates_conn,
            y=fc_upper_conn,
            name="Upper 95% Bound",
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig_fc.add_trace(go.Scatter(
            x=fc_dates_conn,
            y=fc_lower_conn,
            name="95% Confidence Interval (±1.96σ)",
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(22, 163, 74, 0.18)",
            line=dict(width=0),
            hovertemplate="<b>Date:</b> %{x|%Y-%m}<br><b>Lower 95% Bound:</b> %{y:$,.2f}<extra></extra>",
        ))

        # Holt-Winters Champion Point Forecast
        fig_fc.add_trace(go.Scatter(
            x=fc_dates_conn,
            y=fc_vals_conn,
            name="🏆 Holt-Winters Champion Forecast",
            mode="lines+markers",
            line=dict(color="#16a34a", width=3.2, dash="solid"),
            marker=dict(size=6, color="#16a34a"),
            hovertemplate="<b>Date:</b> %{x|%Y-%m}<br><b>HW Forecast:</b> %{y:$,.2f}<extra></extra>",
        ))

        # Vertical line for cutoff (decoupled from annotation to prevent Timestamp arithmetic error in Plotly)
        fig_fc.add_vline(
            x=cutoff_date,
            line_width=1.8,
            line_dash="dash",
            line_color="#dc2626",
        )
        fig_fc.add_annotation(
            x=cutoff_date,
            y=1.0,
            yref="paper",
            text="Forecast Horizon Cutoff",
            showarrow=False,
            xanchor="right",
            yanchor="top",
            font=dict(color="#dc2626", size=11),
            bgcolor="rgba(255, 255, 255, 0.85)",
            bordercolor="#dc2626",
            borderwidth=1,
            borderpad=3,
        )

        fig_fc.update_layout(
            title=f"📈 Holt-Winters Time-Series Forecast (95% CI): {metric_label} ({plot_hist_df['date'].min().strftime('%Y-%m')} to {fc_df['date'].max().strftime('%Y-%m')})",
            xaxis_title="Timeline",
            yaxis_title=y_unit,
            yaxis=dict(rangemode="normal"),
            hovermode="x unified",
            height=530,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_fc, use_container_width=True)

        # 🏆 STEP 9: MODEL TOURNAMENT LEADERBOARD EXPANDER
        with st.expander("🏆 View Empirical Model Benchmark Tournament Leaderboard", expanded=False):
            st.markdown("""
            **Empirical Holdout Tournament Validation:** A strict chronological 12-month holdout evaluation was conducted across all candidate forecasting architectures.
            The **3-Month Moving Average (MA-3)** defines the **non-negotiable Hurdle Floor**.
            **Holt-Winters Triple Exponential Smoothing** demonstrated superior accuracy across MAPE, RMSE, and MAE, qualifying it as the dedicated production engine.
            """)
            if evaluate_model_tournament is not None:
                df_leaderboard = evaluate_model_tournament(sub_agg, date_col="date", value_col="value", holdout_months=12)
                if not df_leaderboard.empty:
                    st.dataframe(df_leaderboard[["Model", "MAE ($)", "RMSE ($)", "MAPE (%)", "Status"]].style.format({
                        "MAE ($)": "${:,.0f}",
                        "RMSE ($)": "${:,.0f}",
                        "MAPE (%)": "{:.2f}%",
                    }), use_container_width=True)
                else:
                    st.info("Leaderboard requires at least 24 months of historical series data.")
            else:
                st.info("Tournament evaluation module initializing...")

        # Forecast Data Table & CSV Download Expander
        with st.expander("📋 View Monthly Forecast Data & Download Table", expanded=True):
            display_fc = fc_df.copy()
            display_fc["Period"] = display_fc["date"].dt.strftime("%Y-%m")
            display_fc["ci_margin"] = (display_fc["upper_bound"] - display_fc["lower_bound"]) / 2.0
            display_fc = display_fc[["Period", "forecast", "lower_bound", "upper_bound", "ci_margin"]].rename(columns={
                "forecast": f"Holt-Winters Expected Point Forecast ({y_unit.split()[0]})",
                "lower_bound": f"Lower 95% Confidence Bound ({y_unit.split()[0]})",
                "upper_bound": f"Upper 95% Confidence Bound ({y_unit.split()[0]})",
                "ci_margin": "Margin of Error (±95%)",
            })
            st.dataframe(display_fc.style.format({
                f"Holt-Winters Expected Point Forecast ({y_unit.split()[0]})": "{:,.2f}",
                f"Lower 95% Confidence Bound ({y_unit.split()[0]})": "{:,.2f}",
                f"Upper 95% Confidence Bound ({y_unit.split()[0]})": "{:,.2f}",
                "Margin of Error (±95%)": "±{:,.2f}",
            }), use_container_width=True)

            csv_data = display_fc.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Holt-Winters 95% CI Forecast CSV",
                data=csv_data,
                file_name=f"cambodia_holt_winters_95ci_{fc_df['date'].min().strftime('%Y%m')}_{fc_df['date'].max().strftime('%Y%m')}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Forecasting engine error: {e}")
