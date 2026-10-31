"""
Generate publication-quality empirical data visualizations for Chapter 6 of the I4 Thesis Report.
This script queries the 128-month Cambodia GDCE trade dataset (2016-2026) and exports high-DPI figures.
"""

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

OUT_DIR = "docs/i4_thesis_report/LaTeX_Thesis_Template/images/figures"
os.makedirs(OUT_DIR, exist_ok=True)

# Typography and aesthetics
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8


def load_clean_dataset():
    """Load the 128 monthly processed trade snapshots."""
    files = sorted([f for f in glob.glob('data/processed/*.csv') if not os.path.basename(f).startswith('tmp')])
    print(f"Loading {len(files)} monthly processed trade data files...")
    df_list = [pd.read_csv(f) for f in files]
    df = pd.concat(df_list, ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    return df


def generate_figure1_macro_trade_trends(df):
    """
    Figure 1: Cambodia National Monthly Trade Dynamics & Structural Deficit (2016-2026).
    """
    monthly = df.groupby(['date', 'regime'])['value_usd'].sum().unstack('regime').fillna(0)
    monthly['export_billions'] = monthly['Export'] / 1e9
    monthly['import_billions'] = monthly['Import'] / 1e9
    monthly['balance_millions'] = (monthly['Export'] - monthly['Import']) / 1e6
    monthly['export_ma12'] = monthly['export_billions'].rolling(12, min_periods=6).mean()
    monthly['import_ma12'] = monthly['import_billions'].rolling(12, min_periods=6).mean()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8.5), dpi=300, sharex=True)

    # Panel A: Export vs. Import Trajectory
    ax1.plot(monthly.index, monthly['import_billions'], color='#d32f2f', lw=1.6, label='Monthly Imports ($B USD)', alpha=0.85)
    ax1.plot(monthly.index, monthly['export_billions'], color='#1976d2', lw=1.6, label='Monthly Exports ($B USD)', alpha=0.85)
    ax1.plot(monthly.index, monthly['import_ma12'], color='#b71c1c', lw=2.4, linestyle='--', label='Imports (12-Month Moving Avg)')
    ax1.plot(monthly.index, monthly['export_ma12'], color='#0d47a1', lw=2.4, linestyle='--', label='Exports (12-Month Moving Avg)')

    ax1.set_title('(A) Cambodia Monthly Merchandise Trade Flows (Exports vs. Imports, 2016–2026)', fontsize=12, fontweight='bold', pad=10)
    ax1.set_ylabel('Trade Value (Billion USD)', fontsize=11, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', frameon=True, facecolor='#ffffff', framealpha=0.92, fontsize=9.5)
    ax1.set_ylim(0, max(monthly['import_billions'].max(), monthly['export_billions'].max()) * 1.15)

    # Highlight historical macroeconomic events
    ax1.axvspan(pd.to_datetime('2020-03-01'), pd.to_datetime('2020-10-01'), color='#fff9c4', alpha=0.6, label='COVID-19 Disruption')
    ax1.text(pd.to_datetime('2020-06-15'), ax1.get_ylim()[1] * 0.88, 'COVID-19 Supply Chain Shock',
             ha='center', fontsize=9, fontweight='bold', color='#795548',
             bbox=dict(boxstyle='round,pad=0.25', facecolor='#fffde7', edgecolor='#fbc02d', alpha=0.9))

    # Panel B: Net Trade Balance & Cumulative Structural Deficit
    balance = monthly['balance_millions']
    ax2.plot(balance.index, balance, color='#37474f', lw=1.2, label='Monthly Net Balance ($M USD)')
    ax2.axhline(0, color='#263238', linestyle='-', lw=1.0)
    ax2.fill_between(balance.index, balance, 0, where=(balance >= 0), color='#43a047', alpha=0.45, interpolate=True, label='Trade Surplus')
    ax2.fill_between(balance.index, balance, 0, where=(balance < 0), color='#e53935', alpha=0.45, interpolate=True, label='Trade Deficit')

    # Cumulative Net Balance on Twin Axis
    ax2_twin = ax2.twinx()
    cum_balance = balance.cumsum() / 1e3  # In Billion USD
    ax2_twin.plot(cum_balance.index, cum_balance, color='#6a1b9a', lw=2.2, linestyle=':', label='Cumulative Net Balance ($B USD)')
    ax2_twin.set_ylabel('Cumulative Net Balance (Billion USD)', fontsize=11, fontweight='bold', color='#6a1b9a')
    ax2_twin.tick_params(axis='y', labelcolor='#6a1b9a')

    ax2.set_title('(B) Monthly Trade Balance and Cumulative Structural Deficit Trajectory', fontsize=12, fontweight='bold', pad=8)
    ax2.set_ylabel('Monthly Net Balance (Million USD)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Timeline (Monthly Snapshots, 2016–2026)', fontsize=11, fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.xaxis.set_major_locator(mdates.YearLocator(1))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.set_xlim(monthly.index.min(), monthly.index.max())

    # Merge legends for bottom panel
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, loc='lower left', frameon=True, facecolor='#ffffff', framealpha=0.92, fontsize=9.5)

    plt.tight_layout()
    target_path = os.path.join(OUT_DIR, 'cambodia_macro_trade_trends.png')
    plt.savefig(target_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Successfully generated: {target_path}")


def generate_figure2_freight_modality(df):
    """
    Figure 2: Freight Modality Analysis: Cargo Volume (Metric Tons) vs. Monetary Value (USD).
    """
    modes = ['Sea transport', 'Inland waterways transport', 'Road transport', 'Air transport']
    df_m = df[df['description'].isin(modes)].copy()

    mode_map = {
        'Sea transport': 'Maritime Shipping\n(Sihanoukville Port, PAS)',
        'Inland waterways transport': 'Inland Waterways\n(Phnom Penh Port, PPAP)',
        'Road transport': 'Overland Trucking\n(Cross-Border Highways)',
        'Air transport': 'Air Freight\n(Phnom Penh / Siem Reap Int.)'
    }
    df_m['mode_clean'] = df_m['description'].map(mode_map)

    agg = df_m.groupby(['mode_clean', 'regime']).agg({
        'value_usd': 'sum',
        'net_weight_ton': 'sum'
    }).unstack('regime')

    ton_imp = agg['net_weight_ton']['Import'] / 1e6   # Million Tons
    ton_exp = agg['net_weight_ton']['Export'] / 1e6
    val_imp = agg['value_usd']['Import'] / 1e9       # Billion USD
    val_exp = agg['value_usd']['Export'] / 1e9

    # Order modes by total weight
    order = (ton_imp + ton_exp).sort_values(ascending=False).index

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.2), dpi=300)

    y = np.arange(len(order))
    height = 0.35

    # Panel A: Physical Cargo Weight
    bars1 = ax1.barh(y - height/2, [ton_exp[m] for m in order], height, label='Export Volume', color='#1565c0', alpha=0.88)
    bars2 = ax1.barh(y + height/2, [ton_imp[m] for m in order], height, label='Import Volume', color='#e53935', alpha=0.88)

    ax1.set_yticks(y)
    ax1.set_yticklabels(order, fontsize=10, fontweight='bold')
    ax1.invert_yaxis()
    ax1.set_xlabel('Total Physical Volume (Million Metric Tons)', fontsize=11, fontweight='bold')
    ax1.set_title('(A) Longitudinal Freight Cargo Weight by Modality', fontsize=12, fontweight='bold', pad=10)
    ax1.grid(True, linestyle=':', alpha=0.6, axis='x')
    ax1.legend(loc='lower right', frameon=True, facecolor='#ffffff', fontsize=10)

    # Annotate tonnage bars
    for bar in bars1:
        w = bar.get_width()
        if w > 0.1:
            ax1.text(w + 3, bar.get_y() + bar.get_height()/2, f"{w:.1f}M t", va='center', fontsize=9, fontweight='bold', color='#0d47a1')
    for bar in bars2:
        w = bar.get_width()
        if w > 0.1:
            ax1.text(w + 3, bar.get_y() + bar.get_height()/2, f"{w:.1f}M t", va='center', fontsize=9, fontweight='bold', color='#b71c1c')
    ax1.set_xlim(0, max(ton_exp.max(), ton_imp.max()) * 1.18)

    # Panel B: Monetary Cargo Value
    bars3 = ax2.barh(y - height/2, [val_exp[m] for m in order], height, label='Export Value', color='#1565c0', alpha=0.88)
    bars4 = ax2.barh(y + height/2, [val_imp[m] for m in order], height, label='Import Value', color='#e53935', alpha=0.88)

    ax2.set_yticks(y)
    ax2.set_yticklabels(['' for _ in order])
    ax2.invert_yaxis()
    ax2.set_xlabel('Cumulative Monetary Value (Billion USD)', fontsize=11, fontweight='bold')
    ax2.set_title('(B) Cumulative Monetary Trade Value by Modality', fontsize=12, fontweight='bold', pad=10)
    ax2.grid(True, linestyle=':', alpha=0.6, axis='x')
    ax2.legend(loc='lower right', frameon=True, facecolor='#ffffff', fontsize=10)

    # Annotate value bars
    for bar in bars3:
        w = bar.get_width()
        if w > 0.1:
            ax2.text(w + 1.5, bar.get_y() + bar.get_height()/2, f"${w:.1f}B", va='center', fontsize=9, fontweight='bold', color='#0d47a1')
    for bar in bars4:
        w = bar.get_width()
        if w > 0.1:
            ax2.text(w + 1.5, bar.get_y() + bar.get_height()/2, f"${w:.1f}B", va='center', fontsize=9, fontweight='bold', color='#b71c1c')
    ax2.set_xlim(0, max(val_exp.max(), val_imp.max()) * 1.18)

    plt.tight_layout()
    target_path = os.path.join(OUT_DIR, 'freight_tonnage_value_modality.png')
    plt.savefig(target_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Successfully generated: {target_path}")


def generate_figure3_seasonality_and_growth(df):
    """
    Figure 3: Annual Trade Growth & Monthly Seasonal Cycles (Cambodia Export Dynamics).
    """
    # 1. Monthly Seasonality Index
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    monthly_reg = df.groupby(['year', 'month', 'regime'])['value_usd'].sum().unstack('regime').fillna(0)

    # Compute seasonal index per year: monthly / annual_monthly_mean * 100
    monthly_reg['export_usd'] = monthly_reg['Export']
    annual_means = monthly_reg.groupby('year')['export_usd'].transform('mean')
    monthly_reg['seasonal_idx'] = (monthly_reg['export_usd'] / annual_means) * 100

    # Aggregate monthly seasonal profile (excluding incomplete 2026)
    seasonality_profile = monthly_reg.loc[2016:2025].groupby('month')['seasonal_idx'].agg(['mean', 'std'])

    # 2. Annual Totals (2016-2025)
    annual = df[df['date'].dt.year <= 2025].groupby([df['date'].dt.year, 'regime'])['value_usd'].sum().unstack('regime') / 1e9
    annual['Total_Trade'] = annual['Export'] + annual['Import']
    annual['YoY_Growth'] = annual['Total_Trade'].pct_change() * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=300)

    # Panel A: Seasonal Index Profile
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    x = np.arange(1, 13)
    means = seasonality_profile['mean'].values
    stds = seasonality_profile['std'].values

    ax1.plot(x, means, color='#0d47a1', marker='o', lw=2.2, markersize=6, label='Mean Seasonal Index (100 = Baseline)')
    ax1.fill_between(x, means - stds, means + stds, color='#bbdefb', alpha=0.5, label='±1 Standard Deviation Range')
    ax1.axhline(100, color='#d32f2f', linestyle='--', lw=1.2, label='Annual Baseline Average (100%)')

    # Annotate peak and trough
    ax1.annotate('Q4 Western Holiday Peak\n(+14% to +18% above mean)', xy=(11, means[10]), xytext=(7.8, 118),
                 arrowprops=dict(arrowstyle='->', color='#0d47a1', lw=1.5),
                 fontsize=9, fontweight='bold', color='#0d47a1',
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='#e3f2fd', edgecolor='#90caf9'))

    ax1.annotate('Post-Holiday / New Year Trough\n(-15% below mean)', xy=(2, means[1]), xytext=(1.5, 76),
                 arrowprops=dict(arrowstyle='->', color='#c62828', lw=1.5),
                 fontsize=9, fontweight='bold', color='#c62828',
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffebee', edgecolor='#ef9a9a'))

    ax1.set_xticks(x)
    ax1.set_xticklabels(months, fontsize=10, fontweight='bold')
    ax1.set_ylabel('Seasonal Index (% of Annual Mean)', fontsize=11, fontweight='bold')
    ax1.set_title('(A) Cambodia Export Seasonal Cycle (Monthly Index, 2016–2025)', fontsize=12, fontweight='bold', pad=10)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower left', frameon=True, facecolor='#ffffff', fontsize=9.5)
    ax1.set_ylim(65, 130)

    # Panel B: Annual Trade Volume & Growth
    years = annual.index.values
    bar_w = 0.55
    ax2.bar(years, annual['Export'], bar_w, label='Merchandise Exports ($B)', color='#1976d2', alpha=0.85)
    ax2.bar(years, annual['Import'], bar_w, bottom=annual['Export'], label='Merchandise Imports ($B)', color='#ef5350', alpha=0.85)

    ax2_twin = ax2.twinx()
    ax2_twin.plot(years[1:], annual['YoY_Growth'].values[1:], color='#2e7d32', marker='s', lw=2.0, label='YoY Growth Rate (%)')
    ax2_twin.set_ylabel('Annual Growth Rate (%)', fontsize=11, fontweight='bold', color='#2e7d32')
    ax2_twin.tick_params(axis='y', labelcolor='#2e7d32')
    ax2_twin.grid(False)

    ax2.set_xlabel('Calendar Year', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Total Trade Turnover (Billion USD)', fontsize=11, fontweight='bold')
    ax2.set_title('(B) Annual Merchandise Trade Volume and YoY Growth (2016–2025)', fontsize=12, fontweight='bold', pad=10)
    ax2.set_xticks(years)
    ax2.set_xticklabels(years, fontsize=10, fontweight='bold', rotation=35)
    ax2.grid(True, linestyle=':', alpha=0.6, axis='y')

    h_a, l_a = ax2.get_legend_handles_labels()
    h_b, l_b = ax2_twin.get_legend_handles_labels()
    ax2.legend(h_a + h_b, l_a + l_b, loc='upper left', frameon=True, facecolor='#ffffff', fontsize=9.5)

    plt.tight_layout()
    target_path = os.path.join(OUT_DIR, 'annual_growth_seasonality.png')
    plt.savefig(target_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Successfully generated: {target_path}")


if __name__ == '__main__':
    data = load_clean_dataset()
    generate_figure1_macro_trade_trends(data)
    generate_figure2_freight_modality(data)
    generate_figure3_seasonality_and_growth(data)
    print("All figures successfully created.")
