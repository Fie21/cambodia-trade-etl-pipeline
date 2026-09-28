import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from scrapers.transport import fetch_gdce_mot, scrape_transport_month
from scrape import scrape_month


class TestScrape(unittest.TestCase):
    @patch("scrapers.transport.requests.Session.get")
    def test_fetch_gdce_mot_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "contents": [
                    {
                        "refYear": 2024,
                        "refMonth": 1,
                        "dscEn": "Sea transport",
                        "dscKh": "ការដឹកជញ្ជូនតាមផ្លូវសមុទ្រ",
                        "imNetWeight": 1000000.0,
                        "imTotalValueUsd": 50000000.0,
                        "imTotalValueKhr": 200000000000,
                    }
                ]
            },
        }
        mock_get.return_value = mock_response

        contents = fetch_gdce_mot(2024, 1, "IM")
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0]["dscEn"], "Sea transport")
        self.assertEqual(contents[0]["imNetWeight"], 1000000.0)

    @patch("scrapers.transport.fetch_gdce_mot")
    def test_scrape_month(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "refYear": 2024,
                "refMonth": 1,
                "dscEn": "Air transport",
                "imNetWeight": 500000.0,
                "imTotalValueUsd": 12000000.0,
            }
        ]

        out_path = scrape_month("2024-01-01", "2024-02-01")
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["period"], "2024-01")
        self.assertIn("Import", data["regimes"])
        self.assertIn("Export", data["regimes"])


if __name__ == "__main__":
    unittest.main()
