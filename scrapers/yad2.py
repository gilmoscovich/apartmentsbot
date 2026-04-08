"""
Yad2 scraper — uses Playwright (JS-heavy site).
Currently returns mock data; real scraping wired in a later step.
"""
from __future__ import annotations

import hashlib
import logging

from scrapers.base import BaseScraper, Listing

logger = logging.getLogger(__name__)


class Yad2Scraper(BaseScraper):
    """Scraper for yad2.co.il."""

    SOURCE = "yad2"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_listings(self) -> list[dict]:
        logger.info("[yad2] Fetching listings…")
        listings = self._mock_listings()
        logger.info("[yad2] Done — %d listings", len(listings))
        return [l.to_dict() for l in listings]

    # ------------------------------------------------------------------
    # Mock data
    # ------------------------------------------------------------------

    def _mock_listings(self) -> list[Listing]:
        return [
            Listing(
                source=self.SOURCE,
                url="https://www.yad2.co.il/item/abc123",
                price=6_500,
                city="Tel Aviv",
                rooms=3.0,
                description="Sunny 3-room apt in the heart of Tel Aviv",
                images=["https://img.yad2.co.il/abc123/1.jpg"],
                external_id="abc123",
            ),
            Listing(
                source=self.SOURCE,
                url="https://www.yad2.co.il/item/def456",
                price=4_800,
                city="Ramat Gan",
                rooms=2.5,
                description="Renovated 2.5-room apt with parking",
                images=["https://img.yad2.co.il/def456/1.jpg"],
                external_id="def456",
            ),
            # Intentional near-duplicate of Madlan listing "dup01":
            # same apartment listed on both sites (different source/ID).
            Listing(
                source=self.SOURCE,
                url="https://www.yad2.co.il/item/dup01",
                price=7_200,
                city="Herzliya",
                rooms=4.0,
                description="Spacious 4-room apt near the beach",
                images=["https://img.yad2.co.il/dup01/1.jpg"],
                external_id="dup01",
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


# ------------------------------------------------------------------
# Quick smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)
    scraper = Yad2Scraper()
    listings = scraper.fetch_listings()
    print(json.dumps(listings, indent=2, ensure_ascii=False))
