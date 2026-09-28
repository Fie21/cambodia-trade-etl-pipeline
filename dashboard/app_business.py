"""
Streamlit Business Analytics BI Dashboard for Cambodia GDCE Trade & Transport.
Audience: Economists, Port Operators (PAS/PPAP), Policy Makers, Supply Chain Planners.
Runs on Port 8501 (http://localhost:8501)
"""
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

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

# Sidebar Filters
st.sidebar.title("🔍 Analytics Filters")
min_date = df_transport["date"].min().date()
max_date = df_transport["date"].max().date()
date_selection = st.sidebar.date_input(
    "Reporting Period Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_selection, (tuple, list)) and len(date_selection) == 2:
    start_dt, end_dt = pd.Timestamp(date_selection[0]), pd.Timestamp(date_selection[1])
else:
    start_dt, end_dt = pd.Timestamp(min_date), pd.Timestamp(max_date)

currency = st.sidebar.radio("💱 Currency Unit", ["USD ($)", "KHR (៛)"], index=0)
val_col = "value_usd" if "USD" in currency else "value_khr"
curr_symbol = "$" if "USD" in currency else "៛"

f_transport = df_transport[(df_transport["date"] >= start_dt) & (df_transport["date"] <= end_dt)]
f_country = df_country[(df_country["date"] >= start_dt) & (df_country["date"] <= end_dt)]
f_sitc = df_sitc[(df_sitc["date"] >= start_dt) & (df_sitc["date"] <= end_dt)]
f_hs = df_hs[(df_hs["date"] >= start_dt) & (df_hs["date"] <= end_dt)]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏛️ Macro & Trade Balance",
    "🚢 Freight & Transport Modes",
    "🌍 Bilateral Partner Countries",
    "📦 Commodity Sectors (SITC & HS)",
    "🔮 Predictive Forecasting",
])

with tab1:
    st.subheader("🏛️ National Trade Performance & Balance")
    macro_summary = f_country.groupby("trade_type")[val_col].sum()
    total_exp = macro_summary.get("Export", 0.0)
    total_imp = macro_summary.get("Import", 0.0)
    trade_balance = total_exp - total_imp
    total_trade = total_exp + total_imp

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Trade Volume", f"{curr_symbol} {total_trade:,.0f}")
    kpi2.metric("Total Exports", f"{curr_symbol} {total_exp:,.0f}")
    kpi3.metric("Total Imports", f"{curr_symbol} {total_imp:,.0f}")
    kpi4.metric("Trade Balance", f"{curr_symbol} {trade_balance:,.0f}", delta=f"{curr_symbol} {trade_balance:,.0f}")

    st.markdown("---")
    monthly_trade = f_country.groupby(["date", "trade_type"])[val_col].sum().reset_index()
    monthly_piv = monthly_trade.pivot(index="date", columns="trade_type", values=val_col).fillna(0)
    if "Export" in monthly_piv and "Import" in monthly_piv:
        monthly_piv["Trade Balance"] = monthly_piv["Export"] - monthly_piv["Import"]

    fig_macro = go.Figure()
    if "Export" in monthly_piv:
        fig_macro.add_trace(go.Bar(x=monthly_piv.index, y=monthly_piv["Export"], name="Exports", marker_color="#2ecc71"))
    if "Import" in monthly_piv:
        fig_macro.add_trace(go.Bar(x=monthly_piv.index, y=monthly_piv["Import"], name="Imports", marker_color="#e74c3c"))
    if "Trade Balance" in monthly_piv:
        fig_macro.add_trace(go.Scatter(x=monthly_piv.index, y=monthly_piv["Trade Balance"], name="Net Trade Balance", line=dict(color="#3498db", width=3)))

    fig_macro.update_layout(title="Monthly Trade Dynamics (Exports vs. Imports & Balance)", barmode="group", xaxis_title="Period", yaxis_title=f"Value ({currency})", hovermode="x unified")
    st.plotly_chart(fig_macro, use_container_width=True)

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
    st.subheader("🌍 Bilateral Partner Country Trade Intelligence")
    top_n = st.slider("Top N Partner Countries", min_value=5, max_value=25, value=10)
    c_exp = f_country[f_country["trade_type"] == "Export"].groupby("country_name_en")[val_col].sum().nlargest(top_n).reset_index()
    c_imp = f_country[f_country["trade_type"] == "Import"].groupby("country_name_en")[val_col].sum().nlargest(top_n).reset_index()

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fig_c_exp = px.bar(c_exp, x=val_col, y="country_name_en", orientation="h", title=f"Top {top_n} Export Destination Markets", color_discrete_sequence=["#2ecc71"])
        fig_c_exp.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title=currency, yaxis_title="Country")
        st.plotly_chart(fig_c_exp, use_container_width=True)

    with col_c2:
        fig_c_imp = px.bar(c_imp, x=val_col, y="country_name_en", orientation="h", title=f"Top {top_n} Import Origin Markets", color_discrete_sequence=["#e74c3c"])
        fig_c_imp.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title=currency, yaxis_title="Country")
        st.plotly_chart(fig_c_imp, use_container_width=True)

    st.markdown("#### Bilateral Trade Matrix (Top 10 Partners)")
    top_partners = (f_country.groupby("country_name_en")[val_col].sum().nlargest(10).index)
    partner_df = f_country[f_country["country_name_en"].isin(top_partners)].pivot_table(index="country_name_en", columns="trade_type", values=val_col, aggfunc="sum").fillna(0)
    if "Export" in partner_df and "Import" in partner_df:
        partner_df["Net Trade (Deficit/Surplus)"] = partner_df["Export"] - partner_df["Import"]
        st.dataframe(partner_df.style.format("{:,.0f}"), use_container_width=True)

with tab4:
    st.subheader("📦 Product & Commodity Classification (SITC & HS Chapters)")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("#### SITC Commodity Sectors")
        sitc_agg = f_sitc.groupby(["description_en", "trade_type"])[val_col].sum().reset_index()
        fig_sitc = px.bar(sitc_agg, x=val_col, y="description_en", color="trade_type", orientation="h", barmode="group", title="Trade Value by SITC Sector")
        fig_sitc.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
        st.plotly_chart(fig_sitc, use_container_width=True)

    with s_col2:
        st.markdown("#### Top 10 HS-2 Product Chapters")
        hs_top = f_hs.groupby(["hs_chapter", "description_en", "trade_type"])[val_col].sum().reset_index()
        hs_top_total = hs_top.groupby("hs_chapter")[val_col].sum().nlargest(10).index
        hs_filtered = hs_top[hs_top["hs_chapter"].isin(hs_top_total)].copy()
        hs_filtered["chapter_label"] = "Ch." + hs_filtered["hs_chapter"] + " - " + hs_filtered["description_en"].str[:25]
        fig_hs = px.bar(hs_filtered, x=val_col, y="chapter_label", color="trade_type", orientation="h", barmode="group", title="Top HS Chapters")
        fig_hs.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
        st.plotly_chart(fig_hs, use_container_width=True)

with tab5:
    st.subheader("🔮 Predictive Time-Series Forecasting & Port Capacity Planning")
    st.caption("Econometric exponential smoothing and Holt-Winters forecasting with calibrated 95% confidence intervals.")

    fc_col1, fc_col2 = st.columns([1, 1])
    with fc_col1:
        target_series = st.selectbox(
            "Forecast Target Metric",
            [
                "🌊 Maritime Port Cargo Throughput (Sea Transport - Metric Tons)",
                "🚚 Cross-Border Road Freight Throughput (Road Transport - Metric Tons)",
                "📈 National Merchandise Total Exports",
                "📉 National Merchandise Total Imports",
            ],
            index=0,
        )
    with fc_col2:
        forecast_horizon = st.slider("Forecast Lead Time Horizon (Months)", min_value=3, max_value=24, value=12, step=1)

    # Build target dataset
    try:
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
        from forecast import forecast_monthly_series

        if "Maritime" in target_series:
            sub_df = df_transport[df_transport["description"].str.contains("Sea|Marine|Port", case=False, na=False)]
            sub_agg = sub_df.groupby("date")["net_weight_ton"].sum().reset_index().rename(columns={"net_weight_ton": "value"})
            metric_label = "Maritime Cargo (Metric Tons)"
            y_unit = "Metric Tons (t)"
        elif "Road" in target_series:
            sub_df = df_transport[df_transport["description"].str.contains("Road|Land", case=False, na=False)]
            sub_agg = sub_df.groupby("date")["net_weight_ton"].sum().reset_index().rename(columns={"net_weight_ton": "value"})
            metric_label = "Road Freight (Metric Tons)"
            y_unit = "Metric Tons (t)"
        elif "Exports" in target_series:
            sub_df = df_country[df_country["trade_type"] == "Export"]
            sub_agg = sub_df.groupby("date")[val_col].sum().reset_index().rename(columns={val_col: "value"})
            metric_label = f"Total Exports ({currency})"
            y_unit = f"{currency}"
        else:
            sub_df = df_country[df_country["trade_type"] == "Import"]
            sub_agg = sub_df.groupby("date")[val_col].sum().reset_index().rename(columns={val_col: "value"})
            metric_label = f"Total Imports ({currency})"
            y_unit = f"{currency}"

        hist_df, fc_df, fc_metrics = forecast_monthly_series(sub_agg, date_col="date", value_col="value", horizon=forecast_horizon)

        # KPI Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Selected Model", fc_metrics["model_used"].split("(")[0].strip())
        m2.metric(f"Projected {forecast_horizon}M Total", f"{fc_metrics['forecast_horizon_total']:,.0f} {y_unit.split()[0]}")
        m3.metric("Projected Growth (YoY)", f"{fc_metrics['projected_growth_rate_pct']:+.1f}%")
        m4.metric("Projected Peak Month", f"{fc_metrics['peak_month']}", f"{fc_metrics['peak_value']:,.0f}")

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

        # Upper 95% Bound
        fig_fc.add_trace(go.Scatter(
            x=fc_df["date"],
            y=fc_df["upper_95"],
            name="Upper 95% Confidence",
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Lower 95% Bound with Shading
        fig_fc.add_trace(go.Scatter(
            x=fc_df["date"],
            y=fc_df["lower_95"],
            name="95% Prediction Interval",
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(243, 156, 18, 0.2)",
            line=dict(width=0),
        ))

        # Forecast Line
        fig_fc.add_trace(go.Scatter(
            x=fc_df["date"],
            y=fc_df["forecast"],
            name=f"Forecast (Next {forecast_horizon}M)",
            mode="lines+markers",
            line=dict(color="#e67e22", width=3, dash="dash"),
            marker=dict(size=6),
        ))

        # Add Capacity Benchmark for Sea Freight (e.g. Sihanoukville Port threshold)
        if "Maritime" in target_series:
            max_hist = hist_df["actual"].max()
            cap_limit = max_hist * 1.25
            fig_fc.add_hline(
                y=cap_limit,
                line_dash="dot",
                line_color="#e74c3c",
                annotation_text=f"Estimated Port Handling Benchmark Threshold ({cap_limit:,.0f} t)",
                annotation_position="bottom right",
            )

        fig_fc.update_layout(
            title=f"📈 Time-Series Forecast: {metric_label} ({hist_df['date'].min().strftime('%Y-%m')} to {fc_df['date'].max().strftime('%Y-%m')})",
            xaxis_title="Month",
            yaxis_title=y_unit,
            hovermode="x unified",
            height=520,
        )
        st.plotly_chart(fig_fc, use_container_width=True)

        # Forecast Data Table
        with st.expander("📋 View Monthly Forecast Data & Download Table"):
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

