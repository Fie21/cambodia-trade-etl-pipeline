"""
Time-Series Forecasting Module for Cambodia GDCE Trade & Logistics.
Implements econometric and exponential smoothing models:
  - 🏆 Holt-Winters Triple Exponential Smoothing (Champion Model)
  - 🥈 SARIMAX(1,1,1)x(1,1,1)12 (Econometric Benchmark)
  - 📊 Seasonal Naive (Baseline)
"""
from typing import Dict, Tuple, Any
import numpy as np
import pandas as pd


def forecast_monthly_series(
    df: pd.DataFrame,
    date_col: str = "date",
    value_col: str = "value",
    horizon: int = 12,
    model_type: str = "Holt-Winters",
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Fits a time-series model on historical monthly data and generates an H-month forward forecast
    with calibrated 95% confidence/prediction intervals.

    Supported model_type:
        - "Holt-Winters" (Triple Exponential Smoothing)
        - "SARIMAX" (Seasonal AutoRegressive Integrated Moving Average)
        - "Seasonal Naive" (Baseline repeat from last year)

    Returns:
        df_history: historical series [date, actual]
        df_forecast: forecasted points [date, forecast, lower_95, upper_95]
        metrics: summary metrics dictionary
    """
    if df.empty or len(df) < 6:
        raise ValueError("Insufficient data points for forecasting (minimum 6 months required).")

    # Clean and aggregate monthly
    data = df[[date_col, value_col]].copy()
    data[date_col] = pd.to_datetime(data[date_col])
    data = data.sort_values(date_col).set_index(date_col)
    
    # Resample to strict month start
    series = data[value_col].resample("MS").sum().ffill().fillna(0)

    # Pre-Fitting Outlier / Shock Smoothing (STL Residual Decomposition)
    if len(series) >= 24:
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
            decomp = seasonal_decompose(series, model="additive", period=12)
            resid = decomp.resid
            std_r = resid.std()
            extreme_mask = np.abs(resid) > 2.5 * std_r
            if extreme_mask.any():
                cleaned_resid = resid.copy()
                cleaned_resid[extreme_mask] = cleaned_resid.rolling(5, center=True, min_periods=1).median()[extreme_mask]
                series = (decomp.trend + decomp.seasonal + cleaned_resid).bfill().ffill()
        except Exception:
            pass

    last_date = series.index[-1]
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=horizon, freq="MS")

    forecast_values = np.zeros(horizon)
    se = np.std(series.values) * 0.15
    model_name_used = model_type
    fitted = False

    # 1. SARIMAX MODEL
    if "SARIMAX" in model_type.upper() and len(series) >= 24:
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
            sarima_model = SARIMAX(
                series,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False, maxiter=50)
            forecast_values = sarima_model.forecast(horizon).values
            residuals = sarima_model.resid.values
            se = np.std(residuals) if np.std(residuals) > 0 else np.std(series.values) * 0.1
            model_name_used = "SARIMAX (1,1,1)x(1,1,1)₁₂ Econometric Model"
            fitted = True
        except Exception:
            fitted = False

    # 2. SEASONAL NAIVE MODEL
    elif "NAIVE" in model_type.upper() and len(series) >= 12:
        s_naive = series.iloc[-12:].values
        forecast_values = np.tile(s_naive, int(np.ceil(horizon / 12)))[:horizon]
        se = np.std(series.diff().dropna().values)
        model_name_used = "Seasonal Naive Baseline (Same Month Last Year)"
        fitted = True

    # 3. HOLT-WINTERS MODEL (Default & Champion)
    if not fitted and len(series) >= 24:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal="add",
                seasonal_periods=12,
                initialization_method="estimated",
            ).fit(optimized=True)
            forecast_values = model.forecast(horizon).values
            residuals = series.values - model.fittedvalues.values
            se = np.std(residuals) if np.std(residuals) > 0 else np.std(series.values) * 0.1
            model_name_used = "Holt-Winters Triple Exponential Smoothing (Additive Trend & 12M Seasonality)"
            fitted = True
        except Exception:
            fitted = False

    # Fallback to Single/Double Exponential Smoothing if series is 12-23 months
    if not fitted and len(series) >= 12:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal=None,
                initialization_method="estimated",
            ).fit(optimized=True)
            forecast_values = model.forecast(horizon).values
            residuals = series.values - model.fittedvalues.values
            se = np.std(residuals) if np.std(residuals) > 0 else np.std(series.values) * 0.1
            model_name_used = "Holt Linear Trend (Double Exponential Smoothing)"
            fitted = True
        except Exception:
            fitted = False

    # Final Fallback to robust linear trend + seasonal factors
    if not fitted:
        x = np.arange(len(series))
        y = series.values
        slope, intercept = np.polyfit(x, y, 1)
        month_factors = series.groupby(series.index.month).mean() - series.mean()
        future_x = np.arange(len(series), len(series) + horizon)
        base_trend = intercept + slope * future_x
        seasonal_adj = np.array([month_factors.get(d.month, 0) for d in future_dates])
        forecast_values = base_trend + seasonal_adj
        hist_fitted = intercept + slope * x + np.array([month_factors.get(d.month, 0) for d in series.index])
        residuals = y - hist_fitted
        se = np.std(residuals) if np.std(residuals) > 0 else np.std(y) * 0.1
        model_name_used = "Linear Trend with Monthly Seasonal Decomposition"

    # Ensure non-negative predictions for merchandise / cargo tonnage
    forecast_values = np.clip(forecast_values, a_min=0, a_max=None)
    
    # 95% Confidence / Prediction interval expanding over horizon: SE * 1.96 * sqrt(1 + h/12)
    step_multipliers = np.sqrt(1 + np.arange(1, horizon + 1) / 12.0)
    margin = 1.96 * se * step_multipliers

    lower_bounds = np.clip(forecast_values - margin, a_min=0, a_max=None)
    upper_bounds = forecast_values + margin

    df_history = pd.DataFrame({
        "date": series.index,
        "actual": series.values,
    })

    df_forecast = pd.DataFrame({
        "date": future_dates,
        "forecast": forecast_values,
        "lower_95": lower_bounds,
        "upper_95": upper_bounds,
    })

    # Summary Analytics
    last_12m_hist = series.iloc[-12:].sum() if len(series) >= 12 else series.sum()
    forecast_12m = forecast_values[:12].sum()
    growth_rate = ((forecast_12m - last_12m_hist) / last_12m_hist * 100) if last_12m_hist > 0 else 0.0

    peak_idx = int(np.argmax(forecast_values))
    peak_date = future_dates[peak_idx].strftime("%Y-%m")
    peak_value = float(forecast_values[peak_idx])

    metrics = {
        "model_used": model_name_used,
        "horizon_months": horizon,
        "historical_last_12m": float(last_12m_hist),
        "forecast_horizon_total": float(forecast_values.sum()),
        "projected_growth_rate_pct": float(growth_rate),
        "peak_month": peak_date,
        "peak_value": peak_value,
        "standard_error": float(se),
    }

    return df_history, df_forecast, metrics
