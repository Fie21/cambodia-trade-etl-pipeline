import json
import os
import shutil
import tempfile
import unittest
from scrapers.country import fetch_country_metadata, scrape_country_month


class TestScrapeCountry(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_fetch_country_metadata(self):
        groups_map, country_to_groups, name_to_country = fetch_country_metadata()
        self.assertGreater(len(groups_map), 0, "Should load country groups")
        self.assertTrue("ASE" in groups_map or "EUU" in groups_map, "Should have ASEAN/EU groups")
        self.assertGreater(len(country_to_groups), 0, "Should have country-to-group mappings")
        self.assertGreater(len(name_to_country), 0, "Should have country master mappings")

    def test_scrape_country_month(self):
        import scrapers.country as sc
        original_dir = sc.RAW_COUNTRY_DIR
        try:
            sc.RAW_COUNTRY_DIR = self.test_dir
            out_path = scrape_country_month("2024-01-01", "2024-02-01")

            self.assertTrue(os.path.exists(out_path), "File should exist")
            with open(out_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data["period"], "2024-01")
            self.assertGreater(data["total_records"], 0)
            record = data["records"][0]
            self.assertIn("country_name_en", record)
            self.assertIn("trade_type", record)
            self.assertIn("value_usd", record)
            self.assertIn("value_khr", record)
            self.assertIn("country_groups", record)
        finally:
            sc.RAW_COUNTRY_DIR = original_dir


if __name__ == "__main__":
    unittest.main()
