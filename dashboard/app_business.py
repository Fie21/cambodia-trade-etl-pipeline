"""
Streamlit Business Analytics BI Dashboard for Cambodia GDCE Trade & Transport.
Audience: Economists, Port Operators (PAS/PPAP), Policy Makers, Supply Chain Planners.
Runs on Port 8501 (http://localhost:8501)
"""
import os
import sys
from pathlib import Path
import pandas as pd
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
_forecast_import_err = None

# Method 1: Standard package import
try:
    from src.forecast import forecast_monthly_series as _fms
    forecast_monthly_series = _fms
except Exception as _e1:
    try:
        from forecast import forecast_monthly_series as _fms
        forecast_monthly_series = _fms
    except Exception as _e2:
        _forecast_import_err = f"{_e1} | {_e2}"

# Method 2: Direct file path loading via importlib (100% immune to cwd / sys.path discrepancies)
if forecast_monthly_series is None:
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
                    forecast_monthly_series = getattr(_mod, "forecast_monthly_series", None)
                    if forecast_monthly_series is not None:
                        _forecast_import_err = None
                        break
            except Exception as _load_err:
                _forecast_import_err = f"Error loading {_path}: {_load_err}"

DW_CONN_STR = os.environ.get(
    "DW_CONN_STR",
    "postgresql+psycopg2://airflow:airflow@postgres:5432/transport_dw",
)

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
        localhost_str = DW_CONN_STR.replace("@postgres:", "@localhost:")
        return create_engine(localhost_str)


@st.cache_data(ttl=300)
def load_transport_data() -> pd.DataFrame:
    engine = get_engine()
    query = """
        SELECT
            date, period, regime, description, description_kh,
            net_weight_ton, net_weight_kg, value_usd, value_khr, loaded_at
        FROM warehouse.fact_transportation_stats
        ORDER BY date ASC, regime ASC, description ASC
    """
    return pd.read_sql(query, engine, parse_dates=["date"])


@st.cache_data(ttl=300)
def load_country_data() -> pd.DataFrame:
    engine = get_engine()
    query = """
        SELECT
            date, period, year, month, country_code, country_code3,
            country_name_en, country_name_kh, country_groups,
            trade_type, regime_code, value_usd, value_khr, loaded_at
        FROM warehouse.fact_country_trade
        ORDER BY date ASC, trade_type ASC, value_usd DESC
    """
    return pd.read_sql(query, engine, parse_dates=["date"])


@st.cache_data(ttl=300)
def load_sitc_data() -> pd.DataFrame:
    engine = get_engine()
    query = """
        SELECT
            date, period, year, month, sitc_code, description_en,
            description_kh, trade_type, regime_code, value_usd, value_khr, loaded_at
        FROM warehouse.fact_trade_by_sitc
        ORDER BY date ASC, trade_type ASC, value_usd DESC
    """
    return pd.read_sql(query, engine, parse_dates=["date"])


@st.cache_data(ttl=300)
def load_hs_data() -> pd.DataFrame:
    engine = get_engine()
    query = """
        SELECT
            date, period, year, month, hs_chapter, description_en,
            description_kh, trade_type, regime_code, value_usd, value_khr, loaded_at
        FROM warehouse.fact_trade_by_hs
        ORDER BY date ASC, trade_type ASC, value_usd DESC
    """
    return pd.read_sql(query, engine, parse_dates=["date"])


# --- Main Dashboard ---
st.title("📊 Cambodia International Trade & Transport Analytics")
st.caption("Official Statistics from General Department of Customs and Excise of Cambodia (GDCE)")

try:
    df_transport = load_transport_data()
    df_country = load_country_data()
    df_sitc = load_sitc_data()
    df_hs = load_hs_data()
except Exception as e:
    st.error(f"Failed to connect to Data Warehouse: {e}")
    st.stop()

if df_transport.empty:
    st.warning("Data Warehouse is currently empty. Run the Airflow ETL pipeline first.")
    st.stop()

# ==========================================
# 🧭 SIDEBAR: ANALYTICS CONTROL HUB
# ==========================================
st.sidebar.markdown("## 🧭 Analytics Control Hub")
st.sidebar.caption("Executive Suite for Investors, Economists & Policy Makers")

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


with tab1:
    st.subheader("🏛️ National Trade Performance & Balance")

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
            height=500,
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
        )
        st.plotly_chart(fig_macro, use_container_width=True)

    # =========================================================================
    # 🌐 GLOBAL BILATERAL TRADE FLOW MAP (CAMBODIA ➔ WORLD HUB)
    # =========================================================================
    st.markdown("---")
    st.markdown(f"### 🌐 Global Trade Flow Corridors ({t_start.strftime('%b %Y')} – {t_end.strftime('%b %Y')})")
    st.caption(f"Geodesic Great-Circle trade routes linking the Cambodia hub (Phnom Penh) to bilateral trading partners dynamically filtered for **{period_info}**.")

    if selected_sector_name != "📦 All Commodity Sectors":
        st.info(f"💡 **Pillar Sector Filter Active ({selected_sector_name}):** Global bilateral routes below reflect total merchandise trade with trading partners during the active horizon. Detailed HS chapter breakdowns ({', '.join(selected_sector_chapters)}) are available in Tab 4 (Commodity Sectors) and Tab 5 (Predictive Forecasting).")

    map_ctrl1, map_ctrl2, map_ctrl3 = st.columns([1.2, 1.2, 1.0])
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
    with map_ctrl3:
        map_top_n = st.slider("Top Partners", min_value=5, max_value=30, value=15, key="tab1_map_top_n")

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
    mode_metric = st.radio("Logistics Metric", ["Net Weight (Metric Tons)", f"Trade Value ({currency})"], horizontal=True)
    metric_col = "net_weight_ton" if "Weight" in mode_metric else val_col

    t_col1, t_col2 = st.columns([2, 1])
    with t_col1:
        fig_modes = px.line(
            f_transport,
            x="date",
            y=metric_col,
            color="description",
            facet_row="regime",
            title="Freight Dynamics by Transport Mode (Import vs Export)",
            labels={metric_col: mode_metric, "description": "Transport Mode"},
        )
        fig_modes.update_layout(height=500)
        st.plotly_chart(fig_modes, use_container_width=True)

    with t_col2:
        st.markdown("#### Modal Share Breakdown")
        share_df = f_transport.groupby("description")[metric_col].sum().reset_index()
        fig_pie = px.pie(share_df, names="description", values=metric_col, hole=0.4, title="Total Transport Share")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### Port Throughput (Maritime / Sea Transport Focus)")
    sea_df = f_transport[f_transport["description"].str.contains("Sea|Marine|Port", case=False, na=False)]
    if not sea_df.empty:
        sea_piv = sea_df.pivot_table(index="date", columns="regime", values=metric_col, aggfunc="sum").fillna(0)
        fig_sea = px.bar(sea_piv.reset_index(), x="date", y=[c for c in sea_piv.columns], title="Maritime Cargo Volume (Imports vs Exports)", barmode="group")
        st.plotly_chart(fig_sea, use_container_width=True)

with tab3:
    st.subheader("📦 Product & Commodity Classification (SITC & HS Chapters)")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("#### SITC Commodity Sectors")
        sitc_agg = f_sitc.groupby(["description_en", "trade_type"])[val_col].sum().reset_index()
        fig_sitc = px.bar(sitc_agg, x=val_col, y="description_en", color="trade_type", orientation="h", barmode="group", title="Trade Value by SITC Sector", color_discrete_map={"Export": COLOR_EXPORT, "Import": COLOR_IMPORT})
        fig_sitc.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
        st.plotly_chart(fig_sitc, use_container_width=True)

    with s_col2:
        st.markdown("#### Top 10 HS-2 Product Chapters")
        hs_top = f_hs.groupby(["hs_chapter", "description_en", "trade_type"])[val_col].sum().reset_index()
        hs_top_total = hs_top.groupby("hs_chapter")[val_col].sum().nlargest(10).index
        hs_filtered = hs_top[hs_top["hs_chapter"].isin(hs_top_total)].copy()
        hs_filtered["chapter_label"] = "Ch." + hs_filtered["hs_chapter"] + " - " + hs_filtered["description_en"].str[:25]
        fig_hs = px.bar(hs_filtered, x=val_col, y="chapter_label", color="trade_type", orientation="h", barmode="group", title="Top HS Chapters", color_discrete_map={"Export": COLOR_EXPORT, "Import": COLOR_IMPORT})
        fig_hs.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
        st.plotly_chart(fig_hs, use_container_width=True)

with tab4:
    st.subheader("🔮 Predictive Time-Series Forecasting & Port Capacity Planning")
    st.caption("Econometric exponential smoothing and Holt-Winters forecasting with calibrated 95% confidence intervals.")

    fc_col1, fc_col2, fc_col3 = st.columns([1.5, 1.3, 1])
    with fc_col1:
        target_series = st.selectbox(
            "Forecast Target Metric",
            [
                "📈 National Merchandise Total Exports (Trade Value)",
                "📉 National Merchandise Total Imports (Trade Value)",
            ],
            index=0,
        )
    with fc_col2:
        model_choice = st.selectbox(
            "Forecasting Model Architecture",
            [
                "🏆 Holt-Winters (Champion - Recommended)",
                "🥈 SARIMAX (1,1,1)x(1,1,1)₁₂ (Econometric Benchmark)",
                "📊 Compare Both Models (Overlay on 1 Chart)",
            ],
            index=0,
        )
    with fc_col3:
        forecast_horizon = st.slider("Forecast Lead Time (Months)", min_value=3, max_value=24, value=12, step=1)

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

        is_compare = "Compare" in model_choice

        if is_compare:
            hist_df, fc_hw, metrics_hw = forecast_monthly_series(sub_agg, date_col="date", value_col="value", horizon=forecast_horizon, model_type="Holt-Winters")
            _, fc_sarima, metrics_sarima = forecast_monthly_series(sub_agg, date_col="date", value_col="value", horizon=forecast_horizon, model_type="SARIMAX")
            fc_df = fc_hw
            fc_metrics = metrics_hw
        elif "SARIMAX" in model_choice:
            hist_df, fc_df, fc_metrics = forecast_monthly_series(sub_agg, date_col="date", value_col="value", horizon=forecast_horizon, model_type="SARIMAX")
        else:
            hist_df, fc_df, fc_metrics = forecast_monthly_series(sub_agg, date_col="date", value_col="value", horizon=forecast_horizon, model_type="Holt-Winters")

        # KPI Metrics
        m1, m2, m3, m4 = st.columns(4)
        if is_compare:
            c_hw_tot, f_hw_tot = format_currency_smart(metrics_hw['forecast_horizon_total'], curr_symbol, num_scale)
            c_sa_tot, f_sa_tot = format_currency_smart(metrics_sarima['forecast_horizon_total'], curr_symbol, num_scale)
            hw_growth = metrics_hw['projected_growth_rate_pct']
            sa_growth = metrics_sarima['projected_growth_rate_pct']
            diff_val = metrics_hw['forecast_horizon_total'] - metrics_sarima['forecast_horizon_total']
            c_diff, f_diff = format_currency_smart(abs(diff_val), curr_symbol, num_scale)

            with m1:
                render_kpi_card("Architecture", "Overlay Mode", "HW & SARIMAX Co-Plot", "2 Models", "#8b5cf6", "📊")
            with m2:
                render_kpi_card(f"HW {forecast_horizon}M Total", c_hw_tot, f_hw_tot, "Champion Model", "#e67e22", "🏆", f"{hw_growth:+.1f}% YoY", hw_growth >= 0)
            with m3:
                render_kpi_card(f"SARIMAX {forecast_horizon}M", c_sa_tot, f_sa_tot, "Econometric Benchmark", "#8e44ad", "🥈", f"{sa_growth:+.1f}% YoY", sa_growth >= 0)
            with m4:
                render_kpi_card("Model Variance", c_diff, f_diff, "HW vs SARIMAX Spread", "#3b82f6", "⚖️")
        else:
            c_proj_tot, f_proj_tot = format_currency_smart(fc_metrics['forecast_horizon_total'], curr_symbol, num_scale)
            c_peak, f_peak = format_currency_smart(fc_metrics['peak_value'], curr_symbol, num_scale)
            proj_growth = fc_metrics['projected_growth_rate_pct']

            with m1:
                render_kpi_card("Active Model", fc_metrics["model_used"].split("(")[0].strip()[:18], fc_metrics["model_used"], "Active Engine", "#8b5cf6", "🧠")
            with m2:
                render_kpi_card(f"Projected {forecast_horizon}M Total", c_proj_tot, f_proj_tot, f"Next {forecast_horizon} Months", "#e67e22", "📈", f"{proj_growth:+.1f}% YoY Projected", proj_growth >= 0)
            with m3:
                render_kpi_card("Projected YoY Growth", f"{proj_growth:+.1f}%", f"Forecast Trajectory", "Macro Trend", "#10b981" if proj_growth >= 0 else "#ef4444", "🚀", f"{proj_growth:+.1f}% YoY", proj_growth >= 0)
            with m4:
                render_kpi_card("Projected Peak Month", str(fc_metrics['peak_month']), f"Peak Value: {f_peak}", "Peak Month", "#f59e0b", "⭐")

        st.markdown("---")

        # Interactive Forecast Plotly Chart
        fig_fc = go.Figure()

        # Historical Line
        fig_fc.add_trace(go.Scatter(
            x=hist_df["date"],
            y=hist_df["actual"],
            name="Historical Actuals",
            mode="lines",
            line=dict(color="#2980b9", width=2.5),
        ))

        if is_compare:
            # Holt-Winters Shaded Interval
            fig_fc.add_trace(go.Scatter(
                x=fc_hw["date"], y=fc_hw["upper_95"], name="HW Upper 95%", mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"
            ))
            fig_fc.add_trace(go.Scatter(
                x=fc_hw["date"], y=fc_hw["lower_95"], name="HW 95% Interval", mode="lines", fill="tonexty", fillcolor="rgba(243, 156, 18, 0.15)", line=dict(width=0)
            ))
            # Holt-Winters Line
            fig_fc.add_trace(go.Scatter(
                x=fc_hw["date"], y=fc_hw["forecast"], name="🏆 Holt-Winters Forecast", mode="lines+markers", line=dict(color="#e67e22", width=3, dash="dash"), marker=dict(size=6)
            ))
            # SARIMAX Line
            fig_fc.add_trace(go.Scatter(
                x=fc_sarima["date"], y=fc_sarima["forecast"], name="🥈 SARIMAX Forecast", mode="lines+markers", line=dict(color="#8e44ad", width=2.5, dash="dot"), marker=dict(size=6)
            ))
        else:
            # Single Selected Model Forecast
            fig_fc.add_trace(go.Scatter(
                x=fc_df["date"], y=fc_df["upper_95"], name="Upper 95% Confidence", mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"
            ))
            fig_fc.add_trace(go.Scatter(
                x=fc_df["date"], y=fc_df["lower_95"], name="95% Prediction Interval", mode="lines", fill="tonexty", fillcolor="rgba(243, 156, 18, 0.2)", line=dict(width=0)
            ))
            fig_fc.add_trace(go.Scatter(
                x=fc_df["date"], y=fc_df["forecast"], name=f"Forecast (Next {forecast_horizon}M)", mode="lines+markers", line=dict(color="#e67e22" if "Holt" in model_choice else "#8e44ad", width=3, dash="dash"), marker=dict(size=6)
            ))

        fig_fc.update_layout(
            title=f"📈 Time-Series Forecast: {metric_label} ({hist_df['date'].min().strftime('%Y-%m')} to {fc_df['date'].max().strftime('%Y-%m')})",
            xaxis_title="Month",
            yaxis_title=y_unit,
            hovermode="x unified",
            height=530,
        )
        st.plotly_chart(fig_fc, use_container_width=True)


        # Forecast Data Table
        with st.expander("📋 View Monthly Forecast Data & Download Table"):
            if is_compare:
                display_fc = pd.DataFrame({
                    "Period": fc_hw["date"].dt.strftime("%Y-%m"),
                    f"Holt-Winters ({y_unit.split()[0]})": fc_hw["forecast"],
                    f"SARIMAX ({y_unit.split()[0]})": fc_sarima["forecast"],
                    "Difference ($)": fc_hw["forecast"] - fc_sarima["forecast"],
                    "HW Lower 95%": fc_hw["lower_95"],
                    "HW Upper 95%": fc_hw["upper_95"],
                })
                st.dataframe(display_fc.style.format({
                    f"Holt-Winters ({y_unit.split()[0]})": "{:,.2f}",
                    f"SARIMAX ({y_unit.split()[0]})": "{:,.2f}",
                    "Difference ($)": "{:+,.2f}",
                    "HW Lower 95%": "{:,.2f}",
                    "HW Upper 95%": "{:,.2f}",
                }), use_container_width=True)
            else:
                display_fc = fc_df.copy()
                display_fc["Period"] = display_fc["date"].dt.strftime("%Y-%m")
                display_fc = display_fc[["Period", "forecast", "lower_95", "upper_95"]].rename(columns={
                    "forecast": f"Expected Point Forecast ({y_unit.split()[0]})",
                    "lower_95": "Lower 95% Bound",
                    "upper_95": "Upper 95% Bound",
                })
                st.dataframe(display_fc.style.format({
                    f"Expected Point Forecast ({y_unit.split()[0]})": "{:,.2f}",
                    "Lower 95% Bound": "{:,.2f}",
                    "Upper 95% Bound": "{:,.2f}",
                }), use_container_width=True)

            csv_data = display_fc.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Forecast CSV",
                data=csv_data,
                file_name=f"cambodia_gdce_forecast_{fc_df['date'].min().strftime('%Y%m')}_{fc_df['date'].max().strftime('%Y%m')}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Forecasting engine error: {e}")
