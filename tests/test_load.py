import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from load import load_month


class TestLoad(unittest.TestCase):
    def test_load_month_executes_batch_upsert(self):
        # Create temp CSV
        df = pd.DataFrame([
            {
                "date": "2024-01-01",
                "period": "2024-01",
                "regime": "Import",
                "description": "Air transport",
                "description_kh": "ការដឹកជញ្ជូនតាមផ្លូវអាកាស",
                "net_weight_ton": 1184.2828,
                "net_weight_kg": 1184282.8,
                "value_usd": 148472300.0,
                "value_khr": 606294488891,
            }
        ])

        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as tf:
            df.to_csv(tf.name, index=False)
            temp_csv = tf.name

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_conn

        try:
            loaded_count = load_month(
                processed_csv_path=temp_csv,
                dag_run_id="test_run_1",
                data_interval_start="2024-01-01",
                data_interval_end="2024-02-01",
                engine=mock_engine,
            )

            self.assertEqual(loaded_count, 1)
            self.assertTrue(mock_conn.execute.called)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)


if __name__ == "__main__":
    unittest.main()
