"""
Deduplication layer — removes duplicate listings within a batch and across sources.

Two listings are considered duplicates when ALL of the following hold:
  - location strings overlap (case-insensitive substring match)
  - price difference is <= 200 ILS
  - room count difference is < 0.2
"""
from __future__ import annotations


class Deduplicator:

    def deduplicate(self, listings: list[dict]) -> list[dict]:
        """Return listings with duplicates removed (first occurrence wins)."""
        unique: list[dict] = []
        for candidate in listings:
            duplicate_of = self._find_duplicate(candidate, unique)
            if duplicate_of is not None:
                print(
                    f"Duplicate detected: {candidate['link']} == {duplicate_of['link']}"
                )
            else:
                unique.append(candidate)
        return unique

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_duplicate(self, candidate: dict, accepted: list[dict]) -> dict | None:
        """Return the first accepted listing that is a duplicate of candidate, or None."""
        for accepted_listing in accepted:
            if self._is_duplicate(candidate, accepted_listing):
                return accepted_listing
        return None

    def _is_duplicate(self, l1: dict, l2: dict) -> bool:
        """True when location, price, and rooms all match within thresholds."""
        if not self._location_similar(l1.get("location", ""), l2.get("location", "")):
            return False
        if abs(l1.get("price", 0) - l2.get("price", 0)) > 200:
            return False
        if abs(l1.get("rooms", 0) - l2.get("rooms", 0)) >= 0.2:
            return False
        return True

    def _location_similar(self, loc1: str, loc2: str) -> bool:
        """True when either location string is a substring of the other (case-insensitive)."""
        a = loc1.strip().lower()
        b = loc2.strip().lower()
        return a in b or b in a


# ------------------------------------------------------------------
# Quick smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from scrapers.yad2 import Yad2Scraper
    from scrapers.madlan import MadlanScraper

    s1 = Yad2Scraper()
    s2 = MadlanScraper()

    listings = s1.fetch_listings() + s2.fetch_listings()

    d = Deduplicator()
    unique = d.deduplicate(listings)

    print("\n=== UNIQUE LISTINGS ===")
    for l in unique:
        print(l)

    print(f"\nBefore: {len(listings)}, After: {len(unique)}")
