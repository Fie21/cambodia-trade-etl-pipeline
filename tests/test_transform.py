import json
import os
import sys
import tempfile
import unittest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from transform import clean_float, clean_int, transform_month


class TestTransform(unittest.TestCase):
    def test_clean_float(self):
        self.assertEqual(clean_float("1,234.56"), 1234.56)
        self.assertEqual(clean_float(100.5), 100.5)
        self.assertEqual(clean_float(None), 0.0)
        self.assertEqual(clean_float("invalid"), 0.0)

    def test_clean_int(self):
        self.assertEqual(clean_int("1,000"), 1000)
        self.assertEqual(clean_int(50), 50)
        self.assertEqual(clean_int(None), 0)
        self.assertEqual(clean_int("invalid"), 0)

    def test_transform_month_normalizes_data(self):
        sample_payload = {
            "period": "2024-05",
            "data_interval_start": "2024-05-01",
            "data_interval_end": "2024-06-01",
            "scraped_at": "2024-05-15T00:00:00",
            "regimes": {
                "Import": {
                    "regime_code": "IM",
                    "contents": [
                        {
                            "refYear": 2024,
                            "refMonth": 5,
                            "dscEn": "Sea transport",
                            "dscKh": "ការដឹកជញ្ជូនតាមផ្លូវសមុទ្រ",
                            "imNetWeight": 2500000.0,
                            "imTotalValueUsd": 80000000.0,
                            "imTotalValueKhr": 320000000000,
                        }
                    ]
                },
                "Export": {
                    "regime_code": "EX,RX",
                    "contents": [
                        {
                            "refYear": 2024,
                            "refMonth": 5,
                            "dscEn": "Air transport",
                            "dscKh": "ការដឹកជញ្ជូនតាមផ្លូវអាកាស",
                            "exNetWeight": 150000.0,
                            "exTotalValueUsd": 25000000.0,
                            "exTotalValueKhr": 100000000000,
                        }
                    ]
                }
            }
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(sample_payload, tf)
            temp_json = tf.name

        try:
            out_csv = transform_month(temp_json)
            self.assertTrue(os.path.exists(out_csv))
            df = pd.read_csv(out_csv)

            self.assertEqual(len(df), 2)
            self.assertListEqual(
                list(df.columns),
                [
                    "date",
                    "period",
                    "regime",
                    "description",
                    "description_kh",
                    "net_weight_ton",
                    "net_weight_kg",
                    "value_usd",
                    "value_khr",
                ],
            )

            # Sea transport Import verification
            sea_row = df[(df["description"] == "Sea transport") & (df["regime"] == "Import")].iloc[0]
            self.assertEqual(sea_row["period"], "2024-05")
            self.assertEqual(sea_row["date"], "2024-05-01")
            self.assertEqual(sea_row["net_weight_ton"], 2500.0)  # 2,500,000 kg -> 2,500 tons
            self.assertEqual(sea_row["value_usd"], 80000000.0)

            # Air transport Export verification
            air_row = df[(df["description"] == "Air transport") & (df["regime"] == "Export")].iloc[0]
            self.assertEqual(air_row["net_weight_ton"], 150.0)  # 150,000 kg -> 150 tons
            self.assertEqual(air_row["value_usd"], 25000000.0)
        finally:
            if os.path.exists(temp_json):
                os.remove(temp_json)


if __name__ == "__main__":
    unittest.main()
