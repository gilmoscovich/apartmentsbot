"""
Listing filter — applies city / price / rooms rules.
Works on the unified dict format produced by BaseScraper.fetch_listings().
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ListingFilter:
    """Filters listings to only those matching ALL business criteria."""

    def __init__(self) -> None:
        self.allowed_locations = [
            "פרדס חנה",
            "בנימינה",
            "חדרה",
            "אור עקיבא"
        ]
        self.max_price = 4800
        self.required_rooms = 3

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter_listings(self, listings: list[dict]) -> list[dict]:
        valid = []
        for listing in listings:
            reason = self._rejection_reason(listing)
            if reason:
                print(f"Filtered out ({reason}): {listing.get('link', '?')}")
            else:
                valid.append(listing)
        return valid
    # ------------------------------------------------------------------
    # Composite check
    # ------------------------------------------------------------------

    def _rejection_reason(self, listing: dict) -> str | None:
        """Return a human-readable rejection reason, or None if listing is valid."""
        if not self._is_valid_location(listing.get("location", "")):
            return "wrong location"
        if not self._is_valid_price(listing.get("price", 0)):
            return "price too high"
        if not self._is_valid_rooms(listing.get("rooms", 0)):
            return "wrong rooms"
        return None

    # ------------------------------------------------------------------
    # Individual field checks
    # ------------------------------------------------------------------

    def _is_valid_location(self, location: str) -> bool:
        location_lower = location.lower()
        return any(allowed.lower() in location_lower for allowed in self.allowed_locations)

    def _is_valid_price(self, price: int) -> bool:
        return price <= self.max_price

    def _is_valid_rooms(self, rooms: float) -> bool:
        return abs(rooms - self.required_rooms) < 0.1


# ------------------------------------------------------------------
# Smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import os

    # Allow running from repo root
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    logging.basicConfig(level=logging.INFO)

    from scrapers.yad2 import Yad2Scraper
    from scrapers.madlan import MadlanScraper

    scraper1 = Yad2Scraper()
    scraper2 = MadlanScraper()

    all_listings = scraper1.fetch_listings() + scraper2.fetch_listings()

    f = ListingFilter()
    filtered = f.filter_listings(all_listings)

    print("\n=== FILTERED RESULTS ===")
    for l in filtered:
        print(l)
