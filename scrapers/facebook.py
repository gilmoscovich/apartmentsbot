"""
Facebook Groups scraper — fetches posts via Apify actor apify/facebook-groups-scraper.
"""
from __future__ import annotations

import logging
import re

from apify_client import ApifyClient

import config
from scrapers.base import BaseScraper, Listing
from scrapers.yad2 import Yad2Scraper

logger = logging.getLogger(__name__)


class FacebookScraper(BaseScraper):
    SOURCE = "facebook"

    # Hebrew keywords indicating sublet, roommate, sale or search posts — skip these
    _SKIP_KEYWORDS = [
        # roommates — use word-boundary phrases to avoid catching "משותף"
        "מחפש שותף", "מחפשת שותף", "להיכנס כשותף", "להיכנס כשותפה",
        "חדר להשכרה", "חדר פנוי", "שכירות חלקית",
        # sublets
        "סאבלט", "סבלט", "subletting", "מסבלט", "מסבלטת",
        # going abroad / short-term
        'יוצא לחו"ל', 'יוצאת לחו"ל',
        "שכירות זמנית", "לתקופה קצרה",
        # master-tenant
        "מאגד",
        # for sale
        "למכירה",
        # people searching (not offering)
        "מחפש דירה", "מחפשת דירה", "מחפשים דירה",
        "מחפש בית להשכרה", "מחפשת בית להשכרה", "מחפשים בית להשכרה",
        "מחפש להשכרה", "מחפשת להשכרה", "מחפשים להשכרה",
        "מחפש יחידת דיור", "מחפשת יחידת דיור",
        "מחפש להתקרקע", "מחפשת להתקרקע", "מחפשים להתקרקע",
    ]

    def __init__(self, results_limit: int | None = None, newer_than: str | None = None) -> None:
        # Per-group cap and date filter — default to config (env-tunable) values.
        self.results_limit = results_limit or config.FACEBOOK_RESULTS_LIMIT
        self.newer_than = newer_than or config.FACEBOOK_NEWER_THAN

    def fetch_listings(self) -> list[dict]:
        if not config.APIFY_API_TOKEN:
            logger.warning("[facebook] APIFY_API_TOKEN not set — skipping")
            return []
        if not config.FACEBOOK_GROUP_URLS:
            logger.warning("[facebook] FACEBOOK_GROUP_URLS not set — skipping")
            return []

        client = ApifyClient(config.APIFY_API_TOKEN)
        run_input = {
            "startUrls": [{"url": u} for u in config.FACEBOOK_GROUP_URLS],
            # resultsLimit is the actor's real per-group cap (NOT "maxPosts").
            "resultsLimit": self.results_limit,
            # Only recent posts — the main credit saver.
            "onlyPostsNewerThan": self.newer_than,
            # Newest first, so the per-group cap keeps the freshest posts.
            "viewOption": "CHRONOLOGICAL",
        }

        logger.info(
            "[facebook] Scraping %d group(s), %d posts/group, newer than '%s'",
            len(config.FACEBOOK_GROUP_URLS), self.results_limit, self.newer_than,
        )

        try:
            # max_items is a hard ceiling on charged dataset items across all groups.
            run = client.actor("apify/facebook-groups-scraper").call(
                run_input=run_input,
                max_items=config.FACEBOOK_MAX_ITEMS,
            )
        except Exception as exc:
            logger.error("[facebook] Apify run failed: %s", exc, exc_info=True)
            return []

        listings: list[dict] = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            listing = self._parse_post(item)
            if listing:
                listings.append(listing.to_dict())

        logger.info("[facebook] Done — %d listings", len(listings))
        return listings

    def _parse_post(self, item: dict) -> Listing | None:
        post_url = item.get("facebookUrl") or ""
        text = item.get("text") or item.get("body") or ""

        # Skip sublet / roommate posts
        for kw in self._SKIP_KEYWORDS:
            if kw in text:
                logger.debug("[facebook] Skipping sublet/roommate post: %s", post_url)
                return None

        price = self._extract_price(text)
        rooms = Yad2Scraper._extract_rooms(text)

        if not price or not rooms:
            logger.debug("[facebook] Skipping post (no price/rooms): %s", post_url)
            return None

        # Free-text posts: match a known city anywhere in the body, rather than
        # Yad2's positional comma-parsing (which produces garbage here).
        city = self._extract_city(text)

        title = next((line.strip() for line in text.splitlines() if line.strip()), text[:100])

        attachments = item.get("attachments") or []
        image_url = ""
        for att in attachments:
            image_url = att.get("thumbnail") or att.get("image", {}).get("uri") or ""
            if image_url:
                break

        return Listing(
            source=self.SOURCE,
            url=post_url,
            price=price,
            city=city,
            rooms=rooms,
            description=title,
            images=[image_url] if image_url else [],
            external_id=post_url or None,
        )

    # ------------------------------------------------------------------
    # Facebook-specific extraction (free-text posts, not structured titles)
    # ------------------------------------------------------------------

    # Plausible monthly-rent bounds (ILS) — filters out phone numbers,
    # square-meters, property values, etc.
    _MIN_RENT = 1_500
    _MAX_RENT = 12_000

    @staticmethod
    def _extract_city(text: str) -> str:
        """Return the first ALLOWED city whose name appears anywhere in the text."""
        for city in config.ALLOWED_CITIES:
            if city in text:
                return city
        return "unknown"

    @classmethod
    def _extract_price(cls, text: str) -> int:
        """Pick the lowest amount within a plausible rent range.

        Free-text posts often contain several numbers (phone, size, deposit);
        the monthly rent is almost always the smallest figure in range.
        We match numbers next to a shekel sign OR next to rent keywords
        (שכ"ד / שכירות / מחיר / לחודש), since FB posts often omit the ₪ sign.
        """
        shekel = r'₪|ש["״]ח|שח'
        rent_kw = r'שכ["״]?ד|שכירות|שכ"ד|מחיר|לחודש|בחודש'
        marker = rf'{shekel}|{rent_kw}'
        candidates = re.findall(
            rf'([\d,]+)\s*(?:{marker})|(?:{marker})\s*:?\s*([\d,]+)', text
        )
        values = []
        for a, b in candidates:
            digits = (a or b).replace(",", "")
            if digits.isdigit():
                values.append(int(digits))
        plausible = [v for v in values if cls._MIN_RENT <= v <= cls._MAX_RENT]
        return min(plausible) if plausible else 0


# ------------------------------------------------------------------
# Quick smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    scraper = FacebookScraper(results_limit=5, newer_than="3 days")
    listings = scraper.fetch_listings()
    print(json.dumps(listings, indent=2, ensure_ascii=False))
