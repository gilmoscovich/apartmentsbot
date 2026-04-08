"""
Madlan scraper — uses Requests + BeautifulSoup (+ Playwright fallback).
Currently returns mock data; real scraping wired in a later step.
"""
from __future__ import annotations

import hashlib
import logging

from scrapers.base import BaseScraper, Listing

logger = logging.getLogger(__name__)


class MadlanScraper(BaseScraper):
    """Scraper for madlan.co.il."""

    SOURCE = "madlan"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_listings(self) -> list[dict]:
        logger.info("[madlan] Fetching listings…")
        listings = self._mock_listings()
        logger.info("[madlan] Done — %d listings", len(listings))
        return [l.to_dict() for l in listings]

    # ------------------------------------------------------------------
    # Mock data
    # ------------------------------------------------------------------

    def _mock_listings(self) -> list[Listing]:
        return [
            Listing(
                source=self.SOURCE,
                url="https://www.madlan.co.il/listings/m001",
                price=5_500,
                city="Jerusalem",
                rooms=3.5,
                description="Quiet 3.5-room apt in Katamon",
                images=["https://img.madlan.co.il/m001/1.jpg"],
                external_id="m001",
            ),
            Listing(
                source=self.SOURCE,
                url="https://www.madlan.co.il/listings/m002",
                price=3_900,
                city="Haifa",
                rooms=2.0,
                description="Sea-view 2-room apt on the Carmel",
                images=["https://img.madlan.co.il/m002/1.jpg"],
                external_id="m002",
            ),
            # Intentional near-duplicate of Yad2 listing "dup01":
            # same apartment (Herzliya, 4 rooms, ₪7200) listed on both sites.
            Listing(
                source=self.SOURCE,
                url="https://www.madlan.co.il/listings/m003",
                price=7_200,
                city="Herzliya",
                rooms=4.0,
                description="Spacious 4-room apt near the beach",
                images=["https://img.madlan.co.il/m003/1.jpg"],
                external_id="m003",
            ),
        ]

    # ------------------------------------------------------------------
    # Hooks for real scraping (filled in next step)
    # ------------------------------------------------------------------

    def _parse_listing(self, raw_data) -> dict:
        """Parse a raw page/API payload into a Listing dict.  (placeholder)"""
        raise NotImplementedError

    def _generate_id(self, data: dict) -> str:
        """Stable hash from title + price + location."""
        key = f"{data.get('title', '')}|{data.get('price', '')}|{data.get('location', '')}"
        return hashlib.md5(key.encode()).hexdigest()
