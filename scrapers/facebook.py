"""
Facebook Groups scraper — fetches posts via Apify actor apify/facebook-groups-scraper.
"""
from __future__ import annotations

import logging

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

    def __init__(self, max_posts: int = 100) -> None:
        self.max_posts = max_posts

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
            "maxPosts": self.max_posts,
        }

        try:
            run = client.actor("apify/facebook-groups-scraper").call(run_input=run_input)
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

        price = Yad2Scraper._extract_price(text)
        rooms = Yad2Scraper._extract_rooms(text)

        if not price or not rooms:
            logger.debug("[facebook] Skipping post (no price/rooms): %s", post_url)
            return None

        city = Yad2Scraper.extract_city_from_title(text)
        if not city:
            city = "unknown"

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
# Quick smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    scraper = FacebookScraper(max_posts=10)
    listings = scraper.fetch_listings()
    print(json.dumps(listings, indent=2, ensure_ascii=False))
