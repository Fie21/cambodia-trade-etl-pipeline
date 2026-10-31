"""
Unit tests for the time-series forecasting module.
"""
import unittest
import numpy as np
import pandas as pd
from src.forecast import forecast_monthly_series


class TestTimeSeriesForecasting(unittest.TestCase):
    def setUp(self):
        # Generate 36 months of synthetic monthly data with trend and seasonality
        dates = pd.date_range(start="2021-01-01", periods=36, freq="MS")
        trend = np.linspace(100, 300, 36)
        seasonal = 20 * np.sin(2 * np.pi * np.arange(36) / 12)
        noise = np.random.normal(0, 5, 36)
        values = trend + seasonal + noise
        self.df = pd.DataFrame({"date": dates, "value": values})

    def test_forecast_horizon_length(self):
        horizon = 12
        hist_df, fc_df, metrics = forecast_monthly_series(self.df, horizon=horizon)
        self.assertEqual(len(fc_df), horizon)
        self.assertIn("forecast", fc_df.columns)
        self.assertIn("lower_95", fc_df.columns)
        self.assertIn("upper_95", fc_df.columns)

    def test_forecast_confidence_intervals(self):
        hist_df, fc_df, metrics = forecast_monthly_series(self.df, horizon=6)
        # Upper bound must always be greater than or equal to lower bound
        self.assertTrue((fc_df["upper_95"] >= fc_df["lower_95"]).all())
        # Point forecast should generally lie within bounds
        self.assertTrue((fc_df["forecast"] >= fc_df["lower_95"]).all())
        self.assertTrue((fc_df["forecast"] <= fc_df["upper_95"]).all())

    def test_forecast_metrics_content(self):
        hist_df, fc_df, metrics = forecast_monthly_series(self.df, horizon=12)
        self.assertIn("model_used", metrics)
        self.assertIn("forecast_horizon_total", metrics)
        self.assertIn("peak_month", metrics)
        self.assertGreater(metrics["forecast_horizon_total"], 0)

    def test_insufficient_data_error(self):
        short_df = self.df.iloc[:3]
        with self.assertRaises(ValueError):
            forecast_monthly_series(short_df, horizon=6)

    def test_hampel_outlier_filtering(self):
        from src.forecast import apply_hampel_filter
        s = pd.Series(self.df["value"].values, index=self.df["date"])
        # Inject extreme shock
        s.iloc[15] += 500.0
        cleaned, is_outlier = apply_hampel_filter(s, window=5, n_sigmas=3.0)
        self.assertTrue(is_outlier.iloc[15])
        self.assertLess(cleaned.iloc[15], 400.0)

    def test_all_model_families(self):
        for m_type in ["Holt-Winters", "SARIMAX", "Random Forest", "Gradient Boosting", "3-Month MA", "Seasonal Naive", "Linear Trend"]:
            hist_df, fc_df, metrics = forecast_monthly_series(self.df, horizon=6, model_type=m_type)
            self.assertEqual(len(fc_df), 6)
            self.assertFalse(fc_df["forecast"].isna().any())

    def test_model_tournament_evaluation(self):
        from src.forecast import evaluate_model_tournament
        leaderboard = evaluate_model_tournament(self.df, holdout_months=6)
        self.assertFalse(leaderboard.empty)
        self.assertIn("Model", leaderboard.columns)
        self.assertIn("MAPE (%)", leaderboard.columns)
        self.assertIn("Status", leaderboard.columns)


if __name__ == "__main__":
    unittest.main()

