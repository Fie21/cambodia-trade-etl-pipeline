"""
Unified GDCE Scraper entry point for backward compatibility and CLI execution.
Wraps modular scrapers from the src.scrapers package:
- Transport Mode: src.scrapers.transport
- Partner Country: src.scrapers.country
- SITC Sectors: src.scrapers.sitc
- HS Chapters: src.scrapers.hs
"""
import logging
import sys
from typing import Dict, Optional

from scrapers import (
    create_session,
    scrape_all_month,
    scrape_country_month,
    scrape_hs_month,
    scrape_sitc_month,
    scrape_transport_month,
)
from scrapers.transport import fetch_gdce_mot

# For backward compatibility with existing DAG / tests
scrape_month = scrape_transport_month

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start = sys.argv[1] if len(sys.argv) > 1 else "2024-01-01"
    end = sys.argv[2] if len(sys.argv) > 2 else "2024-02-01"
    
    mode = sys.argv[3] if len(sys.argv) > 3 else "all"
    if mode == "all":
        paths = scrape_all_month(start, end)
        print("Scraped all datasets:", paths)
    elif mode == "transport":
        print("Transport path:", scrape_transport_month(start, end))
    elif mode == "country":
        print("Country path:", scrape_country_month(start, end))
    elif mode == "sitc":
        print("SITC path:", scrape_sitc_month(start, end))
    elif mode == "hs":
        print("HS path:", scrape_hs_month(start, end))
