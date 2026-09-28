"""
GDCE Scrapers Package.
Provides modular scrapers for:
- Transport Mode statistics (transport.py)
- Partner Country statistics (country.py)
- SITC Sector statistics (sitc.py)
- HS Chapter statistics (hs.py)
"""
from typing import Dict, Optional

from .common import create_session
from .country import scrape_country_month
from .hs import scrape_hs_month
from .sitc import scrape_sitc_month
from .transport import scrape_transport_month


def scrape_all_month(
    data_interval_start: str,
    data_interval_end: Optional[str] = None,
) -> Dict[str, str]:
    """
    Executes all 4 GDCE scrapers for the specified month period.
    Returns a dictionary of generated raw JSON file paths.
    """
    session = create_session()
    return {
        "transport": scrape_transport_month(data_interval_start, data_interval_end, session=session),
        "country": scrape_country_month(data_interval_start, data_interval_end, session=session),
        "sitc": scrape_sitc_month(data_interval_start, data_interval_end, session=session),
        "hs": scrape_hs_month(data_interval_start, data_interval_end, session=session),
    }


__all__ = [
    "create_session",
    "scrape_transport_month",
    "scrape_country_month",
    "scrape_sitc_month",
    "scrape_hs_month",
    "scrape_all_month",
]
